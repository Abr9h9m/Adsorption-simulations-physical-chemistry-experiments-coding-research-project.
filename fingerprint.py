"""fingerprint.py -- compressed fingerprint vector, per Math spec section 7/12."""

import numpy as np
from scaling import fit_scaler, to_scaled
from windowing import build_kdtree
from derivatives import gradient_and_hessian_at_point


def compute_field(pH_all, I_all, y_all, scaler, bandwidth, grid_n=15, min_n_eff=18.0, margin=0.1):
    """
    Evaluates gradient/Hessian on a grid spanning the data's (scaled) extent,
    shrunk inward by `margin` to avoid edge bias (Math spec section 11).
    Returns a list of result dicts (only valid=True points kept) plus their
    (pH, I) coordinates in real units.
    """
    tree = build_kdtree(*to_scaled(pH_all, I_all, scaler))
    pH_grid = np.linspace(pH_all.min() + margin * np.ptp(pH_all), pH_all.max() - margin * np.ptp(pH_all), grid_n)
    I_grid = np.linspace(I_all.min() + margin * np.ptp(I_all), I_all.max() - margin * np.ptp(I_all), grid_n)

    points, results = [], []
    for pH in pH_grid:
        for I in I_grid:
            r = gradient_and_hessian_at_point((pH, I), pH_all, I_all, y_all, tree, scaler, bandwidth, min_n_eff)
            if r["valid"]:
                points.append((pH, I))
                results.append(r)
    return points, results


def fingerprint_vector(points, results):
    """
    Compresses a computed field into phi(s) per Math spec section 7/12:
    [mean |grad|, std |grad|, mean lambda1, mean lambda2, std lambda1, std lambda2,
     frac(cross-term > 0), frac(pH-dominant)]
    Returns the vector plus a labeled dict for readability.
    """
    if not results:
        return None, None

    grad_mags, lambda1s, lambda2s, cross_signs, ph_dominant = [], [], [], [], []
    for r in results:
        g = r["gradient"]
        grad_mags.append(np.linalg.norm(g))
        eigvals = np.linalg.eigvalsh(r["hessian"])  # ascending
        lambda2s.append(eigvals[0]); lambda1s.append(eigvals[1])  # lambda1 >= lambda2
        cross_signs.append(r["hessian"][0, 1] > 0)
        ph_dominant.append(abs(g[0]) > abs(g[1]))

    vec = np.array([
        np.mean(grad_mags), np.std(grad_mags),
        np.mean(lambda1s), np.mean(lambda2s),
        np.std(lambda1s), np.std(lambda2s),
        np.mean(cross_signs), np.mean(ph_dominant),
    ])
    labels = ["mean_grad_mag", "std_grad_mag", "mean_lambda1", "mean_lambda2",
              "std_lambda1", "std_lambda2", "frac_cross_positive", "frac_pH_dominant"]
    return vec, dict(zip(labels, vec))


if __name__ == "__main__":
    import pandas as pd
    df = pd.read_csv("synthetic_pilot_data.csv")
    for mineral, sorbate in [("goethite", "U(+6)"), ("goethite", "Se(+4)"), ("montmorillonite", "U(+6)")]:
        sub = df[(df["Mineral"] == mineral) & (df["Sorbate"] == sorbate)]
        pH_all, I_all = sub["pH"].to_numpy(), sub["Electrolyte1_val"].to_numpy()
        y_all = sub["Sorbed_val"].to_numpy()
        scaler = fit_scaler(pH_all, I_all)
        points, results = compute_field(pH_all, I_all, y_all, scaler, bandwidth=(0.1, 0.1), grid_n=10)
        vec, labeled = fingerprint_vector(points, results)
        print(f"\n{mineral}-{sorbate} ({len(results)}/{len(points) if points else 0} grid points valid):")
        for k, v in labeled.items():
            print(f"  {k}: {v:.3f}")
