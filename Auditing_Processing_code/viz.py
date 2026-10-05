"""viz.py -- gradient quiver, slope-vs-pH slices, Hessian component heatmaps."""

import numpy as np
import matplotlib.pyplot as plt


def plot_gradient_quiver(points, results, title="", save_path=None):
    pH = [p[0] for p in points]; I = [p[1] for p in points]
    u = [r["gradient"][0] for r in results]; v = [r["gradient"][1] for r in results]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.quiver(pH, I, u, v, angles="xy", scale_units="xy", color="steelblue")
    ax.set(xlabel="pH", ylabel="Ionic strength", title=f"Gradient field: {title}")
    if save_path: fig.savefig(save_path, dpi=150); plt.close(fig)
    return fig


def plot_slope_slices(pH_all, I_all, y_all, scaler, bandwidth, fit_fn, tree,
                       I_levels=None, pH_range=None, n_points=30, title="", save_path=None):
    """Plot dA/dpH vs pH, as separate curves for a few fixed ionic-strength levels."""
    if I_levels is None:
        I_levels = np.quantile(I_all, [0.2, 0.5, 0.8])
    if pH_range is None:
        pH_range = (pH_all.min(), pH_all.max())
    pH_vals = np.linspace(*pH_range, n_points)

    fig, ax = plt.subplots(figsize=(6, 5))
    for I_level in I_levels:
        slopes = []
        for pH in pH_vals:
            r = fit_fn((pH, I_level), pH_all, I_all, y_all, tree, scaler, bandwidth)
            slopes.append(r["gradient"][0] if r["valid"] else np.nan)
        ax.plot(pH_vals, slopes, label=f"I={I_level:.3g}")
    ax.set(xlabel="pH", ylabel="dA/dpH", title=f"Slope vs pH, sliced by I: {title}")
    ax.legend()
    if save_path: fig.savefig(save_path, dpi=150); plt.close(fig)
    return fig


def plot_hessian_heatmaps(points, results, title="", save_path=None):
    pH = np.array([p[0] for p in points]); I = np.array([p[1] for p in points])
    Hpp = np.array([r["hessian"][0, 0] for r in results])
    Hii = np.array([r["hessian"][1, 1] for r in results])
    Hpi = np.array([r["hessian"][0, 1] for r in results])

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, vals, name in zip(axes, [Hpp, Hii, Hpi], ["H_pH,pH", "H_I,I", "H_pH,I"]):
        sc = ax.scatter(pH, I, c=vals, cmap="RdBu_r", s=60,
                         vmin=-np.abs(vals).max(), vmax=np.abs(vals).max())
        ax.set(xlabel="pH", ylabel="Ionic strength", title=name)
        plt.colorbar(sc, ax=ax)
    fig.suptitle(f"Hessian components: {title}")
    plt.tight_layout()
    if save_path: fig.savefig(save_path, dpi=150); plt.close(fig)
    return fig


if __name__ == "__main__":
    import pandas as pd
    from scaling import fit_scaler
    from windowing import build_kdtree
    from fingerprint import compute_field
    from derivatives import gradient_and_hessian_at_point

    df = pd.read_csv("synthetic_pilot_data.csv")
    sub = df[(df["Mineral"] == "goethite") & (df["Sorbate"] == "U(+6)")]
    pH_all, I_all, y_all = sub["pH"].to_numpy(), sub["Electrolyte1_val"].to_numpy(), sub["Sorbed_val"].to_numpy()
    scaler = fit_scaler(pH_all, I_all)
    bandwidth = (0.1, 0.1)
    tree = build_kdtree(*__import__("scaling").to_scaled(pH_all, I_all, scaler))

    points, results = compute_field(pH_all, I_all, y_all, scaler, bandwidth, grid_n=10)
    plot_gradient_quiver(points, results, title="goethite-U(VI)", save_path="quiver_test.png")
    plot_hessian_heatmaps(points, results, title="goethite-U(VI)", save_path="heatmap_test.png")
    plot_slope_slices(pH_all, I_all, y_all, scaler, bandwidth, gradient_and_hessian_at_point, tree,
                       title="goethite-U(VI)", save_path="slices_test.png")
    print("Wrote quiver_test.png, heatmap_test.png, slices_test.png")
