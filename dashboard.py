from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

import pandas as pd


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
        return "—"
    if number >= 1_000_000_000:
        return f"A${number / 1_000_000_000:.2f}b"
    if number >= 1_000_000:
        return f"A${number / 1_000_000:.0f}m"
    return f"A${number:,.0f}"


def fmt_int(value: Any) -> str:
    number = as_float(value)
    return "—" if number is None else f"{int(number):,}"


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
    status_match = re.search(r"## Scan status\s*(.*?)(?:\n## |\Z)", text, flags=re.S)
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


def classification_label(value: Any) -> str:
    text = str(value or "").strip().replace("_", " ")
    if not text or text.lower() in {"nan", "not run"}:
        return "AI not run"
    return text.title()


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
    return (
        f'<div class="movement-chip {tone}">'
        f'<span>{esc(label)}</span><strong>{fmt_pct(number)}</strong>'
        "</div>"
    )


def headline_details(row: pd.Series) -> str:
    raw = str(row.get("news_headlines", "") or "")
    headlines = [x.strip() for x in raw.split("|") if x.strip() and x.strip().lower() != "nan"]
    if not headlines:
        return ""
    items = "".join(f"<li>{esc(item)}</li>" for item in headlines[:3])
    return f'<details class="signal-details"><summary>Recent headlines</summary><ul>{items}</ul></details>'


def signal_cards(df: pd.DataFrame, *, near_miss: bool = False) -> str:
    if df.empty:
        if near_miss:
            return (
                '<div class="empty-state"><div class="empty-icon">◎</div>'
                "<strong>No near misses today</strong>"
                "<span>No shares reached the early-warning sell-off thresholds.</span></div>"
            )
        return (
            '<div class="empty-state good"><div class="empty-icon">✓</div>'
            "<strong>No qualifying contrarian candidates today</strong>"
            "<span>Nothing met the stronger price-fall thresholds in this scan.</span></div>"
        )

    cards: list[str] = []
    for _, row in df.head(12).iterrows():
        ticker = str(row.get("ticker", "") or "").replace(".AX", "")
        company = str(row.get("company", "") or "")
        rank = fmt_int(row.get("rank"))
        trigger = str(row.get("trigger", "") or "")
        avoid_flags = str(row.get("avoid_flags", "") or "").strip()
        ai_score = as_float(row.get("openai_score"))
        ai_classification = classification_label(row.get("openai_classification"))
        rationale = str(row.get("openai_rationale", "") or "").strip()
        volume = as_float(row.get("volume_spike_vs_20d"))

        score_html = (
            f'<span class="score-badge">AI {int(ai_score)}/5</span>'
            if ai_score is not None
            else '<span class="score-badge muted">AI not run</span>'
        )
        flag_html = (
            f'<span class="risk-flag">⚠ {esc(avoid_flags)}</span>'
            if avoid_flags and avoid_flags.lower() != "nan"
            else '<span class="clear-flag">No headline avoid flags</span>'
        )
        rationale_html = ""
        if rationale and rationale.lower() != "nan" and "not run" not in rationale.lower():
            rationale_html = f'<p class="rationale">{esc(rationale)}</p>'

        volume_text = f"{volume:.2f}× 20-day avg" if volume is not None else "—"

        cards.append(
            f"""
            <article class="signal-card {'near' if near_miss else 'candidate'}">
              <div class="signal-card-head">
                <div>
                  <div class="eyebrow">#{rank} · {'NEAR MISS' if near_miss else 'CANDIDATE'}</div>
                  <h3>{esc(ticker)} <span>{esc(company)}</span></h3>
                </div>
                {score_html}
              </div>
              <div class="signal-key-data">
                <div><span>Price</span><strong>{fmt_price(row.get('last_price'))}</strong></div>
                <div><span>Market cap</span><strong>{fmt_market_cap(row.get('market_cap_aud_approx'))}</strong></div>
                <div><span>Volume</span><strong>{esc(volume_text)}</strong></div>
              </div>
              <div class="movement-row">
                {movement_chip("1 day", row.get("one_day_pct"))}
                {movement_chip("5 days", row.get("five_day_pct"))}
                {movement_chip("20 days", row.get("twenty_day_pct"))}
              </div>
              <div class="trigger-line"><span>Triggered by</span><strong>{esc(trigger)}</strong></div>
              <div class="assessment-row">
                <span class="classification">{esc(ai_classification)}</span>
                {flag_html}
              </div>
              {rationale_html}
              {headline_details(row)}
            </article>
            """
        )
    return "".join(cards)


