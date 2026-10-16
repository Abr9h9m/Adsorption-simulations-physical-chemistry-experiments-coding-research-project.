"""E1 -- log10 K mixed model (protocol section 5, E1). EXPLORATORY; development papers only.

Formulation (TWO-STEP, as the protocol allows when the one-step fit is impractical): the one-step
model with crossed random slopes for pair and paper on ~10,000 points is not available in the
installed tools at usable speed, so:

  step 1  per curve, OLS line of log10 K on pH over mid-range points (kd.py, data.py): a, b, R2
  step 2  for each training fold, with pH_c = the pair's median native edge in the TRAINING data
          (fallback: sorbate class x direction median, then direction median):
            level  a_c = a + b * pH_c   ~ 1 + falling + covariates
                                          + (1 | sorbate_class:direction) + (1 | pair:direction) + (1 | unit)
            slope  b                    ~ 1 + falling
                                          + (1 | sorbate_class:direction) + (1 | pair:direction) + (1 | unit)
          REML (phslope/reml.py); the curve effect is the residual. Pair effects shrink towards the
          sorbate class (partial pooling); a pair with one paper gets only class + covariates.
          Covariates (level): log10 solids x direction, loading hinge x direction (breakpoint chosen
          inside the training fold by grid search), log10 total sorbate, co-solute, CO2, log10 I.

Prediction for a held-out unit (lineage cluster from E3, i.e. a paper or a group of papers that
share copied data): fixed part + class BLUP + pair BLUP (if the pair is in training); the paper
effect is unknown, so its variance enters the predictive variance together with the residual and
the BLUP prediction-error variances. 400 correlated draws of (a_c, b) give the native edge
(log10 K = 0), the solids-normalised edge (log10 K = log10 S, Kd = 1 L/g) and 90% intervals.
"""
import os

import numpy as np
import pandas as pd

from phslope.common import solids_term
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)
from phslope.reml import fit_reml, predict_effects

OUT = os.path.join(EXP_DIR, "E1")
LEVEL_COVS = ["solids_r", "solids_f", "hinge_r", "hinge_f", "log10_total", "cosolute", "co2", "log10_I"]
FACTORS = {"class_dir": "class_dir", "pair_dir": "pair_dir", "unit": "unit"}


def main_set(curves, cfg):
    """Rising/falling curves with solids and total sorbate whose log10 K line is usable."""
    base = curves[curves["shape"].isin(["rising", "falling"]) & (curves["solids_g_L"] > 0)
                  & (curves["total_sorbate_mol_L"] > 0)].copy()
    use = base["line_dir_ok"] & (base["r2"] >= cfg["line_r2_min"]) & base["line_in_range"]
    return base, base[use].copy()


def attach_units(curves):
    lin = pd.read_csv(os.path.join(EXP_DIR, "E3", "lineage_clusters.csv"))
    c = curves.merge(lin[["reference", "lineage_cluster"]], on="reference", how="left")
    c["unit"] = c["lineage_cluster"].fillna(c["reference"])
    c["falling"] = (c["shape"] == "falling").astype(float)
    c["class_dir"] = c["sorbate_class"].fillna("unassigned") + "|" + c["shape"]
    c["pair_dir"] = c["pair"] + "|" + c["shape"]
    return c


def reference_pH(train, test):
    pair = train.groupby("pair_dir")["pH_native"].median()
    cls = train.groupby("class_dir")["pH_native"].median()
    dirm = train.groupby("shape")["pH_native"].median()
    return test["pair_dir"].map(pair).fillna(test["class_dir"].map(cls)).fillna(test["shape"].map(dirm))


def add_covariates(d, bp):
    d = d.copy()
    r, f = (d["shape"] == "rising").astype(float), (d["shape"] == "falling").astype(float)
    hinge = np.maximum(d["log10L"] - bp, 0.0)
    d["solids_r"], d["solids_f"] = d["log10_solids"] * r, d["log10_solids"] * f
    d["hinge_r"], d["hinge_f"] = hinge * r, hinge * f
    return d


