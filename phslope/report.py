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


# ------------------------------------------------------------------ stage 2

CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


def stage2_part_a_figures(out_dir, reg, f):
    u = reg["u"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    for r in reg["R"][:400]:
        a1.plot(u, r, color=GRAY, lw=.5, alpha=.25)
    a1.plot(u, reg["reference"], color=BLUE, lw=2, label="mean registered curve")
    s = 1 / (1 + np.exp(-u))
    a1.plot(u, s * (1 - s), color=ORANGE, lw=1.5, ls="--", label="exact logistic")
    a1.set_xlabel("registered pH, u = (pH - edge) / width", fontsize=9)
    a1.set_ylabel("slope x width / height", fontsize=9)
    a1.set_title(f"Registered single-edge curves (n = {len(reg['R'])})", fontsize=10, loc="left")
    a1.legend(frameon=False, fontsize=8)
    _style(a1)
    uk = u[f["columns"]]
    for j in range(f["n_components"]):
        a2.plot(uk, f["components"][j], color=CAT[j], lw=2,
                label=f"FPC{j + 1} ({f['explained'][j]:.0%} of variance)")
    a2.axhline(0, color="#c9c8c3", lw=.8)
    a2.set_xlabel("registered pH, u", fontsize=9)
    a2.set_title("Main shape variations after registration", fontsize=10, loc="left")
    a2.legend(frameon=False, fontsize=8)
    _style(a2)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "registration_and_fpca.png"), dpi=150)
    plt.close(fig)


def stage2_part_b_figures(out_dir, split, t):
    params = list(dict.fromkeys(split["parameter"]))
    comps = ["mineral_class", "sorbate_class", "mineral_sorbate", "reference", "residual"]
    fig, ax = plt.subplots(figsize=(7.5, 0.6 + 0.55 * len(params)))
    left = np.zeros(len(params))
    for j, c in enumerate(comps):
        vals = np.array([split[(split.parameter == p) & (split.component == c)]["share"].sum() for p in params])
        ax.barh(params, vals, left=left, color=CAT[j] if c != "residual" else "#c9c8c3", height=.6,
                edgecolor="white", linewidth=1, label=c.replace("_", " "))
        left += vals
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of variance", fontsize=9)
    ax.set_title(f"Variance split (n = {len(t)} core edge curves; intervals in variance_split.csv)",
                 fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8, ncol=5, loc="upper center", bbox_to_anchor=(.5, -.25))
    _style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "variance_shares.png"), dpi=150)
    plt.close(fig)

    g = t.groupby(["mineral", "sorbate"])["edge_pH"].agg(["mean", "size"]).reset_index()
    top_m = t["mineral"].value_counts().head(15).index
    top_s = t["sorbate"].value_counts().head(20).index
    piv = g.pivot(index="mineral", columns="sorbate", values="mean").reindex(index=top_m, columns=top_s)
    cnt = g.pivot(index="mineral", columns="sorbate", values="size").reindex(index=top_m, columns=top_s)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    im = ax.imshow(piv.to_numpy(), cmap="Blues", vmin=2, vmax=11, aspect="auto")
    for (i, j), v in np.ndenumerate(cnt.to_numpy()):
        if np.isfinite(v):
            ax.text(j, i, int(v), ha="center", va="center", fontsize=6,
                    color="white" if piv.to_numpy()[i, j] > 7.5 else INK)
    ax.set_xticks(range(len(top_s)), top_s, rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(top_m)), top_m, fontsize=7)
    cb = fig.colorbar(im, ax=ax, fraction=.03)
    cb.set_label("mean edge pH", fontsize=8)
    ax.set_title("Mean edge position per mineral-sorbate pair (numbers = curves; blank = no data)",
                 fontsize=10, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "edge_grid.png"), dpi=150)
    plt.close(fig)