def performance_section(perf: pd.DataFrame) -> tuple[str, str]:
    if perf.empty:
        empty = (
            '<div class="empty-state"><div class="empty-icon">↗</div>'
            "<strong>No performance history yet</strong>"
            "<span>Historical signals will appear here after they are tracked.</span></div>"
        )
        return "", empty

    perf = perf.copy()

    def calculated_return(row: pd.Series) -> float | None:
        current = as_float(row.get("current_price"))
        signal = as_float(row.get("signal_price"))
        if current is not None and signal not in {None, 0}:
            return (current / signal - 1) * 100
        return as_float(row.get("return_pct"))

    perf["dashboard_return_pct"] = perf.apply(calculated_return, axis=1)
    valid = perf["dashboard_return_pct"].dropna()
    positive = int((valid > 0).sum()) if not valid.empty else 0
    average = float(valid.mean()) if not valid.empty else None
    best = float(valid.max()) if not valid.empty else None

    metrics = f"""
    <div class="mini-metrics">
      <div><span>Signals tracked</span><strong>{len(perf)}</strong></div>
      <div><span>Positive now</span><strong>{positive}</strong></div>
      <div><span>Average return</span><strong>{fmt_pct(average)}</strong></div>
      <div><span>Best return</span><strong>{fmt_pct(best)}</strong></div>
    </div>
    """

    recent = perf.sort_values(["signal_date", "ticker"], ascending=[False, True]).head(20)
    max_abs = max([abs(x) for x in recent["dashboard_return_pct"].dropna().tolist()] + [1.0])
    rows: list[str] = []
    for _, row in recent.iterrows():
        ret = as_float(row.get("dashboard_return_pct"))
        width = 0 if ret is None else min(100.0, abs(ret) / max_abs * 100)
        tone = "positive" if ret is not None and ret >= 0 else "negative"
        ticker = str(row.get("ticker", "") or "").replace(".AX", "")
        rows.append(
            f"""
            <tr>
              <td><strong>{esc(ticker)}</strong><span class="subtext">{esc(row.get('company', ''))}</span></td>
              <td>{esc(row.get('signal_date', ''))}</td>
              <td><span class="type-pill">{esc(str(row.get('signal_type', '')).replace('_', ' ').title())}</span></td>
              <td>{fmt_price(row.get('signal_price'))}</td>
              <td>{fmt_price(row.get('current_price'))}</td>
              <td class="return-cell {tone}">
                <strong>{fmt_pct(ret)}</strong>
                <div class="return-track"><div class="return-fill {tone}" style="width:{width:.1f}%"></div></div>
              </td>
              <td>{fmt_int(row.get('days_since_signal'))}</td>
              <td>{esc(row.get('last_checked', ''))}</td>
            </tr>
            """
        )

    table = (
        '<div class="table-wrap"><table class="performance-table">'
        "<thead><tr><th>Share</th><th>Signal date</th><th>Type</th><th>Signal price</th>"
        "<th>Current</th><th>Return</th><th>Days</th><th>Checked</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        '<p class="footnote">Return is recalculated for display from current price versus signal price, rather than relying on the stored CSV return column.</p>'
    )
    return metrics, table


