"""report.py -- figures and SUMMARY.md files for each stage.

Figure style: one quiet axis, light grid, thin marks; blue (#2a78d6) for the
primary estimate, orange (#eb6834) for the comparison model, gray for data.
Every figure states n in its title.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

BLUE, ORANGE, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#52514e"
FLAG_ORDER = ["fit_failed", "too_few_points", "narrow_span", "unit_mismatch", "edge_not_bracketed",
              "poor_fit", "wide_interval", "bootstrap_unstable"]


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c9c8c3")
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(True, color="#ebeae6", linewidth=0.6)
    ax.set_axisbelow(True)


def md_table(df, floatfmt="{:.3g}"):
    if df is None or not len(df):
        return "_(none)_"
    fmt = lambda v: floatfmt.format(v) if isinstance(v, (float, np.floating)) and np.isfinite(v) else (
        "" if isinstance(v, (float, np.floating)) else str(v))
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def _stamp_line(stamp):
    return (f"Run: commit `{stamp['git_commit']}`, config `{stamp['config_hash']}`, "
            f"data `{stamp['data_file']}`, {stamp['run_at_utc']}.")


def flag_table(meta):
    flags = meta["qc_flags"].fillna("").str.split(";")
    rows = []
    for f in FLAG_ORDER:
        has = flags.apply(lambda fl: f in fl)
        only = flags.apply(lambda fl: fl == [f])
        rows.append({"flag": f, "curves_with_flag": int(has.sum()), "curves_with_only_this_flag": int(only.sum())})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ synthetic

def stage1_synthetic_summary(out_dir, lib, scores, thr_all, stamp):
    thr = thr_all["stage1"]
    non_flat = scores[scores["true_shape"] != "flat"]
    med = float(non_flat["slope_error"].median())
    verdict = "PASS" if med < thr["synthetic_median_slope_error_frac"] else "FAIL"
    by_shape = scores.groupby("true_shape").agg(
        n=("curve_id", "size"), median_slope_error=("slope_error", "median"),
        median_abs_edge_error=("edge_pH", lambda s: np.nan),
        edge_interval_coverage=("edge_covered", "mean")).reset_index()
    by_shape["median_abs_edge_error"] = [
        float((scores.loc[scores.true_shape == s, "edge_pH"] - scores.loc[scores.true_shape == s, "true_edge"])
              .abs().median()) for s in by_shape["true_shape"]]
    confusion = pd.crosstab(scores["true_shape"], scores["shape"]).reset_index()
    primary = pd.crosstab(scores["true_shape"], scores["primary_model"]).reset_index()
    flags = flag_table(lib["meta"])

    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    shapes = list(by_shape["true_shape"])
    for k, s in enumerate(shapes):
        v = scores.loc[scores.true_shape == s, "slope_error"].dropna().to_numpy()
        ax.scatter(v, np.full(len(v), k) + np.random.default_rng(k).uniform(-.15, .15, len(v)), s=10,
                   color=BLUE, alpha=.6, linewidths=0)
    ax.axvline(thr["synthetic_median_slope_error_frac"], color=MUTED, lw=1, ls="--")
    ax.text(thr["synthetic_median_slope_error_frac"], len(shapes) - .5, " pass line (median)", color=MUTED,
            fontsize=8, va="bottom")
    ax.set_yticks(range(len(shapes)), shapes)
    ax.set_xlabel("slope error (RMSE / range of true slope)", color=INK, fontsize=9)
    ax.set_title(f"Synthetic slope recovery, n = {len(scores)} curves", color=INK, fontsize=10, loc="left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "synthetic_slope_error.png"), dpi=150)
    plt.close(fig)

    lines = [
        "# Stage 1 synthetic check: can we recover known slope curves?", "", _stamp_line(stamp), "",
        "## Result", "",
        f"**{verdict}.** Median slope error over non-flat curves = {med:.3f} of the true slope range "
        f"(pass if below {thr['synthetic_median_slope_error_frac']}). n = {len(scores)} curves "
        f"({len(non_flat)} non-flat), B = {lib['draws'].shape[1] if lib['draws'].size else 'n/a'} bootstrap resamples.", "",
        "Slope error = root-mean-square difference between estimated and true slope over the curve's observed "
        "grid points, divided by the range of the true slope there. Edge = half-way point of the main rise or "
        "fall (the logistic p50); the true edge uses the same definition on the true curve.", "",
        "## By true shape", "", md_table(by_shape), "",
        "Edge-interval coverage is the fraction of curves whose 95% bootstrap interval contains the true edge "
        "(nominal 0.95).", "",
        "## Shape classification (rows = truth, columns = assigned)", "", md_table(confusion), "",
        "## Primary model chosen", "", md_table(primary), "",
        "## QC flags", "", md_table(flags), "",
        "## Known limitations", "",
        "- Smoother-based intervals under-cover the truth (see coverage for bell and two-step curves): the pairs "
        "bootstrap captures noise but not the smoothing bias of a fixed penalty. Logistic intervals are close to "
        "nominal. Treat edge intervals of smoother-primary curves as too narrow.",
        "- Two-step curves are often classified as `rising`/`falling` when the plateau between steps is short "
        "or poorly sampled; their slope error is the highest of the shapes.",
        "- `edge_not_bracketed` fires often here because synthetic pH positions are uniform random, which leaves "
        "gaps wider than 0.5 pH near some edges.", "",
        "Per-curve table: `synthetic_scores.csv`. Figure: `synthetic_slope_error.png`.",
    ]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Stage 1 synthetic {verdict}: median slope error {med:.3f}")
    return verdict


# ------------------------------------------------------------------ real data

def stage1_real_summary(out_dir, lib, thr_all, stamp):
    thr, qthr = thr_all["stage1"], thr_all["qc"]
    meta = lib["meta"].copy()
    census = meta[meta["in_census_set"].astype(bool)]
    core_frac = float(census["in_core_library"].mean()) if len(census) else np.nan
    verdict = "PASS" if core_frac >= thr["real_min_core_fraction"] else "FAIL"
    shape_counts = meta["shape"].value_counts().rename_axis("shape").reset_index(name="curves")
    census_shapes = census["shape"].value_counts(normalize=True)
    other_share = float(1 - census_shapes.get("rising", 0) - census_shapes.get("falling", 0))
    flags_all, flags_census = flag_table(meta), flag_table(census)

    disagree = meta[meta["n_disagree_points"] >= qthr["disagree_min_points"]].sort_values(
        "n_disagree_points", ascending=False)
    disagree[["curve_id", "reference", "mineral", "sorbate", "shape", "primary_model", "n_disagree_points",
              "qc_flags"]].to_csv(os.path.join(out_dir, "logistic_vs_smoother_disagreements.csv"), index=False)
    meta.sort_values(["in_core_library", "rmse"], ascending=[True, False]).to_csv(
        os.path.join(out_dir, "curve_table.csv"), index=False)

    # figure 1: flag counts
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    ft = flags_census[::-1]
    ax.barh(ft["flag"], ft["curves_with_flag"], color=BLUE, height=.6)
    for y, v in enumerate(ft["curves_with_flag"]):
        ax.text(v, y, f" {v}", va="center", fontsize=8, color=MUTED)
    ax.set_xlabel("curves with flag", fontsize=9, color=INK)
    ax.set_title(f"QC flags, census-set curves (n = {len(census)})", fontsize=10, color=INK, loc="left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "qc_flag_counts.png"), dpi=150)
    plt.close(fig)

    # figure 2: edge position by sorbate (core curves with an edge)
    core = meta[meta["in_core_library"] & meta["edge_pH"].notna()]
    top = core["sorbate"].value_counts().head(15).index
    fig, ax = plt.subplots(figsize=(6.5, 5))
    order = core[core["sorbate"].isin(top)].groupby("sorbate")["edge_pH"].median().sort_values().index
    for k, s in enumerate(order):
        sub = core[core["sorbate"] == s]
        jit = np.random.default_rng(k).uniform(-.18, .18, len(sub))
        rising = (sub["shape"] == "rising").to_numpy()
        ax.scatter(sub["edge_pH"][rising], k + jit[rising], s=9, color=BLUE, alpha=.65, linewidths=0,
                   label="rising edge" if k == 0 else None)
        ax.scatter(sub["edge_pH"][~rising], k + jit[~rising], s=9, color=ORANGE, alpha=.65, linewidths=0,
                   label="falling / other" if k == 0 else None)
        ax.text(11.6, k, f"n={len(sub)}", fontsize=7, color=MUTED, va="center")
    ax.set_yticks(range(len(order)), order)
    ax.set_xlim(1.5, 12.3)
    ax.set_xlabel("edge position (pH at half-way point)", fontsize=9, color=INK)
    ax.set_title(f"Edge position by sorbate, core-library curves (top {len(order)} sorbates, "
                 f"n = {int(core['sorbate'].isin(top).sum())})", fontsize=10, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "edge_position_by_sorbate.png"), dpi=150)
    plt.close(fig)

    lines = [
        "# Stage 1 summary: slope curves from the real data", "", _stamp_line(stamp), "",
        "## Result", "",
        f"**{verdict}.** {core_frac:.1%} of census-set curves ({int(census['in_core_library'].sum())} of "
        f"{len(census)}) survive QC with a usable shape class; the pass line is "
        f"{thr['real_min_core_fraction']:.0%}. (Census set = clean curves in the {census[['mineral','sorbate']].drop_duplicates().shape[0]} "
        "mineral-sorbate pairs that passed Stage 0.)", "",
        f"All clean curves processed: {len(meta)}; in core library: {int(meta['in_core_library'].sum())}.", "",
        f"Shapes other than rising/falling in the census set: {other_share:.1%} "
        f"({'above' if other_share > thr['multi_shape_warn_fraction'] else 'not above'} the "
        f"{thr['multi_shape_warn_fraction']:.0%} warning line"
        + ("; multi-shape handling stays in scope)." if other_share > thr["multi_shape_warn_fraction"] else ")."),
        "",
        "## Shapes (all processed curves)", "", md_table(shape_counts), "",
        "## Where curves are lost (census set)", "",
        "A curve can carry several flags, so the first column does not add up; the second column counts curves "
        "lost to that flag alone.", "", md_table(flags_census), "",
        "## Where curves are lost (all processed curves)", "", md_table(flags_all), "",
        "## Logistic vs smoother (Task 1.4)", "",
        f"{len(disagree)} curves have at least {qthr['disagree_min_points']} grid points where the two models' "
        "slopes differ by more than the larger of their 95% bootstrap half-widths. These are the curves that are "
        "not simple edges. List: `logistic_vs_smoother_disagreements.csv`.", "",
        "## Known limitations (carried from the synthetic check)", "",
        "- Edge intervals of smoother-primary curves are too narrow (synthetic coverage about 0.65 for a nominal "
        "0.95). Logistic-primary intervals are close to nominal.",
        "- Two-step curves can be classified as single edges.", "",
        "## Files", "",
        "- `curve_table.csv`: every curve with fit parameters, shape, flags (non-core and worst fits first).",
        "- `library/`: G, intervals, mask, meta (`library.npz`, `meta.csv`); bootstrap draws in `draws.npz` "
        "(not committed).",
        "- `qc_flag_counts.png`, `edge_position_by_sorbate.png`.",
        "- `diagnostics.pdf`: one page per curve (data, both fits, slope with interval); not committed, "
        "regenerate with `python -m phslope.stage1`.", "",
        "## Next decision", "",
        "Stage 2 needs `classes.yaml` filled and confirmed by Samuel and Dr. Black (task 2.1)."
        if verdict == "PASS" else
        "Stage 1 FAILS the survival rule. Look at which flags remove the most curves before deciding whether "
        "the QC rule or the data is the problem. Do not loosen thresholds just to pass.",
    ]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Stage 1 {verdict}: core fraction in census set {core_frac:.3f}")
    return verdict


def diagnostics_pdf(path, lib, curve_obs, max_pages=None):
    """One page per curve: data with both fits (left), slope with 95% band (right)."""
    meta = lib["meta"]
    grid = lib["grid"]
    groups = {cid: g for cid, g in curve_obs.groupby("curve_id")}
    with PdfPages(path) as pdf:
        for i, cid in enumerate(lib["curve_ids"][:max_pages]):
            m = meta.iloc[i]
            g = groups.get(cid)
            fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
            if g is not None:
                a1.scatter(g["pH"], g["response"], s=14, color=GRAY, zorder=3, label=f"data (n={len(g)})")
            a1.plot(grid, lib["F_logistic"][i], color=BLUE if m["primary_model"] == "logistic" else ORANGE,
                    lw=2, label="logistic" + (" (primary)" if m["primary_model"] == "logistic" else ""))
            a1.plot(grid, lib["F_spline"][i], color=BLUE if m["primary_model"] == "spline" else ORANGE,
                    lw=2, ls="--", label="smoother" + (" (primary)" if m["primary_model"] == "spline" else ""))
            if np.isfinite(m.get("edge_pH", np.nan)):
                a1.axvline(m["edge_pH"], color=MUTED, lw=.8, ls=":")
            a1.set_xlabel("pH", fontsize=9)
            a1.set_ylabel("fraction sorbed", fontsize=9)
            a1.legend(frameon=False, fontsize=7)
            _style(a1)
            a2.fill_between(grid, lib["lower"][i], lib["upper"][i], color=BLUE, alpha=.18, lw=0,
                            label="95% bootstrap band")
            a2.plot(grid, lib["G"][i], color=BLUE, lw=2, label=f"slope ({m['primary_model']})")
            other = lib["G_spline"][i] if m["primary_model"] == "logistic" else lib["G_logistic"][i]
            a2.plot(grid, other, color=ORANGE, lw=1.2, ls="--", label="other model")
            a2.axhline(0, color="#c9c8c3", lw=.8)
            a2.set_xlabel("pH", fontsize=9)
            a2.set_ylabel("dA/dpH (fraction per pH unit)", fontsize=9)
            a2.legend(frameon=False, fontsize=7)
            _style(a2)
            title = (f"{cid} | {m.get('mineral', '')} | {m.get('sorbate', '')} | {m.get('reference', '')} | "
                     f"shape: {m['shape']} | flags: {m['qc_flags'] or 'none'}")
            fig.suptitle(title, fontsize=9, color=INK, x=0.01, ha="left")
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
    print(f"Wrote {path}")