def stage2_part_c_figure(out_dir, res):
    """Group share of edge position per grouping, FDR-significant groupings highlighted."""
    r = res[res["parameter"] == "edge_pH"].dropna(subset=["group_share"]).sort_values("group_share")
    r = r.assign(significant_fdr=r["significant_fdr"].fillna(False).astype(bool))
    if not len(r):
        return
    fig, ax = plt.subplots(figsize=(7.5, 0.25 * len(r) + 1.2))
    sig = r["significant_fdr"].to_numpy(bool)
    y = np.arange(len(r))
    ax.hlines(y, 0, r["group_share"], color="#dcdbd5", lw=1)
    ax.scatter(r["group_share"][~sig], y[~sig], s=22, color=GRAY, zorder=3, label="not significant (q >= 0.05)")
    ax.scatter(r["group_share"][sig], y[sig], s=26, color=BLUE, zorder=3, label="significant after FDR (q < 0.05)")
    ax.set_yticks(y, [f"{g}  [{k.replace('_', ' ')}]" for g, k in zip(r["grouping"], r["kind"])], fontsize=6.5)
    ax.set_xlabel("share of edge-position variance (model with study as a second random effect)", fontsize=8)
    ax.set_title(f"EXPLORATORY: which groupings track edge position? ({len(r)} groupings)", fontsize=10,
                 loc="left")
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "exploratory_groupings.png"), dpi=150)
    plt.close(fig)


