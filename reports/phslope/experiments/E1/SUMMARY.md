# E1 log10 K mixed model (two-step)

**Plain English.** Instead of fitting an S-curve to each experiment and throwing away the ones that do not show a full S, we fitted a straight line to how strongly the sorbate sticks (on a log scale) against pH, which works even for partial curves, and let a statistical model learn how the lines differ between sorbates, mineral-sorbate pairs and papers, and with the amount of mineral used. For a paper the model has not seen, it predicts where the curve crosses 50% to a median of 0.88 pH units, against 0.96 for the best simple rule (copying the closest-conditions papers). Verdict on the pre-declared rule: **ACCEPT**.

> EXPLORATORY. Development papers only; leave-out unit = E3 lineage cluster. Locked set hash `88b1c3a1b769`. Commit `353c5ee-dirty`.

## Formulation

Two-step (allowed by the protocol): per-curve log10 K lines, then REML models of the level at the pair's reference pH and of the slope, with random effects for sorbate class x direction, pair x direction and unit, and direction-specific solids and loading-hinge terms plus total sorbate, co-solute, CO2 and ionic strength for the level. The one-step random-slope model on all points was not run (not available at a usable speed with the installed tools). Loading breakpoint on all development data: -5.5 log10 mol/g (chosen inside each fold for the held-out runs).

## Decision rule (pre-declared)

- median native edge error <= B3 on pairs with >= 2 units: yes (0.882 vs 0.962)
- log10 K RMSE not worse than B3 (paired 95% interval lower bound <= 0): yes
- edge interval coverage in [0.80, 0.95]: yes (0.85)
- curve usage >= 70%: yes (81.3%; 757 curves)
- guard, not worse than B0 on pairs with >= 2 units: yes
- guard, no degradation on falling edges vs B3: yes
- **Verdict: ACCEPT**

## Edge error, pairs with >= 2 units (paired with all baselines)

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 535 | 107 | 0.882 | 0.672 | 1.12 | 0.368 | 1.61 | 1.49 | 0.336 | 0.548 | 0.899 |
| E1_no_covariates | 535 | 107 | 0.992 | 0.792 | 1.26 | 0.415 | 1.99 | 1.7 | 0.297 | 0.505 | 0.886 |
| B0_all_other | 535 | 107 | 0.988 | 0.82 | 1.25 | 0.421 | 1.79 | 1.63 | 0.271 | 0.505 | 0 |
| B1_nearest1 | 535 | 107 | 0.973 | 0.741 | 1.21 | 0.407 | 1.82 | 1.7 | 0.318 | 0.521 | 0 |
| B2_nearest3 | 535 | 107 | 0.867 | 0.708 | 1.13 | 0.354 | 1.78 | 1.64 | 0.351 | 0.55 | 0 |
| B3_matched_fb | 535 | 107 | 0.962 | 0.782 | 1.21 | 0.364 | 1.79 | 1.61 | 0.303 | 0.52 | 0 |
| B4_class_mean | 535 | 107 | 1.14 | 0.977 | 1.35 | 0.53 | 2.05 | 1.93 | 0.245 | 0.437 | 0 |
| B5_global_mean | 535 | 107 | 1.34 | 1 | 1.56 | 0.606 | 2.17 | 1.99 | 0.207 | 0.413 | 0 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | model_median | baseline_median |
|---|---|---|---|---|---|---|---|
| E1 | B3_matched_fb | 535 | -0.0808 | -0.157 | 0.00238 | 0.882 | 0.962 |
| E1 | B0_all_other | 535 | -0.0861 | -0.163 | 0.00024 | 0.882 | 0.988 |
| E1 | B1_nearest1 | 535 | -0.126 | -0.203 | -0.0094 | 0.882 | 0.973 |
| E1 | B5_global_mean | 535 | -0.35 | -0.712 | -0.105 | 0.882 | 1.34 |
| E1 | E1_no_covariates | 535 | -0.101 | -0.19 | -0.0307 | 0.882 | 0.992 |

Noise-ceiling fraction (share of the gap between the global mean B5 and the plain average B0 that E1 closes; 1 = as good as B0): 1.30 [-0.97, 7.26], n = 535.

