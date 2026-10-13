# E23 placebo battery and M-Power minimal detectable effects

**Plain English.** (1) We deliberately broke the data (shuffled the amount of mineral, the salt level, or the pH values) and checked that our tests then find nothing; they should claim an effect only about 5 times in 100. Result: **PLACEBO FAILURE: tighten rules**. (2) For each test we computed the smallest effect our number of papers could reliably detect, so a 'no effect' result can be read as 'no effect larger than X'.

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `53f0944`.

## Placebo and planted-effect checks

| test | reps | detections | interval_covers_truth | rate |
|---|---|---|---|---|
| a: E1 solids (rising), solids shuffled within pair | 50 | 24 |  | 0.48 |
| b: E8 outer-sphere slope, log10 I shuffled within series | 50 | 4 |  | 0.08 |
| c: E1 random-noise covariate | 50 | 3 |  | 0.06 |
| e: planted covariate +0.3 per SD | 20 | 20 | 13 | 1 |

d: curves passing the E1 line rule: 757; after permuting pH within curves: 28 (edges should mostly disappear).

f: paper (unit) share of the level variance: real labels 0.30; paper labels shuffled within pair 0.00.

## Minimal detectable effect (80% power, alpha 0.05), MDE = 2.80 x SE

| test | estimate | se | papers | mde_80pct_power | detectable_as_estimated |
|---|---|---|---|---|---|
| E1 level coefficient: intercept | -0.168 | 0.182 |  | 0.51 | False |
| E1 level coefficient: falling | 0.388 | 0.123 |  | 0.346 | True |
| E1 level coefficient: solids_r | 0.114 | 0.0461 |  | 0.129 | False |
| E1 level coefficient: solids_f | 0.357 | 0.0687 |  | 0.192 | True |
| E1 level coefficient: hinge_r | -0.162 | 0.0569 |  | 0.159 | True |
| E1 level coefficient: hinge_f | -0.41 | 0.0612 |  | 0.172 | True |
| E1 level coefficient: log10_total | 0.00307 | 0.022 |  | 0.0616 | False |
| E1 level coefficient: cosolute | -0.271 | 0.088 |  | 0.247 | True |
| E1 level coefficient: co2 | 0.0393 | 0.0845 |  | 0.237 | False |
| E1 level coefficient: log10_I | -0.169 | 0.0331 |  | 0.0926 | True |
| E8 within-paper slope: outer_sphere_prone | 0.787 | 0.237 | 7 | 0.664 | True |
| E8 within-paper slope: inner_sphere_prone | 0.15 | 0.0822 | 36 | 0.23 | False |
| E8 within-paper slope: oxyanion | -0.295 | 0.0852 | 11 | 0.239 | True |

E1 rows are in log10 K units per unit of the covariate (per decade for log10 terms); E8 rows in pH per decade of ionic strength.

## Simulation check, E1 log10 I coefficient

| planted_effect | multiple_of_MDE | reps | power |
|---|---|---|---|
| 0.0463 | 0.5 | 20 | 0 |
| 0.0926 | 1 | 20 | 0 |
| 0.139 | 1.5 | 20 | 1 |

Power near 0.8 at 1x MDE confirms the analytic formula.

## Analyst notes (follow-up runs, logged in REGISTRY.md as E23-a2 and E23-a3)

- **Placebo (a) exposed between-pair confounding in E1, not only a placebo flaw.** Re-running it with loading kept at its real values (a2) still gave 48% / 46% false detections, so the loading hinge was not the cause. Shuffling solids WITHIN a pair keeps each pair's average solids, and E1's solids coefficient was identified partly by differences BETWEEN pairs, which are confounded (systems studied at high solids differ chemically from those studied at low solids).
- **Fix: within-between (Mundlak) split** (`E1Model(within_between=["solids_r", "solids_f"])`): each pair's mean solids enters as its own term, so the solids coefficient uses only within-pair differences. Placebo (a3): false-detection rate 0.06 (rising) and 0.12 (falling; slightly above the 0.10 line, few falling pairs).
- **Real-data within-pair solids effects** on log10 K: +0.24 per decade (rising, SE 0.05) and **+0.91** (falling, SE 0.09). The falling value is close to the +1.0 expected for linear sorption, as in the solids follow-up; rising edges remain far below it (particle-concentration effect). Between-pair terms are negative (-0.35 rising, -1.06 falling): the confounding the old coefficient mixed in.
- **MDE caveat:** the simulation check for log10 I found power ~0 at 1x the analytic MDE and ~1 at 1.5x. E1 re-centres each pair on its own reference pH, which absorbs most between-pair covariate variation, so the analytic SE is optimistic; treat 1.5x the tabled MDE as the working detectable effect for E1 level terms.
- Placebos b (E8, 0.08) and c (noise covariate, 0.06) pass; the planted effect is always detected but its interval covers the truth in 13 of 20 runs (somewhat narrow).
