# E16 Transfer to a new mineral or a new sorbate

**Plain English.** The realistic question is not 'predict another paper on a system we know' but 'predict a mineral or sorbate nobody has measured yet'. We left out one whole mineral (or sorbate) at a time and compared the model with simple class averages. Useful for a new mineral: **no**; for a new sorbate: **no**. No chemical descriptors exist yet (E6, E18 tables are empty), so the model can only use classes and conditions.

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `59dda0c`.

## Edge error

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted | left_out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 757 | 32 | 1.5 | 1.24 | 1.74 | 0.664 | 2.45 | 2.17 | 0.188 | 0.365 | 0.734 | 1.66 | 0.166 | mineral |
| B4_class_mean | 753 | 32 | 1.39 | 1.21 | 1.61 | 0.642 | 2.29 | 2.04 | 0.205 | 0.384 | 0 | 1.74 | 0.152 | mineral |
| B5_global_mean | 757 | 32 | 1.49 | 1.32 | 1.81 | 0.671 | 2.52 | 2.09 | 0.184 | 0.374 | 0 | 2.01 | 0.0922 | mineral |
| E1 | 757 | 40 | 1.8 | 1.24 | 2.46 | 0.857 | 2.88 | 2.43 | 0.148 | 0.312 | 0.701 | 1.88 | 0.155 | sorbate |
| B4_class_mean | 753 | 39 | 1.67 | 1.14 | 2.07 | 0.755 | 2.61 | 2.29 | 0.167 | 0.332 | 0 | 1.59 | 0.145 | sorbate |
| B5_global_mean | 757 | 40 | 1.62 | 0.982 | 1.89 | 0.717 | 2.55 | 2.14 | 0.17 | 0.366 | 0 | 1.78 | 0.136 | sorbate |

## E1 minus baseline (difference of medians; 95% interval over left-out minerals / sorbates)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | left_out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B4_class_mean | 753 | 0.109 | -0.0463 | 0.224 | 0.0856 | 0.0234 | 0.147 | 1.5 | 1.39 | 0.41 | 0 | mineral |
| E1 | B5_global_mean | 757 | 0.0135 | -0.321 | 0.256 | -0.0777 | -0.245 | 0.193 | 1.5 | 1.49 | 0.531 | 0 | mineral |
| E1 | B4_class_mean | 753 | 0.133 | -0.0614 | 0.397 | 0.108 | 0.0377 | 0.196 | 1.8 | 1.67 | 0.394 | 0 | sorbate |
| E1 | B5_global_mean | 757 | 0.187 | -0.183 | 0.788 | 0.101 | -0.0617 | 0.516 | 1.8 | 1.62 | 0.439 | 0 | sorbate |
