"""E3 -- duplicate and outlier audit (protocol section 5, E3). Development papers only.

Duplicates: within each (mineral, sorbate), every pair of curves is compared point by point. A
point matches if the other curve has a point within match_pH in pH and match_f in fraction sorbed.
A pair is flagged when >= match_share of the SHORTER curve's points match. Papers linked by a
flagged cross-paper pair form a LINEAGE CLUSTER (connected components); later experiments leave
out a lineage cluster as one unit.

Validity rules: flags in `data_flag` (semicolon list); nothing is dropped.

Outlier review (pages + review table with empty verdict columns for Samuel / Abraham) is written
by `outlier_review`, after E1 provides model residuals.
"""
import os

import numpy as np
import pandas as pd

from phslope.experiments import harness as H
from phslope.experiments.data import build
from phslope.experiments.registry import EXP_DIR, exp_stamp, load_exp_config, log_run, write_run_info

OUT = os.path.join(EXP_DIR, "E3")


def match_share(a, b, tol_pH, tol_f):
    """Share of points of the shorter curve that have a match in the other. a, b: (n, 2) arrays."""
    s, l = (a, b) if len(a) <= len(b) else (b, a)
    if not len(s):
        return 0.0
    hit = (np.abs(s[:, None, 0] - l[None, :, 0]) <= tol_pH) & (np.abs(s[:, None, 1] - l[None, :, 1]) <= tol_f)
    return float(hit.any(axis=1).mean())


def duplicate_pairs(curves, obs, cfg):
    pts = {cid: g[["pH", "response"]].to_numpy(float) for cid, g in obs.groupby("curve_id")}
    ref = curves.set_index("curve_id")["reference"]
    rows = []
    for (m, s), g in curves.groupby(["mineral", "sorbate"]):
        ids = [c for c in g["curve_id"] if c in pts]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                sh = match_share(pts[ids[i]], pts[ids[j]], cfg["match_pH"], cfg["match_f"])
                if sh >= cfg["match_share"]:
                    rows.append({"curve_a": ids[i], "curve_b": ids[j], "mineral": m, "sorbate": s,
                                 "reference_a": ref[ids[i]], "reference_b": ref[ids[j]], "match_share": sh,
                                 "cross_paper": ref[ids[i]] != ref[ids[j]]})
    return pd.DataFrame(rows, columns=["curve_a", "curve_b", "mineral", "sorbate", "reference_a", "reference_b",
                                       "match_share", "cross_paper"])


