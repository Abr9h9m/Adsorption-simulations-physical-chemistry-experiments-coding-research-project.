"""
Data Auditing Pipeline for Sorption Fingerprint Pilot Systems
==============================================================
Built against the actual library schema (Appendix A). Vectorized throughout
for the ~80k-row dataset — no per-row Python loops on the full table; the only
per-row-ish work happens inside small, per-system subsets, and even that uses
a KD-tree rather than a nested loop.

HOW TO USE
----------
1. Set CONFIG["DATA_FILE"] to your real file, and fix PILOT_SYSTEMS' mineral/
   sorbate labels to match your data's actual spelling/case.
2. Run: python data_audit.py
   It always runs the synthetic self-test and a performance check first, then
   the real audit if the file exists.
3. Check outputs/audit_table.csv and outputs/coverage_<system>.png.

Requires: pandas, numpy, matplotlib, scipy
"""

import os
import re
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import cKDTree

# =============================================================================
# CONFIG
# =============================================================================

CONFIG = {
    "DATA_FILE": r"C:\Users\itzju\sc.dataset.csv",

    # Core identity columns (Appendix A)
    "COL_MINERAL": "Mineral",
    "COL_MINERAL_FORMULA": "Mineral_formula",
    "COL_SORBATE": "Sorbate",
    "COL_REFERENCE": "Reference",
    "COL_SET": "Set",
    "COL_SETID": "SetID",

    # Environmental columns
    "COL_PH": "pH",
    "COL_TEMP": "Temp",
    "N_ELECTROLYTE_SLOTS": 7,   # Electrolyte1..7 / ElectrolyteX_val
    "N_GAS_SLOTS": 3,           # Gas1..3 / GasX_val

    # Response and mineral-descriptor columns
    "COL_SORPTION": "Sorbed_val",
    "COL_MINERALSITES": "Mineralsites",

    # Which (mineral, electrolyte signature, sorbate) combos to audit.
    # electrolyte = None matches any electrolyte background.
    "PILOT_SYSTEMS": [
        ("goethite", None, "U(+6)"),   # <-- replace with your real mineral/sorbate labels
        ("goethite", None, "Se(+4)"),
        ("montmorillonite", None, "U(+6)"),
        ("ferrihydrite", None, "U(+6)"),
    ],

    # Set to True to ignore PILOT_SYSTEMS and instead scan every (mineral,
    # electrolyte, sorbate) combination in the dataset, ranking all of them
    # by data quality -- use this to discover which systems, beyond the ones
    # already tried, actually have the pH x I spread needed.
    "SCAN_ALL_SYSTEMS": True,

    # When scanning everything, skip groups below this size immediately --
    # keeps runtime and output size sane when there are many small groups.
    "MIN_POINTS_TO_SCAN": 20,

    # When scanning everything, only generate coverage/detail plots for the
    # top N ranked systems (plotting all of them could mean hundreds of files).
    "MAX_PLOTS_WHEN_SCANNING": 15,

    "OUTPUT_DIR": "outputs",
}

THRESHOLDS = {
    "min_points_floor": 50,
    "min_points_preferred": 100,
    "min_pH_span": 4.0,
    "preferred_pH_span": 5.0,
    "min_distinct_I_levels": 3,
    "preferred_distinct_I_levels": 5,
    "min_joint_coverage_fraction": 0.15,
    "I_level_rounding_decimals": 3,
    "max_temp_range_C": 5.0,                  # wider than this within one system -> flagged (unmodeled confound)
    "site_density_cv_swept_threshold": 0.02,  # coefficient of variation above this -> "appears swept", not fixed
    "max_references_before_flag": 1,          # more than this many distinct sources -> flagged (pooled-study heterogeneity)
}


# =============================================================================
# Ionic strength — ion identity is a VALUE in Electrolyte1..7, not the column name
# =============================================================================

_CHARGE_RE = re.compile(r"\(([+-]?\d+)\)")


