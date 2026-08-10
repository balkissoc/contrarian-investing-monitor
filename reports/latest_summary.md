# Latest Contrarian Monitor Summary

Run time: 2026-08-10 12:38:59 UTC
Watchlist scanned: 295
Candidates found: 4
Near misses found: 5
Candidate report: `contrarian_candidates_2026-08-10.csv`
Near-miss report: `near_misses_2026-08-10.csv`

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
|      1 | ARF.AX   | ARENA REIT             |         2.56 | A$1,045,239,232         |        -21.95 |         -19.5  |           -21.71 |                 17.96 | 1D <= -7.0%; 5D <= -12.0%; 20D <= -20.0% |               |                | not_run                 |
|      2 | WBT.AX   | WEEBIT NANO LTD        |         4.31 | A$1,036,243,776         |         -2.49 |           0.94 |           -38.43 |                  0.74 | 20D <= -20.0%                            |               |                | not_run                 |
|      3 | TVN.AX   | TIVAN LTD              |         0.25 | A$569,862,848           |         -2    |          -2    |           -25.76 |                  1.07 | 20D <= -20.0%                            |               |                | not_run                 |
|      4 | DTR.AX   | DATELINE RESOURCES LTD |         0.12 | A$511,880,256           |          0    |           0    |           -30.56 |                  0    | 20D <= -20.0%                            |               |                | not_run                 |

## Near Misses

|   rank | ticker   | company                |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                  | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:-----------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:-------------------------|:--------------|:---------------|:------------------------|
|      1 | WBC.AX   | WESTPAC BANKING CORP   |        35.7  | A$121,912,197,120       |         -5.88 |          -6.47 |            -3.25 |                  2.17 | 1D <= -4.0%              |               |                | not_run                 |
|      2 | CDA.AX   | CODAN LTD              |        39.12 | A$7,114,962,432         |         -4.72 |          -2.4  |            -7.41 |                  1.5  | 1D <= -4.0%              |               |                | not_run                 |
|      3 | BPT.AX   | BEACH ENERGY LTD       |         0.82 | A$1,882,100,352         |         -4.62 |          -8.84 |            -5.71 |                  1.91 | 1D <= -4.0%; 5D <= -8.0% |               |                | not_run                 |
|      4 | CNI.AX   | CENTURIA CAPITAL GROUP |         1.49 | A$1,492,076,928         |          0.68 |           1.71 |           -16.06 |                  0.45 | 20D <= -15.0%            |               |                | not_run                 |
|      5 | LTR.AX   | LIONTOWN LTD           |         1.2  | A$3,814,933,248         |          1.69 |          21.21 |           -15.79 |                  1.02 | 20D <= -15.0%            |               |                | not_run                 |

## Manual review discipline

Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.

## Scan status

- below_market_cap_threshold: 1
- candidate: 4
- near_miss: 5
- no_price_drop_trigger: 285

## Latest Performance Log Snapshot

| signal_date   | ticker   | company                     | signal_type   |   signal_price |   current_price |   days_since_signal |   return_pct | last_checked   |   openai_score_at_signal | openai_classification_at_signal   |
|:--------------|:---------|:----------------------------|:--------------|---------------:|----------------:|--------------------:|-------------:|:---------------|-------------------------:|:----------------------------------|
| 2026-08-10    | ARF.AX   | ARENA REIT                  | candidate     |           2.56 |            2.56 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | BPT.AX   | BEACH ENERGY LTD            | near_miss     |           0.82 |            0.82 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | CDA.AX   | CODAN LTD                   | near_miss     |          39.12 |           39.12 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | CNI.AX   | CENTURIA CAPITAL GROUP      | near_miss     |           1.49 |            1.49 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | DTR.AX   | DATELINE RESOURCES LTD      | candidate     |           0.12 |            0.12 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | LTR.AX   | LIONTOWN LTD                | near_miss     |           1.2  |            1.2  |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | MYR.AX   | MYER HOLDINGS LTD           | candidate     |           0.22 |            0.22 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | TVN.AX   | TIVAN LTD                   | candidate     |           0.25 |            0.25 |                   0 |           -2 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | WBC.AX   | Westpac Banking Corporation | near_miss     |          35.7  |           35.7  |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-08-10    | WBT.AX   | WEEBIT NANO LTD             | candidate     |           4.31 |            4.31 |                   0 |            0 | 2026-08-10     |                      nan | not_run                           |
| 2026-07-02    | WES.AX   | Wesfarmers                  | near_miss     |          86.85 |           89.54 |                  39 |            0 | 2026-07-02     |                      nan | not_run                           |
| 2026-07-01    | COL.AX   | Coles Group                 | near_miss     |          23.35 |           23.9  |                  40 |            0 | 2026-07-01     |                      nan | not_run                           |
| 2026-06-25    | BHP.AX   | BHP Group                   | near_miss     |          58.52 |           63.52 |                  46 |            0 | 2026-06-25     |                      nan | not_run                           |
| 2026-06-24    | BHP.AX   | BHP Group                   | near_miss     |          59.5  |           63.52 |                  47 |            0 | 2026-06-24     |                      nan | not_run                           |
| 2026-06-24    | REA.AX   | REA Group                   | near_miss     |         131.58 |          175.34 |                  47 |            0 | 2026-06-24     |                      nan | not_run                           |
| 2026-06-23    | BHP.AX   | BHP Group                   | near_miss     |          59.92 |           63.52 |                  48 |            1 | 2026-08-04     |                      nan | not_run                           |
| 2026-06-23    | REA.AX   | REA Group                   | near_miss     |         131.52 |          175.34 |                  48 |            0 | 2026-06-23     |                      nan | not_run                           |
