# Contrarian Investing Monitor

Daily ASX contrarian-event monitor for manual review.

This tool screens a broad Australian large/mid-cap universe of roughly 300 companies for sharp falls. It is a research aide only and does not place trades or provide personal financial advice.

## Evidence-based hybrid research upgrade

The dashboard now separates **discovery, evidence, valuation and validation**. A price fall or clean headline scan cannot produce an investment approval. All automatically generated signals remain **research incomplete**.

The illustrative model uses **A$50,000** and a **20% target in each year**: A$1,000 would need to become A$1,200. The default measurement basis includes dividends and trading costs, before tax. This is an ambition, not an assured return or demonstrated strategy. A 20% long-term average would not establish success in each individual year.

### Daily research workflow

1. Filter **New / changed** events. Repeats remain on the radar and in CSV history. **Systemic sell-off** is a separate filter so market-wide panics are not lost.
2. Inspect 3/6/12-month context, volatility units, market-relative returns, liquidity and the dated financial snapshot.
3. Select **Research this company**. Record an official filing, the market expectation you disagree with, funding under stress, normalised valuation, catalyst, next review and evidence that would disprove the thesis.
4. Save a dated review. The notebook distinguishes **incomplete**, **blocked by your evidence** and **checklist complete — decision remains manual**.
5. Optionally queue a **paper order**. No broker is connected. It can fill only at the first later market close observed when this browser reopens the dashboard; it cannot fill at the already-known signal close.

The notebook and paper portfolio use browser storage on that device. They are **not uploaded to GitHub**. Use **Export notebook** for backups and **Import notebook** on another device. Import replaces the local notebook after a confirmation. Storage failures are visible, and unreadable existing data is not silently overwritten. Do not commit exported notebooks to this public repository.

### Hybrid lanes and provisional controls

| Lane | Research requirement | Model treatment |
| --- | --- | --- |
| Core | Positive provider earnings and free cash flow, followed by evidence of sustainability | 5% initial; normal 8–10%; 15% single-company review ceiling |
| Cyclical | Positive current figures plus mid-cycle commodity assumptions, costs and normalised cash flow | Core limits only after the additional cyclical review |
| Turnaround | Loss or negative free cash flow; funded milestones, stressed liquidity and dilution case | 3% maximum each; 15% combined |
| Sector specialist | Banks/financials and property require appropriate capital, credit-loss, FFO/LTV measures | Manual sector assessment; no generic debt/EBITDA pass |
| Missing evidence | Financial fields cannot establish a lane | Incomplete, never promoted by absence of data |

These lanes are research routing, not verified quality ratings. The hybrid is a testable choice that keeps speculative underwriting separate; its superiority has not been established. Never infer sustainable profits from one trailing provider figure.

At A$50,000, the initial core model position is A$2,500, a normal researched position A$4,000–5,000, and the single-company review ceiling A$7,500. No leverage; maximum 20 holdings is a ceiling, not a target. Shared economic exposures above 30% prompt review, even across different stock-market sectors. Price appreciation can breach limits and creates a review warning; the tool does not automatically sell.

Paper purchases check cash, whole shares, holdings count, concentration, turnaround exposure and liquidity again at the assumed fill. Initial core orders are capped at 5%; adding requires a new saved review and cannot exceed 15%. The provisional turnover floor is A$1m median daily value and the order participation limit is 1%. The turnover estimate uses adjusted close × volume. These are configurable hypotheses, not proven optimal thresholds.

Add only after re-underwriting, never because the price fell. Reduce or sell when the thesis fails, financing changes materially or remaining expected return is inadequate. The intended holding period over one year does not override those rules.

### Funding and valuation calculations

The 24-month aggregate stress calculation is usable cash + drawable facilities + two years of stressed operating cash flow − debt due − committed capex − minimum cash buffer. All inputs must use the same currency and units. Operating cash flow is after interest and before capex; avoid double counting. A positive total does not prove funds are available at each maturity, so a separately evidenced maturity schedule and covenant review are mandatory.

