"""E16 -- transfer tests that match real use (Addendum 1). EXPLORATORY; development papers only.

(a) leave one MINERAL out (a known sorbate on a new mineral), (b) leave one SORBATE out (a new sorbate on
known minerals). E1 (core covariates; no descriptors exist yet) vs B4 (sorbate class x direction mean of
the other units) and B5 (global mean). Report only; "useful" = median edge error below B4 with the paired
95% interval excluding zero (experiments.yaml e16).
"""
import os

import pandas as pd

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info

OUT = os.path.join(EXP_DIR, "E16")


def run(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    B = ecfg["harness"]["paper_bootstrap_B"]
    curves, obs = build(purpose="E16")
    stamp = exp_stamp(extra={"experiment": "E16"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    _, c = E1.main_set(curves, ecfg["e1"])
    summ, diffs = [], []
    os.makedirs(OUT, exist_ok=True)
    for level in ("mineral", "sorbate"):
        cache = os.path.join(OUT, f"cv_leave_one_{level}_out.csv")
        cc = c.assign(paper_unit=c["unit"], unit=c[level])
        if os.path.exists(cache):
            P = pd.read_csv(cache)
        else:
            P = E1.cross_validate(cc, obs, ecfg["e1"], covariates=True, seed=seed)
            P.to_csv(cache, index=False)
        cb = H.prepare(cc, "pH_native")
        base = H.baseline_predictions(cb, unit_col="unit")
        base = base.merge(P[["curve_id", "pred_edge", "edge_lo", "edge_hi"]].rename(
            columns={"pred_edge": "E1", "edge_lo": "E1__lo", "edge_hi": "E1__hi"}), on="curve_id", how="left")
        L = H.long_errors(cb, base, ["E1", "B4_class_mean", "B5_global_mean"], unit_col="unit")
        summ.append(H.summarize(L, B=B, seed=seed).assign(left_out=level))
        diffs.append(H.paired(L, "E1", ["B4_class_mean", "B5_global_mean"], B=B, seed=seed).assign(left_out=level))
    S, D = pd.concat(summ), pd.concat(diffs)
    S.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    D.to_csv(os.path.join(OUT, "paired.csv"), index=False)
    useful = {lv: bool(((D["left_out"] == lv) & (D["baseline"] == "B4_class_mean") & (D["diff_hi"] < 0)).any())
              for lv in ("mineral", "sorbate")}
    from phslope.report import md_table
    lines = [
        "# E16 Transfer to a new mineral or a new sorbate", "",
        "**Plain English.** The realistic question is not 'predict another paper on a system we know' but "
        "'predict a mineral or sorbate nobody has measured yet'. We left out one whole mineral (or sorbate) at a "
        "time and compared the model with simple class averages. "
        f"Useful for a new mineral: **{'yes' if useful['mineral'] else 'no'}**; for a new sorbate: "
        f"**{'yes' if useful['sorbate'] else 'no'}**. No chemical descriptors exist yet (E6, E18 tables are empty), "
        "so the model can only use classes and conditions.", "",
        f"> EXPLORATORY. Development papers only. Locked set hash `{stamp['locked_set_hash']}`. Commit "
        f"`{stamp['git_commit']}`.", "",
        "## Edge error", "", md_table(S), "",
        "## E1 minus baseline (difference of medians; 95% interval over left-out minerals / sorbates)", "",
        md_table(D),
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E16", "reported", f"useful: {useful}", stamp)
    print(S.to_string())


if __name__ == "__main__":
    run()
