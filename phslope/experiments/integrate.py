"""integrate.py -- integration (protocol section 7, F).

    python -m phslope.experiments.integrate                 # development papers only: final model,
                                                            # ablation, baselines (safe to run any time)
    python -m phslope.experiments.integrate --open-locked-set "I understand this is the single final look"
                                                            # THE ONE-TIME locked-set evaluation

Final model = E1 core + every adjustment whose experiment met its pre-declared rule:
  E8  ionic strength x sorbate type (log10 I x outer-sphere and x oxyanion on the level)
  E7  log10 pCO2 (+ unknown-atmosphere indicator), if E7 step 1a said KEEP
  E2  line-fit weighting / window, if E2 adopted a scheme
(E5 changes QC, not the model, and needs decision D3; E9 was not adopted; E4 adds no model term.)
Ablation: each accepted adjustment dropped in turn; change in held-out median edge error (difference of
medians, 95% interval over units). Development results are EXPLORATORY.
"""
import argparse
import os

import numpy as np
import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import harness as H
from phslope.experiments.data import build, refit_lines
from phslope.experiments.e07_carbonate import carbonate_columns
from phslope.experiments.e08_ionic_strength import assign_class
from phslope.experiments.registry import (EXP_DIR, exp_stamp, final_papers, load_exp_config, log_run,
                                          write_run_info)

OUT = os.path.join(EXP_DIR, "F")
CONFIRM = "I understand this is the single final look"


def accepted_adjustments():
    """Read each experiment's saved decision. Returns {name: spec}."""
    acc = {}
    e8 = os.path.join(EXP_DIR, "E8", "SUMMARY.md")
    if os.path.exists(e8) and "EFFECT FOUND" in open(e8, encoding="utf-8").read():
        acc["E8 ionic strength x sorbate type"] = {"covs": ["logI_outer", "logI_oxy"]}
    e7 = os.path.join(EXP_DIR, "E7", "SUMMARY.md")
    if os.path.exists(e7) and "**KEEP log10 pCO2**" in open(e7, encoding="utf-8").read():
        acc["E7 log10 pCO2"] = {"covs": ["log10_pco2_f", "atmosphere_unknown"]}
    if os.path.exists(os.path.join(EXP_DIR, "E23_MPower", "SUMMARY.md")):
        acc["E1 within-between solids (E23)"] = {"within_between": ["solids_r", "solids_f"]}
    e2 = os.path.join(EXP_DIR, "E2", "scheme_summary.csv")
    if os.path.exists(e2):
        s = pd.read_csv(e2)
        win = s[s["meets_rule"].astype(bool)].sort_values("median_logK_rmse")
        if len(win):
            acc["E2 " + win["scheme"].iloc[0]] = {"scheme": win["scheme"].iloc[0]}
    return acc


def scheme_lines(curves, obs, scheme):
    from phslope.experiments import e02_weights_censoring as E2
    if scheme.startswith("W2"):
        return refit_lines(curves, obs, (0.03, 0.97), E2.weight_W2)
    if scheme.startswith("W1"):
        return refit_lines(curves, obs, (0.03, 0.97), E2.weight_W1(E2.empirical_error_model(curves, obs)))
    if scheme.startswith("W0"):
        lo, hi = [float(x) for x in scheme.split("(")[1].rstrip(")").split(",")]
        return refit_lines(curves, obs, (lo, hi), None)
    raise ValueError(scheme)


def prepare(curves, obs, ecfg, adjustments):
    c = carbonate_columns(E1.attach_units(curves), ecfg["e7"]["pco2_floor_log10"])
    for name, spec in adjustments.items():
        if "scheme" in spec:
            c = scheme_lines(c, obs, spec["scheme"])
    cls = c["sorbate"].map(lambda s: assign_class(s, ecfg["e8"]["classes"]))
    c["logI_outer"] = c["log10_I"] * (cls == "outer_sphere_prone")
    c["logI_oxy"] = c["log10_I"] * (cls == "oxyanion")
    _, main = E1.main_set(c, ecfg["e1"])
    return main


def evaluate(c, obs, ecfg, covs, seed, wb=()):
    return E1.cross_validate(c, obs, ecfg["e1"], covariates=True, seed=seed, extra_covs=covs, within_between=wb)