## Edge error, pairs with only 1 unit (E1 relies on class and covariates)

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 222 | 66 | 1.73 | 1.45 | 1.96 | 0.853 | 2.65 | 2.34 | 0.149 | 0.27 | 0.743 |
| E1_no_covariates | 222 | 66 | 1.67 | 1.43 | 1.93 | 0.86 | 2.31 | 2.15 | 0.158 | 0.279 | 0.824 |
| B4_class_mean | 221 | 65 | 1.71 | 1.53 | 1.93 | 0.929 | 2.47 | 2.17 | 0.131 | 0.29 | 0 |
| B5_global_mean | 222 | 66 | 1.94 | 1.55 | 2.26 | 0.88 | 2.86 | 2.32 | 0.108 | 0.27 | 0 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | model_median | baseline_median |
|---|---|---|---|---|---|---|---|
| E1 | B4_class_mean | 221 | 0.0694 | -0.0711 | 0.122 | 1.72 | 1.71 |
| E1 | B5_global_mean | 222 | -0.187 | -0.472 | 0.0558 | 1.73 | 1.94 |

## Falling edges (guard)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | model_median | baseline_median |
|---|---|---|---|---|---|---|---|
| E1 | B3_matched_fb | 166 | -0.268 | -0.501 | -0.04 | 0.958 | 1.19 |

## log10 K RMSE at the held-out curve's mid-range points (pairs with >= 2 units)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | model_median | baseline_median |
|---|---|---|---|---|---|---|---|
| E1 | B3_matched_fb | 535 | -0.0202 | -0.0707 | 0.0381 | 0.689 | 0.706 |
| E1 | B0_all_other | 535 | -0.0239 | -0.0683 | 0.0334 | 0.689 | 0.706 |

## Variance components (full development fit)

| target | class_dir | pair_dir | unit | residual | share_class_dir | share_pair_dir | share_unit | share_residual |
|---|---|---|---|---|---|---|---|---|
| level a_c | 1.54e-09 | 0.084 | 0.187 | 0.237 | 3.03e-09 | 0.165 | 0.368 | 0.467 |
| slope b | 0.0432 | 0.0725 | 0.037 | 0.0808 | 0.185 | 0.31 | 0.159 | 0.346 |

## Level coefficients (full development fit; per unit of the covariate; level = log10 K at pH_c)

| term | estimate | se | ci_lo | ci_hi |
|---|---|---|---|---|
| intercept | -0.168 | 0.182 | -0.525 | 0.189 |
| falling | 0.388 | 0.123 | 0.146 | 0.63 |
| solids_r | 0.114 | 0.0461 | 0.0232 | 0.204 |
| solids_f | 0.357 | 0.0687 | 0.222 | 0.491 |
| hinge_r | -0.162 | 0.0569 | -0.273 | -0.0504 |
| hinge_f | -0.41 | 0.0612 | -0.53 | -0.29 |
| log10_total | 0.00307 | 0.022 | -0.04 | 0.0462 |
| cosolute | -0.271 | 0.088 | -0.444 | -0.0985 |
| co2 | 0.0393 | 0.0845 | -0.126 | 0.205 |
| log10_I | -0.169 | 0.0331 | -0.234 | -0.105 |

## Curve usage

| set | curves |
|---|---|
| rising/falling with solids and total (development) | 931 |
| E1 main set (line usable) | 757 |
| Stage 1 core single-edge (development) | 316 |

Files: `heldout_predictions.csv`, `per_curve_worst_first.csv`, `summary_edge.csv`, `paired_differences.csv`, `variance_components.csv`, `coefficients.csv`, `curve_usage.csv`, `calibration.png`.

## Limitations

- Two-step: per-curve line uncertainty is not propagated into step 2 (lines are treated as exact); intervals rest on the fitted variance components.
- Lines are fitted over 3-97% sorbed only; bell and multi-step curves are excluded by the R2 >= 0.5 and direction rules (E2 revisits the window).
- The class labels are the unconfirmed proposal in classes.yaml.
