# E20 Temperature and contact time

**Plain English.** Warmer or longer experiments can shift sorption curves. The dataset has no contact-time column at all, and temperature is reported for few curves, so only a small temperature check is possible: curves from the same paper that differ only in temperature.

> EXPLORATORY. Development papers only. 68 of 757 E1 curves report temperature. Locked set hash `88b1c3a1b769`. Commit `c80a5b8`.

| outcome | series | papers | n | n_clusters | slope | ci_lo | ci_hi | p |
|---|---|---|---|---|---|---|---|---|
| native edge (pH per 10 degC) | 3 | 3 | 15 | 3 | -0.0795 | -0.17 | 0.011 | 0.0853 |
| solids-normalised edge (pH per 10 degC) | 3 | 3 | 15 | 3 | -0.134 | -0.204 | -0.0645 | 0.000158 |
| slope b (log10 K per pH, per 10 degC) | 3 | 3 | 15 | 3 | 0.00899 | -0.0411 | 0.0591 | 0.725 |

Contact time: not in the file; it is a column of `data/descriptors/study_methods.csv` (E10, human entry).

## Analyst note

Only 3 within-paper temperature series (3 papers, 15 curves). Paper-clustered intervals with 3 clusters are unreliable, so these numbers are anecdotal, not evidence for or against a temperature effect.
