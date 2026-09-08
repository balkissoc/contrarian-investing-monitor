# Latest Contrarian Monitor Summary

Run time: 2026-09-08 23:44:55 UTC
Watchlist scanned: 294
Candidates found: 9
Near misses found: 38
Candidate report: `contrarian_candidates_2026-09-08.csv`
Near-miss report: `near_misses_2026-09-08.csv`

## Thresholds

- Minimum market capitalisation: A$500,000,000
- Candidate 1-day fall: -7.0% or worse
- Candidate 5-day fall: -12.0% or worse
- Candidate 20-day fall: -20.0% or worse
- Near-miss 1-day fall: -4.0% or worse
- Near-miss 5-day fall: -8.0% or worse
- Near-miss 20-day fall: -15.0% or worse

## Candidates

|   rank | ticker   | company                 |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                     | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:------------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:----------------------------|:--------------|:---------------|:------------------------|
|      1 | VSL.AX   | VULCAN STEEL LTD        |         5.15 | A$754,629,248           |         -8.36 |         -10.12 |            -6.7  |                  0.27 | 1D <= -7.0%                 |               |                | not_run                 |
|      2 | CHC.AX   | CHARTER HALL GROUP      |        18.67 | A$8,830,857,216         |         -1.74 |          -2.3  |           -21.72 |                  0.5  | 20D <= -20.0%               |               |                | not_run                 |
|      3 | WBT.AX   | WEEBIT NANO LTD         |         3.51 | A$845,011,072           |         -1.4  |          -2.77 |           -20.95 |                  1.04 | 20D <= -20.0%               |               |                | not_run                 |
|      4 | HSN.AX   | HANSEN TECHNOLOGIES LTD |         3.35 | A$685,161,728           |         -0.59 |          -2.33 |           -23.37 |                  0.46 | 20D <= -20.0%               |               |                | not_run                 |
|      5 | SDR.AX   | SITEMINDER LTD          |         2.89 | A$818,115,264           |         -0.34 |          -1.03 |           -24.15 |                  0.46 | 20D <= -20.0%               |               |                | not_run                 |
|      6 | REG.AX   | REGIS HEALTHCARE LTD    |         4.63 | A$1,399,933,824         |          0.96 |         -23.67 |           -24.88 |                  0.89 | 5D <= -12.0%; 20D <= -20.0% |               |                | not_run                 |
|      7 | ELS.AX   | ELSIGHT LTD             |         4.85 | A$1,078,574,336         |          1.04 |          -6.01 |           -31.5  |                  0.67 | 20D <= -20.0%               |               |                | not_run                 |
|      8 | IRE.AX   | IRESS LTD               |         5.7  | A$1,064,699,968         |          1.06 |           2.89 |           -23.51 |                  1.19 | 20D <= -20.0%               |               |                | not_run                 |
|      9 | NAN.AX   | NANOSONICS LTD          |         2.8  | A$836,950,464           |          2.94 |           3.7  |           -23.29 |                  0.77 | 20D <= -20.0%               |               |                | not_run                 |

## Near Misses

