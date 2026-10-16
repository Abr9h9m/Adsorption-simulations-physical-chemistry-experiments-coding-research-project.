# E16 Transfer to a new mineral or a new sorbate

**Plain English.** The realistic question is not 'predict another paper on a system we know' but 'predict a mineral or sorbate nobody has measured yet'. We left out one whole mineral (or sorbate) at a time and compared the model with simple class averages. Useful for a new mineral: **no**; for a new sorbate: **no**. No chemical descriptors exist yet (E6, E18 tables are empty), so the model can only use classes and conditions.

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## Edge error

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted | left_out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | 639 | 32 | 1.38 | 1.21 | 1.78 | 0.599 | 2.35 | 2.12 | 0.21 | 0.399 | 0.667 | 1.85 | 0.187 | mineral |
| B4_class_mean | 639 | 32 | 1.41 | 1.25 | 1.7 | 0.633 | 2.43 | 2.09 | 0.189 | 0.366 | 0 | 1.75 | 0.142 | mineral |
| B5_global_mean | 641 | 32 | 1.44 | 1.34 | 1.8 | 0.664 | 2.7 | 2.19 | 0.178 | 0.354 | 0 | 1.69 | 0.137 | mineral |
| E1 | 639 | 36 | 1.57 | 1.12 | 2.32 | 0.629 | 2.95 | 2.45 | 0.208 | 0.352 | 0.603 | 1.84 | 0.178 | sorbate |
| B4_class_mean | 639 | 34 | 1.57 | 1.17 | 2.26 | 0.736 | 2.87 | 2.39 | 0.188 | 0.351 | 0 | 1.77 | 0.149 | sorbate |
| B5_global_mean | 641 | 36 | 1.53 | 1.14 | 2.06 | 0.707 | 2.71 | 2.24 | 0.164 | 0.356 | 0 | 1.91 | 0.152 | sorbate |

## E1 minus baseline (difference of medians; 95% interval over left-out minerals / sorbates)

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | left_out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | B4_class_mean | 637 | -0.0175 | -0.108 | 0.121 | -0.0524 | -0.112 | 0.0626 | 1.38 | 1.39 | 0.545 | 0 | mineral |
| E1 | B5_global_mean | 639 | -0.0597 | -0.281 | 0.302 | -0.192 | -0.414 | 0.221 | 1.38 | 1.44 | 0.523 | 0 | mineral |
| E1 | B4_class_mean | 637 | 0.0107 | -0.102 | 0.329 | -0.0548 | -0.0929 | 0.119 | 1.57 | 1.56 | 0.568 | 0 | sorbate |
| E1 | B5_global_mean | 639 | 0.0487 | -0.399 | 0.902 | 0.0266 | -0.468 | 0.482 | 1.57 | 1.52 | 0.499 | 0 | sorbate |
