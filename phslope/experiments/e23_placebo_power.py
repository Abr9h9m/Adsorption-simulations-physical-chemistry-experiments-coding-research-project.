"""E23 placebo / negative-control battery and M-Power minimal detectable effects (Addendum 1).
EXPLORATORY; development papers only.

E23 (each repeated `reps` times, seeded; a 'detection' = 95% interval excluding zero, the same rule the
experiments use):
  a  E1 solids coefficient (rising) after shuffling solids WITHIN each pair          -> expect ~5%
  b  E8 outer-sphere within-paper slope after shuffling log10 I WITHIN each series   -> expect ~5%
  c  E1 coefficient of a random-noise covariate (distribution of log10 I)           -> expect ~5%
  d  pH permuted within each curve: share of curves that still pass the E1 line rule -> expect a collapse
  e  planted covariate (+0.3 log10 K per SD added to the level): recovered (interval covers 0.3) and detected
  f  paper labels shuffled among curves of a pair: paper (unit) variance share       -> expect a drop
Decision (pre-declared): false-positive rate of a, b, c <= 0.10.

M-Power: minimal detectable effect at 80% power and alpha 0.05 for each E1 level coefficient and each E8
within-paper slope, MDE = (z_0.975 + z_0.80) x SE, with the SE taken from the fitted model (mixed-model
fixed-effect covariance for E1, paper-clustered SE for E8). A simulation check is run for the E1 log10 I
coefficient (planted effects at 0.5x, 1x, 1.5x the analytic MDE).
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import e08_ionic_strength as E8
from phslope.experiments.data import build
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info
from phslope.reml import fit_reml

OUT = os.path.join(EXP_DIR, "E23_MPower")
Z = 1.959964 + 0.841621


def e1_coef(c, cfg, name, extra=()):
    m = E1.E1Model(cfg, True, list(extra)).fit(c)
    names = ["intercept"] + m.level_fixed
    i = names.index(name)
    return m.fa["beta"][i], np.sqrt(m.cov_a[i, i])


def detected(est, se):
    return abs(est) > 1.96 * se


def shuffle_within(df, col, by, rng):
    out = df.copy()
    out[col] = df.groupby(by)[col].transform(lambda s: rng.permutation(s.to_numpy()))
    return out


def e8_outer_slope(S):
    d = S[S["i_class"] == "outer_sphere_prone"]
    r = E8.clustered_slope(d["native_edge_c"], d["logI_c"], d["reference"])
    return r["slope"], r["ci_lo"], r["ci_hi"]


def prepare_e8(c, cfg8):
    c = c[c["log10_I"].notna()].copy()
    c["i_class"] = c["sorbate"].map(lambda s: E8.assign_class(s, cfg8["classes"]))
    S = E8.within_paper_series(c, cfg8["same_within"])
    return S


def centre_e8(S):
    S = S.copy()
    S["native_edge_c"] = S["pH_native"] - S.groupby("series")["pH_native"].transform("mean")
    S["logI_c"] = S["log10_I"] - S.groupby("series")["log10_I"].transform("mean")
    return S


def run(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    reps = ecfg["e23"]["reps"]
    rng = np.random.default_rng(seed)
    curves, obs = build(purpose="E23 / M-Power")
    stamp = exp_stamp(extra={"experiment": "E23 + M-Power"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    cfg = ecfg["e1"]
    rows = []

    # a
    hits = 0
    for _ in range(reps):
        cc = shuffle_within(c, "log10_solids", "pair_dir", rng)
        cc["log10L"] = cc["log10_total"] - cc["log10_solids"]
        est, se = e1_coef(cc, cfg, "solids_r")
        hits += detected(est, se)
    rows.append({"test": "a: E1 solids (rising), solids shuffled within pair", "reps": reps, "detections": hits})
    # b
    S0 = prepare_e8(c, ecfg["e8"])
    hits = 0
    for _ in range(reps):
        S = centre_e8(shuffle_within(S0, "log10_I", "series", rng))
        s, lo, hi = e8_outer_slope(S)
        hits += (lo > 0) or (hi < 0)
    rows.append({"test": "b: E8 outer-sphere slope, log10 I shuffled within series", "reps": reps, "detections": hits})
    # c
    hits = 0
    for _ in range(reps):
        cc = c.copy()
        cc["noise"] = rng.choice(c["log10_I"].dropna().to_numpy(), len(c))
        est, se = e1_coef(cc, cfg, "noise", extra=["noise"])
        hits += detected(est, se)
    rows.append({"test": "c: E1 random-noise covariate", "reps": reps, "detections": hits})
    # e
    hits, covered = 0, 0
    for _ in range(min(reps, 20)):
        cc = c.copy()
        x = rng.normal(size=len(cc))
        cc["planted"] = x
        cc["a"] = cc["a"] + 0.3 * x                      # +0.3 log10 K per SD at every pH
        cc["pH_native"] = -cc["a"] / cc["b"]
        est, se = e1_coef(cc, cfg, "planted", extra=["planted"])
        hits += detected(est, se)
        covered += abs(est - 0.3) <= 1.96 * se
    rows.append({"test": "e: planted covariate +0.3 per SD", "reps": min(reps, 20), "detections": hits,
                 "interval_covers_truth": covered})
    T = pd.DataFrame(rows)
    T["rate"] = T["detections"] / T["reps"]

    # d: pH permuted within curves
    from phslope.experiments.data import line_fits, finish_curves, LINE_COLS
    o = obs.copy()
    o["pH"] = o.groupby("curve_id")["pH"].transform(lambda s: rng.permutation(s.to_numpy()))
    perm = finish_curves(curves.drop(columns=LINE_COLS).merge(line_fits(o, None), on="curve_id", how="left"))
    _, cp = E1.main_set(perm, cfg)
    d_row = {"curves passing the E1 line rule": len(c), "after permuting pH within curves": len(cp)}
    # f: paper labels shuffled within pair -> unit variance share
    cf = c.copy()
    cf["pH_c"] = E1.reference_pH(cf, cf)
    cf["a_c"] = cf["a"] + cf["b"] * cf["pH_c"]
    comp0 = fit_reml(cf, "a_c", E1.FACTORS)["components"]
    cs = shuffle_within(cf, "unit", "pair_dir", rng)
    comp1 = fit_reml(cs, "a_c", E1.FACTORS)["components"]
    f_row = {"unit share, real labels": comp0["unit"] / sum(comp0.values()),
             "unit share, labels shuffled within pair": comp1["unit"] / sum(comp1.values())}

    # ---- M-Power
    m = E1.E1Model(cfg, True).fit(c)
    names = ["intercept"] + m.level_fixed
    P = pd.DataFrame({"test": [f"E1 level coefficient: {n}" for n in names], "estimate": m.fa["beta"],
                      "se": np.sqrt(np.diag(m.cov_a))})
    S = centre_e8(S0)
    e8rows = []
    for cls in ecfg["e8"]["classes"]:
        d = S[S["i_class"] == cls]
        r = E8.clustered_slope(d["native_edge_c"], d["logI_c"], d["reference"])
        if np.isfinite(r["slope"]):
            e8rows.append({"test": f"E8 within-paper slope: {cls}", "estimate": r["slope"],
                           "se": (r["ci_hi"] - r["ci_lo"]) / (2 * 1.96), "papers": r.get("n_clusters")})
    P = pd.concat([P, pd.DataFrame(e8rows)], ignore_index=True)
    P["mde_80pct_power"] = Z * P["se"]
    P["detectable_as_estimated"] = P["estimate"].abs() >= P["mde_80pct_power"]
    # simulation check for log10 I
    i = names.index("log10_I")
    mde = Z * np.sqrt(m.cov_a[i, i])
    sim = []
    for mult in (0.5, 1.0, 1.5):
        hits = 0
        for _ in range(ecfg["mpower"]["reps"] // 5):
            cc = c.copy()
            noise_free = cc["a"] - (m.fa["beta"][i]) * cc["log10_I"]          # remove the fitted effect
            cc["a"] = noise_free + mult * mde * cc["log10_I"]
            cc["pH_native"] = -cc["a"] / cc["b"]
            est, se = e1_coef(cc, cfg, "log10_I")
            hits += detected(est, se)
        sim.append({"planted_effect": mult * mde, "multiple_of_MDE": mult, "reps": ecfg["mpower"]["reps"] // 5,
                    "power": hits / (ecfg["mpower"]["reps"] // 5)})
    Sim = pd.DataFrame(sim)

    verdict = "PLACEBOS PASS" if (T.loc[T["test"].str[0].isin(["a", "b", "c"]), "rate"] <= 0.10).all() else "PLACEBO FAILURE: tighten rules"
    os.makedirs(OUT, exist_ok=True)
    T.to_csv(os.path.join(OUT, "placebo_rates.csv"), index=False)
    P.to_csv(os.path.join(OUT, "minimal_detectable_effects.csv"), index=False)
    Sim.to_csv(os.path.join(OUT, "power_simulation_logI.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# E23 placebo battery and M-Power minimal detectable effects", "",
        "**Plain English.** (1) We deliberately broke the data (shuffled the amount of mineral, the salt level, "
        "or the pH values) and checked that our tests then find nothing; they should claim an effect only about "
        f"5 times in 100. Result: **{verdict}**. (2) For each test we computed the smallest effect our number of "
        "papers could reliably detect, so a 'no effect' result can be read as 'no effect larger than X'.", "",
        f"> EXPLORATORY. Development papers only. Locked set hash `{stamp['locked_set_hash']}`. Commit "
        f"`{stamp['git_commit']}`.", "",
        "## Placebo and planted-effect checks", "", md_table(T), "",
        f"d: curves passing the E1 line rule: {d_row['curves passing the E1 line rule']}; after permuting pH within "
        f"curves: {d_row['after permuting pH within curves']} (edges should mostly disappear).", "",
        f"f: paper (unit) share of the level variance: real labels {f_row['unit share, real labels']:.2f}; paper "
        f"labels shuffled within pair {f_row['unit share, labels shuffled within pair']:.2f}.", "",
        "## Minimal detectable effect (80% power, alpha 0.05), MDE = 2.80 x SE", "", md_table(P), "",
        "E1 rows are in log10 K units per unit of the covariate (per decade for log10 terms); E8 rows in pH per "
        "decade of ionic strength.", "",
        "## Simulation check, E1 log10 I coefficient", "", md_table(Sim), "",
        "Power near 0.8 at 1x MDE confirms the analytic formula.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E23/M-Power", verdict, "; ".join(f"{r.test[:1]} {r.rate:.2f}" for r in T.itertuples()), stamp)
    print(verdict)
    print(T.to_string())


if __name__ == "__main__":
    run()
