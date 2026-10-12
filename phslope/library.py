"""library.py -- build / save / load the slope library G (spec 4.1, Stage 1.2).

G[i, j] is the slope of curve i at grid pH j (fraction sorbed per pH unit),
from the curve's primary model fitted to all its points. lower / upper are the
bootstrap 2.5 / 97.5 percentiles. mask[i, j] is True where grid pH j lies
inside curve i's observed pH range; everything else is NaN.

Files written to the library directory:
  library.npz   grid, curve_ids, G, lower, upper, mask, G_logistic, G_spline, fitted
                (primary-model response), F_logistic, F_spline (each model's response)
  meta.csv      one row per curve: identity, conditions, fit parameters, QC flags, shape
  draws.npz     bootstrap slope draws of the primary model (curves x B x grid, float32);
                large and regenerable, so not committed (see .gitignore)
"""
import os

import numpy as np
import pandas as pd

ARRAYS = ("G", "lower", "upper", "mask", "G_logistic", "G_spline", "fitted", "F_logistic", "F_spline")


def build_library(results, grid):
    """results: list of per-curve dicts from stage1.process_curve."""
    meta = pd.DataFrame([r["meta"] for r in results])
    lib = {"grid": np.asarray(grid), "curve_ids": meta["curve_id"].to_numpy(dtype=str), "meta": meta}
    for k in ARRAYS:
        lib[k] = np.vstack([r["arrays"][k] for r in results]) if results else np.empty((0, len(grid)))
    lib["mask"] = lib["mask"].astype(bool)
    lib["draws"] = (np.stack([r["arrays"]["draws"] for r in results]).astype(np.float32)
                    if results else np.empty((0, 0, len(grid)), np.float32))
    return lib


def save_library(lib, out_dir, include_draws=True):
    os.makedirs(out_dir, exist_ok=True)
    np.savez_compressed(os.path.join(out_dir, "library.npz"), grid=lib["grid"], curve_ids=lib["curve_ids"],
                        **{k: lib[k] for k in ARRAYS})
    lib["meta"].to_csv(os.path.join(out_dir, "meta.csv"), index=False)
    if include_draws:
        np.savez_compressed(os.path.join(out_dir, "draws.npz"), curve_ids=lib["curve_ids"], draws=lib["draws"])


def load_library(out_dir, with_draws=False):
    z = np.load(os.path.join(out_dir, "library.npz"), allow_pickle=False)
    lib = {k: z[k] for k in z.files}
    lib["mask"] = lib["mask"].astype(bool)
    lib["meta"] = pd.read_csv(os.path.join(out_dir, "meta.csv"), keep_default_na=True)
    lib["meta"]["qc_flags"] = lib["meta"]["qc_flags"].fillna("")
    if with_draws:
        d = np.load(os.path.join(out_dir, "draws.npz"), allow_pickle=False)
        assert (d["curve_ids"] == lib["curve_ids"]).all()
        lib["draws"] = d["draws"]
    return lib


def core_subset(lib):
    """Indices of curves in the core library (no QC flag, usable shape class)."""
    return np.where(lib["meta"]["in_core_library"].to_numpy(bool))[0]
