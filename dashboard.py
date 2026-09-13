from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd

from monitor_metrics import attention_band, attention_score, risk_gate

REPORTS_DIR = Path("reports")
SUMMARY_PATH = REPORTS_DIR / "latest_summary.md"
CANDIDATES_PATH = REPORTS_DIR / "latest_candidates.csv"
NEAR_MISSES_PATH = REPORTS_DIR / "latest_near_misses.csv"
PERFORMANCE_PATH = REPORTS_DIR / "performance_log.csv"
DASHBOARD_PATH = Path("index.html")


def esc(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return html.escape(str(value))


def as_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_price(value: Any) -> str:
    number = as_float(value)
    return "—" if number is None else f"A${number:,.2f}"


def fmt_pct(value: Any) -> str:
    number = as_float(value)
    return "—" if number is None else f"{number:+.2f}%"


def fmt_market_cap(value: Any) -> str:
    number = as_float(value)
    if number is None:
        return "Unverified"
    if number >= 1_000_000_000:
        return f"A${number / 1_000_000_000:.2f}b"
    if number >= 1_000_000:
        return f"A${number / 1_000_000:.0f}m"
    return f"A${number:,.0f}"


def fmt_int(value: Any) -> str:
    number = as_float(value)
    return "—" if number is None else f"{int(number):,}"


def fmt_date(value: Any) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "—"
    return pd.Timestamp(parsed).strftime("%d %b %Y")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def parse_summary() -> dict[str, Any]:
    text = SUMMARY_PATH.read_text(encoding="utf-8") if SUMMARY_PATH.exists() else ""

    def capture(pattern: str, default: str = "") -> str:
        match = re.search(pattern, text, flags=re.MULTILINE)
        return match.group(1).strip() if match else default

    def capture_int(pattern: str, default: int = 0) -> int:
        raw = capture(pattern)
        try:
            return int(raw.replace(",", ""))
        except Exception:
            return default

    thresholds = {
        "min_market_cap": capture(r"^- Minimum market capitalisation:\s*A\$([\d,]+)", "500,000,000"),
        "candidate_1d": capture(r"^- Candidate 1-day fall:\s*([-\d.]+)%", "-7"),
        "candidate_5d": capture(r"^- Candidate 5-day fall:\s*([-\d.]+)%", "-12"),
        "candidate_20d": capture(r"^- Candidate 20-day fall:\s*([-\d.]+)%", "-20"),
        "near_1d": capture(r"^- Near-miss 1-day fall:\s*([-\d.]+)%", "-4"),
        "near_5d": capture(r"^- Near-miss 5-day fall:\s*([-\d.]+)%", "-8"),
        "near_20d": capture(r"^- Near-miss 20-day fall:\s*([-\d.]+)%", "-15"),
    }

    status_counts: dict[str, int] = {}
    status_match = re.search(r"## Scan status\s*(.*?)(?:\n## |\Z)", text, flags=re.DOTALL)
    if status_match:
        for key, count in re.findall(r"^-\s*([^:]+):\s*(\d+)\s*$", status_match.group(1), flags=re.MULTILINE):
            status_counts[key.strip()] = int(count)

    return {
        "run_time": capture(r"^Run time:\s*(.+)$", "Unknown"),
        "total_scanned": capture_int(r"^Watchlist scanned:\s*(\d+)$"),
        "candidates": capture_int(r"^Candidates found:\s*(\d+)$"),
        "near_misses": capture_int(r"^Near misses found:\s*(\d+)$"),
        "thresholds": thresholds,
        "status_counts": status_counts,
    }


def run_timestamp(value: str) -> pd.Timestamp | None:
    for fmt in ("%d %b %Y %H:%M:%S AWST", "%Y-%m-%d %H:%M:%S UTC"):
        try:
            parsed = pd.Timestamp(pd.to_datetime(value, format=fmt, errors="raise"))
            if fmt.endswith("UTC"):
                parsed = parsed.tz_localize("UTC").tz_convert("Australia/Perth")
            else:
                parsed = parsed.tz_localize("Australia/Perth")
            return parsed
        except Exception:
            continue
    return None


def display_run_time(value: str) -> str:
    parsed = run_timestamp(value)
    return parsed.strftime("%d %b %Y, %H:%M AWST") if parsed is not None else value


def freshness_banner(value: str) -> str:
    parsed = run_timestamp(value)
    if parsed is None:
        return '<div class="coverage-warning" role="status">Scan freshness is unknown. Check the latest workflow run before relying on these results.</div>'
    stale = pd.Timestamp.now(tz="UTC") - parsed > pd.Timedelta(hours=96)
    return f'<div class="coverage-warning" role="status" data-freshness-at="{parsed.isoformat()}" {"" if stale else "hidden"}><strong>Stale scan.</strong> The last scan is more than 96 hours old. These are historical signals; check the workflow before relying on them.</div>'


def split_pipe(value: Any, *, keep_empty: bool = False) -> list[str]:
    text = str(value or "")
    if text.lower() == "nan":
        return []
    return [part.strip() for part in text.split("|") if keep_empty or part.strip()]


def safe_external_url(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith(("https://", "http://")):
        return html.escape(text, quote=True)
    return ""


def classification_label(value: Any) -> str:
    text = str(value or "").strip().replace("_", " ")
    if not text or text.lower() in {"nan", "not run", "not run limit reached"}:
        return ""
    return text.title()


def prepare_signals(df: pd.DataFrame, thresholds: dict[str, str]) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    candidate_thresholds = (
        float(thresholds["candidate_1d"]),
        float(thresholds["candidate_5d"]),
        float(thresholds["candidate_20d"]),
    )
    out["dashboard_score"] = out.apply(
        lambda row: attention_score(
            row.get("one_day_pct"), row.get("five_day_pct"), row.get("twenty_day_pct"),
            row.get("volume_spike_vs_20d"), candidate_thresholds=candidate_thresholds,
        ), axis=1,
    )
    out["dashboard_band"] = out["dashboard_score"].map(attention_band)
    gates = out.apply(
        lambda row: risk_gate(
            row.get("avoid_flags"), row.get("market_cap_aud_approx"),
            row.get("openai_classification"), row.get("news_headlines"),
        ), axis=1,
    )
    out["dashboard_gate"] = [gate[0] for gate in gates]
    out["dashboard_gate_label"] = [gate[1] for gate in gates]
    out = out.sort_values(
        ["dashboard_score", "one_day_pct", "five_day_pct", "twenty_day_pct"],
        ascending=[False, True, True, True], na_position="last",
    ).reset_index(drop=True)
    out["dashboard_rank"] = range(1, len(out) + 1)
    return out


def signal_history_map(performance: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if performance.empty or "ticker" not in performance.columns:
        return {}
    perf = performance.copy()
    perf["signal_date_dt"] = pd.to_datetime(perf.get("signal_date"), errors="coerce")
    result: dict[str, dict[str, Any]] = {}
    for ticker, group in perf.groupby(perf["ticker"].astype(str)):
        dates = group["signal_date_dt"].dropna().sort_values().drop_duplicates()
        if not dates.empty:
            result[ticker] = {"first_date": dates.iloc[0], "last_date": dates.iloc[-1], "signal_days": len(dates)}
    return result


def movement_chip(label: str, value: Any) -> str:
    number = as_float(value)
    if number is None:
        tone = "neutral"
    elif number <= -15:
        tone = "severe"
    elif number <= -7:
        tone = "warning"
    elif number < 0:
        tone = "soft-warning"
    else:
        tone = "positive"
    return f'<div class="movement-chip {tone}"><span>{esc(label)}</span><strong>{fmt_pct(number)}</strong></div>'


def headline_details(row: pd.Series) -> str:
    headlines = split_pipe(row.get("news_headlines", ""))
    sources = split_pipe(row.get("news_sources", ""), keep_empty=True)
    urls = split_pipe(row.get("news_urls", ""), keep_empty=True)
    published = split_pipe(row.get("news_published", ""), keep_empty=True)
    if not headlines:
        return '<p class="context-note">No recent news context was returned. Check official ASX announcements manually.</p>'
    items: list[str] = []
    for index, title in enumerate(headlines[:5]):
        source = sources[index] if index < len(sources) else ""
        url = safe_external_url(urls[index]) if index < len(urls) else ""
        title_html = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{esc(title)}</a>' if url else esc(title)
        date = fmt_date(published[index]) if index < len(published) and published[index] else ""
        attribution = " · ".join(value for value in (source, date) if value and value != "—")
        source_html = f'<span>{esc(attribution)}</span>' if attribution else ""
        items.append(f"<li>{title_html}{source_html}</li>")
    return f'<details class="signal-details"><summary>News context ({len(headlines)})</summary><ul>{"".join(items)}</ul></details>'


def signal_cards(df: pd.DataFrame, performance: pd.DataFrame, *, near_miss: bool = False) -> str:
    if df.empty:
        label = "near misses" if near_miss else "qualifying candidates"
        return f'<div class="empty-state good"><div class="empty-icon">✓</div><strong>No {label} today</strong><span>No shares reached this section\'s thresholds.</span></div>'

    history = signal_history_map(performance)
    cards: list[str] = []
    for _, row in df.iterrows():
        ticker_full = str(row.get("ticker", "") or "")
        ticker = ticker_full.replace(".AX", "")
        company = str(row.get("company", "") or "")
        rank = int(as_float(row.get("dashboard_rank")) or 0)
        trigger = str(row.get("trigger", "") or "")
        avoid_flags = str(row.get("avoid_flags", "") or "").strip()
        if avoid_flags.lower() == "nan":
            avoid_flags = ""
        ai_score = as_float(row.get("openai_score"))
        ai_classification = classification_label(row.get("openai_classification"))
        rationale = str(row.get("openai_rationale", "") or "").strip()
        if rationale.lower() == "nan" or "not run" in rationale.lower():
            rationale = ""
        volume = as_float(row.get("volume_spike_vs_20d"))
        market_cap = as_float(row.get("market_cap_aud_approx"))
        score = int(as_float(row.get("dashboard_score")) or 0)
        band = str(row.get("dashboard_band", "") or "")
        gate = str(row.get("dashboard_gate", "") or "")
        gate_label = str(row.get("dashboard_gate_label", "") or "")

        record = history.get(ticker_full, {})
        signal_days = int(record.get("signal_days", 0) or 0)
        first_date = record.get("first_date")
        history_text = f"First flagged {fmt_date(first_date)} · {signal_days} scan day{'s' if signal_days != 1 else ''}" if first_date is not None else ""
        price_date = fmt_date(row.get("price_date"))
        date_text = f"Price data {price_date}" if price_date != "—" else "Latest available close"
        if history_text:
            date_text += f" · {history_text}"

        volume_text = f"{volume:.2f}× 20-day avg" if volume is not None else "—"
        risk_class = "clear" if gate == "clear_first_pass" else "warning"
        flag_html = f'<span class="risk-detail">Flag terms: {esc(avoid_flags)}</span>' if avoid_flags else ""
        ai_html = ""
        if ai_classification:
            ai_text = f"AI {int(ai_score)}/5 · {ai_classification}" if ai_score is not None else ai_classification
            ai_html = f'<span class="classification">{esc(ai_text)}</span>'
        rationale_html = f'<p class="rationale">{esc(rationale)}</p>' if rationale else ""
        asx_url = f"https://www.asx.com.au/markets/company/{quote(ticker.lower())}"
        yahoo_url = f"https://au.finance.yahoo.com/quote/{quote(ticker_full)}"
        searchable = " ".join((ticker, company, trigger, avoid_flags, ai_classification, gate_label)).lower()
        market_cap_numeric = "" if market_cap is None else f"{market_cap:.0f}"
        volume_numeric = "" if volume is None else f"{volume:.4f}"

        cards.append(f"""
            <article class="signal-card {'near' if near_miss else 'candidate'}" id="signal-{esc(ticker.lower())}"
              data-search="{html.escape(searchable, quote=True)}" data-score="{score}"
              data-one-day="{as_float(row.get('one_day_pct')) or 0}" data-five-day="{as_float(row.get('five_day_pct')) or 0}"
              data-twenty-day="{as_float(row.get('twenty_day_pct')) or 0}" data-volume="{volume_numeric}"
              data-market-cap="{market_cap_numeric}" data-risk="{esc(gate)}" data-ticker="{esc(ticker)}">
              <div class="signal-card-head"><div class="signal-identity"><div class="eyebrow">#{rank} · {'NEAR MISS' if near_miss else 'CANDIDATE'}</div>
                <h3><a href="{asx_url}" target="_blank" rel="noopener noreferrer">{esc(ticker)}</a> <span>{esc(company)}</span></h3><p>{esc(date_text)}</p></div>
                <div class="attention-score" aria-label="Attention score {score} out of 100"><strong>{score}</strong><span>/100</span></div></div>
              <div class="badge-row"><span class="attention-band">{esc(band)}</span><span class="risk-gate {risk_class}">{esc(gate_label)}</span>{ai_html}</div>{flag_html}
              <div class="signal-key-data"><div><span>Price</span><strong>{fmt_price(row.get('last_price'))}</strong></div><div><span>Market cap</span><strong>{fmt_market_cap(market_cap)}</strong></div><div><span>Volume</span><strong>{esc(volume_text)}</strong></div></div>
              <div class="movement-row">{movement_chip('1 day', row.get('one_day_pct'))}{movement_chip('5 days', row.get('five_day_pct'))}{movement_chip('20 days', row.get('twenty_day_pct'))}</div>
              <div class="trigger-line"><span>Threshold reached</span><strong>{esc(trigger)}</strong></div>{rationale_html}{headline_details(row)}
              <div class="source-actions"><a href="{asx_url}" target="_blank" rel="noopener noreferrer">ASX company &amp; announcements ↗</a><a href="{yahoo_url}" target="_blank" rel="noopener noreferrer">Price history ↗</a></div>
            </article>""")
    return "".join(cards)


def signal_section(section_id: str, title: str, description: str, df: pd.DataFrame, performance: pd.DataFrame, *, near_miss: bool, initial_limit: int) -> str:
    return f"""
    <section class="panel signal-section" id="{section_id}" data-signal-section data-limit="{initial_limit}">
      <div class="panel-head"><div><h2>{esc(title)}</h2><p>{esc(description)}</p></div><span class="section-count">{len(df)}</span></div>
      <div class="filter-bar"><label class="search-field"><span>Search</span><input type="search" placeholder="Ticker, company, flag…" data-search-input></label>
        <label><span>Sort</span><select data-sort-select><option value="score">Attention score</option><option value="one-day">Largest 1-day fall</option><option value="five-day">Largest 5-day fall</option><option value="twenty-day">Largest 20-day fall</option><option value="volume">Highest volume</option><option value="market-cap">Largest company</option><option value="ticker">Ticker A–Z</option></select></label>
        <label><span>Risk gate</span><select data-risk-select><option value="all">All results</option><option value="flagged">Flags / missing data</option><option value="clear">No first-pass flags</option></select></label></div>
      <div class="result-status" data-result-status aria-live="polite"></div><div class="signal-grid" data-card-grid>{signal_cards(df, performance, near_miss=near_miss)}</div>
      <button class="show-more" type="button" data-show-more hidden>Show all</button>
    </section>"""


def build_episodes(performance: pd.DataFrame, *, gap_days: int = 7) -> pd.DataFrame:
    if performance.empty or "ticker" not in performance.columns:
        return pd.DataFrame()
    perf = performance.copy()
    perf["signal_date_dt"] = pd.to_datetime(perf.get("signal_date"), errors="coerce")
    perf = perf.dropna(subset=["signal_date_dt"]).sort_values(["ticker", "signal_date_dt"])
    if perf.empty:
        return pd.DataFrame()

    episode_numbers = pd.Series(index=perf.index, dtype="int64")
    for _, group in perf.groupby("ticker", sort=False):
        episode = 0
        prior_date: pd.Timestamp | None = None
        for index, signal_date in group["signal_date_dt"].items():
            if prior_date is None or (signal_date - prior_date).days > gap_days:
                episode += 1
            episode_numbers.at[index] = episode
            prior_date = signal_date
    perf["episode"] = episode_numbers.astype(int)

    rows: list[dict[str, Any]] = []
    for (ticker, episode), group in perf.groupby(["ticker", "episode"], sort=False):
        group = group.sort_values("signal_date_dt")
        anchor, latest = group.iloc[0], group.iloc[-1]
        current_price, signal_price = as_float(anchor.get("current_price")), as_float(anchor.get("signal_price"))
        stored_return = as_float(anchor.get("return_pct"))
        sessions = as_float(anchor.get("trading_sessions_since_signal"))
        history_status = str(anchor.get("history_status", "legacy"))
        if history_status == "refreshed" and sessions is not None and stored_return is not None:
            current_return = stored_return
        elif history_status == "legacy" and current_price is not None and signal_price not in {None, 0}:
            current_return = (current_price / signal_price - 1) * 100
        else:
            current_return = None
        rows.append({
            "ticker": ticker, "company": str(latest.get("company", "") or ""), "episode": episode,
            "signal_date": anchor.get("signal_date", ""), "price_date": anchor.get("price_date", ""),
            "signal_type": "candidate" if (group["signal_type"].astype(str) == "candidate").any() else "near_miss",
            "signal_price": signal_price, "current_price": current_price, "current_return_pct": current_return,
            "days_since_signal": as_float(anchor.get("days_since_signal")), "trading_sessions_since_signal": sessions,
            "return_5d_pct": as_float(anchor.get("return_5d_pct")), "return_20d_pct": as_float(anchor.get("return_20d_pct")),
            "return_60d_pct": as_float(anchor.get("return_60d_pct")), "signal_days": int(group["signal_date_dt"].nunique()),
            "last_checked": anchor.get("last_checked", ""),
            "current_price_date": anchor.get("current_price_date", ""),
            "history_status": history_status,
        })
    return pd.DataFrame(rows)


def horizon_table(episodes: pd.DataFrame) -> str:
    rows: list[str] = []
    refreshed = episodes[episodes["history_status"] == "refreshed"]
    for label, column in (("5 sessions", "return_5d_pct"), ("20 sessions", "return_20d_pct"), ("60 sessions", "return_60d_pct")):
        values = pd.to_numeric(refreshed.get(column, pd.Series(dtype=float)), errors="coerce").dropna()
        if values.empty:
            reason = "Awaiting history refresh" if refreshed.empty else "Not mature / incomplete"
            rows.append(f'<tr><td><strong>{label}</strong></td><td>0</td><td>—</td><td>—</td><td>{reason}</td></tr>')
        else:
            rows.append(f'<tr><td><strong>{label}</strong></td><td>{len(values)}</td><td>{fmt_pct(values.median())}</td><td>{fmt_pct(values.mean())}</td><td>{(values > 0).mean() * 100:.0f}%</td></tr>')
    return '<div class="cohort-block"><h3>Fixed-horizon outcomes</h3><p>Distinct sell-off episodes measured after the same number of ASX trading sessions.</p><div class="table-wrap"><table><thead><tr><th>Horizon</th><th>Episodes</th><th>Median</th><th>Average</th><th>Positive</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div></div>"


def performance_section(performance: pd.DataFrame) -> tuple[str, str, int]:
    episodes = build_episodes(performance)
    if episodes.empty:
        empty = '<div class="empty-state"><div class="empty-icon">↗</div><strong>No performance history yet</strong><span>Outcomes will appear after signals mature.</span></div>'
        return "", empty, 0

    sessions = pd.to_numeric(episodes.get("trading_sessions_since_signal"), errors="coerce")
    refreshed = episodes["history_status"] == "refreshed"
    mature = episodes[(sessions >= 5) & refreshed].copy()
    mature_returns = pd.to_numeric(mature.get("current_return_pct"), errors="coerce").dropna()
    positive_rate = float((mature_returns > 0).mean() * 100) if not mature_returns.empty else None
    median_return = float(mature_returns.median()) if not mature_returns.empty else None
    average_return = float(mature_returns.mean()) if not mature_returns.empty else None
    metrics = f"""<div class="mini-metrics"><div><span>Distinct episodes</span><strong>{len(episodes)}</strong><small>{len(performance)} daily observations deduplicated</small></div>
      <div><span>Mature episodes</span><strong>{len(mature_returns)}</strong><small>Refreshed; at least 5 sessions</small></div>
      <div><span>Positive at last close</span><strong>{'—' if positive_rate is None else f'{positive_rate:.0f}%'} </strong><small>Among mature episodes</small></div>
      <div><span>Median return</span><strong>{fmt_pct(median_return)}</strong><small>Average {fmt_pct(average_return)}</small></div></div>"""

    recent = episodes.sort_values(["signal_date", "ticker"], ascending=[False, True]).head(15)
    rows: list[str] = []
    for _, row in recent.iterrows():
        ret = as_float(row.get("current_return_pct")); tone = "positive" if ret is not None and ret >= 0 else "negative"
        ticker = str(row.get("ticker", "") or "").replace(".AX", "")
        rows.append(f'<tr><td><strong>{esc(ticker)}</strong><span class="subtext">{esc(row.get("company", ""))}</span></td><td>{fmt_date(row.get("signal_date"))}</td><td><span class="type-pill">{esc(str(row.get("signal_type", "")).replace("_", " ").title())}</span></td><td>{fmt_price(row.get("signal_price"))}</td><td class="return-cell {tone}"><strong>{fmt_pct(ret)}</strong></td><td>{fmt_int(row.get("trading_sessions_since_signal"))}</td><td>{fmt_int(row.get("signal_days"))}</td></tr>')
    excluded = int((~refreshed).sum())
    warning = f'<p class="coverage-warning">{excluded} episodes await a successful adjusted-history refresh and are excluded from aggregate outcomes. Legacy table returns, where shown, are price-only estimates.</p>' if excluded else ""
    as_of = pd.to_datetime(episodes.loc[refreshed, "current_price_date"], errors="coerce").dropna()
    dates_note = f' Latest available return dates: {fmt_date(as_of.min())}–{fmt_date(as_of.max())}.' if not as_of.empty else ""
    table = warning + horizon_table(episodes) + '<div class="cohort-block"><h3>Recent distinct episodes</h3><div class="table-wrap"><table class="performance-table"><thead><tr><th>Share</th><th>First signal</th><th>Peak type</th><th>Signal price</th><th>Return at last close</th><th>Sessions</th><th>Signal days</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div><p class="footnote">Signals for the same ticker separated by no more than seven calendar days are grouped into one episode; this does not make episodes statistically independent. Aggregates use adjusted closes after a successful refresh. Legacy anchor dates are inferred from the signal date. Returns exclude fees and are descriptive, not a tradable back-test or benchmark-relative result.' + dates_note + '</p></div>'
    return metrics, table, len(episodes)


CSS = """
*{box-sizing:border-box}:root{--ink:#122033;--muted:#65758a;--line:#dce4ed;--panel:#fff;--bg:#f2f5f9;--green:#137657;--green-bg:#eaf7f1;--amber:#a76006;--amber-bg:#fff5df;--red:#bd3341;--red-bg:#fff0f2;--violet:#6e4bd3;--slate:#edf2f7;--shadow:0 10px 28px rgba(25,43,65,.08)}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink);line-height:1.45}a{color:inherit}[hidden]{display:none!important}.topbar{background:radial-gradient(circle at 88% 20%,#1c7190 0,transparent 32%),linear-gradient(125deg,#091a30,#123a5e 68%,#13506a);color:#fff;padding:28px 0 72px}.container{width:min(1220px,calc(100% - 32px));margin:0 auto}.brand-row{display:flex;justify-content:space-between;gap:24px;align-items:flex-start}.brand{display:flex;gap:14px;align-items:center}.logo{width:50px;height:50px;border-radius:15px;display:grid;place-items:center;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.18);font-size:24px}.brand h1{margin:0;font-size:clamp(25px,4vw,38px);letter-spacing:-.045em}.brand p{margin:5px 0 0;color:#c9d8e7}.header-meta{text-align:right;color:#c9d8e7;font-size:12px}.header-meta strong{display:block;color:#fff;font-size:14px;margin-top:4px}.header-meta span{display:block;margin-top:2px}.top-nav{display:flex;justify-content:flex-end;gap:8px;margin-top:12px}.top-nav a{text-decoration:none;padding:5px 8px;border-radius:7px;color:#d9e7f2;font-size:11px}.top-nav a:hover{background:rgba(255,255,255,.1)}.dashboard{margin-top:-45px;padding-bottom:46px}.hero{border-radius:19px;padding:22px 24px;display:grid;grid-template-columns:auto 1fr auto;gap:18px;align-items:center;box-shadow:0 15px 38px rgba(12,30,51,.16);border:1px solid var(--line);background:#fff}.hero-icon{width:52px;height:52px;border-radius:50%;display:grid;place-items:center;font-size:25px;font-weight:850}.hero.alert .hero-icon{color:var(--red);background:var(--red-bg)}.hero.watch .hero-icon{color:var(--amber);background:var(--amber-bg)}.hero.clear .hero-icon{color:var(--green);background:var(--green-bg)}.hero h2{margin:0 0 3px;font-size:21px}.hero p{margin:0;color:var(--muted)}.hero-priority{min-width:180px;border-left:1px solid var(--line);padding-left:20px}.hero-priority span,.hero-priority small{display:block;color:var(--muted);font-size:11px}.hero-priority strong{display:block;font-size:19px;margin:2px 0}.hero-priority a{text-decoration:none}.coverage-warning{margin-top:14px;padding:13px 16px;border-radius:12px;background:var(--amber-bg);color:#70440a;border:1px solid #f1d493;font-size:13px}.kpi-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:16px 0}.kpi{background:#fff;border:1px solid var(--line);border-radius:15px;padding:16px;box-shadow:0 4px 14px rgba(22,42,66,.04)}.kpi span{display:block;color:var(--muted);font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.075em}.kpi strong{display:block;margin-top:5px;font-size:28px;letter-spacing:-.04em}.kpi small{display:block;margin-top:3px;color:var(--muted);font-size:11px}.kpi.accent strong{color:var(--red)}.kpi.watch strong{color:var(--amber)}.kpi.priority strong{color:#17638a}.kpi.issue strong{color:var(--violet)}.layout{display:grid;grid-template-columns:minmax(0,1.85fr) minmax(290px,.72fr);gap:16px;align-items:start}.panel{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:0 4px 14px rgba(22,42,66,.035)}.panel-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:15px}.panel h2{margin:0;font-size:19px;letter-spacing:-.015em}.panel-head p,.cohort-block>p{margin:4px 0 0;color:var(--muted);font-size:12px}.section-count{font-weight:850;font-size:12px;padding:6px 9px;border-radius:999px;background:var(--slate);color:#41556b}.filter-bar{display:grid;grid-template-columns:1.25fr 1fr .9fr;gap:9px;padding:11px;background:#f7f9fc;border:1px solid #e6ecf2;border-radius:12px;margin-bottom:8px}.filter-bar label>span{display:block;font-size:9px;text-transform:uppercase;letter-spacing:.07em;font-weight:850;color:var(--muted);margin:0 0 4px 2px}.filter-bar input,.filter-bar select{width:100%;border:1px solid #ccd7e3;border-radius:9px;background:#fff;padding:9px 10px;color:var(--ink);font:inherit;font-size:12px;min-height:38px}.filter-bar input:focus,.filter-bar select:focus,.show-more:focus{outline:3px solid rgba(23,99,138,.2);border-color:#17638a}.result-status{min-height:22px;text-align:right;color:var(--muted);font-size:11px;padding:2px}.signal-grid{display:grid;gap:12px}.signal-card{border:1px solid var(--line);border-left:5px solid var(--red);border-radius:14px;padding:16px;background:#fff;transition:box-shadow .18s ease,transform .18s ease}.signal-card:hover{box-shadow:var(--shadow);transform:translateY(-1px)}.signal-card.near{border-left-color:var(--amber)}.signal-card-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.signal-identity{min-width:0}.eyebrow{font-size:10px;color:var(--muted);font-weight:850;letter-spacing:.085em}.signal-card h3{margin:3px 0 0;font-size:19px}.signal-card h3>a{text-decoration:none}.signal-card h3>a:hover{text-decoration:underline}.signal-card h3 span{font-size:13px;font-weight:550;color:var(--muted);margin-left:4px}.signal-identity p{margin:3px 0 0;color:var(--muted);font-size:10px}.attention-score{width:58px;height:58px;flex:0 0 58px;border-radius:50%;display:grid;place-content:center;text-align:center;background:linear-gradient(#fff,#fff) padding-box,linear-gradient(145deg,#1c7393,#79b5c9) border-box;border:4px solid transparent}.attention-score strong{font-size:20px;line-height:17px}.attention-score span{font-size:9px;color:var(--muted)}.badge-row{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}.attention-band,.risk-gate,.classification,.type-pill{display:inline-flex;padding:5px 8px;border-radius:999px;font-size:10px;font-weight:780}.attention-band{background:#e8f2f8;color:#135578}.risk-gate.clear{background:var(--green-bg);color:#176b4c}.risk-gate.warning{background:var(--red-bg);color:#9f2632}.classification{background:#f0edff;color:#5b42aa}.risk-detail{display:block;margin-top:7px;color:#9f2632;font-size:11px;font-weight:650}.signal-key-data,.movement-row{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.signal-key-data{margin:13px 0 8px}.signal-key-data>div{background:#f8fafc;border:1px solid #e7edf4;padding:9px 10px;border-radius:10px}.signal-key-data span,.movement-chip span{display:block;color:var(--muted);font-size:9px;font-weight:850;text-transform:uppercase;letter-spacing:.035em}.movement-chip{padding:9px 10px;border-radius:10px;background:var(--slate)}.movement-chip strong{display:block;margin-top:2px;font-size:15px}.movement-chip.severe{background:#ffe8eb;color:#a61f2c}.movement-chip.warning{background:#fff0e3;color:#a55300}.movement-chip.soft-warning{background:#fff8e8;color:#856000}.movement-chip.positive{background:var(--green-bg);color:var(--green)}.trigger-line{display:flex;gap:8px;align-items:center;margin-top:11px;font-size:11px}.trigger-line span{color:var(--muted)}.rationale{margin:11px 0 0;padding:9px 11px;border-left:3px solid #9db5d1;background:#f7f9fc;color:#42556a;font-size:12px}.signal-details{margin-top:9px;font-size:11px;color:#42556a}.signal-details summary{cursor:pointer;font-weight:750}.signal-details ul{padding-left:18px;margin:8px 0 0}.signal-details li{margin:6px 0}.signal-details li span{display:block;color:var(--muted);font-size:9px}.context-note{margin:9px 0 0;color:var(--muted);font-size:10px}.source-actions{display:flex;flex-wrap:wrap;gap:14px;margin-top:11px;padding-top:10px;border-top:1px solid #edf1f5}.source-actions a{color:#245f87;font-size:10px;font-weight:750;text-decoration:none}.source-actions a:hover{text-decoration:underline}.show-more{width:100%;margin-top:12px;border:1px solid #cbd7e3;background:#f8fafc;color:#31556f;border-radius:10px;padding:10px;font-weight:800;cursor:pointer}.empty-state{padding:27px 18px;text-align:center;border:1px dashed #ccd7e2;border-radius:14px;background:#fafcfe;color:var(--muted)}.empty-state.good{background:#f4fbf7;border-color:#b8ddca}.empty-state strong,.empty-state span{display:block}.empty-state strong{color:var(--ink);margin:7px 0 4px}.empty-icon{font-size:27px;color:var(--green)}.status-row{margin:11px 0}.status-label{display:flex;justify-content:space-between;gap:12px;font-size:11px;color:#465b70;margin-bottom:5px}.status-track{height:7px;background:#edf2f7;border-radius:999px;overflow:hidden}.status-fill{height:100%;border-radius:999px;background:#8ba0b5}.status-fill.bad{background:#9368c6}.status-fill.signal{background:var(--amber)}.threshold-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.threshold-card{padding:12px;border-radius:11px;background:#f8fafc;border:1px solid #e5ebf1}.threshold-card span,.threshold-card small,.threshold-card em{display:block}.threshold-card span{color:var(--muted);font-size:9px;font-weight:850;letter-spacing:.08em}.threshold-card strong{display:block;font-size:20px;margin:2px 0}.threshold-card small{font-size:10px}.threshold-card em{font-size:10px;color:var(--muted);font-style:normal;margin-top:3px}.method-list{margin:0;padding-left:17px;color:#42556a;font-size:11px}.method-list li{margin:7px 0}.methodology-details summary{cursor:pointer;font-size:11px;font-weight:800;color:#31556f}.methodology-details p{font-size:10px;color:var(--muted)}.mini-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:15px}.mini-metrics>div{padding:12px;background:#f8fafc;border:1px solid #e5ebf1;border-radius:11px}.mini-metrics span{display:block;font-size:9px;color:var(--muted);font-weight:850;text-transform:uppercase}.mini-metrics strong{display:block;margin-top:3px;font-size:19px}.mini-metrics small{display:block;margin-top:3px;color:var(--muted);font-size:9px}.cohort-block{margin-top:16px}.cohort-block h3{margin:0;font-size:14px}.table-wrap{overflow-x:auto;margin-top:8px}table{width:100%;border-collapse:collapse}th{text-align:left;padding:9px 8px;font-size:9px;text-transform:uppercase;color:var(--muted);letter-spacing:.055em;border-bottom:1px solid var(--line);white-space:nowrap}td{padding:10px 8px;border-bottom:1px solid #edf1f5;font-size:11px;vertical-align:middle}.subtext{display:block;color:var(--muted);font-size:9px;margin-top:2px;max-width:150px}.return-cell.positive>strong{color:var(--green)}.return-cell.negative>strong{color:var(--red)}.type-pill{background:var(--slate);color:#475b70}.footnote,.disclaimer{color:var(--muted);font-size:10px;line-height:1.55}.actions{display:flex;flex-wrap:wrap;gap:7px}.button{display:inline-flex;text-decoration:none;font-size:11px;font-weight:800;border-radius:9px;padding:8px 10px;background:#e9f1ff;color:#24559e}.button.primary{background:#245f87;color:#fff}details.raw{margin-top:8px}details.raw summary{cursor:pointer;color:#42556a;font-weight:700;font-size:11px}.footer{text-align:center;color:var(--muted);font-size:10px;padding-top:10px}@media(max-width:960px){.kpi-grid{grid-template-columns:repeat(3,1fr)}.layout{grid-template-columns:1fr}.mini-metrics{grid-template-columns:repeat(2,1fr)}.top-nav{display:none}}@media(max-width:640px){.container{width:min(100% - 20px,1220px)}.topbar{padding-top:20px}.brand-row{display:block}.header-meta{text-align:left;margin:15px 0 0 64px}.hero{grid-template-columns:auto 1fr;padding:17px}.hero-priority{grid-column:2;border-left:0;padding-left:0}.kpi-grid{grid-template-columns:repeat(2,1fr)}.kpi:last-child{grid-column:1/-1}.panel{padding:15px}.filter-bar{grid-template-columns:1fr}.signal-key-data,.movement-row{grid-template-columns:1fr 1fr}.signal-key-data>div:last-child,.movement-row>div:last-child{grid-column:1/-1}.signal-card h3 span{display:block;margin:2px 0 0}.mini-metrics{grid-template-columns:1fr 1fr}.threshold-grid{grid-template-columns:1fr 1fr}}@media(max-width:390px){.brand{align-items:flex-start}.logo{width:44px;height:44px}.header-meta{margin-left:58px}.kpi-grid,.mini-metrics{grid-template-columns:1fr}.kpi:last-child{grid-column:auto}.signal-key-data,.movement-row{grid-template-columns:1fr}.signal-key-data>div:last-child,.movement-row>div:last-child{grid-column:auto}}
"""


JAVASCRIPT = """
document.querySelectorAll('[data-freshness-at]').forEach((banner) => {
  const check = () => { banner.hidden = Date.now() - Date.parse(banner.dataset.freshnessAt) <= 96 * 60 * 60 * 1000; };
  check(); setInterval(check, 60000);
});
document.querySelectorAll('[data-signal-section]').forEach((section) => {
  const grid = section.querySelector('[data-card-grid]');
  const cards = Array.from(grid.querySelectorAll('.signal-card'));
  const search = section.querySelector('[data-search-input]');
  const sort = section.querySelector('[data-sort-select]');
  const risk = section.querySelector('[data-risk-select]');
  const status = section.querySelector('[data-result-status]');
  const more = section.querySelector('[data-show-more]');
  const limit = Number(section.dataset.limit || 8);
  let expanded = false;
  const number = (card, key, fallback) => { const parsed = Number(card.dataset[key]); return Number.isFinite(parsed) ? parsed : fallback; };
  const compare = (a, b) => {
    switch (sort.value) {
      case 'one-day': return number(a, 'oneDay', 0) - number(b, 'oneDay', 0);
      case 'five-day': return number(a, 'fiveDay', 0) - number(b, 'fiveDay', 0);
      case 'twenty-day': return number(a, 'twentyDay', 0) - number(b, 'twentyDay', 0);
      case 'volume': return number(b, 'volume', -1) - number(a, 'volume', -1);
      case 'market-cap': return number(b, 'marketCap', -1) - number(a, 'marketCap', -1);
      case 'ticker': return a.dataset.ticker.localeCompare(b.dataset.ticker);
      default: return number(b, 'score', 0) - number(a, 'score', 0);
    }
  };
  const render = () => {
    const query = search.value.trim().toLowerCase(); const choice = risk.value;
    const matching = cards.filter((card) => { const textMatch = !query || card.dataset.search.includes(query); const isClear = card.dataset.risk === 'clear_first_pass'; return textMatch && (choice === 'all' || (choice === 'clear' && isClear) || (choice === 'flagged' && !isClear)); }).sort(compare);
    matching.forEach((card) => grid.appendChild(card)); cards.forEach((card) => { card.hidden = true; });
    const shown = expanded ? matching : matching.slice(0, limit); shown.forEach((card) => { card.hidden = false; });
    status.textContent = matching.length === cards.length ? `${shown.length} of ${cards.length} shown` : `${shown.length} of ${matching.length} matching shown`;
    more.hidden = matching.length <= limit; more.textContent = expanded ? `Show top ${limit}` : `Show all ${matching.length}`;
    if (matching.length === 0) status.textContent = 'No matching results';
  };
  [search, sort, risk].forEach((control) => control.addEventListener(control === search ? 'input' : 'change', () => { expanded = false; render(); }));
  more.addEventListener('click', () => { expanded = !expanded; render(); }); render();
});
"""


def build_dashboard() -> str:
    summary = parse_summary(); thresholds: dict[str, str] = summary["thresholds"]
    candidates = prepare_signals(read_csv(CANDIDATES_PATH), thresholds)
    near_misses = prepare_signals(read_csv(NEAR_MISSES_PATH), thresholds)
    performance = read_csv(PERFORMANCE_PATH)
    total = int(summary["total_scanned"]); candidate_count = len(candidates); near_count = len(near_misses)
    status_counts: dict[str, int] = summary["status_counts"]; denominator = max(total, 1)
    priority_count = int((candidates.get("dashboard_score", pd.Series(dtype=float)) >= 80).sum()) if not candidates.empty else 0
    current_signals = pd.concat([candidates, near_misses], ignore_index=True)
    quality_warnings = int((current_signals.get("dashboard_gate", pd.Series(dtype=str)) != "clear_first_pass").sum()) if not current_signals.empty else 0
    data_issue_keys = {"market_cap_unavailable", "insufficient_price_history", "insufficient_close_history", "error"}
    technical_issues = sum(int(status_counts.get(key, 0)) for key in data_issue_keys); no_trigger = int(status_counts.get("no_price_drop_trigger", 0)); below_cap = int(status_counts.get("below_market_cap_threshold", 0))
    labels = {"candidate":"Candidates","near_miss":"Near misses","no_price_drop_trigger":"No qualifying price fall","market_cap_unavailable":"Market cap unavailable","below_market_cap_threshold":"Below market-cap threshold","insufficient_price_history":"Insufficient price history","insufficient_close_history":"Insufficient close history","error":"Data / processing error"}
    status_html: list[str] = []
    for key, count in sorted(status_counts.items(), key=lambda item: item[1], reverse=True):
        width = min(100.0, count / denominator * 100); tone = "bad" if key in data_issue_keys else "signal" if key in {"candidate", "near_miss"} else "muted"
        status_html.append(f'<div class="status-row"><div class="status-label"><span>{esc(labels.get(key, key.replace("_", " ").title()))}</span><strong>{count}</strong></div><div class="status-track"><div class="status-fill {tone}" style="width:{width:.1f}%"></div></div></div>')

    if candidate_count:
        hero_class, hero_icon, hero_title = "alert", "!", f"{candidate_count} candidate{'s' if candidate_count != 1 else ''} require triage"
        hero_text = f"Ranked by price-event strength; {near_count} additional near miss{'es' if near_count != 1 else ''} detected."
    elif near_count:
        hero_class, hero_icon, hero_title = "watch", "◎", "No full candidates — early warning activity detected"; hero_text = f"{near_count} near miss{'es' if near_count != 1 else ''} reached the weaker thresholds."
    else:
        hero_class, hero_icon, hero_title, hero_text = "clear", "✓", "No qualifying price events today", "No security reached either the candidate or near-miss thresholds."
    top_priority_html = '<span>Highest attention</span><strong>None today</strong><small>Awaiting a qualifying event</small>'
    if not candidates.empty:
        top = candidates.iloc[0]; top_ticker = str(top.get("ticker", "")).replace(".AX", "")
        top_priority_html = f'<span>Highest attention</span><strong><a href="#signal-{esc(top_ticker.lower())}">{esc(top_ticker)} · {int(top["dashboard_score"])}/100</a></strong><small>Review urgency, not investment quality</small>'
    coverage_warning = ""
    if total < 250:
        coverage_warning = f'<div class="coverage-warning"><strong>⚠ Reduced universe.</strong> Only {total} securities were loaded; the intended A300-style range is 250–380.</div>'
    elif technical_issues:
        coverage_warning = f'<div class="coverage-warning"><strong>⚠ Partial data.</strong> {technical_issues} securities could not be fully assessed in this run.</div>'
    if candidate_count != summary["candidates"] or near_count != summary["near_misses"]:
        coverage_warning += '<div class="coverage-warning"><strong>Report mismatch.</strong> The CSV result counts differ from the scan summary. Do not interpret missing results as an all-clear.</div>'
    coverage_warning += freshness_banner(str(summary["run_time"]))
    price_dates = pd.to_datetime(current_signals.get("price_date"), errors="coerce") if not current_signals.empty and "price_date" in current_signals else pd.Series(dtype="datetime64[ns]")
    latest_price_date = fmt_date(price_dates.max()) if not price_dates.dropna().empty else "Not recorded in legacy data"
    run_time = display_run_time(str(summary["run_time"])); perf_metrics, perf_table, episode_count = performance_section(performance)
    min_cap_number = as_float(str(thresholds["min_market_cap"]).replace(",", ""))
    threshold_html = f'<div class="threshold-grid"><div class="threshold-card"><span>1 DAY</span><strong>{esc(thresholds["candidate_1d"])}%</strong><small>Candidate</small><em>{esc(thresholds["near_1d"])}% near miss</em></div><div class="threshold-card"><span>5 DAYS</span><strong>{esc(thresholds["candidate_5d"])}%</strong><small>Candidate</small><em>{esc(thresholds["near_5d"])}% near miss</em></div><div class="threshold-card"><span>20 DAYS</span><strong>{esc(thresholds["candidate_20d"])}%</strong><small>Candidate</small><em>{esc(thresholds["near_20d"])}% near miss</em></div><div class="threshold-card"><span>MIN SIZE</span><strong>{fmt_market_cap(min_cap_number)}</strong><small>Market cap</small><em>A300 fallback flagged if unverified</em></div></div>'

    return f'''<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="Automated ASX contrarian price-event monitor for manual research triage."><title>Contrarian Investing Monitor</title><style>{CSS}</style></head><body>
  <header class="topbar"><div class="container brand-row"><div class="brand"><div class="logo">↘</div><div><h1>Contrarian Investing Monitor</h1><p>ASX price-event radar · research triage</p></div></div><div class="header-meta">Latest automated scan<strong>{esc(run_time)}</strong><span>Latest displayed price: {esc(latest_price_date)}</span><nav class="top-nav" aria-label="Dashboard sections"><a href="#candidates">Candidates</a><a href="#near-misses">Near misses</a><a href="#performance">Performance</a></nav></div></div></header>
  <main class="container dashboard"><section class="hero {hero_class}"><div class="hero-icon">{hero_icon}</div><div><h2>{esc(hero_title)}</h2><p>{esc(hero_text)}</p></div><div class="hero-priority">{top_priority_html}</div></section>{coverage_warning}
    <section class="kpi-grid" aria-label="Scan summary"><div class="kpi"><span>Universe</span><strong>{total}</strong><small>A300-style shares scanned</small></div><div class="kpi accent"><span>Candidates</span><strong>{candidate_count}</strong><small>strong threshold events</small></div><div class="kpi watch"><span>Near misses</span><strong>{near_count}</strong><small>early warning events</small></div><div class="kpi priority"><span>Immediate review</span><strong>{priority_count}</strong><small>attention score 80+</small></div><div class="kpi issue"><span>Quality warnings</span><strong>{quality_warnings}</strong><small>risk or missing-data gates</small></div></section>
    <div class="layout"><div>{signal_section("candidates", "Candidate radar", "Complete candidate list, ranked by transparent review urgency — not expected return.", candidates, performance, near_miss=False, initial_limit=8)}{signal_section("near-misses", "Near misses", "Early sell-offs approaching the stronger candidate thresholds.", near_misses, performance, near_miss=True, initial_limit=6)}<section class="panel" id="performance"><div class="panel-head"><div><h2>Signal performance</h2><p>Daily repeats condensed into distinct sell-off episodes with maturity-aware results.</p></div><span class="section-count">{episode_count}</span></div>{perf_metrics}{perf_table}</section></div>
      <aside><section class="panel"><div class="panel-head"><div><h2>Scan health</h2><p>Exclusive outcomes across the loaded universe.</p></div></div>{''.join(status_html) if status_html else '<p class="disclaimer">No scan-status information available.</p>'}<p class="footnote">No trigger: {no_trigger}. Below size threshold: {below_cap}. Quality warnings can overlap candidate and near-miss counts.</p></section><section class="panel"><div class="panel-head"><div><h2>Trigger thresholds</h2><p>Automatic price-event settings.</p></div></div>{threshold_html}</section>
      <section class="panel" id="methodology"><div class="panel-head"><div><h2>How to read the score</h2><p>Attention score ≠ investment score.</p></div></div><ol class="method-list"><li><strong>55 points:</strong> strongest fall relative to its candidate threshold.</li><li><strong>25 points:</strong> breadth across 1-, 5- and 20-day windows.</li><li><strong>10 points:</strong> confirmation across multiple candidate windows.</li><li><strong>10 points:</strong> volume above the 20-day average.</li></ol><details class="methodology-details"><summary>Risk-gate limitations</summary><p>Headline flags and automated classifications are only a first pass. “No first-pass flags” does not verify solvency, governance, valuation or that a shock is temporary.</p></details></section>
      <section class="panel"><div class="panel-head"><div><h2>Controls &amp; data</h2><p>Run the workflow or inspect source records.</p></div></div><div class="actions"><a class="button primary" href="https://github.com/balkissoc/contrarian-investing-monitor/actions/workflows/daily.yml">Run scan manually</a><a class="button" href="reports/latest_candidates.csv">Candidates CSV</a><a class="button" href="reports/latest_near_misses.csv">Near misses CSV</a></div><details class="raw"><summary>Developer / history links</summary><div class="actions" style="margin-top:8px"><a class="button" href="reports/performance_log.csv">Performance CSV</a><a class="button" href="https://github.com/balkissoc/contrarian-investing-monitor/tree/main/reports">Reports folder</a></div></details></section>
      <section class="panel disclaimer"><strong>Research aide only.</strong><p>This monitor finds unusual price falls. It does not recommend securities or verify investment suitability. Before acting, review official ASX announcements, the cause of the fall, balance-sheet strength, debt maturities, liquidity, cash flow, governance and valuation.</p></section></aside></div><div class="footer">Generated automatically · Performance figures are descriptive, not a back-test or forecast</div></main><script>{JAVASCRIPT}</script></body></html>'''


def main() -> None:
    DASHBOARD_PATH.write_text(build_dashboard(), encoding="utf-8")
    print(f"Updated graphical dashboard: {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
