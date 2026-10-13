# E5 Edge-coverage artefact and a slope-based QC rule

**Plain English.** We took well-measured curves, pretended only part of each had been measured, and checked how wrong the edge estimate became. The error is predicted well by how precisely the steepness of the curve is determined and how far the edge is from the nearest measured point. A quality rule built on that keeps 93% of the Stage 1 census curves (the old rule kept 36%), with a validated median edge error of 0.11 pH on the kept test curves. Verdict on the pre-declared rule: **MEETS RULE**. Changing the Stage 1 rule is a decision for Samuel and Dr. Black (D3); the Stage 1 failure stays recorded as a failure.

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `b5c03f2`.

## Truncation experiment (111 well-measured curves; 1446 usable truncations)

| window | n | median_line_error | median_logistic_error | share_within_0_5 | share_slope_sign_flipped | share_no_usable_edge |
|---|---|---|---|---|---|---|
| 2 | 281 | 0.211 | 0.378 | 0.79 | 0.00315 | 0.114 |
| 3 | 355 | 0.143 | 0.243 | 0.823 | 0.00499 | 0.115 |
| 4 | 382 | 0.121 | 0.169 | 0.869 | 0.00234 | 0.107 |
| 5 | 428 | 0.0829 | 0.117 | 0.918 | 0 | 0.0835 |

## Error model (fitted on half the curves)

| term | coefficient |
|---|---|
| intercept | -0.917 |
| log10(SE(b)/|b|) | 0.294 |
| extrapolation distance (pH) | 0.354 |
| log10 n_mid | 0.07 |

Residual SD 0.71 (log10 units). Validation on the other half: rank correlation between predicted and actual edge error 0.52; truncations kept by the rule (predicted error <= 0.5 pH): 648 of 689, median actual error 0.11 pH.

## Census set under the slope-based rule

- Census-set rising/falling curves (development papers): 713
- Kept by the Stage 1 rule (core library): 36.3%
- Kept by the E5 rule (predicted edge error <= 0.5 pH): 93.4%

## Similar vs different curve pairs on a common window

Cross-paper pairs: 741; with a shared window of >= 2 pH and usable lines on it: 663. Spearman |edge difference| vs |pH-span difference|: native edges 0.29 (all pairs), 0.32 (same pairs as below); common-window edges 0.30. A drop towards zero means the span association was partly a coverage artefact.

Files: `truncations.csv`, `error_by_window.csv`, `error_model.csv`, `census_predicted_edge_error.csv`.