def stage2_summary(out_dir, lib, a, b, thr_all, stamp, exploratory=False, classes_confirmed=False, c=None):
    f, vr = a["fpca"], a["variance_removed"]
    n_core = int(lib["meta"]["in_core_library"].sum())
    src = a["scores"]["slope_source"].value_counts().to_dict()
    sd_cols = [c for c in a["scores"].columns if c.endswith("_sd")]
    unc = ", ".join(f"{c[:-3].upper()} {np.nanmedian(a['scores'][c]):.3g} vs spread "
                    f"{np.nanstd(a['scores'][c[:-3]]):.3g}" for c in sd_cols)
    banner = []
    if exploratory:
        banner = [
            "> **EXPLORATORY.** Stage 1 did not meet its pre-set survival rule (46.8% of census-set curves "
            "survived QC; 80% required). Samuel chose on 2026-10-12 to continue with the core library. "
            + ("The classes in Part B are the PROPOSED assignment in classes.yaml, **not yet confirmed** by "
               "Samuel and Dr. Black. " if not classes_confirmed else "")
            + "Nothing here is a confirmatory result.", ""]
    lines = [
        "# Stage 2 summary: do mineral and sorbate classes matter?", "", *banner, _stamp_line(stamp), "",
        "## Part A: registration and shape components (task 2.2)", "",
        f"- Single-edge (rising/falling) core curves registered: {len(a['reg']['idx'])} of {n_core} core curves. "
        f"Registered slope source: {src}.",
        f"- Slope variance removed by registration alone (aligning edge position, width and height): "
        f"{vr['all']:.1%} overall; rising {vr['rising']:.1%}; falling {vr['falling']:.1%}.",
        f"- FPCA: {f['n_components']} component(s) kept (rule: >= 90% of variance, max 5). Explained: "
        + ", ".join(f"FPC{j + 1} {f['explained'][j]:.1%}" for j in range(f["n_components"]))
        + f". {f['filled_fraction']:.1%} of the cells were filled by iterative SVD imputation, so these shares "
        "are somewhat optimistic.",
        f"- Score uncertainty (median bootstrap SD of projected scores vs the spread of scores across curves): {unc}.",
        "", "Files: `registration_and_scores.csv` (warp a, b, w per curve, ratios to the median curve, FPC "
        "scores and SDs), `fpca_components.csv`, `registration_and_fpca.png`.", "",
        "## Part B: class tests (tasks 2.3-2.5)", "",
    ]
    if b is None:
        lines += [
            "**Not run.** `phslope/config/classes.yaml` holds a PROPOSED class assignment with `confirmed: false`. "
            "Samuel and Dr. Black review it (spec task 2.1) and set `confirmed: true`; then re-run "
            "`python -m phslope.stage2`. The classes must not be changed after seeing Part B results.",
        ]
    else:
        v, perm, cond = b["verdict"], b["perm"], b["cond"]
        lines += [
            f"### Go/no-go: **{v['verdict']}**", "",
            f"{v['reason']}. For edge position: class share (mineral class + sorbate class + pair) = "
            f"{v['class_share']:.1%}, reference (study) share = {v['reference_share']:.1%}; within-reference "
            f"permutation p = {perm['p_value']:.4f} ({len(perm['null'])} permutations).", "",
            f"Permutation informativeness: {perm['n_refs_shufflable']} of {perm['n_refs']} references "
            f"({perm['n_curves_shufflable']} of {perm['n']} curves) contain more than one class cell and can be "
            "shuffled; the rest are fixed under the null, which makes the test conservative.", "",
            "Unassigned names (excluded): " + str(b["unassigned"]), "",
            "### Variance shares (95% parametric-bootstrap intervals: simulate from the fitted model, refit)", "",
            md_table(b["split"][["parameter", "component", "share", "share_lo", "share_hi"]]), "",
            f"### Edge position with conditions as fixed effects (n = {cond.attrs['n']}, "
            f"{cond.attrs['dropped_rows']} curves dropped for a missing covariate; temperature "
            f"{'included' if cond.attrs['temp_used'] else 'not included (reported for < 80% of curves)'}; "
            f"constant covariates dropped: {cond.attrs.get('constant_covariates_dropped') or 'none'})", "",
            md_table(cond[["component", "share"]]), "",
            "### Clustering vs class labels (within-reference permutations)", "", md_table(b["tests"]), "",
            "Figures: `variance_shares.png`, `edge_grid.png`.", "",
            "### Next decision", "",
            ("Stage 2 passes: continue to Stage 3 (descriptor tables, then freeze thresholds.yaml)."
             if v["verdict"] == "PASS" else
             "Stage 2 does not pass: stop, write up the negative result, and decide whether conditions as "
             "covariates (not classes) is the next thing to test.")
            + (" (Exploratory: the verdict uses unconfirmed classes and a library that failed Stage 1.)"
               if exploratory else ""),
        ]
    if c is not None:
        r, pr = c["results"], c["property_report"]
        edge = r[r["parameter"] == "edge_pH"]
        sig = r[r["significant_fdr"]]
        lines += [
            "", "## Part C: exploratory groupings (config/schemes.yaml)", "",
            f"{c['n_groupings']} groupings tested on {c['n_curves']} core edge curves: one T-vs-F split per "
            "usable column of the mineral property table, two mineral schemes built from it, four sorbate "
            "schemes and four ionic-condition schemes. Each was tested for edge position (all) and log width and "
            "height (schemes only): variance share in a model with study as a second random effect, and a "
            "within-reference permutation test of the between-group share. "
            f"{len(r)} tests in total; q = Benjamini-Hochberg adjusted p over the exploratory groupings. "
            f"Significant after FDR: {len(sig)}. The two pre-specified classes from classes.yaml are included as "
            "reference rows (kind `prespecified_class`), tested the same way, with their raw p and no q: they "
            "are not part of the exploratory screen.", "",
            "Mineral property table: " + f"`{os.path.basename(pr['file'])}`; cell codes {pr['cell_codes']} "
            "(only T and F used; TO/O/FO treated as missing). "
            f"Rows left out pending correction: {', '.join(pr['excluded_rows'])}. "
            f"Minerals in the library with no row: {', '.join(pr.get('data_minerals_without_row', [])) or 'none'}. "
            "The table has no source column, so these are uncited properties.", "",
            "### Edge position, all groupings (sorted by q)", "",
            md_table(edge[["grouping", "kind", "n_curves", "n_groups", "group_share", "reference_share",
                           "between_group_R2", "p_value", "q_value", "curves_shufflable"]]), "",
            "### Width and height, schemes", "",
            md_table(r[r["parameter"] != "edge_pH"][["grouping", "parameter", "n_curves", "group_share",
                                                    "reference_share", "p_value", "q_value"]]), "",
            "How to read this: `group_share` is the share of variance the grouping takes when study is also in "
            "the model; `between_group_R2` is the plain share between groups (what the permutation test uses); "
            "`curves_shufflable` counts curves in papers that contain more than one group (only those carry "
            "information in the within-paper test). Groupings tested here are correlated (e.g. iron-containing "
            "and oxyhydroxide pick out almost the same minerals), so several significant rows can be one effect.",
            "", "Files: `exploratory_groupings.csv`, `exploratory_group_labels.csv` (label of every curve under "
            "every grouping), `exploratory_groupings.png`.",
        ]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("Stage 2 summary written" + ("" if b else " (Part B not run: classes not confirmed)"))


