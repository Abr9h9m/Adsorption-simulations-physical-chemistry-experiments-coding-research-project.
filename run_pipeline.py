"""
run_pipeline.py -- end-to-end run on synthetic OR real data.

Set MODE below. In "real" mode it uses the audit's filtered single-study
subsets (NOT the pooled systems), a normalized response (see response.py), and
compares everything in scaled coordinates. Run: python run_pipeline.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from scaling import fit_scaler, to_scaled
from windowing import build_kdtree
from bandwidth_selection import select_bandwidth
from uncertainty import bootstrap_gradient_hessian
from fingerprint import compute_field, fingerprint_vector
from compare import vector_distance, compare_on_shared_grid
from viz import plot_gradient_quiver, plot_slope_slices, plot_hessian_heatmaps
from derivatives import gradient_and_hessian_at_point
from response import compute_response, check_response_range

# ============================== CONFIG =====================================
MODE = os.environ.get("PIPELINE_MODE", "real")   # "synthetic" or "real"
REAL_DATA_FILE = os.environ.get("PIPELINE_DATA", r"C:\Users\itzju\sc.dataset.csv")
REAL_RESPONSE_MODE = "fraction_sorbed"  # or "log_kd"

# Real mode: exact (mineral, electrolyte signature, sorbate) groups from the
# audit's `system` column, e.g. "goethite-Cl(-1)+Na(+1)+P(+5)-Se(+4)".
REAL_SUBSETS = [
    ("goethite",        "Cl(-1)+Na(+1)+P(+5)", "Se(+4)"),
    ("ferrihydrite",    "N(+5)+Na(+1)+P(+5)",  "U(+6)"),
    ("montmorillonite", "Cl(-1)+Na(+1)",       "U(+6)"),
    ("goethite",        "N(+5)+Na(+1)",        "U(+6)"),
]
ONLY_I_VARYING_REFS = True   # keep only references that themselves vary I
MIN_I_LEVELS_PER_REF = 3

BANDWIDTH_CANDIDATES = [(b, b) for b in (0.03, 0.04, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5)]
ERROR_TOLERANCE = 1.25   # candidates within 25% of the best CV error are "acceptable"
MIN_VALID_FRAC = 0.40    # prefer the LEAST smoothing that still covers this much of the grid
GRID_N = 12
MIN_VALID_POINTS = 20    # systems with fewer valid grid points are excluded from comparison
MIN_MATCHED = 20         # pairs with fewer shared grid points get NaN (not a number from 2 points)
MAX_CV_POINTS = 250
# ===========================================================================

OUTPUT_DIR = os.path.join("results", f"pipeline_{MODE}")
FIG_DIR = os.path.join(OUTPUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)
PILOT_SYNTH = [("goethite", "U(+6)"), ("goethite", "Se(+4)"),
               ("montmorillonite", "U(+6)"), ("ferrihydrite", "U(+6)")]


def safe(label):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in label)


def load_systems():
    systems = []
    if MODE == "synthetic":
        from generate_synthetic_dataset import generate_full_dataset, SYSTEM_PARAMS
        df = generate_full_dataset()
        df.to_csv(os.path.join(OUTPUT_DIR, "synthetic_pilot_data.csv"), index=False)
        for mineral, sorbate in PILOT_SYNTH:
            sub = df[(df["Mineral"] == mineral) & (df["Sorbate"] == sorbate)]
            systems.append(dict(label=f"{mineral}-{sorbate}", mineral=mineral, sorbate=sorbate,
                                pH=sub["pH"].to_numpy(), I=sub["Electrolyte1_val"].to_numpy(),
                                y=sub["Sorbed_val"].to_numpy(), truth=SYSTEM_PARAMS[f"{mineral}|{sorbate}"]))
        return systems

    import data_audit as da
    cfg = dict(da.CONFIG); cfg["DATA_FILE"] = REAL_DATA_FILE
    df = da.prepare_data(da.load_raw_data(REAL_DATA_FILE), cfg)
    groups = da.group_by_system(df, cfg)
    for mineral, esig, sorbate in REAL_SUBSETS:
        label = f"{mineral}-{esig}-{sorbate}"
        sub = groups.get((mineral, esig, sorbate))
        if sub is None:
            print(f"[{label}] NOT FOUND in data -- check the exact signature spelling"); continue
        sub = sub.copy()
        sub["_y"] = compute_response(sub, REAL_RESPONSE_MODE)
        sub = sub.dropna(subset=["_pH", "_ionic_strength", "_y"])
        sub = sub[sub["_ionic_strength"] > 0]
        if ONLY_I_VARYING_REFS:
            ref_col = cfg["COL_REFERENCE"]
            n_levels = sub.groupby(ref_col)["_ionic_strength"].transform(lambda s: s.round(3).nunique())
            before = len(sub); sub = sub[n_levels >= MIN_I_LEVELS_PER_REF]
            print(f"[{label}] kept {len(sub)}/{before} rows from references with >= {MIN_I_LEVELS_PER_REF} I levels")
        check_response_range(sub["_y"], REAL_RESPONSE_MODE, label)
        if len(sub) < 50:
            print(f"[{label}] only {len(sub)} usable rows -- skipping"); continue
        systems.append(dict(label=label, mineral=mineral, sorbate=sorbate,
                            pH=sub["_pH"].to_numpy(), I=sub["_ionic_strength"].to_numpy(),
                            y=sub["_y"].to_numpy(), truth=None))
    return systems


def choose_bandwidth(label, pH, I, y, scaler):
    """Returns (bandwidth, points, results) or None if the system can't support a field."""
    best, cv = select_bandwidth(pH, I, y, scaler, BANDWIDTH_CANDIDATES, max_points=MAX_CV_POINTS)
    if not np.isfinite(cv[best]):
        print(f"[{label}] SKIPPED: no candidate bandwidth can predict >=60% of held-out points (too little data)")
        return None
    cands = sorted(cv)
    if best in (cands[0], cands[-1]):
        print(f"[{label}] WARNING: CV optimum {best} is at the EDGE of the candidate range -- extend the range")
    cache = {}
    def field_for(bw):
        if bw not in cache: cache[bw] = compute_field(pH, I, y, scaler, bw, grid_n=GRID_N)
        return cache[bw]
    acceptable = sorted(bw for bw, e in cv.items() if np.isfinite(e) and e <= ERROR_TOLERANCE * cv[best])
    for bw in acceptable:                                   # least smoothing first
        pts, res = field_for(bw)
        if len(res) >= MIN_VALID_FRAC * GRID_N**2:
            print(f"[{label}] CV-best {best}; chosen {bw} -> {len(res)}/{GRID_N**2} valid grid points")
            return bw, pts, res
    fallback = max(acceptable, key=lambda bw: len(field_for(bw)[1]))
    if len(field_for(fallback)[1]) == 0:                    # nothing within tolerance: look wider
        for bw in cands:
            if np.isfinite(cv[bw]) and len(field_for(bw)[1]) >= 0.10 * GRID_N**2:
                print(f"[{label}] WARNING: using {bw}, OUTSIDE the CV error tolerance, to get any field")
                return (bw, *field_for(bw))
        print(f"[{label}] SKIPPED: no bandwidth yields a valid field (insufficient local support)")
        return None
    pts, res = field_for(fallback)
    print(f"[{label}] WARNING: no acceptable bandwidth reached {MIN_VALID_FRAC:.0%} coverage; "
          f"using {fallback} -> {len(res)}/{GRID_N**2} valid (interpret with care)")
    return fallback, pts, res


