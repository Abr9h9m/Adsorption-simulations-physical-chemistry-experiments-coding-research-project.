# E4 Lab (research-group) effect

**Plain English.** Papers from the same research group often reuse the same recipe, so their curves may agree for reasons that do not carry over to other labs. We asked whether the benefit of matching experimental conditions survives when the matched paper must come from a different group. Result (exact-initials grouping): **GAIN DOES NOT SURVIVE (partly a lab effect, or not significant)**.

> EXPLORATORY. The file has no author fields, so labs are a proxy built from the reference code (letters = author initials). 180 exact-initial groups, 141 first-two-letter groups. The exact proxy under-counts same-lab pairs (a lab with changing co-authors is split); the coarse proxy over-counts (unrelated authors with the same initials are merged). Development papers only; leave-out unit = lineage cluster. Locked set hash `88b1c3a1b769`. Commit `4f79b50`.

## 2. Matched-gain survival (core single-edge curves, logistic edge)

| lab_id | matching | model | n | median | median_lo | median_hi | within_0_5 |
|---|---|---|---|---|---|---|---|
| lab_exact | any lab | B0_all_other | 218 | 0.642 | 0.392 | 0.913 | 0.44 |
| lab_exact | any lab | B1_nearest1 | 218 | 0.491 | 0.392 | 0.857 | 0.514 |
| lab_exact | any lab | B2_nearest3 | 218 | 0.609 | 0.361 | 0.884 | 0.463 |
| lab_exact | any lab | B3_matched_fb | 218 | 0.535 | 0.312 | 0.871 | 0.482 |
| lab_exact | different lab (lab_exact) | B0_all_other | 214 | 0.658 | 0.391 | 0.914 | 0.43 |
| lab_exact | different lab (lab_exact) | B1_nearest1 | 214 | 0.498 | 0.389 | 0.872 | 0.505 |
| lab_exact | different lab (lab_exact) | B2_nearest3 | 214 | 0.642 | 0.361 | 0.897 | 0.453 |
| lab_exact | different lab (lab_exact) | B3_matched_fb | 214 | 0.566 | 0.297 | 0.872 | 0.472 |
| lab_coarse | any lab | B0_all_other | 218 | 0.642 | 0.392 | 0.913 | 0.44 |
| lab_coarse | any lab | B1_nearest1 | 218 | 0.491 | 0.392 | 0.857 | 0.514 |
| lab_coarse | any lab | B2_nearest3 | 218 | 0.609 | 0.361 | 0.884 | 0.463 |
| lab_coarse | any lab | B3_matched_fb | 218 | 0.535 | 0.312 | 0.871 | 0.482 |
| lab_coarse | different lab (lab_coarse) | B0_all_other | 209 | 0.711 | 0.392 | 0.967 | 0.416 |
| lab_coarse | different lab (lab_coarse) | B1_nearest1 | 209 | 0.512 | 0.392 | 0.878 | 0.493 |
| lab_coarse | different lab (lab_coarse) | B2_nearest3 | 209 | 0.694 | 0.338 | 0.941 | 0.431 |
| lab_coarse | different lab (lab_coarse) | B3_matched_fb | 209 | 0.642 | 0.387 | 0.884 | 0.44 |

Paired B3 minus B0 (negative = matching helps):

| model | baseline | n_common | median_diff | diff_lo | diff_hi | median_of_diffs | mod_lo | mod_hi | model_median | baseline_median | share_model_better | share_tied | matching | lab_id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3_matched_fb | B0_all_other | 218 | -0.107 | -0.26 | 0.00501 | 0 | 0 | 0 | 0.535 | 0.642 | 0.0688 | 0.876 | any lab | lab_exact |
| B3_matched_fb | B0_all_other | 214 | -0.092 | -0.267 | 0.000897 | 0 | 0 | 0 | 0.566 | 0.658 | 0.0701 | 0.874 | different lab (lab_exact) | lab_exact |
| B3_matched_fb | B0_all_other | 218 | -0.107 | -0.26 | 0.00501 | 0 | 0 | 0 | 0.535 | 0.642 | 0.0688 | 0.876 | any lab | lab_coarse |
| B3_matched_fb | B0_all_other | 209 | -0.0684 | -0.203 | 0.045 | 0 | 0 | 0 | 0.642 | 0.711 | 0.0526 | 0.89 | different lab (lab_coarse) | lab_coarse |

Decision (exact proxy): paired 95% interval below zero: NO; B3 median 0.566 <= 0.5: NO -> **GAIN DOES NOT SURVIVE (partly a lab effect, or not significant)**.

## 1. Lab random effect in the E1 level model (variance shares)

| model | share_class_dir | share_pair_dir | share_unit | share_residual | share_lab | lab_id |
|---|---|---|---|---|---|---|
| without lab | 3.03e-09 | 0.165 | 0.368 | 0.467 |  | lab_exact |
| with lab | 5.24e-08 | 0.167 | 0.301 | 0.451 | 0.0804 | lab_exact |
| without lab | 3.03e-09 | 0.165 | 0.368 | 0.467 |  | lab_coarse |
| with lab | 1.2e-07 | 0.166 | 0.334 | 0.455 | 0.045 | lab_coarse |

## 3. Same-lab vs different-lab cross-paper pairs (edge difference after solids adjustment)

| lab_id | same_lab_pairs | different_lab_pairs | median_same | median_different | mannwhitney_p |
|---|---|---|---|---|---|
| lab_exact | 2 | 669 | 0.253 | 0.455 |  |
| lab_coarse | 28 | 643 | 1.75 | 0.445 | 0.00015 |


## Analyst notes

- This is the second E4 run. The first used the median of per-curve differences, which is 0 when most curves tie (B3 falls back to B0 for 87% of curves); the paired statistic is now the difference of medians (experiments.yaml, REGISTRY.md).
- **The conditions-matching gain is weak on development papers even before any lab exclusion**: B3 minus B0 = -0.107 pH, 95% interval [-0.26, +0.005], once copies are grouped into lineage clusters (E3). Requiring a different lab changes it little (-0.092 [-0.27, +0.001]). So the "does not survive" verdict reflects a gain that is small and borderline overall, not mainly a lab effect.
- The lab random effect takes 8% of the level variance (exact proxy) and the paper share falls from 37% to 30%: some paper-to-paper variation is shared within a lab.
- Test 3 is not informative with the exact proxy (2 same-lab pairs); the coarse proxy's 28 same-lab pairs differ MORE than different-lab pairs, which suggests the coarse proxy merges unrelated authors.