# ------------------------------------------------------------------ pooled comparison

MODE_LABEL = {"pair_band": "pooled within ionic-strength band", "pair_all": "pooled across all ionic strengths"}


def _pool_stats(t):
    edge = t[t["shape"].isin(("rising", "falling", "bell", "multi_step"))]
    pt_w = edge["edge_hi"] - edge["edge_lo"]
    cl_w = edge["cluster_edge_hi"] - edge["cluster_edge_lo"]
    ok = pt_w.notna() & cl_w.notna() & (pt_w > 0)
    return {
        "pools": len(t),
        "median_refs": float(t["n_references"].median()) if len(t) else np.nan,
        "core_fraction": float(t["in_core_library"].mean()) if len(t) else np.nan,
        "shape_counts": t["shape"].value_counts().to_dict(),
        "shape_agrees": float((edge["shape"] == edge["curves_majority_shape"])[edge["curves_majority_shape"] != ""].mean())
        if len(edge) else np.nan,
        "width_ratio_median": float(edge["width_ratio"].median()),
        "width_ratio_iqr": (float(edge["width_ratio"].quantile(.25)), float(edge["width_ratio"].quantile(.75))),
        "width_ratio_gt_1_5": float((edge["width_ratio"] > 1.5).mean()),
        "abs_edge_shift_median": float(edge["edge_shift"].abs().median()),
        "cluster_over_point_interval": float((cl_w[ok] / pt_w[ok]).median()) if ok.any() else np.nan,
        "resid_ref_R2_median": float(t["resid_ref_R2"].median()),
        "n_with_comparison": int(edge["width_ratio"].notna().sum()),
    }


