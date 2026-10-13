"""E5 -- edge-coverage artefact (protocol section 5, E5). EXPLORATORY; development papers only.

1. Truncation experiment. Well-measured curves (pH span >= 6, line R2 >= 0.9, >= 12 points) are cut
   to windows of 2, 3, 4, 5 pH units at seeded random positions (kept if >= 3 mid-range points).
   For each truncation: the log10 K line edge (and the logistic p50) is compared with the full-curve
   edge. Predictors of the error: number of mid-range points, pH span of mid-range points, distance
   from the edge to the nearest measured point (extrapolation), SE of the slope b.
2. Error model: log10 |edge error| ~ log10 SE(b) + extrapolation distance + log10 n_mid, fitted on
   half of the well-measured curves and VALIDATED on the other half (split by curve).
3. Revised QC rule: keep a curve if its predicted edge error <= 0.5 pH. Report the share of Stage 1
   census-set curves (development papers) retained and the validated median error on retained
   truncations. Decision (pre-declared): rule retains >= 70% of census-set curves AND median truncation
   error on retained validation curves <= 0.5 pH. Changing the Stage 1 rule itself is decision D3.
4. Similar-vs-different pairs on a common window: refit both curves of a cross-paper pair on their
   shared pH window and check whether the association between |edge difference| and pH-span
   difference disappears.
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from phslope import fit_edge
from phslope.common import load_config
from phslope.experiments.data import build
from phslope.experiments.kd import line_fit
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E5")


def truncations(curves, obs, cfg, seed):
    sel = cfg["select"]
    rng = np.random.default_rng(seed)
    fit_cfg = load_config()["fit"]
    good = curves[(curves["pH_span"] >= sel["min_span"]) & (curves["r2"] >= sel["min_r2"])
                  & (curves["n_points"] >= sel["min_points"]) & curves["line_dir_ok"]]
    by = {k: g for k, g in obs.groupby("curve_id")}
    rows = []
    for r in good.itertuples():
        g = by[r.curve_id]
        full_edge = r.pH_native
        try:
            full_logit = fit_edge.fit_logistic(g["pH"], g["response"], fit_cfg, n_starts=8, seed=0)["p50"]
        except fit_edge.EdgeFitError:
            full_logit = np.nan
        for wdt in cfg["windows"]:
            for k in range(cfg["draws_per_window"]):
                lo = rng.uniform(g["pH"].min(), max(g["pH"].min(), g["pH"].max() - wdt))
                s = g[(g["pH"] >= lo) & (g["pH"] <= lo + wdt)]
                m = s[s["mid"] & s["log10K"].notna()]
                if len(m) < cfg["min_mid_points"] or np.ptp(m["pH"]) < 0.3:
                    continue
                f = line_fit(m["pH"], m["log10K"])
                if f["b"] * np.sign(r.b) <= 0:
                    rows.append({"curve_id": r.curve_id, "window": wdt, "draw": k, "edge": np.nan,
                                 "sign_flip": True})
                    continue
                e = -f["a"] / f["b"]
                try:
                    lp = fit_edge.fit_logistic(s["pH"], s["response"], fit_cfg, n_starts=4, seed=k)["p50"] \
                        if s["pH"].nunique() >= 4 else np.nan
                except fit_edge.EdgeFitError:
                    lp = np.nan
                pts = s["pH"].to_numpy()
                rows.append({"curve_id": r.curve_id, "window": wdt, "draw": k, "edge": e, "sign_flip": False,
                             "edge_error": abs(e - full_edge), "logistic_error": abs(lp - full_logit),
                             "n_mid": len(m), "mid_span": float(np.ptp(m["pH"])),
                             "extrap_dist": float(np.min(np.abs(pts - e))) if not (pts.min() <= e <= pts.max())
                             else 0.0,
                             "gap_at_edge": float(np.min(np.abs(pts - e))),
                             "se_b": float(np.sqrt(f["cov"][1, 1])), "abs_b": abs(f["b"])})
    return pd.DataFrame(rows), good


def error_model_features(d):
    return np.column_stack([np.ones(len(d)), np.log10(np.clip(d["se_b"] / d["abs_b"], 1e-4, None)),
                            d["extrap_dist"], np.log10(d["n_mid"])])


def fit_error_model(d):
    y = np.log10(np.clip(d["edge_error"], 1e-3, None))
    X = error_model_features(d)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid_sd = float(np.std(y - X @ beta))
    return beta, resid_sd


def predict_error(beta, d):
    return 10 ** (error_model_features(d) @ beta)


def curve_features(curves, obs):
    """Error-model features for each development curve's own (full) line fit."""
    rows = []
    by = {k: g for k, g in obs.groupby("curve_id")}
    for r in curves.dropna(subset=["a", "b"]).itertuples():
        g = by.get(r.curve_id)
        if g is None:
            continue
        pts = g["pH"].to_numpy()
        e = r.pH_native
        rows.append({"curve_id": r.curve_id, "se_b": np.sqrt(r.var_b), "abs_b": abs(r.b), "n_mid": r.n_mid,
                     "extrap_dist": float(np.min(np.abs(pts - e))) if not (pts.min() <= e <= pts.max()) else 0.0})
    return pd.DataFrame(rows)


