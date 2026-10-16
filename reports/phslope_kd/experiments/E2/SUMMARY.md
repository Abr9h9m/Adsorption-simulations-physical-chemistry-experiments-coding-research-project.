# E2 Weighting and point windows for the log10 K lines

**Plain English.** Points where almost nothing or almost everything is stuck are the least reliable, because small measurement errors there become huge errors on the log scale. We tried down-weighting them in different ways and changing which points are used, and checked whether predictions of held-out papers got better. Result: **KEEP W0 (0.03, 0.97)**.

> EXPLORATORY. Development papers only; E1 model unchanged except the step-1 line fits. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Error model (W1): robust variance of log10 K about the curve's own line, by fraction sorbed

| f_mid | var | n |
|---|---|---|
| 0.015 | 0.665 | 1698 |
| 0.045 | 0.017 | 1001 |
| 0.08 | 0.0147 | 981 |
| 0.15 | 0.0281 | 1284 |
| 0.275 | 0.021 | 1302 |
| 0.425 | 0.0296 | 1181 |
| 0.575 | 0.0295 | 1056 |
| 0.725 | 0.0334 | 1324 |
| 0.85 | 0.0509 | 1274 |
| 0.92 | 0.0815 | 863 |
| 0.955 | 0.0808 | 910 |
| 0.985 | 1.19 | 2739 |

## Held-out results on the 499 curves present under every scheme (same evaluation points)

| scheme | n | median_logK_rmse | median_edge_error | coverage | rel_change_vs_W0 | meets_rule |
|---|---|---|---|---|---|---|
| W0 (0.01, 0.99) | 499 | 0.765 | 0.978 | 0.87 | 0.0524 | False |
| W0 (0.03, 0.97) | 499 | 0.727 | 0.951 | 0.844 | 0 | False |
| W0 (0.10, 0.90) | 499 | 0.765 | 1.05 | 0.864 | 0.0535 | False |
| W1 empirical (0.03, 0.97) | 499 | 0.73 | 0.993 | 0.84 | 0.00484 | False |
| W2 logit-delta (0.03, 0.97) | 499 | 0.729 | 0.922 | 0.822 | 0.00385 | False |

## Paired differences in held-out log10 K RMSE vs W0 (95% intervals over units)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W0 (0.01, 0.99) | W0 (0.03, 0.97) | 499 | 0.0381 | -0.00608 | 0.0631 | 0.0108 | 0.00179 | 0.0308 | 0.765 | 0.727 | 0.435 | 0 |
| W0 (0.10, 0.90) | W0 (0.03, 0.97) | 499 | 0.0389 | -0.0324 | 0.0888 | 0.000633 | -0.021 | 0.033 | 0.765 | 0.727 | 0.497 | 0 |
| W1 empirical (0.03, 0.97) | W0 (0.03, 0.97) | 499 | 0.00352 | -0.0341 | 0.0419 | 0.00321 | -0.00679 | 0.0125 | 0.73 | 0.727 | 0.477 | 0 |
| W2 logit-delta (0.03, 0.97) | W0 (0.03, 0.97) | 499 | 0.0028 | -0.0733 | 0.0665 | 0.00219 | -0.0114 | 0.0131 | 0.729 | 0.727 | 0.491 | 0 |

## Curves and points per window

| scheme | curves_in_main_set | of_rising_falling | points_in_window |
|---|---|---|---|
| W0 (0.03, 0.97) | 641 | 827 | 11358 |
| W0 (0.01, 0.99) | 674 | 827 | 13789 |
| W0 (0.10, 0.90) | 529 | 827 | 7501 |
| W1 empirical (0.03, 0.97) | 646 | 827 | 11358 |
| W2 logit-delta (0.03, 0.97) | 616 | 827 | 11358 |

## Notes

- W3 (censored/Tobit fit of points outside the window) was not implemented in this round.
- The W1 error model is estimated from all development curves' own line residuals (a property of the measurements, not of held-out outcomes).
- Reported detection limits were looked for in E0.1; the file has no detection-limit column.
