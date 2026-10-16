# E20 Temperature and contact time

**Plain English.** Warmer or longer experiments can shift sorption curves. The dataset has no contact-time column at all, and temperature is reported for few curves, so only a small temperature check is possible: curves from the same paper that differ only in temperature.

> EXPLORATORY. Development papers only. 59 of 641 E1 curves report temperature. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

| outcome | series | papers | n | slope | ci_lo | ci_hi | p |
|---|---|---|---|---|---|---|---|
| native edge (pH per 10 degC) | 1 | 1 | 9 |  |  |  |  |
| solids-normalised edge (pH per 10 degC) | 1 | 1 | 9 |  |  |  |  |
| slope b (log10 K per pH, per 10 degC) | 1 | 1 | 9 |  |  |  |  |

Contact time: not in the file; it is a column of `data/descriptors/study_methods.csv` (E10, human entry).
