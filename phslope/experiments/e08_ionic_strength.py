"""E8 -- ionic strength by sorbate type (protocol section 5, E8). EXPLORATORY; development only.

Classes are pre-declared in experiments.yaml (outer-sphere-prone, inner-sphere-prone, oxyanion,
organic acid). Curves: rising/falling with a usable log10 K line (E1 main-set rule).

1. Within paper: series of curves from the same paper and pair (and direction) that differ in ionic
   strength while solids, total sorbate and temperature agree within 10% of the series median.
   Outcomes: native edge, solids-normalised edge, plateau (95th percentile of fraction sorbed).
   Effect = slope of series-centred outcome on series-centred log10 I, errors clustered by paper.
2. Cross paper: pair-centred native edge on pair-centred log10 I and log10 solids (by direction),
   clustered by unit.
3. Nonlinearity (within paper): ionic-strength bands vs linear in log10 I (AIC).
Decision (pre-declared): outer-sphere within-paper effect on the native edge with a 95% interval
excluding zero AND a difference from the inner-sphere class with an interval excluding zero.
Benjamini-Hochberg across all class x outcome tests; the number of tests is reported.
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, bh, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E8")
OUTCOMES = {"native_edge": "pH_native", "solids_normalised_edge": "pH_S1", "plateau": "plateau"}


def assign_class(sorbate, classes):
    for k, v in classes.items():
        if sorbate in v:
            return k
    return "unclassified"


def within_paper_series(c, tol):
    """Rows of c that belong to a within-paper ionic-strength series (>= 2 distinct I levels)."""
    keep = []
    for (ref, pd_), g in c.groupby(["reference", "pair_dir"]):
        if g["log10_I"].round(3).nunique() < 2:
            continue
        ok = np.ones(len(g), bool)
        for col in ("solids_g_L", "total_sorbate_mol_L"):
            med = g[col].median()
            ok &= (g[col] - med).abs().to_numpy() <= tol * abs(med)
        t = g["temp"]
        if t.notna().any():
            ok &= ((t - t.median()).abs() <= tol * abs(t.median())).fillna(False).to_numpy()
        s = g[ok]
        if s["log10_I"].round(3).nunique() >= 2:
            keep.append(s.assign(series=f"{ref}|{pd_}"))
    return pd.concat(keep) if keep else c.iloc[:0].assign(series=[])


def clustered_slope(y, x, groups):
    d = pd.DataFrame({"y": y, "x": x, "g": groups}).dropna()
    if len(d) < 6 or d["x"].std() == 0 or d["g"].nunique() < 2:
        return {"n": len(d), "slope": np.nan, "ci_lo": np.nan, "ci_hi": np.nan, "p": np.nan}
    r = sm.OLS(d["y"], sm.add_constant(d["x"])).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["g"])[0]})
    ci = r.conf_int().iloc[1]
    return {"n": len(d), "n_clusters": d["g"].nunique(), "slope": r.params.iloc[1], "ci_lo": ci[0], "ci_hi": ci[1],
            "p": r.pvalues.iloc[1]}


def run():
    ecfg = load_exp_config()
    cfg = ecfg["e8"]
    curves, obs = build(purpose="E8")
    stamp = exp_stamp(extra={"experiment": "E8"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    c = c[c["log10_I"].notna()].copy()
    c["plateau"] = c["curve_id"].map(obs.groupby("curve_id")["response"].quantile(0.95))
    c["i_class"] = c["sorbate"].map(lambda s: assign_class(s, cfg["classes"]))

    S = within_paper_series(c, cfg["same_within"])
    for k, col in OUTCOMES.items():
        S[f"{k}_c"] = S[col] - S.groupby("series")[col].transform("mean")
    S["logI_c"] = S["log10_I"] - S.groupby("series")["log10_I"].transform("mean")
    rows = []
    for cls in list(cfg["classes"]) + ["all"]:
        d = S if cls == "all" else S[S["i_class"] == cls]
        for k in OUTCOMES:
            r = clustered_slope(d[f"{k}_c"], d["logI_c"], d["reference"])
            rows.append({"analysis": "within paper", "class": cls, "outcome": k, "n_series": d["series"].nunique(), **r})
    # class difference outer vs inner (native edge), interaction model
    d = S[S["i_class"].isin(["outer_sphere_prone", "inner_sphere_prone"])].dropna(subset=["native_edge_c"])
    diff = {"estimate": np.nan, "ci_lo": np.nan, "ci_hi": np.nan, "p": np.nan, "n": len(d)}
    if d["i_class"].nunique() == 2 and len(d) > 10:
        X = pd.DataFrame({"x": d["logI_c"], "x_outer": d["logI_c"] * (d["i_class"] == "outer_sphere_prone")})
        r = sm.OLS(d["native_edge_c"], sm.add_constant(X)).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d["reference"])[0]})
        ci = r.conf_int().loc["x_outer"]
        diff = {"estimate": r.params["x_outer"], "ci_lo": ci[0], "ci_hi": ci[1], "p": r.pvalues["x_outer"], "n": len(d)}

    # cross-paper
    c["edge_c"] = c["pH_native"] - c.groupby("pair_dir")["pH_native"].transform("mean")
    c["logI_pc"] = c["log10_I"] - c.groupby("pair_dir")["log10_I"].transform("mean")
    c["sol_pc"] = (c["log10_solids"] - c.groupby("pair_dir")["log10_solids"].transform("mean")) * c["direction"]
    for cls in list(cfg["classes"]) + ["all"]:
        d = (c if cls == "all" else c[c["i_class"] == cls])[["edge_c", "logI_pc", "sol_pc", "unit"]].dropna()
        if len(d) < 10 or d["logI_pc"].std() == 0:
            rows.append({"analysis": "cross paper", "class": cls, "outcome": "native_edge", "n": len(d)})
            continue
        r = sm.OLS(d["edge_c"], sm.add_constant(d[["logI_pc", "sol_pc"]])).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d["unit"])[0]})
        ci = r.conf_int().loc["logI_pc"]
        rows.append({"analysis": "cross paper", "class": cls, "outcome": "native_edge", "n": len(d),
                     "n_clusters": d["unit"].nunique(), "slope": r.params["logI_pc"], "ci_lo": ci[0], "ci_hi": ci[1],
                     "p": r.pvalues["logI_pc"]})
    R = pd.DataFrame(rows)
    tested = R["p"].notna() & (R["class"] != "all")
    R["q_value"] = np.nan
    R.loc[tested, "q_value"] = bh(R.loc[tested, "p"])

    # nonlinearity: bands vs linear, within paper, native edge
    bands = pd.cut(S["log10_I"], [-np.inf, -2, -1, np.inf], labels=["<0.01", "0.01-0.1", ">0.1"])
    dd = S.assign(band=bands).dropna(subset=["native_edge_c"])
    aic_lin = sm.OLS(dd["native_edge_c"], sm.add_constant(dd["logI_c"])).fit().aic if len(dd) > 5 else np.nan
    Xb = pd.get_dummies(dd["band"], drop_first=True, dtype=float)
    Xb = Xb - Xb.groupby(dd["series"]).transform("mean")
    aic_band = sm.OLS(dd["native_edge_c"], sm.add_constant(Xb)).fit().aic if len(dd) > 5 else np.nan

    outer = R[(R["analysis"] == "within paper") & (R["class"] == "outer_sphere_prone") & (R["outcome"] == "native_edge")]
    outer_ok = len(outer) and np.isfinite(outer["ci_lo"].iloc[0]) and (outer["ci_lo"].iloc[0] > 0 or outer["ci_hi"].iloc[0] < 0)
    diff_ok = np.isfinite(diff["ci_lo"]) and (diff["ci_lo"] > 0 or diff["ci_hi"] < 0)
    verdict = "EFFECT FOUND (meets rule)" if (outer_ok and diff_ok) else "NO CLASS-SPECIFIC EFFECT (rule not met)"

    S.to_csv(os.path.join(OUT, "within_paper_series.csv"), index=False)
    R.to_csv(os.path.join(OUT, "effects.csv"), index=False)
    counts = S.groupby("i_class").agg(series=("series", "nunique"), curves=("curve_id", "size"),
                                      papers=("reference", "nunique")).reset_index()
    from phslope.report import md_table
    lines = [
        "# E8 Ionic strength by sorbate type", "",
        "**Plain English.** Overall, the amount of background salt did not move the sorption edge. Here we "
        "checked whether it matters for weakly held cations (like caesium or strontium), where textbook chemistry "
        "says more salt should reduce sorption, using experiments where the same lab changed only the salt. "
        f"Result: **{verdict}**.", "",
        f"> EXPLORATORY. Development papers only. Classes pre-declared in experiments.yaml. Locked set hash "
        f"`{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        "## Within-paper ionic-strength series (solids, total sorbate, temperature within 10%)", "", md_table(counts), "",
        "## Effects per unit log10 I (pH units for edges, fraction sorbed for plateau)", "",
        f"{int(tested.sum())} class-level tests; q = Benjamini-Hochberg over them.", "", md_table(R), "",
        "## Outer-sphere minus inner-sphere slope (native edge, within paper)", "",
        f"{diff['estimate']:.3f} pH per log10 I, 95% interval [{diff['ci_lo']:.3f}, {diff['ci_hi']:.3f}], "
        f"p = {diff['p']:.3g}, n = {diff['n']}.", "",
        f"Expected sign for outer-sphere complexes: sorption decreases as ionic strength increases, i.e. a rising "
        "edge moves to higher pH (positive slope).", "",
        "## Bands vs linear (within paper, native edge)", "",
        f"AIC linear in log10 I: {aic_lin:.1f}; AIC with bands (<0.01, 0.01-0.1, >0.1 M): {aic_band:.1f} "
        "(lower is better).", "",
        "Files: `within_paper_series.csv`, `effects.csv`.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E8", verdict, f"{int(tested.sum())} tests; {S['series'].nunique()} within-paper series", stamp)
    record_adjustment("E8 class-specific ionic-strength term", "ACCEPT" if (outer_ok and diff_ok) else "REJECT",
                      f"outer-sphere vs inner-sphere slope difference {diff['estimate']:.3f} "
                      f"[{diff['ci_lo']:.3f}, {diff['ci_hi']:.3f}] pH per log10 I")
    print(f"E8 {verdict}")
    print(counts.to_string())
    return R


if __name__ == "__main__":
    run()