|   rank | ticker   | company                      |   last_price | market_cap_aud_approx   |   one_day_pct |   five_day_pct |   twenty_day_pct |   volume_spike_vs_20d | trigger                    | avoid_flags   | openai_score   | openai_classification   |
|-------:|:---------|:-----------------------------|-------------:|:------------------------|--------------:|---------------:|-----------------:|----------------------:|:---------------------------|:--------------|:---------------|:------------------------|
|      1 | TEA.AX   | TASMEA LTD                   |         9.3  | A$2,608,461,056         |         -5.68 |          -3.43 |             6.9  |                  1.04 | 1D <= -4.0%                |               |                | not_run                 |
|      2 | 4DX.AX   | 4DMEDICAL LTD                |         3.35 | A$2,009,776,512         |         -4.83 |          -2.05 |           -17.89 |                  1.3  | 1D <= -4.0%; 20D <= -15.0% |               |                | not_run                 |
|      3 | BAP.AX   | BAPCOR LTD                   |         0.79 | A$531,474,944           |         -4.82 |           1.28 |            88.1  |                  0.96 | 1D <= -4.0%                | impairment    |                | not_run                 |
|      4 | JDO.AX   | JUDO CAPITAL HOLDINGS LTD    |         1.02 | A$1,144,800,768         |         -4.67 |          -5.99 |             6.81 |                  0.67 | 1D <= -4.0%                | downgrade     |                | not_run                 |
|      5 | DDR.AX   | DICKER DATA LTD              |        14.1  | A$2,560,340,224         |         -4.21 |          -1.61 |            10.47 |                  0.44 | 1D <= -4.0%                |               |                | not_run                 |
|      6 | TWE.AX   | TREASURY WINE ESTATES LTD    |         5.35 | A$4,327,814,144         |         -4.12 |          -3.43 |            -5.14 |                  0.77 | 1D <= -4.0%                |               |                | not_run                 |
|      7 | LOV.AX   | LOVISA HOLDINGS LTD          |        22.72 | A$2,515,990,016         |         -3.73 |          -9.52 |           -13.22 |                  0.46 | 5D <= -8.0%                |               |                | not_run                 |
|      8 | NEC.AX   | NINE ENTERTAINMENT CO HOLDIN |         0.86 | A$1,363,755,520         |         -3.37 |         -11.79 |           -14.85 |                  1.07 | 5D <= -8.0%                |               |                | not_run                 |
|      9 | LYL.AX   | LYCOPODIUM LTD               |        20.74 | A$824,212,224           |         -3.26 |          -8.92 |             8.02 |                  0.87 | 5D <= -8.0%                |               |                | not_run                 |
|     10 | ZIP.AX   | ZIP CO LTD                   |         2.31 | A$2,878,079,232         |         -2.94 |         -11.83 |           -15.69 |                  0.61 | 5D <= -8.0%; 20D <= -15.0% |               |                | not_run                 |
|     11 | IPX.AX   | IPERIONX LTD                 |         3.03 | A$1,097,266,304         |         -2.88 |          -2.26 |           -18.55 |                  0.59 | 20D <= -15.0%              |               |                | not_run                 |
|     12 | TPW.AX   | TEMPLE & WEBSTER GROUP LTD   |         4.75 | A$553,596,928           |         -2.86 |          -2.06 |           -16.37 |                  0.39 | 20D <= -15.0%              |               |                | not_run                 |
|     13 | WTC.AX   | WISETECH GLOBAL LTD          |        35.25 | A$11,854,682,112        |         -2.79 |         -11.21 |           -13.69 |                  0.67 | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     14 | XRO.AX   | XERO LTD                     |        74.25 | A$13,117,121,536        |         -2.61 |         -10.84 |            -5.88 |                  0.5  | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     15 | JBH.AX   | JB HI-FI LTD                 |        66.07 | A$7,223,696,384         |         -2.25 |          -0.75 |           -19.5  |                  0.63 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     16 | NWL.AX   | NETWEALTH GROUP LTD          |        19.79 | A$4,909,423,616         |         -2.15 |          -3.47 |           -19.19 |                  0.72 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     17 | VUL.AX   | VULCAN ENERGY RESOURCES LTD  |         2.56 | A$1,225,371,520         |         -1.92 |          -5.88 |           -16.61 |                  0.65 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     18 | NCK.AX   | NICK SCALI LTD               |        14.63 | A$1,251,314,048         |         -1.81 |           0.21 |           -15.53 |                  0.71 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     19 | TNE.AX   | TECHNOLOGY ONE LTD           |        29.16 | A$9,546,066,944         |         -1.75 |          -9.41 |           -12.33 |                  1.83 | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     20 | HUB.AX   | HUB24 LTD                    |        72.18 | A$5,902,431,232         |         -1.65 |          -1.61 |           -19.24 |                  1.05 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     21 | CMW.AX   | CROMWELL PROPERTY GROUP      |         0.37 | A$968,980,672           |         -1.33 |          -1.33 |           -15.91 |                  0.66 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     22 | SLC.AX   | SUPERLOOP LTD                |         2.71 | A$1,394,874,624         |         -1.09 |          -4.58 |           -16.1  |                  0.63 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     23 | IPH.AX   | IPH LTD                      |         3.32 | A$851,537,088           |         -0.9  |          -1.48 |           -17.82 |                  0.67 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     24 | L1G.AX   | L1 GROUP LTD                 |         1.17 | A$3,002,865,152         |         -0.85 |         -10    |             7.03 |                  0.56 | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     25 | WA1.AX   | WA1 RESOURCES LTD            |        11.04 | A$820,761,920           |         -0.63 |          -1.25 |           -18.28 |                  0.41 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     26 | QAL.AX   | QUALITAS LTD                 |         2.66 | A$801,789,248           |         -0.37 |          -6.98 |           -16.36 |                  0.38 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     27 | DRO.AX   | DRONESHIELD LTD              |         1.75 | A$1,614,508,416         |         -0.29 |          -1.13 |           -17.69 |                  0.32 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     28 | FLT.AX   | FLIGHT CENTRE TRAVEL GROUP L |        11.45 | A$2,344,803,584         |         -0.26 |          -2.47 |           -15.44 |                  0.68 | 20D <= -15.0%              | downgrade     |                | not_run_limit_reached   |
|     29 | ABB.AX   | AUSSIE BROADBAND LTD         |         4.13 | A$1,302,705,536         |         -0.24 |          -2.66 |           -15.66 |                  0.94 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     30 | PNI.AX   | PINNACLE INVESTMENT MANAGEME |        14.95 | A$3,602,725,888         |         -0.13 |          -1.39 |           -18.74 |                  1.46 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     31 | PLS.AX   | PLS GROUP LTD                |         4.93 | A$15,892,454,400        |          0    |          -9.21 |             6.31 |                  0.71 | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     32 | SIQ.AX   | SMARTGROUP CORP LTD          |        11.22 | A$1,458,353,024         |          0.04 |           2.93 |           -16.1  |                  1.98 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     33 | GDG.AX   | GENERATION DEVELOPMENT GROUP |         3.37 | A$1,347,721,984         |          0.3  |          10.48 |           -15.9  |                  0.97 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     34 | LTR.AX   | LIONTOWN LTD                 |         1.2  | A$3,813,407,744         |          0.84 |          -8.43 |             1.27 |                  0.61 | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     35 | MFG.AX   | MAGELLAN FINANCIAL GROUP LTD |         8.92 | A$2,610,062,592         |          1.36 |           2.53 |           -16.69 |                  0.72 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     36 | ELV.AX   | ELEVRA LITHIUM LTD           |         7.75 | A$1,495,911,552         |          2.92 |          -9.88 |            -8.93 |                  1.13 | 5D <= -8.0%                |               |                | not_run_limit_reached   |
|     37 | CU6.AX   | CLARITY PHARMACEUTICALS LTD  |         2.37 | A$884,202,432           |          4.41 |           1.72 |           -17.13 |                  1.19 | 20D <= -15.0%              |               |                | not_run_limit_reached   |
|     38 | EQR.AX   | EQ RESOURCES LTD             |         0.38 | A$1,988,194,816         |          5.48 |          -9.41 |            24.19 |                  0.83 | 5D <= -8.0%                |               |                | not_run_limit_reached   |

