# Latest Contrarian Monitor Summary

Run time: 2026-08-13 22:28:29 UTC
Watchlist scanned: 295
Candidates found: 4
Near misses found: 16
Candidate report: `contrarian_candidates_2026-08-13.csv`
Near-miss report: `near_misses_2026-08-13.csv`

## Thresholds

- Minimum market capitalisation: A$500,000,000
- Candidate 1-day fall: -7.0% or worse
- Candidate 5-day fall: -12.0% or worse
- Candidate 20-day fall: -20.0% or worse
- Near-miss 1-day fall: -4.0% or worse
- Near-miss 5-day fall: -8.0% or worse
- Near-miss 20-day fall: -15.0% or worse

## Candidates

|   rank | ticker   | company                    |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                     | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:---------------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:----------------------------|:--------------|:---------------|:------------------------|
|      1 | 4DX.AX   | 4DMEDICAL LTD              |         3.91 | A$2,344,588,032         |         -5.1  |         -15.73 |             3.17 |                  0.74 | 5D <= -12.0%                |               |                | not_run                 |
|      2 | TPW.AX   | TEMPLE & WEBSTER GROUP LTD |         5.24 | A$610,704,832           |         -1.87 |         -15.48 |            -0.76 |                  1.29 | 5D <= -12.0%                |               |                | not_run                 |
|      3 | ARF.AX   | ARENA REIT                 |         2.33 | A$951,331,008           |         -0.43 |         -27.86 |           -29.39 |                  1.2  | 5D <= -12.0%; 20D <= -20.0% | default       |                | not_run                 |
|      4 | WBT.AX   | WEEBIT NANO LTD            |         4.68 | A$1,125,202,048         |         -0.43 |           4.7  |           -28.22 |                  0.86 | 20D <= -20.0%               |               |                | not_run                 |

## Near Misses

|   rank | ticker   | company                      |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                  | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:-----------------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:-------------------------|:--------------|:---------------|:------------------------|
|      1 | ASB.AX   | AUSTAL LTD                   |         4.13 | A$1,743,166,464         |         -6.77 |           7.55 |            16.34 |                  1.81 | 1D <= -4.0%              |               |                | not_run                 |
|      2 | EQR.AX   | EQ RESOURCES LTD             |         0.3  | A$1,546,536,192         |         -6.25 |          -6.25 |            22.45 |                  0.63 | 1D <= -4.0%              |               |                | not_run                 |
|      3 | ELS.AX   | ELSIGHT LTD                  |         6.49 | A$1,440,802,432         |         -5.67 |          -7.68 |           -10.48 |                  0.98 | 1D <= -4.0%              |               |                | not_run                 |
|      4 | HDN.AX   | HOMECO DAILY NEEDS REIT      |         1.21 | A$2,517,605,632         |         -5.49 |          -6.59 |            -4.37 |                  3.89 | 1D <= -4.0%              |               |                | not_run                 |
|      5 | IAG.AX   | INSURANCE AUSTRALIA GROUP    |         7.81 | A$18,259,412,992        |         -5.1  |          -8.44 |            -5.33 |                  3.45 | 1D <= -4.0%; 5D <= -8.0% |               |                | not_run                 |
|      6 | HLI.AX   | HELIA GROUP LTD              |         5.75 | A$1,575,500,032         |         -4.8  |          11.87 |             5.12 |                  1.22 | 1D <= -4.0%              |               |                | not_run                 |
|      7 | VUL.AX   | VULCAN ENERGY RESOURCES LTD  |         2.96 | A$1,416,835,840         |         -4.52 |           8.03 |             6.47 |                  1.22 | 1D <= -4.0%              |               |                | not_run                 |
|      8 | MAD.AX   | MADER GROUP LTD              |         6.82 | A$1,387,608,960         |         -2.57 |          -9.55 |           -11.2  |                  1.76 | 5D <= -8.0%              |               |                | not_run                 |
|      9 | CQE.AX   | CHARTER HALL SOCIAL INFRASTR |         2.47 | A$916,638,656           |         -2.37 |         -10.18 |            -6.79 |                  1.43 | 5D <= -8.0%              |               |                | not_run                 |
|     10 | LOV.AX   | LOVISA HOLDINGS LTD          |        24.56 | A$2,719,737,344         |         -1.8  |          -8.7  |             3.94 |                  0.73 | 5D <= -8.0%              |               |                | not_run                 |
|     11 | DRO.AX   | DRONESHIELD LTD              |         2.01 | A$1,857,422,464         |         -1.47 |         -11.84 |           -13.36 |                  1.06 | 5D <= -8.0%              |               |                | not_run                 |
|     12 | SGH.AX   | SGH LTD                      |        41.02 | A$16,695,065,600        |         -1.47 |         -11.69 |            -6.43 |                  2.41 | 5D <= -8.0%              |               |                | not_run                 |
|     13 | JDO.AX   | JUDO CAPITAL HOLDINGS LTD    |         0.92 | A$1,031,581,632         |         -1.08 |         -11.11 |            -2.13 |                  1.39 | 5D <= -8.0%              | downgrade     |                | not_run_limit_reached   |
|     14 | AOV.AX   | AMOTIV LTD                   |         6.64 | A$888,763,712           |          0    |          -9.66 |             1.53 |                  1.21 | 5D <= -8.0%              |               |                | not_run_limit_reached   |
|     15 | SEK.AX   | SEEK LTD                     |        13.91 | A$4,979,364,864         |          1.02 |          -9.5  |            -2.18 |                  2.11 | 5D <= -8.0%              |               |                | not_run_limit_reached   |
|     16 | PMV.AX   | PREMIER INVESTMENTS LTD      |        12.27 | A$1,957,917,312         |          2.59 |          -8.36 |           -11.96 |                  1.51 | 5D <= -8.0%              | downgrade     |                | not_run_limit_reached   |

