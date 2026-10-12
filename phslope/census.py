"""census.py -- Stage 0: counts, coverage, gap list, descriptor templates.

Run from the project root:
    python -m phslope.census [--data PATH]
Writes reports/phslope/stage0/ (tables, SUMMARY.md, RUN_INFO.json) and
data/descriptors/*_template.csv.

Counting rules (thresholds.yaml, stage0): a mineral-sorbate pair passes if its
CLEAN pH-sweep curves together have >= pair_min_points usable points, a pooled
pH span >= pair_min_ph_span, and >= pair_min_references distinct references.
A clean curve is a ph_sweep curve without unit_mismatch or conditions_vary.
All counts are recomputed from raw rows; nothing is read from older audit tables.
"""
import argparse
import os

import pandas as pd

from phslope.common import (DESCRIPTOR_DIR, REPORTS_DIR, load_config, load_thresholds,
                            run_stamp, write_stamp)
from phslope.curves import build_curves, signature_fragmentation
from phslope.load import load_observations, unit_report

MINERAL_DESCRIPTOR_COLS = ["mineral", "mineral_class", "formula", "pzc_low", "pzc_high", "pzc_source",
                           "surface_area_m2_g", "surface_area_source", "notes"]
SORBATE_DESCRIPTOR_COLS = ["sorbate", "element", "oxidation_state", "speciation_class",
                           "first_hydrolysis_logK", "hydrolysis_source", "notes"]

# Earlier pipeline subsets (mineral, electrolyte signature, sorbate) -> raw row count.
# The spec quotes 205 for goethite-N+Na-U(VI); the raw group has 275 rows (205 was
# after run_pipeline's I-varying-reference filter). See SUMMARY.md.
KNOWN_SUBSET_ROWS = {
    ("goethite", "Cl(-1)+Na(+1)+P(+5)", "Se(+4)"): 104,
    ("ferrihydrite", "N(+5)+Na(+1)+P(+5)", "U(+6)"): 105,
    ("montmorillonite", "Cl(-1)+Na(+1)", "U(+6)"): 66,
    ("goethite", "N(+5)+Na(+1)", "U(+6)"): 275,
}


def clean_curves(curves):
    return curves[(curves["kind"] == "ph_sweep") & ~curves["unit_mismatch"] & ~curves["conditions_vary"]]


def pair_table(curves, thr):
    c = clean_curves(curves)
    g = c.groupby(["mineral", "sorbate"])
    t = pd.DataFrame({
        "n_curves": g.size(),
        "n_points": g["n_points"].sum(),
        "pH_min": g["pH_min"].min(),
        "pH_max": g["pH_max"].max(),
        "n_references": g["reference"].nunique(),
        "n_curves_solids_reported": g["solids_reported"].sum(),
        "n_curves_total_reported": g["total_sorbate_reported"].sum(),
        "n_curves_both_reported": g.apply(lambda d: (d["solids_reported"] & d["total_sorbate_reported"]).sum(),
                                          include_groups=False),
        "n_curves_cosolute": g["has_cosolute"].sum(),
        "n_curves_co2": g["co2_present"].sum(),
    }).reset_index()
    t["pH_span"] = t["pH_max"] - t["pH_min"]
    t["passes"] = ((t["n_points"] >= thr["pair_min_points"]) & (t["pH_span"] >= thr["pair_min_ph_span"])
                   & (t["n_references"] >= thr["pair_min_references"]))
    return t.sort_values("n_points", ascending=False).reset_index(drop=True)


def gap_reason(row, thr):
    if row is None or row["n_curves"] == 0:
        return "empty"
    reasons = []
    if row["n_points"] < thr["pair_min_points"]:
        reasons.append(f"points {int(row['n_points'])}<{thr['pair_min_points']}")
    if row["pH_span"] < thr["pair_min_ph_span"]:
        reasons.append(f"pH span {row['pH_span']:.1f}<{thr['pair_min_ph_span']}")
    if row["n_references"] < thr["pair_min_references"]:
        reasons.append(f"references {int(row['n_references'])}<{thr['pair_min_references']}")
    return "; ".join(reasons)


def gap_list(pairs, n_min, n_sorb, thr):
    """Empty or thin cells inside the dense block (top minerals x top sorbates by usable points)."""
    top_m = pairs.groupby("mineral")["n_points"].sum().nlargest(n_min).index
    top_s = pairs.groupby("sorbate")["n_points"].sum().nlargest(n_sorb).index
    idx = pairs.set_index(["mineral", "sorbate"])
    rows = []
    for m in top_m:
        for s in top_s:
            row = idx.loc[(m, s)] if (m, s) in idx.index else None
            if row is not None and row["passes"]:
                continue
            rows.append({"mineral": m, "sorbate": s,
                         "n_curves": 0 if row is None else int(row["n_curves"]),
                         "n_points": 0 if row is None else int(row["n_points"]),
                         "reason": gap_reason(row, thr)})
    return pd.DataFrame(rows), list(top_m), list(top_s)


