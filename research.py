"""Evidence-aware research enrichment. Discovery never produces a buy approval."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from monitor_metrics import as_number

ROOT = Path(__file__).resolve().parent
SETTINGS = json.loads((ROOT / "config/research_settings.json").read_text(encoding="utf-8"))
CACHE_PATH = ROOT / "reports/fundamental_cache.json"
STATE_PATH = ROOT / "reports/alert_state.json"
BENCHMARKS: dict[str, pd.DataFrame] = {}
FUNDAMENTALS: dict | None = None

RESEARCH_COLUMNS = [
    "settings_version", "three_month_pct", "six_month_pct", "twelve_month_pct",
    "one_day_z", "five_day_z", "twenty_day_z", "volatility_trigger",
    "median_turnover_20d_aud", "liquidity_gate", "price_freshness",
    "market_benchmark", "market_five_day_pct", "market_twenty_day_pct",
    "market_relative_five_day_pp", "market_relative_twenty_day_pp", "market_context",
    "sector", "industry", "sector_benchmark", "sector_relative_five_day_pp",
    "sector_relative_twenty_day_pp", "sector_context", "fundamental_currency",
    "fundamental_period", "fundamental_fetched", "fundamental_status",
    "net_income", "free_cash_flow", "operating_cash_flow", "total_cash", "total_debt",
    "fundamental_source", "research_lane", "research_status", "required_information",
    "investigation_flags", "alert_status", "alert_reason", "universe_lane",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def daily_series(history: pd.DataFrame, field: str = "Close") -> pd.Series:
    if field not in history:
        return pd.Series(dtype=float)
    values = pd.to_numeric(history[field], errors="coerce").dropna()
    values = values[values > 0].copy()
    index = pd.to_datetime(values.index)
    if index.tz is not None:
        index = index.tz_localize(None)
    values.index = index.normalize()
    return values.groupby(level=0).last().sort_index()


def change(values: pd.Series, sessions: int) -> float | None:
    if len(values) <= sessions:
        return None
    return round((float(values.iloc[-1]) / float(values.iloc[-sessions - 1]) - 1) * 100, 6)


def price_context(history: pd.DataFrame) -> dict:
    """Close is adjusted by caller. Estimate volatility strictly before each event window."""
    close = daily_series(history)
    out = {"settings_version": SETTINGS["version"]}
    for label, sessions in (("three_month", 63), ("six_month", 126), ("twelve_month", 252)):
        out[f"{label}_pct"] = change(close, sessions)
    returns = close.map(math.log).diff().dropna()
    unusual = []
    for (label, sessions), minimum_fall in zip(
        (("one_day", 1), ("five_day", 5), ("twenty_day", 20)), SETTINGS["volatility_min_falls_pct"]
    ):
        baseline = returns.iloc[:-sessions].tail(60)
        sigma = float(baseline.std()) if len(baseline) >= 40 else 0
        z = None
        if sigma > 1e-8 and len(close) > sessions:
            event = math.log(float(close.iloc[-1]) / float(close.iloc[-sessions - 1]))
            z = (event - sessions * float(baseline.mean())) / (sigma * math.sqrt(sessions))
        out[f"{label}_z"] = round(z, 2) if z is not None else None
        move = change(close, sessions)
        if z is not None and z <= SETTINGS["volatility_trigger_z"] and move is not None and move <= minimum_fall:
            unusual.append(f"{sessions}D {z:.1f}σ")
    out["volatility_trigger"] = "; ".join(unusual)
    if "Volume" in history and len(history) >= 21:
        # Adjusted close × volume is an approximation; do not call it exact traded value.
        turnover = (history["Close"] * history["Volume"]).iloc[-21:-1].dropna()
        out["median_turnover_20d_aud"] = float(turnover.median()) if len(turnover) >= 15 else None
    else:
        out["median_turnover_20d_aud"] = None
    turnover = out["median_turnover_20d_aud"]
    out["liquidity_gate"] = "unknown" if turnover is None else "below_research_floor" if turnover < SETTINGS["minimum_median_turnover_aud"] else "screen_pass_only"
    return out


def benchmark_history(ticker: str) -> pd.DataFrame:
    if ticker not in BENCHMARKS:
        try:
            BENCHMARKS[ticker] = yf.Ticker(ticker).history(period="2y", auto_adjust=True)
        except Exception:
            BENCHMARKS[ticker] = pd.DataFrame()
    return BENCHMARKS[ticker]


def aligned_return(benchmark: pd.Series, stock: pd.Series, sessions: int) -> float | None:
    """Require the exact stock endpoints: never compare differing dates or forward-fill a halt."""
    if len(stock) <= sessions:
        return None
    start, end = stock.index[-sessions - 1], stock.index[-1]
    if start not in benchmark.index or end not in benchmark.index:
        return None
    return round((float(benchmark.loc[end]) / float(benchmark.loc[start]) - 1) * 100, 6)


def market_context(history: pd.DataFrame, sector: str, today: str) -> dict:
    close = daily_series(history)
    benchmark = SETTINGS["market_benchmark"]
    market = daily_series(benchmark_history(benchmark))
    result = {"market_benchmark": benchmark, "market_context": "context_unavailable", "sector_context": "context_unavailable", "sector_benchmark": ""}
    if not close.empty:
        age = (pd.Timestamp(today) - close.index[-1]).days
        result["price_freshness"] = "stale_or_mismatched" if age > 5 or age < 0 or (not market.empty and close.index[-1] != market.index[-1]) else "recent"
    for name, sessions in (("five_day", 5), ("twenty_day", 20)):
        move = aligned_return(market, close, sessions)
        stock_move = change(close, sessions)
        result[f"market_{name}_pct"] = move
        result[f"market_relative_{name}_pp"] = round(stock_move - move, 4) if move is not None and stock_move is not None else None
    m5, m20 = result["market_five_day_pct"], result["market_twenty_day_pct"]
    if m5 is not None and m20 is not None:
        result["market_context"] = "systemic_selloff" if m5 <= SETTINGS["systemic_five_day_pct"] or m20 <= SETTINGS["systemic_twenty_day_pct"] else "no_systemic_trigger"
    symbol = SETTINGS["sector_price_benchmarks"].get(sector)
    if symbol:
        sector_close = daily_series(benchmark_history(symbol))
        result["sector_benchmark"] = symbol
        for name, sessions in (("five_day", 5), ("twenty_day", 20)):
            move = aligned_return(sector_close, close, sessions)
            stock_move = change(close, sessions)
            result[f"sector_relative_{name}_pp"] = round(stock_move - move, 4) if move is not None and stock_move is not None else None
        result["sector_context"] = "price_index_proxy" if result.get("sector_relative_twenty_day_pp") is not None else "context_unavailable"
    return result


def snapshot_from_info(info: dict, ticker: str, today: str) -> dict:
    period = as_number(info.get("mostRecentQuarter"))
    result = {
        "sector": str(info.get("sector") or ""), "industry": str(info.get("industry") or ""),
        "fundamental_currency": str(info.get("financialCurrency") or ""),
        "fundamental_period": datetime.fromtimestamp(period, timezone.utc).date().isoformat() if period and 0 < period < 7258118400 else "",
        "fundamental_fetched": today,
        "fundamental_source": f"https://au.finance.yahoo.com/quote/{ticker}/financials/",
    }
    for field, yahoo in {"net_income": "netIncomeToCommon", "free_cash_flow": "freeCashflow", "operating_cash_flow": "operatingCashflow", "total_cash": "totalCash", "total_debt": "totalDebt"}.items():
        result[field] = as_number(info.get(yahoo))
    return result


def fundamental_snapshot(stock: yf.Ticker, ticker: str, today: str) -> dict:
    global FUNDAMENTALS
    if FUNDAMENTALS is None:
        FUNDAMENTALS = read_json(CACHE_PATH)
    cached = FUNDAMENTALS.get(ticker, {})
    fetched = pd.to_datetime(cached.get("fundamental_fetched"), errors="coerce")
    age = (pd.Timestamp(today) - fetched).days if pd.notna(fetched) else 9999
    status = "cached" if 0 <= age < SETTINGS["fundamentals_cache_days"] else "refresh_unavailable"
    if status != "cached":
        try:
            info = stock.get_info()
            if isinstance(info, dict) and any(as_number(info.get(key)) is not None for key in ("netIncomeToCommon", "totalCash", "totalDebt")):
                cached = snapshot_from_info(info, ticker, today)
                FUNDAMENTALS[ticker] = cached
                write_json(CACHE_PATH, FUNDAMENTALS)
                status = "fetched"
        except Exception:
            pass
    result = dict(cached)
    result["fundamental_status"] = status
    return result


def evidence_gate(row: dict) -> dict:
    required = ["Official filing and announcement evidence", "Debt maturities and covenant headroom", "Usable cash and facilities; stressed cash flow and committed capex", "Bear/base/bull per-share valuation", "Catalyst, review date and thesis failure conditions"]
    issues = []
    for column, label in (("market_cap_aud_approx", "Market capitalisation"), ("net_income", "Earnings"), ("free_cash_flow", "Free cash flow"), ("total_cash", "Cash"), ("total_debt", "Debt")):
        if as_number(row.get(column)) is None:
            required.append(label)
    if row.get("avoid_flags"):
        issues.append("Headline terms require verification; allegation or context is not a verified exclusion")
    if row.get("liquidity_gate") != "screen_pass_only":
        issues.append("Liquidity unverified or below research floor")
    if row.get("price_freshness") != "recent":
        issues.append("Price date needs review")
    if row.get("fundamental_status") not in {"fetched", "cached"}:
        issues.append("Fundamentals unavailable or refresh failed")
    period = pd.to_datetime(row.get("fundamental_period"), errors="coerce")
    fetched = pd.to_datetime(row.get("fundamental_fetched"), errors="coerce")
    if pd.isna(period) or pd.isna(fetched) or not 0 <= (fetched - period).days <= SETTINGS["fundamentals_max_age_days"]:
        issues.append("Financial reporting date missing or old")
    earnings, fcf = as_number(row.get("net_income")), as_number(row.get("free_cash_flow"))
    sector = row.get("sector", "")
    if sector in {"Financial Services", "Real Estate"}:
        lane = "sector_specialist"
        required.append("Sector measures: regulatory capital/credit losses for banks; FFO, LTV and valuations for property")
    elif earnings is None or fcf is None:
        lane = "unclassified_missing_data"
    elif earnings <= 0 or fcf <= 0:
        lane = "turnaround_research"
        required.append("Funded path to sustainable positive cash flow; dilution scenario")
    elif sector in {"Basic Materials", "Energy"}:
        lane = "cyclical_research"
        required.append("Mid-cycle commodity prices, cost curve and normalised earnings")
    else:
        lane = "core_research"
    return {"research_lane": lane, "research_status": "incomplete", "required_information": "; ".join(required), "investigation_flags": "; ".join(issues)}


def enrich_signal(row: dict, stock: yf.Ticker, history: pd.DataFrame, today: str) -> dict:
    row.update(fundamental_snapshot(stock, row["ticker"], today))
    row.update(market_context(history, row.get("sector", ""), today))
    row.update(evidence_gate(row))
    row["universe_lane"] = "baseline_a300"
    return row


def annotate_alerts(frame: pd.DataFrame, today: str, path: Path = STATE_PATH) -> pd.DataFrame:
    """Compare against last alerted state so small daily changes can accumulate to material ones."""
    state = read_json(path)
    out = frame.copy()
    for index, series in out.iterrows():
        row = series.to_dict()
        if row.get("signal_type") not in {"candidate", "near_miss"}:
            continue
        ticker = str(row["ticker"])
        previous = state.get(ticker, {})
        last_seen = pd.to_datetime(previous.get("last_seen"), errors="coerce")
        new = not previous or pd.isna(last_seen) or (pd.Timestamp(today) - last_seen).days > SETTINGS["episode_gap_days"]
        reasons = []
        if new:
            reasons.append("New sell-off episode")
        else:
            prior_price, price = as_number(previous.get("last_price")), as_number(row.get("last_price"))
            if prior_price and price and abs(price / prior_price - 1) * 100 >= SETTINGS["material_price_change_pct"]:
                reasons.append("Price moved at least 5% since last alert")
            for field, description in (("signal_type", "Threshold category changed"), ("avoid_flags", "Headline investigation terms changed"), ("research_lane", "Financial research lane changed"), ("investigation_flags", "Evidence/data status changed"), ("market_context", "Market regime changed")):
                if str(row.get(field) or "") != str(previous.get(field) or ""):
                    reasons.append(description)
            if abs((as_number(row.get("attention_score")) or 0) - (as_number(previous.get("attention_score")) or 0)) >= SETTINGS["material_score_change"]:
                reasons.append("Attention score changed materially")
            for field in ("net_income", "free_cash_flow", "total_cash", "total_debt"):
                old, current = as_number(previous.get(field)), as_number(row.get(field))
                if old is not None and current is not None and abs(current - old) > max(abs(old) * .1, 1):
                    reasons.append("Financial snapshot changed; verify filing")
                    break
        status = "new" if new else "changed" if reasons else "repeat"
        # A rerun on the same date preserves today's alert instead of silently consuming it.
        if status == "repeat" and previous.get("alert_date") == today:
            status, reason = previous.get("alert_status", "changed"), previous.get("alert_reason", "")
        else:
            reason = "; ".join(reasons) if reasons else "No material change since last alert"
        out.at[index, "alert_status"], out.at[index, "alert_reason"] = status, reason
        if reasons:
            fields = ("last_price", "attention_score", "signal_type", "avoid_flags", "research_lane", "investigation_flags", "market_context", "net_income", "free_cash_flow", "total_cash", "total_debt")
            previous = {key: (None if pd.isna(row.get(key)) else row.get(key)) for key in fields}
            previous.update(alert_date=today, alert_status=status, alert_reason=reason)
        previous["last_seen"] = today
        state[ticker] = previous
    write_json(path, state)
    return out
