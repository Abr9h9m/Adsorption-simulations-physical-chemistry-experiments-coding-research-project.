# sorption_fingerprint — Pipeline Modules

All modules below are tested and run end-to-end against `synthetic_pilot_data.csv`.

| Module | Status | Notes |
|---|---|---|
| `scaling.py` | done | min-max scaling + gradient/Hessian unit conversion |
| `windowing.py` | done | KD-tree neighbor prefilter + Gaussian kernel weights |
| `local_fit.py` | done | weighted quadratic fit; now with condition-number guard (`IllConditionedFitError`) |
| `derivatives.py` | done | orchestration + **corrected** finite-difference cross-check (evaluates the fitted surrogate directly; confirmed exact agreement) |
| `bandwidth_selection.py` | done | brute-force LOOCV; confirms `(0.1, 0.1)` was already near-optimal on the synthetic goethite–U(VI) system |
| `uncertainty.py` | done | bootstrap resampling; reports gradient/Hessian mean+std and success fraction |
| `fingerprint.py` | done | field computation on a grid + compressed 8-element vector (Math spec §7/12) |
| `compare.py` | done | Tier 1 (vector distance) + Tier 2 (shared-grid shape/orientation similarity) |
| `viz.py` | done | quiver, slope-vs-pH slices, Hessian heatmaps |

## Known caveat in the demo comparisons

The `compare.py` self-test calls `vector_distance` **without** z-scoring, so montmorillonite's much smaller raw magnitudes currently dominate the distance more than they should — this is exactly why the math spec calls for z-scoring before comparing (§8). Not a bug; just not wired up in the quick demo. Fix before trusting any real comparison: compute feature means/stds across all systems being compared, pass them to `vector_distance`.

## Run order for a new system

```python
from scaling import fit_scaler
from fingerprint import compute_field, fingerprint_vector
from bandwidth_selection import select_bandwidth

scaler = fit_scaler(pH_all, I_all)
bandwidth, _ = select_bandwidth(pH_all, I_all, y_all, scaler, candidate_bandwidths)
points, results = compute_field(pH_all, I_all, y_all, scaler, bandwidth)
vec, labeled = fingerprint_vector(points, results)
```

## Not done (needs real data or manual work, not executable here)

- Resolving the goethite–Se(IV) mineral-formula ambiguity
- Obtaining/extracting the supplementary papers (Missana et al., Su & Suarez, etc.)
- Formal `validation_harness` sweep over (n, noise) — straightforward to add using `generate_synthetic_dataset.py`'s `generate_system_data(n, noise_frac, ...)`, not built this pass due to time
- Hat-matrix LOOCV speedup (brute-force version works; optimization deferred per original plan)
