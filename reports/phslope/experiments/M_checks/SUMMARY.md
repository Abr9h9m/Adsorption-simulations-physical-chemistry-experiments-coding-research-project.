# M7, M8, M9 checks

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `deab33c`.

## M7: the conditions-matched subset, with its uncertainty

Curves with a conditions-matched paper: 38, from 18 papers in 18 lineage units (development papers; the follow-up's 79 curves included locked papers and counted copies as separate papers).

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3 matched | 38 | 18 | 0.324 | 0.225 | 0.732 | 0.151 | 0.862 | 0.867 | 0.605 | 0.789 |  | 0.272 | 0.611 |
| B0 plain average | 38 | 18 | 0.832 | 0.391 | 1.17 | 0.29 | 1.23 | 0.959 | 0.368 | 0.632 |  | 0.779 | 0.38 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3 matched | B0 plain average | 38 | -0.507 | -0.873 | 0.0229 | 0 | -0.325 | 0.0601 | 0.324 | 0.832 | 0.395 | 0.289 |

## M8: the same figure digitized twice (every point matches, same number of points, different papers)

2 curve pairs.

| curve_a | curve_b | mineral | sorbate | reference_a | reference_b | match_share | cross_paper |
|---|---|---|---|---|---|---|---|
| sblvd14_f2b | bs14_f4b | goethite | Ra(+2) | sblvd14 | bs14 | 1 | True |
| d01_f5-6f | kckd96_f2b | quartz | U(+6) | d01 | kckd96 | 1 | True |

## M9: truncation error by edge steepness (E5 truncations)

| steepness | window | n | median_error | within_0_5 |
|---|---|---|---|---|
| shallow (|b| < 0.54) | 2 | 156 | 0.289 | 0.705 |
| shallow (|b| < 0.54) | 3 | 183 | 0.218 | 0.727 |
| shallow (|b| < 0.54) | 4 | 202 | 0.186 | 0.787 |
| shallow (|b| < 0.54) | 5 | 213 | 0.139 | 0.85 |
| steep (|b| >= 0.54) | 2 | 125 | 0.173 | 0.896 |
| steep (|b| >= 0.54) | 3 | 172 | 0.0894 | 0.924 |
| steep (|b| >= 0.54) | 4 | 180 | 0.0738 | 0.961 |
| steep (|b| >= 0.54) | 5 | 215 | 0.0383 | 0.986 |

