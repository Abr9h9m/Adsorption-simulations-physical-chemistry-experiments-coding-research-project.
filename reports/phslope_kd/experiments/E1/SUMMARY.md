# E1 log10 K mixed model (two-step)

**Plain English.** Instead of fitting an S-curve to each experiment and throwing away the ones that do not show a full S, we fitted a straight line to how strongly the sorbate sticks (on a log scale) against pH, which works even for partial curves, and let a statistical model learn how the lines differ between sorbates, mineral-sorbate pairs and papers, and with the amount of mineral used. For a paper the model has not seen, it predicts where the curve crosses 50% to a median of 0.75 pH units, against 0.83 for the best simple rule (copying the closest-conditions papers). Verdict on the pre-declared rule: **ACCEPT**.

> EXPLORATORY. Development papers only; leave-out unit = E3 lineage cluster. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Formulation

Two-step (allowed by the protocol): per-curve log10 K lines, then REML models of the level at the pair's reference pH and of the slope, with random effects for sorbate class x direction, pair x direction and unit, and direction-specific solids and loading-hinge terms plus total sorbate, co-solute, CO2 and ionic strength for the level. The one-step random-slope model on all points was not run (not available at a usable speed with the installed tools). Loading breakpoint on all development data: -6.5 log10 mol/g (chosen inside each fold for the held-out runs).

## Decision rule (pre-declared)

- median native edge error <= B3 on pairs with >= 2 units: yes (0.751 vs 0.828)
- log10 K RMSE not worse than B3 (paired 95% interval lower bound <= 0): yes
- edge interval coverage in [0.80, 0.95]: yes (0.83)
- curve usage >= 70%: yes (77.5%; 641 curves)
- guard, not worse than B0 on pairs with >= 2 units: yes
- guard, no degradation on falling edges vs B3: yes
- **Verdict: ACCEPT**

## Edge error, pairs with >= 2 units (paired with all baselines)

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 459 | 99 | 0.751 | 0.541 | 0.944 | 0.3 | 1.51 | 1.52 | 0.39 | 0.608 | 0.882 | 0.849 | 0.354 |
| E1_no_covariates | 459 | 99 | 0.725 | 0.612 | 0.88 | 0.32 | 1.51 | 1.6 | 0.368 | 0.621 | 0.871 | 0.822 | 0.351 |
| B0_all_other | 459 | 99 | 0.816 | 0.659 | 1.01 | 0.28 | 1.57 | 1.58 | 0.353 | 0.582 | 0 | 0.941 | 0.314 |
| B1_nearest1 | 459 | 99 | 0.724 | 0.566 | 0.926 | 0.306 | 1.58 | 1.67 | 0.386 | 0.595 | 0 | 0.819 | 0.388 |
| B2_nearest3 | 459 | 99 | 0.731 | 0.576 | 0.958 | 0.336 | 1.5 | 1.56 | 0.397 | 0.612 | 0 | 0.852 | 0.368 |
| B3_matched_fb | 459 | 99 | 0.828 | 0.691 | 0.991 | 0.341 | 1.58 | 1.61 | 0.32 | 0.586 | 0 | 0.94 | 0.3 |
| B4_class_mean | 459 | 99 | 1.22 | 1.01 | 1.53 | 0.577 | 2.12 | 1.96 | 0.196 | 0.412 | 0 | 1.3 | 0.205 |
| B5_global_mean | 459 | 99 | 1.35 | 1.11 | 1.64 | 0.593 | 2.39 | 2.07 | 0.19 | 0.381 | 0 | 1.37 | 0.18 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B3_matched_fb | 459 | -0.0767 | -0.275 | 0.0516 | -0.0405 | -0.132 | 0.0666 | 0.751 | 0.828 | 0.534 | 0 |
| E1 | B0_all_other | 459 | -0.0649 | -0.209 | 0.0634 | -0.0297 | -0.113 | 0.0682 | 0.751 | 0.816 | 0.521 | 0 |
| E1 | B1_nearest1 | 459 | 0.0274 | -0.231 | 0.194 | -0.0441 | -0.1 | 0.0503 | 0.751 | 0.724 | 0.538 | 0 |
| E1 | B5_global_mean | 459 | -0.6 | -0.973 | -0.267 | -0.56 | -0.753 | -0.24 | 0.751 | 1.35 | 0.678 | 0 |
| E1 | E1_no_covariates | 459 | 0.0258 | -0.103 | 0.132 | -0.0533 | -0.0955 | -0.0171 | 0.751 | 0.725 | 0.601 | 0 |

