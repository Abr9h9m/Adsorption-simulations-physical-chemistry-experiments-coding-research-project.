"""E17 (partial) particle-concentration diagnostics and E22 where to measure next (Addendum 1).
EXPLORATORY; development papers only.

E17 (rising edges; [lit] particle-concentration effect, titles only so far). Within pair, log10 K at the
pair reference pH (level) on centred log10 solids. Linear sorption predicts slope +1. Tested:
  (i)   interaction with pair strength (pair-mean log10 Kd at the reference pH, standardised): negative
        if the deficit is larger for strongly sorbing systems
  (iii) curvature: centred log10 solids squared (negative = deficit grows at high solids)
  (iv)  the same model for falling edges (expected slope near +1, no deficit)
  (ii)  needs the separation method (E10 table): not run
E22 Using the final development model's variance components: for every pair x direction in the training
data, prediction variance of a new paper's level now (pair-effect prediction error + paper + residual) and
after one more paper with k curves (Bayesian update of the pair effect); unmeasured pairs inside the
Stage 0 dense block start from the pair (+ class) variance. Ranked by variance reduction.
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.integrate import accepted_adjustments, prepare
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)


def e17(c):
    c = c.copy()
    c["pH_c"] = E1.reference_pH(c, c)
    c["level"] = c["a"] + c["b"] * c["pH_c"]
    c["logKd_ref"] = c["level"] - c["log10_solids"]
    rows = []
    for shape in ("rising", "falling"):
        d = c[c["shape"] == shape].dropna(subset=["level", "log10_solids"])
        d = d[d.groupby("pair_dir")["log10_solids"].transform(lambda s: s.max() - s.min()) >= 0.3]
        y = d["level"] - d.groupby("pair_dir")["level"].transform("mean")
        x = d["log10_solids"] - d.groupby("pair_dir")["log10_solids"].transform("mean")
        strength = d.groupby("pair_dir")["logKd_ref"].transform("mean")
        strength = (strength - strength.mean()) / strength.std()
        sq = x ** 2
        X = pd.DataFrame({"solids": x, "solids_x_strength": x * strength,
                          "solids_sq": sq - sq.groupby(d["pair_dir"]).transform("mean")})
        r = sm.OLS(y, sm.add_constant(X)).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["unit"])[0]})
        ci = r.conf_int()
        for term in X.columns:
            rows.append({"direction": shape, "term": term, "estimate": r.params[term], "ci_lo": ci.loc[term, 0],
                         "ci_hi": ci.loc[term, 1], "n": len(d), "pairs": d["pair_dir"].nunique(),
                         "units": d["unit"].nunique()})
    return pd.DataFrame(rows)


def e22(c, ecfg, k):
    acc = accepted_adjustments()
    covs = [x for s in acc.values() for x in s.get("covs", [])]
    wb = [x for s in acc.values() for x in s.get("within_between", [])]
    m = E1.E1Model(ecfg["e1"], True, covs, wb).fit(c)
    comp = m.fa["components"]
    pev = m.ea["pair_dir"].set_index("level")["pev"]
    noise = comp["unit"] + comp["residual"] / k             # one new paper's mean level, as information
    n_units = c.groupby("pair_dir")["unit"].nunique()
    rows = []
    for pdir, v in pev.items():
        new = 1 / (1 / v + 1 / noise) if v > 0 else 0.0
        rows.append({"pair_direction": pdir, "units_now": int(n_units.get(pdir, 0)),
                     "pred_sd_now": np.sqrt(v + comp["unit"] + comp["residual"]),
                     "pred_sd_after_one_paper": np.sqrt(new + comp["unit"] + comp["residual"]),
                     "variance_reduction": v - new})
    gaps_path = os.path.join(EXP_DIR, "..", "stage0", "gap_list.csv")
    if os.path.exists(gaps_path):
        prior = comp["pair_dir"] + comp["class_dir"]
        for g in pd.read_csv(gaps_path).itertuples():
            if g.n_curves == 0:
                new = 1 / (1 / prior + 1 / noise)
                rows.append({"pair_direction": f"{g.mineral} | {g.sorbate} (unmeasured)", "units_now": 0,
                             "pred_sd_now": np.sqrt(prior + comp["unit"] + comp["residual"]),
                             "pred_sd_after_one_paper": np.sqrt(new + comp["unit"] + comp["residual"]),
                             "variance_reduction": prior - new})
    R = pd.DataFrame(rows).sort_values("variance_reduction", ascending=False).reset_index(drop=True)
    R["rank"] = np.arange(1, len(R) + 1)
    return R, comp


def run():
    from phslope.report import md_table
    ecfg = load_exp_config()
    curves, obs = build(purpose="E17/E22")
    stamp = exp_stamp(extra={"experiment": "E17 partial + E22"})
    c = prepare(curves, obs, ecfg, accepted_adjustments())
    for exp in ("E17", "E22"):
        write_run_info(os.path.join(EXP_DIR, exp), stamp)
    T = e17(c)
    ri = T[(T["direction"] == "rising") & (T["term"] == "solids_x_strength")].iloc[0]
    ok_i = ri["ci_hi"] < 0
    v17 = "PREDICTION (i) HOLDS" if ok_i else "PREDICTION (i) NOT SUPPORTED"
    T.to_csv(os.path.join(EXP_DIR, "E17", "interactions.csv"), index=False)
    with open(os.path.join(EXP_DIR, "E17", "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join([
            "# E17 (partial) Particle-concentration diagnostics", "",
            "**Plain English.** For metal cations, adding more mineral increases sorption much less than simple "
            "chemistry predicts. One known explanation is fine particles slipping through the separation step. If "
            "so, the shortfall should be biggest for strongly sorbing systems and at high mineral amounts. "
            f"Result: **{v17}**.", "",
            f"> EXPLORATORY. [lit] titles only (read before wording). Development papers only. Locked set hash "
            f"`{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`. Prediction (ii) needs the separation "
            "method (E10 table) and was not run.", "",
            "Within pair: level of log10 K (at the pair reference pH) on centred log10 solids (linear sorption: "
            "+1), with interactions; clustered by lineage unit.", "", md_table(T), "",
            "Read: `solids` = slope at average strength (expected +1); `solids_x_strength` negative = (i); "
            "`solids_sq` negative = (iii). Falling rows test (iv).", ""]) + "\n")
    R, comp = e22(c, ecfg, ecfg["e22"]["curves_per_new_paper"])
    R.to_csv(os.path.join(EXP_DIR, "E22", "measure_next_ranking.csv"), index=False)
    with open(os.path.join(EXP_DIR, "E22", "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join([
            "# E22 Where to measure next", "",
            "**Plain English.** For each mineral-contaminant pair, how much would ONE more independent paper (with "
            f"{ecfg['e22']['curves_per_new_paper']} curves) shrink the uncertainty of predictions? Pairs measured "
            "by a single paper and unmeasured pairs in the well-studied block gain most. This ranking is for "
            "planning experiments and for the web interface's coverage map.", "",
            f"> EXPLORATORY. Final development model; level of log10 K at the pair reference pH. Paper-to-paper SD "
            f"{np.sqrt(comp['unit']):.2f}, residual SD {np.sqrt(comp['residual']):.2f}, pair SD "
            f"{np.sqrt(comp['pair_dir']):.2f} (log10 K units). Locked set hash `{stamp['locked_set_hash']}`.", "",
            "The paper-to-paper term cannot be reduced by more papers on the same pair, so even a large reduction "
            "of the pair term changes the predictive SD only modestly.", "",
            "## Top 25", "", md_table(R.head(25)), "", "Full ranking: `measure_next_ranking.csv`."]) + "\n")
    log_run("E17", v17, "(ii) waits for E10", stamp)
    log_run("E22", "reported", f"{len(R)} pairs ranked", stamp)
    record_adjustment("E17 particle-concentration interaction", "ACCEPT" if ok_i else "REJECT",
                      f"rising solids x strength {ri['estimate']:.3f} [{ri['ci_lo']:.3f}, {ri['ci_hi']:.3f}]")
    print(v17)
    print(T.to_string())
    print(R.head(8).to_string())


if __name__ == "__main__":
    run()
