"""bandwidth_selection.py -- leave-one-out cross-validation for bandwidth choice."""

import numpy as np
from scaling import fit_scaler, to_scaled
from windowing import build_kdtree, find_candidate_neighbors, kernel_weights
from local_fit import design_matrix, fit_weighted_quadratic, IllConditionedFitError
from derivatives import evaluate_fitted_surrogate


def _predict_held_out(held_idx, pH_scaled_all, I_scaled_all, y_all, tree, bandwidth):
    """Fits using every point EXCEPT held_idx, predicts the held-out point's own value."""
    query_scaled = (pH_scaled_all[held_idx], I_scaled_all[held_idx])
    idx = find_candidate_neighbors(query_scaled, tree, bandwidth)
    idx = idx[idx != held_idx]
    if len(idx) < 10:
        return None
    coords = np.column_stack([pH_scaled_all[idx], I_scaled_all[idx]])
    weights = kernel_weights(query_scaled, coords, bandwidth)
    d_pH, d_I = coords[:, 0] - query_scaled[0], coords[:, 1] - query_scaled[1]
    Phi = design_matrix(d_pH, d_I)
    try:
        theta = fit_weighted_quadratic(Phi, y_all[idx], weights)
    except IllConditionedFitError:
        return None
    return evaluate_fitted_surrogate(theta, 0.0, 0.0)  # predict AT the held-out point (delta=0)


def loocv_error(pH_all, I_all, y_all, scaler, bandwidth, max_points=300, seed=0):
    """
    Brute-force LOOCV mean squared error. Subsamples to max_points for speed
    on large datasets (still O(n) refits, each cheap) -- full n not required
    to get a reliable bandwidth comparison.
    """
    pH_scaled, I_scaled = to_scaled(pH_all, I_all, scaler)
    n = len(pH_all)
    if n > max_points:
        rng = np.random.default_rng(seed)
        sample_idx = rng.choice(n, max_points, replace=False)
    else:
        sample_idx = np.arange(n)

    tree = build_kdtree(pH_scaled, I_scaled)
    errors = []
    for i in sample_idx:
        pred = _predict_held_out(i, pH_scaled, I_scaled, y_all, tree, bandwidth)
        if pred is not None:
            errors.append((pred - y_all[i]) ** 2)
    return float(np.mean(errors)) if errors else np.inf


def select_bandwidth(pH_all, I_all, y_all, scaler, candidate_bandwidths, max_points=300):
    """Tries each candidate bandwidth, returns (best_bandwidth, all_results)."""
    results = {}
    for bw in candidate_bandwidths:
        results[bw] = loocv_error(pH_all, I_all, y_all, scaler, bw, max_points=max_points)
    best = min(results, key=results.get)
    return best, results


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("synthetic_pilot_data.csv")
    sub = df[(df["Mineral"] == "goethite") & (df["Sorbate"] == "U(+6)")]
    pH_all, I_all, y_all = sub["pH"].to_numpy(), sub["Electrolyte1_val"].to_numpy(), sub["Sorbed_val"].to_numpy()
    scaler = fit_scaler(pH_all, I_all)

    candidates = [(0.03, 0.03), (0.05, 0.05), (0.1, 0.1), (0.2, 0.2), (0.3, 0.3)]
    best, results = select_bandwidth(pH_all, I_all, y_all, scaler, candidates, max_points=200)
    for bw, err in sorted(results.items(), key=lambda x: x[1]):
        print(f"  bandwidth={bw}: LOOCV MSE={err:.3f}")
    print(f"Best bandwidth: {best} (placeholder used previously was (0.1, 0.1))")