def lineage_clusters(references, dup):
    """Union-find over papers linked by a cross-paper duplicate."""
    parent = {r: r for r in references}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for r in dup[dup["cross_paper"]].itertuples():
        a, b = find(r.reference_a), find(r.reference_b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    out = pd.DataFrame({"reference": list(references)})
    out["lineage_cluster"] = out["reference"].map(find)
    out["cluster_size"] = out.groupby("lineage_cluster")["reference"].transform("size")
    return out


def validity_flags(curves, obs, cfg):
    v = cfg["validity"]
    g = obs.groupby("curve_id")
    stats = pd.DataFrame({"f_min": g["response"].min(), "f_max": g["response"].max(),
                          "n_distinct_pH": g["pH"].apply(lambda s: s.round(2).nunique()),
                          "obs_pH_min": g["pH"].min(), "obs_pH_max": g["pH"].max()})
    c = curves.set_index("curve_id").join(stats)
    s0 = pd.read_csv(os.path.join(EXP_DIR, "..", "stage0", "curves.csv"), usecols=["curve_id", "n_bad_ph"])
    c = c.join(s0.set_index("curve_id"))
    rules = {
        "f_out_of_range": (c["f_min"] < v["f_range"][0]) | (c["f_max"] > v["f_range"][1]),
        "response_maybe_percent": c["f_max"] > v["percent_response_max"],
        "pH_out_of_range": (c["obs_pH_min"] < 0) | (c["obs_pH_max"] > 14) | (c["n_bad_ph"] > 0),
        "solids_nonpositive_or_implausible": (c["solids_g_L"] <= 0) | (c["solids_g_L"] > v["solids_max_g_L"]),
        "total_sorbate_nonpositive": c["total_sorbate_mol_L"] <= 0,
        "ionic_strength_not_finite": ~np.isfinite(c["ionic_strength"]),
        "slope_sign_contradicts_shape": c["shape"].isin(["rising", "falling"]) & c["b"].notna() & ~c["line_dir_ok"],
        "fewer_than_3_pH_values": c["n_distinct_pH"] < 3,
    }
    flags = pd.DataFrame(rules).fillna(False)
    c["data_flag"] = flags.apply(lambda r: ";".join(k for k, x in r.items() if x), axis=1)
    return c[["data_flag"]].reset_index(), flags.sum().rename("curves_flagged").reset_index()


def agreement_with_units(curves, unit_col):
    """B0-B3 benchmark on development core single-edge curves, leaving out `unit_col` units."""
    c = H.prepare(curves[curves["in_core_library"].astype(bool) & curves["shape"].isin(["rising", "falling"])],
                  "logistic_p50")
    c = c[c.groupby("grp")[unit_col].transform("nunique") >= 2].reset_index(drop=True)
    p = H.baseline_predictions(c, unit_col=unit_col)
    L = H.long_errors(c, p, H.BASELINES[:4], unit_col=unit_col)
    s = H.summarize(L, B=0)
    s.insert(0, "leave_out_unit", unit_col)
    return s


def run():
    ecfg = load_exp_config()
    cfg = ecfg["e3"]
    curves, obs = build(purpose="E3")
    stamp = exp_stamp(extra={"experiment": "E3"})
    write_run_info(OUT, stamp)
    dup = duplicate_pairs(curves, obs, cfg)
    dup.to_csv(os.path.join(OUT, "duplicate_pairs.csv"), index=False)
    lin = lineage_clusters(sorted(curves["reference"].unique()), dup)
    lin.to_csv(os.path.join(OUT, "lineage_clusters.csv"), index=False)
    flags, flag_counts = validity_flags(curves, obs, cfg)
    flags.to_csv(os.path.join(OUT, "data_flags.csv"), index=False)
    flag_counts.to_csv(os.path.join(OUT, "data_flag_counts.csv"), index=False)
    curves = curves.merge(lin[["reference", "lineage_cluster"]], on="reference")
    comp = pd.concat([agreement_with_units(curves, "reference"), agreement_with_units(curves, "lineage_cluster")])
    comp.to_csv(os.path.join(OUT, "benchmark_paper_vs_lineage.csv"), index=False)

    multi = lin[lin["cluster_size"] > 1]
    from phslope.report import md_table
    lines = [
        "# E3 Duplicate and validity audit", "",
        "**Plain English.** We looked for the same experiment appearing twice in the dataset (for example a "
        "figure re-used in a later paper), because copies make different papers look like they agree. "
        f"We found {int(dup['cross_paper'].sum())} curve pairs that are near-copies across different papers and "
        f"{int((~dup['cross_paper']).sum())} within the same paper. Papers linked by copies are now treated as "
        f"one source when testing predictions ({len(multi['lineage_cluster'].unique())} such groups covering "
        f"{len(multi)} papers). We also flagged curves that break simple validity rules; nothing was deleted.", "",
        f"> EXPLORATORY. Development papers only (locked set hash `{stamp['locked_set_hash']}`). Commit "
        f"`{stamp['git_commit']}`.", "",
        "## Duplicates", "",
        f"Rule: points match within {cfg['match_pH']} pH and {cfg['match_f']} fraction sorbed; a pair is flagged "
        f"when at least {cfg['match_share']:.0%} of the shorter curve's points match. Flagged pairs: {len(dup)} "
        f"({int(dup['cross_paper'].sum())} across papers). Table: `duplicate_pairs.csv`.", "",
        md_table(dup[dup["cross_paper"]].head(25)), "",
        "## Lineage clusters", "",
        f"{lin['lineage_cluster'].nunique()} clusters from {len(lin)} papers; {len(multi)} papers sit in "
        f"{multi['lineage_cluster'].nunique()} multi-paper clusters. Table: `lineage_clusters.csv`.", "",
        "## Agreement benchmark: leaving out papers vs leaving out lineage clusters", "",
        "Core single-edge development curves in groups with >= 2 units (edge = logistic p50). If duplicates "
        "inflated cross-paper agreement, errors rise when copies can no longer be used to predict each other.", "",
        md_table(comp), "",
        "## Validity flags (counts of curves; nothing dropped)", "",
        md_table(flag_counts), "",
        "Per-curve flags: `data_flags.csv` (column `data_flag`).", "",
        "## Outlier review", "",
        "Pages and the review table are added after E1 (they need the E1 residuals): `outlier_pages.pdf`, "
        "`outlier_review.csv` with empty `reviewer`, `verdict`, `notes` columns for Samuel or Abraham. "
        "Sensitivity runs excluding verdict = data error wait for those verdicts.",
    ]
    with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log_run("E3", "done (no decision rule)", f"{len(dup)} duplicate pairs, {int(dup['cross_paper'].sum())} cross-paper; "
            f"{len(multi)} papers in multi-paper lineage clusters", stamp)
    print(f"E3: {len(dup)} duplicate pairs ({int(dup['cross_paper'].sum())} cross-paper); "
          f"{len(multi)} papers in multi-paper clusters")
    print(comp.to_string())
    return dup, lin, flags


if __name__ == "__main__":
    run()
