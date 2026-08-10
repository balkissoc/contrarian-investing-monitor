# Contrarian Investing Monitor

Daily ASX contrarian-event monitor for manual review.

This tool screens a broad Australian large/mid-cap universe of roughly 300 companies for sharp falls. It is a research aide only and does not place trades or provide personal financial advice.

## What it now does

- Refreshes the screening universe from the Global X Australia 300 ETF holdings, which provides exposure to roughly the 300 largest Australian companies listed on the ASX.
- Maps each holding's SEDOL identifier to an ASX ticker using OpenFIGI rather than unreliable company-name matching.
- Caches the successfully resolved universe in `config/watchlist_asx.csv`, so a temporary external-source failure does not silently collapse the monitor back to a small watchlist.
- Pulls recent prices using Yahoo Finance via `yfinance`.
- Checks market capitalisation only after a stock has triggered a price event, reducing unnecessary data requests on the ~300-stock universe.
- Flags **candidates** that meet the sharp-drop thresholds.
- Flags **near misses** that are not yet candidates but are starting to sell off.
- Pulls recent Google News RSS headlines for triggered stocks.
- Scans headlines for avoid flags such as insolvency, fraud, trading halt, capital raising, covenant and going concern terms.
- Optionally uses OpenAI to classify each triggered stock as temporary panic, watch-only, high risk or possible permanent impairment.
- Writes dated CSV reports to `reports/`.
- Updates `reports/latest_candidates.csv`, `reports/latest_near_misses.csv`, `reports/latest_summary.md` and `reports/performance_log.csv` each run.
- Regenerates `index.html` into a graphical GitHub Pages dashboard.
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
| `reports/performance_log.csv` | Tracks later performance of triggered stocks |
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