Noise-ceiling fraction (share of the gap between the global mean B5 and the plain average B0 that E1 closes; 1 = as good as B0): 1.12 [0.87, 1.52], n = 459.

## Edge error, pairs with only 1 unit (E1 relies on class and covariates)

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 180 | 55 | 1.79 | 1.37 | 2.34 | 0.799 | 2.66 | 2.27 | 0.183 | 0.306 | 0.689 | 2.04 | 0.159 |
| E1_no_covariates | 182 | 56 | 1.78 | 1.43 | 2.22 | 0.759 | 2.82 | 2.29 | 0.176 | 0.319 | 0.637 | 2.09 | 0.154 |
| B4_class_mean | 180 | 55 | 1.72 | 1.37 | 2.29 | 0.799 | 2.84 | 2.31 | 0.156 | 0.3 | 0 | 1.87 | 0.121 |
| B5_global_mean | 182 | 56 | 1.93 | 1.21 | 2.47 | 0.753 | 3.22 | 2.44 | 0.143 | 0.352 | 0 | 1.9 | 0.115 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B4_class_mean | 178 | 0.0858 | -0.139 | 0.266 | -0.0857 | -0.181 | 0.0575 | 1.79 | 1.7 | 0.567 | 0 |
| E1 | B5_global_mean | 180 | -0.12 | -0.526 | 0.49 | -0.217 | -0.579 | 0.317 | 1.79 | 1.91 | 0.561 | 0 |

## Falling edges (guard)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B3_matched_fb | 147 | 0.0243 | -0.422 | 0.392 | 0.0719 | -0.243 | 0.278 | 1.11 | 1.09 | 0.469 | 0 |

## log10 K RMSE at the held-out curve's mid-range points (pairs with >= 2 units)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B3_matched_fb | 459 | 0.00822 | -0.102 | 0.0944 | 0.0189 | -0.0384 | 0.0826 | 0.644 | 0.635 | 0.466 | 0 |
| E1 | B0_all_other | 459 | 0.0234 | -0.0686 | 0.0827 | 0.00897 | -0.0273 | 0.0626 | 0.644 | 0.62 | 0.475 | 0 |

## Variance components (full development fit)

| target | class_dir | pair_dir | unit | residual | share_class_dir | share_pair_dir | share_unit | share_residual |
|---|---|---|---|---|---|---|---|---|
| level a_c | 0.00294 | 0.0115 | 0.128 | 0.209 | 0.00837 | 0.0327 | 0.364 | 0.595 |
| slope b | 0.0241 | 0.1 | 0.0561 | 0.0774 | 0.0935 | 0.389 | 0.218 | 0.3 |

## Level coefficients (full development fit; per unit of the covariate; level = log10 K at pH_c)

| term | estimate | se | ci_lo | ci_hi |
|---|---|---|---|---|
| intercept | 0.00952 | 0.201 | -0.384 | 0.403 |
| falling | 0.419 | 0.142 | 0.141 | 0.697 |
| solids_r | -0.178 | 0.0569 | -0.29 | -0.0667 |
| solids_f | -0.0533 | 0.0748 | -0.2 | 0.0932 |
| hinge_r | -0.1 | 0.0517 | -0.201 | 0.00124 |
| hinge_f | -0.309 | 0.0591 | -0.425 | -0.193 |
| log10_total | 0.0112 | 0.0226 | -0.033 | 0.0555 |
| cosolute | 0.0267 | 0.0926 | -0.155 | 0.208 |
| co2 | 0.00387 | 0.0759 | -0.145 | 0.153 |
| log10_I | -0.115 | 0.032 | -0.178 | -0.0524 |

## Curve usage

| set | curves |
|---|---|
| rising/falling with solids and total (development) | 827 |
| E1 main set (line usable) | 641 |
| Stage 1 core single-edge (development) | 233 |

Files: `heldout_predictions.csv`, `per_curve_worst_first.csv`, `summary_edge.csv`, `paired_differences.csv`, `variance_components.csv`, `coefficients.csv`, `curve_usage.csv`, `calibration.png`.

## Limitations

- Two-step: per-curve line uncertainty is not propagated into step 2 (lines are treated as exact); intervals rest on the fitted variance components.
- Lines are fitted over 3-97% sorbed only; bell and multi-step curves are excluded by the R2 >= 0.5 and direction rules (E2 revisits the window).
- The class labels are the unconfirmed proposal in classes.yaml.
