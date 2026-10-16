# F Integration on development papers (locked set NOT opened)

**Plain English.** We combined the core model from E1 with every correction that passed its own test, then removed each correction in turn to see whether it still helps. This is all on the development papers; the 24 locked papers have not been looked at.

> EXPLORATORY. Locked set hash `88b1c3a1b769` (not opened). Commit `d468a46`.

Accepted adjustments included: E8 ionic strength x sorbate type, E1 within-between solids (E23).

## Held-out edge error, pairs with >= 2 units

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| final model | 459 | 99 | 0.765 | 0.582 | 0.931 | 0.32 | 1.63 | 1.48 | 0.375 | 0.597 | 0.847 | 0.798 | 0.367 |
| E1 core only | 459 | 99 | 0.751 | 0.535 | 0.902 | 0.3 | 1.51 | 1.52 | 0.39 | 0.608 | 0.882 | 0.849 | 0.354 |
| final without E8 ionic strength x sorbate type | 459 | 99 | 0.764 | 0.556 | 0.931 | 0.341 | 1.63 | 1.48 | 0.377 | 0.593 | 0.858 | 0.811 | 0.374 |
| final without E1 within-between solids (E23) | 459 | 99 | 0.752 | 0.557 | 0.963 | 0.29 | 1.51 | 1.51 | 0.394 | 0.61 | 0.871 | 0.866 | 0.359 |
| B0_all_other | 459 | 99 | 0.816 | 0.667 | 1.02 | 0.28 | 1.57 | 1.58 | 0.353 | 0.582 | 0 | 0.941 | 0.314 |
| B1_nearest1 | 459 | 99 | 0.724 | 0.565 | 0.932 | 0.306 | 1.58 | 1.67 | 0.386 | 0.595 | 0 | 0.819 | 0.388 |
| B2_nearest3 | 459 | 99 | 0.731 | 0.576 | 0.923 | 0.336 | 1.5 | 1.56 | 0.397 | 0.612 | 0 | 0.852 | 0.368 |
| B3_matched_fb | 459 | 99 | 0.828 | 0.682 | 0.984 | 0.341 | 1.58 | 1.61 | 0.32 | 0.586 | 0 | 0.94 | 0.3 |
| B4_class_mean | 459 | 99 | 1.22 | 1.03 | 1.55 | 0.577 | 2.12 | 1.96 | 0.196 | 0.412 | 0 | 1.3 | 0.205 |
| B5_global_mean | 459 | 99 | 1.35 | 1.1 | 1.64 | 0.593 | 2.39 | 2.07 | 0.19 | 0.381 | 0 | 1.37 | 0.18 |

## Final model minus each alternative (difference of medians; negative = final better)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| final model | E1 core only | 459 | 0.014 | -0.0978 | 0.139 | 0.0024 | -0.0505 | 0.0665 | 0.765 | 0.751 | 0.497 | 0 |
| final model | final without E8 ionic strength x sorbate type | 459 | 0.00069 | -0.0306 | 0.0422 | 0.000932 | -0.00452 | 0.00725 | 0.765 | 0.764 | 0.484 | 0 |
| final model | final without E1 within-between solids (E23) | 459 | 0.0135 | -0.0745 | 0.116 | 0.0151 | -0.0296 | 0.0462 | 0.765 | 0.752 | 0.479 | 0 |
| final model | B0_all_other | 459 | -0.0508 | -0.207 | 0.0823 | 0.00177 | -0.12 | 0.0917 | 0.765 | 0.816 | 0.495 | 0 |
| final model | B1_nearest1 | 459 | 0.0414 | -0.209 | 0.207 | -0.0178 | -0.122 | 0.0744 | 0.765 | 0.724 | 0.516 | 0 |
| final model | B2_nearest3 | 459 | 0.0338 | -0.1 | 0.147 | -0.000144 | -0.0922 | 0.108 | 0.765 | 0.731 | 0.503 | 0 |
| final model | B3_matched_fb | 459 | -0.0626 | -0.241 | 0.0722 | -0.0349 | -0.136 | 0.0877 | 0.765 | 0.828 | 0.523 | 0 |
| final model | B4_class_mean | 459 | -0.458 | -0.756 | -0.234 | -0.382 | -0.683 | -0.225 | 0.765 | 1.22 | 0.664 | 0 |
| final model | B5_global_mean | 459 | -0.586 | -0.899 | -0.289 | -0.514 | -0.679 | -0.296 | 0.765 | 1.35 | 0.66 | 0 |

An adjustment whose removal does not make the model worse (interval including zero or positive) is a candidate for removal before the locked-set evaluation (protocol F2).

## Locked-set evaluation

Not run. It is run once, after E6, E10 and the full E7 (which wait for human-entered data and constants), with `python -m phslope.experiments.integrate --open-locked-set "I understand this is the single final look"`.