Bear/base/bull valuations are entered per share, including a future diluted share count where relevant. The calculator shows total return, annualised planning return and the maximum entry price for the 20% hurdle. It assumes dividends are held as cash to the end, no reinvestment, and proportional costs on entry/exit prices. Flat brokerage is accounted for separately in the paper ledger. Multi-year annualisation is not proof of meeting an each-year target.

For example, a price recovery from A$70 to A$100 over three years is about 12.62% annually before costs/dividends. The maximum entry for 20% annualised growth to A$100 over three years would be about A$57.87 on that simplified basis. A previous high is not a valuation.

### Data and trigger improvements

- Price history now spans two years. Context uses 63/126/252 sessions as approximate 3/6/12 months.
- The original fixed fall thresholds remain the baseline. Additional volatility watches require at least 3 standard deviations and minimum falls of 3%/5%/10% over 1/5/20 sessions. Volatility and mean are estimated from up to 60 daily log returns **before** each event window, with at least 40 observations. Volatility units are descriptive and are not normal-distribution probabilities.
- Market context uses exact matching start/end sessions of the A300 ETF adjusted history. A market fall of 4% over five sessions or 8% over twenty marks the systemic queue. No missing endpoint is forward-filled.
- Yahoo sector price-index symbols are best-effort context. Missing coverage is shown. Sector indices exclude distributions, so comparisons with adjusted stock returns are approximate and are not alpha; market comparisons use adjusted prices on both sides.
- Triggered companies receive cached Yahoo earnings, cash flow, cash/debt, sector, reporting currency and dates. The cache lasts three days. Failure retains the last facts with a failed-refresh status. Unknown or old reporting periods are investigation flags. No currency conversion or fabricated financial values are used.
- Google News RSS is limited to the last 30 days where publication dates are available. Headline terms indicate an investigation, not confirmed fraud/insolvency or an automatic exclusion. Optional AI is labelled as opinion and cannot clear funding or valuation evidence.
- Alerts compare with the last alerted state: new episode, threshold/risk/lane/regime changes, at least 5% cumulative price change, 15 score points, or a 10% change in a financial field. Repeated same-day runs retain that day's alerts. First adoption establishes the alert baseline; new does not imply a historically independent opportunity.

### Honest forward validation

`reports/event_validation.csv` records distinct episodes using the **type and score known at the first signal**. It uses the first available close strictly after the scan date, with a seven-calendar-day gap limit; entry gaps, stale prices and unavailable histories are explicit. Fixed horizons are 5/20/60 sessions and **12/24/36 calendar months**. These are independent event observations, not a portfolio backtest.

Matched A300 ETF adjusted returns provide a broad Australian total-return proxy, including fund expenses. Both sides receive the same provisional 40 bps round-trip cost assumption. Cost is split equally between entry and exit. Distributions follow the provider's adjusted-price convention; no raw-price fallback is substituted when adjusted history is missing. Excess return is a percentage-point difference, not risk-adjusted alpha. The dashboard reports mature sample sizes and score-band outcomes, and separates legacy episodes from new episodes under the recorded settings version.

The private paper ledger includes uninvested cash, explicit brokerage/slippage, positions, dividends and splits. Dividends are credited on the provider's ex-date rather than actual payment date; no franking credits or reinvestment. Missing/stale held prices suppress total performance. Portfolio drawdown uses observations made when the browser is opened, so intraperiod falls may be missed. Its calendar-year target table separates complete years, partial years and missing year-end observations; open the dashboard at year end to record a boundary. Partial years are never annualised into a claimed 20% success. This editable local model is not an independently verified investment record.

**Historical validation is not complete.** A rigorous test needs company membership and financial information as it was known on each historical decision date — “point-in-time” data — plus failed/delisted companies and their actual proceeds. Current Yahoo facts cannot reconstruct that. Daily universe snapshots and signal financial snapshots are retained from this upgrade, but a surviving current universe cannot be used to claim an unbiased historical backtest. Separate out-of-sample periods and multiple market regimes are required before interpreting any return target as supported. A few successful trades are unnecessary for this forward process and do not establish an edge.

### Universe experiments

