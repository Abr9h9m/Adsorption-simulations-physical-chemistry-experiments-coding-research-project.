"""schemes.py -- EXPLORATORY groupings for Stage 2 (config/schemes.yaml).

Groupings come from four places:
  mineral_property  one T-vs-F split per column of Samuel's mineral property table
  mineral_scheme    categorical labels built from that table (first listed property that is T)
  sorbate_scheme    explicit sorbate -> label mappings
  condition_scheme  per-curve labels from the data (ionic-strength band, background anion,
                    carbonate, co-solute)

Each grouping is tested the same way, for each parameter in testing.parameters:
  - variance share of the grouping, REML model  value ~ 1 + (1 | group) + (1 | reference)
  - within-reference permutation test of the between-group share (labels shuffled only
    inside papers, so a paper's own offset cannot pass for a group effect)
p values are adjusted across ALL exploratory tests with Benjamini-Hochberg (q values).
None of this decides the Stage 2 go/no-go; that stays with classes.yaml.
"""
import os

import numpy as np
import pandas as pd

from phslope.common import PROJECT_ROOT, load_yaml
from phslope.load import split_signature
from phslope.reml import fit_reml
from phslope.variance import within_reference_permutation_test


def load_schemes():
    return load_yaml("schemes.yaml")


# ------------------------------------------------------------ property table

def load_mineral_properties(cfg, data_minerals=None):
    """Returns (props, report). props: index = mineral name as spelled in the data,
    columns = properties, values 1.0 (T), 0.0 (F), NaN (other codes or excluded row)."""
    mp = cfg["mineral_properties"]
    path = mp["file"] if os.path.isabs(mp["file"]) else os.path.join(PROJECT_ROOT, mp["file"])
    raw = pd.read_csv(path, index_col=0)
    raw["Mineral"] = raw["Mineral"].astype(str).str.strip()
    raw = raw.set_index("Mineral")
    codes = pd.Series(raw.to_numpy().ravel()).value_counts().to_dict()
    tc, fc = set(mp["true_codes"]), set(mp["false_codes"])
    props = raw.apply(lambda col: col.map(lambda v: 1.0 if v in tc else (0.0 if v in fc else np.nan)))
    excluded = {k: v for k, v in (mp.get("exclude_rows") or {}).items()}
    props.loc[props.index.isin(excluded)] = np.nan

    aliases = {k.lower(): v.lower() for k, v in (mp.get("aliases") or {}).items()}
    props.index = [aliases.get(n.lower(), n.lower()) for n in props.index]
    report = {"file": path, "cell_codes": codes, "excluded_rows": excluded, "n_rows": len(props)}
    if data_minerals is not None:
        lower = {m.lower(): m for m in data_minerals}
        report["data_minerals_without_row"] = sorted(m for m in data_minerals if m.lower() not in props.index)
        report["rows_not_in_data"] = sorted(n for n in props.index if n not in lower)
        props.index = [lower.get(n, n) for n in props.index]
    return props, report


def mineral_scheme_labels(props, spec):
    """First property (in listed order) that is T for the mineral -> its label; else `other`.
    Minerals whose row is all-NaN (excluded or missing) get NaN."""
    out = {}
    for m, row in props.iterrows():
        if row.isna().all():
            out[m] = np.nan
            continue
        lab = "other"
        for col, label in spec["from_properties"].items():
            if row.get(col) == 1.0:
                lab = label
                break
        out[m] = lab
    return pd.Series(out)


# ------------------------------------------------------------ conditions

def condition_labels(t, cfg):
    cs = cfg["condition_schemes"]
    out = {}
    b = cs["ionic_strength_band"]
    out["ionic_strength_band"] = pd.cut(t["ionic_strength"], bins=b["bins"], labels=b["labels"],
                                        right=False).astype(object)
    an = cs["background_anion"]

    def anion(sig):
        found = sorted({an["members"][p] for p in split_signature(sig) if p in an["members"]})
        return an["none_label"] if not found else (found[0] if len(found) == 1 else an["mixed_label"])

    out["background_anion"] = t["electrolyte_sig"].map(anion)
    out["carbonate"] = t[cs["carbonate"]].map({True: "carbonate_present", False: "no_carbonate"})
    out["cosolute"] = t[cs["cosolute"]].map({True: "cosolute_present", False: "no_cosolute"})
    return out


