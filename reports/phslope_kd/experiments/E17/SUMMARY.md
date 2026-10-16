# E17 (partial) Particle-concentration diagnostics

**Plain English.** For metal cations, adding more mineral increases sorption much less than simple chemistry predicts. One known explanation is fine particles slipping through the separation step. If so, the shortfall should be biggest for strongly sorbing systems and at high mineral amounts. Result: **PREDICTION (i) NOT SUPPORTED**.

> EXPLORATORY. [lit] titles only (read before wording). Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`. Prediction (ii) needs the separation method (E10 table) and was not run.

Within pair: level of log10 K (at the pair reference pH) on centred log10 solids (linear sorption: +1), with interactions; clustered by lineage unit.

| direction | term | estimate | ci_lo | ci_hi | n | pairs | units |
|---|---|---|---|---|---|---|---|
| rising | solids | -0.239 | -0.398 | -0.08 | 294 | 37 | 68 |
| rising | solids_x_strength | -0.0433 | -0.224 | 0.137 | 294 | 37 | 68 |
| rising | solids_sq | 0.195 | 0.0164 | 0.373 | 294 | 37 | 68 |
| falling | solids | -0.0345 | -0.344 | 0.275 | 151 | 10 | 27 |
| falling | solids_x_strength | 0.297 | -0.0962 | 0.691 | 151 | 10 | 27 |
| falling | solids_sq | 0.0818 | -0.117 | 0.281 | 151 | 10 | 27 |

Read: `solids` = slope at average strength (expected +1); `solids_x_strength` negative = (i); `solids_sq` negative = (iii). Falling rows test (iv).

