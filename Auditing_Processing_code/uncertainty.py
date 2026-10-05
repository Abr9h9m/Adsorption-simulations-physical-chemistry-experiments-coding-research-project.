"""uncertainty.py -- bootstrap resampling for gradient/Hessian confidence."""

import numpy as np
from scaling import fit_scaler
from windowing import build_kdtree
from derivatives import gradient_and_hessian_at_point


def bootstrap_gradient_hessian(query_point, pH_all, I_all, y_all, scaler, bandwidth,
                                n_bootstrap=200, min_n_eff=18.0, seed=0):
    """
    Resamples (pH, I, y) triples with replacement n_bootstrap times, refits
    gradient/Hessian at query_point each time. Returns the point estimate
    (from the full dataset) plus the bootstrap mean/std for gradient and
    the 3 unique Hessian entries, and the fraction of successful fits
    (fits can fail/be invalid on a resample, e.g. ill-conditioned).
    """
    rng = np.random.default_rng(seed)
    n = len(pH_all)

    pH_scaled_full, I_scaled_full = None, None  # not needed here; tree built per resample
    full_tree = build_kdtree(*_scaled(pH_all, I_all, scaler))
    point_estimate = gradient_and_hessian_at_point(query_point, pH_all, I_all, y_all, full_tree, scaler, bandwidth, min_n_eff)

    grads, hesss = [], []
    for b in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        pH_b, I_b, y_b = pH_all[idx], I_all[idx], y_all[idx]
        tree_b = build_kdtree(*_scaled(pH_b, I_b, scaler))
        result = gradient_and_hessian_at_point(query_point, pH_b, I_b, y_b, tree_b, scaler, bandwidth, min_n_eff)
        if result["valid"]:
            grads.append(result["gradient"])
            hesss.append([result["hessian"][0, 0], result["hessian"][1, 1], result["hessian"][0, 1]])

    success_frac = len(grads) / n_bootstrap
    if not grads:
        return {"point_estimate": point_estimate, "success_frac": 0.0,
                "gradient_mean": None, "gradient_std": None,
                "hessian_mean": None, "hessian_std": None}

    grads, hesss = np.array(grads), np.array(hesss)
    return {
        "point_estimate": point_estimate,
        "success_frac": success_frac,
        "gradient_mean": grads.mean(axis=0), "gradient_std": grads.std(axis=0),
        "hessian_mean": hesss.mean(axis=0), "hessian_std": hesss.std(axis=0),  # [Hpp, Hii, Hpi]
    }


def _scaled(pH, I, scaler):
    from scaling import to_scaled
    return to_scaled(pH, I, scaler)


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("synthetic_pilot_data.csv")
    sub = df[(df["Mineral"] == "goethite") & (df["Sorbate"] == "U(+6)")]
    pH_all, I_all, y_all = sub["pH"].to_numpy(), sub["Electrolyte1_val"].to_numpy(), sub["Sorbed_val"].to_numpy()
    scaler = fit_scaler(pH_all, I_all)

    result = bootstrap_gradient_hessian((6.0, 0.1), pH_all, I_all, y_all, scaler, (0.1, 0.1), n_bootstrap=100)
    print(f"Success fraction: {result['success_frac']:.2f}")
    if result["gradient_mean"] is not None:
        print(f"Gradient: point={np.round(result['point_estimate']['gradient'], 2)}, "
              f"bootstrap mean={np.round(result['gradient_mean'], 2)}, std={np.round(result['gradient_std'], 2)}")
        print(f"Hessian [Hpp,Hii,Hpi] std: {np.round(result['hessian_std'], 2)} "
              f"-- wide std relative to mean = low-confidence estimate")
