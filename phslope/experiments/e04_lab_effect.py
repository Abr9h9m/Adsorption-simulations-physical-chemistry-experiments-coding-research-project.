"""E4 -- lab or research-group effect (protocol section 5, E4). EXPLORATORY; development papers only.

Group IDs: the raw file has no bibliographic fields (E0.1), so labs are a WEAK PROXY from the reference
code (letters = author initials, digits = year):
  lab_exact   the full letter prefix (same set of author initials). Splits a lab whose author lists
              vary; never merges different initials. Bias: under-counts same-lab pairs.
  lab_coarse  the first two letters. Merges unrelated authors with the same initials. Bias: over-counts.
Tests
  1. Lab random effect added to the E1 level model (crossed with paper): variance share, and whether
     the paper (unit) share falls.
  2. Matched-gain survival: B0-B3 with the matched curve required to come from a DIFFERENT lab (and a
     different lineage cluster). Decision (pre-declared): B3 still beats B0 (paired 95% interval below
     zero) AND median error <= 0.5 pH.
  3. Same-lab vs different-lab cross-paper curve pairs: edge difference after adjusting for solids
     (direction-specific), compared between the two kinds of pairs.
"""
import os
import re

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from phslope.experiments import e01_logk_mixed as E1
from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.registry import (EXP_DIR, exp_stamp, load_exp_config, log_run, record_adjustment,
                                          write_run_info)
from phslope.reml import fit_reml

OUT = os.path.join(EXP_DIR, "E4")


def lab_ids(refs):
    def letters(r):
        m = re.match(r"[A-Za-z]+", str(r))
        return m.group(0).lower() if m else str(r)
    s = pd.Series(list(refs), index=list(refs))
    return pd.DataFrame({"reference": s.index, "lab_exact": s.map(letters).to_numpy(),
                         "lab_coarse": s.map(lambda r: letters(r)[:2]).to_numpy()})


def survival(curves, lab_col, B, seed):
    c = H.prepare(curves[curves["in_core_library"].astype(bool) & curves["shape"].isin(["rising", "falling"])],
                  "logistic_p50")
    c = c[c.groupby("grp")["unit"].transform("nunique") >= 2].reset_index(drop=True)
    base = H.baseline_predictions(c, unit_col="unit")
    excl = H.baseline_predictions(c, unit_col="unit", also_differ=(lab_col,))
    out = []
    for name, p in (("any lab", base), (f"different lab ({lab_col})", excl)):
        L = H.long_errors(c, p, H.BASELINES[:4], unit_col="unit")
        s = H.summarize(L, B=B, seed=seed).assign(matching=name)
        d = H.paired(L, "B3_matched_fb", ["B0_all_other"], B=B, seed=seed).assign(matching=name)
        out.append((s, d))
    return pd.concat([o[0] for o in out]), pd.concat([o[1] for o in out])


def lab_variance(curves, lab_col, cfg):
    _, c = E1.main_set(curves, cfg)
    c = c.copy()
    c["pH_c"] = E1.reference_pH(c, c)
    c["a_c"] = c["a"] + c["b"] * c["pH_c"]
    bp = E1.choose_breakpoint(c, cfg["hinge_grid"])
    c = E1.add_covariates(c, bp)
    fixed = [x for x in ["falling"] + E1.LEVEL_COVS if c[x].nunique(dropna=True) > 1]
    c = c.dropna(subset=fixed + ["a_c"])
    rows = []
    for label, factors in (("without lab", E1.FACTORS), ("with lab", {**E1.FACTORS, "lab": lab_col})):
        comp = fit_reml(c, "a_c", factors, fixed)["components"]
        tot = sum(comp.values())
        rows.append({"model": label, **{f"share_{k}": v / tot for k, v in comp.items()}})
    return pd.DataFrame(rows)


def same_lab_pairs(curves, lab_col):
    c = curves[curves["in_core_library"].astype(bool) & curves["shape"].isin(["rising", "falling"])].copy()
    c["grp"] = c["mineral"] + "|" + c["sorbate"] + "|" + c["shape"]
    c["e"] = c["logistic_p50"] - c.groupby("grp")["logistic_p50"].transform("mean")
    x = (c["log10_solids"] - c.groupby("grp")["log10_solids"].transform("mean")) * c["direction"]
    ok = x.notna() & c["e"].notna()
    beta = np.polyfit(x[ok], c.loc[ok, "e"], 1)
    c["resid"] = c["e"] - np.polyval(beta, x.fillna(0))
    rows = []
    for _, g in c.groupby("grp"):
        idx = g.index.to_list()
        for i in range(len(idx)):
            for j in range(i + 1, len(idx)):
                a, b = g.loc[idx[i]], g.loc[idx[j]]
                if a["unit"] == b["unit"]:
                    continue
                rows.append({"same_lab": a[lab_col] == b[lab_col], "d_resid": abs(a["resid"] - b["resid"])})
    P = pd.DataFrame(rows)
    s, d = P[P["same_lab"]]["d_resid"], P[~P["same_lab"]]["d_resid"]
    p = mannwhitneyu(s, d).pvalue if len(s) >= 5 and len(d) >= 5 else np.nan
    return {"lab_id": lab_col, "same_lab_pairs": len(s), "different_lab_pairs": len(d),
            "median_same": s.median(), "median_different": d.median(), "mannwhitney_p": p}