def run_system(s):
    label, pH, I, y = s["label"], s["pH"], s["I"], s["y"]
    scaler = fit_scaler(pH, I)
    chosen = choose_bandwidth(label, pH, I, y, scaler)
    if chosen is None:
        return None
    bw, points, results = chosen
    vec, labeled = fingerprint_vector(points, results)
    rep = (float(np.median(pH)), float(np.median(I)))
    boot = bootstrap_gradient_hessian(rep, pH, I, y, scaler, bw, n_bootstrap=100, seed=0)
    tree = build_kdtree(*to_scaled(pH, I, scaler))
    f = safe(label)
    plot_gradient_quiver(points, results, title=label, save_path=os.path.join(FIG_DIR, f"{f}_quiver.png"))
    plot_hessian_heatmaps(points, results, title=label, save_path=os.path.join(FIG_DIR, f"{f}_heatmap.png"))
    plot_slope_slices(pH, I, y, scaler, bw, gradient_and_hessian_at_point, tree, title=label,
                      save_path=os.path.join(FIG_DIR, f"{f}_slices.png"))
    out = dict(s, bandwidth=bw, points=points, results=results, vec=vec, labeled=labeled,
               boot=boot, rep=rep, n=len(y))
    if s["truth"] is not None:
        from generate_synthetic_dataset import true_gradient_and_hessian
        out["true_g"], out["true_h"] = true_gradient_and_hessian(*rep, s["truth"])
    return out


