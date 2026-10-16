# E12 Loading and heterogeneous sites

**Plain English.** If a mineral surface has a few strong binding sites and many weak ones, adding more contaminant fills the strong sites first, so each extra unit binds less well. We checked within papers that varied only the amount of contaminant. Result: **HETEROGENEITY SUPPORTED**.

> EXPLORATORY. **[lit]** Balistrieri & Chao 1987; Dzombak & Morel 1986 (abstracts read). Development papers only. Locked set hash `88b1c3a1b769`. Commit `d468a46`.

## 1. Within-paper concentration series (43 series, 36 papers)

| outcome | direction | series | n | n_clusters | slope | ci_lo | ci_hi | p |
|---|---|---|---|---|---|---|---|---|
| native edge (pH per decade of total) | rising | 28 | 113 | 24 | 0.232 | 0.0132 | 0.451 | 0.0377 |
| native edge (pH per decade of total) | falling | 15 | 80 | 12 | -0.945 | -1.72 | -0.174 | 0.0163 |
| solids-normalised edge | rising | 28 | 113 | 24 | 0.232 | 0.0132 | 0.451 | 0.0377 |
| solids-normalised edge | falling | 15 | 80 | 12 | -0.945 | -1.72 | -0.174 | 0.0163 |
| plateau (fraction) | rising | 28 | 113 | 24 | -0.0104 | -0.0256 | 0.00473 | 0.177 |
| plateau (fraction) | falling | 15 | 80 | 12 | -0.104 | -0.197 | -0.0117 | 0.0273 |
| slope b | rising | 28 | 113 | 24 | -0.0515 | -0.106 | 0.00339 | 0.0659 |
| slope b | falling | 15 | 80 | 12 | 0.165 | 0.0171 | 0.313 | 0.0288 |

## 2. Freundlich exponent (slope of log sorbed per gram on log dissolved, within series)

Pooled within-series exponent: 0.597, 95% interval [0.427, 0.768] (193 curves, 36 papers). 1 = linear sorption; below 1 = heterogeneous sites.

Per series with >= 3 loading levels (17): 6 have an interval below 1; median exponent 0.72.

| series | levels | n | ci_lo | ci_hi |
|---|---|---|---|---|
| bc87|goethite | Se(+4)|falling | 4 | 0.287 | -0.169 | 0.742 |
| d01|kaolinite | U(+6)|rising | 3 | 0.643 | -0.298 | 1.58 |
| dl80|ferrihydrite | Se(+6)|falling | 4 | 0.847 | 0.782 | 0.912 |
| hm86|hematite | U(+6)|falling | 3 | 0.763 | -0.352 | 1.88 |
| j95|gibbsite | U(+6)|rising | 3 | 0.377 | -0.369 | 1.12 |
| k62|ferrihydrite | Sr(+2)|rising | 6 | 0.718 | 0.584 | 0.853 |
| kv13|goethite | Se(+6)|falling | 3 | 0.262 | 0.141 | 0.383 |
| lbhka80|ferrihydrite | Se(+4)|falling | 3 | 0.745 | 0.122 | 1.37 |
| lbhka80|ferrihydrite | Se(+6)|falling | 4 | 0.92 | 0.813 | 1.03 |
| mf92a|goethite | Oxalic acid|falling | 5 | 0.493 | 0.182 | 0.804 |
| mf92|goethite | Oxalic acid|falling | 3 | 0.278 | 0.158 | 0.397 |
| mh20|ferrihydrite | Ra(+2)|rising | 3 | 1.19 | 0.115 | 2.26 |
| sblvd14|ferrihydrite | Ra(+2)|rising | 3 | 1.15 | -0.312 | 2.61 |
| sblvd14|goethite | Ra(+2)|rising | 4 | 1.37 | 1.04 | 1.69 |
| sph08|goethite | U(+6)|rising | 3 | 0.614 | -0.898 | 2.13 |
| t83|goethite | U(+6)|rising | 3 | 0.662 | -0.454 | 1.78 |
| wdpwx94|ferrihydrite | U(+6)|rising | 3 | 0.807 | 0.358 | 1.26 |

## 3. One-site vs two-site saturation of log10 Kd against loading (leave-one-pair-out)

420 curves, 48 pairs. Squared error: one-site 76.05, two-site 74.38 (lower is better). One-site saturation loading 10^-3.65 mol/g; two-site 10^-4.75 and 10^-0.00 mol/g, strong-site fraction 0.82.

Not checked: whether high-loading points exceed solubility (needs a cited solubility source).
