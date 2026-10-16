# Stage 3 summary: can we predict a held-out system's slope curve?

> **EXPLORATORY.** Stage 1 failed its survival rule; classes are the unconfirmed proposal; thresholds.yaml is not frozen (frozen: false). Feature sets other than `descriptors` use the uncited mineral property table and Claude's proposed sorbate schemes. Nothing here is a confirmatory result.

Run: commit `d468a46`, config `7683c4e695c4`, data `library: C:\Users\itzju\Mineral Fingerprinting\reports\phslope_kd\stage1\library`, 2026-10-16T12:38:07Z.

Data: 286 single-edge (rising/falling) core curves, 105 papers, 88 mineral-sorbate pairs.

Feature sets used: `properties` (59 features, 180 curves with every feature), `conditions` (4 features, 286 curves with every feature).
Not used: `descriptors`: descriptor tables are empty or too sparse ({'n_features': 4, 'n_curves': 286, 'n_complete': 286}).

Without the descriptor tables the edge-position rule baseline (edge from PZC and first hydrolysis constant), the one the spec says decides whether the project says anything new, cannot run.

## Verdict per model and level (thresholds.yaml stage3)

Pass = median edge error <= 0.5 pH, slope-interval coverage in [0.8, 0.95], and better than every baseline (95% interval of the paired difference below zero, for edge error and curve error).

| level | model | median_p50_error | p50_ok | interval_coverage | coverage_ok | beats_every_baseline | verdict |
|---|---|---|---|---|---|---|---|
| mineral | version_a@conditions | 1.15 | False | 0.875 | True | False | FAIL |
| mineral | version_a@properties | 1.21 | False | 0.876 | True | False | FAIL |
| mineral | version_b@conditions | 1.15 | False | 0.876 | True | False | FAIL |
| mineral | version_b@properties | 1.21 | False | 0.88 | True | False | FAIL |
| pair | version_a@conditions | 1.18 | False | 0.876 | True | False | FAIL |
| pair | version_a@properties | 1.42 | False | 0.853 | True | False | FAIL |
| pair | version_b@conditions | 1.18 | False | 0.877 | True | False | FAIL |
| pair | version_b@properties | 1.42 | False | 0.856 | True | False | FAIL |
| sorbate | version_a@conditions | 1.23 | False | 0.86 | True | False | FAIL |
| sorbate | version_a@properties | 1.91 | False | 0.838 | True | False | FAIL |
| sorbate | version_b@conditions | 1.23 | False | 0.861 | True | False | FAIL |
| sorbate | version_b@properties | 1.91 | False | 0.837 | True | False | FAIL |
| study | version_a@conditions | 1.18 | False | 0.882 | True | False | FAIL |
| study | version_a@properties | 1.1 | False | 0.885 | True | False | FAIL |
| study | version_b@conditions | 1.18 | False | 0.881 | True | False | FAIL |
| study | version_b@properties | 1.1 | False | 0.885 | True | False | FAIL |

## Metrics by model