def compare_all(data):
    vecs = np.array([d["vec"] for d in data]); mu, sd = vecs.mean(0), vecs.std(0); sd[sd == 0] = 1
    rows = []
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            a, b = data[i], data[j]
            comps = compare_on_shared_grid(a["points"], a["results"], b["points"], b["results"])
            n_matched = len(comps)
            if n_matched < MIN_MATCHED: comps = []        # too few shared points to report anything
            rows.append({"system_1": a["label"], "system_2": b["label"],
                         "same_mineral": a["mineral"] == b["mineral"], "same_sorbate": a["sorbate"] == b["sorbate"],
                         "tier1_z_distance": vector_distance(a["vec"], b["vec"], mu, sd, n_systems=len(data)),
                         "tier2_shape_sim": np.mean([c["shape_similarity"] for c in comps]) if comps else np.nan,
                         "tier2_shape_sim_signless": np.mean([c["abs_shape_similarity"] for c in comps]) if comps else np.nan,
                         "tier2_angle_deg": np.mean([c["orientation_angle_deg"] for c in comps]) if comps else np.nan,
                         "n_matched": n_matched})
    return pd.DataFrame(rows).round(3)


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def write_summary(data, comp, path):
    L = [f"# Pipeline Run Summary ({MODE} data)\n", "## Per-system fingerprints (scaled units)\n"]
    fp = pd.DataFrame([{"system": d["label"], "N": d["n"], "bandwidth": d["bandwidth"], "valid_pts": len(d["results"]),
                        **{k: f"{v:.3g}" for k, v in d["labeled"].items()}} for d in data])
    L.append(md_table(fp))
    L.append("\n## Bootstrap uncertainty at the representative point (gradient std; Hessian [Hpp,Hii,Hpi] std; real units)\n")
    L.append(md_table(pd.DataFrame([{"system": d["label"], "success_frac": d["boot"]["success_frac"],
        "grad_std": None if d["boot"]["gradient_std"] is None else np.array2string(d["boot"]["gradient_std"], precision=3),
        "hess_std": None if d["boot"]["hessian_std"] is None else np.array2string(d["boot"]["hessian_std"], precision=3)} for d in data])))
    if all(d["truth"] is not None for d in data):
        L.append("\n## Fitted vs true at the representative point (validation)\n")
        L.append(md_table(pd.DataFrame([{"system": d["label"],
            "fitted_grad": np.array2string(d["boot"]["point_estimate"]["gradient"], precision=3),
            "true_grad": np.array2string(d["true_g"], precision=3)} for d in data
            if d["boot"]["point_estimate"]["valid"]])))
    L.append("\n## Cross-system comparison (scaled Hessians; |lambda|-dominant eigenvector)\n")
    L.append(md_table(comp))
    flags = ["Signed shape similarity treats an increasing edge (e.g. cation) and a decreasing edge (e.g. anion) as "
             "opposite shapes; use the signless column to ask about geometry independent of sorbate charge."]
    if len(comp):
        if np.nanmax(comp["tier2_shape_sim"]) - np.nanmin(comp["tier2_shape_sim"]) < 0.05:
            flags.append("Tier-2 shape similarity barely varies across pairs: metric is not discriminating.")
        if np.nanmax(comp["tier2_angle_deg"]) < 10:
            flags.append("All orientation angles < 10 deg: curvature direction is the same everywhere (or saturated).")
        if len(data) < 6:
            flags.append(f"Only {len(data)} systems: Tier-1 z-scored distances are descriptive only.")
    L.append("\n## Metric sanity flags\n" + ("\n".join(f"- {f}" for f in flags) if flags else "- none triggered"))
    open(path, "w").write("\n".join(L))


if __name__ == "__main__":
    systems = load_systems()
    data = [d for d in (run_system(s) for s in systems) if d is not None and len(d["results"]) >= MIN_VALID_POINTS]
    skipped = [s["label"] for s in systems if s["label"] not in {d["label"] for d in data}]
    if skipped: print(f"EXCLUDED from comparison (< {MIN_VALID_POINTS} valid grid points or no field):", skipped)
    if len(data) < 2:
        raise SystemExit("Fewer than 2 systems produced a valid field -- nothing to compare.")
    comp = compare_all(data)
    comp.to_csv(os.path.join(OUTPUT_DIR, "comparison_table.csv"), index=False)
    print(comp.to_string(index=False))
    write_summary(data, comp, os.path.join(OUTPUT_DIR, "SUMMARY.md"))
    print(f"\nDone -> {OUTPUT_DIR}/SUMMARY.md and {FIG_DIR}/")