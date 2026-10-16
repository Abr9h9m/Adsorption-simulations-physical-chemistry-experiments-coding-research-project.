# E5 Edge-coverage artefact and a slope-based QC rule

**Plain English.** We took well-measured curves, pretended only part of each had been measured, and checked how wrong the edge estimate became. The error is predicted well by how precisely the steepness of the curve is determined and how far the edge is from the nearest measured point. A quality rule built on that keeps 90% of the Stage 1 census curves (the old rule kept 30%), with a validated median edge error of 0.17 pH on the kept test curves. Verdict on the pre-declared rule: **MEETS RULE**. Changing the Stage 1 rule is a decision for Samuel and Dr. Black (D3); the Stage 1 failure stays recorded as a failure.

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Truncation experiment (89 well-measured curves; 1076 usable truncations)

| window | n | median_line_error | median_logistic_error | share_within_0_5 | share_slope_sign_flipped | share_no_usable_edge |
|---|---|---|---|---|---|---|
| 2 | 203 | 0.25 | 0.46 | 0.773 | 0 | 0.0897 |
| 3 | 256 | 0.198 | 0.261 | 0.824 | 0 | 0.0857 |
| 4 | 292 | 0.151 | 0.195 | 0.873 | 0 | 0.0519 |
| 5 | 325 | 0.11 | 0.138 | 0.932 | 0 | 0.0607 |

## Error model (fitted on half the curves)

| term | coefficient |
|---|---|
| intercept | -0.38 |
| log10(SE(b)/|b|) | 0.157 |
| extrapolation distance (pH) | 0.341 |
| log10 n_mid | -0.61 |

Residual SD 0.59 (log10 units). Validation on the other half: rank correlation between predicted and actual edge error 0.52; truncations kept by the rule (predicted error <= 0.5 pH): 505 of 541, median actual error 0.17 pH.

## Census set under the slope-based rule

- Census-set rising/falling curves (development papers): 624
- Kept by the Stage 1 rule (core library): 30.4%
- Kept by the E5 rule (predicted edge error <= 0.5 pH): 89.9%

## Similar vs different curve pairs on a common window

Cross-paper pairs: 429; with a shared window of >= 2 pH and usable lines on it: 397. Spearman |edge difference| vs |pH-span difference|: native edges -0.05 (all pairs), -0.04 (same pairs as below); common-window edges 0.02. A drop towards zero means the span association was partly a coverage artefact.

Files: `truncations.csv`, `error_by_window.csv`, `error_model.csv`, `census_predicted_edge_error.csv`.