def pooled_summary(out_dir, res, stamp, bands):
    stats = {m: _pool_stats(r["table"]) for m, r in res.items()}
    # same pair, pooled within one band vs pooled across all bands
    a, b = res["pair_band"]["table"], res["pair_all"]["table"]
    multi = b[b["n_I_bands"] >= 2][["mineral", "sorbate", "width", "edge_pH", "I_span_decades"]]
    a_best = (a.sort_values("n_points", ascending=False).drop_duplicates(["mineral", "sorbate"])
              [["mineral", "sorbate", "width", "edge_pH", "band"]])
    ab = multi.merge(a_best, on=["mineral", "sorbate"], suffixes=("_all", "_band"))
    ab["width_ratio_all_vs_band"] = ab["width_all"] / ab["width_band"]
    ab["edge_shift_all_vs_band"] = ab["edge_pH_all"] - ab["edge_pH_band"]
    ab.to_csv(os.path.join(out_dir, "band_vs_all_same_pair.csv"), index=False)

    # figure: width ratio by mode
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    for k, (m, r) in enumerate(res.items()):
        v = r["table"]["width_ratio"].dropna()
        v = v[v > 0]
        a1.scatter(np.log2(v), k + np.random.default_rng(k).uniform(-.15, .15, len(v)), s=10,
                   color=[BLUE, ORANGE][k], alpha=.6, linewidths=0)
        a1.text(np.log2(v).max() + .2 if len(v) else 0, k, f"n={len(v)}", fontsize=7, color=MUTED, va="center")
    a1.axvline(0, color=MUTED, lw=1, ls="--")
    a1.set_yticks(range(len(res)), [MODE_LABEL[m] for m in res], fontsize=8)
    a1.set_xlabel("log2(pooled width / median single-curve width);  > 0 = pooling smears the edge", fontsize=8)
    a1.set_title("Edge width after pooling", fontsize=10, loc="left")
    _style(a1)
    for k, (m, r) in enumerate(res.items()):
        t = r["table"]
        a2.scatter(t["curves_edge_median"], t["edge_pH"], s=12, color=[BLUE, ORANGE][k], alpha=.6, linewidths=0,
                   label=MODE_LABEL[m])
    a2.plot([2, 11], [2, 11], color=MUTED, lw=1, ls="--")
    a2.set_xlabel("median edge of the pool's single curves (pH)", fontsize=8)
    a2.set_ylabel("edge of the pooled curve (pH)", fontsize=8)
    a2.set_title("Edge position after pooling", fontsize=10, loc="left")
    a2.legend(frameon=False, fontsize=7)
    _style(a2)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "pooling_effects.png"), dpi=150)
    plt.close(fig)

    def block(m):
        s = stats[m]
        lo, hi = s["width_ratio_iqr"]
        return [
            f"### {MODE_LABEL[m]} (`pools_{m}.csv`)", "",
            f"- Pools: {s['pools']} (median {s['median_refs']:.0f} references per pool). Pools passing the same QC "
            f"as single curves: {s['core_fraction']:.1%}. Shapes: {s['shape_counts']}.",
            f"- Pooled shape equals the majority shape of the pool's own core curves: {s['shape_agrees']:.1%}.",
            f"- Width ratio (pooled / median single-curve width), {s['n_with_comparison']} pools: median "
            f"{s['width_ratio_median']:.2f} (IQR {lo:.2f}-{hi:.2f}); {s['width_ratio_gt_1_5']:.0%} of pools above 1.5.",
            f"- |pooled edge - median single-curve edge|: median {s['abs_edge_shift_median']:.2f} pH.",
            f"- Edge interval from resampling whole papers vs resampling points: median ratio "
            f"{s['cluster_over_point_interval']:.1f}x wider. The point bootstrap treats points from one paper as "
            "independent and is too narrow for pooled data.",
            f"- Share of the pooled fit's residual scatter that lies between papers: median "
            f"{s['resid_ref_R2_median']:.1%}.", "",
        ]

    show = ["pool_id", "n_curves", "n_references", "n_points", "shape", "edge_pH", "cluster_edge_lo",
            "cluster_edge_hi", "width", "width_ratio", "edge_shift", "resid_ref_R2", "qc_flags"]
    lines = [
        "# Pooled-pair comparison: what if curves are pooled instead of fitted one by one?", "",
        "> **EXPLORATORY**, not in the spec (added at Samuel's request, 2026-10-12). Uses all clean curves, "
        "including the ones Stage 1 QC rejected.", "", _stamp_line(stamp), "",
        "Two pooling modes: all points of a mineral-sorbate pair inside one ionic-strength band "
        f"({', '.join(bands['labels'])}), across Sets and papers; and all points of a pair whatever the ionic "
        "strength. Other conditions (total sorbate, solids loading, carbonate) are NOT held constant in either "
        "mode; their spread per pool is in the CSVs (`total_sorbate_span_decades`, `solids_span_ratio`, "
        "`co2_fraction`).", "",
        "Each pool is fitted exactly like a single curve (logistic + smoother, shape class, QC flags). Smoother "
        "points are averaged into 0.1-pH levels for pooled data. Comparison is with the pool's own curves that "
        "are in the core library.", "",
        "## Results", "", *block("pair_band"), *block("pair_all"),
        "## Same pair: one ionic-strength band vs all bands together", "",
        f"{len(ab)} pairs have curves in two or more bands. Pooling across bands vs within the best-covered band: "
        f"median width ratio {ab['width_ratio_all_vs_band'].median():.2f}, median |edge shift| "
        f"{ab['edge_shift_all_vs_band'].abs().median():.2f} pH. Table: `band_vs_all_same_pair.csv`.", "",
        "## Largest pools (pooled across all ionic strengths)", "",
        md_table(res["pair_all"]["table"].sort_values("n_points", ascending=False).head(20)[show]), "",
        "## How to read this", "",
        "If pooling across papers were harmless, pooled widths would match single-curve widths (ratio ~1), pooled "
        "edges would sit on the single-curve median, and little residual scatter would line up with papers. A "
        "ratio well above 1 and a large between-paper residual share mean the pooled curve mixes study offsets "
        "into its shape: the pooled slope is flatter and wider than any single experiment's.", "",
        "Files: `pools_pair_band.csv`, `pools_pair_all.csv`, `band_vs_all_same_pair.csv`, `pooling_effects.png`, "
        "`pooled_diagnostics.pdf` (one page per pool; not committed).",
    ]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("Pooled summary written")
    return stats


