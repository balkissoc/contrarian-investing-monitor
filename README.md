# Contrarian Investing Monitor

Daily ASX price-drop monitor for manual review.

This tool screens a configurable ASX watchlist for sharp falls in companies with market capitalisation above A$500 million. It is a research aide only and does not place trades or provide personal financial advice.

## What it does

- Screens ASX tickers from `config/watchlist_asx.csv`.
- Pulls recent prices and market capitalisation using Yahoo Finance via `yfinance`.
- Flags stocks that meet any configured sharp-drop threshold.
- Saves dated CSV reports to `reports/`.
- Updates `reports/latest_candidates.csv` and `reports/latest_summary.md` each run.
- Shows the latest summary inside the GitHub Actions run summary.
- Emails the report to `balkissoc@gmail.com` if SMTP secrets are configured.
- Runs manually from GitHub Actions using `workflow_dispatch`.
- Runs automatically on ASX business days at about 6:00am Perth time.

## Thresholds

| Test | Default |
| --- | ---: |
| Minimum market capitalisation | A$500,000,000 |
| 1-day fall | -7% or worse |
| 5-day fall | -12% or worse |
| 20-day fall | -20% or worse |

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

## Run locally

```bash
pip install -r requirements.txt
python contrarian.py
```

## Manage the watchlist

Edit:

`config/watchlist_asx.csv`

Format:

```csv
ticker,company
FMG.AX,Fortescue
QAN.AX,Qantas Airways
```

## Important

This project does not recommend, buy or sell securities. Treat output as a shortlist for manual review only.