def common_window_pairs(curves, obs, min_overlap=2.0):
    c = curves[curves["in_core_library"].astype(bool) & curves["shape"].isin(["rising", "falling"])].copy()
    c["grp"] = c["mineral"] + "|" + c["sorbate"] + "|" + c["shape"]
    by = {k: g for k, g in obs[obs["mid"] & obs["log10K"].notna()].groupby("curve_id")}
    rows = []
    for _, g in c.groupby("grp"):
        idx = g.index.to_list()
        for i in range(len(idx)):
            for j in range(i + 1, len(idx)):
                a, b = g.loc[idx[i]], g.loc[idx[j]]
                if a["reference"] == b["reference"]:
                    continue
                lo, hi = max(a["pH_min"], b["pH_min"]), min(a["pH_max"], b["pH_max"])
                row = {"d_edge_native": abs(a["logistic_p50"] - b["logistic_p50"]),
                       "d_span": abs(a["pH_span"] - b["pH_span"])}
                if hi - lo >= min_overlap and a["curve_id"] in by and b["curve_id"] in by:
                    ea = by[a["curve_id"]]; eb = by[b["curve_id"]]
                    ea, eb = ea[(ea["pH"] >= lo) & (ea["pH"] <= hi)], eb[(eb["pH"] >= lo) & (eb["pH"] <= hi)]
                    if len(ea) >= 3 and len(eb) >= 3:
                        fa, fb = line_fit(ea["pH"], ea["log10K"]), line_fit(eb["pH"], eb["log10K"])
                        if fa["b"] * fb["b"] > 0:
                            row["d_edge_common"] = abs(-fa["a"] / fa["b"] + fb["a"] / fb["b"])
                rows.append(row)
    return pd.DataFrame(rows)


