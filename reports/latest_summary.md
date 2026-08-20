# Latest Contrarian Monitor Summary

Run time: 2026-08-20 22:14:54 UTC
Watchlist scanned: 295
Candidates found: 15
Near misses found: 18
Candidate report: `contrarian_candidates_2026-08-20.csv`
Near-miss report: `near_misses_2026-08-20.csv`

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
|      1 | IPH.AX   | IPH LTD                    |         3.75 | A$961,099,328           |        -11.14 |         -10.29 |            -6.02 |                  4.85 | 1D <= -7.0%                 |               |                | not_run                 |
|      2 | DOW.AX   | DOWNER EDI LTD             |         6.68 | A$4,402,191,360         |        -10.34 |         -12.11 |           -15.97 |                  7.05 | 1D <= -7.0%; 5D <= -12.0%   |               |                | not_run                 |
|      3 | SHL.AX   | SONIC HEALTHCARE LTD       |        21.38 | A$10,566,806,528        |         -9.25 |          -4.55 |             2.79 |                  2.45 | 1D <= -7.0%                 |               |                | not_run                 |
|      4 | IPX.AX   | IPERIONX LTD               |         2.89 | A$1,046,567,552         |         -4.3  |         -16.47 |           -13.21 |                  2.02 | 5D <= -12.0%                |               |                | not_run                 |
|      5 | HUB.AX   | HUB24 LTD                  |        76.48 | A$6,254,058,496         |         -4.09 |         -12.64 |            -8.87 |                  2.79 | 5D <= -12.0%                |               |                | not_run                 |
|      6 | HSN.AX   | HANSEN TECHNOLOGIES LTD    |         3.22 | A$658,573,440           |         -3.88 |         -24.94 |           -21.46 |                  5.54 | 5D <= -12.0%; 20D <= -20.0% |               |                | not_run                 |
|      7 | BRE.AX   | BRAZILIAN RARE EARTHS LTD  |         4    | A$1,104,614,912         |         -1.23 |         -15.43 |            -0.25 |                  1.63 | 5D <= -12.0%                |               |                | not_run                 |
|      8 | JBH.AX   | JB HI-FI LTD               |        70.21 | A$7,676,338,688         |         -0.89 |         -14.81 |            -8.47 |                  1.1  | 5D <= -12.0%                |               |                | not_run                 |
|      9 | AZJ.AX   | AURIZON HOLDINGS LTD       |         3.6  | A$6,059,906,048         |         -0.55 |         -14.08 |           -15.89 |                  2.33 | 5D <= -12.0%                |               |                | not_run                 |
|     10 | WBT.AX   | WEEBIT NANO LTD            |         4.16 | A$1,000,179,584         |         -0.24 |         -11.11 |           -20.91 |                  0.99 | 20D <= -20.0%               |               |                | not_run                 |
|     11 | TVN.AX   | TIVAN LTD                  |         0.25 | A$593,465,728           |          2    |         -12.07 |           -13.56 |                  0.45 | 5D <= -12.0%                | trading halt  |                | not_run                 |
|     12 | ARF.AX   | ARENA REIT                 |         2.42 | A$984,057,472           |          2.11 |           3.86 |           -23.66 |                  0.78 | 20D <= -20.0%               | default       |                | not_run                 |
|     13 | SGM.AX   | SIMS LTD                   |        23.24 | A$4,490,734,592         |          2.51 |         -12.17 |           -11.63 |                  2.61 | 5D <= -12.0%                |               |                | not_run_limit_reached   |
|     14 | IRE.AX   | IRESS LTD                  |         6.24 | A$1,165,566,208         |          3.31 |         -22.19 |            -4.15 |                  1.96 | 5D <= -12.0%                |               |                | not_run_limit_reached   |
|     15 | TPW.AX   | TEMPLE & WEBSTER GROUP LTD |         4.51 | A$525,625,760           |          8.67 |         -13.93 |            -9.26 |                  2.91 | 5D <= -12.0%                | downgrade     |                | not_run_limit_reached   |