def compute_ionic_strength(df, n_slots):
    """
    I = 0.5 * sum_i( c_i * z_i^2 ), where each row can have a different ion in
    each of the N electrolyte slots (e.g. Electrolyte1='Na(+1)', Electrolyte1_val=0.1).
    Fully vectorized: one regex extraction + one numeric multiply per slot.
    """
    I = pd.Series(0.0, index=df.index)
    for i in range(1, n_slots + 1):
        label_col, val_col = f"Electrolyte{i}", f"Electrolyte{i}_val"
        if label_col not in df.columns or val_col not in df.columns:
            continue
        charge = pd.to_numeric(
            df[label_col].astype(str).str.extract(_CHARGE_RE)[0], errors="coerce"
        ).fillna(0.0)
        conc = pd.to_numeric(df[val_col], errors="coerce").fillna(0.0)
        I += conc * (charge ** 2)
    return 0.5 * I


def electrolyte_signature(df, n_slots):
    """A canonical, order-independent label for the background electrolyte
    composition of each row, e.g. 'Cl(-1)+Na(+1)', used as the categorical
    'electrolyte identity' for system grouping."""
    label_cols = [f"Electrolyte{i}" for i in range(1, n_slots + 1) if f"Electrolyte{i}" in df.columns]
    if not label_cols:
        return pd.Series([""] * len(df), index=df.index)
    labels = df[label_cols].fillna("")
    return labels.apply(lambda row: "+".join(sorted(v for v in row if v)), axis=1)


# =============================================================================
# Loading and preparation
# =============================================================================

def load_raw_data(filepath):
    return pd.read_excel(filepath) if filepath.lower().endswith((".xlsx", ".xls")) else pd.read_csv(filepath)


def prepare_data(df, config):
    df = df.copy()
    n_slots = config["N_ELECTROLYTE_SLOTS"]
    df["_pH"] = pd.to_numeric(df[config["COL_PH"]], errors="coerce")
    df["_response"] = pd.to_numeric(df[config["COL_SORPTION"]], errors="coerce")
    df["_ionic_strength"] = compute_ionic_strength(df, n_slots)
    df["_electrolyte_sig"] = electrolyte_signature(df, n_slots)
    if config["COL_TEMP"] in df.columns:
        df["_temp"] = pd.to_numeric(df[config["COL_TEMP"]], errors="coerce")
    if config["COL_MINERALSITES"] in df.columns:
        df["_mineralsites"] = pd.to_numeric(df[config["COL_MINERALSITES"]], errors="coerce")
    return df


def group_by_system(df, config):
    keys = [config["COL_MINERAL"], "_electrolyte_sig", config["COL_SORBATE"]]
    return {k: sub for k, sub in df.groupby(keys)}


def select_candidate_systems(all_groups, pilot_systems):
    selected = {}
    for mineral, electrolyte, sorbate in pilot_systems:
        matches = [sub for (m, e, s), sub in all_groups.items()
                   if (mineral is None or m == mineral)
                   and (electrolyte is None or e == electrolyte)
                   and (sorbate is None or s == sorbate)]
        label = f"{mineral or '*'}-{electrolyte or '*'}-{sorbate or '*'}"
        selected[label] = pd.concat(matches, ignore_index=True) if matches else pd.DataFrame(
            columns=["_pH", "_ionic_strength", "_response"])
    return selected


# =============================================================================
# Audit computations — each vectorized / O(n) or O(n log n) within a system
# =============================================================================

def audit_point_count(sub):
    return {"n_points": int(sub["_response"].notna().sum())}


def audit_pH_span(sub):
    v = sub["_pH"].dropna()
    if v.empty:
        return {"pH_min": np.nan, "pH_max": np.nan, "pH_span": 0.0}
    return {"pH_min": v.min(), "pH_max": v.max(), "pH_span": v.max() - v.min()}


def audit_ionic_strength_levels(sub, decimals):
    v = sub["_ionic_strength"].dropna().round(decimals)
    distinct_sorted = sorted(v.unique().tolist())
    return {"I_min": v.min() if not v.empty else np.nan,
            "I_max": v.max() if not v.empty else np.nan,
            "n_distinct_I_levels": int(v.nunique()),
            "I_levels_list": ", ".join(f"{x:g}" for x in distinct_sorted[:20]) +
                             (f", ... (+{len(distinct_sorted)-20} more)" if len(distinct_sorted) > 20 else "")}


