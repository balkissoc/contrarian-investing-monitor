# Contrarian Investing Monitor

Daily ASX price-drop monitor for manual review.

This tool screens a configurable ASX watchlist for sharp falls in companies with market capitalisation above A$500 million. It is a research aide only and does not place trades or provide personal financial advice.

## What it does

- Screens ASX tickers from `config/watchlist_asx.csv`.
- Pulls recent prices and market capitalisation using Yahoo Finance via `yfinance`.
- Flags stocks that meet any configured sharp-drop threshold.
- Saves a CSV report to `reports/`.
- Runs manually from GitHub Actions using `workflow_dispatch`.
- Runs automatically on ASX business days at about 6:00am Perth time.

## Thresholds

| Test | Default |
| --- | ---: |
| Minimum market capitalisation | A$500,000,000 |
| 1-day fall | -7% or worse |
| 5-day fall | -12% or worse |
| 20-day fall | -20% or worse |

## Run locally

```bash
pip install -r requirements.txt
python contrarian.py
```

## Important

This project does not recommend, buy or sell securities. Treat output as a shortlist for manual review only.
