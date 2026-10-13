"""data.py -- the one way experiments get data (development papers only by default).

build(include_locked=False) returns (curves, obs):
  curves  one row per clean pH-sweep curve: Stage 1 meta (shape, logistic fit, core flag, conditions)
          + per-curve extras from the raw file (specific surface area, material source, CO2 partial
          pressure, atmosphere class, added carbonate) + the log10 K line fit over mid-range points
          (a, b, r2, n_mid, pH_native, pH_S1, line_ok)
  obs     observation rows of those curves with the kd.py quantities
include_locked=True is used ONLY by the E0 regression check, which reproduces numbers that were
computed on all papers before the locked set existed; every such call is written to the registry.
"""
import os

import numpy as np
import pandas as pd

from phslope.common import REPORTS_DIR, load_config, load_yaml
from phslope.experiments import kd as kdmod
from phslope.experiments.registry import load_exp_config, log_run, read_locked
from phslope.load import split_signature

LIB = os.path.join(REPORTS_DIR, "stage1", "library")
AIR_PCO2 = (2.5e-4, 5.0e-4)        # bar; reported pCO2 in this window -> "air-equilibrated"


def _gas_co2(g):
    """log10 pCO2 (bar) from Gas1..3 for one curve's rows (median), or NaN."""
    vals = []
    for i in (1, 2, 3):
        lab, val = g.get(f"Gas{i}"), g.get(f"Gas{i}_val")
        if lab is None:
            continue
        v = pd.to_numeric(val, errors="coerce").where(lab == "CO2(g)")
        vals.append(v)
    v = pd.concat(vals, axis=1).max(axis=1) if vals else pd.Series(dtype=float)
    v = v[v > 0]
    return float(np.log10(v.median())) if len(v) else np.nan


def _atmosphere(g, log_pco2):
    gases = set()
    for i in (1, 2, 3):
        if f"Gas{i}" in g:
            gases |= set(g[f"Gas{i}"].dropna().unique())
    if np.isfinite(log_pco2):
        p = 10 ** log_pco2
        return "air_equilibrated" if AIR_PCO2[0] <= p <= AIR_PCO2[1] else "controlled_co2"
    if gases & {"N2(g)", "Ar(g)", "H2(g)"}:
        return "co2_free"
    return "unknown"


def _added_carbonate(g):
    tot = 0.0
    for i in range(1, 8):
        lab, val = f"Electrolyte{i}", f"Electrolyte{i}_val"
        if lab in g:
            v = pd.to_numeric(g[val], errors="coerce").where(g[lab] == "C(+4)")
            if v.notna().any():
                tot += float(v.median())
    return tot


def curve_extras(obs):
    rows = []
    for cid, g in obs.groupby("curve_id"):
        lp = _gas_co2(g)
        sa = pd.to_numeric(g["MineralSA"], errors="coerce").where(g.get("MineralSA_units") == "m2/g")
        src = g["Mineral_source"].dropna()
        rows.append({"curve_id": cid, "surface_area_m2_g": float(sa.median()) if sa.notna().any() else np.nan,
                     "mineral_source": src.mode().iloc[0] if len(src) else np.nan,
                     "log10_pco2": lp, "atmosphere": _atmosphere(g, lp), "dic_added_mol_L": _added_carbonate(g)})
    return pd.DataFrame(rows)


