# M7, M8, M9 checks

> EXPLORATORY. Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## M7: the conditions-matched subset, with its uncertainty

Curves with a conditions-matched paper: 44, from 24 papers in 24 lineage units (development papers; the follow-up's 79 curves included locked papers and counted copies as separate papers).

| model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage | median_paper_weighted | within_0_5_paper_weighted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3 matched | 44 | 24 | 0.443 | 0.269 | 0.716 | 0.244 | 0.85 | 0.825 | 0.568 | 0.773 |  | 0.463 | 0.519 |
| B0 plain average | 44 | 24 | 0.543 | 0.315 | 0.82 | 0.261 | 1.1 | 0.894 | 0.5 | 0.727 |  | 0.711 | 0.429 |

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3 matched | B0 plain average | 44 | -0.1 | -0.481 | 0.121 | -0.0186 | -0.236 | 0.00849 | 0.443 | 0.543 | 0.523 | 0.114 |

## M8: the same figure digitized twice (every point matches, same number of points, different papers)

2 curve pairs.

| curve_a | curve_b | mineral | sorbate | reference_a | reference_b | match_share | cross_paper |
|---|---|---|---|---|---|---|---|
| zb04_fb4 | zrhsk05_f11b | calcite | Pu(+5) | zb04 | zrhsk05 | 1 | True |
| d01_f5-6f | kckd96_f2b | quartz | U(+6) | d01 | kckd96 | 1 | True |

## M9: truncation error by edge steepness (E5 truncations)

| steepness | window | n | median_error | within_0_5 |
|---|---|---|---|---|
| shallow (|b| < 0.58) | 2 | 129 | 0.332 | 0.713 |
| shallow (|b| < 0.58) | 3 | 154 | 0.253 | 0.76 |
| shallow (|b| < 0.58) | 4 | 171 | 0.205 | 0.842 |
| shallow (|b| < 0.58) | 5 | 173 | 0.122 | 0.902 |
| steep (|b| >= 0.58) | 2 | 74 | 0.132 | 0.878 |
| steep (|b| >= 0.58) | 3 | 102 | 0.106 | 0.922 |
| steep (|b| >= 0.58) | 4 | 121 | 0.0665 | 0.917 |
| steep (|b| >= 0.58) | 5 | 152 | 0.0965 | 0.967 |

