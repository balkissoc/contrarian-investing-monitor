# Latest Contrarian Monitor Summary

Run time: 2026-08-11 22:28:46 UTC
Watchlist scanned: 295
Candidates found: 6
Near misses found: 5
Candidate report: `contrarian_candidates_2026-08-11.csv`
Near-miss report: `near_misses_2026-08-11.csv`

## Thresholds

- Minimum market capitalisation: A$500,000,000
- Candidate 1-day fall: -7.0% or worse
- Candidate 5-day fall: -12.0% or worse
- Candidate 20-day fall: -20.0% or worse
- Near-miss 1-day fall: -4.0% or worse
- Near-miss 5-day fall: -8.0% or worse
- Near-miss 20-day fall: -15.0% or worse

## Candidates

|   rank | ticker   | company                |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                                  | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:-----------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:-----------------------------------------|:--------------|:---------------|:------------------------|
|      1 | AOV.AX   | AMOTIV LTD             |         6.41 | A$857,978,240           |        -13.5  |         -10.47 |            -1.84 |                  9.44 | 1D <= -7.0%                              |               |                | not_run                 |
|      2 | ARF.AX   | ARENA REIT             |         2.24 | A$914,584,320           |        -12.5  |         -30.65 |           -31.08 |                  8.78 | 1D <= -7.0%; 5D <= -12.0%; 20D <= -20.0% | default       |                | not_run                 |
|      3 | SGH.AX   | SGH LTD                |        41.58 | A$16,922,984,448        |        -10.27 |          -8.68 |            -4.7  |                  8.8  | 1D <= -7.0%                              |               |                | not_run                 |
|      4 | 4DX.AX   | 4DMEDICAL LTD          |         4.08 | A$2,446,526,464         |         -7.27 |          -5.12 |             4.35 |                  1.03 | 1D <= -7.0%                              |               |                | not_run                 |
|      5 | DTR.AX   | DATELINE RESOURCES LTD |         0.12 | A$501,791,936           |          0    |           0    |           -21.87 |                  0    | 20D <= -20.0%                            | suspended     |                | not_run                 |
|      6 | WBT.AX   | WEEBIT NANO LTD        |         4.44 | A$1,067,499,392         |          3.02 |           1.37 |           -36.57 |                  1.06 | 20D <= -20.0%                            |               |                | not_run                 |

## Near Misses

|   rank | ticker   | company                |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger       | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:-----------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:--------------|:--------------|:---------------|:------------------------|
|      1 | A4N.AX   | ALPHA HPA LTD          |         0.5  | A$733,207,680           |         -5.61 |          -1.94 |           -12.93 |                  0.55 | 1D <= -4.0%   |               |                | not_run                 |
|      2 | DVP.AX   | DEVELOP GLOBAL LTD     |         4.96 | A$1,636,727,936         |         -2.75 |           2.06 |           -15.36 |                  0.85 | 20D <= -15.0% |               |                | not_run                 |
|      3 | LTR.AX   | LIONTOWN LTD           |         1.18 | A$3,751,350,784         |         -1.67 |          14.56 |           -16.9  |                  0.65 | 20D <= -15.0% |               |                | not_run                 |
|      4 | CNI.AX   | CENTURIA CAPITAL GROUP |         1.47 | A$1,472,049,152         |         -1.34 |          -1.01 |           -16    |                  0.37 | 20D <= -15.0% |               |                | not_run                 |
|      5 | WBC.AX   | WESTPAC BANKING CORP   |        35.69 | A$121,878,036,480       |         -0.03 |          -8.06 |            -2.59 |                  1.29 | 5D <= -8.0%   |               |                | not_run                 |

## Manual review discipline

Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.

## Scan status

- below_market_cap_threshold: 2
- candidate: 6
- near_miss: 5
- no_price_drop_trigger: 282

## Latest Performance Log Snapshot

| signal_date   | ticker   | company                     | signal_type   |   signal_price |   current_price |   days_since_signal |   return_pct | last_checked   |   openai_score_at_signal | openai_classification_at_signal   |
|:--------------|:---------|:----------------------------|:--------------|---------------:|----------------:|--------------------:|-------------:|:---------------|-------------------------:|:----------------------------------|
| 2026-08-11    | 4DX.AX   | 4DMEDICAL LTD               | candidate     |           4.08 |            4.08 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | A4N.AX   | ALPHA HPA LTD               | near_miss     |           0.5  |            0.5  |                   0 |            1 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | AOV.AX   | AMOTIV LTD                  | candidate     |           6.41 |            6.41 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | ARF.AX   | ARENA REIT                  | candidate     |           2.24 |            2.24 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | CNI.AX   | CENTURIA CAPITAL GROUP      | near_miss     |           1.47 |            1.47 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | DTR.AX   | DATELINE RESOURCES LTD      | candidate     |           0.12 |            0.12 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | DVP.AX   | DEVELOP GLOBAL LTD          | near_miss     |           4.96 |            4.96 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | LTR.AX   | LIONTOWN LTD                | near_miss     |           1.18 |            1.18 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | SGH.AX   | SGH LTD                     | candidate     |          41.58 |           41.58 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | WBC.AX   | WESTPAC BANKING CORP        | near_miss     |          35.69 |           35.69 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-11    | WBT.AX   | WEEBIT NANO LTD             | candidate     |           4.44 |            4.44 |                   0 |            0 | 2026-08-11     |                          | not_run                           |
| 2026-08-10    | ARF.AX   | ARENA REIT                  | candidate     |           2.56 |            2.24 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | BPT.AX   | BEACH ENERGY LTD            | near_miss     |           0.82 |            0.87 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | CDA.AX   | CODAN LTD                   | near_miss     |          39.12 |           40.75 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | CNI.AX   | CENTURIA CAPITAL GROUP      | near_miss     |           1.49 |            1.47 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | DTR.AX   | DATELINE RESOURCES LTD      | candidate     |           0.12 |            0.12 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | LTR.AX   | LIONTOWN LTD                | near_miss     |           1.2  |            1.18 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | MYR.AX   | MYER HOLDINGS LTD           | candidate     |           0.22 |            0.22 |                   1 |            0 | 2026-08-11     |                      nan | not_run                           |
| 2026-08-10    | TVN.AX   | TIVAN LTD                   | candidate     |           0.25 |            0.26 |                   1 |            6 | 2026-08-11     |                      nan | not_run                           |
| 2026-08-10    | WBC.AX   | Westpac Banking Corporation | near_miss     |          35.7  |           35.69 |                   1 |            0 | 2026-08-10     |                      nan | not_run                           |
