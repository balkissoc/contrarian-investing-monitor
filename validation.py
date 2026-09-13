"""Prospective event cohorts with conservative entry timing and matched benchmarks.

These are independent hypothetical observations, not an investable portfolio.
Legacy observations are retained separately; today's fundamentals are never backfilled.
"""
from __future__ import annotations

import pandas as pd

from research import SETTINGS, write_json

HORIZONS = {"5d": ("sessions", 5), "20d": ("sessions", 20), "60d": ("sessions", 60), "12m": ("months", 12), "24m": ("months", 24), "36m": ("months", 36)}
COHORT_COLUMNS = ["ticker", "signal_date", "signal_type", "settings_version", "research_lane", "attention_score", "entry_date", "entry_raw_close", "latest_date", "status", "entry_rule", "cost_bps"] + [f"{prefix}_{name}_pct" for name in HORIZONS for prefix in ("net_return", "benchmark", "excess")]


def event_anchors(log: pd.DataFrame) -> list[dict]:
    out = []
    if log.empty:
        return out
    for ticker, rows in log.groupby("ticker"):
        last = None
        # Sorting retains the type known on the first day; no future candidate upgrade.
        rows = rows.sort_values(["signal_date", "signal_type"], kind="stable").drop_duplicates("signal_date")
        for _, row in rows.iterrows():
            day = pd.to_datetime(row["signal_date"], errors="coerce")
            if pd.isna(day):
                continue
            if last is None or (day - last).days > SETTINGS["episode_gap_days"]:
                out.append(row.to_dict())
            last = day
    return out


def net_return(start: float, end: float) -> float:
    half_cost = SETTINGS["simulation_round_trip_cost_bps"] / 20000
    return (end * (1 - half_cost) / (start * (1 + half_cost)) - 1) * 100


def measure_event(row: dict, histories: dict, today: str) -> dict:
    result = {
        "ticker": row["ticker"], "signal_date": row["signal_date"], "signal_type": row["signal_type"],
        "settings_version": row.get("settings_version_at_signal", ""), "research_lane": row.get("research_lane_at_signal", ""),
        "attention_score": row.get("attention_score_at_signal", ""), "status": "history_unavailable",
        "entry_rule": "First available close strictly after scan date; observation only",
        "cost_bps": SETTINGS["simulation_round_trip_cost_bps"],
    }
    history = histories.get(row["ticker"])
    if history is None:
        return result
    raw, adjusted = history
    adjusted = adjusted[(adjusted > 0) & (adjusted.index <= pd.Timestamp(today))]
    possible = adjusted[adjusted.index > pd.Timestamp(row["signal_date"])]
    if possible.empty:
        result["status"] = "awaiting_entry"
        return result
    entry = possible.index[0]
    if (entry - pd.Timestamp(row["signal_date"])).days > 7 or entry not in raw.index:
        result["status"] = "entry_gap_requires_review"
        return result
    result.update(entry_date=entry.date().isoformat(), entry_raw_close=float(raw.loc[entry]), latest_date=adjusted.index[-1].date().isoformat())
    result["status"] = "current" if (pd.Timestamp(today) - adjusted.index[-1]).days <= 5 else "stale_history"
    benchmark = histories.get(SETTINGS["market_benchmark"])
    benchmark = benchmark[1] if benchmark else pd.Series(dtype=float)
    for label, (unit, length) in HORIZONS.items():
        if unit == "sessions":
            if len(possible) <= length:
                continue
            end = possible.index[length]
        else:
            target = entry + pd.DateOffset(months=length)
            eligible = possible[possible.index >= target]
            if eligible.empty:
                continue
            end = eligible.index[0]
            if (end - target).days > 7:
                continue
        ret = net_return(float(adjusted.loc[entry]), float(adjusted.loc[end]))
        result[f"net_return_{label}_pct"] = round(ret, 4)
        if entry in benchmark.index and end in benchmark.index and benchmark.loc[entry] > 0:
            bench = net_return(float(benchmark.loc[entry]), float(benchmark.loc[end]))
            result[f"benchmark_{label}_pct"] = round(bench, 4)
            result[f"excess_{label}_pct"] = round(ret - bench, 4)
    return result


def update_validation(log: pd.DataFrame, histories: dict, today: str, reports_dir) -> pd.DataFrame:
    rows = [measure_event(row, histories, today) for row in event_anchors(log)]
    output = pd.DataFrame(rows, columns=COHORT_COLUMNS)
    output.to_csv(reports_dir / "event_validation.csv", index=False)
    prospective = output[output["settings_version"].fillna("") == SETTINGS["version"]]
    summary = {"as_of": today, "settings_version": SETTINGS["version"], "benchmark": SETTINGS["market_benchmark"], "prospective_events": len(prospective), "legacy_events": len(output) - len(prospective), "unavailable_or_stale": int((~output["status"].isin(["current", "awaiting_entry"])).sum()), "horizons": {}, "score_bands": {}}
    for label in HORIZONS:
        valid = prospective[(prospective["status"] == "current") & prospective[f"net_return_{label}_pct"].notna()]
        matched = valid[valid[f"excess_{label}_pct"].notna()]
        values = pd.to_numeric(valid[f"net_return_{label}_pct"])
        summary["horizons"][label] = {"mature": len(valid), "matched": len(matched), "median_net_pct": round(float(values.median()), 2) if len(valid) else None, "median_excess_pp": round(float(matched[f"excess_{label}_pct"].median()), 2) if len(matched) else None, "hit_20_pct": round(float((values >= 20).mean()) * 100, 1) if label == "12m" and len(valid) else None}
    scores = pd.to_numeric(prospective["attention_score"], errors="coerce")
    for name, low, high in (("0–39", 0, 40), ("40–59", 40, 60), ("60–79", 60, 80), ("80–100", 80, 101)):
        group = prospective[(scores >= low) & (scores < high) & (prospective["status"] == "current")]
        values = pd.to_numeric(group["excess_20d_pct"], errors="coerce").dropna()
        summary["score_bands"][name] = {"matched_20d": len(values), "median_excess_pp": round(float(values.median()), 2) if len(values) else None}
    write_json(reports_dir / "validation_summary.json", summary)
    return output
