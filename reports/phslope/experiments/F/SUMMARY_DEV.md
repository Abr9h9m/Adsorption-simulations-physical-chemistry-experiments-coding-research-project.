# F Integration on development papers (locked set NOT opened)

**Plain English.** We combined the core model from E1 with every correction that passed its own test, then removed each correction in turn to see whether it still helps. This is all on the development papers; the 24 locked papers have not been looked at.

> EXPLORATORY. Locked set hash `88b1c3a1b769` (not opened). Commit `4f24f3c`.

Accepted adjustments included: E8 ionic strength x sorbate type, E1 within-between solids (E23).

## Held-out edge error, pairs with >= 2 units

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| final model | 535 | 107 | 0.801 | 0.613 | 0.979 | 0.345 | 1.5 | 1.48 | 0.361 | 0.598 | 0.877 | 0.952 | 0.28 |
| E1 core only | 535 | 107 | 0.882 | 0.673 | 1.12 | 0.368 | 1.61 | 1.49 | 0.336 | 0.548 | 0.899 | 1.07 | 0.284 |
| final without E8 ionic strength x sorbate type | 535 | 107 | 0.802 | 0.621 | 0.989 | 0.349 | 1.49 | 1.48 | 0.353 | 0.602 | 0.877 | 0.954 | 0.283 |
| final without E1 within-between solids (E23) | 535 | 107 | 0.878 | 0.661 | 1.15 | 0.368 | 1.59 | 1.49 | 0.335 | 0.55 | 0.897 | 1.02 | 0.271 |
| B0_all_other | 535 | 107 | 0.988 | 0.82 | 1.26 | 0.421 | 1.79 | 1.63 | 0.271 | 0.505 | 0 | 1.1 | 0.234 |
| B1_nearest1 | 535 | 107 | 0.973 | 0.755 | 1.26 | 0.407 | 1.82 | 1.7 | 0.318 | 0.521 | 0 | 1.15 | 0.274 |
| B2_nearest3 | 535 | 107 | 0.867 | 0.742 | 1.11 | 0.354 | 1.78 | 1.64 | 0.351 | 0.55 | 0 | 1.12 | 0.293 |
| B3_matched_fb | 535 | 107 | 0.962 | 0.791 | 1.21 | 0.364 | 1.79 | 1.61 | 0.303 | 0.52 | 0 | 1.14 | 0.245 |
| B4_class_mean | 535 | 107 | 1.14 | 0.973 | 1.36 | 0.53 | 2.05 | 1.93 | 0.245 | 0.437 | 0 | 1.26 | 0.231 |
| B5_global_mean | 535 | 107 | 1.34 | 0.948 | 1.58 | 0.606 | 2.17 | 1.99 | 0.207 | 0.413 | 0 | 1.43 | 0.2 |

## Final model minus each alternative (difference of medians; negative = final better)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| final model | E1 core only | 535 | -0.0812 | -0.284 | 0.1 | -0.0366 | -0.123 | 0.0251 | 0.801 | 0.882 | 0.564 | 0 |
| final model | final without E8 ionic strength x sorbate type | 535 | -0.000777 | -0.041 | 0.0466 | -0.000466 | -0.00894 | 0.00638 | 0.801 | 0.802 | 0.512 | 0 |
| final model | final without E1 within-between solids (E23) | 535 | -0.0767 | -0.271 | 0.112 | -0.0354 | -0.125 | 0.0348 | 0.801 | 0.878 | 0.538 | 0 |
| final model | B0_all_other | 535 | -0.187 | -0.412 | -0.00515 | -0.126 | -0.265 | -0.00884 | 0.801 | 0.988 | 0.591 | 0 |
| final model | B1_nearest1 | 535 | -0.172 | -0.455 | 0.0936 | -0.147 | -0.299 | -0.0597 | 0.801 | 0.973 | 0.607 | 0 |
| final model | B2_nearest3 | 535 | -0.0657 | -0.267 | 0.0968 | -0.105 | -0.215 | -0.0147 | 0.801 | 0.867 | 0.579 | 0 |
| final model | B3_matched_fb | 535 | -0.161 | -0.366 | 0.00677 | -0.116 | -0.272 | -0.0208 | 0.801 | 0.962 | 0.576 | 0 |
| final model | B4_class_mean | 535 | -0.34 | -0.589 | -0.137 | -0.333 | -0.548 | -0.0151 | 0.801 | 1.14 | 0.596 | 0 |
| final model | B5_global_mean | 535 | -0.538 | -0.881 | -0.0941 | -0.408 | -0.722 | -0.105 | 0.801 | 1.34 | 0.645 | 0 |

An adjustment whose removal does not make the model worse (interval including zero or positive) is a candidate for removal before the locked-set evaluation (protocol F2).

## Locked-set evaluation

Not run. It is run once, after E6, E10 and the full E7 (which wait for human-entered data and constants), with `python -m phslope.experiments.integrate --open-locked-set "I understand this is the single final look"`.