def run(seed=None):
    ecfg = load_exp_config()
    seed = ecfg["seed"] if seed is None else seed
    B = ecfg["harness"]["paper_bootstrap_B"]
    curves, _ = build(purpose="E4")
    stamp = exp_stamp(extra={"experiment": "E4", "lab_id": "proxy from reference code"})
    write_run_info(OUT, stamp)
    curves = E1.attach_units(curves)
    curves = curves.merge(lab_ids(curves["reference"].unique()), on="reference")
    surv, diffs, var, pairs = [], [], [], []
    for lab_col in ("lab_exact", "lab_coarse"):
        s, d = survival(curves, lab_col, B, seed)
        surv.append(s.assign(lab_id=lab_col)); diffs.append(d.assign(lab_id=lab_col))
        var.append(lab_variance(curves, lab_col, ecfg["e1"]).assign(lab_id=lab_col))
        pairs.append(same_lab_pairs(curves, lab_col))
    S, D, V, PR = pd.concat(surv), pd.concat(diffs), pd.concat(var), pd.DataFrame(pairs)

    key = D[(D["lab_id"] == "lab_exact") & D["matching"].str.startswith("different")].iloc[0]
    b3_med = S[(S["lab_id"] == "lab_exact") & S["matching"].str.startswith("different") &
               (S["model"] == "B3_matched_fb")]["median"].iloc[0]
    survives = key["diff_hi"] < 0 and b3_med <= 0.5
    verdict = "GAIN SURVIVES" if survives else "GAIN DOES NOT SURVIVE (partly a lab effect, or not significant)"
    for df, name in ((S, "survival_summary.csv"), (D, "survival_paired.csv"), (V, "lab_variance_shares.csv"),
                     (PR, "same_vs_different_lab_pairs.csv")):
        df.to_csv(os.path.join(OUT, name), index=False)
    n_labs = curves[["lab_exact", "lab_coarse"]].nunique().to_dict()
    from phslope.report import md_table
    lines = [
        "# E4 Lab (research-group) effect", "",
        "**Plain English.** Papers from the same research group often reuse the same recipe, so their curves may "
        "agree for reasons that do not carry over to other labs. We asked whether the benefit of matching "
        "experimental conditions survives when the matched paper must come from a different group. "
        f"Result (exact-initials grouping): **{verdict}**.", "",
        "> EXPLORATORY. The file has no author fields, so labs are a proxy built from the reference code "
        f"(letters = author initials). {n_labs['lab_exact']} exact-initial groups, {n_labs['lab_coarse']} "
        "first-two-letter groups. The exact proxy under-counts same-lab pairs (a lab with changing co-authors is "
        "split); the coarse proxy over-counts (unrelated authors with the same initials are merged). "
        f"Development papers only; leave-out unit = lineage cluster. Locked set hash `{stamp['locked_set_hash']}`. "
        f"Commit `{stamp['git_commit']}`.", "",
        "## 2. Matched-gain survival (core single-edge curves, logistic edge)", "",
        md_table(S[["lab_id", "matching", "model", "n", "median", "median_lo", "median_hi", "within_0_5"]]), "",
        "Paired B3 minus B0 (negative = matching helps):", "", md_table(D), "",
        f"Decision (exact proxy): paired 95% interval below zero: {'yes' if key['diff_hi'] < 0 else 'NO'}; "
        f"B3 median {b3_med:.3f} <= 0.5: {'yes' if b3_med <= 0.5 else 'NO'} -> **{verdict}**.", "",
        "## 1. Lab random effect in the E1 level model (variance shares)", "", md_table(V), "",
        "## 3. Same-lab vs different-lab cross-paper pairs (edge difference after solids adjustment)", "",
        md_table(PR), "",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E4", verdict, "lab proxy from reference code; 2 proxies", stamp)
    record_adjustment("E4 lab random effect / different-lab matching", verdict,
                      f"B3-B0 different lab (exact): {key['median_diff']:.3f} [{key['diff_lo']:.3f}, "
                      f"{key['diff_hi']:.3f}]; B3 median {b3_med:.3f}")
    print(f"E4 {verdict}")
    return S, D


if __name__ == "__main__":
    run()