## Near Misses

|   rank | ticker   | company                      |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                  | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:-----------------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:-------------------------|:--------------|:---------------|:------------------------|
|      1 | BSL.AX   | BLUESCOPE STEEL LTD          |        30.05 |                         |         -6.53 |         -11.25 |            -7.11 |                  2.91 | 1D <= -4.0%; 5D <= -8.0% |               |                | not_run                 |
|      2 | MPL.AX   | MEDIBANK PRIVATE LTD         |         4.71 | A$12,971,355,136        |         -6.36 |          -7.1  |            -7.83 |                  4.4  | 1D <= -4.0%              |               |                | not_run                 |
|      3 | SLC.AX   | SUPERLOOP LTD                |         3.13 | A$1,611,054,592         |         -6.01 |           0.32 |            -1.57 |                  3.11 | 1D <= -4.0%              |               |                | not_run                 |
|      4 | RDX.AX   | REDOX LTD/AUSTRALIA          |         3.59 | A$1,885,042,304         |         -5.53 |          -5.28 |            -4.52 |                  2.29 | 1D <= -4.0%              |               |                | not_run                 |
|      5 | NHF.AX   | NIB HOLDINGS LTD             |         7.09 | A$3,466,391,808         |         -5.34 |          -3.67 |            -5.09 |                  1.41 | 1D <= -4.0%              |               |                | not_run                 |
|      6 | MP1.AX   | MEGAPORT LTD                 |        19.31 | A$4,680,136,192         |         -5.06 |         -10.93 |             1.15 |                  3.41 | 1D <= -4.0%; 5D <= -8.0% |               |                | not_run                 |
|      7 | NWL.AX   | NETWEALTH GROUP LTD          |        22.11 | A$5,425,721,344         |         -4.29 |          -8.22 |             1.01 |                  1.94 | 1D <= -4.0%; 5D <= -8.0% |               |                | not_run                 |
|      8 | IAG.AX   | INSURANCE AUSTRALIA GROUP    |         7.8  |                         |         -4.18 |          -0.13 |            -7.47 |                  1.13 | 1D <= -4.0%              |               |                | not_run                 |
|      9 | GNP.AX   | GENUSPLUS GROUP LTD          |         9.07 | A$1,646,437,376         |         -4.02 |          -0.33 |            -1.73 |                  1.14 | 1D <= -4.0%              |               |                | not_run                 |
|     10 | GWA.AX   | GWA GROUP LTD                |         2.09 | A$531,661,568           |         -2.56 |          -8.71 |            -6.75 |                  3.42 | 5D <= -8.0%              |               |                | not_run                 |
|     11 | BEN.AX   | BENDIGO AND ADELAIDE BANK    |        10.21 | A$5,757,081,088         |         -1.83 |          -8.27 |            -5.55 |                  1.52 | 5D <= -8.0%              |               |                | not_run                 |
|     12 | SKG.AX   | STORAGE KING GROUP           |         1.14 | A$1,504,647,936         |          0    |          -9.49 |           -11.58 |                  0.96 | 5D <= -8.0%              |               |                | not_run                 |
|     13 | GDG.AX   | GENERATION DEVELOPMENT GROUP |         3.79 | A$1,515,687,296         |          0.53 |          -1.3  |           -17.25 |                  0.55 | 20D <= -15.0%            |               |                | not_run_limit_reached   |
|     14 | GPT.AX   | GPT GROUP                    |         4.74 | A$9,079,836,672         |          0.85 |          -8.32 |            -3.66 |                  1.3  | 5D <= -8.0%              |               |                | not_run_limit_reached   |
|     15 | LLC.AX   | LENDLEASE GROUP              |         2.69 | A$1,927,586,432         |          1.09 |         -11.71 |            -3.79 |                  1.23 | 5D <= -8.0%              | downgrade     |                | not_run_limit_reached   |
|     16 | SRL.AX   | SUNRISE ENERGY METALS LTD    |        16.63 | A$2,817,960,448         |          1.71 |         -10.97 |             7.99 |                  0.44 | 5D <= -8.0%              |               |                | not_run_limit_reached   |
|     17 | CNI.AX   | CENTURIA CAPITAL GROUP       |         1.4  |                         |          2.18 |         -11.08 |           -11.64 |                  0.69 | 5D <= -8.0%              |               |                | not_run_limit_reached   |
|     18 | MYR.AX   | MYER HOLDINGS LTD            |         0.22 |                         |          2.38 |           0    |           -15.69 |                  0.32 | 20D <= -15.0%            |               |                | not_run_limit_reached   |