def audit_joint_coverage(sub, n_bins=6):
    valid = sub.dropna(subset=["_pH", "_ionic_strength"])
    if len(valid) < 4:
        return {"joint_coverage_fraction": 0.0}
    pH_bins = np.linspace(valid["_pH"].min(), valid["_pH"].max(), n_bins + 1)
    I_bins = np.linspace(valid["_ionic_strength"].min(), valid["_ionic_strength"].max(), n_bins + 1)
    hist, _, _ = np.histogram2d(valid["_pH"], valid["_ionic_strength"], bins=[pH_bins, I_bins])
    return {"joint_coverage_fraction": np.count_nonzero(hist) / hist.size}


def audit_missing_invalid(sub, config):
    return {
        "n_rows_total": len(sub),
        "missing_response": int(sub["_response"].isna().sum()),
        "missing_pH": int(sub["_pH"].isna().sum()),
        "missing_I": int(sub["_ionic_strength"].isna().sum()),
        "invalid_response_values": int((sub["_response"] < 0).sum()),
    }


def audit_replicates_via_set(sub, config):
    """Uses the dataset's own Set/SetID design (rows sharing a Set are
    replicates/variations of one condition block) instead of an inferred
    distance-based heuristic — exact, and O(n) via groupby."""
    if config["COL_SET"] not in sub.columns:
        return {"n_sets": np.nan, "median_replicates_per_set": np.nan}
    counts = sub.groupby(config["COL_SET"]).size()
    return {"n_sets": int(counts.shape[0]), "median_replicates_per_set": float(counts.median())}


def reference_breakdown(sub, config, decimals, min_I_levels_for_local_fit=3):
    """
    The critical check: pooled ionic-strength coverage across many studies can
    look fine while no single study actually varied ionic strength at all —
    each study may have used one fixed background level, with the *appearance*
    of a spread coming entirely from stacking different studies' different
    fixed choices. This checks I-variation WITHIN each individual reference.

    Returns a per-reference DataFrame (for inspection) plus a summary dict
    (for the main audit table).
    """
    ref_col = config["COL_REFERENCE"]
    if ref_col not in sub.columns:
        return pd.DataFrame(), {"n_refs_with_sufficient_I_variation": np.nan,
                                 "n_points_in_I_varying_refs": np.nan,
                                 "pct_points_in_I_varying_refs": np.nan}

    rows = []
    for ref, g in sub.groupby(ref_col):
        I_vals = g["_ionic_strength"].dropna().round(decimals)
        pH_vals = g["_pH"].dropna()
        n_I = int(I_vals.nunique())
        rows.append({
            "reference": ref,
            "n_points": len(g),
            "n_distinct_I_levels": n_I,
            "I_min": I_vals.min() if not I_vals.empty else np.nan,
            "I_max": I_vals.max() if not I_vals.empty else np.nan,
            "pH_span": (pH_vals.max() - pH_vals.min()) if not pH_vals.empty else np.nan,
            "sufficient_for_local_I_derivative": n_I >= min_I_levels_for_local_fit,
        })
    breakdown = pd.DataFrame(rows).sort_values("n_points", ascending=False)

    sufficient = breakdown[breakdown["sufficient_for_local_I_derivative"]]
    n_points_total = breakdown["n_points"].sum()
    n_points_sufficient = sufficient["n_points"].sum()

    summary = {
        "n_refs_total": len(breakdown),
        "n_refs_with_sufficient_I_variation": len(sufficient),
        "n_points_in_I_varying_refs": int(n_points_sufficient),
        "pct_points_in_I_varying_refs": round(100 * n_points_sufficient / n_points_total, 1) if n_points_total else 0.0,
    }
    return breakdown, summary


def audit_study_consistency(sub, config):
    if config["COL_REFERENCE"] not in sub.columns:
        return {"n_references": np.nan}
    return {"n_references": int(sub[config["COL_REFERENCE"]].nunique(dropna=True))}


