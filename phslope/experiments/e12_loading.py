"""E12 -- loading shifts the edge; heterogeneous sites (Addendum 1, E12 [lit]). EXPLORATORY; development only.

[lit] Balistrieri & Chao 1987 (selenite/goethite: higher total selenite shifted the edge to lower pH;
heterogeneous sites; abstract read). Dzombak & Morel 1986 (Cd/HFO: strong and weak sites; Langmuir at low,
Freundlich at moderate concentration; abstract read).

1. Within-paper concentration series: same paper, pair and direction; total sorbate varies by >= 0.3
   decade; solids within 10%. Effect of log10 total on native edge, solids-normalised edge, plateau
   (95th percentile of fraction sorbed) and slope b; errors clustered by paper.
2. Freundlich exponent: at the series reference pH (median native edge), each curve's log10 K line gives
   f, hence sorbed q = f x total / S (mol/g) and aqueous C = (1 - f) x total (mol/L). Slope of log q on
   log C within series (n = 1 linear; n < 1 heterogeneous). Per series (>= 3 loading levels) and pooled
   within-series with paper-clustered interval.
3. One-site vs two-site saturation of log10 Kd (at the pair reference pH) against loading, with a free level
   per pair: one-site log Kd = c_g - log10(1 + L / Ls); two-site log Kd = c_g + log10(w / (1 + L / L1) +
   (1 - w) / (1 + L / L2)). Leave-one-pair-out squared error.
Pitfall (not checked here): precipitation at high loading mimics saturation; solubility limits need a cited
source (Samuel).
"""
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.optimize import least_squares

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments.data import build
from phslope.experiments.e08_ionic_strength import clustered_slope
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "E12")


def concentration_series(c, cfg):
    keep = []
    for (ref, pdir), g in c.groupby(["reference", "pair_dir"]):
        if g["log10_total"].max() - g["log10_total"].min() < cfg["min_loading_span_decades"]:
            continue
        med = g["solids_g_L"].median()
        s = g[(g["solids_g_L"] - med).abs() <= cfg["same_within"] * med]
        if s["log10_total"].round(2).nunique() >= 2:
            keep.append(s.assign(series=f"{ref}|{pdir}"))
    return pd.concat(keep) if keep else c.iloc[:0].assign(series=[])


def freundlich(S):
    S = S.copy()
    S["pH_ref"] = S.groupby("series")["pH_native"].transform("median")
    lk = S["a"] + S["b"] * S["pH_ref"]
    f = 1 / (1 + 10 ** -lk)
    tot = 10 ** S["log10_total"]
    S["log_q"] = np.log10(f * tot / S["solids_g_L"])
    S["log_C"] = np.log10((1 - f) * tot)
    per = []
    for name, g in S.groupby("series"):
        if g["log10_total"].round(2).nunique() >= 3:
            r = sm.OLS(g["log_q"], sm.add_constant(g["log_C"])).fit()
            lo, hi = r.conf_int().iloc[1]
            per.append({"series": name, "levels": g["log10_total"].round(2).nunique(), "n": r.params.iloc[1],
                        "ci_lo": lo, "ci_hi": hi})
    yc = S["log_q"] - S.groupby("series")["log_q"].transform("mean")
    xc = S["log_C"] - S.groupby("series")["log_C"].transform("mean")
    pooled = clustered_slope(yc, xc, S["reference"])
    return pd.DataFrame(per), pooled


def _shape(params, L, two):
    if not two:
        (ls,) = params
        return -np.log10(1 + 10 ** (L - ls))
    l1, l2, wl = params
    w = 1 / (1 + np.exp(-wl))
    return np.log10(w / (1 + 10 ** (L - l1)) + (1 - w) / (1 + 10 ** (L - l2)))


def fit_saturation(d, two):
    y, L, g = d["logKd"].to_numpy(), d["log10L"].to_numpy(), d["pair_dir"].to_numpy()
    codes, inv = np.unique(g, return_inverse=True)

    def resid(p):
        s = _shape(p, L, two)
        r = y - s
        off = np.bincount(inv, weights=r) / np.bincount(inv)
        return r - off[inv]
    x0 = [-4.5] if not two else [-6.0, -3.5, 0.0]
    lb = [-12] if not two else [-12, -12, -10]
    ub = [0] if not two else [0, 0, 10]
    best = None
    for shift in (0.0, -1.5, 1.5):
        r = least_squares(resid, np.array(x0) + shift, bounds=(lb, ub))
        if best is None or r.cost < best.cost:
            best = r
    return best.x


def lopo_error(d, two):
    sse = 0.0
    for pdir in d["pair_dir"].unique():
        tr, te = d[d["pair_dir"] != pdir], d[d["pair_dir"] == pdir]
        if len(te) < 2:
            continue
        p = fit_saturation(tr, two)
        s = _shape(p, te["log10L"].to_numpy(), two)
        r = te["logKd"].to_numpy() - s
        r = r - r.mean()                                # the held-out pair's own level is free
        sse += float(r @ r)
    return sse