| level | model | n_curves | n_groups | median_p50_error | p50_error_q25 | p50_error_q75 | median_curve_error | median_curve_error_unweighted | shape_correct | sign_correct | interval_coverage | p50_coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mineral | global_mean | 286 | 25 | 1.12 | 0.523 | 2 | 0.0739 | 0.419 | 0.696 | 0.608 | 0.877 | 0.902 |
| mineral | mineral_class_mean | 286 | 25 | 1.19 | 0.555 | 2.15 | 0.0866 | 0.443 | 0.696 | 0.587 | 0.876 | 0.899 |
| mineral | sorbate_class_mean | 286 | 25 | 1.1 | 0.502 | 1.99 | 0.111 | 0.419 | 0.986 | 0.853 | 0.875 | 0.871 |
| mineral | version_a@conditions | 286 | 25 | 1.15 | 0.57 | 1.88 | 0.0792 | 0.444 | 0.689 | 0.605 | 0.875 | 0.895 |
| mineral | version_a@properties | 180 | 15 | 1.21 | 0.561 | 2 | 0.0913 | 0.464 | 0.989 | 0.772 | 0.876 | 0.856 |
| mineral | version_b@conditions | 286 | 25 | 1.15 | 0.57 | 1.88 | 0.0775 | 0.449 | 0.689 | 0.619 | 0.876 | 0.895 |
| mineral | version_b@properties | 180 | 15 | 1.21 | 0.561 | 2 | 0.103 | 0.457 | 0.989 | 0.778 | 0.88 | 0.856 |
| pair | global_mean | 286 | 88 | 1.1 | 0.504 | 1.99 | 0.0717 | 0.431 | 0.696 | 0.626 | 0.874 | 0.895 |
| pair | mineral_class_mean | 286 | 88 | 1.14 | 0.46 | 2.11 | 0.0606 | 0.455 | 0.696 | 0.605 | 0.872 | 0.895 |
| pair | sorbate_class_mean | 286 | 88 | 1.18 | 0.483 | 2.01 | 0.11 | 0.418 | 0.986 | 0.836 | 0.877 | 0.867 |
| pair | version_a@conditions | 286 | 88 | 1.18 | 0.585 | 1.9 | 0.072 | 0.445 | 0.678 | 0.612 | 0.876 | 0.892 |
| pair | version_a@properties | 180 | 52 | 1.42 | 0.7 | 2.39 | 0.104 | 0.429 | 0.983 | 0.761 | 0.853 | 0.8 |
| pair | version_b@conditions | 286 | 88 | 1.18 | 0.585 | 1.9 | 0.0673 | 0.446 | 0.678 | 0.626 | 0.877 | 0.892 |
| pair | version_b@properties | 180 | 52 | 1.42 | 0.7 | 2.39 | 0.103 | 0.441 | 0.983 | 0.772 | 0.856 | 0.8 |
| sorbate | global_mean | 286 | 31 | 1.15 | 0.549 | 2.16 | 0.0764 | 0.432 | 0.696 | 0.619 | 0.856 | 0.878 |
| sorbate | mineral_class_mean | 286 | 31 | 1.16 | 0.47 | 2.23 | 0.0787 | 0.454 | 0.664 | 0.573 | 0.859 | 0.881 |
| sorbate | sorbate_class_mean | 286 | 31 | 1.53 | 0.614 | 2.57 | 0.128 | 0.443 | 0.986 | 0.759 | 0.861 | 0.776 |
| sorbate | version_a@conditions | 286 | 31 | 1.23 | 0.625 | 2.15 | 0.0777 | 0.456 | 0.58 | 0.5 | 0.86 | 0.867 |
| sorbate | version_a@properties | 180 | 24 | 1.91 | 1.02 | 3.05 | 0.179 | 0.461 | 0.983 | 0.628 | 0.838 | 0.7 |
| sorbate | version_b@conditions | 286 | 31 | 1.23 | 0.625 | 2.15 | 0.0762 | 0.462 | 0.58 | 0.507 | 0.861 | 0.867 |
| sorbate | version_b@properties | 180 | 24 | 1.91 | 1.02 | 3.05 | 0.171 | 0.468 | 0.983 | 0.628 | 0.837 | 0.7 |
| study | global_mean | 286 | 105 | 1.09 | 0.498 | 1.98 | 0.07 | 0.43 | 0.696 | 0.626 | 0.878 | 0.899 |
| study | mineral_class_mean | 286 | 105 | 1.06 | 0.456 | 2.1 | 0.058 | 0.446 | 0.696 | 0.608 | 0.883 | 0.899 |
| study | sorbate_class_mean | 286 | 105 | 1.16 | 0.409 | 1.94 | 0.103 | 0.412 | 0.986 | 0.85 | 0.887 | 0.899 |
| study | version_a@conditions | 286 | 105 | 1.18 | 0.59 | 1.9 | 0.0709 | 0.439 | 0.713 | 0.647 | 0.882 | 0.895 |
| study | version_a@properties | 180 | 62 | 1.1 | 0.588 | 2.01 | 0.0893 | 0.407 | 0.978 | 0.817 | 0.885 | 0.878 |
| study | version_b@conditions | 286 | 105 | 1.18 | 0.59 | 1.9 | 0.0671 | 0.442 | 0.713 | 0.657 | 0.881 | 0.895 |
| study | version_b@properties | 180 | 62 | 1.1 | 0.588 | 2.01 | 0.0861 | 0.415 | 0.978 | 0.822 | 0.885 | 0.878 |

Note on curve error: the spec weights each grid point by the inverse of its bootstrap variance. Plateau points have narrow intervals and slopes near zero, so they dominate, and a nearly flat prediction (e.g. a global mean that averages rising and falling edges) can score well while getting the edge direction wrong. Read `median_curve_error` together with `median_curve_error_unweighted`, `shape_correct` and `sign_correct`.