def audit_temperature_consistency(sub):
    if "_temp" not in sub.columns:
        return {"temp_range_C": np.nan}
    v = sub["_temp"].dropna()
    return {"temp_range_C": float(v.max() - v.min()) if not v.empty else np.nan}


def audit_site_density(sub):
    """Checks whether Mineralsites is essentially constant for this mineral
    (expected — treat as a fixed descriptor) or actually varies (would need
    to be handled as a real axis, contrary to this cycle's 2D scope)."""
    if "_mineralsites" not in sub.columns:
        return {"site_density_mean": np.nan, "site_density_cv": np.nan, "site_density_status": "column not found"}
    v = sub["_mineralsites"].dropna()
    if v.empty or v.mean() == 0:
        return {"site_density_mean": np.nan, "site_density_cv": np.nan, "site_density_status": "no data"}
    cv = v.std() / v.mean()
    status = "SWEPT (varies within this system!)" if cv > THRESHOLDS["site_density_cv_swept_threshold"] else "fixed, as expected"
    return {"site_density_mean": float(v.mean()), "site_density_cv": float(cv), "site_density_status": status}


def audit_mineral_formula_consistency(sub, config):
    col = config["COL_MINERAL_FORMULA"]
    if col not in sub.columns:
        return {"n_distinct_formulas": np.nan}
    return {"n_distinct_formulas": int(sub[col].nunique(dropna=True))}


def estimate_initial_bandwidth(sub):
    """Median nearest-neighbor distance in scaled (0-1) pH/I space, via a
    KD-tree — O(n log n), safe even if a single system's subset is large."""
    valid = sub.dropna(subset=["_pH", "_ionic_strength"])
    if len(valid) < 5:
        return {"initial_bandwidth_pH_scaled": np.nan, "initial_bandwidth_I_scaled": np.nan}
    pH = valid["_pH"].to_numpy()
    I = valid["_ionic_strength"].to_numpy()
    pH_s = (pH - pH.min()) / (pH.max() - pH.min() + 1e-9)
    I_s = (I - I.min()) / (I.max() - I.min() + 1e-9)
    coords = np.column_stack([pH_s, I_s])
    tree = cKDTree(coords)
    dists, _ = tree.query(coords, k=2)  # column 0 is the point itself (distance 0)
    median_nn = float(np.median(dists[:, 1]))
    return {"initial_bandwidth_pH_scaled": round(median_nn, 4), "initial_bandwidth_I_scaled": round(median_nn, 4)}


# =============================================================================
# Verdict
# =============================================================================