def choose_breakpoint(train, grid):
    """Breakpoint with the smallest residual SS of pair-centred level on solids and hinge, by direction."""
    best = (np.inf, grid[0])
    for bp in grid:
        d = add_covariates(train, bp).dropna(subset=["a_c", "log10_solids", "log10L"])
        cols = ["solids_r", "solids_f", "hinge_r", "hinge_f"]
        y = d["a_c"] - d.groupby("pair_dir")["a_c"].transform("mean")
        X = d[cols] - d.groupby("pair_dir")[cols].transform("mean")
        X = X.loc[:, X.abs().sum() > 0]
        beta, *_ = np.linalg.lstsq(X.to_numpy(), y.to_numpy(), rcond=None)
        rss = float(((y.to_numpy() - X.to_numpy() @ beta) ** 2).sum())
        if rss < best[0]:
            best = (rss, bp)
    return best[1]


class E1Model:
    def __init__(self, cfg, covariates=True, extra_covs=(), within_between=()):
        """extra_covs: additional level covariates (columns of the curve table), e.g. for E7 / E9.
        within_between: covariates for which the pair mean (training data) is added as a separate term
        (Mundlak / within-between split), so the covariate's own coefficient is identified only by
        differences WITHIN a pair. Added after E23 showed between-pair confounding of the solids term."""
        self.cfg, self.covariates, self.extra_covs = cfg, covariates, list(extra_covs)
        self.within_between = list(within_between)

    def fit(self, train):
        t = train.copy()
        t["pH_c"] = reference_pH(t, t)
        t["a_c"] = t["a"] + t["b"] * t["pH_c"]
        self.bp = choose_breakpoint(t, self.cfg["hinge_grid"]) if self.covariates else np.nan
        t = add_covariates(t, self.bp) if self.covariates else t
        self.pair_means = {v: t.groupby("pair_dir")[v].mean() for v in self.within_between}
        for v in self.within_between:
            t[v + "_pm"] = t["pair_dir"].map(self.pair_means[v])
        self.level_fixed = ["falling"] + (LEVEL_COVS if self.covariates else []) + self.extra_covs             + [v + "_pm" for v in self.within_between]
        self.level_fixed = [c for c in self.level_fixed if t[c].nunique(dropna=True) > 1]
        t = t.dropna(subset=self.level_fixed + ["a_c", "b"])
        self.train = t
        self.fa = fit_reml(t, "a_c", FACTORS, self.level_fixed)
        self.fb = fit_reml(t, "b", FACTORS, ["falling"])
        self.ea, self.cov_a = predict_effects(t, "a_c", FACTORS, self.fa, self.level_fixed)
        self.eb, self.cov_b = predict_effects(t, "b", FACTORS, self.fb, ["falling"])
        # residual correlation of level and slope across training curves (paper + curve parts)
        ra = t["a_c"] - self._mean(t, "a")[0]
        rb = t["b"] - self._mean(t, "b")[0]
        self.rho = float(np.corrcoef(ra, rb)[0, 1]) if len(t) > 3 else 0.0
        return self

    def _mean(self, d, which):
        fit, eff, fixed = (self.fa, self.ea, self.level_fixed) if which == "a" else (self.fb, self.eb, ["falling"])
        X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in fixed])
        mean = X @ fit["beta"]
        var = np.zeros(len(d))
        comps = fit["components"]
        for name, col in (("class_dir", "class_dir"), ("pair_dir", "pair_dir")):
            e = eff[name].set_index("level")
            seen = d[col].isin(e.index).to_numpy()
            mean = mean + np.where(seen, d[col].map(e["blup"]).fillna(0).to_numpy(), 0.0)
            var = var + np.where(seen, d[col].map(e["pev"]).fillna(0).to_numpy(), comps[name])
        var = var + comps["unit"] + comps["residual"]
        return mean, var

    def predict(self, test, rng):
        d = test.copy()
        d["pH_c"] = reference_pH(self.train, d)
        d = add_covariates(d, self.bp) if self.covariates else d
        for v in self.within_between:                      # unseen pair: its own value is the best guess
            d[v + "_pm"] = d["pair_dir"].map(self.pair_means[v]).fillna(d[v])
        ok = d[self.level_fixed].notna().all(axis=1)
        d = d[ok].copy()
        ma, va = self._mean(d, "a")
        mb, vb = self._mean(d, "b")
        n = self.cfg["prediction_draws"]
        za = rng.standard_normal((len(d), n))
        zb = self.rho * za + np.sqrt(max(1 - self.rho ** 2, 0)) * rng.standard_normal((len(d), n))
        A = ma[:, None] + np.sqrt(va)[:, None] * za
        Bd = mb[:, None] + np.sqrt(vb)[:, None] * zb
        sign = np.where(d["shape"] == "rising", 1, -1)[:, None]
        Bd = np.where(Bd * sign > 0, Bd, np.nan)                         # draws with the wrong slope sign
        pc = d["pH_c"].to_numpy()[:, None]
        edge_draws = pc - A / Bd
        s1_draws = pc + (solids_term(d["log10_solids"]).to_numpy()[:, None] - A) / Bd
        d["pred_edge"] = d["pH_c"] - ma / mb
        d["pred_edge_S1"] = d["pH_c"] + (solids_term(d["log10_solids"]) - ma) / mb
        q = 0.05                                                          # 90% intervals
        with np.errstate(all="ignore"):
            d["edge_lo"], d["edge_hi"] = np.nanquantile(edge_draws, q, axis=1), np.nanquantile(edge_draws, 1 - q, axis=1)
            d["edge_S1_lo"], d["edge_S1_hi"] = np.nanquantile(s1_draws, q, axis=1), np.nanquantile(s1_draws, 1 - q, axis=1)
        d["pred_a_c"], d["pred_b"], d["sd_a"], d["sd_b"] = ma, mb, np.sqrt(va), np.sqrt(vb)
        return d


