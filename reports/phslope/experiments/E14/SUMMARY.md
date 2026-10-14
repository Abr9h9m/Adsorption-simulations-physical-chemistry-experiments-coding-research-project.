# E14 Specification curve: which conclusions survive arbitrary analysis choices?

**Plain English.** Every analysis involves choices that have no single right answer (which points to use, how strict the quality filter is, how the edge is defined, whether copies are merged). We redid the headline analyses for all 648 combinations of reasonable choices and counted how often each conclusion still holds. A conclusion that holds in at least 90% of them is called robust.

> EXPLORATORY. Development papers only. 648 of 648 specifications had enough curves. Locked set hash `88b1c3a1b769`. Commit `ed145ae`.

| conclusion | specifications | share_holding | robust (>= 90%) |
|---|---|---|---|
| H1 matching gain (B3 < B0) | 648 | 0.735 | False |
| H2 rising solids slope < 0 (interval below 0) | 648 | 0.508 | False |
| H3 falling solids slope > 0 (interval above 0) | 648 | 0.912 | True |
| H4 loading Kd drop (interval below 0) | 648 | 0.829 | False |
| H5 ionic strength null (interval includes 0) | 648 | 0.968 | True |

Per-specification estimates: `specifications.csv`; figure: `specification_curve.png`.

## Analyst notes

- **Robust (>= 90%)**: the falling-edge solids effect (91%) and the overall ionic-strength null (97%; E8 shows the null averages opposite class-specific effects, so "no overall effect" is robust but "no effect" is not).
- **Fragile**: the conditions-matching gain (73%), the rising-edge solids effect (51%) and the high-loading Kd drop (83%). These should be worded as conditional on analysis choices in any write-up.
- 648 specifications (the earlier "324" in the code docstring miscounted the grid).
