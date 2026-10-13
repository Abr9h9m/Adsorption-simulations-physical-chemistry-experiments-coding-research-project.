# Pooled-pair comparison: what if curves are pooled instead of fitted one by one?

> **EXPLORATORY**, not in the spec (added at Samuel's request, 2026-10-12). Uses all clean curves, including the ones Stage 1 QC rejected.

Run: commit `dfc1d5d`, config `9bb7572104f8`, data `C:\Users\itzju\sc.dataset.csv`, 2026-10-13T11:20:52Z.

Two pooling modes: all points of a mineral-sorbate pair inside one ionic-strength band (low_below_0.01M, medium_0.01_to_0.1M, high_above_0.1M), across Sets and papers; and all points of a pair whatever the ionic strength. Other conditions (total sorbate, solids loading, carbonate) are NOT held constant in either mode; their spread per pool is in the CSVs (`total_sorbate_span_decades`, `solids_span_ratio`, `co2_fraction`).

Each pool is fitted exactly like a single curve (logistic + smoother, shape class, QC flags). Smoother points are averaged into 0.1-pH levels for pooled data. Comparison is with the pool's own curves that are in the core library.

## Results

### pooled within ionic-strength band (`pools_pair_band.csv`)

- Pools: 244 (median 2 references per pool). Pools passing the same QC as single curves: 28.7%. Shapes: {'rising': 108, 'falling': 43, 'bell': 36, 'flat': 29, 'unclassified': 21, 'multi_step': 7}.
- Pooled shape equals the majority shape of the pool's own core curves: 77.6%.
- Width ratio (pooled / median single-curve width), 134 pools: median 1.42 (IQR 1.06-2.00); 31% of pools above 1.5.
- |pooled edge - median single-curve edge|: median 0.28 pH.
- Edge interval from resampling whole papers vs resampling points: median ratio 2.0x wider. The point bootstrap treats points from one paper as independent and is too narrow for pooled data.
- Share of the pooled fit's residual scatter that lies between papers: median 21.7%.

### pooled across all ionic strengths (`pools_pair_all.csv`)

- Pools: 191 (median 2 references per pool). Pools passing the same QC as single curves: 32.5%. Shapes: {'rising': 75, 'falling': 35, 'flat': 32, 'bell': 24, 'unclassified': 18, 'multi_step': 7}.
- Pooled shape equals the majority shape of the pool's own core curves: 79.6%.
- Width ratio (pooled / median single-curve width), 98 pools: median 1.37 (IQR 0.98-1.90); 30% of pools above 1.5.
- |pooled edge - median single-curve edge|: median 0.22 pH.
- Edge interval from resampling whole papers vs resampling points: median ratio 1.9x wider. The point bootstrap treats points from one paper as independent and is too narrow for pooled data.
- Share of the pooled fit's residual scatter that lies between papers: median 22.4%.

## Same pair: one ionic-strength band vs all bands together

90 pairs have curves in two or more bands. Pooling across bands vs within the best-covered band: median width ratio 1.08, median |edge shift| 0.16 pH. Table: `band_vs_all_same_pair.csv`.

## Largest pools (pooled across all ionic strengths)

| pool_id | n_curves | n_references | n_points | shape | edge_pH | cluster_edge_lo | cluster_edge_hi | width | width_ratio | edge_shift | resid_ref_R2 | qc_flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ferrihydrite | U(+6) | 60 | 9 | 982 | unclassified | 8.34 | 4.2 | 4.58 | 0.267 | 1.46 | -0.155 | 0.0776 |  |
| montmorillonite | U(+6) | 51 | 8 | 919 | unclassified | 7.67 | 3.24 | 4.18 | 0.419 | 1.63 | 0.209 | 0.237 |  |
| hematite | Np(+5) | 51 | 6 | 762 | multi_step | 7.01 | 6.63 | 9.5 | 0.442 | 1.55 | -2.2 | 0.12 |  |
| goethite | Se(+4) | 53 | 14 | 705 | multi_step | 10.6 | 7.31 | 11.2 | 0.93 | 1.18 | 0.727 | 0.238 |  |
| hematite | U(+6) | 48 | 10 | 620 | bell | 4.2 | 3.97 | 5.03 | 0.654 | 3.4 | -2.97 | 0.341 |  |
| goethite | Se(+6) | 47 | 8 | 604 | bell | 2.71 | 3.52 | 7.86 | 0.181 | 0.291 | -2.21 | 0.392 |  |
| kaolinite | U(+6) | 39 | 5 | 591 | bell | 8.72 | 4.3 | 4.67 | 0.57 | 2.05 | 0.315 | 0.128 |  |
| illite | Eu(+3) | 28 | 7 | 560 | rising | 4.4 | 3.77 | 4.98 | 0.918 | 2.63 | -0.945 | 0.107 | poor_fit |
| quartz | U(+6) | 42 | 12 | 514 | bell | 4.75 | 4.59 | 5.08 | 0.46 | 1.74 | -1.79 | 0.29 |  |
| goethite | U(+6) | 36 | 9 | 510 | unclassified | 4.22 | 3.85 | 5.97 | 0.381 | 1.39 | -0.474 | 0.324 |  |
| montmorillonite | Ni(+2) | 14 | 3 | 507 | bell | 5.97 | 5.84 | 6.62 | 1.01 | 1.74 | -0.87 | 0.0541 | poor_fit |
| illite | Ni(+2) | 25 | 4 | 448 | rising | 5.07 | 4.6 | 5.7 | 0.91 | 1.37 | -0.0529 | 0.262 | poor_fit |
| hematite | Am(+3) | 34 | 3 | 443 | rising | 6.31 | 3.61 | 6.45 | 0.569 | 2.13 | 0.0294 | 0.14 | poor_fit |
| goethite | Oxalic acid | 34 | 9 | 406 | bell | 7.19 | 6.44 | 7.48 | 1 | 1.17 | 0.363 | 0.212 |  |
| montmorillonite | Np(+5) | 22 | 5 | 395 | rising | 9.85 | 9.06 | 10.3 | 0.762 | 1.5 | 1.73 | 0.325 | poor_fit |
| ferrihydrite | Se(+4) | 24 | 6 | 331 | falling | 8.84 | 8.52 | 10.2 | 0.751 | 1.87 | -0.1 | 0.231 |  |
| montmorillonite | Eu(+3) | 13 | 6 | 319 | unclassified | 4.87 | 3.72 | 6.29 | 0.338 | 0.581 | -0.68 | 0.0552 | poor_fit |
| ferrihydrite | Se(+6) | 28 | 7 | 281 | falling | 5.27 | 4.96 | 6.24 | 0.988 | 1.97 | -0.831 | 0.338 | wide_interval |
| gibbsite | U(+6) | 16 | 5 | 274 | rising | 4.67 | 4.44 | 5.48 | 0.713 | 2.58 | -0.166 | 0.227 |  |
| bentonite | U(+6) | 17 | 4 | 272 | unclassified | 5.36 | 4.02 | 5.94 | 0.591 | 1.5 | -0.709 | 0.236 |  |

## How to read this

If pooling across papers were harmless, pooled widths would match single-curve widths (ratio ~1), pooled edges would sit on the single-curve median, and little residual scatter would line up with papers. A ratio well above 1 and a large between-paper residual share mean the pooled curve mixes study offsets into its shape: the pooled slope is flatter and wider than any single experiment's.

Files: `pools_pair_band.csv`, `pools_pair_all.csv`, `band_vs_all_same_pair.csv`, `pooling_effects.png`, `pooled_diagnostics.pdf` (one page per pool; not committed).