def logk_metrics(pred, obs, min_pH=None):
    """RMSE and 90% coverage of log10 K at the held-out curve's mid-range points (optionally pH > min_pH)."""
    rows = []
    o = obs[obs["mid"] & obs["log10K"].notna()]
    if min_pH is not None:
        o = o[o["pH"] > min_pH]
    by = {k: g for k, g in o.groupby("curve_id")}
    for r in pred.itertuples():
        g = by.get(r.curve_id)
        if g is None:
            continue
        yhat = r.pred_a_c + r.pred_b * (g["pH"].to_numpy() - r.pH_c)
        sd = np.sqrt(r.sd_a ** 2 + (r.sd_b * (g["pH"].to_numpy() - r.pH_c)) ** 2)
        y = g["log10K"].to_numpy()
        rows.append({"curve_id": r.curve_id, "logK_rmse": float(np.sqrt(np.mean((yhat - y) ** 2))),
                     "logK_coverage": float(np.mean(np.abs(y - yhat) <= 1.645 * sd))})
    return pd.DataFrame(rows)


def baseline_logk(c, obs):
    """logK_rmse of baselines B0 (line averaged over other units' mean lines) and B3 (matched curves'
    mean line, else B0). Same population and units as the edge baselines."""
    o = obs[obs["mid"] & obs["log10K"].notna()]
    by = {k: g for k, g in o.groupby("curve_id")}
    sd = {v: c[v].std() for v in H.FEATS}
    rows = []
    for _, r in c.iterrows():
        oth = c[(c["grp"] == r["grp"]) & (c["unit"] != r["unit"])]
        g = by.get(r["curve_id"])
        if oth.empty or g is None:
            continue
        um = oth.groupby("unit")[["a", "b"]].mean()
        a0, b0 = um["a"].mean(), um["b"].mean()
        m = ((oth["log10_solids"] - r["log10_solids"]).abs() < 0.5).fillna(False) \
            & ((oth["log10_total"] - r["log10_total"]).abs() < 1.0).fillna(False) \
            & (oth["co2"] == r["co2"]) & (oth["cosolute"] == r["cosolute"])
        a3, b3 = (oth.loc[m, "a"].mean(), oth.loc[m, "b"].mean()) if m.sum() else (a0, b0)
        pH, y = g["pH"].to_numpy(), g["log10K"].to_numpy()
        for name, (aa, bb) in (("B0_all_other", (a0, b0)), ("B3_matched_fb", (a3, b3))):
            rows.append({"curve_id": r["curve_id"], "model": name,
                         "logK_rmse": float(np.sqrt(np.mean((aa + bb * pH - y) ** 2)))})
    return pd.DataFrame(rows)


def cross_validate(c, obs, cfg, covariates=True, seed=0, extra_covs=(), within_between=()):
    rng = np.random.default_rng(seed)
    preds = []
    for u in c["unit"].unique():
        test = c[c["unit"] == u]
        train = c[c["unit"] != u]
        m = E1Model(cfg, covariates, extra_covs, within_between).fit(train)
        p = m.predict(test, rng)
        p["bp"] = m.bp
        preds.append(p)
    P = pd.concat(preds, ignore_index=True)
    return P.merge(logk_metrics(P, obs), on="curve_id", how="left")


