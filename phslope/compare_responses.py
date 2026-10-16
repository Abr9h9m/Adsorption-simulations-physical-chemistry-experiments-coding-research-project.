"""compare_responses.py -- fraction-sorbed run vs Kd run, side by side (EXPLORATORY).

    python -m phslope.compare_responses

Reads reports/phslope/ (fraction sorbed) and reports/phslope_kd/ (Kd = 1000 Sorbed / (solids Aq), response
Kd / (Kd + 1000)) and writes reports/phslope_kd/comparison/: COMPARISON_TABLES.md, one CSV per joined table,
verdicts.csv, and figures (one PNG each). Run it from any mode; it never recomputes anything.
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from phslope.common import PROJECT_ROOT

FR = os.path.join(PROJECT_ROOT, "reports", "phslope")
KD = os.path.join(PROJECT_ROOT, "reports", "phslope_kd")
OUT = os.path.join(KD, "comparison")

TABLES = [  # (file, keys, values)
    ("stage2/variance_split.csv", ["parameter", "component"], ["share", "share_lo", "share_hi"]),
    ("stage3/metrics_by_model.csv", ["level", "model"], ["n_curves", "median_p50_error", "interval_coverage"]),
    ("experiments/E1/summary_edge.csv", ["model", "subset"], ["n", "median", "median_lo", "median_hi", "coverage"]),
    ("experiments/E1/coefficients.csv", ["term"], ["estimate", "ci_lo", "ci_hi"]),
    ("experiments/E1/variance_components.csv", None, None),
    ("experiments/F/dev_summary.csv", ["model"], ["n", "median", "median_lo", "median_hi", "coverage"]),
    ("experiments/E8/effects.csv", ["analysis", "class", "outcome"], ["n", "slope", "ci_lo", "ci_hi", "q_value"]),
    ("experiments/E17/interactions.csv", ["direction", "term"], ["n", "estimate", "ci_lo", "ci_hi"]),
    ("experiments/E15/summary.csv", ["model", "split"], ["n", "median", "median_lo", "median_hi"]),
    ("experiments/E15/gbm_followup_summary.csv", None, None),
    ("experiments/E16/summary.csv", ["model", "left_out"], ["n", "median", "median_lo", "median_hi"]),
    ("experiments/E11/slope_variance.csv", ["component"], ["share"]),
    ("experiments/E11/slope_by_sorbate.csv", ["sorbate", "direction"], ["curves", "median_abs_b"]),
    ("experiments/E23_MPower/placebo_rates.csv", ["test"], ["rate"]),
    ("experiments/E14/robustness.csv", ["conclusion"], ["share_holding"]),
    ("experiments/E9/within_pair_r2.csv", ["x"], ["n", "R2", "slope_rising", "slope_falling"]),
    ("experiments/E9/breakpoints.csv", ["loading"], ["n", "breakpoint", "ci90_lo", "ci90_hi"]),
    ("experiments/E12/concentration_series_effects.csv", None, None),
    ("experiments/E21_M2_M3/summary.csv", None, None),
    ("experiments/E4/summary.csv", None, None),
    ("experiments/E2/summary.csv", None, None),
    ("experiments/E5/summary.csv", None, None),
]


def _read(root, rel):
    p = os.path.join(root, rel)
    return pd.read_csv(p) if os.path.exists(p) else None


def joined(rel, keys, vals):
    a, b = _read(FR, rel), _read(KD, rel)
    if a is None or b is None:
        return None, ("missing in " + ("fraction run" if a is None else "") + (" Kd run" if b is None else "")).strip()
    if keys is None:                                   # first text column(s) as keys, numeric columns as values
        keys = [c for c in a.columns if a[c].dtype == object and c in b.columns][:3] or [a.columns[0]]
        vals = [c for c in a.columns if c not in keys and c in b.columns and pd.api.types.is_numeric_dtype(a[c])][:6]
    keys = [k for k in keys if k in a.columns and k in b.columns]
    vals = [v for v in vals if v in a.columns and v in b.columns]
    a = a.drop_duplicates(keys)[keys + vals]
    b = b.drop_duplicates(keys)[keys + vals]
    m = a.merge(b, on=keys, how="outer", suffixes=(" [fraction]", " [Kd]"))
    cols = keys + [f"{v} [{s}]" for v in vals for s in ("fraction", "Kd")]
    return m[cols], None


def _fmt(x):
    if isinstance(x, (float, np.floating)):
        return "" if np.isnan(x) else (f"{x:.3g}" if abs(x) < 1e4 else f"{x:.0f}")
    return str(x).replace("|", "/")


def md_table(df, max_rows=40):
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for _, r in df.head(max_rows).iterrows():
        lines.append("| " + " | ".join(_fmt(v) for v in r) + " |")
    if len(df) > max_rows:
        lines.append(f"\n({len(df) - max_rows} more rows in the CSV)")
    return "\n".join(lines)


def registry(root):
    p = os.path.join(root, "experiments", "REGISTRY.md")
    rows = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            parts = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(parts) >= 6 and re.match(r"\d{4}-\d\d-\d\d", parts[0]) and parts[1] not in ("data",):
                rows.append({"experiment": parts[1], "verdict": parts[4], "note": parts[5]})
    d = pd.DataFrame(rows, columns=["experiment", "verdict", "note"])
    return d.drop_duplicates("experiment", keep="last")


def stage_verdicts():
    out = []
    for st in ("stage0", "stage1", "stage2", "stage3", "pooled"):
        row = {"stage": st}
        for lab, root in (("fraction", FR), ("Kd", KD)):
            p = os.path.join(root, st, "SUMMARY.md")
            txt = open(p, encoding="utf-8").read() if os.path.exists(p) else ""
            m = re.search(r"\*\*(PASS|FAIL|[^*]{3,80})\*\*", txt)
            row[lab] = m.group(1) if m else ("not run" if not txt else "")
        out.append(row)
    return pd.DataFrame(out)


def fig_edges():
    """Stage 1 per-curve edges: fraction vs Kd, and the shift against log10 solids."""
    a, b = _read(FR, "stage1/library/meta.csv"), _read(KD, "stage1/library/meta.csv")
    if a is None or b is None:
        return None
    m = a.merge(b, on="curve_id", suffixes=("_f", "_k"))
    m = m[m["edge_pH_f"].notna() & m["edge_pH_k"].notna()]
    ls = np.log10(m["solids_g_L_f"].where(m["solids_g_L_f"] > 0))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))
    sc = ax[0].scatter(m["edge_pH_f"], m["edge_pH_k"], c=ls, s=8, cmap="viridis")
    lim = [min(m["edge_pH_f"].min(), m["edge_pH_k"].min()), max(m["edge_pH_f"].max(), m["edge_pH_k"].max())]
    ax[0].plot(lim, lim, "k--", lw=0.8)
    ax[0].set(xlabel="edge pH, fraction sorbed", ylabel="edge pH, Kd (pH where Kd = 1000 L/kg)",
              title=f"Stage 1 edges, {len(m)} curves in both runs")
    fig.colorbar(sc, ax=ax[0], label="log10 solids (g/L)")
    d = m["edge_pH_k"] - m["edge_pH_f"]
    for shape, col in (("rising", "tab:blue"), ("falling", "tab:red")):
        s = m["shape_f"] == shape
        ax[1].scatter(ls[s], d[s], s=8, color=col, label=shape, alpha=0.7)
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set(xlabel="log10 solids (g/L)", ylabel="edge shift, Kd minus fraction (pH)",
              title="Edge shift vs solids (0 at 1 g/L)")
    ax[1].legend()
    fig.suptitle("EXPLORATORY", x=0.99, ha="right", fontsize=8, color="gray")
    fig.tight_layout()
    p = os.path.join(OUT, "fig1_edges_fraction_vs_kd.png")
    fig.savefig(p, dpi=150)
    plt.close(fig)
    m.assign(log10_solids=ls, edge_shift=d)[["curve_id", "mineral_f", "sorbate_f", "shape_f", "shape_k", "log10_solids",
                                            "edge_pH_f", "edge_pH_k", "edge_shift", "in_core_library_f",
                                            "in_core_library_k"]].to_csv(os.path.join(OUT, "stage1_edges_joined.csv"),
                                                                         index=False)
    shapes = pd.crosstab(m["shape_f"], m["shape_k"])
    shapes.to_csv(os.path.join(OUT, "stage1_shape_crosstab.csv"))
    return {"n": len(m), "corr": float(np.corrcoef(m["edge_pH_f"], m["edge_pH_k"])[0, 1]),
            "median_abs_shift": float(d.abs().median()), "shapes": shapes,
            "core_f": float(a["in_core_library"].mean()), "core_k": float(b["in_core_library"].mean()),
            "n_f": len(a), "n_k": len(b)}


def fig_bars(rel, keys, val, label, fname, title, filt=None):
    t, _ = joined(rel, keys, [val])
    if t is None:
        return
    if filt is not None:
        t = t[filt(t)]
    lab = t[keys].astype(str).agg(" / ".join, axis=1)
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(8.5, 0.35 * len(t) + 1.5))
    ax.barh(y - 0.2, t[f"{val} [fraction]"], 0.4, label="fraction sorbed", color="tab:gray")
    ax.barh(y + 0.2, t[f"{val} [Kd]"], 0.4, label="Kd", color="tab:green")
    ax.set_yticks(y, lab, fontsize=8)
    ax.invert_yaxis()
    ax.set(xlabel=label, title=title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close(fig)


def fig_coefs():
    """Solids-related coefficients with intervals, both runs."""
    rows = []
    for rel, keys, est, lo, hi, pick in (
            ("experiments/E17/interactions.csv", ["direction", "term"], "estimate", "ci_lo", "ci_hi",
             lambda t: t["term"] == "solids"),
            ("experiments/E1/coefficients.csv", ["term"], "estimate", "ci_lo", "ci_hi",
             lambda t: t["term"].str.contains("solids|log10L", regex=True))):
        for lab, root in (("fraction", FR), ("Kd", KD)):
            t = _read(root, rel)
            if t is None:
                continue
            t = t[pick(t)]
            for _, r in t.iterrows():
                rows.append({"term": rel.split("/")[1] + ": " + " / ".join(str(r[k]) for k in keys), "run": lab,
                             "est": r[est], "lo": r[lo], "hi": r[hi]})
    if not rows:
        return
    d = pd.DataFrame(rows)
    terms = list(dict.fromkeys(d["term"]))
    fig, ax = plt.subplots(figsize=(8.5, 0.5 * len(terms) + 1.5))
    for off, (lab, col) in zip((-0.15, 0.15), (("fraction", "tab:gray"), ("Kd", "tab:green"))):
        s = d[d["run"] == lab].set_index("term").reindex(terms)
        y = np.arange(len(terms)) + off
        ax.errorbar(s["est"], y, xerr=[s["est"] - s["lo"], s["hi"] - s["est"]], fmt="o", color=col, label=lab)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_yticks(np.arange(len(terms)), terms, fontsize=8)
    ax.invert_yaxis()
    ax.set(xlabel="change in log10 K level per decade of solids, 95% interval (fraction run: 1 = Kd constant; Kd run: 0 = Kd constant)",
           title="Solids effects; near 0 in the Kd run = Kd removes the solids effect")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4_solids_coefficients.png"), dpi=150)
    plt.close(fig)
    d.to_csv(os.path.join(OUT, "solids_coefficients.csv"), index=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    parts = ["# Fraction sorbed vs Kd: all tables side by side (EXPLORATORY)\n",
             "Fraction run: `reports/phslope/`. Kd run: `reports/phslope_kd/` (Kd = 1000 x Sorbed / (solids x Aq), "
             "L/kg; every edge in the Kd run is the pH where Kd = 1000 L/kg; log10 K columns there are log10 Kd in "
             "L/g, i.e. log10 Kd(L/kg) - 3). Generated by `python -m phslope.compare_responses`.\n"]
    sv = stage_verdicts()
    sv.to_csv(os.path.join(OUT, "stage_verdicts.csv"), index=False)
    parts += ["## Stage verdicts\n", md_table(sv), ""]
    rf, rk = registry(FR), registry(KD)
    v = rf.merge(rk, on="experiment", how="outer", suffixes=(" [fraction]", " [Kd]"))
    v.to_csv(os.path.join(OUT, "verdicts.csv"), index=False)
    parts += ["## Experiment verdicts (last run of each in REGISTRY.md)\n", md_table(v, 60), ""]
    e = fig_edges()
    if e:
        parts += ["## Stage 1 per-curve edges\n",
                  f"Curves in the library: fraction {e['n_f']}, Kd {e['n_k']}; in both with an edge: {e['n']}. "
                  f"Core-library share: fraction {e['core_f']:.1%}, Kd {e['core_k']:.1%}. Correlation of edges "
                  f"{e['corr']:.3f}; median absolute shift {e['median_abs_shift']:.2f} pH. Figure "
                  "`fig1_edges_fraction_vs_kd.png`.\n", "Shape class (rows fraction, columns Kd):\n",
                  md_table(e["shapes"].reset_index()), ""]
    for rel, keys, vals in TABLES:
        t, why = joined(rel, keys, vals)
        parts.append(f"## `{rel}`\n")
        if t is None:
            parts.append(f"({why})\n")
            continue
        t.to_csv(os.path.join(OUT, rel.replace("/", "__")), index=False)
        parts += [md_table(t), ""]
    fig_bars("stage2/variance_split.csv", ["parameter", "component"], "share", "share of variance",
             "fig2_stage2_variance_shares.png", "Stage 2: what explains differences between curves",
             filt=lambda t: t["parameter"] == "edge_pH")
    fig_bars("experiments/F/dev_summary.csv", ["model"], "median", "median edge error (pH)",
             "fig3_model_errors.png", "F (development papers): median edge error by model")
    fig_bars("experiments/E15/summary.csv", ["model", "split"], "median", "median per-curve RMSE (log10 K; log10 Kd in the Kd run)",
             "fig3b_bakeoff_errors.png", "E15 bake-off")
    fig_coefs()
    with open(os.path.join(OUT, "COMPARISON_TABLES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