def run_dev(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    B = ecfg["harness"]["paper_bootstrap_B"]
    curves, obs = build(purpose="F development")
    acc = accepted_adjustments()
    stamp = exp_stamp(extra={"experiment": "F (development only)", "accepted_adjustments": list(acc)})
    write_run_info(OUT, stamp)
    c = prepare(curves, obs, ecfg, acc)
    all_covs = [x for spec in acc.values() for x in spec.get("covs", [])]
    all_wb = [x for spec in acc.values() for x in spec.get("within_between", [])]
    variants = {"final model": (all_covs, all_wb), "E1 core only": ([], [])}
    for name, spec in acc.items():
        if spec.get("covs") or spec.get("within_between"):
            variants[f"final without {name}"] = ([x for x in all_covs if x not in spec.get("covs", [])],
                                                [x for x in all_wb if x not in spec.get("within_between", [])])
    preds = {}
    for name, (covs, wb) in variants.items():
        cache = os.path.join(OUT, "cv_" + "".join(ch if ch.isalnum() else "_" for ch in name) + ".csv")
        if os.path.exists(cache):
            preds[name] = pd.read_csv(cache)
            continue
        print(f"F: {name}")
        preds[name] = evaluate(c, obs, ecfg, covs, seed, wb)
        os.makedirs(OUT, exist_ok=True)
        preds[name].to_csv(cache, index=False)
    cb = H.prepare(c, "pH_native")
    base = H.baseline_predictions(cb, unit_col="unit")
    for name, P in preds.items():
        base = base.merge(P[["curve_id", "pred_edge", "edge_lo", "edge_hi"]].rename(
            columns={"pred_edge": name, "edge_lo": f"{name}__lo", "edge_hi": f"{name}__hi"}), on="curve_id", how="left")
    models = list(preds) + H.BASELINES
    L = H.long_errors(cb, base, models, unit_col="unit")
    multi = set(cb.loc[cb.groupby("grp")["unit"].transform("nunique") >= 2, "curve_id"])
    Lm = L[L["curve_id"].isin(multi)]
    S = H.summarize(Lm, B=B, seed=seed)
    abl = H.paired(Lm, "final model", [m for m in preds if m != "final model"] + H.BASELINES, B=B, seed=seed)
    os.makedirs(OUT, exist_ok=True)
    S.to_csv(os.path.join(OUT, "dev_summary.csv"), index=False)
    abl.to_csv(os.path.join(OUT, "dev_ablation_and_baselines.csv"), index=False)
    L.to_csv(os.path.join(OUT, "dev_per_curve.csv"), index=False)
    from phslope.report import md_table
    lines = [
        "# F Integration on development papers (locked set NOT opened)", "",
        "**Plain English.** We combined the core model from E1 with every correction that passed its own test, "
        "then removed each correction in turn to see whether it still helps. This is all on the development "
        "papers; the 24 locked papers have not been looked at.", "",
        f"> EXPLORATORY. Locked set hash `{stamp['locked_set_hash']}` (not opened). Commit `{stamp['git_commit']}`.", "",
        "Accepted adjustments included: " + (", ".join(acc) if acc else "none") + ".", "",
        "## Held-out edge error, pairs with >= 2 units", "", md_table(S), "",
        "## Final model minus each alternative (difference of medians; negative = final better)", "", md_table(abl), "",
        "An adjustment whose removal does not make the model worse (interval including zero or positive) is a "
        "candidate for removal before the locked-set evaluation (protocol F2).", "",
        "## Locked-set evaluation", "",
        "Not run. It is run once, after E6, E10 and the full E7 (which wait for human-entered data and constants), "
        "with `python -m phslope.experiments.integrate --open-locked-set \"" + CONFIRM + "\"`.",
    ]
    with open(os.path.join(OUT, "SUMMARY_DEV.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("F-dev", "done", f"accepted: {list(acc)}", stamp)
    return S, abl


def run_locked(phrase, seed=None):
    """The single final look: fit on ALL development papers, predict the locked papers once."""
    if phrase != CONFIRM:
        raise SystemExit(f'refused: pass --open-locked-set "{CONFIRM}"')
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    locked = final_papers(confirm=True)
    curves, obs = build(include_locked=True, purpose="F: single locked-set evaluation")
    acc = accepted_adjustments()
    c = prepare(curves, obs, ecfg, acc)
    covs = [x for spec in acc.values() for x in spec.get("covs", [])]
    wb = [x for spec in acc.values() for x in spec.get("within_between", [])]
    dev, test = c[~c["reference"].isin(locked)], c[c["reference"].isin(locked)]
    m = E1.E1Model(ecfg["e1"], True, covs, wb).fit(dev)
    P = m.predict(test, np.random.default_rng(seed))
    P.to_csv(os.path.join(OUT, "LOCKED_predictions.csv"), index=False)
    log_run("F-locked", "LOCKED SET EVALUATED", f"{len(P)} curves", exp_stamp())
    print("Locked-set predictions written; write FINAL.md from LOCKED_predictions.csv")
    return P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--open-locked-set", dest="phrase")
    args = ap.parse_args()
    if args.phrase is not None:
        run_locked(args.phrase)
    else:
        run_dev()


if __name__ == "__main__":
    main()