The existing A300-style universe and A$500m baseline floor remain in production. `config/experimental_watchlist.csv` and `experimental_universe_enabled` provide a separate, default-off A$100m+ experiment. Populate only with explicitly researched ASX names before enabling it. Experimental observations go to `reports/experimental_candidates.csv`; they never inflate the main candidate list, its emails or its measured outcomes. A broader universe has not yet been shown to improve results.

### Configuration, validation and public records

`config/research_settings.json` versions all research settings. Bump its version before prospectively changing a tested rule. The historical data, decisions and original rule version must be retained; do not repeatedly tune settings to make past results look attractive.

Additional public outputs: `reports/fundamental_cache.json`, `reports/alert_state.json`, `reports/latest_prices.json`, `reports/validation_summary.json`, `reports/event_validation.csv` and dated `reports/universe_YYYY-MM-DD.csv`. They contain public market data and model methodology, not the private notebook.

```bash
python -m unittest discover -s tests -v
node --test tests/research_core.test.cjs
```

Tests cover the no-lookahead entry rule, benchmark date alignment, missing-data treatment, hybrid routing, cumulative alert changes, costs, funding gaps, position limits, cash, dividends and splits. Top-level Python dependencies are pinned to the tested versions. Workflow code pushes rebuild the site without sending an extra email; scheduled/manual scans retain the existing email delivery.

