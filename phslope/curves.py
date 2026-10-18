"""curves.py -- define curves (single pH sweeps) from the observation table (Stage 0.2-0.4).

CURVE DEFINITION (confirmed by Samuel 2026-10-12; see phslope/README.md):
    one curve = one `Set`.
Evidence (2025 file, 38,906 rows, 3,125 Sets): `Set` is one plotted series in
one paper (e.g. "azbn00_f1" = paper azbn00, figure 1); `SetID` is only a row
counter inside the Set, so (Set, SetID) is unique per row. Every Set has a
single Reference, mineral, sorbate and electrolyte signature, and every Set
with a pH span of at least 1 has exactly one value of ionic strength, total
sorbate, solids loading and temperature. Sets whose pH is constant are mostly
isotherms (total sorbate varies) and are not pH curves.

`build_curves` re-checks these facts on every run (columns `n_*_levels`) and
flags any curve whose conditions are not constant, rather than trusting them.
"""
import warnings

import numpy as np
import pandas as pd

from phslope.common import load_config
from phslope.load import split_signature

CONDITION_COLS = {
    "ionic_strength": 4,        # rounding (decimals) used to count distinct levels
    "total_sorbate_mol_L": None,  # compared on log10 scale, 2 decimals
    "solids_g_L": 4,
    "temp": 0,
    "electrolyte_sig": None,
}


def _n_levels(s, decimals):
    s = s.dropna()
    if s.empty:
        return 0
    # Pandas 3 can infer nullable Arrow string columns, which are not `object`.
    # Condition summaries must treat every non-numeric dtype as categories.
    if not pd.api.types.is_numeric_dtype(s.dtype):
        return s.nunique()
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return 0
    if decimals is None:
        s = np.log10(s[s > 0]).round(2)
    else:
        s = s.round(decimals)
    return s.nunique()


def _cosolutes(sig, background):
    return "+".join(p for p in split_signature(sig) if p not in background)


def _unit_mismatch(resp, cfg):
    r = resp.dropna()
    if r.empty:
        return True
    out = ((r > cfg["upper"]) | (r < cfg["lower"])).mean()
    return bool(out > cfg["max_out_of_range_frac"])


def build_curves(obs, config=None):
    """Returns (curves, curve_obs).

    curves: one row per Set with identity, conditions, point counts, pH range,
            kind ('ph_sweep' / 'constant_ph' / 'too_few_ph_levels'), and flags.
    curve_obs: the observation rows that belong to ph_sweep curves and are
            usable (valid pH, non-missing response), tagged with curve_id.
    """
    config = config or load_config()
    ccfg, rcfg = config["curves"], config["response"]
    background = set(ccfg["background_ions"])

    obs = obs.copy()
    obs["usable"] = ~obs["bad_ph"] & obs["response"].notna()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Mean of empty slice")  # all-NaN medians -> NaN, expected
        curves = _summarise_sets(obs, ccfg, rcfg, background)

    level_cols = [f"n_{c}_levels" for c in CONDITION_COLS]
    identity_cols = ["n_reference_values", "n_mineral_values", "n_sorbate_values"]
    curves["conditions_vary"] = (curves[level_cols] > 1).any(axis=1) | (curves[identity_cols] > 1).any(axis=1)
    curves["has_cosolute"] = curves["cosolutes"] != ""
    curves["solids_reported"] = curves["solids_g_L"].notna() | curves["solids_m2_L"].notna()
    curves["total_sorbate_reported"] = curves["total_sorbate_mol_L"].notna()

    sweep_ids = set(curves.loc[curves["kind"] == "ph_sweep", "curve_id"])
    curve_obs = obs[obs["usable"] & obs["Set"].isin(sweep_ids)].rename(columns={"Set": "curve_id"})
    return curves, curve_obs


def _summarise_sets(obs, ccfg, rcfg, background):
    rows = []
    for set_id, g in obs.groupby("Set", sort=False):
        u = g[g["usable"]]
        ph = u["pH"]
        n_ph_levels = ph.round(ccfg["ph_round"]).nunique()
        span = float(ph.max() - ph.min()) if len(ph) else 0.0
        if n_ph_levels >= ccfg["min_ph_levels"] and span >= ccfg["min_span"]:
            kind = "ph_sweep"
        elif span < 0.2:
            kind = "constant_ph"
        else:
            kind = "too_few_ph_levels"

        row = {
            "curve_id": set_id,
            "reference": g["Reference"].iloc[0],
            "mineral": g["Mineral"].iloc[0],
            "sorbate": g["Sorbate"].iloc[0],
            "electrolyte_sig": g["electrolyte_sig"].iloc[0],
            "cosolutes": _cosolutes(g["electrolyte_sig"].iloc[0], background),
            "kind": kind,
            "n_rows": len(g),
            "n_points": len(u),
            "n_bad_ph": int(g["bad_ph"].sum()),
            "n_missing_response": int(g["response"].isna().sum()),
            "n_ph_levels": int(n_ph_levels),
            "pH_min": float(ph.min()) if len(ph) else np.nan,
            "pH_max": float(ph.max()) if len(ph) else np.nan,
            "pH_span": span,
            "ionic_strength": g["ionic_strength"].median(),
            "total_sorbate_mol_L": g["total_sorbate_mol_L"].median(),
            "solids_g_L": g["solids_g_L"].median(),
            "solids_m2_L": g["solids_m2_L"].median(),
            "temp": g["temp"].median(),
            "co2_present": bool(g["co2_present"].any()),
            "mineralsites": g["mineralsites"].median(),
            "unit_mismatch": _unit_mismatch(u["response"], rcfg),
        }
        for col, dec in CONDITION_COLS.items():
            row[f"n_{col}_levels"] = _n_levels(g[col], dec)
        for key in ("Reference", "Mineral", "Sorbate"):
            row[f"n_{key.lower()}_values"] = g[key].nunique()
        rows.append(row)

    return pd.DataFrame(rows)


def signature_fragmentation(obs, curves):
    """Task 0.4: for each (reference, mineral, sorbate), how many electrolyte
    signatures split it, and what the extra (non-background) members are."""
    sw = curves[curves["kind"] == "ph_sweep"]
    g = sw.groupby(["reference", "mineral", "sorbate"])
    out = pd.DataFrame({
        "n_signatures": g["electrolyte_sig"].nunique(),
        "n_curves": g.size(),
        "n_points": g["n_points"].sum(),
        "signatures": g["electrolyte_sig"].apply(lambda s: "; ".join(sorted(s.unique()))),
        "cosolutes": g["cosolutes"].apply(lambda s: "; ".join(sorted(x for x in s.unique() if x))),
    }).reset_index()
    return out.sort_values(["n_signatures", "n_points"], ascending=False)