## Paired differences vs baselines (model minus baseline; negative = model better; 95% intervals over held-out papers)

| level | model | baseline | n_common | p50_error_diff | p50_diff_lo | p50_diff_hi | curve_error_diff | curve_diff_lo | curve_diff_hi |
|---|---|---|---|---|---|---|---|---|---|
| mineral | version_a@properties | global_mean | 180 | -0.157 | -0.318 | 0.181 | 0.00643 | 1.71e-05 | 0.0256 |
| mineral | version_a@properties | sorbate_class_mean | 180 | -0.00526 | -0.214 | 0.181 | 6.86e-05 | -0.00239 | 0.00405 |
| mineral | version_a@properties | mineral_class_mean | 180 | -0.195 | -0.343 | 0.0868 | 0.0103 | 0.000133 | 0.0274 |
| pair | version_a@properties | global_mean | 180 | 0.0557 | -0.147 | 0.361 | 0.0134 | 0.00132 | 0.0363 |
| pair | version_a@properties | sorbate_class_mean | 180 | 0.0826 | -0.0876 | 0.267 | 0.0016 | -2.2e-07 | 0.0126 |
| pair | version_a@properties | mineral_class_mean | 180 | 0.113 | -0.128 | 0.452 | 0.0261 | 0.00296 | 0.0638 |
| sorbate | version_a@properties | global_mean | 180 | 0.247 | 0.0608 | 0.4 | 0.0365 | 0.017 | 0.0645 |
| sorbate | version_a@properties | sorbate_class_mean | 180 | 0.0714 | -0.0374 | 0.225 | 0.0118 | 7.37e-05 | 0.0333 |
| sorbate | version_a@properties | mineral_class_mean | 180 | 0.328 | 0.18 | 0.498 | 0.045 | 0.0221 | 0.0725 |
| study | version_a@properties | global_mean | 180 | -0.0301 | -0.192 | 0.205 | 0.00271 | 3.43e-05 | 0.0134 |
| study | version_a@properties | sorbate_class_mean | 180 | 0.0265 | -0.0904 | 0.136 | -0.000259 | -0.00695 | 0.000956 |
| study | version_a@properties | mineral_class_mean | 180 | -0.0288 | -0.186 | 0.307 | 0.0145 | 0.000852 | 0.0485 |
| mineral | version_b@properties | global_mean | 180 | -0.157 | -0.318 | 0.181 | 0.00056 | -0.000945 | 0.0253 |
| mineral | version_b@properties | sorbate_class_mean | 180 | -0.00526 | -0.214 | 0.181 | -5.82e-05 | -0.00366 | 0.000693 |
| mineral | version_b@properties | mineral_class_mean | 180 | -0.195 | -0.343 | 0.0868 | 0.00487 | -2.06e-06 | 0.0295 |
| pair | version_b@properties | global_mean | 180 | 0.0557 | -0.147 | 0.361 | 0.0128 | 0.000385 | 0.0288 |
| pair | version_b@properties | sorbate_class_mean | 180 | 0.0826 | -0.0876 | 0.267 | 0.00137 | -5.95e-05 | 0.0142 |
| pair | version_b@properties | mineral_class_mean | 180 | 0.113 | -0.128 | 0.452 | 0.0219 | 0.00341 | 0.0564 |
| sorbate | version_b@properties | global_mean | 180 | 0.247 | 0.0608 | 0.4 | 0.0326 | 0.0151 | 0.0516 |
| sorbate | version_b@properties | sorbate_class_mean | 180 | 0.0714 | -0.0374 | 0.225 | 0.0135 | 3.06e-05 | 0.0256 |
| sorbate | version_b@properties | mineral_class_mean | 180 | 0.328 | 0.18 | 0.498 | 0.038 | 0.0202 | 0.072 |
| study | version_b@properties | global_mean | 180 | -0.0301 | -0.192 | 0.205 | 0.000893 | -0.000391 | 0.012 |
| study | version_b@properties | sorbate_class_mean | 180 | 0.0265 | -0.0904 | 0.136 | -3.76e-05 | -0.00711 | 0.000962 |
| study | version_b@properties | mineral_class_mean | 180 | -0.0288 | -0.186 | 0.307 | 0.00999 | 0.000431 | 0.0397 |
| mineral | version_a@conditions | global_mean | 286 | 0.0115 | -0.0795 | 0.0572 | -6.24e-05 | -0.00157 | 0.00069 |
| mineral | version_a@conditions | sorbate_class_mean | 286 | 0.0894 | -0.245 | 0.313 | -0.00282 | -0.0167 | 7.14e-07 |
| mineral | version_a@conditions | mineral_class_mean | 286 | -0.0908 | -0.213 | 0.0491 | 0.000155 | -0.000414 | 0.00521 |
| pair | version_a@conditions | global_mean | 286 | 0.0124 | -0.06 | 0.0656 | -0.000137 | -0.00353 | 0.000446 |
| pair | version_a@conditions | sorbate_class_mean | 286 | 0.123 | -0.0383 | 0.289 | -0.00904 | -0.0199 | -0.000218 |
| pair | version_a@conditions | mineral_class_mean | 286 | -0.0132 | -0.0619 | 0.0763 | 2.67e-05 | -0.000747 | 0.00202 |
| sorbate | version_a@conditions | global_mean | 286 | 0.0273 | -0.0737 | 0.0961 | -0.000154 | -0.00241 | 0.000395 |
| sorbate | version_a@conditions | sorbate_class_mean | 286 | -0.0815 | -0.323 | 0.00253 | -0.0124 | -0.0368 | -0.00241 |
| sorbate | version_a@conditions | mineral_class_mean | 286 | 0.0213 | -0.0402 | 0.0972 | 6.83e-05 | -0.000783 | 0.00262 |
| study | version_a@conditions | global_mean | 286 | 0.0141 | -0.0576 | 0.0625 | -0.000146 | -0.0024 | 0.000235 |
| study | version_a@conditions | sorbate_class_mean | 286 | 0.142 | -0.019 | 0.349 | -0.00577 | -0.0178 | -7.74e-05 |
| study | version_a@conditions | mineral_class_mean | 286 | -1.54e-05 | -0.0652 | 0.108 | 8.66e-05 | -0.000565 | 0.00324 |
| mineral | version_b@conditions | global_mean | 286 | 0.0115 | -0.0795 | 0.0572 | -0.000191 | -0.00244 | 0.000342 |
| mineral | version_b@conditions | sorbate_class_mean | 286 | 0.0894 | -0.245 | 0.313 | -0.00365 | -0.0161 | -1.47e-05 |
| mineral | version_b@conditions | mineral_class_mean | 286 | -0.0908 | -0.213 | 0.0491 | 3.61e-05 | -0.00117 | 0.00245 |
| pair | version_b@conditions | global_mean | 286 | 0.0124 | -0.06 | 0.0656 | -0.000326 | -0.00409 | 0.000221 |
| pair | version_b@conditions | sorbate_class_mean | 286 | 0.123 | -0.0383 | 0.289 | -0.0113 | -0.0239 | -0.00033 |
| pair | version_b@conditions | mineral_class_mean | 286 | -0.0132 | -0.0619 | 0.0763 | -3.7e-06 | -0.00114 | 0.00273 |
| sorbate | version_b@conditions | global_mean | 286 | 0.0273 | -0.0737 | 0.0961 | -0.000812 | -0.00552 | -1.05e-05 |
| sorbate | version_b@conditions | sorbate_class_mean | 286 | -0.0815 | -0.323 | 0.00253 | -0.0133 | -0.0401 | -0.00285 |
| sorbate | version_b@conditions | mineral_class_mean | 286 | 0.0213 | -0.0402 | 0.0972 | 1.58e-06 | -0.00167 | 0.00227 |
| study | version_b@conditions | global_mean | 286 | 0.0141 | -0.0576 | 0.0625 | -0.000339 | -0.00365 | 9.68e-05 |
| study | version_b@conditions | sorbate_class_mean | 286 | 0.142 | -0.019 | 0.349 | -0.00817 | -0.0233 | -0.000271 |
| study | version_b@conditions | mineral_class_mean | 286 | -1.54e-05 | -0.0652 | 0.108 | 1.99e-05 | -0.00132 | 0.00252 |

Files: `per_curve_worst_first.csv` (every held-out curve, worst first), `metrics_by_model.csv`, `paired_differences.csv`, `verdicts.csv`, `p50_error_by_model.png`.
