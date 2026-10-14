"""predictor.py -- predict_slope_curve (PH_ONLY_DEV_SPEC.md Stage 4.3). EXPLORATORY.

    from phslope.predictor import predict_slope_curve
    out = predict_slope_curve("goethite", "U(+6)", {"solids_g_L": 1.0, "total_sorbate_mol_L": 1e-6,
                                                   "ionic_strength": 0.1})

Model: the final development model (E1 two-step log10 K model + within-between solids + E8 ionic-strength
terms, as assembled by experiments/integrate.py), fitted on DEVELOPMENT papers only (the locked test
papers are never used). log10 K(pH) = a_c + b (pH - pH_c); fraction sorbed f = 1 / (1 + 10^-log10 K);
slope g = df/dpH = ln(10) b f (1 - f). The 2.5/97.5 percentiles come from 400 correlated draws of (a_c, b)
that include paper-to-paper variation, i.e. what a NEW paper would measure.

Returns dict: grid, slope (g), lower, upper, fraction, fraction_lower, fraction_upper, edge_pH (+ interval),
notes (list of plain-language warnings), status.
Raises PredictorError for missing required conditions; warns (in notes) when the system is far from the
training data: pair unseen (class-level prediction only), mineral or sorbate unseen, a condition outside the
training range, sorbate class unassigned.
"""
import os
import pickle

import numpy as np
import pandas as pd

from phslope.common import load_config, load_yaml
from phslope.experiments.registry import EXP_DIR

CACHE = os.path.join(EXP_DIR, "F", "predictor_model.pkl")
REQUIRED = ["solids_g_L", "total_sorbate_mol_L", "ionic_strength"]


class PredictorError(ValueError):
    pass


def _fit():
    from phslope.experiments import e01_logk_mixed as E1
    from phslope.experiments.data import build
    from phslope.experiments.integrate import accepted_adjustments, prepare
    from phslope.experiments.registry import load_exp_config
    ecfg = load_exp_config()
    curves, obs = build(purpose="predictor fit (development papers)")
    acc = accepted_adjustments()
    c = prepare(curves, obs, ecfg, acc)
    covs = [x for s in acc.values() for x in s.get("covs", [])]
    wb = [x for s in acc.values() for x in s.get("within_between", [])]
    m = E1.E1Model(ecfg["e1"], True, covs, wb).fit(c)
    ranges = {k: (c[k].quantile(0.02), c[k].quantile(0.98)) for k in ("log10_solids", "log10_total", "log10_I")}
    meta = {"pairs": c.groupby("pair_dir")["unit"].nunique().to_dict(),
            "minerals": set(c["mineral"]), "sorbates": set(c["sorbate"]),
            "direction_by_sorbate": c.groupby("sorbate")["shape"].agg(lambda s: s.mode().iloc[0]).to_dict(),
            "ranges": ranges, "accepted": list(acc)}
    return m, meta


def load_model(refit=False):
    if not refit and os.path.exists(CACHE):
        with open(CACHE, "rb") as f:
            return pickle.load(f)
    m, meta = _fit()
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "wb") as f:
        pickle.dump((m, meta), f)
    return m, meta