def pooled_pdf(path, res):
    from phslope import fit_edge
    with PdfPages(path) as pdf:
        for m, r in res.items():
            t = r["table"].set_index("pool_id")
            for pid, o in r["obs"].groupby("pool_id", sort=False):
                row = t.loc[pid]
                fig, ax = plt.subplots(figsize=(8, 4))
                refs = o["reference"].unique()
                for k, ref in enumerate(refs):
                    sub = o[o["reference"] == ref]
                    ax.scatter(sub["pH"], sub["response"], s=10, color=CAT[k] if len(refs) <= 8 else GRAY,
                               alpha=.7, linewidths=0, label=ref if len(refs) <= 8 else None)
                if np.isfinite(row.get("logistic_p50", np.nan)):
                    p = np.linspace(o["pH"].min(), o["pH"].max(), 200)
                    q = {k: row[f"logistic_{k}"] for k in ("lo", "hi", "p50", "w")}
                    ax.plot(p, fit_edge.predict(q, p), color=INK, lw=2, label="pooled logistic")
                ax.set_xlabel("pH", fontsize=9)
                ax.set_ylabel("fraction sorbed", fontsize=9)
                ax.set_title(f"{MODE_LABEL[m]}: {pid} | {int(row['n_curves'])} curves, {int(row['n_references'])} "
                             f"papers | width ratio {row['width_ratio']:.2f}", fontsize=8, loc="left")
                ax.legend(frameon=False, fontsize=6, ncol=2)
                _style(ax)
                fig.tight_layout()
                pdf.savefig(fig)
                plt.close(fig)
    print(f"Wrote {path}")


# ------------------------------------------------------------------ stage 3

def stage3_verdicts(summ, diffs, thr):
    """Per level and model: pass if median p50 error <= limit, slope-interval coverage within
    [coverage_min, coverage_max], and the 95% interval of the paired difference vs EVERY baseline is
    below zero for both p50_error and curve_error (margin_over_baseline, if set, must also be met)."""
    margin = thr.get("margin_over_baseline") or 0.0
    rows = []
    for (level, model), s in summ.set_index(["level", "model"]).iterrows():
        if not model.startswith("version"):
            continue
        d = diffs[(diffs["level"] == level) & (diffs["model"] == model)]
        beats = (len(d) > 0 and (d["p50_diff_hi"] < -margin).all() and (d["curve_diff_hi"] < 0).all())
        cov_ok = thr["coverage_min"] <= s["interval_coverage"] <= thr["coverage_max"]
        p50_ok = s["median_p50_error"] <= thr["median_p50_error_max"]
        rows.append({"level": level, "model": model, "median_p50_error": s["median_p50_error"],
                     "p50_ok": p50_ok, "interval_coverage": s["interval_coverage"], "coverage_ok": cov_ok,
                     "beats_every_baseline": beats, "verdict": "PASS" if (p50_ok and cov_ok and beats) else "FAIL"})
    return pd.DataFrame(rows)


