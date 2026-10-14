# E17 (partial) Particle-concentration diagnostics

**Plain English.** For metal cations, adding more mineral increases sorption much less than simple chemistry predicts. One known explanation is fine particles slipping through the separation step. If so, the shortfall should be biggest for strongly sorbing systems and at high mineral amounts. Result: **PREDICTION (i) NOT SUPPORTED**.

> EXPLORATORY. [lit] titles only (read before wording). Development papers only. Locked set hash `88b1c3a1b769`. Commit `c7b22e2-dirty`. Prediction (ii) needs the separation method (E10 table) and was not run.

Within pair: level of log10 K (at the pair reference pH) on centred log10 solids (linear sorption: +1), with interactions; clustered by lineage unit.

| direction | term | estimate | ci_lo | ci_hi | n | pairs | units |
|---|---|---|---|---|---|---|---|
| rising | solids | 0.327 | 0.123 | 0.53 | 374 | 46 | 71 |
| rising | solids_x_strength | 0.193 | -0.0255 | 0.411 | 374 | 46 | 71 |
| rising | solids_sq | -0.071 | -0.291 | 0.149 | 374 | 46 | 71 |
| falling | solids | 0.946 | 0.525 | 1.37 | 172 | 11 | 33 |
| falling | solids_x_strength | -0.0589 | -0.43 | 0.312 | 172 | 11 | 33 |
| falling | solids_sq | 0.103 | -0.188 | 0.395 | 172 | 11 | 33 |

Read: `solids` = slope at average strength (expected +1); `solids_x_strength` negative = (i); `solids_sq` negative = (iii). Falling rows test (iv).

