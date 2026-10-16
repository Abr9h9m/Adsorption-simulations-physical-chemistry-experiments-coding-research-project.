# E15 Model bake-off and how much random splits overstate skill

**Plain English.** Machine-learning studies on compiled sorption data often test models by hiding a random 20% of the data points. Points from the same experiment then sit on both sides of the split, so the model mostly 'remembers' the experiment. We compared that with hiding whole papers, which is what predicting new work requires. Model choice under the honest test: **ADOPT random_forest, gradient_boosting**.

> EXPLORATORY. Development papers only; grouped split = 20 folds of whole lineage units (all models on the same folds). Target: log10 K at mid-range points (6,155 points, 641 curves). Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Median per-curve log10 K RMSE, by split

| model | grouped (whole units) | random 80/20 by point | inflation (grouped / random) |
|---|---|---|---|
| B0_all_other | 0.616 | 0.368 | 1.67 |
| B5_global_mean | 1.21 | 1.15 | 1.05 |
| E1_final | 0.764 | 0.316 | 2.42 |
| gradient_boosting | 0.472 | 0.192 | 2.46 |
| random_forest | 0.604 | 0.254 | 2.38 |

An inflation factor above 1 means the random split makes the model look that many times better than it is for new papers.

## Full summaries

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted | split |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| random_forest | 641 | 134 | 0.604 | 0.56 | 0.673 | 0.404 | 0.831 |  | 0.362 | 0.874 |  | 0.6 | 0.361 | grouped (whole units) |
| gradient_boosting | 641 | 134 | 0.472 | 0.428 | 0.526 | 0.323 | 0.72 |  | 0.538 | 0.93 |  | 0.489 | 0.514 | grouped (whole units) |
| B0_all_other | 457 | 98 | 0.616 | 0.537 | 0.702 | 0.401 | 0.947 |  | 0.396 | 0.777 |  | 0.67 | 0.366 | grouped (whole units) |
| B5_global_mean | 641 | 134 | 1.21 | 1.08 | 1.33 | 0.773 | 1.76 |  | 0.111 | 0.368 |  | 1.27 | 0.0931 | grouped (whole units) |
| E1_final | 639 | 133 | 0.764 | 0.683 | 0.852 | 0.479 | 1.35 |  | 0.269 | 0.626 |  | 0.83 | 0.268 | grouped (whole units) |
| B0_all_other | 638 | 134 | 0.368 | 0.326 | 0.42 | 0.213 | 0.657 |  | 0.632 | 0.903 |  | 0.355 | 0.627 | random 80/20 by point |
| B5_global_mean | 638 | 134 | 1.15 | 1.01 | 1.25 | 0.676 | 1.68 |  | 0.139 | 0.429 |  | 1.16 | 0.124 | random 80/20 by point |
| E1_final | 636 | 133 | 0.316 | 0.285 | 0.34 | 0.194 | 0.5 |  | 0.75 | 0.962 |  | 0.322 | 0.713 | random 80/20 by point |
| gradient_boosting | 638 | 134 | 0.192 | 0.179 | 0.206 | 0.128 | 0.288 |  | 0.936 | 0.992 |  | 0.199 | 0.902 | random 80/20 by point |
| random_forest | 638 | 134 | 0.254 | 0.228 | 0.274 | 0.165 | 0.394 |  | 0.868 | 0.989 |  | 0.269 | 0.831 | random 80/20 by point |

## E1 minus each alternative (negative = E1 better; difference of medians, interval over units)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | split |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1_final | random_forest | 639 | 0.161 | 0.0692 | 0.242 | 0.206 | 0.0973 | 0.327 | 0.764 | 0.603 | 0.363 | 0 | grouped (whole units) |
| E1_final | gradient_boosting | 639 | 0.293 | 0.223 | 0.375 | 0.28 | 0.207 | 0.36 | 0.764 | 0.471 | 0.228 | 0 | grouped (whole units) |
| E1_final | B0_all_other | 457 | 0.0405 | -0.0455 | 0.141 | 0.0463 | -0.0264 | 0.132 | 0.657 | 0.616 | 0.442 | 0 | grouped (whole units) |
| E1_final | B5_global_mean | 639 | -0.439 | -0.56 | -0.297 | -0.344 | -0.442 | -0.227 | 0.764 | 1.2 | 0.681 | 0 | grouped (whole units) |
| E1_final | random_forest | 636 | 0.0628 | 0.0241 | 0.0922 | 0.0525 | 0.0253 | 0.083 | 0.316 | 0.253 | 0.384 | 0 | random 80/20 by point |
| E1_final | gradient_boosting | 636 | 0.125 | 0.092 | 0.149 | 0.0905 | 0.0711 | 0.119 | 0.316 | 0.191 | 0.263 | 0 | random 80/20 by point |
| E1_final | B0_all_other | 636 | -0.0526 | -0.112 | -0.0191 | -0.043 | -0.0739 | -0.0184 | 0.316 | 0.369 | 0.626 | 0 | random 80/20 by point |
| E1_final | B5_global_mean | 636 | -0.832 | -0.938 | -0.704 | -0.706 | -0.832 | -0.605 | 0.316 | 1.15 | 0.912 | 0 | random 80/20 by point |