def verdict_for_system(m, thresholds):
    fail, marginal = [], []

    if m["n_points"] < thresholds["min_points_floor"]:
        fail.append(f"only {m['n_points']} points (< {thresholds['min_points_floor']})")
    elif m["n_points"] < thresholds["min_points_preferred"]:
        marginal.append(f"{m['n_points']} points (< preferred {thresholds['min_points_preferred']})")

    if m["pH_span"] < thresholds["min_pH_span"]:
        fail.append(f"pH span only {m['pH_span']:.2f}")
    elif m["pH_span"] < thresholds["preferred_pH_span"]:
        marginal.append(f"pH span {m['pH_span']:.2f} (< preferred {thresholds['preferred_pH_span']})")

    if m["n_distinct_I_levels"] < thresholds["min_distinct_I_levels"]:
        fail.append(f"only {m['n_distinct_I_levels']} distinct ionic-strength levels")
    elif m["n_distinct_I_levels"] < thresholds["preferred_distinct_I_levels"]:
        marginal.append(f"{m['n_distinct_I_levels']} distinct I levels (< preferred)")

    if m["joint_coverage_fraction"] < thresholds["min_joint_coverage_fraction"]:
        marginal.append(f"joint pH x I coverage only {m['joint_coverage_fraction']:.2f}")

    if m.get("invalid_response_values", 0) > 0:
        marginal.append(f"{m['invalid_response_values']} invalid (negative) response values")

    temp_range = m.get("temp_range_C", np.nan)
    if not (isinstance(temp_range, float) and np.isnan(temp_range)) and temp_range > thresholds["max_temp_range_C"]:
        marginal.append(f"temperature range {temp_range:.1f} degrees C within this system (unmodeled confound)")

    if isinstance(m.get("site_density_status"), str) and m["site_density_status"].startswith("SWEPT"):
        marginal.append("site density VARIES within this system - cannot be treated as a fixed descriptor as planned")

    n_refs = m.get("n_references", np.nan)
    if not (isinstance(n_refs, float) and np.isnan(n_refs)) and n_refs > thresholds["max_references_before_flag"]:
        marginal.append(f"data pooled from {int(n_refs)} sources - check protocol consistency")

    n_formulas = m.get("n_distinct_formulas", np.nan)
    if not (isinstance(n_formulas, float) and np.isnan(n_formulas)) and n_formulas > 1:
        fail.append(f"{int(n_formulas)} distinct mineral formulas under one mineral label - ambiguous phase")

    pct_I_varying = m.get("pct_points_in_I_varying_refs", np.nan)
    if not (isinstance(pct_I_varying, float) and np.isnan(pct_I_varying)):
        if pct_I_varying < 20:
            fail.append(f"only {pct_I_varying:.0f}% of points come from references that vary ionic strength "
                        f"internally - most 'I coverage' is pooled across studies with fixed I, not real within-study variation")
        elif pct_I_varying < 50:
            marginal.append(f"only {pct_I_varying:.0f}% of points come from references with internal I variation")

    if fail:
        return "FAIL", "; ".join(fail)
    if marginal:
        return "MARGINAL", "; ".join(marginal)
    return "PASS", "meets all thresholds"


def export_pilot_subset(systems, config):
    """
    Writes the actual pilot-system data (not just summary stats) to disk:
    one CSV per system, plus one combined CSV with a 'system' label column,
    ready to drop into the repo. Keeps only the columns actually needed
    downstream (raw identity/environment columns + the computed _pH,
    _ionic_strength, _response fields), not every original column.
    """
    keep_cols = [c for c in [
        config["COL_MINERAL"], config["COL_MINERAL_FORMULA"], config["COL_SORBATE"],
        config["COL_REFERENCE"], config["COL_SET"], config["COL_SETID"],
        "_electrolyte_sig", "_pH", "_ionic_strength", "_response", "_temp", "_mineralsites",
    ] if c]

    out_dir = os.path.join(config["OUTPUT_DIR"], "pilot_data")
    os.makedirs(out_dir, exist_ok=True)

    combined = []
    for label, sub in systems.items():
        if sub.empty:
            continue
        cols_present = [c for c in keep_cols if c in sub.columns]
        subset = sub[cols_present].rename(columns=lambda c: c.lstrip("_"))
        safe_label = re.sub(r"[^\w-]", "_", label)
        subset.to_csv(os.path.join(out_dir, f"{safe_label}.csv"), index=False)

        subset_labeled = subset.copy()
        subset_labeled.insert(0, "system", label)
        combined.append(subset_labeled)

    if combined:
        pd.concat(combined, ignore_index=True).to_csv(
            os.path.join(out_dir, "all_pilot_systems_combined.csv"), index=False)

    print(f"Pilot data subset written to {out_dir}/ "
          f"({len(combined)} system file(s) + 1 combined file)")


def rank_systems(report):
    """
    Sorts the audit report so the best candidate systems bubble to the top:
    PASS before MARGINAL before FAIL, then by how much of the data actually
    comes from references with real internal ionic-strength variation (the
    single most important number for this project), then by joint coverage,
    then by raw point count as a tiebreaker.
    """
    verdict_rank = {"PASS": 0, "MARGINAL": 1, "FAIL": 2}
    report = report.copy()
    report["_verdict_rank"] = report["verdict"].map(verdict_rank)
    report = report.sort_values(
        by=["_verdict_rank", "pct_points_in_I_varying_refs", "joint_coverage_fraction", "n_points"],
        ascending=[True, False, False, False],
    ).drop(columns="_verdict_rank")
    return report


# =============================================================================
# Plotting
# =============================================================================

