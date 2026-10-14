# E15 Model bake-off and how much random splits overstate skill

**Plain English.** Machine-learning studies on compiled sorption data often test models by hiding a random 20% of the data points. Points from the same experiment then sit on both sides of the split, so the model mostly 'remembers' the experiment. We compared that with hiding whole papers, which is what predicting new work requires. Model choice under the honest test: **ADOPT random_forest, gradient_boosting**.

> EXPLORATORY. Development papers only; grouped split = 20 folds of whole lineage units (all models on the same folds). Target: log10 K at mid-range points (7,473 points, 757 curves). Locked set hash `88b1c3a1b769`. Commit `deab33c`.

## Median per-curve log10 K RMSE, by split

| model | grouped (whole units) | random 80/20 by point | inflation (grouped / random) |
|---|---|---|---|
| B0_all_other | 0.705 | 0.412 | 1.71 |
| B5_global_mean | 1.09 | 1.01 | 1.08 |
| E1_final | 0.769 | 0.321 | 2.4 |
| gradient_boosting | 0.517 | 0.186 | 2.79 |
| random_forest | 0.593 | 0.246 | 2.41 |

An inflation factor above 1 means the random split makes the model look that many times better than it is for new papers.

## Full summaries

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted | split |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| random_forest | 757 | 143 | 0.593 | 0.547 | 0.637 | 0.424 | 0.799 |  | 0.374 | 0.897 |  | 0.58 | 0.362 | grouped (whole units) |
| gradient_boosting | 757 | 143 | 0.517 | 0.488 | 0.553 | 0.358 | 0.698 |  | 0.468 | 0.897 |  | 0.509 | 0.488 | grouped (whole units) |
| B0_all_other | 530 | 107 | 0.705 | 0.638 | 0.779 | 0.44 | 1.09 |  | 0.302 | 0.704 |  | 0.739 | 0.282 | grouped (whole units) |
| B5_global_mean | 757 | 143 | 1.09 | 0.986 | 1.24 | 0.694 | 1.65 |  | 0.145 | 0.44 |  | 1.18 | 0.115 | grouped (whole units) |
| E1_final | 757 | 143 | 0.769 | 0.685 | 0.906 | 0.468 | 1.27 |  | 0.275 | 0.641 |  | 0.919 | 0.218 | grouped (whole units) |
| B0_all_other | 752 | 142 | 0.412 | 0.368 | 0.484 | 0.225 | 0.703 |  | 0.578 | 0.871 |  | 0.37 | 0.62 | random 80/20 by point |
| B5_global_mean | 752 | 142 | 1.01 | 0.914 | 1.18 | 0.606 | 1.56 |  | 0.174 | 0.495 |  | 1.09 | 0.137 | random 80/20 by point |
| E1_final | 752 | 142 | 0.321 | 0.296 | 0.343 | 0.194 | 0.486 |  | 0.759 | 0.956 |  | 0.333 | 0.745 | random 80/20 by point |
| gradient_boosting | 752 | 142 | 0.186 | 0.173 | 0.202 | 0.128 | 0.29 |  | 0.939 | 0.997 |  | 0.208 | 0.909 | random 80/20 by point |
| random_forest | 752 | 142 | 0.246 | 0.224 | 0.266 | 0.167 | 0.399 |  | 0.876 | 0.995 |  | 0.28 | 0.817 | random 80/20 by point |

## E1 minus each alternative (negative = E1 better; difference of medians, interval over units)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | split |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1_final | random_forest | 757 | 0.176 | 0.0727 | 0.323 | 0.227 | 0.112 | 0.322 | 0.769 | 0.593 | 0.328 | 0 | grouped (whole units) |
| E1_final | gradient_boosting | 757 | 0.252 | 0.157 | 0.383 | 0.268 | 0.176 | 0.347 | 0.769 | 0.517 | 0.281 | 0 | grouped (whole units) |
| E1_final | B0_all_other | 530 | -0.014 | -0.136 | 0.0797 | -0.00479 | -0.0565 | 0.0619 | 0.691 | 0.705 | 0.504 | 0 | grouped (whole units) |
| E1_final | B5_global_mean | 757 | -0.322 | -0.482 | -0.183 | -0.225 | -0.312 | -0.167 | 0.769 | 1.09 | 0.683 | 0 | grouped (whole units) |
| E1_final | random_forest | 752 | 0.0747 | 0.0456 | 0.111 | 0.0533 | 0.0202 | 0.0913 | 0.321 | 0.246 | 0.388 | 0 | random 80/20 by point |
| E1_final | gradient_boosting | 752 | 0.135 | 0.107 | 0.16 | 0.104 | 0.0759 | 0.138 | 0.321 | 0.186 | 0.25 | 0 | random 80/20 by point |
| E1_final | B0_all_other | 752 | -0.0911 | -0.15 | -0.0414 | -0.0437 | -0.0885 | -0.0239 | 0.321 | 0.412 | 0.618 | 0 | random 80/20 by point |
| E1_final | B5_global_mean | 752 | -0.692 | -0.834 | -0.591 | -0.641 | -0.751 | -0.54 | 0.321 | 1.01 | 0.863 | 0 | random 80/20 by point |

## E15b: edge position from gradient boosting (same grouped folds)

