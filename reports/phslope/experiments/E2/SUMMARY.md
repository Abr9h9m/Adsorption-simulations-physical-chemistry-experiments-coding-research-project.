# E2 Weighting and point windows for the log10 K lines

**Plain English.** Points where almost nothing or almost everything is stuck are the least reliable, because small measurement errors there become huge errors on the log scale. We tried down-weighting them in different ways and changing which points are used, and checked whether predictions of held-out papers got better. Result: **KEEP W0 (0.03, 0.97)**.

> EXPLORATORY. Development papers only; E1 model unchanged except the step-1 line fits. Locked set hash `88b1c3a1b769`. Commit `c835343`.

## Error model (W1): robust variance of log10 K about the curve's own line, by fraction sorbed

| f_mid | var | n |
|---|---|---|
| 0.015 | 1.01 | 1288 |
| 0.045 | 0.0399 | 973 |
| 0.08 | 0.0265 | 1122 |
| 0.15 | 0.0212 | 1841 |
| 0.275 | 0.0212 | 1796 |
| 0.425 | 0.0209 | 1505 |
| 0.575 | 0.0226 | 1471 |
| 0.725 | 0.0318 | 1617 |
| 0.85 | 0.037 | 1391 |
| 0.92 | 0.068 | 960 |
| 0.955 | 0.109 | 999 |
| 0.985 | 1.07 | 2318 |

## Held-out results on the 662 curves present under every scheme (same evaluation points)

| scheme | n | median_logK_rmse | median_edge_error | coverage | rel_change_vs_W0 | meets_rule |
|---|---|---|---|---|---|---|
| W0 (0.01, 0.99) | 662 | 0.788 | 1.18 | 0.878 | -0.00119 | False |
| W0 (0.03, 0.97) | 662 | 0.788 | 1.14 | 0.856 | 0 | False |
| W0 (0.10, 0.90) | 662 | 0.818 | 1.17 | 0.841 | 0.0372 | False |
| W1 empirical (0.03, 0.97) | 662 | 0.771 | 1.12 | 0.853 | -0.0219 | False |
| W2 logit-delta (0.03, 0.97) | 662 | 0.769 | 1.14 | 0.835 | -0.0248 | False |

## Paired differences in held-out log10 K RMSE vs W0 (95% intervals over units)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W0 (0.01, 0.99) | W0 (0.03, 0.97) | 662 | -0.000941 | -0.048 | 0.0666 | -0.00175 | -0.0173 | 0.00719 | 0.788 | 0.788 | 0.514 | 0 |
| W0 (0.10, 0.90) | W0 (0.03, 0.97) | 662 | 0.0293 | -0.0433 | 0.0833 | 0.0419 | 0.00466 | 0.0631 | 0.818 | 0.788 | 0.417 | 0 |
| W1 empirical (0.03, 0.97) | W0 (0.03, 0.97) | 662 | -0.0173 | -0.0499 | 0.00778 | -0.00941 | -0.0227 | -0.0017 | 0.771 | 0.788 | 0.594 | 0 |
| W2 logit-delta (0.03, 0.97) | W0 (0.03, 0.97) | 662 | -0.0195 | -0.0569 | 0.0196 | -0.00417 | -0.0242 | 0.0102 | 0.769 | 0.788 | 0.523 | 0 |

## Curves and points per window

| scheme | curves_in_main_set | of_rising_falling | points_in_window |
|---|---|---|---|
| W0 (0.03, 0.97) | 757 | 931 | 13771 |
| W0 (0.01, 0.99) | 775 | 931 | 15985 |
| W0 (0.10, 0.90) | 689 | 931 | 9663 |
| W1 empirical (0.03, 0.97) | 773 | 931 | 13771 |
| W2 logit-delta (0.03, 0.97) | 765 | 931 | 13771 |

## Notes

- W3 (censored/Tobit fit of points outside the window) was not implemented in this round.
- The W1 error model is estimated from all development curves' own line residuals (a property of the measurements, not of held-out outcomes).
- Reported detection limits were looked for in E0.1; the file has no detection-limit column.
