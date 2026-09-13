"""Server-rendered research context and browser-local notebook shell."""
from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

from research import ROOT, SETTINGS, read_json


def clean(value) -> str:
    return "" if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)) else str(value)


def esc(value) -> str:
    return html.escape(clean(value), quote=True)


def number(value, suffix="", digits=1) -> str:
    try:
        return f"{float(value):,.{digits}f}{suffix}" if pd.notna(value) else "Not available"
    except (ValueError, TypeError):
        return "Not available"


def card_context(row) -> str:
    if not clean(row.get("settings_version")):
        return '<p class="research-incomplete">Research enrichment awaits the next scan.</p>'
    lane = clean(row.get("research_lane")).replace("_", " ").title()
    alert = clean(row.get("alert_status")) or "Not assessed"
    market = clean(row.get("market_context")).replace("_", " ")
    status = clean(row.get("fundamental_status"))
    currency = clean(row.get("fundamental_currency")) or "Currency unknown"
    missing = esc(row.get("required_information"))
    facts = "".join(f'<div><span>{label}</span><strong>{number(row.get(field), digits=0)}</strong></div>' for label, field in (("Net income", "net_income"), ("Free cash flow", "free_cash_flow"), ("Cash", "total_cash"), ("Total debt", "total_debt")))
    return f'''<div class="research-context"><div class="badge-row"><span class="event-badge {esc(alert)}">{esc(alert.title())}</span><span>{esc(lane)}</span><strong>Research incomplete</strong></div>
      <p class="footnote">{esc(row.get('alert_reason'))}</p><div class="context-grid"><div><span>3 / 6 / 12 months</span><strong>{number(row.get('three_month_pct'), '%')} / {number(row.get('six_month_pct'), '%')} / {number(row.get('twelve_month_pct'), '%')}</strong></div>
      <div><span>5D / 20D vs market</span><strong>{number(row.get('market_relative_five_day_pp'), ' pp')} / {number(row.get('market_relative_twenty_day_pp'), ' pp')}</strong></div>
      <div><span>1D / 5D / 20D volatility units</span><strong>{number(row.get('one_day_z'), 'σ')} / {number(row.get('five_day_z'), 'σ')} / {number(row.get('twenty_day_z'), 'σ')}</strong></div>
      <div><span>Median daily turnover · approx.</span><strong>A${number(row.get('median_turnover_20d_aud'), digits=0)}</strong></div></div>
      <p class="footnote">Market: {esc(market)} · Prices: {esc(row.get('price_freshness'))} · Liquidity: {esc(row.get('liquidity_gate'))}</p>
      <details><summary>Financial evidence and sector context</summary><p>Yahoo snapshot · {esc(currency)} · latest reported quarter {esc(row.get('fundamental_period')) or 'unknown'} · retrieved {esc(row.get('fundamental_fetched')) or 'unavailable'} ({esc(status)}). Earnings/cash flow are provider aggregates; cash/debt are balance-sheet snapshots. Verify periods and accounting in filings.</p>
      <div class="context-grid">{facts}</div><p>Sector: {esc(row.get('sector')) or 'unknown'} · {esc(row.get('industry'))}. 5D / 20D relative to {esc(row.get('sector_benchmark')) or 'unavailable'}: {number(row.get('sector_relative_five_day_pp'), ' pp')} / {number(row.get('sector_relative_twenty_day_pp'), ' pp')}. Sector indices exclude dividends; this approximate comparison includes stock distributions and is not alpha.</p>
      <p><strong>Investigation:</strong> {esc(row.get('investigation_flags')) or 'No automated issues recorded; mandatory evidence is still missing.'}</p><p><strong>Required information:</strong> {missing}</p></details>
      <button class="research-open button" type="button" data-research-ticker="{esc(row.get('ticker'))}">Research this company</button></div>'''


def field(key: str, label: str, kind="text", default="") -> str:
    control = f'<textarea id="r-{key}" name="{key}" rows="2"></textarea>' if kind == "textarea" else f'<input id="r-{key}" name="{key}" type="{kind}" value="{esc(default)}" {"step=any" if kind == "number" else ""}>'
    return f'<label for="r-{key}">{label}{control}</label>'