## E15b: edge position from gradient boosting (same grouped folds)

Gradient boosting predicts log10 K on a fine pH grid at each held-out curve's conditions; its edge is where that crosses 0. E1_final edges are the integration run's leave-one-unit-out predictions.

| subset | model | n | median | median_lo | median_hi | within_0_5 | median_paper_weighted |
|---|---|---|---|---|---|---|---|
| pairs with >= 2 units | gbm_edge | 459 | 0.77 | 0.572 | 0.98 | 0.386 | 0.847 |
| pairs with >= 2 units | E1_final | 459 | 0.765 | 0.585 | 0.916 | 0.375 | 0.798 |
| pairs with >= 2 units | B0_all_other | 459 | 0.816 | 0.658 | 1.01 | 0.353 | 0.941 |
| pairs with >= 2 units | B3_matched_fb | 459 | 0.828 | 0.672 | 1.02 | 0.32 | 0.94 |
| pairs with 1 unit | gbm_edge | 180 | 1.35 | 1.02 | 1.8 | 0.183 | 1.44 |
| pairs with 1 unit | E1_final | 180 | 1.88 | 1.4 | 2.42 | 0.183 | 2.19 |

gbm minus each model (negative = gbm better):

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | subset |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gbm_edge | E1_final | 459 | 0.00456 | -0.209 | 0.238 | -0.0329 | -0.108 | 0.0481 | 0.77 | 0.765 | 0.538 | 0 | pairs with >= 2 units |
| gbm_edge | B0_all_other | 459 | -0.0463 | -0.301 | 0.152 | -0.0519 | -0.193 | 0.0401 | 0.77 | 0.816 | 0.547 | 0 | pairs with >= 2 units |
| gbm_edge | B3_matched_fb | 459 | -0.0581 | -0.331 | 0.146 | -0.106 | -0.235 | 0.0329 | 0.77 | 0.828 | 0.562 | 0 | pairs with >= 2 units |
| gbm_edge | E1_final | 180 | -0.527 | -1.16 | 0.154 | -0.175 | -0.589 | 0.151 | 1.35 | 1.88 | 0.594 | 0 | pairs with 1 unit |

## E15c: gradient boosting follow-ups (feature ablation, fraction error, conformal intervals)

Same 20 grouped folds. Edge errors are on all E1 main-set curves (single- and multi-unit pairs). Fraction MAE = mean |predicted - observed fraction sorbed| over the curve's measured points (E21/M3: E1 0.153, B0 0.161, B3 0.163 on multi-unit pairs). Conformal = paper-level CV+.

| feature_set | n | median_edge_error | median_edge_error_multi_unit_pairs | median_edge_error_single_unit_pairs | median_fraction_mae | conformal_coverage | conformal_median_width |
|---|---|---|---|---|---|---|---|
| full | 641 | 0.932 | 0.77 | 1.37 | 0.137 | 0.897 | 5.95 |
| no_conditions | 641 | 1.02 | 0.864 | 1.42 | 0.165 | 0.899 | 6.55 |
| no_identity | 641 | 1.3 | 1.27 | 1.45 | 0.194 | 0.899 | 8.2 |

Coverage by pair size:

| feature_set | pair_size | n | coverage |
|---|---|---|---|
| full | 1 unit | 182 | 0.819 |
| full | 2-3 units | 210 | 0.914 |
| full | 4+ units | 249 | 0.94 |
| no_conditions | 1 unit | 182 | 0.879 |
| no_conditions | 2-3 units | 210 | 0.871 |
| no_conditions | 4+ units | 249 | 0.936 |
| no_identity | 1 unit | 182 | 0.896 |
| no_identity | 2-3 units | 210 | 0.867 |
| no_identity | 4+ units | 249 | 0.928 |