def run(seed=None, reuse=False):
    """reuse=True loads the saved held-out predictions (cv_with_covariates.csv, cv_without_covariates.csv)
    instead of re-running the cross-validation."""
    ecfg = load_exp_config()
    cfg = ecfg["e1"]
    seed = ecfg["seed"] if seed is None else seed
    curves, obs = build(purpose="E1")
    stamp = exp_stamp(extra={"experiment": "E1", "formulation": "two-step REML with BLUPs"})
    write_run_info(OUT, stamp)
    curves = attach_units(curves)
    base, c = main_set(curves, cfg)
    usage = len(c) / len(base)
    n_with_cov = c.dropna(subset=["log10_I"]).shape[0]

    os.makedirs(OUT, exist_ok=True)
    f1, f0 = os.path.join(OUT, "cv_with_covariates.csv"), os.path.join(OUT, "cv_without_covariates.csv")
    if reuse and os.path.exists(f1) and os.path.exists(f0):
        P, P0 = pd.read_csv(f1), pd.read_csv(f0)
    else:
        P = cross_validate(c, obs, cfg, covariates=True, seed=seed)
        P.to_csv(f1, index=False)
        P0 = cross_validate(c, obs, cfg, covariates=False, seed=seed)
        P0.to_csv(f0, index=False)

    # baselines on the same curves, line-based native edge as input and target
    cb = H.prepare(c, "pH_native")
    bp_ = H.baseline_predictions(cb, unit_col="unit")
    preds = bp_.merge(P[["curve_id", "pred_edge", "edge_lo", "edge_hi"]].rename(
        columns={"pred_edge": "E1", "edge_lo": "E1__lo", "edge_hi": "E1__hi"}), on="curve_id", how="left")
    preds = preds.merge(P0[["curve_id", "pred_edge", "edge_lo", "edge_hi"]].rename(
        columns={"pred_edge": "E1_no_covariates", "edge_lo": "E1_no_covariates__lo",
                 "edge_hi": "E1_no_covariates__hi"}), on="curve_id", how="left")
    models = ["E1", "E1_no_covariates"] + H.BASELINES
    L = H.long_errors(cb, preds, models, unit_col="unit")
    L = L.merge(cb[["curve_id", "grp"]], on="curve_id")
    multi = cb.groupby("grp")["unit"].transform("nunique") >= 2
    multi_ids = set(cb.loc[multi, "curve_id"])
    Lm = L[L["curve_id"].isin(multi_ids)]
    Ls = L[~L["curve_id"].isin(multi_ids)]

    B = ecfg["harness"]["paper_bootstrap_B"]
    s_multi = H.summarize(Lm, B=B, seed=seed)
    s_single = H.summarize(Ls, B=B, seed=seed)
    d_multi = H.paired(Lm, "E1", ["B3_matched_fb", "B0_all_other", "B1_nearest1", "B5_global_mean", "E1_no_covariates"],
                       B=B, seed=seed)
    d_single = H.paired(Ls, "E1", ["B4_class_mean", "B5_global_mean"], B=B, seed=seed)
    d_fall = H.paired(Lm[Lm["shape"] == "falling"], "E1", ["B3_matched_fb"], B=B, seed=seed)
    nc = H.noise_ceiling(Lm, "E1", B=B, seed=seed)

    # log K rmse vs baselines
    lk_b = baseline_logk(cb, obs)
    lk = pd.concat([P[["curve_id", "logK_rmse"]].assign(model="E1"), lk_b], ignore_index=True)
    lk = lk.merge(cb[["curve_id", "unit"]], on="curve_id")
    lk = lk[lk["curve_id"].isin(multi_ids)]
    lk_diff = H.paired(lk.rename(columns={"logK_rmse": "edge_error"}), "E1", ["B3_matched_fb", "B0_all_other"],
                       B=B, seed=seed)

    # decision (pre-declared in experiments.yaml)
    e1m = s_multi.set_index("model")
    edge_ok = e1m.loc["E1", "median"] <= e1m.loc["B3_matched_fb", "median"]
    lk_row = lk_diff[lk_diff["baseline"] == "B3_matched_fb"].iloc[0]
    logk_ok = lk_row["diff_lo"] <= 0
    cov = float(L[L["model"] == "E1"]["covered"].mean())
    cov_ok = cfg["decision"]["coverage"][0] <= cov <= cfg["decision"]["coverage"][1]
    usage_ok = usage >= cfg["decision"]["curve_usage_min"]
    g_b0 = d_multi[d_multi["baseline"] == "B0_all_other"].iloc[0]["diff_lo"] <= 0
    g_fall = d_fall.iloc[0]["diff_lo"] <= 0 if len(d_fall) else True
    verdict = "ACCEPT" if (edge_ok and logk_ok and cov_ok and usage_ok and g_b0 and g_fall) else "REJECT"

    # full development fit: variance components and coefficients
    full = E1Model(cfg, True).fit(c)
    comp = pd.DataFrame([{"target": "level a_c", **{k: v for k, v in full.fa["components"].items()}},
                         {"target": "slope b", **{k: v for k, v in full.fb["components"].items()}}])
    for k in ("class_dir", "pair_dir", "unit", "residual"):
        comp[f"share_{k}"] = comp[k] / comp[["class_dir", "pair_dir", "unit", "residual"]].sum(axis=1)
    se = np.sqrt(np.diag(full.cov_a))
    coef = pd.DataFrame({"term": ["intercept"] + full.level_fixed, "estimate": full.fa["beta"], "se": se})
    coef["ci_lo"], coef["ci_hi"] = coef["estimate"] - 1.96 * coef["se"], coef["estimate"] + 1.96 * coef["se"]

    os.makedirs(OUT, exist_ok=True)
    P.to_csv(os.path.join(OUT, "heldout_predictions.csv"), index=False)
    L.sort_values("edge_error", ascending=False).to_csv(os.path.join(OUT, "per_curve_worst_first.csv"), index=False)
    pd.concat([s_multi.assign(subset="pairs with >= 2 units"), s_single.assign(subset="pairs with 1 unit")]).to_csv(
        os.path.join(OUT, "summary_edge.csv"), index=False)
    pd.concat([d_multi.assign(subset="multi"), d_single.assign(subset="single"), d_fall.assign(subset="falling multi"),
               lk_diff.assign(subset="logK multi")]).to_csv(os.path.join(OUT, "paired_differences.csv"), index=False)
    comp.to_csv(os.path.join(OUT, "variance_components.csv"), index=False)
    coef.to_csv(os.path.join(OUT, "coefficients.csv"), index=False)
    usage_tab = pd.DataFrame([{"set": "rising/falling with solids and total (development)", "curves": len(base)},
                              {"set": "E1 main set (line usable)", "curves": len(c)},
                              {"set": "Stage 1 core single-edge (development)",
                               "curves": int((base["in_core_library"].astype(bool)).sum())}])
    usage_tab.to_csv(os.path.join(OUT, "curve_usage.csv"), index=False)
    _calibration_plot(P, os.path.join(OUT, "calibration.png"))

    _write_summary(stamp, verdict, dict(edge_ok=edge_ok, logk_ok=logk_ok, cov=cov, cov_ok=cov_ok, usage=usage,
                                        usage_ok=usage_ok, g_b0=g_b0, g_fall=g_fall), s_multi, s_single, d_multi,
                   d_single, d_fall, lk_diff, nc, comp, coef, usage_tab, full.bp, n_with_cov, len(c))
    log_run("E1", verdict, f"edge median E1 {e1m.loc['E1','median']:.3f} vs B3 {e1m.loc['B3_matched_fb','median']:.3f}; "
            f"coverage {cov:.2f}; usage {usage:.2f}", stamp)
    record_adjustment("E1 log10 K mixed model (two-step) as the core model", verdict,
                      f"multi-unit pairs: median edge error E1 {e1m.loc['E1','median']:.3f} vs B3 "
                      f"{e1m.loc['B3_matched_fb','median']:.3f} pH; logK paired diff vs B3 {lk_row['median_diff']:.3f} "
                      f"[{lk_row['diff_lo']:.3f}, {lk_row['diff_hi']:.3f}]; coverage {cov:.2f}; usage {usage:.2f}")
    print(f"E1 {verdict}")
    return P, L