## Manual review discipline

Before buying, check ASX announcements, balance sheet strength, debt maturities, liquidity, free cash flow, regulatory risk and whether the adverse event is temporary or permanently damaging.

## Scan status

- below_market_cap_threshold: 7
- candidate: 9
- insufficient_price_history: 1
- near_miss: 38
- no_price_drop_trigger: 239

## Latest Performance Log Snapshot

| signal_date   | ticker   | company                      | signal_type   |   signal_price |   current_price |   days_since_signal |   return_pct | last_checked   | openai_score_at_signal   | openai_classification_at_signal   |
|:--------------|:---------|:-----------------------------|:--------------|---------------:|----------------:|--------------------:|-------------:|:---------------|:-------------------------|:----------------------------------|
| 2026-09-08    | 4DX.AX   | 4DMEDICAL LTD                | near_miss     |           3.35 |            3.35 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | ABB.AX   | AUSSIE BROADBAND LTD         | near_miss     |           4.13 |            4.13 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | BAP.AX   | BAPCOR LTD                   | near_miss     |           0.79 |            0.79 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | CHC.AX   | CHARTER HALL GROUP           | candidate     |          18.67 |           18.67 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | CMW.AX   | CROMWELL PROPERTY GROUP      | near_miss     |           0.37 |            0.37 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | CU6.AX   | CLARITY PHARMACEUTICALS LTD  | near_miss     |           2.37 |            2.37 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | DDR.AX   | DICKER DATA LTD              | near_miss     |          14.1  |           14.1  |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | DRO.AX   | DRONESHIELD LTD              | near_miss     |           1.75 |            1.75 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | ELS.AX   | ELSIGHT LTD                  | candidate     |           4.85 |            4.85 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | ELV.AX   | ELEVRA LITHIUM LTD           | near_miss     |           7.75 |            7.75 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | EQR.AX   | EQ RESOURCES LTD             | near_miss     |           0.38 |            0.38 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | FLT.AX   | FLIGHT CENTRE TRAVEL GROUP L | near_miss     |          11.45 |           11.45 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | GDG.AX   | GENERATION DEVELOPMENT GROUP | near_miss     |           3.37 |            3.37 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | HSN.AX   | HANSEN TECHNOLOGIES LTD      | candidate     |           3.35 |            3.35 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | HUB.AX   | HUB24 LTD                    | near_miss     |          72.18 |           72.18 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | IPH.AX   | IPH LTD                      | near_miss     |           3.32 |            3.32 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | IPX.AX   | IPERIONX LTD                 | near_miss     |           3.03 |            3.03 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | IRE.AX   | IRESS LTD                    | candidate     |           5.7  |            5.7  |                   0 |            0 | 2026-09-08     |                          | not_run                           |
| 2026-09-08    | JBH.AX   | JB HI-FI LTD                 | near_miss     |          66.07 |           66.07 |                   0 |            0 | 2026-09-08     |                          | not_run_limit_reached             |
| 2026-09-08    | JDO.AX   | JUDO CAPITAL HOLDINGS LTD    | near_miss     |           1.02 |            1.02 |                   0 |            0 | 2026-09-08     |                          | not_run                           |
