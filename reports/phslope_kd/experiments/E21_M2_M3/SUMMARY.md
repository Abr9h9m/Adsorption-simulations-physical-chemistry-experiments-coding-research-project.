# E21 calibrated intervals, M2 edge definitions, M3 fraction-sorbed error

**Plain English.** (1) Our 90% ranges for where a new paper's curve turns are checked two ways; result: **PREFER conformal** intervals. (2) Errors at the 20% and 80% points of the curve and in its width show whether the steepness is predicted as well as the midpoint. (3) The error a web-interface user would see, in fraction sorbed across the measured pH range, is reported for the model and the simple rules.

> EXPLORATORY. From E1's saved held-out predictions (development papers, lineage-cluster leave-out). Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## M2: absolute errors of alternative edge definitions (pH units)

| quantity | count | 25% | median_abs_error | 75% |
|---|---|---|---|---|
| pH20 | 639 | 0.404 | 0.895 | 1.85 |
| pH50 | 639 | 0.357 | 0.922 | 1.92 |
| pH80 | 639 | 0.386 | 1.05 | 2.18 |
| width | 639 | 0.354 | 0.71 | 1.47 |

## M3: mean absolute error in fraction sorbed over the measured points

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 459 | 99 | 0.118 | 0.106 | 0.152 | 0.075 | 0.221 |  | 0.978 | 1 |  | 0.14 | 0.958 |
| B0 | 459 | 99 | 0.12 | 0.104 | 0.15 | 0.078 | 0.232 |  | 0.985 | 1 |  | 0.139 | 0.973 |
| B3 | 459 | 99 | 0.122 | 0.104 | 0.156 | 0.078 | 0.241 |  | 0.976 | 1 |  | 0.143 | 0.97 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B0 | 459 | -0.00216 | -0.0175 | 0.0171 | -0.000679 | -0.00972 | 0.00591 | 0.118 | 0.12 | 0.516 | 0 |
| E1 | B3 | 459 | -0.0042 | -0.0239 | 0.0132 | -0.000715 | -0.011 | 0.00523 | 0.118 | 0.122 | 0.523 | 0 |

## E21: edge interval coverage and width (90% nominal)

| n | parametric_coverage | parametric_median_width | conformal_coverage | conformal_median_width | group |
|---|---|---|---|---|---|
| 639 | 0.828 | 4.8 | 0.897 | 5.57 | all |
| 182 | 0.868 | 5.92 | 0.901 | 5.57 | falling |
| 457 | 0.812 | 4.54 | 0.895 | 5.57 | rising |
| 180 | 0.689 | 4.95 | 0.783 | 5.56 | 1 unit |
| 210 | 0.852 | 4.94 | 0.919 | 5.57 | 2-3 units |
| 249 | 0.908 | 4.52 | 0.96 | 5.58 | 4+ units |

Decision rule: coverage in [0.85, 0.95] with the narrower width -> **PREFER conformal**.