def _calibration_plot(P, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from phslope.report import BLUE, GRAY, _style
    d = P.dropna(subset=["pred_edge", "pH_native"])
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.scatter(d["pH_native"], d["pred_edge"], s=8, color=BLUE, alpha=.5, linewidths=0)
    ax.plot([2, 11], [2, 11], color=GRAY, lw=1, ls="--")
    ax.set_xlabel("observed native edge (pH)", fontsize=9)
    ax.set_ylabel("E1 predicted edge, held-out unit (pH)", fontsize=9)
    ax.set_title(f"E1 held-out predictions (n = {len(d)})", fontsize=10, loc="left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_summary(stamp, verdict, chk, s_multi, s_single, d_multi, d_single, d_fall, lk_diff, nc, comp, coef,
                   usage_tab, bp, n_with_cov, n_main):
    from phslope.report import md_table
    e = s_multi.set_index("model")
    lines = [
        "# E1 log10 K mixed model (two-step)", "",
        "**Plain English.** Instead of fitting an S-curve to each experiment and throwing away the ones that "
        "do not show a full S, we fitted a straight line to how strongly the sorbate sticks (on a log scale) "
        "against pH, which works even for partial curves, and let a statistical model learn how the lines differ "
        "between sorbates, mineral-sorbate pairs and papers, and with the amount of mineral used. "
        f"For a paper the model has not seen, it predicts where the curve crosses 50% to a median of "
        f"{e.loc['E1','median']:.2f} pH units, against {e.loc['B3_matched_fb','median']:.2f} for the best simple "
        f"rule (copying the closest-conditions papers). Verdict on the pre-declared rule: **{verdict}**.", "",
        f"> EXPLORATORY. Development papers only; leave-out unit = E3 lineage cluster. Locked set hash "
        f"`{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## Formulation", "",
        "Two-step (allowed by the protocol): per-curve log10 K lines, then REML models of the level at the pair's "
        "reference pH and of the slope, with random effects for sorbate class x direction, pair x direction and "
        "unit, and direction-specific solids and loading-hinge terms plus total sorbate, co-solute, CO2 and ionic "
        "strength for the level. The one-step random-slope model on all points was not run (not available at a "
        f"usable speed with the installed tools). Loading breakpoint on all development data: {bp} log10 mol/g "
        "(chosen inside each fold for the held-out runs).", "",
        "## Decision rule (pre-declared)", "",
        f"- median native edge error <= B3 on pairs with >= 2 units: {'yes' if chk['edge_ok'] else 'NO'} "
        f"({e.loc['E1','median']:.3f} vs {e.loc['B3_matched_fb','median']:.3f})",
        f"- log10 K RMSE not worse than B3 (paired 95% interval lower bound <= 0): {'yes' if chk['logk_ok'] else 'NO'}",
        f"- edge interval coverage in [0.80, 0.95]: {'yes' if chk['cov_ok'] else 'NO'} ({chk['cov']:.2f})",
        f"- curve usage >= 70%: {'yes' if chk['usage_ok'] else 'NO'} ({chk['usage']:.1%}; {n_main} curves)",
        f"- guard, not worse than B0 on pairs with >= 2 units: {'yes' if chk['g_b0'] else 'NO'}",
        f"- guard, no degradation on falling edges vs B3: {'yes' if chk['g_fall'] else 'NO'}",
        f"- **Verdict: {verdict}**", "",
        "## Edge error, pairs with >= 2 units (paired with all baselines)", "", md_table(s_multi), "",
        md_table(d_multi), "",
        f"Noise-ceiling fraction (share of the gap between the global mean B5 and the plain average B0 that E1 "
        f"closes; 1 = as good as B0): {nc['fraction']:.2f} [{nc['lo']:.2f}, {nc['hi']:.2f}], n = {nc['n']}.", "",
        "## Edge error, pairs with only 1 unit (E1 relies on class and covariates)", "", md_table(s_single), "",
        md_table(d_single), "",
        "## Falling edges (guard)", "", md_table(d_fall), "",
        "## log10 K RMSE at the held-out curve's mid-range points (pairs with >= 2 units)", "", md_table(lk_diff), "",
        "## Variance components (full development fit)", "", md_table(comp), "",
        "## Level coefficients (full development fit; per unit of the covariate; level = log10 K at pH_c)", "",
        md_table(coef), "",
        "## Curve usage", "", md_table(usage_tab), "",
        "Files: `heldout_predictions.csv`, `per_curve_worst_first.csv`, `summary_edge.csv`, `paired_differences.csv`, "
        "`variance_components.csv`, `coefficients.csv`, `curve_usage.csv`, `calibration.png`.", "",
        "## Limitations", "",
        "- Two-step: per-curve line uncertainty is not propagated into step 2 (lines are treated as exact); "
        "intervals rest on the fitted variance components.",
        "- Lines are fitted over 3-97% sorbed only; bell and multi-step curves are excluded by the R2 >= 0.5 and "
        "direction rules (E2 revisits the window).",
        "- The class labels are the unconfirmed proposal in classes.yaml.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    import sys
    run(reuse="--reuse" in sys.argv)