def line_fits(obs, cfg_exp, window=None, weight=None):
    """Per-curve log10 K line over mid-range points (>= 3 points spanning >= 0.5 pH).
    window=(lo, hi) overrides the fraction-sorbed window; weight(g) -> array of point weights (WLS)."""
    rows = []
    sel = obs["mid"] if window is None else (obs["response"] > window[0]) & (obs["response"] < window[1])
    for cid, g in obs[sel & obs["log10K"].notna()].groupby("curve_id"):
        if len(g) < 3 or np.ptp(g["pH"]) < 0.5:
            continue
        f = kdmod.line_fit(g["pH"], g["log10K"], None if weight is None else weight(g))
        if abs(f["b"]) < 1e-6:
            continue
        rows.append({"curve_id": cid, "a": f["a"], "b": f["b"], "r2": f["r2"], "n_mid": f["n"], "line_sd": f["sd"],
                     "var_a": f["cov"][0, 0], "var_b": f["cov"][1, 1], "cov_ab": f["cov"][0, 1],
                     "mid_pH_lo": g["pH"].min(), "mid_pH_hi": g["pH"].max()})
    return pd.DataFrame(rows)


def build(include_locked=False, data_file=None, purpose=""):
    from phslope.library import load_library
    from phslope.stage1 import load_real
    cfg, ecfg = load_config(), load_exp_config()
    if include_locked:
        log_run("data", "INCLUDES LOCKED PAPERS", purpose or "unspecified")
    _, curve_obs, _ = load_real(data_file, cfg)
    meta = load_library(LIB)["meta"]
    if not include_locked:
        locked = read_locked()
        meta = meta[~meta["reference"].isin(locked)]
        curve_obs = curve_obs[~curve_obs["Reference"].isin(locked)]
    curve_obs = curve_obs[curve_obs["curve_id"].isin(meta["curve_id"])]
    obs = kdmod.add_kd(curve_obs, ecfg)
    curves = meta.merge(curve_extras(obs), on="curve_id", how="left").merge(line_fits(obs, ecfg), on="curve_id",
                                                                            how="left")
    classes = load_yaml("classes.yaml")
    curves["sorbate_class"] = curves["sorbate"].map(classes.get("sorbates") or {})
    curves["mineral_class"] = curves["mineral"].map(classes.get("minerals") or {})
    curves["pair"] = curves["mineral"] + " | " + curves["sorbate"]
    curves["log10_solids"] = np.log10(curves["solids_g_L"].where(curves["solids_g_L"] > 0))
    curves["log10_total"] = np.log10(curves["total_sorbate_mol_L"].where(curves["total_sorbate_mol_L"] > 0))
    curves["log10_I"] = np.log10(curves["ionic_strength"].where(curves["ionic_strength"] > 0))
    curves["log10L"] = curves["log10_total"] - curves["log10_solids"]
    curves["cosolute"] = curves["has_cosolute"].astype(float)
    curves["co2"] = curves["co2_present"].astype(float)
    curves["direction"] = np.where(curves["shape"] == "falling", -1, np.where(curves["shape"] == "rising", 1, 0))
    curves = finish_curves(curves)
    obs = obs.merge(curves[["curve_id", "reference"]], on="curve_id", how="left")
    return curves, obs


def finish_curves(curves):
    """Derived line columns (edges, direction checks); used after any (re)fit of the lines."""
    curves = curves.copy()
    curves["pH_native"] = -curves["a"] / curves["b"]
    curves["pH_S1"] = (curves["log10_solids"] - curves["a"]) / curves["b"]
    ok_dir = np.where(curves["direction"] == 1, curves["b"] > 0,
                      np.where(curves["direction"] == -1, curves["b"] < 0, False))
    curves["line_dir_ok"] = ok_dir & curves["b"].notna()
    curves["line_in_range"] = (curves["pH_native"] > curves["mid_pH_lo"] - 0.5) & \
                              (curves["pH_native"] < curves["mid_pH_hi"] + 0.5)
    return curves


LINE_COLS = ["a", "b", "r2", "n_mid", "line_sd", "var_a", "var_b", "cov_ab", "mid_pH_lo", "mid_pH_hi"]


def refit_lines(curves, obs, window=None, weight=None):
    """Replace the per-curve line columns with a fit using another window and/or point weights."""
    new = line_fits(obs, None, window, weight)
    return finish_curves(curves.drop(columns=LINE_COLS).merge(new, on="curve_id", how="left"))
