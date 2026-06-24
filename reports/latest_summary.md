# Latest Contrarian Monitor Summary

Run time: 2026-06-24 22:57:39 UTC
Watchlist scanned: 20
Candidates found: 0
Near misses found: 2
Candidate report: `contrarian_candidates_2026-06-24.csv`
Near-miss report: `near_misses_2026-06-24.csv`

## Thresholds

- Minimum market capitalisation: A$500,000,000
- Candidate 1-day fall: -7.0% or worse
- Candidate 5-day fall: -12.0% or worse
- Candidate 20-day fall: -20.0% or worse
- Near-miss 1-day fall: -4.0% or worse
- Near-miss 5-day fall: -8.0% or worse
- Near-miss 20-day fall: -15.0% or worse

## Candidates

_None._

## Near Misses

|   rank | ticker   | company   |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger     | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:----------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:------------|:--------------|:---------------|:------------------------|
|      1 | BHP.AX   | BHP Group |        59.5  | A$302,301,052,928       |         -0.7  |          -9.28 |            -1.41 |                  0.83 | 5D <= -8.0% |               |                | not_run                 |
|      2 | REA.AX   | REA Group |       131.58 | A$17,218,533,376        |          0.05 |          -9.55 |           -12.58 |                  1.64 | 5D <= -8.0% | downgrade     |                | not_run                 |

## Manual review discipline

Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.

## Scan status

- market_cap_unavailable: 1
- near_miss: 2
- no_price_drop_trigger: 17

## Latest Performance Log Snapshot

| signal_date   | ticker   | company   | signal_type   |   signal_price |   current_price |   days_since_signal |   return_pct | last_checked   |   openai_score_at_signal | openai_classification_at_signal   |
|:--------------|:---------|:----------|:--------------|---------------:|----------------:|--------------------:|-------------:|:---------------|-------------------------:|:----------------------------------|
| 2026-06-24    | BHP.AX   | BHP Group | near_miss     |          59.5  |           59.5  |                   0 |            0 | 2026-06-24     |                          | not_run                           |
| 2026-06-24    | REA.AX   | REA Group | near_miss     |         131.58 |          131.58 |                   0 |            0 | 2026-06-24     |                          | not_run                           |
| 2026-06-23    | BHP.AX   | BHP Group | near_miss     |          59.92 |           59.5  |                   1 |            0 | 2026-06-23     |                      nan | not_run                           |
| 2026-06-23    | REA.AX   | REA Group | near_miss     |         131.52 |          131.58 |                   1 |            0 | 2026-06-23     |                      nan | not_run                           |