def stage3_summary(out_dir, D, fsets, skipped, summ, diffs, thr_all, stamp):
    thr = thr_all["stage3"]
    ver = stage3_verdicts(summ, diffs, thr)
    ver.to_csv(os.path.join(out_dir, "verdicts.csv"), index=False)

    # figure: median p50 error per model and level
    levels = list(dict.fromkeys(summ["level"]))
    models = list(dict.fromkeys(summ["model"]))
    fig, ax = plt.subplots(figsize=(8, 0.35 * len(models) + 1.5))
    for k, lev in enumerate(levels):
        s = summ[summ["level"] == lev].set_index("model").reindex(models)
        ax.scatter(s["median_p50_error"], np.arange(len(models)) + (k - 1.5) * 0.15, s=18, color=CAT[k],
                   label=f"leave one {lev} out", zorder=3)
    ax.axvline(thr["median_p50_error_max"], color=MUTED, lw=1, ls="--")
    ax.set_yticks(range(len(models)), models, fontsize=7)
    ax.set_xlabel("median |predicted - observed edge| (pH)", fontsize=9)
    ax.set_title(f"Held-out edge error by model (n = {len(D['t'])} single-edge core curves)", fontsize=10,
                 loc="left")
    ax.legend(frameon=False, fontsize=7)
    _style(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "p50_error_by_model.png"), dpi=150)
    plt.close(fig)

    banner = []
    if stamp.get("exploratory"):
        banner = ["> **EXPLORATORY.** Stage 1 failed its survival rule; classes "
                  + ("are confirmed" if stamp.get("classes_confirmed") else "are the unconfirmed proposal")
                  + f"; {stamp.get('thresholds')}. Feature sets other than `descriptors` use the uncited mineral "
                  "property table and Claude's proposed sorbate schemes. Nothing here is a confirmatory result.", ""]
    lines = [
        "# Stage 3 summary: can we predict a held-out system's slope curve?", "", *banner, _stamp_line(stamp), "",
        f"Data: {len(D['t'])} single-edge (rising/falling) core curves, {D['t']['reference'].nunique()} papers, "
        f"{D['t']['pair'].nunique()} mineral-sorbate pairs.", "",
        "Feature sets used: " + ", ".join(f"`{k}` ({v[1]['n_features']} features, {v[1]['n_complete']} curves "
                                          "with every feature)" for k, v in fsets.items()) + ".",
        "Not used: " + ("; ".join(f"`{k}`: {v}" for k, v in skipped.items()) or "none") + ".", "",
        "Without the descriptor tables the edge-position rule baseline (edge from PZC and first hydrolysis "
        "constant), the one the spec says decides whether the project says anything new, cannot run."
        if "edge_position_rule" not in set(summ["model"]) else "", "",
        "## Verdict per model and level (thresholds.yaml stage3)", "",
        f"Pass = median edge error <= {thr['median_p50_error_max']} pH, slope-interval coverage in "
        f"[{thr['coverage_min']}, {thr['coverage_max']}], and better than every baseline (95% interval of the paired "
        "difference below zero, for edge error and curve error).", "",
        md_table(ver), "",
        "## Metrics by model", "", md_table(summ), "",
        "## Paired differences vs baselines (model minus baseline; negative = model better; 95% intervals over "
        "held-out papers)", "", md_table(diffs), "",
        "Files: `per_curve_worst_first.csv` (every held-out curve, worst first), `metrics_by_model.csv`, "
        "`paired_differences.csv`, `verdicts.csv`, `p50_error_by_model.png`.",
    ]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("Stage 3 summary written")