## Manual review discipline

Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.

## Scan status

- below_market_cap_threshold: 4
- candidate: 4
- near_miss: 16
- no_price_drop_trigger: 271

## Latest Performance Log Snapshot

| signal_date   | ticker   | company                      | signal_type   |   signal_price |   current_price |   days_since_signal |   return_pct | last_checked   | openai_score_at_signal   | openai_classification_at_signal   |
|:--------------|:---------|:-----------------------------|:--------------|---------------:|----------------:|--------------------:|-------------:|:---------------|:-------------------------|:----------------------------------|
| 2026-08-13    | 4DX.AX   | 4DMEDICAL LTD                | candidate     |           3.91 |            3.91 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | AOV.AX   | AMOTIV LTD                   | near_miss     |           6.64 |            6.64 |                   0 |            0 | 2026-08-13     |                          | not_run_limit_reached             |
| 2026-08-13    | ARF.AX   | ARENA REIT                   | candidate     |           2.33 |            2.33 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | ASB.AX   | AUSTAL LTD                   | near_miss     |           4.13 |            4.13 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | CQE.AX   | CHARTER HALL SOCIAL INFRASTR | near_miss     |           2.47 |            2.47 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | DRO.AX   | DRONESHIELD LTD              | near_miss     |           2.01 |            2.01 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | ELS.AX   | ELSIGHT LTD                  | near_miss     |           6.49 |            6.49 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | EQR.AX   | EQ RESOURCES LTD             | near_miss     |           0.3  |            0.3  |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | HDN.AX   | HOMECO DAILY NEEDS REIT      | near_miss     |           1.21 |            1.21 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | HLI.AX   | HELIA GROUP LTD              | near_miss     |           5.75 |            5.75 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | IAG.AX   | INSURANCE AUSTRALIA GROUP    | near_miss     |           7.81 |            7.81 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | JDO.AX   | JUDO CAPITAL HOLDINGS LTD    | near_miss     |           0.92 |            0.92 |                   0 |            0 | 2026-08-13     |                          | not_run_limit_reached             |
| 2026-08-13    | LOV.AX   | LOVISA HOLDINGS LTD          | near_miss     |          24.56 |           24.56 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | MAD.AX   | MADER GROUP LTD              | near_miss     |           6.82 |            6.82 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | PMV.AX   | PREMIER INVESTMENTS LTD      | near_miss     |          12.27 |           12.27 |                   0 |            0 | 2026-08-13     |                          | not_run_limit_reached             |
| 2026-08-13    | SEK.AX   | SEEK LTD                     | near_miss     |          13.91 |           13.91 |                   0 |            0 | 2026-08-13     |                          | not_run_limit_reached             |
| 2026-08-13    | SGH.AX   | SGH LTD                      | near_miss     |          41.02 |           41.02 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | TPW.AX   | TEMPLE & WEBSTER GROUP LTD   | candidate     |           5.24 |            5.24 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | VUL.AX   | VULCAN ENERGY RESOURCES LTD  | near_miss     |           2.96 |            2.96 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
| 2026-08-13    | WBT.AX   | WEEBIT NANO LTD              | candidate     |           4.68 |            4.68 |                   0 |            0 | 2026-08-13     |                          | not_run                           |
