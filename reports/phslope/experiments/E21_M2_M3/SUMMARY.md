# E21 calibrated intervals, M2 edge definitions, M3 fraction-sorbed error

**Plain English.** (1) Our 90% ranges for where a new paper's curve turns are checked two ways; result: **PREFER conformal** intervals. (2) Errors at the 20% and 80% points of the curve and in its width show whether the steepness is predicted as well as the midpoint. (3) The error a web-interface user would see, in fraction sorbed across the measured pH range, is reported for the model and the simple rules.

> EXPLORATORY. From E1's saved held-out predictions (development papers, lineage-cluster leave-out). Locked set hash `88b1c3a1b769`. Commit `c835343-dirty`.

## M2: absolute errors of alternative edge definitions (pH units)

| quantity | count | 25% | median_abs_error | 75% |
|---|---|---|---|---|
| pH20 | 757 | 0.497 | 0.989 | 1.83 |
| pH50 | 757 | 0.445 | 1.1 | 1.9 |
| pH80 | 757 | 0.545 | 1.22 | 2.09 |
| width | 757 | 0.347 | 0.806 | 1.3 |

## M3: mean absolute error in fraction sorbed over the measured points

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 535 | 107 | 0.153 | 0.14 | 0.167 | 0.102 | 0.248 |  | 0.974 | 1 |  | 0.158 | 0.974 |
| B0 | 535 | 107 | 0.161 | 0.141 | 0.179 | 0.0983 | 0.262 |  | 0.959 | 1 |  | 0.166 | 0.969 |
| B3 | 535 | 107 | 0.163 | 0.137 | 0.195 | 0.0938 | 0.275 |  | 0.951 | 1 |  | 0.172 | 0.967 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B0 | 535 | -0.00806 | -0.0263 | 0.0104 | -0.00659 | -0.0162 | 0.00196 | 0.153 | 0.161 | 0.551 | 0 |
| E1 | B3 | 535 | -0.0109 | -0.0361 | 0.0156 | -0.00688 | -0.0189 | 0.00284 | 0.153 | 0.163 | 0.538 | 0 |

## E21: edge interval coverage and width (90% nominal)

| n | parametric_coverage | parametric_median_width | conformal_coverage | conformal_median_width | group |
|---|---|---|---|---|---|
| 757 | 0.853 | 5.91 | 0.897 | 5.87 | all |
| 221 | 0.891 | 7.88 | 0.905 | 5.88 | falling |
| 536 | 0.838 | 5.55 | 0.894 | 5.87 | rising |
| 222 | 0.743 | 6.05 | 0.788 | 5.87 | 1 unit |
| 280 | 0.886 | 5.87 | 0.936 | 5.87 | 2-3 units |
| 255 | 0.914 | 5.76 | 0.949 | 5.88 | 4+ units |

Decision rule: coverage in [0.85, 0.95] with the narrower width -> **PREFER conformal**.