def plot_coverage(sub, label, output_dir):
    valid = sub.dropna(subset=["_pH", "_ionic_strength"])
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    axes[0].scatter(valid["_pH"], valid["_ionic_strength"], alpha=0.5, s=15)
    axes[0].set(xlabel="pH", ylabel="Ionic strength (mol/L)", title=f"{label}\npH x I coverage")
    axes[1].hist(valid["_pH"], bins=15, color="steelblue", edgecolor="white")
    axes[1].set(xlabel="pH", ylabel="Count", title="pH distribution")

    # Log-spaced bins for ionic strength: linear bins crush everything into
    # the first bin when I spans orders of magnitude (e.g. 0.001 to 1 M),
    # which is exactly the "looks like no spread" symptom to watch for.
    I_vals = valid["_ionic_strength"]
    I_positive = I_vals[I_vals > 0]
    if len(I_positive) > 1 and I_positive.max() > I_positive.min():
        log_bins = np.logspace(np.log10(I_positive.min()), np.log10(I_positive.max()), 16)
        axes[2].hist(I_positive, bins=log_bins, color="darkorange", edgecolor="white")
        axes[2].set_xscale("log")
    else:
        axes[2].hist(I_vals, bins=15, color="darkorange", edgecolor="white")
    axes[2].set(xlabel="Ionic strength (mol/L, log scale)", ylabel="Count", title="Ionic strength distribution")

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    safe_label = re.sub(r"[^\w-]", "_", label)
    fig.savefig(os.path.join(output_dir, f"coverage_{safe_label}.png"), dpi=150)
    plt.close(fig)


def plot_ionic_strength_detail(sub, label, output_dir):
    """
    A dedicated diagnostic for exactly the problem of 'not enough ionic
    strength coverage': a log-scale histogram, a strip plot showing every
    individual value (so gaps are visible directly, not hidden by binning),
    and the empirical cumulative distribution (shows what fraction of data
    sits below any given I value — flat stretches mean gaps, steep jumps
    mean clusters).
    """
    I_vals = sub["_ionic_strength"].dropna()
    I_vals = I_vals[I_vals > 0]
    if I_vals.empty:
        return

    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)

    log_bins = np.logspace(np.log10(I_vals.min()), np.log10(I_vals.max()), 25) \
        if I_vals.max() > I_vals.min() else 10
    axes[0].hist(I_vals, bins=log_bins, color="darkorange", edgecolor="white")
    axes[0].set_xscale("log")
    axes[0].set(ylabel="Count", title=f"{label} — ionic strength coverage (log scale)")

    rng = np.random.default_rng(0)
    jitter = rng.uniform(-0.15, 0.15, size=len(I_vals))
    axes[1].scatter(I_vals, jitter, alpha=0.4, s=12, color="darkorange")
    axes[1].set_xscale("log")
    axes[1].set_yticks([])
    axes[1].set_ylabel("individual\nvalues")

    sorted_I = np.sort(I_vals.to_numpy())
    ecdf = np.arange(1, len(sorted_I) + 1) / len(sorted_I)
    axes[2].step(sorted_I, ecdf, color="darkorange")
    axes[2].set_xscale("log")
    axes[2].set(xlabel="Ionic strength (mol/L, log scale)", ylabel="Cumulative fraction",
                title="Flat = gap in coverage, steep = cluster of values")

    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    safe_label = re.sub(r"[^\w-]", "_", label)
    fig.savefig(os.path.join(output_dir, f"I_detail_{safe_label}.png"), dpi=150)
    plt.close(fig)


# =============================================================================
# Main pipeline
# =============================================================================