def choice(key, label, options) -> str:
    return f'<label for="r-{key}">{label}<select id="r-{key}" name="{key}">' + ''.join(f'<option value="{esc(value)}">{esc(text)}</option>' for value, text in options) + '</select></label>'


def workspace(signals: pd.DataFrame) -> str:
    s = SETTINGS
    counts = signals.get("alert_status", pd.Series(dtype=str)).value_counts()
    systemic = int((signals.get("market_context", pd.Series(dtype=str)) == "systemic_selloff").sum())
    options = [("unclassified_missing_data", "Unclassified — missing evidence"), ("core_research", "Core — established business"), ("cyclical_research", "Cyclical — normalise the cycle"), ("turnaround_research", "Turnaround — restricted allocation"), ("sector_specialist", "Bank / property / specialist")]
    verify = [("unknown", "Not checked"), ("pass", "Checked against evidence"), ("fail", "Verified concern")]
    funding = ''.join(field(k, label, "number") for k, label in (("cash", "Usable cash now"), ("facilities", "Committed, drawable facilities"), ("debtDue", "Debt due within 24 months"), ("stressOcf", "Annual stressed operating cash flow, after interest, before capex"), ("capex", "Committed capex over 24 months"), ("buffer", "Minimum cash buffer")))
    scenarios = ''.join(field(k, label, "number", value) for k, label, value in (("entry", "Assumed entry price A$", ""), ("bear", "Bear terminal price A$", ""), ("base", "Base terminal price A$", ""), ("bull", "Bull terminal price A$", ""), ("dividend", "Annual cash dividend per share A$", ""), ("years", "Scenario horizon in years", "1"), ("costBps", "Round-trip spread / slippage cost, basis points", s["simulation_round_trip_cost_bps"])))
    signals_data = json.loads(signals.to_json(orient="records"))
    payload = {"settings": s, "signals": signals_data, "marks": read_json(ROOT / "reports/latest_prices.json")}
    encoded = json.dumps(payload, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'''<section class="panel research-workspace" id="research"><div class="panel-head"><div><h2>Research &amp; decision workspace</h2><p>Find the expectation that is wrong. Prove the business can survive. Price the outcome per share.</p></div><span class="event-badge">Hybrid research</span></div>
      <div class="research-summary"><div><strong>{int(counts.get('new', 0)) + int(counts.get('changed', 0))}</strong><span>new / changed events</span></div><div><strong>{int(counts.get('repeat', 0))}</strong><span>repeats kept on radar</span></div><div><strong>{systemic}</strong><span>in a systemic sell-off</span></div><div><strong>{s['annual_target_pct']}%</strong><span>each-year ambition · unvalidated</span></div></div>
      <p>The model starts with A${s['model_capital_aud']:,.0f}. A 20% year would end at A${s['model_capital_aud'] * 1.2:,.0f} without contributions or withdrawals. Losses and years below target remain possible. Default return basis includes dividends and costs, before tax.</p>
      <details id="research-notebook"><summary>Open private research notebook and scenario calculator</summary><p>Notes and the paper portfolio stay in this browser on this device. They are not sent to GitHub. Export a backup before clearing browser data or changing devices. Anyone using this browser profile can read them.</p>
      <div class="notebook-actions"><button type="button" id="research-export" class="button">Export notebook</button><label class="button">Import notebook<input type="file" id="research-import" accept="application/json,.json"></label></div><p id="research-storage" role="status"></p>
      <form id="research-form"><div class="research-form-grid">{field('ticker', 'ASX ticker, e.g. FMG.AX')}{choice('lane', 'Research lane', options)}</div><button type="button" id="research-load" class="button">Load company notes</button>
      <fieldset><legend>1. What is the market getting wrong?</legend><div class="research-form-grid">{field('thesis', 'Investment thesis and event', 'textarea')}{field('expectations', 'Market expectation versus your evidence', 'textarea')}{field('source', 'Official ASX announcement / company filing URL', 'url')}{field('evidenceDate', 'Financial evidence checked as of', 'date')}{field('exposures', 'Shared exposures, comma separated: China, iron ore, fuel…')}{choice('liquidity', 'Liquidity and intended order size checked', verify)}</div></fieldset>
      <fieldset><legend>2. Can it survive the adverse case?</legend><p>Enter all funding values in the same currency and units, e.g. USD millions. An aggregate cash surplus cannot prove cash is available when each debt falls due. Do not double-count debt service or capex.</p><div class="research-form-grid">{field('currency', 'Funding currency and units')}{funding}{choice('covenants', 'Covenants', verify + [('na', 'No covenants — evidenced')])}{choice('governance', 'Governance and solvency evidence', verify)}{choice('timeline', 'Funding sufficient at every maturity date', verify)}{field('fundingNotes', 'Maturity schedule, covenants, facility restrictions and stress assumptions', 'textarea')}{field('sectorNotes', 'Mid-cycle prices / cost curve, or bank capital / property FFO and LTV', 'textarea')}{field('turnaround', 'Turnaround funding, milestones and diluted share count', 'textarea')}</div></fieldset>
      <fieldset><legend>3. Is the return worth the risk?</legend><div class="research-form-grid">{scenarios}{field('valuationBasis', 'Normalised earnings / cash flow, multiple, dilution and sources supporting each scenario', 'textarea')}{field('catalyst', 'Measurable catalyst and milestones', 'textarea')}{field('reviewDate', 'Next review date', 'date')}{field('falsify', 'What evidence would make you sell or abandon the thesis?', 'textarea')}</div><p class="footnote">Dividend cash is held to the end with no reinvestment. Costs apply to entry and exit prices. Flat brokerage belongs in the paper ledger. A multi-year annualised scenario does not establish 20% in each intervening year.</p></fieldset>
      <div id="research-calculation" aria-live="polite"></div><button type="submit" class="button primary">Save dated research review</button></form>
      <details class="research-rules"><summary>Buying, adding and selling rules</summary><ul><li>Core initial position: {s['initial_position_pct']}% (A${s['model_capital_aud'] * s['initial_position_pct'] / 100:,.0f}); normal researched position: 8–{s['normal_position_pct']}%; single-company review ceiling: {s['max_position_pct']}%.</li><li>Turnarounds: maximum {s['turnaround_position_pct']}% each and {s['turnaround_total_pct']}% combined, with a funded path to recovery. Cyclicals require normalised commodity assumptions; banks and property need sector measures.</li><li>Re-underwrite before adding. A lower price alone is insufficient. Review shared economic exposure above {s['shared_exposure_review_pct']}%. Maximum {s['max_holdings']} holdings is a ceiling, not a target. No leverage.</li><li>Sell or reduce when the thesis fails, financing risk rises or expected return becomes inadequate. A planned holding period over one year does not oblige holding a broken thesis.</li></ul></details>
      <section id="paper-portfolio"><h3>Forward paper portfolio</h3><p>Illustrative orders only. Queue an order after saving a complete research review; it uses the first later market close seen when this dashboard is reopened. If you return late, the fill is late. No broker connection or actual trades.</p><div class="research-form-grid"><label>Action<select id="paper-side"><option>BUY</option><option>SELL</option></select></label><label>Whole shares<input type="number" id="paper-units" min="1" step="1"></label><label>Brokerage per order A$<input type="number" id="paper-fee" value="5" min="0" step="any"></label><label>Slippage per side (bps)<input type="number" id="paper-slippage" value="20" min="0" step="any"></label><label>Decision / sell reason<input id="paper-reason"></label></div><button type="button" id="paper-order" class="button">Queue paper order for selected company</button><div id="paper-status" role="status"></div><div id="paper-results"></div><p class="footnote">Distributions are credited on the provider's ex-date, with no franking credits or reinvestment. Splits use provider events. These assumptions differ from actual brokerage cash timing. Missing or stale held-share prices suppress portfolio return. Drawdown uses observed visits, not every trading day. Paper history is private and editable via import; it is not independently verified.</p></section></details>
      <details><summary>Risk / trap scan and required information</summary><ul><li>Growing demand can coexist with oversupply. Test the supply curve and producer economics.</li><li>A temporary conflict or restriction can still leave lasting debt, dilution or lost earnings.</li><li>The previous share-price high is not fair value. Value each scenario using normalised cash flow and the future share count.</li><li>News keywords and AI opinions cannot clear a company for investment. Verify allegations, dates and official disclosures.</li></ul><p>Required for a decision: the official filing, maturity-by-maturity funding test, evidence-based valuation and falsification conditions. Your old trades are not needed. A rigorous historical test additionally needs archived company lists and financial reports exactly as they were known on each decision date. Today's information must never be inserted into old decisions.</p><p>The broader A$100m+ experiment is configured separately and disabled until a researched watchlist is supplied. It cannot populate the main candidate queue. <a href="reports/experimental_candidates.csv">Experimental observations</a>. The hybrid and all numerical limits are hypotheses to test, not proven optimal settings.</p></details></section><script type="application/json" id="research-data">{encoded}</script>'''


def validation_panel() -> str:
    data = read_json(ROOT / "reports/validation_summary.json")
    horizons = data.get("horizons", {})
    rows = ''.join(f'<tr><td>{label}</td><td>{horizons.get(key, {}).get("mature", 0)}</td><td>{horizons.get(key, {}).get("matched", 0)}</td><td>{number(horizons.get(key, {}).get("median_net_pct"), "%")}</td><td>{number(horizons.get(key, {}).get("median_excess_pp"), " pp")}</td></tr>' for key, label in (("5d", "5 sessions"), ("20d", "20 sessions"), ("60d", "60 sessions"), ("12m", "12 months"), ("24m", "24 months"), ("36m", "36 months")))
    scores = ''.join(f'<tr><td>{esc(key)}</td><td>{value.get("matched_20d", 0)}</td><td>{number(value.get("median_excess_pp"), " pp")}</td></tr>' for key, value in data.get("score_bands", {}).items())
    return f'''<section class="panel" id="validation"><div class="panel-head"><div><h2>Is the approach working?</h2><p>Prospective validation begins with new episodes under these settings.</p></div><span class="event-badge">Not yet validated</span></div><p><strong>{data.get('prospective_events', 0)} prospective episodes</strong> · {data.get('legacy_events', 0)} legacy episodes kept separate · {data.get('unavailable_or_stale', 0)} histories unavailable, stale or requiring review.</p><div class="table-wrap"><table><thead><tr><th>Horizon</th><th>Mature</th><th>Matched benchmark</th><th>Median after model costs</th><th>Median excess return</th></tr></thead><tbody>{rows}</tbody></table></div><p class="footnote">First close strictly after the scan date; adjusted returns with distributions, {SETTINGS['simulation_round_trip_cost_bps']} bps round-trip model costs on both stock and benchmark. A300 ETF adjusted returns approximate a broad Australian total return benchmark, including its fund expenses. Excess return is percentage-point difference, not risk-adjusted alpha. Independent event observations do not account for portfolio cash, overlap or position limits; they are not portfolio returns.</p>
      <details><summary>Attention-score validation and evidence gaps</summary><p>The overlapping price windows and 55/25/10/10 weights are unvalidated judgement choices. Compare future outcomes by score band before treating a high score as useful.</p><div class="table-wrap"><table><thead><tr><th>Score at first signal</th><th>Matched 20-session outcomes</th><th>Median excess return</th></tr></thead><tbody>{scores}</tbody></table></div><p>Pre-registered rule version: {esc(SETTINGS['version'])}. Never fill a historical gap with current fundamentals. Failed and delisted histories remain counted as missing; their outcomes are not assumed to be zero. Comprehensive delisting proceeds and historical membership are not available from this feed. A multi-regime, out-of-sample historical test remains uncompleted. No result here demonstrates 20% in every year.</p></details><a class="button" href="reports/event_validation.csv">Download event observations</a></section>'''
