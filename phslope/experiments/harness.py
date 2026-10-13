"""harness.py -- the single held-out evaluation loop (protocol E0.3).

Leave out whole UNITS: papers by default, or lineage clusters (E3) / lab clusters (E4) when a
unit column is given. Baselines B0-B5 follow the pooling follow-up (pool_experiments.py Part 4):

  B0 all_other   mean over other units (same mineral, sorbate, direction) of each unit's mean edge
  B1 nearest1    edge of the single other-unit curve with the closest conditions
  B2 nearest3    mean edge of the three closest-conditions other-unit curves
  B3 matched_fb  mean edge of other-unit curves matched on conditions (solids within 0.5 decade,
                 total sorbate within 1 decade, same CO2 flag, same co-solute flag); else B0
  B4 class_mean  mean edge of other-unit curves of the same sorbate class and direction
  B5 global_mean mean edge of all other-unit curves
Closeness = sum over log10 solids, log10 total, log10 I of |difference| / SD (missing -> 1.5),
+1 if the CO2 flag differs, +1 if the co-solute flag differs, +0.5 if the background anion differs.

Metrics per held-out curve, then summarised (median, IQR, RMSE, share within 0.5 / 1 pH, coverage),
with 95% intervals from resampling UNITS; paired differences against baselines; noise-ceiling
fraction = (median B5 error - median model error) / (median B5 error - median B0 error).
"""
import numpy as np
import pandas as pd

BASELINES = ["B0_all_other", "B1_nearest1", "B2_nearest3", "B3_matched_fb", "B4_class_mean", "B5_global_mean"]
FEATS = ["log10_solids", "log10_total", "log10_I"]


def background(sig):
    s = str(sig)
    for k, v in (("N(+5)", "nitrate"), ("Cl(+7)", "perchlorate"), ("Cl(-1)", "chloride"), ("S(+6)", "sulfate")):
        if k in s:
            return v
    return "other"


def prepare(curves, edge_col):
    c = curves.copy()
    c["edge"] = c[edge_col]
    c["grp"] = c["mineral"] + "|" + c["sorbate"] + "|" + c["shape"]
    c["background"] = c["electrolyte_sig"].map(background)
    return c


def baseline_predictions(c, unit_col="reference", hcfg=None, sd=None, also_differ=()):
    """One row per curve with the six baseline edge predictions (NaN where undefined).
    also_differ: extra columns (e.g. a lab id) on which a usable other curve must ALSO differ."""
    hcfg = hcfg or {"match_solids_decades": 0.5, "match_total_decades": 1.0}
    sd = sd or {v: c[v].std() for v in FEATS}
    rows = []
    by_grp = {g: d for g, d in c.groupby("grp")}
    for i, r in c.iterrows():
        keep_all = c[unit_col] != r[unit_col]
        for col in also_differ:
            keep_all &= c[col] != r[col]
        other_all = c[keep_all]
        o = by_grp[r["grp"]]
        keep = o[unit_col] != r[unit_col]
        for col in also_differ:
            keep &= o[col] != r[col]
        o = o[keep]
        row = {"curve_id": r["curve_id"], "n_other_units": int(o[unit_col].nunique())}
        cls = other_all[(other_all["sorbate_class"] == r["sorbate_class"]) & (other_all["shape"] == r["shape"])]
        row["B4_class_mean"] = cls["edge"].mean() if len(cls) else np.nan
        row["B5_global_mean"] = other_all["edge"].mean()
        if o.empty:
            row.update({b: np.nan for b in BASELINES[:4]})
            row["n_matched"] = 0
            rows.append(row)
            continue
        row["B0_all_other"] = o.groupby(unit_col)["edge"].mean().mean()
        dist = np.zeros(len(o))
        for v in FEATS:
            dist += ((o[v] - r[v]).abs() / sd[v]).fillna(1.5).to_numpy()
        dist += 1.0 * (o["co2"] != r["co2"]).to_numpy() + 1.0 * (o["cosolute"] != r["cosolute"]).to_numpy() \
            + 0.5 * (o["background"] != r["background"]).to_numpy()
        order = np.argsort(dist, kind="stable")
        e = o["edge"].to_numpy()
        row["B1_nearest1"] = e[order[0]]
        row["B2_nearest3"] = e[order[:3]].mean()
        m = ((o["log10_solids"] - r["log10_solids"]).abs() < hcfg["match_solids_decades"]).fillna(False) \
            & ((o["log10_total"] - r["log10_total"]).abs() < hcfg["match_total_decades"]).fillna(False) \
            & (o["co2"] == r["co2"]) & (o["cosolute"] == r["cosolute"])
        row["n_matched"] = int(m.sum())
        row["B3_matched"] = o.loc[m, "edge"].mean() if m.sum() else np.nan
        row["B3_matched_fb"] = row["B3_matched"] if m.sum() else row["B0_all_other"]
        rows.append(row)
    return pd.DataFrame(rows)