Gradient boosting predicts log10 K on a fine pH grid at each held-out curve's conditions; its edge is where that crosses 0. E1_final edges are the integration run's leave-one-unit-out predictions.

| subset | model | n | median | median_lo | median_hi | within_0_5 | median_paper_weighted |
|---|---|---|---|---|---|---|---|
| pairs with >= 2 units | gbm_edge | 535 | 0.722 | 0.555 | 0.88 | 0.379 | 0.819 |
| pairs with >= 2 units | E1_final | 535 | 0.801 | 0.604 | 0.978 | 0.361 | 0.952 |
| pairs with >= 2 units | B0_all_other | 535 | 0.988 | 0.822 | 1.25 | 0.271 | 1.1 |
| pairs with >= 2 units | B3_matched_fb | 535 | 0.962 | 0.791 | 1.2 | 0.303 | 1.14 |
| pairs with 1 unit | gbm_edge | 222 | 1.08 | 0.806 | 1.47 | 0.266 | 1.23 |
| pairs with 1 unit | E1_final | 222 | 1.73 | 1.41 | 2.01 | 0.158 | 1.96 |

gbm minus each model (negative = gbm better):

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | subset |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gbm_edge | E1_final | 535 | -0.0787 | -0.24 | 0.0827 | -0.0474 | -0.207 | 0.0616 | 0.722 | 0.801 | 0.54 | 0 | pairs with >= 2 units |
| gbm_edge | B0_all_other | 535 | -0.266 | -0.445 | -0.143 | -0.197 | -0.335 | -0.107 | 0.722 | 0.988 | 0.639 | 0 | pairs with >= 2 units |
| gbm_edge | B3_matched_fb | 535 | -0.24 | -0.398 | -0.111 | -0.163 | -0.28 | -0.0954 | 0.722 | 0.962 | 0.639 | 0 | pairs with >= 2 units |
| gbm_edge | E1_final | 222 | -0.652 | -1.01 | -0.23 | -0.454 | -0.683 | -0.19 | 1.08 | 1.73 | 0.658 | 0 | pairs with 1 unit |

## Analyst notes

- **Under honest (grouped) validation, gradient boosting beats the mixed model** on held-out log10 K (median per-curve RMSE 0.52 vs 0.77; E1 minus GBM +0.25 [0.16, 0.38]) and on the edge (0.72 vs 0.80 pH on pairs with >= 2 units, difference not significant; 1.08 vs 1.73 pH on pairs measured by a single unit, -0.65 [-1.01, -0.23]). Against the simple rules it is significantly better (vs B3 -0.24 [-0.40, -0.11]), which E1 never achieved. Pre-declared decision: ADOPT a flexible model.
- Why: it uses mineral and sorbate identities SEPARATELY (it can combine "goethite" knowledge and "U(VI)" knowledge for a pair it has not seen) and allows log10 K to bend with pH; E1 uses class-level effects for unseen pairs and a straight line.
- Fairness: GBM used 20 grouped folds (~95% of units for training), E1's edges come from leave-one-unit-out (~99%), so the edge comparison is conservative for GBM. No hyperparameters were tuned.
- **Random 80/20 point splits overstate skill 1.7-2.8x** (E1 2.4x, gradient boosting 2.8x, random forest 2.4x, B0 1.7x): a careless split makes every model look much better than it is for new papers, and flexible models most of all.
- On log10 K at each point, E1 is not better than the plain average of other papers (-0.01 [-0.14, +0.08]); its edge advantage over B0 comes from the edge summary, not from the whole curve.
- Not yet done for GBM: calibrated intervals (E21-style conformal at paper level is the natural next step), the M3 fraction-sorbed metric, and ablation of the identity features (how much is mineral/sorbate identity vs conditions).

## E15c: gradient boosting follow-ups (feature ablation, fraction error, conformal intervals)

Same 20 grouped folds. Edge errors are on all E1 main-set curves (single- and multi-unit pairs). Fraction MAE = mean |predicted - observed fraction sorbed| over the curve's measured points (E21/M3: E1 0.153, B0 0.161, B3 0.163 on multi-unit pairs). Conformal = paper-level CV+.

| feature_set | n | median_edge_error | median_edge_error_multi_unit_pairs | median_edge_error_single_unit_pairs | median_fraction_mae | conformal_coverage | conformal_median_width |
|---|---|---|---|---|---|---|---|
| full | 757 | 0.813 | 0.722 | 1.08 | 0.164 | 0.901 | 5.45 |
| no_conditions | 757 | 1.09 | 0.933 | 1.35 | 0.197 | 0.897 | 6.42 |
| no_identity | 757 | 1.19 | 1.07 | 1.48 | 0.21 | 0.9 | 7.85 |

Coverage by pair size:

| feature_set | pair_size | n | coverage |
|---|---|---|---|
| full | 1 unit | 222 | 0.833 |
| full | 2-3 units | 280 | 0.911 |
| full | 4+ units | 255 | 0.949 |
| no_conditions | 1 unit | 222 | 0.856 |
| no_conditions | 2-3 units | 280 | 0.946 |
| no_conditions | 4+ units | 255 | 0.878 |
| no_identity | 1 unit | 222 | 0.892 |
| no_identity | 2-3 units | 280 | 0.918 |
| no_identity | 4+ units | 255 | 0.886 |
