# E22 Where to measure next

**Plain English.** For each mineral-contaminant pair, how much would ONE more independent paper (with 3 curves) shrink the uncertainty of predictions? Pairs measured by a single paper and unmeasured pairs in the well-studied block gain most. This ranking is for planning experiments and for the web interface's coverage map.

> EXPLORATORY. Final development model; level of log10 K at the pair reference pH. Paper-to-paper SD 0.38, residual SD 0.47, pair SD 0.18 (log10 K units). Locked set hash `88b1c3a1b769`.

The paper-to-paper term cannot be reduced by more papers on the same pair, so even a large reduction of the pair term changes the predictive SD only modestly.

## Top 25

| pair_direction | units_now | pred_sd_now | pred_sd_after_one_paper | variance_reduction | rank |
|---|---|---|---|---|---|
| birnessite | Citric acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 1 |
| quartz | Citric acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 2 |
| kaolinite | Oxalic acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 3 |
| kaolinite | Zn(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 4 |
| kaolinite | Sr(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 5 |
| quartz | Ni(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 6 |
| quartz | Se(+6) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 7 |
| quartz | Oxalic acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 8 |
| alumina | Se(+4) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 9 |
| kaolinite | Se(+6) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 10 |
| alumina | Ni(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 11 |
| alumina | Se(+6) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 12 |
| alumina | Ra(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 13 |
| alumina | Zn(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 14 |
| alumina | Citric acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 15 |
| magnetite | Oxalic acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 16 |
| kaolinite | Am(+3) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 17 |
| kaolinite | Ni(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 18 |
| magnetite | Zn(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 19 |
| hematite | Sr(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 20 |
| montmorillonite | Se(+4) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 21 |
| montmorillonite | Se(+6) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 22 |
| montmorillonite | Oxalic acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 23 |
| montmorillonite | Sr(+2) (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 24 |
| hematite | Oxalic acid (unmeasured) | 0 | 0.631 | 0.628 | 0.00428 | 25 |

Full ranking: `measure_next_ranking.csv`.

## Analyst note

The ranking is nearly flat: one more paper on a pair lowers the predictive SD for a NEW paper by less than 1% (0.631 -> 0.628 for unmeasured pairs), because paper-to-paper variation dominates the pair term in the final model. More papers on the same system mostly help estimate that system's average, not what the next paper will measure; better prediction needs explanations for why papers differ (E10 methods, E9 materials, E3 copies). Unmeasured pairs in the dense block tie at the top; among measured pairs, single-paper pairs gain most. For the web coverage map, the per-pair `pred_sd_now` is the useful field.