# ------------------------------------------------------------ all groupings

def merge_small(labels, min_n):
    counts = labels.value_counts()
    small = counts[counts < min_n].index
    return labels.where(~labels.isin(small), "other") if len(small) else labels


def build_groupings(t, cfg, props=None):
    """Returns list of dicts: name, kind, labels (Series aligned to t; NaN = not in this grouping)."""
    min_n = cfg["testing"]["min_curves_per_group"]
    g = []
    if props is not None:
        min_side = cfg["mineral_properties"]["min_minerals_per_side"]
        present = props.loc[props.index.isin(t["mineral"].unique())]
        for col in props.columns:
            v = present[col].dropna()
            if (v == 1).sum() >= min_side and (v == 0).sum() >= min_side:
                lab = t["mineral"].map(props[col].map({1.0: "T", 0.0: "F"}))
                g.append({"name": f"property: {col}", "kind": "mineral_property", "labels": lab})
        for name, spec in (cfg.get("mineral_schemes") or {}).items():
            lab = t["mineral"].map(mineral_scheme_labels(props, spec))
            g.append({"name": name, "kind": "mineral_scheme", "labels": lab})
    for name, mapping in (cfg.get("sorbate_schemes") or {}).items():
        g.append({"name": name, "kind": "sorbate_scheme", "labels": t["sorbate"].map(mapping)})
    for name, lab in condition_labels(t, cfg).items():
        g.append({"name": name, "kind": "condition_scheme", "labels": lab})
    for d in g:
        d["labels"] = merge_small(d["labels"].dropna(), min_n).reindex(t.index)
    return [d for d in g if d["labels"].nunique() >= 2]


# ------------------------------------------------------------ tests

def bh_adjust(p):
    p = np.asarray(p, float)
    q = np.full_like(p, np.nan)
    ok = np.isfinite(p)
    if not ok.any():
        return q
    pv = p[ok]
    order = np.argsort(pv)
    ranked = pv[order] * len(pv) / (np.arange(len(pv)) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(pv)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


def evaluate_grouping(t, labels, param, n_perm, seed):
    d = t.assign(group=labels)[["group", "reference", param]].dropna()
    row = {"parameter": param, "n_curves": len(d), "n_groups": d["group"].nunique(),
           "groups": "; ".join(f"{k} ({v})" for k, v in d["group"].value_counts().items())}
    if len(d) < 20 or d["group"].nunique() < 2:
        return {**row, "group_share": np.nan, "reference_share": np.nan, "p_value": np.nan}
    try:
        comp = fit_reml(d, param, {"group": "group", "reference": "reference"})["components"]
        tot = sum(comp.values())
        gs, rs = comp["group"] / tot, comp["reference"] / tot
    except ValueError:
        gs = rs = np.nan
    perm = within_reference_permutation_test(d, param, n_perm=n_perm, seed=seed, label_cols=("group",))
    return {**row, "group_share": gs, "reference_share": rs, "between_group_R2": perm["observed"],
            "p_value": perm["p_value"], "curves_shufflable": perm["n_curves_shufflable"]}


def run_exploratory(t, cfg, props, n_perm, seed):
    groupings = build_groupings(t, cfg, props)
    params = cfg["testing"]["parameters"]
    rows = []
    for gdef in groupings:
        for p in (["edge_pH"] if gdef["kind"] == "mineral_property" else params):
            if p not in t:
                continue
            rows.append({"grouping": gdef["name"], "kind": gdef["kind"],
                         **evaluate_grouping(t, gdef["labels"], p, n_perm, seed)})
    res = pd.DataFrame(rows)
    res["q_value"] = bh_adjust(res["p_value"])
    res["significant_fdr"] = res["q_value"] < cfg["testing"]["alpha"]
    return res.sort_values(["q_value", "p_value"]).reset_index(drop=True), groupings