def run():
    ecfg = load_exp_config()
    cfg = ecfg["e12"]
    curves, obs = build(purpose="E12")
    stamp = exp_stamp(extra={"experiment": "E12"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    c["plateau"] = c["curve_id"].map(obs.groupby("curve_id")["response"].quantile(0.95))

    S = concentration_series(c, cfg)
    eff = []
    for col, lab in (("pH_native", "native edge (pH per decade of total)"),
                     ("pH_S1", "solids-normalised edge"), ("plateau", "plateau (fraction)"), ("b", "slope b")):
        y = S[col] - S.groupby("series")[col].transform("mean")
        x = S["log10_total"] - S.groupby("series")["log10_total"].transform("mean")
        for shape in ("rising", "falling"):
            sel = S["shape"] == shape
            eff.append({"outcome": lab, "direction": shape, "series": S.loc[sel, "series"].nunique(),
                        **clustered_slope(y[sel], x[sel], S.loc[sel, "reference"])})
    EFF = pd.DataFrame(eff)
    per, pooled = freundlich(S)

    d = c.copy()
    d["pH_ref"] = d.groupby("pair_dir")["pH_native"].transform("median")
    d = d[(d["pH_ref"] >= d["mid_pH_lo"] - 0.25) & (d["pH_ref"] <= d["mid_pH_hi"] + 0.25)]
    d["logKd"] = d["a"] + d["b"] * d["pH_ref"] - d["log10_solids"]
    d = d.dropna(subset=["logKd", "log10L"])
    d = d[d.groupby("pair_dir")["log10L"].transform(lambda s: s.max() - s.min()) >= 0.5]
    one, two = lopo_error(d, False), lopo_error(d, True)
    p1, p2 = fit_saturation(d, False), fit_saturation(d, True)

    het = np.isfinite(pooled["ci_hi"]) and pooled["ci_hi"] < 1 and two < one
    verdict = "HETEROGENEITY SUPPORTED" if het else "HETEROGENEITY NOT SUPPORTED (rule not met)"
    os.makedirs(OUT, exist_ok=True)
    EFF.to_csv(os.path.join(OUT, "concentration_series_effects.csv"), index=False)
    per.to_csv(os.path.join(OUT, "freundlich_per_series.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E12 Loading and heterogeneous sites", "",
        "**Plain English.** If a mineral surface has a few strong binding sites and many weak ones, adding more "
        "contaminant fills the strong sites first, so each extra unit binds less well. We checked within papers "
        f"that varied only the amount of contaminant. Result: **{verdict}**.", "",
        f"> EXPLORATORY. **[lit]** Balistrieri & Chao 1987; Dzombak & Morel 1986 (abstracts read). Development "
        f"papers only. Locked set hash `{stamp['locked_set_hash']}`. Commit `{stamp['git_commit']}`.", "",
        f"## 1. Within-paper concentration series ({S['series'].nunique()} series, {S['reference'].nunique()} papers)", "",
        md_table(EFF), "",
        "## 2. Freundlich exponent (slope of log sorbed per gram on log dissolved, within series)", "",
        f"Pooled within-series exponent: {pooled['slope']:.3f}, 95% interval [{pooled['ci_lo']:.3f}, "
        f"{pooled['ci_hi']:.3f}] ({pooled['n']} curves, {pooled.get('n_clusters')} papers). 1 = linear sorption; "
        "below 1 = heterogeneous sites.", "",
        f"Per series with >= 3 loading levels ({len(per)}): " + (f"{int((per['ci_hi'] < 1).sum())} have an interval "
        f"below 1; median exponent {per['n'].median():.2f}." if len(per) else "none."), "", md_table(per), "",
        "## 3. One-site vs two-site saturation of log10 Kd against loading (leave-one-pair-out)", "",
        f"{len(d)} curves, {d['pair_dir'].nunique()} pairs. Squared error: one-site {one:.2f}, two-site {two:.2f} "
        f"(lower is better). One-site saturation loading 10^{p1[0]:.2f} mol/g; two-site 10^{p2[0]:.2f} and "
        f"10^{p2[1]:.2f} mol/g, strong-site fraction {1 / (1 + np.exp(-p2[2])):.2f}.", "",
        "Not checked: whether high-loading points exceed solubility (needs a cited solubility source).",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E12", verdict, f"Freundlich {pooled['slope']:.2f} [{pooled['ci_lo']:.2f},{pooled['ci_hi']:.2f}]; "
            f"SSE one {one:.1f} two {two:.1f}", stamp)
    record_adjustment("E12 two-site loading term", "ACCEPT" if het else "REJECT",
                      f"Freundlich {pooled['slope']:.2f} [{pooled['ci_lo']:.2f}, {pooled['ci_hi']:.2f}]; LOPO SSE one-site "
                      f"{one:.1f} vs two-site {two:.1f}")
    print(verdict); print(EFF.to_string()); print(pooled, one, two)


if __name__ == "__main__":
    run()
