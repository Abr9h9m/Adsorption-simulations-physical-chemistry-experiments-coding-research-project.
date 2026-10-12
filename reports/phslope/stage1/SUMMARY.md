# Stage 1 summary: slope curves from the real data

Run: commit `c3ff9f9`, config `00e9e1029ccf`, data `C:\Users\itzju\sc.dataset.csv`, 2026-10-12T23:09:51Z.

## Result

**FAIL.** 46.8% of census-set curves (546 of 1166) survive QC with a usable shape class; the pass line is 80%. (Census set = clean curves in the 76 mineral-sorbate pairs that passed Stage 0.)

All clean curves processed: 1680; in core library: 745.

Shapes other than rising/falling in the census set: 28.0% (not above the 30% warning line).

## Shapes (all processed curves)

| shape | curves |
|---|---|
| rising | 799 |
| falling | 371 |
| flat | 236 |
| bell | 214 |
| unclassified | 33 |
| multi_step | 27 |

## Where curves are lost (census set)

A curve can carry several flags, so the first column does not add up; the second column counts curves lost to that flag alone.

| flag | curves_with_flag | curves_with_only_this_flag |
|---|---|---|
| fit_failed | 4 | 0 |
| too_few_points | 140 | 12 |
| narrow_span | 151 | 74 |
| unit_mismatch | 0 | 0 |
| edge_not_bracketed | 304 | 110 |
| poor_fit | 57 | 29 |
| wide_interval | 277 | 106 |
| bootstrap_unstable | 79 | 0 |

## Where curves are lost (all processed curves)

| flag | curves_with_flag | curves_with_only_this_flag |
|---|---|---|
| fit_failed | 11 | 0 |
| too_few_points | 267 | 19 |
| narrow_span | 242 | 114 |
| unit_mismatch | 0 | 0 |
| edge_not_bracketed | 446 | 131 |
| poor_fit | 72 | 41 |
| wide_interval | 420 | 149 |
| bootstrap_unstable | 171 | 0 |

## Logistic vs smoother (Task 1.4)

948 curves have at least 2 grid points where the two models' slopes differ by more than the larger of their 95% bootstrap half-widths. These are the curves that are not simple edges. List: `logistic_vs_smoother_disagreements.csv`.

## Known limitations (carried from the synthetic check)

- Edge intervals of smoother-primary curves are too narrow (synthetic coverage about 0.65 for a nominal 0.95). Logistic-primary intervals are close to nominal.
- Two-step curves can be classified as single edges.

## Files

- `curve_table.csv`: every curve with fit parameters, shape, flags (non-core and worst fits first).
- `library/`: G, intervals, mask, meta (`library.npz`, `meta.csv`); bootstrap draws in `draws.npz` (not committed).
- `qc_flag_counts.png`, `edge_position_by_sorbate.png`.
- `diagnostics.pdf`: one page per curve (data, both fits, slope with interval); not committed, regenerate with `python -m phslope.stage1`.

## Next decision

Stage 1 FAILS the survival rule. Look at which flags remove the most curves before deciding whether the QC rule or the data is the problem. Do not loosen thresholds just to pass.

## Decision after the failure (Samuel, 2026-10-12)

Continue with the core library (745 curves; 546 in the census set) and label every later result **EXPLORATORY**, because Stage 1 did not meet its pre-set survival rule. Thresholds were not changed. Diagnosis: most lost curves have their edge inside a sampling gap (median gap straddling the edge 0.9 pH) or an edge-position interval wider than 1 pH (median 1.8 pH for flagged curves); only 33 census-set curves have the edge outside the measured range. Reading the bracketing rule as "data extend >= 0.5 pH past the edge on both sides" would give 55.8%, still a FAIL.
