"""
derivatives.py -- OWNER: you build the orchestration; cross-check is a joint task

Ties scaling.py + windowing.py + local_fit.py together, and is where the
validity/trust judgment call (n_eff threshold) lives.
"""

import numpy as np

from scaling import fit_scaler, to_scaled, gradient_to_real_units, hessian_to_real_units
from windowing import build_kdtree, find_candidate_neighbors, kernel_weights
from local_fit import design_matrix, fit_weighted_quadratic


def gradient_and_hessian_at_point(query_point, pH_all, I_all, y_all,
                                   tree, scaler, bandwidth, min_n_eff=18.0):
    """
    [YOU BUILD THIS -- the orchestration]
    Returns a dict: {"gradient", "hessian", "n_eff", "valid"}.
    If n_eff < min_n_eff, returns valid=False rather than an unreliable
    estimate -- this is the direct fix for the "sparse-data spike" problem.
    """
    pH_scaled_all, I_scaled_all = to_scaled(pH_all, I_all, scaler)
    query_scaled = to_scaled(np.array([query_point[0]]), np.array([query_point[1]]), scaler)
    query_scaled = (query_scaled[0][0], query_scaled[1][0])

    idx = find_candidate_neighbors(query_scaled, tree, bandwidth)
    if len(idx) == 0:
        return {"gradient": None, "hessian": None, "n_eff": 0.0, "valid": False}

    neighbor_coords = np.column_stack([pH_scaled_all[idx], I_scaled_all[idx]])
    weights = kernel_weights(query_scaled, neighbor_coords, bandwidth)
    n_eff = float(np.sum(weights))

    if n_eff < min_n_eff:
        return {"gradient": None, "hessian": None, "n_eff": n_eff, "valid": False}

    d_pH = neighbor_coords[:, 0] - query_scaled[0]
    d_I = neighbor_coords[:, 1] - query_scaled[1]
    Phi = design_matrix(d_pH, d_I)
    y_neighbors = y_all[idx]
    theta = fit_weighted_quadratic(Phi, y_neighbors, weights)

    grad_scaled = np.array([theta[1], theta[2]])
    hess_scaled = np.array([[theta[3], theta[5]], [theta[5], theta[4]]])

    gradient = gradient_to_real_units(grad_scaled, scaler)
    hessian = hessian_to_real_units(hess_scaled, scaler)

    return {"gradient": gradient, "hessian": hessian, "n_eff": n_eff, "valid": True}


def finite_difference_cross_check(gradient_hessian_fn, query_point, args, step=1e-4):
    """
    [BUILD TOGETHER]
    Independent check: recompute the gradient/Hessian by finite-differencing
    the ALREADY-FITTED surrogate's predictions, not by refitting from scratch.
    NOTE: a fuller version of this evaluates the fitted polynomial surface
    directly; this simplified version instead re-runs the local fit at
    shifted query points, which is a reasonable first pass but slower than
    necessary -- worth revisiting once the basic pipeline is confirmed correct.
    """
    pH0, I0 = query_point
    results = {}
    for name, (dpH, dI) in [("+pH", (step, 0)), ("-pH", (-step, 0)),
                             ("+I", (0, step)), ("-I", (0, -step)), ("0", (0, 0))]:
        pt = (pH0 + dpH, I0 + dI)
        results[name] = gradient_hessian_fn(pt, *args)
    return results


if __name__ == "__main__":
    # Real validation test: fit against synthetic_pilot_data.csv and compare
    # to the known true gradient/Hessian from generate_synthetic_dataset.py.
    import pandas as pd
    import sys
    sys.path.append("..")  # adjust path as needed to find the generator script
    from generate_synthetic_dataset import SYSTEM_PARAMS, true_gradient_and_hessian

    df = pd.read_csv("synthetic_pilot_data.csv")
    system_df = df[(df["Mineral"] == "goethite") & (df["Sorbate"] == "U(+6)")]

    pH_all = system_df["pH"].to_numpy()
    I_all = system_df["Electrolyte1_val"].to_numpy()  # ionic strength, simplified z=1 case
    y_all = system_df["Sorbed_val"].to_numpy()

    scaler = fit_scaler(pH_all, I_all)
    pH_scaled, I_scaled = to_scaled(pH_all, I_all, scaler)
    tree = build_kdtree(pH_scaled, I_scaled)

    query = (6.0, 0.1)
    bandwidth = (0.1, 0.1)  # placeholder -- real value comes from bandwidth_selection.py later

    result = gradient_and_hessian_at_point(query, pH_all, I_all, y_all, tree, scaler, bandwidth)
    print("Fitted result at pH=6, I=0.1:")
    print(f"  valid: {result['valid']}, n_eff: {result['n_eff']:.1f}")
    if result["valid"]:
        print(f"  gradient: {np.round(result['gradient'], 3)}")
        print(f"  hessian:\n{np.round(result['hessian'], 3)}")

    true_grad, true_hess = true_gradient_and_hessian(6.0, 0.1, SYSTEM_PARAMS["goethite|U(+6)"])
    print(f"\nTrue gradient: {np.round(true_grad, 3)}")
    print(f"True Hessian:\n{np.round(true_hess, 3)}")
    print("\n(Fitted values are from NOISY sampled data with a placeholder bandwidth --")
    print(" they won't match exactly yet, but should be in the same ballpark. Exact")
    print(" agreement is the job of Week 5's real validation gate, once bandwidth")
    print(" selection (bandwidth_selection.py) replaces the placeholder above.)")