def descriptor_templates(curves, out_dir):
    """One row per mineral / sorbate in the data, descriptor columns empty.
    Writes *_template.csv every run; never overwrites the human-filled files."""
    os.makedirs(out_dir, exist_ok=True)
    minerals = sorted(curves["mineral"].dropna().unique())
    sorbates = sorted(curves["sorbate"].dropna().unique())
    m = pd.DataFrame({c: "" for c in MINERAL_DESCRIPTOR_COLS}, index=range(len(minerals)))
    m["mineral"] = minerals
    s = pd.DataFrame({c: "" for c in SORBATE_DESCRIPTOR_COLS}, index=range(len(sorbates)))
    s["sorbate"] = sorbates
    written = []
    for df, name in ((m, "mineral_descriptors"), (s, "sorbate_descriptors")):
        df.to_csv(os.path.join(out_dir, f"{name}_template.csv"), index=False)
        written.append(f"{name}_template.csv")
        filled = os.path.join(out_dir, f"{name}.csv")
        if not os.path.exists(filled):
            df.to_csv(filled, index=False)
            written.append(f"{name}.csv (new, for Samuel to fill)")
    return written


def known_subset_check(obs):
    rows = []
    for (m, sig, s), expected in KNOWN_SUBSET_ROWS.items():
        n = int(((obs["Mineral"] == m) & (obs["electrolyte_sig"] == sig) & (obs["Sorbate"] == s)).sum())
        rows.append({"mineral": m, "electrolyte_sig": sig, "sorbate": s, "expected": expected, "found": n,
                     "ok": n == expected})
    return pd.DataFrame(rows)


