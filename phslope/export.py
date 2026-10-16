"""export.py -- plain tables for the web interface (spec section 9).

    python -m phslope.export [--library DIR] [--out export]

Writes four CSV files that the Streamlit app can read with no pipeline code.
Every row carries `schema_version`; changing a column name is a breaking
change and must bump SCHEMA_VERSION (documented in phslope/README.md).
Every row also carries `library_status`, because the current library failed
the Stage 1 survival rule and is exploratory.
"""
import argparse
import os

import numpy as np
import pandas as pd

from phslope import fit_edge
from phslope.common import EXPORT_DIR, PROJECT_ROOT, REPORTS_DIR, run_stamp, write_stamp
from phslope.library import load_library

SCHEMA_VERSION = 1
LIBRARY_STATUS = "exploratory: Stage 1 core-survival rule not met (46.8% < 80%)"

CURVES_COLS = ["curve_id", "reference", "set_id", "mineral", "sorbate", "electrolyte_sig", "temp_mean",
               "n_points", "pH_min", "pH_max", "shape_class", "qc_flags", "p50", "p50_lo", "p50_hi", "width",
               "height", "in_core_library"]


def curves_meta(lib):
    m = lib["meta"]
    out = pd.DataFrame({
        "curve_id": m["curve_id"], "reference": m["reference"], "set_id": m["curve_id"],   # one curve = one Set
        "mineral": m["mineral"], "sorbate": m["sorbate"], "electrolyte_sig": m["electrolyte_sig"],
        "temp_mean": m["temp"], "n_points": m["n_points"], "pH_min": m["pH_min"], "pH_max": m["pH_max"],
        "shape_class": m["shape"], "qc_flags": m["qc_flags"].fillna(""),
        "p50": m["edge_pH"], "p50_lo": m["edge_lo"], "p50_hi": m["edge_hi"],
        "width": m["width"], "height": m["height"], "in_core_library": m["in_core_library"].astype(bool),
    })
    return out[CURVES_COLS]


def slope_grid(lib):
    n, G = lib["G"].shape
    return pd.DataFrame({
        "curve_id": np.repeat(lib["curve_ids"], G),
        "pH": np.tile(lib["grid"], n),
        "slope": lib["G"].ravel(), "slope_lo": lib["lower"].ravel(), "slope_hi": lib["upper"].ravel(),
        "observed": lib["mask"].ravel(),
    })


def observations(lib, curve_obs):
    """Points used per curve with the primary model's fitted value at each point: exact for
    logistic-primary curves, linear interpolation of the fitted grid (0.25 pH) for smoother-primary."""
    meta = lib["meta"].set_index("curve_id")
    row_of = {c: i for i, c in enumerate(lib["curve_ids"])}
    parts = []
    for cid, g in curve_obs[curve_obs["curve_id"].isin(row_of)].groupby("curve_id"):
        i, m = row_of[cid], meta.loc[cid]
        pH = g["pH"].to_numpy(float)
        if m["primary_model"] == "logistic":
            q = {k: m[f"logistic_{k}"] for k in ("lo", "hi", "p50", "w")}
            fitted, how = fit_edge.predict(q, pH), "exact"
        elif m["primary_model"] == "spline":
            ok = lib["mask"][i] & np.isfinite(lib["fitted"][i])
            fitted = np.interp(pH, lib["grid"][ok], lib["fitted"][i][ok]) if ok.sum() >= 2 else np.full(len(pH), np.nan)
            how = "grid_interpolation"
        else:
            fitted, how = np.full(len(pH), np.nan), "none"
        parts.append(pd.DataFrame({"curve_id": cid, "pH": pH, "response": g["response"].to_numpy(float),
                                   "fitted": fitted, "fitted_method": how}))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["curve_id", "pH", "response", "fitted", "fitted_method"])


def pair_summary(cm):
    core = cm[cm["in_core_library"]]
    g = cm.groupby(["mineral", "sorbate"])
    out = pd.DataFrame({"curve_count": g.size(), "reference_count": g["reference"].nunique(),
                        "core_curve_count": core.groupby(["mineral", "sorbate"]).size()}).fillna(0)
    edge = core.dropna(subset=["p50"]).groupby(["mineral", "sorbate"])["p50"]
    out["mean_p50"] = edge.mean()
    out["p50_spread_sd"] = edge.std()
    out["predicted"] = False                 # filled by Stage 3
    out["heldout_p50_error"] = np.nan        # filled by Stage 3
    out["core_curve_count"] = out["core_curve_count"].astype(int)
    return out.reset_index()


def stamp_columns(df):
    return df.assign(schema_version=SCHEMA_VERSION, library_status=LIBRARY_STATUS)


def run(library_dir, out_dir, curve_obs):
    lib = load_library(library_dir)
    os.makedirs(out_dir, exist_ok=True)
    cm = curves_meta(lib)
    tables = {"curves_meta.csv": cm, "slope_grid.csv": slope_grid(lib),
              "observations.csv": observations(lib, curve_obs), "pair_summary.csv": pair_summary(cm)}
    for name, df in tables.items():
        stamp_columns(df).to_csv(os.path.join(out_dir, name), index=False)
        print(f"  {name}: {len(df):,} rows")
    return tables


def main():
    from phslope.common import load_config
    from phslope.stage1 import load_real
    ap = argparse.ArgumentParser(description="Export tables for the web interface.")
    ap.add_argument("--library", default=os.path.join(REPORTS_DIR, "stage1", "library"))
    ap.add_argument("--data")
    ap.add_argument("--out", default=EXPORT_DIR)
    args = ap.parse_args()
    _, curve_obs, path = load_real(args.data, load_config())
    write_stamp(args.out, run_stamp(path))
    run(args.library, args.out, curve_obs)


if __name__ == "__main__":
    main()
