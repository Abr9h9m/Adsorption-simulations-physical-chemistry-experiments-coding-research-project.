# E12 Loading and heterogeneous sites

**Plain English.** If a mineral surface has a few strong binding sites and many weak ones, adding more contaminant fills the strong sites first, so each extra unit binds less well. We checked within papers that varied only the amount of contaminant. Result: **HETEROGENEITY SUPPORTED**.

> EXPLORATORY. **[lit]** Balistrieri & Chao 1987; Dzombak & Morel 1986 (abstracts read). Development papers only. Locked set hash `88b1c3a1b769`. Commit `431e55c-dirty`.

## 1. Within-paper concentration series (52 series, 40 papers)

| outcome | direction | series | n | n_clusters | slope | ci_lo | ci_hi | p |
|---|---|---|---|---|---|---|---|---|
| native edge (pH per decade of total) | rising | 35 | 162 | 27 | 0.251 | 0.00823 | 0.493 | 0.0427 |
| native edge (pH per decade of total) | falling | 17 | 86 | 13 | -1.3 | -2.19 | -0.417 | 0.00397 |
| solids-normalised edge | rising | 35 | 162 | 27 | 0.297 | -0.197 | 0.791 | 0.239 |
| solids-normalised edge | falling | 17 | 86 | 13 | -1.02 | -1.91 | -0.134 | 0.0242 |
| plateau (fraction) | rising | 35 | 162 | 27 | -0.0237 | -0.0458 | -0.00166 | 0.0351 |
| plateau (fraction) | falling | 17 | 86 | 13 | -0.137 | -0.248 | -0.0259 | 0.0156 |
| slope b | rising | 35 | 162 | 27 | -0.0919 | -0.14 | -0.0438 | 0.000183 |
| slope b | falling | 17 | 86 | 13 | 0.197 | 0.00782 | 0.385 | 0.0412 |

## 2. Freundlich exponent (slope of log sorbed per gram on log dissolved, within series)

Pooled within-series exponent: 0.659, 95% interval [0.494, 0.824] (248 curves, 40 papers). 1 = linear sorption; below 1 = heterogeneous sites.

Per series with >= 3 loading levels (25): 10 have an interval below 1; median exponent 0.75.

| series | levels | n | ci_lo | ci_hi |
|---|---|---|---|---|
| akbn96|ferrihydrite | U(+6)|rising | 3 | 0.671 | 0.26 | 1.08 |
| bc87|goethite | Se(+4)|falling | 6 | 0.465 | 0.286 | 0.644 |
| bm81|goethite | Ca(+2)|rising | 5 | 0.275 | 0.033 | 0.516 |
| bm81|goethite | Mg(+2)|rising | 5 | 0.376 | -0.236 | 0.988 |
| bs14|ferrihydrite | Ra(+2)|rising | 3 | 1.21 | 0.718 | 1.7 |
| bs14|goethite | Ra(+2)|rising | 4 | 0.968 | 0.919 | 1.02 |
| d01|kaolinite | U(+6)|rising | 3 | 0.701 | 0.47 | 0.932 |
| d01|quartz | U(+6)|rising | 5 | 0.662 | 0.25 | 1.07 |
| dl80|ferrihydrite | Se(+6)|falling | 3 | 0.842 | 0.662 | 1.02 |
| eicg03|illite | Ni(+2)|rising | 5 | 0.826 | 0.765 | 0.887 |
| fw98|goethite | Humic acid|falling | 3 | 0.301 | -0.306 | 0.907 |
| j95|gibbsite | U(+6)|rising | 3 | 0.377 | -0.369 | 1.12 |
| k62|ferrihydrite | Sr(+2)|rising | 7 | 0.773 | 0.689 | 0.857 |
| kdse04|montmorillonite | U(+6)|rising | 3 | 0.844 | 0.427 | 1.26 |
| kv13|goethite | Se(+6)|falling | 3 | 0.262 | 0.141 | 0.383 |
| lbhka80|ferrihydrite | Se(+4)|falling | 3 | 0.861 | 0.436 | 1.29 |
| lbhka80|ferrihydrite | Se(+6)|falling | 3 | 0.89 | 0.359 | 1.42 |
| mf92a|goethite | Oxalic acid|falling | 5 | 0.532 | 0.236 | 0.828 |
| mf92|goethite | Oxalic acid|falling | 3 | 0.317 | 0.21 | 0.425 |
| mh20|ferrihydrite | Ra(+2)|rising | 3 | 1.24 | 0.979 | 1.5 |
| sblvd14|ferrihydrite | Ra(+2)|rising | 3 | 1.25 | 1.15 | 1.34 |
| sblvd14|goethite | Ra(+2)|rising | 4 | 1.06 | 0.903 | 1.21 |
| sph08|goethite | U(+6)|rising | 3 | 0.649 | -0.403 | 1.7 |
| t83|goethite | U(+6)|rising | 3 | 0.754 | -0.0305 | 1.54 |
| wdpwx94|ferrihydrite | U(+6)|rising | 3 | 0.813 | -0.515 | 2.14 |

## 3. One-site vs two-site saturation of log10 Kd against loading (leave-one-pair-out)

496 curves, 56 pairs. Squared error: one-site 224.68, two-site 189.07 (lower is better). One-site saturation loading 10^-0.00 mol/g; two-site 10^-0.00 and 10^-4.42 mol/g, strong-site fraction 0.26.

Not checked: whether high-loading points exceed solubility (needs a cited solubility source).