def run_audit(config, thresholds):
    t0 = time.time()
    df = prepare_data(load_raw_data(config["DATA_FILE"]), config)
    print(f"Loaded and prepared {len(df):,} rows in {time.time()-t0:.2f}s")

    groups = group_by_system(df, config)
    scanning_all = config.get("SCAN_ALL_SYSTEMS", False)

    if scanning_all:
        min_pts = config.get("MIN_POINTS_TO_SCAN", 20)
        systems = {f"{m}-{e}-{s}": sub for (m, e, s), sub in groups.items() if len(sub) >= min_pts}
        print(f"Scanning all systems: {len(groups)} total combinations found, "
              f"{len(systems)} have >= {min_pts} points and will be audited.")
    else:
        systems = select_candidate_systems(groups, config["PILOT_SYSTEMS"])

    rows = []
    for label, sub in systems.items():
        m = {}
        m.update(audit_point_count(sub))
        m.update(audit_pH_span(sub))
        m.update(audit_ionic_strength_levels(sub, thresholds["I_level_rounding_decimals"]))
        m.update(audit_joint_coverage(sub))
        m.update(audit_missing_invalid(sub, config))
        m.update(audit_replicates_via_set(sub, config))
        m.update(audit_study_consistency(sub, config))
        m.update(audit_temperature_consistency(sub))
        m.update(audit_site_density(sub))
        m.update(audit_mineral_formula_consistency(sub, config))
        m.update(estimate_initial_bandwidth(sub))

        breakdown, ref_summary = reference_breakdown(sub, config, thresholds["I_level_rounding_decimals"])
        m.update(ref_summary)
        if not breakdown.empty and not scanning_all:
            safe_label = re.sub(r"[^\w-]", "_", label)
            ref_dir = os.path.join(config["OUTPUT_DIR"], "reference_breakdown")
            os.makedirs(ref_dir, exist_ok=True)
            breakdown.to_csv(os.path.join(ref_dir, f"{safe_label}.csv"), index=False)

        verdict, reason = verdict_for_system(m, thresholds)
        m["system"], m["verdict"], m["reason"] = label, verdict, reason
        rows.append(m)

    report = pd.DataFrame(rows).set_index("system")
    front = ["verdict", "reason", "n_points", "pH_span", "n_distinct_I_levels", "I_levels_list",
             "joint_coverage_fraction", "n_refs_total", "n_refs_with_sufficient_I_variation",
             "pct_points_in_I_varying_refs", "site_density_status", "n_references", "temp_range_C"]
    report = report[front + [c for c in report.columns if c not in front]]
    report = rank_systems(report)

    os.makedirs(config["OUTPUT_DIR"], exist_ok=True)
    report.to_csv(os.path.join(config["OUTPUT_DIR"], "audit_table.csv"))

    # Plot (and export the raw subset for) either everything, or -- when
    # scanning broadly -- just the top-ranked candidates, to keep output sane.
    labels_to_detail = list(report.index) if not scanning_all else list(report.index)[:config.get("MAX_PLOTS_WHEN_SCANNING", 15)]
    for label in labels_to_detail:
        sub = systems[label]
        if len(sub) > 0:
            plot_coverage(sub, label, config["OUTPUT_DIR"])
            plot_ionic_strength_detail(sub, label, config["OUTPUT_DIR"])

    if scanning_all:
        print("\nTop candidates by data quality (best first):")
        print(report[["verdict", "n_points", "pH_span", "n_distinct_I_levels",
                       "pct_points_in_I_varying_refs", "joint_coverage_fraction"]].head(15).to_string())
        print(f"\n(Plots generated only for the top {len(labels_to_detail)}. "
              f"Full ranked table: {os.path.join(config['OUTPUT_DIR'], 'audit_table.csv')})")
    else:
        export_pilot_subset(systems, config)

    print(f"Total audit time: {time.time()-t0:.2f}s for {len(systems)} systems")
    return report


# =============================================================================
# Self-test on synthetic data matching the real schema
# =============================================================================