## Manual review discipline

Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.

## Scan status

- below_market_cap_threshold: 2
- candidate: 15
- near_miss: 18
- no_price_drop_trigger: 260

## Latest Performance Log Snapshot

| signal_date   | ticker   | company                      | signal_type   |   signal_price |   current_price |   days_since_signal |   return_pct | last_checked   | openai_score_at_signal   | openai_classification_at_signal   |
|:--------------|:---------|:-----------------------------|:--------------|---------------:|----------------:|--------------------:|-------------:|:---------------|:-------------------------|:----------------------------------|
| 2026-08-20    | ARF.AX   | ARENA REIT                   | candidate     |           2.42 |            2.42 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | AZJ.AX   | AURIZON HOLDINGS LTD         | candidate     |           3.6  |            3.6  |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | BEN.AX   | BENDIGO AND ADELAIDE BANK    | near_miss     |          10.21 |           10.21 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | BRE.AX   | BRAZILIAN RARE EARTHS LTD    | candidate     |           4    |            4    |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | BSL.AX   | BLUESCOPE STEEL LTD          | near_miss     |          30.05 |           30.05 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | CNI.AX   | CENTURIA CAPITAL GROUP       | near_miss     |           1.4  |            1.4  |                   0 |            0 | 2026-08-20     |                          | not_run_limit_reached             |
| 2026-08-20    | DOW.AX   | DOWNER EDI LTD               | candidate     |           6.68 |            6.68 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | GDG.AX   | GENERATION DEVELOPMENT GROUP | near_miss     |           3.79 |            3.79 |                   0 |            0 | 2026-08-20     |                          | not_run_limit_reached             |
| 2026-08-20    | GNP.AX   | GENUSPLUS GROUP LTD          | near_miss     |           9.07 |            9.07 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | GPT.AX   | GPT GROUP                    | near_miss     |           4.74 |            4.74 |                   0 |            0 | 2026-08-20     |                          | not_run_limit_reached             |
| 2026-08-20    | GWA.AX   | GWA GROUP LTD                | near_miss     |           2.09 |            2.09 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | HSN.AX   | HANSEN TECHNOLOGIES LTD      | candidate     |           3.22 |            3.22 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | HUB.AX   | HUB24 LTD                    | candidate     |          76.48 |           76.48 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | IAG.AX   | INSURANCE AUSTRALIA GROUP    | near_miss     |           7.8  |            7.8  |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | IPH.AX   | IPH LTD                      | candidate     |           3.75 |            3.75 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | IPX.AX   | IPERIONX LTD                 | candidate     |           2.89 |            2.89 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | IRE.AX   | IRESS LTD                    | candidate     |           6.24 |            6.24 |                   0 |            0 | 2026-08-20     |                          | not_run_limit_reached             |
| 2026-08-20    | JBH.AX   | JB HI-FI LTD                 | candidate     |          70.21 |           70.21 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
| 2026-08-20    | LLC.AX   | LENDLEASE GROUP              | near_miss     |           2.69 |            2.69 |                   0 |            0 | 2026-08-20     |                          | not_run_limit_reached             |
| 2026-08-20    | MP1.AX   | MEGAPORT LTD                 | near_miss     |          19.31 |           19.31 |                   0 |            0 | 2026-08-20     |                          | not_run                           |