def _md(df):
    """Markdown table without the optional `tabulate` dependency."""
    if not len(df):
        return "_(none)_"
    fmt = lambda v: f"{v:.2f}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def write_summary(path, ctx):
    t, thr = ctx["pairs"], ctx["thr"]
    n_pass = int(t["passes"].sum())
    verdict = "PASS" if n_pass >= thr["min_passing_pairs"] else "FAIL"
    kinds = ctx["curves"]["kind"].value_counts().to_dict()
    c = ctx["curves"]
    sw = c[c["kind"] == "ph_sweep"]
    frag = ctx["frag"]
    lines = [
        "# Stage 0 summary: census and clean systems table",
        "",
        f"Run: commit `{ctx['stamp']['git_commit']}`, config `{ctx['stamp']['config_hash']}`, "
        f"data `{ctx['stamp']['data_file']}`, {ctx['stamp']['run_at_utc']}.",
        "",
        "## Result",
        "",
        f"**{verdict}.** {n_pass} mineral-sorbate pairs meet the rule "
        f"(>= {thr['pair_min_points']} usable points, pooled pH span >= {thr['pair_min_ph_span']}, "
        f">= {thr['pair_min_references']} references). The stage needs >= {thr['min_passing_pairs']}.",
        "",
        f"Pairs passing when only curves reporting both solids loading and total sorbate are counted: "
        f"{int(ctx['pairs_reported']['passes'].sum())}.",
        "",
        "## Data loaded",
        "",
        f"- Rows: {ctx['units']['rows']:,}. (The handoff said ~80k; this file has fewer.)",
        f"- Rows with pH missing or outside [0, 14] (flagged `bad_ph`, kept but not used): {ctx['units']['bad_ph']}.",
        f"- Rows with no fraction-sorbed response: {ctx['units']['response_missing']:,}.",
        f"- Total-sorbate units: {ctx['units']['sorbate_units']} (converted to mol/L).",
        f"- Solids-loading units: {ctx['units']['solids_units']}. g/L, mg/mL and mg/L are converted to g/L; "
        f"m2/L is kept separately; {ctx['units']['solids_unconvertible']} rows have a unit that cannot be "
        "converted (cm3/g, L/kg) and are left missing.",
        "",
        "## Curves (one curve = one `Set`; provisional, see phslope/README.md)",
        "",
        f"- Sets by kind: {kinds}.",
        f"- pH-sweep curves: {len(sw):,}; with conditions that vary inside the curve: "
        f"{int(sw['conditions_vary'].sum())}; flagged unit_mismatch: {int(sw['unit_mismatch'].sum())}; "
        f"clean: {len(clean_curves(c)):,}.",
        f"- Clean curves: median {clean_curves(c)['n_points'].median():.0f} points, "
        f"median pH span {clean_curves(c)['pH_span'].median():.2f}.",
        f"- Clean curves with a co-solute in the electrolyte (not plain background salt): "
        f"{int(clean_curves(c)['has_cosolute'].sum())}; with CO2/carbonate: {int(clean_curves(c)['co2_present'].sum())}.",
        f"- Clean curves reporting solids loading: {int(clean_curves(c)['solids_reported'].sum())}; "
        f"total sorbate: {int(clean_curves(c)['total_sorbate_reported'].sum())}; "
        f"temperature: {int(clean_curves(c)['temp'].notna().sum())}.",
        "",
        "## Task 0.4: electrolyte-signature fragmentation",
        "",
        f"{int((frag['n_signatures'] > 1).sum())} (reference, mineral, sorbate) studies are split across more than "
        "one electrolyte signature. Because a curve is a Set, the split never cuts a curve in two; it only "
        "matters if signature were used to group curves. It is not: pairs are (mineral, sorbate) and the "
        "signature is kept as a reported column plus `has_cosolute`. Largest splits:",
        "",
        _md(frag[frag["n_signatures"] > 1].head(8)[["reference", "mineral", "sorbate", "n_signatures",
                                                     "n_curves", "n_points", "cosolutes"]]),
        "",
        "Most extra signature members are co-solutes (phosphate, sulfate, humic acid, a second sorbate), "
        "which change the chemistry, not tracer ions. Whether to exclude co-solute curves from the core "
        "library is an open question (OPEN_QUESTIONS.md).",
        "",
        "## Known subset row counts (Task 0.1 check)",
        "",
        _md(ctx["known"]),
        "",
        "The spec quoted 205 rows for goethite-N(+5)+Na(+1)-U(+6). The raw group has 275 rows from 4 references; "
        "205 was the count after `run_pipeline.py`'s I-varying-reference filter, so 275 is the correct raw check.",
        "",
        "## Top pairs",
        "",
        _md(t.head(25)[["mineral", "sorbate", "n_curves", "n_points", "pH_span", "n_references",
                        "n_curves_both_reported", "passes"]]),
        "",
        f"Full table: `pair_table.csv`. Matrices: `matrix_curves.csv`, `matrix_references.csv`. "
        f"Gap list (dense block {len(ctx['top_m'])} minerals x {len(ctx['top_s'])} sorbates): `gap_list.csv` "
        f"({len(ctx['gaps'])} empty or thin cells).",
        "",
        "## Descriptor templates",
        "",
        "Written to data/descriptors/: " + ", ".join(ctx["templates"]) + ". All descriptor columns are empty; "
        "Samuel fills them with cited sources.",
        "",
        "## Next decision",
        "",
        "Samuel confirms the curve definition (one curve = one Set) and the co-solute question before Stage 1. "
        + ("Stage 0 passes, so Stage 1 can start after that confirmation." if verdict == "PASS" else
           "Stage 0 FAILS the pair-count rule: stop here and decide whether to relax the rule or narrow the question."),
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return verdict, n_pass


def run(data_file=None, out_dir=None):
    config, thr_all = load_config(), load_thresholds()
    thr = thr_all["stage0"]
    out_dir = out_dir or os.path.join(REPORTS_DIR, "stage0")
    os.makedirs(out_dir, exist_ok=True)

    obs, path = load_observations(data_file, config)
    stamp = run_stamp(path)
    write_stamp(out_dir, stamp)

    curves, curve_obs = build_curves(obs, config)
    frag = signature_fragmentation(obs, curves)
    pairs = pair_table(curves, thr)
    both = curves[curves["solids_reported"] & curves["total_sorbate_reported"]]
    pairs_reported = pair_table(both, thr)
    gaps, top_m, top_s = gap_list(pairs, config["census"]["dense_block_minerals"],
                                  config["census"]["dense_block_sorbates"], thr)
    templates = descriptor_templates(curves, DESCRIPTOR_DIR)

    curves.to_csv(os.path.join(out_dir, "curves.csv"), index=False)
    pairs.to_csv(os.path.join(out_dir, "pair_table.csv"), index=False)
    pairs_reported.to_csv(os.path.join(out_dir, "pair_table_conditions_reported.csv"), index=False)
    pairs.pivot(index="mineral", columns="sorbate", values="n_curves").to_csv(os.path.join(out_dir, "matrix_curves.csv"))
    pairs.pivot(index="mineral", columns="sorbate", values="n_references").to_csv(
        os.path.join(out_dir, "matrix_references.csv"))
    gaps.to_csv(os.path.join(out_dir, "gap_list.csv"), index=False)
    frag.to_csv(os.path.join(out_dir, "signature_fragmentation.csv"), index=False)

    ctx = dict(pairs=pairs, pairs_reported=pairs_reported, thr=thr, curves=curves, frag=frag, gaps=gaps,
               top_m=top_m, top_s=top_s, templates=templates, units=unit_report(obs),
               known=known_subset_check(obs), stamp=stamp)
    verdict, n_pass = write_summary(os.path.join(out_dir, "SUMMARY.md"), ctx)
    print(f"Stage 0 {verdict}: {n_pass} passing pairs -> {out_dir}")
    return ctx


def main():
    ap = argparse.ArgumentParser(description="Stage 0 census.")
    ap.add_argument("--data", help="path to the raw CSV (overrides SORPTION_DATA_FILE)")
    ap.add_argument("--out", help="output directory (default reports/phslope/stage0)")
    args = ap.parse_args()
    run(args.data, args.out)


if __name__ == "__main__":
    main()
