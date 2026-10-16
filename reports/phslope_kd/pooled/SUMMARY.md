# Pooled-pair comparison: what if curves are pooled instead of fitted one by one?

> **EXPLORATORY**, not in the spec (added at Samuel's request, 2026-10-12). Uses all clean curves, including the ones Stage 1 QC rejected.

Run: commit `d468a46`, config `7683c4e695c4`, data `C:\Users\itzju\sc.dataset.csv`, 2026-10-16T12:28:41Z.

Two pooling modes: all points of a mineral-sorbate pair inside one ionic-strength band (low_below_0.01M, medium_0.01_to_0.1M, high_above_0.1M), across Sets and papers; and all points of a pair whatever the ionic strength. Other conditions (total sorbate, solids loading, carbonate) are NOT held constant in either mode; their spread per pool is in the CSVs (`total_sorbate_span_decades`, `solids_span_ratio`, `co2_fraction`).

Each pool is fitted exactly like a single curve (logistic + smoother, shape class, QC flags). Smoother points are averaged into 0.1-pH levels for pooled data. Comparison is with the pool's own curves that are in the core library.

## Results

### pooled within ionic-strength band (`pools_pair_band.csv`)

- Pools: 239 (median 2 references per pool). Pools passing the same QC as single curves: 24.3%. Shapes: {'rising': 91, 'flat': 46, 'bell': 36, 'falling': 33, 'unclassified': 27, 'multi_step': 6}.
- Pooled shape equals the majority shape of the pool's own core curves: 68.7%.
- Width ratio (pooled / median single-curve width), 99 pools: median 1.40 (IQR 1.00-1.85); 27% of pools above 1.5.
- |pooled edge - median single-curve edge|: median 0.34 pH.
- Edge interval from resampling whole papers vs resampling points: median ratio 1.7x wider. The point bootstrap treats points from one paper as independent and is too narrow for pooled data.
- Share of the pooled fit's residual scatter that lies between papers: median 23.5%.

### pooled across all ionic strengths (`pools_pair_all.csv`)

- Pools: 188 (median 1 references per pool). Pools passing the same QC as single curves: 32.4%. Shapes: {'rising': 66, 'flat': 48, 'bell': 25, 'falling': 25, 'unclassified': 20, 'multi_step': 4}.
- Pooled shape equals the majority shape of the pool's own core curves: 69.4%.
- Width ratio (pooled / median single-curve width), 72 pools: median 1.34 (IQR 0.97-1.81); 25% of pools above 1.5.
- |pooled edge - median single-curve edge|: median 0.39 pH.
- Edge interval from resampling whole papers vs resampling points: median ratio 2.6x wider. The point bootstrap treats points from one paper as independent and is too narrow for pooled data.
- Share of the pooled fit's residual scatter that lies between papers: median 26.3%.

## Same pair: one ionic-strength band vs all bands together

90 pairs have curves in two or more bands. Pooling across bands vs within the best-covered band: median width ratio 1.06, median |edge shift| 0.16 pH. Table: `band_vs_all_same_pair.csv`.

## Largest pools (pooled across all ionic strengths)

| pool_id | n_curves | n_references | n_points | shape | edge_pH | cluster_edge_lo | cluster_edge_hi | width | width_ratio | edge_shift | resid_ref_R2 | qc_flags |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ferrihydrite | U(+6) | 60 | 9 | 982 | bell | 3.8 | 3.71 | 9.13 | 0.456 | 2.33 | -4.96 | 0.0604 | poor_fit |
| montmorillonite | U(+6) | 45 | 8 | 763 | unclassified | 7.83 | 3.73 | 4.14 | 0.359 | 1.23 | 0.911 | 0.0542 |  |
| hematite | Np(+5) | 49 | 6 | 739 | bell | 6.72 | 6.47 | 6.88 | 0.387 | 1.6 | -2.67 | 0.214 |  |
| goethite | Se(+4) | 52 | 13 | 686 | unclassified | 9.03 | 8.98 | 10.2 | 0.552 | 0.822 | -0.385 | 0.645 |  |
| hematite | U(+6) | 48 | 10 | 620 | unclassified | 4.74 | 4.31 | 5.16 | 0.569 | 2.27 | -0.161 | 0.175 |  |
| goethite | Se(+6) | 47 | 8 | 604 | bell | 2.76 | 4.65 | 6.64 | 0.211 | 0.357 | -2.11 | 0.164 |  |
| illite | Eu(+3) | 28 | 7 | 560 | rising | 4.45 | 3.76 | 5.12 | 0.939 | 2.35 | -1.18 | 0.195 | poor_fit |
| kaolinite | U(+6) | 37 | 5 | 555 | bell | 8.46 | 4.5 | 5.03 | 0.54 | 1.91 | 0.591 | 0.258 |  |
| quartz | U(+6) | 43 | 13 | 529 | bell | 5.42 | 4.63 | 7.8 | 0.378 | 1.45 | -0.328 | 0.796 |  |
| goethite | U(+6) | 36 | 9 | 510 | unclassified | 4.18 | 3.91 | 4.54 | 0.404 | 1.48 | -0.209 | 0.243 |  |
| montmorillonite | Ni(+2) | 14 | 3 | 507 | bell | 6.05 | 5.92 | 6.64 | 1 | 1.7 | -0.599 | 0.0543 | poor_fit |
| illite | Ni(+2) | 25 | 4 | 448 | multi_step | 5.53 | 5.17 | 8.17 | 0.884 | 1.43 | 0.439 | 0.533 | poor_fit |
| hematite | Am(+3) | 33 | 2 | 432 | unclassified | 4.64 | 4.54 | 5.14 | 0.0485 | 0.15 | -1.13 | 0.00169 | poor_fit |
| goethite | Oxalic acid | 34 | 9 | 406 | bell | 6.92 | 5.73 | 7.24 | 0.846 | 1.27 | 0.56 | 0.276 |  |
| montmorillonite | Np(+5) | 22 | 5 | 395 | rising | 10.5 | 10.2 | 11.2 | 0.579 | 1.04 | 2.17 | 0.477 | poor_fit |
| ferrihydrite | Se(+4) | 24 | 6 | 331 | falling | 10.2 | 9.7 | 10.5 | 0.521 | 1.37 | 0.373 | 0.349 |  |
| montmorillonite | Eu(+3) | 13 | 6 | 319 | unclassified | 5.12 | 3.89 | 6.37 | 0.388 | 0.717 | -0.543 | 0.0422 | poor_fit |
| gibbsite | U(+6) | 16 | 5 | 274 | unclassified | 5.09 | 4.21 | 7.34 | 0.207 | 0.886 | -0.00644 | 0.445 |  |
| bentonite | U(+6) | 17 | 4 | 272 | bell | 5.38 | 4.09 | 5.89 | 0.57 | 1.31 | -0.683 | 0.0929 |  |
| ferrihydrite | Se(+6) | 26 | 7 | 259 | falling | 6.66 | 6.32 | 6.86 | 0.566 | 1.43 | 0.168 | 0.241 |  |

## How to read this

If pooling across papers were harmless, pooled widths would match single-curve widths (ratio ~1), pooled edges would sit on the single-curve median, and little residual scatter would line up with papers. A ratio well above 1 and a large between-paper residual share mean the pooled curve mixes study offsets into its shape: the pooled slope is flatter and wider than any single experiment's.

Files: `pools_pair_band.csv`, `pools_pair_all.csv`, `band_vs_all_same_pair.csv`, `pooling_effects.png`, `pooled_diagnostics.pdf` (one page per pool; not committed).