def run(seed=None):
    ecfg = load_exp_config()
    cfg = ecfg["e5"]
    seed = ecfg["seed"] if seed is None else seed
    curves, obs = build(purpose="E5")
    stamp = exp_stamp(extra={"experiment": "E5"})
    write_run_info(OUT, stamp)
    T, good = truncations(curves, obs, cfg, seed)
    T.to_csv(os.path.join(OUT, "truncations.csv"), index=False)
    ok = T.dropna(subset=["edge_error"])
    rng = np.random.default_rng(seed)
    ids = good["curve_id"].to_numpy()
    rng.shuffle(ids)
    half = set(ids[: len(ids) // 2])
    tr, va = ok[ok["curve_id"].isin(half)], ok[~ok["curve_id"].isin(half)]
    beta, sd = fit_error_model(tr)
    va = va.assign(pred_error=predict_error(beta, va))
    va_kept = va[va["pred_error"] <= 0.5]
    val_median = float(va_kept["edge_error"].median()) if len(va_kept) else np.nan
    rank_r = spearmanr(va["pred_error"], va["edge_error"]).correlation
    by_w = ok.groupby("window").agg(n=("edge_error", "size"), median_line_error=("edge_error", "median"),
                                    median_logistic_error=("logistic_error", "median"),
                                    share_within_0_5=("edge_error", lambda s: (s <= 0.5).mean())).reset_index()
    flips = T.groupby("window")["sign_flip"].mean().rename("share_slope_sign_flipped").reset_index()
    by_w = by_w.merge(flips, on="window")

    census = curves[curves["in_census_set"].astype(bool) & curves["shape"].isin(["rising", "falling"])]
    feats = curve_features(census, obs)
    feats["pred_error"] = predict_error(beta, feats)
    retained = float((feats["pred_error"] <= 0.5).sum() / len(census)) if len(census) else np.nan
    stage1_kept = float(census["in_core_library"].mean())
    dec = cfg["decision"]
    verdict = "MEETS RULE" if (retained >= dec["retain_min"] and val_median <= dec["median_error_max"]) else "DOES NOT MEET RULE"

    P = common_window_pairs(curves, obs)
    sp_native = spearmanr(P["d_edge_native"], P["d_span"], nan_policy="omit").correlation
    Pc = P.dropna(subset=["d_edge_common"])
    sp_common = spearmanr(Pc["d_edge_common"], Pc["d_span"]).correlation if len(Pc) > 10 else np.nan
    sp_native_same = spearmanr(Pc["d_edge_native"], Pc["d_span"]).correlation if len(Pc) > 10 else np.nan

    by_w.to_csv(os.path.join(OUT, "error_by_window.csv"), index=False)
    feats.to_csv(os.path.join(OUT, "census_predicted_edge_error.csv"), index=False)
    coef = pd.DataFrame({"term": ["intercept", "log10(SE(b)/|b|)", "extrapolation distance (pH)", "log10 n_mid"],
                         "coefficient": beta})
    coef.to_csv(os.path.join(OUT, "error_model.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E5 Edge-coverage artefact and a slope-based QC rule", "",
        "**Plain English.** We took well-measured curves, pretended only part of each had been measured, and "
        "checked how wrong the edge estimate became. The error is predicted well by how precisely the steepness "
        "of the curve is determined and how far the edge is from the nearest measured point. A quality rule "
        f"built on that keeps {retained:.0%} of the Stage 1 census curves (the old rule kept {stage1_kept:.0%}), "
        f"with a validated median edge error of {val_median:.2f} pH on the kept test curves. Verdict on the "
        f"pre-declared rule: **{verdict}**. Changing the Stage 1 rule is a decision for Samuel and Dr. Black "
        "(D3); the Stage 1 failure stays recorded as a failure.", "",
        f"> EXPLORATORY. Development papers only. Locked set hash `{stamp['locked_set_hash']}`. Commit "
        f"`{stamp['git_commit']}`.", "",
        f"## Truncation experiment ({len(good)} well-measured curves; {len(ok)} usable truncations)", "",
        md_table(by_w), "",
        "## Error model (fitted on half the curves)", "", md_table(coef), "",
        f"Residual SD {sd:.2f} (log10 units). Validation on the other half: rank correlation between predicted and "
        f"actual edge error {rank_r:.2f}; truncations kept by the rule (predicted error <= 0.5 pH): "
        f"{len(va_kept)} of {len(va)}, median actual error {val_median:.2f} pH.", "",
        "## Census set under the slope-based rule", "",
        f"- Census-set rising/falling curves (development papers): {len(census)}",
        f"- Kept by the Stage 1 rule (core library): {stage1_kept:.1%}",
        f"- Kept by the E5 rule (predicted edge error <= 0.5 pH): {retained:.1%}", "",
        "## Similar vs different curve pairs on a common window", "",
        f"Cross-paper pairs: {len(P)}; with a shared window of >= 2 pH and usable lines on it: {len(Pc)}. "
        f"Spearman |edge difference| vs |pH-span difference|: native edges {sp_native:.2f} (all pairs), "
        f"{sp_native_same:.2f} (same pairs as below); common-window edges {sp_common:.2f}. A drop towards zero "
        "means the span association was partly a coverage artefact.", "",
        "Files: `truncations.csv`, `error_by_window.csv`, `error_model.csv`, `census_predicted_edge_error.csv`.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E5", verdict, f"retained {retained:.1%}; validated median error {val_median:.2f}", stamp)
    record_adjustment("E5 slope-based QC rule (edge error predicted from SE(b) and extrapolation)",
                      f"{verdict} (adoption needs decision D3)",
                      f"retains {retained:.1%} of census curves vs Stage 1 {stage1_kept:.1%}; validated median error "
                      f"{val_median:.2f} pH; rank correlation {rank_r:.2f}")
    print(f"E5 {verdict}: retained {retained:.3f}, validated median {val_median:.3f}")
    return T


if __name__ == "__main__":
    run()