Research references: [A300 fund and index objective](https://www.globalxetfs.com.au/funds/a300/), [yfinance data API](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html), [IEA analysis of demand, supply and critical-mineral prices](https://www.iea.org/reports/global-critical-minerals-outlook-2025/executive-summary).

## What it now does

- Refreshes the screening universe from the Global X Australia 300 ETF holdings, which provides exposure to roughly the 300 largest Australian companies listed on the ASX.
- Maps each holding's SEDOL identifier to an ASX ticker using OpenFIGI rather than unreliable company-name matching.
- Caches the successfully resolved universe in `config/watchlist_asx.csv`, so a temporary external-source failure does not silently collapse the monitor back to a small watchlist.
- Pulls recent prices using Yahoo Finance via `yfinance`.
- Checks market capitalisation only after a stock has triggered a price event, reducing unnecessary data requests on the ~300-stock universe.
- Flags **candidates** that meet the sharp-drop thresholds.
- Flags **near misses** that are not yet candidates but are starting to sell off.
- Assigns a transparent **0–100 attention score** based on price-event strength, multi-window confirmation and unusual volume. The score ranks manual-review urgency; it is not a valuation or buy score.
- Applies a separate first-pass risk/data gate for headline risk terms, unverified market capitalisation, missing news context and high-risk AI classifications.
- Pulls recent Google News RSS headlines for triggered stocks.
- Scans headlines for avoid flags such as insolvency, fraud, trading halt, capital raising, covenant and going concern terms.
- Optionally uses OpenAI to classify each triggered stock as temporary panic, watch-only, high risk or possible permanent impairment.
- Writes dated CSV reports to `reports/`.
- Updates `reports/latest_candidates.csv`, `reports/latest_near_misses.csv`, `reports/latest_summary.md` and `reports/performance_log.csv` each run.
- Regenerates `index.html` into a searchable, sortable and mobile-responsive GitHub Pages dashboard, with every result available rather than a truncated top list.
- Records the actual market-data date separately from the AWST scan date.
- Condenses repeated daily signals into distinct sell-off episodes for dashboard reporting.
- Measures mature episodes at fixed 5, 20 and 60 ASX-session horizons and refreshes performance prices in batches to reduce stale records and unnecessary requests.
- Emails `balkissoc@gmail.com` a concise scan summary and a direct link to the graphical dashboard when the Gmail App Password secret is configured.
- Runs manually from GitHub Actions using `workflow_dispatch`.
- Runs automatically on ASX business days at about 6:00am Perth time.

## Universe

The monitor is intended to scan **roughly 300 Australian listed companies**, not to reproduce the official S&P/ASX 300 constituent list exactly.

The current primary universe source is the Global X Australia 300 ETF (A300), which tracks the FTSE Australia 300 Index. The workflow validates that the resolved universe contains between 250 and 380 unique ASX tickers before replacing the cached watchlist.

The latest successfully resolved universe is retained in:

`config/watchlist_asx.csv`

SEDOL-to-ticker resolutions are cached in:

`config/a300_resolution_cache.csv`

The universe refresh diagnostic is written to:

`reports/universe_refresh.log`

## Thresholds

| Test | Candidate | Near miss |
| --- | ---: | ---: |
| Minimum market capitalisation | A$500,000,000 | A$500,000,000 |
| 1-day fall | -7% or worse | -4% or worse |
| 5-day fall | -12% or worse | -8% or worse |
| 20-day fall | -20% or worse | -15% or worse |

## Attention score and risk gate

The attention score is deliberately mechanical and reproducible:

| Component | Maximum points |
| --- | ---: |
| Strongest fall relative to its candidate threshold | 55 |
| Breadth across 1-day, 5-day and 20-day windows | 25 |
| Confirmation across multiple candidate windows | 10 |
| Volume above the 20-day average | 10 |

The score does **not** assess valuation, solvency, balance-sheet strength or expected return. Those matters remain manual-review gates. Signals for the same ticker separated by no more than seven calendar days are treated as one sell-off episode in the dashboard so that a prolonged decline is not counted as a new independent event every day.

Performance aggregates include only successfully refreshed adjusted-price histories. Unavailable histories are retained in the CSV, visibly flagged, and excluded from aggregate outcomes. Legacy signal-close dates are inferred; 5/20/60-session outcomes are descriptive, not a tradable back-test, benchmark comparison or forecast. Episode grouping does not establish statistical independence.

The dashboard displays scan times in Perth time, records price-session dates for new signals, and warns when a scan is more than 96 hours old. Search, sorting and “Show all” controls expose every candidate and near miss. Scheduled and manual runs retain email delivery; code-push runs refresh the site without sending an extra email.

## Email setup

The workflow is already configured to send a link to the graphical dashboard to:

`balkissoc@gmail.com`

Only **one GitHub repository secret** is required:

| Secret | Value |
| --- | --- |
| `SMTP_PASSWORD` | A Gmail App Password for `balkissoc@gmail.com` — not the normal Google account password |

The workflow already supplies:

- SMTP username: `balkissoc@gmail.com`
- sender: `balkissoc@gmail.com`
- SMTP host: `smtp.gmail.com`
- SMTP port: `587`
- dashboard URL: `https://balkissoc.github.io/contrarian-investing-monitor/`

GitHub path to add the secret:

`Settings > Secrets and variables > Actions > New repository secret`

Google requires 2-Step Verification before an App Password can be created. Do not put the normal Gmail password in GitHub.

## Optional OpenFIGI API key

OpenFIGI mapping works without an API key at its public rate limit. The first mapping run can therefore take a few minutes. Resolved SEDOLs are cached, making later daily refreshes much faster.

An optional secret can be added if desired:

| Secret | Value |
| --- | --- |
| `OPENFIGI_API_KEY` | OpenFIGI API key |

## OpenAI setup

OpenAI classification is optional. Without it, the monitor still runs and produces price, news and avoid-flag reports.

To enable classification, add this GitHub repository secret:

| Secret | Value |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key |

The workflow currently uses `gpt-4o-mini` when classification is enabled.

## Key output files

| File | Purpose |
| --- | --- |
| `index.html` | Graphical GitHub Pages dashboard regenerated each run |
| `reports/latest_candidates.csv` | Latest strict contrarian candidates |
| `reports/latest_near_misses.csv` | Latest near-miss sell-offs |
| `reports/latest_summary.md` | Human-readable summary |
| `reports/performance_log.csv` | Tracks current and fixed 5/20/60-session outcomes of triggered stocks |
| `reports/universe_refresh.log` | Records how the ~300-stock universe was built |
| `config/watchlist_asx.csv` | Cached resolved screening universe |

## Run locally

```bash
pip install -r requirements.txt
python universe.py
AUTO_ASX300=false python run_monitor.py
python dashboard.py
```

On Windows PowerShell, set `AUTO_ASX300=false` as an environment variable before running `python run_monitor.py`.

## Important

This project does not recommend, buy or sell securities. Treat output as a shortlist for manual review only. Always check ASX announcements, liquidity, debt, free cash flow, earnings quality and whether the event is temporary or permanent.
