# Contrarian Investing Monitor

Daily ASX contrarian-event monitor for manual review.

This tool screens a broad ASX 300-style universe for sharp falls in companies with market capitalisation above A$500 million. It is a research aide only and does not place trades or provide personal financial advice.

## What it now does

- Attempts to load an ASX 300 watchlist automatically from a free public source.
- Falls back to `config/watchlist_asx.csv` if the automatic ASX 300 source is unavailable.
- Pulls recent prices and market capitalisation using Yahoo Finance via `yfinance`.
- Flags **candidates** that meet the sharp-drop thresholds.
- Flags **near misses** that are not yet candidates but are starting to sell off.
- Pulls recent Google News RSS headlines for triggered stocks.
- Scans headlines for avoid flags such as insolvency, fraud, trading halt, capital raising, covenant and going concern terms.
- Optionally uses OpenAI to classify each triggered stock as temporary panic, watch-only, high risk or possible permanent impairment.
- Writes dated CSV reports to `reports/`.
- Updates `reports/latest_candidates.csv`, `reports/latest_near_misses.csv`, `reports/latest_summary.md` and `reports/performance_log.csv` each run.
- Regenerates `index.html` into a simple dashboard for GitHub Pages.
- Emails the report to `balkissoc@gmail.com` if SMTP secrets are configured.
- Runs manually from GitHub Actions using `workflow_dispatch`.
- Runs automatically on ASX business days at about 6:00am Perth time.

## Thresholds

| Test | Candidate | Near miss |
| --- | ---: | ---: |
| Minimum market capitalisation | A$500,000,000 | A$500,000,000 |
| 1-day fall | -7% or worse | -4% or worse |
| 5-day fall | -12% or worse | -8% or worse |
| 20-day fall | -20% or worse | -15% or worse |

## Email setup

The workflow is already configured to send to `balkissoc@gmail.com`. To enable email, add these GitHub repository secrets:

| Secret | Value |
| --- | --- |
| `EMAIL_FROM` | Your sending Gmail address, usually `balkissoc@gmail.com` |
| `SMTP_USERNAME` | Your sending Gmail address |
| `SMTP_PASSWORD` | A Gmail app password, not your normal Gmail password |

Optional secrets:

| Secret | Default |
| --- | --- |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |

GitHub path:

`Settings > Secrets and variables > Actions > New repository secret`

## OpenAI setup

OpenAI classification is optional. Without it, the monitor still runs and produces price, news and avoid-flag reports.

To enable classification, add this GitHub repository secret:

| Secret | Value |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key |

Optional repository variable:

| Variable | Default |
| --- | --- |
| `OPENAI_MODEL` | `gpt-4o-mini` |

## Key output files

| File | Purpose |
| --- | --- |
| `reports/latest_candidates.csv` | Latest strict contrarian candidates |
| `reports/latest_near_misses.csv` | Latest near-miss sell-offs |
| `reports/latest_summary.md` | Human-readable summary |
| `reports/performance_log.csv` | Tracks later performance of triggered stocks |
| `index.html` | GitHub Pages dashboard regenerated each run |

## Run locally

```bash
pip install -r requirements.txt
python contrarian.py
```

## Manage the watchlist

The default is `AUTO_ASX300=true`, which attempts to load a broad ASX 300 watchlist automatically.

If that fails, edit:

`config/watchlist_asx.csv`

Format:

```csv
ticker,company
FMG.AX,Fortescue
QAN.AX,Qantas Airways
```

## Important

This project does not recommend, buy or sell securities. Treat output as a shortlist for manual review only. Always check ASX announcements, liquidity, debt, free cash flow, earnings quality and whether the event is temporary or permanent.