def build_dashboard() -> str:
    summary = parse_summary()
    candidates = read_csv(CANDIDATES_PATH)
    near_misses = read_csv(NEAR_MISSES_PATH)
    performance = read_csv(PERFORMANCE_PATH)

    total = int(summary["total_scanned"])
    candidate_count = int(summary["candidates"])
    near_count = int(summary["near_misses"])
    status_counts: dict[str, int] = summary["status_counts"]
    thresholds: dict[str, str] = summary["thresholds"]

    data_issue_keys = {"market_cap_unavailable", "insufficient_price_history", "insufficient_close_history", "error"}
    data_issues = sum(int(status_counts.get(key, 0)) for key in data_issue_keys)
    no_trigger = int(status_counts.get("no_price_drop_trigger", 0))
    denominator = max(total, 1)

    labels = {
        "candidate": "Candidates",
        "near_miss": "Near misses",
        "no_price_drop_trigger": "No qualifying price fall",
        "market_cap_unavailable": "Market cap unavailable",
        "below_market_cap_threshold": "Below market-cap threshold",
        "insufficient_price_history": "Insufficient price history",
        "insufficient_close_history": "Insufficient close history",
        "error": "Data / processing error",
    }

    status_html: list[str] = []
    for key, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        width = min(100.0, count / denominator * 100)
        tone = "bad" if key in data_issue_keys else "signal" if key in {"candidate", "near_miss"} else "muted"
        status_html.append(
            f'<div class="status-row"><div class="status-label"><span>{esc(labels.get(key, key.replace("_", " ").title()))}</span>'
            f'<strong>{count}</strong></div><div class="status-track"><div class="status-fill {tone}" style="width:{width:.1f}%"></div></div></div>'
        )

    if candidate_count:
        hero_class, hero_icon = "alert", "!"
        hero_title = f"{candidate_count} candidate{'s' if candidate_count != 1 else ''} need manual review"
        hero_text = f"{near_count} additional near miss{'es' if near_count != 1 else ''} detected."
    elif near_count:
        hero_class, hero_icon = "watch", "◎"
        hero_title = "No full candidates — early warning activity detected"
        hero_text = f"{near_count} near miss{'es' if near_count != 1 else ''} reached the weaker sell-off thresholds."
    else:
        hero_class, hero_icon = "clear", "✓"
        hero_title = "No qualifying contrarian opportunities today"
        hero_text = "No security reached either the candidate or near-miss thresholds in this run."

    coverage_warning = ""
    if total < 100:
        coverage_warning = (
            '<div class="coverage-warning"><strong>⚠ Reduced scan universe.</strong> '
            f"Only {total} securities were loaded. The monitor is intended to use a broad ASX 300-style universe, "
            "so the automatic watchlist source may have fallen back to the local list.</div>"
        )

    perf_metrics, perf_table = performance_section(performance)
    min_cap_number = as_float(str(thresholds["min_market_cap"]).replace(",", ""))

    threshold_html = f"""
      <div class="threshold-grid">
        <div class="threshold-card"><span>1 DAY</span><strong>{esc(thresholds['candidate_1d'])}%</strong><small>Candidate</small><em>{esc(thresholds['near_1d'])}% near miss</em></div>
        <div class="threshold-card"><span>5 DAYS</span><strong>{esc(thresholds['candidate_5d'])}%</strong><small>Candidate</small><em>{esc(thresholds['near_5d'])}% near miss</em></div>
        <div class="threshold-card"><span>20 DAYS</span><strong>{esc(thresholds['candidate_20d'])}%</strong><small>Candidate</small><em>{esc(thresholds['near_20d'])}% near miss</em></div>
        <div class="threshold-card"><span>MIN SIZE</span><strong>{fmt_market_cap(min_cap_number)}</strong><small>Market cap</small><em>Filter before signalling</em></div>
      </div>
    """

    return f"""<!doctype html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Contrarian Investing Monitor</title>
  <style>
    * {{ box-sizing:border-box; }}
    :root {{ --ink:#102033;--muted:#64748b;--line:#dce4ee;--panel:#fff;--bg:#f3f6fa;--green:#16865c;--green-bg:#eaf8f1;--amber:#b96c05;--amber-bg:#fff7e6;--red:#c23a45;--red-bg:#fff0f1;--slate:#eef3f8; }}
    body {{ margin:0;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink); }}
    .topbar {{ background:linear-gradient(125deg,#0d2037,#153b63 62%,#175a78);color:#fff;padding:30px 0 70px; }}
    .container {{ width:min(1180px,calc(100% - 32px));margin:0 auto; }}
    .brand-row {{ display:flex;justify-content:space-between;gap:20px;align-items:flex-start; }}
    .brand {{ display:flex;gap:14px;align-items:center; }} .logo {{ width:48px;height:48px;border-radius:14px;display:grid;place-items:center;background:#ffffff1f;border:1px solid #ffffff2e;font-size:24px; }}
    h1 {{ margin:0;font-size:clamp(25px,4vw,37px);letter-spacing:-.04em; }} .brand p {{ margin:6px 0 0;color:#c7d8e8; }}
    .run-time {{ text-align:right;color:#c7d8e8;font-size:13px; }} .run-time strong {{ display:block;color:#fff;font-size:14px;margin-top:4px; }}
    .dashboard {{ margin-top:-43px;padding-bottom:48px; }} .hero {{ border-radius:18px;padding:22px 24px;display:flex;gap:18px;align-items:center;box-shadow:0 12px 34px #162a421f;border:1px solid var(--line);background:#fff; }}
    .hero-icon {{ width:52px;height:52px;flex:0 0 52px;border-radius:50%;display:grid;place-items:center;font-size:26px;font-weight:800; }}
    .hero.clear .hero-icon {{ color:var(--green);background:var(--green-bg); }} .hero.watch .hero-icon {{ color:var(--amber);background:var(--amber-bg); }} .hero.alert .hero-icon {{ color:var(--red);background:var(--red-bg); }}
    .hero h2 {{ margin:0 0 4px;font-size:21px; }} .hero p {{ margin:0;color:var(--muted); }}
    .coverage-warning {{ margin-top:14px;padding:13px 16px;border-radius:12px;background:var(--amber-bg);color:#70440a;border:1px solid #f4d79b;font-size:14px; }}
    .kpi-grid {{ display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:16px 0; }} .kpi {{ background:#fff;border:1px solid var(--line);border-radius:15px;padding:17px;box-shadow:0 4px 14px #162a420a; }}
    .kpi span {{ display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em; }} .kpi strong {{ display:block;margin-top:6px;font-size:29px;letter-spacing:-.04em; }}
    .kpi small {{ display:block;margin-top:4px;color:var(--muted);font-size:12px; }} .kpi.accent strong {{ color:var(--red); }} .kpi.watch strong {{ color:var(--amber); }} .kpi.issue strong {{ color:#7c3aed; }}
    .layout {{ display:grid;grid-template-columns:minmax(0,1.8fr) minmax(280px,.8fr);gap:16px;align-items:start; }} .panel {{ background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;margin-bottom:16px;box-shadow:0 4px 14px #162a4209; }}
    .panel-head {{ display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:16px; }} .panel h2 {{ margin:0;font-size:19px; }} .panel-head p {{ margin:4px 0 0;color:var(--muted);font-size:13px; }}
    .section-count {{ font-weight:800;font-size:12px;padding:6px 9px;border-radius:999px;background:var(--slate);color:#41556b; }} .signal-grid {{ display:grid;gap:12px; }}
    .signal-card {{ border:1px solid var(--line);border-left:5px solid var(--red);border-radius:14px;padding:16px;background:#fff; }} .signal-card.near {{ border-left-color:var(--amber); }}
    .signal-card-head {{ display:flex;justify-content:space-between;gap:16px;align-items:flex-start; }} .eyebrow {{ font-size:11px;color:var(--muted);font-weight:800;letter-spacing:.08em; }}
    .signal-card h3 {{ margin:4px 0 0;font-size:20px; }} .signal-card h3 span {{ font-size:14px;font-weight:500;color:var(--muted);margin-left:5px; }}
    .score-badge {{ background:#e7f0ff;color:#184c9f;font-size:12px;font-weight:800;padding:7px 9px;border-radius:9px;white-space:nowrap; }} .score-badge.muted {{ background:var(--slate);color:var(--muted); }}
    .signal-key-data,.movement-row {{ display:grid;grid-template-columns:repeat(3,1fr);gap:8px; }} .signal-key-data {{ margin:14px 0; }}
    .signal-key-data>div {{ background:#f8fafc;border:1px solid #e7edf4;padding:9px 10px;border-radius:10px; }} .signal-key-data span,.movement-chip span {{ display:block;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase; }}
    .movement-chip {{ padding:9px 10px;border-radius:10px;background:var(--slate); }} .movement-chip strong {{ display:block;margin-top:2px;font-size:16px; }}
    .movement-chip.severe {{ background:#ffe8ea;color:#a61f2c; }} .movement-chip.warning {{ background:#fff0e3;color:#a55300; }} .movement-chip.soft-warning {{ background:#fff8e8;color:#8a6400; }} .movement-chip.positive {{ background:var(--green-bg);color:var(--green); }}
    .trigger-line {{ display:flex;gap:8px;align-items:center;margin-top:12px;font-size:12px; }} .trigger-line span {{ color:var(--muted); }} .assessment-row {{ display:flex;flex-wrap:wrap;gap:7px;margin-top:12px; }}
    .classification,.risk-flag,.clear-flag,.type-pill {{ display:inline-flex;padding:5px 8px;border-radius:999px;font-size:11px;font-weight:750; }} .classification {{ background:#eaf2ff;color:#28599b; }} .risk-flag {{ background:var(--red-bg);color:#9f2632; }} .clear-flag {{ background:var(--green-bg);color:#176b4c; }} .type-pill {{ background:var(--slate);color:#475b70; }}
    .rationale {{ margin:12px 0 0;padding:10px 12px;border-left:3px solid #9db5d1;background:#f7f9fc;color:#42556a;font-size:13px; }} .signal-details {{ margin-top:10px;font-size:12px;color:#42556a; }}
    .empty-state {{ padding:27px 18px;text-align:center;border:1px dashed #ccd7e2;border-radius:14px;background:#fafcfe;color:var(--muted); }} .empty-state.good {{ background:#f4fbf7;border-color:#b8ddca; }} .empty-state strong,.empty-state span {{ display:block; }} .empty-state strong {{ color:var(--ink);margin:7px 0 4px; }} .empty-icon {{ font-size:28px;color:var(--green); }}
    .status-row {{ margin:12px 0; }} .status-label {{ display:flex;justify-content:space-between;gap:12px;font-size:12px;color:#465b70;margin-bottom:5px; }} .status-track,.return-track {{ height:7px;background:#edf2f7;border-radius:999px;overflow:hidden; }}
    .status-fill,.return-fill {{ height:100%;border-radius:999px;background:#8ba0b5; }} .status-fill.bad {{ background:#9b6ad3; }} .status-fill.signal {{ background:var(--amber); }}
    .threshold-grid {{ display:grid;grid-template-columns:repeat(2,1fr);gap:9px; }} .threshold-card {{ padding:13px;border-radius:12px;background:#f8fafc;border:1px solid #e5ebf1; }}
    .threshold-card span,.threshold-card small,.threshold-card em {{ display:block; }} .threshold-card span {{ color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.08em; }} .threshold-card strong {{ display:block;font-size:22px;margin:2px 0; }} .threshold-card em {{ font-size:11px;color:var(--muted);font-style:normal;margin-top:4px; }}
    .mini-metrics {{ display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:14px; }} .mini-metrics>div {{ padding:12px;background:#f8fafc;border:1px solid #e5ebf1;border-radius:11px; }} .mini-metrics span {{ display:block;font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase; }} .mini-metrics strong {{ display:block;margin-top:4px;font-size:20px; }}
    .table-wrap {{ overflow-x:auto; }} table {{ width:100%;border-collapse:collapse; }} th {{ text-align:left;padding:10px 9px;font-size:10px;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;border-bottom:1px solid var(--line);white-space:nowrap; }} td {{ padding:11px 9px;border-bottom:1px solid #edf1f5;font-size:12px;vertical-align:middle; }}
    .subtext {{ display:block;color:var(--muted);font-size:10px;margin-top:2px;max-width:150px; }} .return-cell {{ min-width:115px; }} .return-cell.positive>strong {{ color:var(--green); }} .return-cell.negative>strong {{ color:var(--red); }} .return-fill.positive {{ background:var(--green); }} .return-fill.negative {{ background:var(--red); }} .return-track {{ margin-top:5px;height:5px; }}
    .footnote,.disclaimer {{ color:var(--muted);font-size:11px;line-height:1.55; }} .actions {{ display:flex;flex-wrap:wrap;gap:8px; }} .button {{ display:inline-flex;text-decoration:none;font-size:12px;font-weight:800;border-radius:10px;padding:9px 11px;background:#e9f1ff;color:#24559e; }} .button.primary {{ background:#24599c;color:#fff; }}
    details.raw {{ margin-top:8px; }} details.raw summary {{ cursor:pointer;color:#42556a;font-weight:700;font-size:12px; }} .footer {{ text-align:center;color:var(--muted);font-size:11px;padding-top:10px; }}
    @media(max-width:900px) {{ .kpi-grid {{ grid-template-columns:repeat(2,1fr); }} .layout {{ grid-template-columns:1fr; }} .mini-metrics {{ grid-template-columns:repeat(2,1fr); }} }}
    @media(max-width:600px) {{ .brand-row {{ display:block; }} .run-time {{ text-align:left;margin-top:15px; }} .signal-key-data,.movement-row {{ grid-template-columns:1fr; }} .threshold-grid,.mini-metrics {{ grid-template-columns:1fr 1fr; }} }}
  </style>
</head>
<body>
  <header class="topbar"><div class="container brand-row">
    <div class="brand"><div class="logo">↘</div><div><h1>Contrarian Investing Monitor</h1><p>ASX sell-off radar · research dashboard</p></div></div>
    <div class="run-time">Latest automated scan<strong>{esc(summary['run_time'])}</strong></div>
  </div></header>

  <main class="container dashboard">
    <section class="hero {hero_class}"><div class="hero-icon">{hero_icon}</div><div><h2>{esc(hero_title)}</h2><p>{esc(hero_text)}</p></div></section>
    {coverage_warning}

    <section class="kpi-grid">
      <div class="kpi"><span>Universe loaded</span><strong>{total}</strong><small>shares checked this run</small></div>
      <div class="kpi accent"><span>Candidates</span><strong>{candidate_count}</strong><small>strong threshold triggers</small></div>
      <div class="kpi watch"><span>Near misses</span><strong>{near_count}</strong><small>early sell-off warnings</small></div>
      <div class="kpi issue"><span>Data issues</span><strong>{data_issues}</strong><small>could not be fully assessed</small></div>
      <div class="kpi"><span>No trigger</span><strong>{no_trigger}</strong><small>price fall below thresholds</small></div>
    </section>

    <div class="layout">
      <div>
        <section class="panel"><div class="panel-head"><div><h2>Candidate radar</h2><p>Strong sell-offs requiring manual investigation — not buy recommendations.</p></div><span class="section-count">{candidate_count}</span></div><div class="signal-grid">{signal_cards(candidates)}</div></section>
        <section class="panel"><div class="panel-head"><div><h2>Near misses</h2><p>Shares approaching the stronger contrarian thresholds.</p></div><span class="section-count">{near_count}</span></div><div class="signal-grid">{signal_cards(near_misses, near_miss=True)}</div></section>
        <section class="panel"><div class="panel-head"><div><h2>Signal performance</h2><p>How previously flagged shares have moved since the signal date.</p></div></div>{perf_metrics}{perf_table}</section>
      </div>
      <aside>
        <section class="panel"><div class="panel-head"><div><h2>Scan health</h2><p>What happened to the loaded universe.</p></div></div>{''.join(status_html) if status_html else '<p class="disclaimer">No scan-status information available.</p>'}</section>
        <section class="panel"><div class="panel-head"><div><h2>Trigger thresholds</h2><p>Automatic screening settings.</p></div></div>{threshold_html}</section>
        <section class="panel"><div class="panel-head"><div><h2>Controls & raw data</h2><p>You normally only need this dashboard.</p></div></div>
          <div class="actions"><a class="button primary" href="https://github.com/balkissoc/contrarian-investing-monitor/actions/workflows/daily.yml">Run scan manually</a><a class="button" href="reports/latest_candidates.csv">Candidates CSV</a><a class="button" href="reports/latest_near_misses.csv">Near misses CSV</a></div>
          <details class="raw"><summary>Show developer / raw report links</summary><div class="actions" style="margin-top:8px"><a class="button" href="reports/performance_log.csv">Performance CSV</a><a class="button" href="https://github.com/balkissoc/contrarian-investing-monitor/tree/main/reports">GitHub reports folder</a></div></details>
        </section>
        <section class="panel disclaimer"><strong>Research aide only.</strong><p>This monitor finds unusual price falls. It does not recommend buying or selling securities and does not verify solvency or investment suitability. Review ASX announcements, balance sheet strength, debt, liquidity, free cash flow and regulatory issues before making any investment decision.</p></section>
      </aside>
    </div>
    <div class="footer">Generated automatically by the Contrarian Investing Monitor</div>
  </main>
</body>
</html>
"""


def main() -> None:
    DASHBOARD_PATH.write_text(build_dashboard(), encoding="utf-8")
    print(f"Updated graphical dashboard: {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