def _make_synthetic_dataset(n_dense=5000, n_sparse=8):
    rng = np.random.default_rng(0)

    def block(n, mineral, formula, sorbate, ph_lo, ph_hi, reference="ref_A"):
        n_sets = max(1, n // 5)
        return pd.DataFrame({
            "Reference": [reference] * n,
            "Set": rng.integers(0, n_sets, n),
            "SetID": np.arange(n),
            "Mineral": [mineral] * n,
            "Mineral_formula": [formula] * n,
            "Sorbate": [sorbate] * n,
            "Temp": rng.normal(25, 0.5, n),
            "pH": rng.uniform(ph_lo, ph_hi, n),
            "Electrolyte1": ["Na(+1)"] * n,
            "Electrolyte1_val": rng.uniform(0.001, 0.5, n),
            "Electrolyte2": ["NO3(-1)"] * n,
            "Electrolyte2_val": rng.uniform(0.001, 0.5, n),
            "Mineralsites": np.full(n, 2.3),  # constant -> "fixed descriptor" expected
            "Sorbed_val": rng.uniform(0, 100, n),
        })

    dense = block(n_dense, "goethite", "FeOOH", "U(+6)", 3, 9)
    sparse = block(n_sparse, "ferrihydrite", "Fe2O3.0.5H2O", "U(+6)", 5.9, 6.1)
    return pd.concat([dense, sparse], ignore_index=True)


def run_self_test():
    print("Running self-test on synthetic data (schema-matched)...\n")
    cfg = dict(CONFIG)
    cfg["PILOT_SYSTEMS"] = [("goethite", None, "U(+6)"), ("ferrihydrite", None, "U(+6)")]
    cfg["OUTPUT_DIR"] = "outputs_selftest"

    df = prepare_data(_make_synthetic_dataset(), cfg)
    groups = group_by_system(df, cfg)
    systems = select_candidate_systems(groups, cfg["PILOT_SYSTEMS"])

    for label, sub in systems.items():
        m = {}
        m.update(audit_point_count(sub)); m.update(audit_pH_span(sub))
        m.update(audit_ionic_strength_levels(sub, THRESHOLDS["I_level_rounding_decimals"]))
        m.update(audit_joint_coverage(sub)); m.update(audit_missing_invalid(sub, cfg))
        m.update(audit_replicates_via_set(sub, cfg)); m.update(audit_study_consistency(sub, cfg))
        m.update(audit_temperature_consistency(sub)); m.update(audit_site_density(sub))
        m.update(audit_mineral_formula_consistency(sub, cfg))
        breakdown, ref_summary = reference_breakdown(sub, cfg, THRESHOLDS["I_level_rounding_decimals"])
        m.update(ref_summary)
        verdict, reason = verdict_for_system(m, THRESHOLDS)
        print(f"  {label}: {verdict} - {reason}")
        print(f"      site density: {m['site_density_status']}, n_sets: {m['n_sets']}, "
              f"references: {m['n_references']}, refs with real I variation: "
              f"{m['n_refs_with_sufficient_I_variation']}/{m['n_refs_total']} "
              f"({m['pct_points_in_I_varying_refs']}% of points)")

    print("\nExpected: goethite PASSes (or is MARGINAL); ferrihydrite FAILs "
          "(too few points, pH range too narrow); site density reads 'fixed, as expected' for both.\n")


def _performance_check(n=80_000):
    print(f"Performance check on a synthetic {n:,}-row table...")
    t0 = time.time()
    df = _make_synthetic_dataset(n_dense=n, n_sparse=0)
    df = prepare_data(df, CONFIG)
    groups = group_by_system(df, CONFIG)
    print(f"  Loaded, prepared, and grouped {n:,} rows in {time.time()-t0:.2f}s "
          f"({len(groups)} system(s) found)")
    sub = next(iter(groups.values()))
    t1 = time.time()
    estimate_initial_bandwidth(sub)
    print(f"  Bandwidth estimate on {len(sub):,}-row system in {time.time()-t1:.3f}s\n")


if __name__ == "__main__":
    run_self_test()
    _performance_check()

    if os.path.exists(CONFIG["DATA_FILE"]):
        print(f"Found '{CONFIG['DATA_FILE']}' - running the real audit...\n")
        report = run_audit(CONFIG, THRESHOLDS)
        print(report[["verdict", "reason", "n_points", "pH_span"]])
        print(f"\nFull report: {os.path.join(CONFIG['OUTPUT_DIR'], 'audit_table.csv')}")
    else:
        print(f"No data file at '{CONFIG['DATA_FILE']}'. Edit CONFIG and re-run.")