# E23 placebo battery and M-Power minimal detectable effects

**Plain English.** (1) We deliberately broke the data (shuffled the amount of mineral, the salt level, or the pH values) and checked that our tests then find nothing; they should claim an effect only about 5 times in 100. Result: **PLACEBOS PASS**. (2) For each test we computed the smallest effect our number of papers could reliably detect, so a 'no effect' result can be read as 'no effect larger than X'.

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Placebo and planted-effect checks

| test | reps | detections | interval_covers_truth | rate |
|---|---|---|---|---|
| a: E1 solids (rising), solids shuffled within pair | 50 | 2 |  | 0.04 |
| b: E8 outer-sphere slope, log10 I shuffled within series | 50 | 5 |  | 0.1 |
| c: E1 random-noise covariate | 50 | 3 |  | 0.06 |
| e: planted covariate +0.3 per SD | 20 | 20 | 12 | 1 |

d: curves passing the E1 line rule: 641; after permuting pH within curves: 24 (edges should mostly disappear).

f: paper (unit) share of the level variance: real labels 0.25; paper labels shuffled within pair 0.05.

## Minimal detectable effect (80% power, alpha 0.05), MDE = 2.80 x SE

| test | estimate | se | papers | mde_80pct_power | detectable_as_estimated |
|---|---|---|---|---|---|
| E1 level coefficient: intercept | 0.00952 | 0.201 |  | 0.562 | False |
| E1 level coefficient: falling | 0.419 | 0.142 |  | 0.397 | True |
| E1 level coefficient: solids_r | -0.178 | 0.0569 |  | 0.159 | True |
| E1 level coefficient: solids_f | -0.0533 | 0.0748 |  | 0.209 | False |
| E1 level coefficient: hinge_r | -0.1 | 0.0517 |  | 0.145 | False |
| E1 level coefficient: hinge_f | -0.309 | 0.0591 |  | 0.166 | True |
| E1 level coefficient: log10_total | 0.0112 | 0.0226 |  | 0.0633 | False |
| E1 level coefficient: cosolute | 0.0267 | 0.0926 |  | 0.259 | False |
| E1 level coefficient: co2 | 0.00387 | 0.0759 |  | 0.213 | False |
| E1 level coefficient: log10_I | -0.115 | 0.032 |  | 0.0896 | True |
| E8 within-paper slope: outer_sphere_prone | 1.22 | 0.399 | 8 | 1.12 | True |
| E8 within-paper slope: inner_sphere_prone | 0.0932 | 0.137 | 27 | 0.384 | False |
| E8 within-paper slope: oxyanion | -0.44 | 0.15 | 10 | 0.42 | True |
| E8 within-paper slope: organic_acid | -0.295 | 0.271 | 2 | 0.76 | False |

E1 rows are in log10 K units per unit of the covariate (per decade for log10 terms); E8 rows in pH per decade of ionic strength.

## Simulation check, E1 log10 I coefficient

| planted_effect | multiple_of_MDE | reps | power |
|---|---|---|---|
| 0.0448 | 0.5 | 20 | 0 |
| 0.0896 | 1 | 20 | 0 |
| 0.134 | 1.5 | 20 | 0 |

Power near 0.8 at 1x MDE confirms the analytic formula.
