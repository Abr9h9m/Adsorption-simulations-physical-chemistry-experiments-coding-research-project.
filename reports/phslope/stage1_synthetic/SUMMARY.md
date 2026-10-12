# Stage 1 synthetic check: can we recover known slope curves?

Run: commit `c3ff9f9`, config `00e9e1029ccf`, data `synthetic: synth.known_edge_set`, 2026-10-12T23:07:17Z.

## Result

**PASS.** Median slope error over non-flat curves = 0.076 of the true slope range (pass if below 0.2). n = 200 curves (160 non-flat), B = 200 bootstrap resamples.

Slope error = root-mean-square difference between estimated and true slope over the curve's observed grid points, divided by the range of the true slope there. Edge = half-way point of the main rise or fall (the logistic p50); the true edge uses the same definition on the true curve.

## By true shape

| true_shape | n | median_slope_error | median_abs_edge_error | edge_interval_coverage |
|---|---|---|---|---|
| bell | 40 | 0.0778 | 0.11 | 0.55 |
| falling | 40 | 0.0495 | 0.0344 | 0.925 |
| flat | 40 |  |  |  |
| rising | 40 | 0.0444 | 0.0299 | 0.975 |
| two_step | 40 | 0.229 | 0.21 | 0.675 |

Edge-interval coverage is the fraction of curves whose 95% bootstrap interval contains the true edge (nominal 0.95).

## Shape classification (rows = truth, columns = assigned)

| true_shape | bell | falling | flat | multi_step | rising |
|---|---|---|---|---|---|
| bell | 40 | 0 | 0 | 0 | 0 |
| falling | 0 | 40 | 0 | 0 | 0 |
| flat | 0 | 0 | 40 | 0 | 0 |
| rising | 0 | 0 | 0 | 0 | 40 |
| two_step | 0 | 0 | 0 | 27 | 13 |

## Primary model chosen

| true_shape | logistic | spline |
|---|---|---|
| bell | 0 | 40 |
| falling | 40 | 0 |
| flat | 39 | 1 |
| rising | 39 | 1 |
| two_step | 13 | 27 |

## QC flags

| flag | curves_with_flag | curves_with_only_this_flag |
|---|---|---|
| fit_failed | 0 | 0 |
| too_few_points | 0 | 0 |
| narrow_span | 1 | 1 |
| unit_mismatch | 0 | 0 |
| edge_not_bracketed | 76 | 55 |
| poor_fit | 2 | 2 |
| wide_interval | 28 | 7 |
| bootstrap_unstable | 0 | 0 |

## Known limitations

- Smoother-based intervals under-cover the truth (see coverage for bell and two-step curves): the pairs bootstrap captures noise but not the smoothing bias of a fixed penalty. Logistic intervals are close to nominal. Treat edge intervals of smoother-primary curves as too narrow.
- Two-step curves are often classified as `rising`/`falling` when the plateau between steps is short or poorly sampled; their slope error is the highest of the shapes.
- `edge_not_bracketed` fires often here because synthetic pH positions are uniform random, which leaves gaps wider than 0.5 pH near some edges.

Per-curve table: `synthetic_scores.csv`. Figure: `synthetic_slope_error.png`.