def predict_slope_curve(mineral, sorbate, conditions, direction=None, grid=None, seed=0, model=None):
    from phslope.experiments.e08_ionic_strength import assign_class
    from phslope.experiments.registry import load_exp_config
    missing = [k for k in REQUIRED if conditions.get(k) is None or not np.isfinite(conditions.get(k))]
    if missing:
        raise PredictorError(f"missing or non-numeric conditions: {missing} (required: {REQUIRED})")
    if any(conditions[k] <= 0 for k in REQUIRED):
        raise PredictorError("solids, total sorbate and ionic strength must be positive")
    m, meta = model or load_model()
    notes = ["EXPLORATORY: development-paper model; not validated on the locked test papers."]
    classes = load_yaml("classes.yaml")
    sclass = (classes.get("sorbates") or {}).get(sorbate)
    if sclass is None:
        notes.append(f"sorbate '{sorbate}' has no class in classes.yaml: prediction uses the direction-level mean only")
    if direction is None:
        direction = meta["direction_by_sorbate"].get(sorbate)
        if direction is None:
            raise PredictorError(f"sorbate '{sorbate}' is not in the training data; give direction='rising' or 'falling'")
        notes.append(f"edge direction taken from the training data for {sorbate}: {direction}")
    pair_dir = f"{mineral} | {sorbate}|{direction}"
    n_units = meta["pairs"].get(pair_dir, 0)
    if n_units == 0:
        notes.append("this mineral-sorbate pair is NOT in the training data: class-level prediction (expect ~1.5-1.8 pH "
                     "edge error, E16)")
    elif n_units == 1:
        notes.append("this pair was measured by only ONE paper (or lineage cluster) in the training data")
    if mineral not in meta["minerals"]:
        notes.append(f"mineral '{mineral}' is not in the training data")
    if sorbate not in meta["sorbates"]:
        notes.append(f"sorbate '{sorbate}' is not in the training data")
    ls, lt, li = np.log10(conditions["solids_g_L"]), np.log10(conditions["total_sorbate_mol_L"]), np.log10(conditions["ionic_strength"])
    for name, v in (("log10_solids", ls), ("log10_total", lt), ("log10_I", li)):
        lo, hi = meta["ranges"][name]
        if not lo <= v <= hi:
            notes.append(f"{name} = {v:.2f} is outside the central 96% of the training data [{lo:.2f}, {hi:.2f}]: extrapolation")
    ecfg = load_exp_config()
    icls = assign_class(sorbate, ecfg["e8"]["classes"])
    row = pd.DataFrame([{
        "curve_id": "query", "mineral": mineral, "sorbate": sorbate, "shape": direction,
        "pair": f"{mineral} | {sorbate}", "pair_dir": pair_dir, "class_dir": f"{sclass or 'unassigned'}|{direction}",
        "unit": "__new_paper__", "falling": float(direction == "falling"),
        "log10_solids": ls, "log10_total": lt, "log10L": lt - ls, "log10_I": li,
        "cosolute": float(conditions.get("cosolute", 0)), "co2": float(conditions.get("co2", 0)),
        "logI_outer": li * (icls == "outer_sphere_prone"), "logI_oxy": li * (icls == "oxyanion"),
        "solids_g_L": conditions["solids_g_L"], "total_sorbate_mol_L": conditions["total_sorbate_mol_L"]}])
    p = m.predict(row, np.random.default_rng(seed))
    if p.empty:
        raise PredictorError("prediction failed: a covariate the model needs is missing")
    r = p.iloc[0]
    grid = np.round(np.arange(2.0, 11.0001, 0.25), 10) if grid is None else np.asarray(grid, float)
    rng = np.random.default_rng(seed)
    n = 400
    za = rng.standard_normal(n)
    zb = m.rho * za + np.sqrt(max(1 - m.rho ** 2, 0)) * rng.standard_normal(n)
    A = r["pred_a_c"] + r["sd_a"] * za
    Bd = r["pred_b"] + r["sd_b"] * zb
    sign = 1 if direction == "rising" else -1
    keep = Bd * sign > 0
    A, Bd = A[keep], Bd[keep]
    logk = A[:, None] + Bd[:, None] * (grid[None, :] - r["pH_c"])
    f = 1 / (1 + 10 ** -logk)
    g = np.log(10) * Bd[:, None] * f * (1 - f)
    lk0 = r["pred_a_c"] + r["pred_b"] * (grid - r["pH_c"])
    f0 = 1 / (1 + 10 ** -lk0)
    return {"grid": grid, "slope": np.log(10) * r["pred_b"] * f0 * (1 - f0),
            "lower": np.percentile(g, 2.5, axis=0), "upper": np.percentile(g, 97.5, axis=0),
            "fraction": f0, "fraction_lower": np.percentile(f, 2.5, axis=0),
            "fraction_upper": np.percentile(f, 97.5, axis=0),
            "edge_pH": float(r["pred_edge"]), "edge_lo": float(r["edge_lo"]), "edge_hi": float(r["edge_hi"]),
            "pair_units_in_training": int(n_units), "direction": direction, "notes": notes, "status": "exploratory"}
