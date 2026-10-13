# E3 Duplicate and validity audit

**Plain English.** We looked for the same experiment appearing twice in the dataset (for example a figure re-used in a later paper), because copies make different papers look like they agree. We found 28 curve pairs that are near-copies across different papers and 46 within the same paper. Papers linked by copies are now treated as one source when testing predictions (8 such groups covering 17 papers). We also flagged curves that break simple validity rules; nothing was deleted.

> EXPLORATORY. Development papers only (locked set hash `88b1c3a1b769`). Commit `2419b6b`.

## Duplicates

Rule: points match within 0.02 pH and 0.01 fraction sorbed; a pair is flagged when at least 80% of the shorter curve's points match. Flagged pairs: 74 (28 across papers). Table: `duplicate_pairs.csv`.

| curve_a | curve_b | mineral | sorbate | reference_a | reference_b | match_share | cross_paper |
|---|---|---|---|---|---|---|---|
| zb04_fb4 | zrhsk05_f11b | calcite | Pu(+5) | zb04 | zrhsk05 | 0.9 | True |
| d01_f4-5b | wdpwx94_f5c | ferrihydrite | U(+6) | d01 | wdpwx94 | 0.889 | True |
| d01_f4-5d | wdpwx94_f5a | ferrihydrite | U(+6) | d01 | wdpwx94 | 0.8 | True |
| awj06a_f2b | afi02_f1c | goethite | Mellitic acid | awj06a | afi02 | 0.914 | True |
| mf92_f1a | mf92a_f1c | goethite | Oxalic acid | mf92 | mf92a | 0.882 | True |
| mf92_f1a | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.938 | True |
| mf92_f2aa | mf92a_f4a | goethite | Oxalic acid | mf92 | mf92a | 0.8 | True |
| mf92_f2ab | mf92a_f1c | goethite | Oxalic acid | mf92 | mf92a | 0.944 | True |
| mf92_f2ab | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 1 | True |
| mf92_f2ac | mf92a_f2a | goethite | Oxalic acid | mf92 | mf92a | 0.889 | True |
| mf92_f2ad | mf92a_f2b | goethite | Oxalic acid | mf92 | mf92a | 0.923 | True |
| mf92_f2ad | mf92a_f3a | goethite | Oxalic acid | mf92 | mf92a | 0.923 | True |
| mf92_f2ad | mf92a_f3b | goethite | Oxalic acid | mf92 | mf92a | 0.923 | True |
| mf92_f2bb | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.938 | True |
| mf92_f2ca | mf92a_f4b | goethite | Oxalic acid | mf92 | mf92a | 0.938 | True |
| sblvd14_f2a | bs14_f4a | goethite | Ra(+2) | sblvd14 | bs14 | 1 | True |
| sblvd14_f2b | bs14_f4b | goethite | Ra(+2) | sblvd14 | bs14 | 1 | True |
| sblvd14_f2c | bs14_f4c | goethite | Ra(+2) | sblvd14 | bs14 | 1 | True |
| sblvd14_f2d | bs14_f4d | goethite | Ra(+2) | sblvd14 | bs14 | 0.8 | True |
| hpl88_f2aa | hrbhl87_f2a | goethite | Se(+4) | hpl88 | hrbhl87 | 0.857 | True |
| hpl88_f3ac | hrbhl87_f2e | goethite | Se(+6) | hpl88 | hrbhl87 | 0.833 | True |
| pbb99_f7a | pbb99a_f23apsi | illite | Cs(+1) | pbb99 | pbb99a | 0.828 | True |
| pbb99_f7a | pbb99a_f23aapsi | illite | Cs(+1) | pbb99 | pbb99a | 1 | True |
| pbb99_f7c | pbb99a_f23bpsi | illite | Cs(+1) | pbb99 | pbb99a | 1 | True |
| bb06_f1aapsi | BB06_f1a | montmorillonite | Am(+3) | bb06 | BB06 | 0.828 | True |

## Lineage clusters

196 clusters from 205 papers; 17 papers sit in 8 multi-paper clusters. Table: `lineage_clusters.csv`.

## Agreement benchmark: leaving out papers vs leaving out lineage clusters

Core single-edge development curves in groups with >= 2 units (edge = logistic p50). If duplicates inflated cross-paper agreement, errors rise when copies can no longer be used to predict each other.

| leave_out_unit | model | n | n_units | median | median_lo | median_hi | q25 | q75 | rmse | within_0_5 | within_1 | coverage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reference | B0_all_other | 220 | 69 | 0.58 |  |  | 0.238 | 1.26 | 1.23 | 0.455 | 0.673 |  |
| reference | B1_nearest1 | 220 | 69 | 0.421 |  |  | 0.132 | 1.14 | 1.22 | 0.586 | 0.709 |  |
| reference | B2_nearest3 | 220 | 69 | 0.476 |  |  | 0.182 | 1.07 | 1.13 | 0.527 | 0.732 |  |
| reference | B3_matched_fb | 220 | 69 | 0.503 |  |  | 0.204 | 1.1 | 1.19 | 0.5 | 0.714 |  |
| lineage_cluster | B0_all_other | 218 | 65 | 0.642 |  |  | 0.244 | 1.24 | 1.27 | 0.44 | 0.67 |  |
| lineage_cluster | B1_nearest1 | 218 | 65 | 0.491 |  |  | 0.194 | 1.32 | 1.33 | 0.514 | 0.665 |  |
| lineage_cluster | B2_nearest3 | 218 | 65 | 0.609 |  |  | 0.206 | 1.15 | 1.24 | 0.463 | 0.693 |  |
| lineage_cluster | B3_matched_fb | 218 | 65 | 0.535 |  |  | 0.228 | 1.19 | 1.26 | 0.482 | 0.697 |  |

## Validity flags (counts of curves; nothing dropped)

| index | curves_flagged |
|---|---|
| f_out_of_range | 1 |
| response_maybe_percent | 0 |
| pH_out_of_range | 3 |
| solids_nonpositive_or_implausible | 1 |
| total_sorbate_nonpositive | 0 |
| ionic_strength_not_finite | 0 |
| slope_sign_contradicts_shape | 1 |
| fewer_than_3_pH_values | 0 |

Per-curve flags: `data_flags.csv` (column `data_flag`).

## Outlier review

Pages and the review table are added after E1 (they need the E1 residuals): `outlier_pages.pdf`, `outlier_review.csv` with empty `reviewer`, `verdict`, `notes` columns for Samuel or Abraham. Sensitivity runs excluding verdict = data error wait for those verdicts.
