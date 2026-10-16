# E14 Specification curve: which conclusions survive arbitrary analysis choices?

**Plain English.** Every analysis involves choices that have no single right answer (which points to use, how strict the quality filter is, how the edge is defined, whether copies are merged). We redid the headline analyses for all 648 combinations of reasonable choices and counted how often each conclusion still holds. A conclusion that holds in at least 90% of them is called robust.

> EXPLORATORY. Development papers only. 648 of 648 specifications had enough curves. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

| conclusion | specifications | share_holding | robust (>= 90%) |
|---|---|---|---|
| H1 matching gain (B3 < B0) | 648 | 0.725 | False |
| H2 rising solids slope < 0 (interval below 0) | 648 | 0 | False |
| H3 falling solids slope > 0 (interval above 0) | 648 | 0 | False |
| H4 loading Kd drop (interval below 0) | 648 | 0.894 | False |
| H5 ionic strength null (interval includes 0) | 648 | 0.975 | True |

Per-specification estimates: `specifications.csv`; figure: `specification_curve.png`.