def long_errors(c, preds, models, unit_col="reference"):
    """Long table: curve_id, unit, model, pred_edge, edge_error (+ interval columns if given)."""
    base = c[["curve_id", unit_col, "edge", "pair", "shape"]].rename(columns={unit_col: "unit"})
    out = []
    for m in models:
        if m not in preds:
            continue
        d = base.merge(preds[["curve_id", m]].rename(columns={m: "pred_edge"}), on="curve_id")
        lo, hi = f"{m}__lo", f"{m}__hi"
        if lo in preds:
            d = d.merge(preds[["curve_id", lo, hi]].rename(columns={lo: "edge_lo", hi: "edge_hi"}), on="curve_id")
        d["model"] = m
        out.append(d)
    L = pd.concat(out, ignore_index=True)
    L["edge_error"] = (L["pred_edge"] - L["edge"]).abs()
    if "edge_lo" in L:
        L["covered"] = (L["edge"] >= L["edge_lo"]) & (L["edge"] <= L["edge_hi"])
    return L.dropna(subset=["edge_error"])


def _boot_median(err, units, B, rng):
    u = np.unique(units)
    idx = {k: np.where(units == k)[0] for k in u}
    meds = []
    for _ in range(B):
        pick = np.concatenate([idx[k] for k in rng.choice(u, len(u))])
        meds.append(np.median(err[pick]))
    return np.percentile(meds, [2.5, 97.5])


def summarize(L, B=500, seed=0, metric="edge_error"):
    rng = np.random.default_rng(seed)
    rows = []
    for m, d in L.groupby("model", sort=False):
        e = d[metric].to_numpy()
        lo, hi = _boot_median(e, d["unit"].to_numpy(), B, rng) if B else (np.nan, np.nan)
        rows.append({"model": m, "n": len(d), "n_units": d["unit"].nunique(), "median": np.median(e), "median_lo": lo,
                     "median_hi": hi, "q25": np.percentile(e, 25), "q75": np.percentile(e, 75),
                     "rmse": float(np.sqrt(np.mean(e ** 2))) if metric == "edge_error" else np.nan,
                     "within_0_5": float(np.mean(e < 0.5)), "within_1": float(np.mean(e < 1.0)),
                     "coverage": float(d["covered"].mean()) if "covered" in d and d["covered"].notna().any() else np.nan})
    return pd.DataFrame(rows)


def paired(L, model, baselines, B=500, seed=0, metric="edge_error"):
    """Median paired difference (model - baseline) over curves both predicted; 95% interval over units."""
    rng = np.random.default_rng(seed)
    a = L[L["model"] == model].set_index("curve_id")
    rows = []
    for b in baselines:
        bb = L[L["model"] == b].set_index("curve_id")
        common = a.index.intersection(bb.index)
        if not len(common):
            continue
        diff = (a.loc[common, metric] - bb.loc[common, metric]).to_numpy()
        units = a.loc[common, "unit"].to_numpy()
        lo, hi = _boot_median(diff, units, B, rng) if B else (np.nan, np.nan)
        rows.append({"model": model, "baseline": b, "n_common": len(common), "median_diff": np.median(diff),
                     "diff_lo": lo, "diff_hi": hi, "model_median": np.median(a.loc[common, metric]),
                     "baseline_median": np.median(bb.loc[common, metric])})
    return pd.DataFrame(rows)


def noise_ceiling(L, model, B=500, seed=0):
    """(median B5 - median model) / (median B5 - median B0) on curves all three predicted."""
    rng = np.random.default_rng(seed)
    w = L.pivot_table(index=["curve_id", "unit"], columns="model", values="edge_error").dropna(
        subset=[model, "B0_all_other", "B5_global_mean"]).reset_index()
    if w.empty:
        return {"fraction": np.nan, "lo": np.nan, "hi": np.nan, "n": 0}

    def frac(d):
        den = d["B5_global_mean"].median() - d["B0_all_other"].median()
        return (d["B5_global_mean"].median() - d[model].median()) / den if den else np.nan
    units = w["unit"].unique()
    idx = {u: w.index[w["unit"] == u] for u in units}
    boots = [frac(w.loc[np.concatenate([idx[u] for u in rng.choice(units, len(units))])]) for _ in range(B)]
    return {"fraction": frac(w), "lo": np.nanpercentile(boots, 2.5), "hi": np.nanpercentile(boots, 97.5), "n": len(w)}


def benchmark_table(c, preds):
    """Reproduces the follow-up Part 4 summary (all curves in groups with >= 2 papers)."""
    L = long_errors(c, preds, ["B0_all_other", "B1_nearest1", "B2_nearest3", "B3_matched_fb"])
    out = {m: float(d["edge_error"].median()) for m, d in L.groupby("model")}
    out["n_curves"] = int(L[L.model == "B0_all_other"].shape[0])
    mm = preds.dropna(subset=["B3_matched"])
    sub = c.set_index("curve_id").loc[mm["curve_id"], "edge"].to_numpy()
    out["matched_subset_n"] = len(mm)
    out["matched_subset_plain"] = float(np.median(np.abs(mm["B0_all_other"].to_numpy() - sub)))
    out["matched_subset_matched"] = float(np.median(np.abs(mm["B3_matched"].to_numpy() - sub)))
    return out


def benchmark_population(curves):
    """Core single-edge curves in mineral-sorbate-direction groups with >= 2 papers, edge = logistic p50."""
    c = prepare(curves[curves["in_core_library"].astype(bool) & curves["shape"].isin(["rising", "falling"])],
                "logistic_p50")
    return c[c.groupby("grp")["reference"].transform("nunique") >= 2].reset_index(drop=True)
