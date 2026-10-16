# Stage 1 summary: slope curves from the real data

Run: commit `d468a46`, config `7683c4e695c4`, data `C:\Users\itzju\sc.dataset.csv`, 2026-10-16T11:34:26Z.

## Result

**FAIL.** 43.7% of census-set curves (489 of 1118) survive QC with a usable shape class; the pass line is 80%. (Census set = clean curves in the 72 mineral-sorbate pairs that passed Stage 0.)

All clean curves processed: 1627; in core library: 683.

Shapes other than rising/falling in the census set: 33.6% (above the 30% warning line; multi-shape handling stays in scope).

## Shapes (all processed curves)

| shape | curves |
|---|---|
| rising | 716 |
| flat | 350 |
| falling | 293 |
| bell | 198 |
| unclassified | 45 |
| multi_step | 25 |

## Where curves are lost (census set)

A curve can carry several flags, so the first column does not add up; the second column counts curves lost to that flag alone.

| flag | curves_with_flag | curves_with_only_this_flag |
|---|---|---|
| fit_failed | 4 | 0 |
| too_few_points | 131 | 15 |
| narrow_span | 145 | 63 |
| unit_mismatch | 0 | 0 |
| edge_not_bracketed | 317 | 94 |
| poor_fit | 68 | 42 |
| wide_interval | 295 | 95 |
| bootstrap_unstable | 76 | 0 |

## Where curves are lost (all processed curves)

| flag | curves_with_flag | curves_with_only_this_flag |
|---|---|---|
| fit_failed | 11 | 0 |
| too_few_points | 258 | 28 |
| narrow_span | 238 | 100 |
| unit_mismatch | 0 | 0 |
| edge_not_bracketed | 451 | 114 |
| poor_fit | 96 | 63 |
| wide_interval | 421 | 128 |
| bootstrap_unstable | 167 | 0 |

## Logistic vs smoother (Task 1.4)

932 curves have at least 2 grid points where the two models' slopes differ by more than the larger of their 95% bootstrap half-widths. These are the curves that are not simple edges. List: `logistic_vs_smoother_disagreements.csv`.

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
