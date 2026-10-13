"""engine.py -- generic loader, validity accounting, curve builder, coverage and sweep (phases P0-P1).

Contains no domain words: everything is expressed through manifest roles. Domain columns are added by
the dataset's pack (`derived_by: pack.<name>.<function>`; response modes with `pack.` expressions).

Row accounting: every row ends in exactly one bucket (usable, or the first reason it is not), and the
buckets sum to the input row count. Every flag is counted.
"""
import importlib

import numpy as np
import pandas as pd

from curvelib.manifest import column, role_columns


def pack_function(ref):
    """'pack.<name>.<fn>' -> callable from packs/<name>/pack.py."""
    _, name, fn = ref.split(".")
    return getattr(importlib.import_module(f"packs.{name}.pack"), fn)


def load_rows(df, manifest):
    """Applies declared unit conversions and pack-derived columns; returns a copy."""
    d = df.copy()
    for role in ("group_a", "group_b", "cluster", "series"):          # trim stray whitespace in identifiers
        for col in role_columns(manifest, role):
            if col in d and d[col].dtype == object:
                d[col] = d[col].where(d[col].isna(), d[col].astype(str).str.strip())
    conv = manifest.get("unit_conversions", {})
    for c in manifest["columns"]:
        if "derived_by" in c:
            d[c["name"]] = pack_function(c["derived_by"])(d)
        elif "convert_to" in c:
            factors = conv[c["convert_to"]]
            d[c["name"] + "__" + c["convert_to"]] = (pd.to_numeric(d[c["name"]], errors="coerce")
                                                    * d[c["units_from"]].map(factors))
        elif c["name"] not in d.columns:
            raise KeyError(f"column '{c['name']}' declared in the manifest is not in the data")
    return d


def response(d, manifest, mode_id=None):
    modes = {m["id"]: m for m in manifest["response_modes"]}
    m = modes[mode_id or manifest["response_modes"][0]["id"]]
    if "column" in m:                                   # plain column, any name
        return pd.to_numeric(d[m["column"]], errors="coerce"), m
    expr = m["expr"]
    if expr.startswith("pack."):
        return pack_function(expr)(d), m
    # arithmetic over columns; names that are not identifiers are written in `backticks`
    num = d.apply(lambda s: pd.to_numeric(s, errors="coerce") if s.dtype == object else s)
    return num.eval(expr), m


def account_rows(d, manifest, mode_id=None):
    """Adds `_x`, `_y`, `_status` (usable or the first exclusion reason). Returns (rows, accounting table)."""
    x_col = manifest["curve"]["x"]
    d = d.copy()
    d["_x"] = pd.to_numeric(d[x_col], errors="coerce")
    d["_y"], _ = response(d, manifest, mode_id)
    lo, hi = manifest["curve"].get("x_valid_range", [-np.inf, np.inf])
    status = np.full(len(d), "usable", dtype=object)
    status[d["_y"].isna().to_numpy()] = "response missing"
    bad_x = (d["_x"].isna() | (d["_x"] < lo) | (d["_x"] > hi)).to_numpy()
    status[bad_x] = "sweep value missing or outside valid range"
    key = manifest["curve"]["key"]
    status[d[key].isna().any(axis=1).to_numpy()] = "curve key missing"
    d["_status"] = status
    acc = d["_status"].value_counts().rename_axis("status").reset_index(name="rows")
    assert acc["rows"].sum() == len(d)
    return d, acc


def build_curves(d, manifest, mode_id=None):
    """One row per curve with point counts, sweep span, sweep classification and response-range flag."""
    cfg = manifest["curve"]
    key = cfg["key"]
    a, b, cl = column(manifest, "group_a"), column(manifest, "group_b"), column(manifest, "cluster")
    _, mode = response(d.head(1), manifest, mode_id) if len(d) else (None, manifest["response_modes"][0])
    rng = mode.get("range")
    tol = mode.get("range_tolerance", 0.05)
    max_out = mode.get("max_out_of_range_frac", 0.05)
    u = d[d["_status"] == "usable"]
    g = u.groupby(key, sort=False)
    curves = pd.DataFrame({
        "n_points": g.size(),
        "n_x_levels": g["_x"].apply(lambda s: s.round(cfg.get("x_round", 2)).nunique()),
        "x_min": g["_x"].min(), "x_max": g["_x"].max(),
        "group_a": g[a].first(), "group_b": g[b].first(), "cluster": g[cl].first(),
    }).reset_index()
    curves["x_span"] = curves["x_max"] - curves["x_min"]
    curves["is_sweep"] = (curves["n_x_levels"] >= cfg.get("min_x_levels", 3)) & (curves["x_span"] >= cfg.get("min_x_span", 1.0))
    if rng is not None:
        out = g["_y"].apply(lambda s: ((s > rng[1] + tol) | (s < rng[0] - tol)).mean()).to_numpy()
        curves["response_out_of_range"] = out > max_out
    else:
        curves["response_out_of_range"] = False
    curves["clean"] = curves["is_sweep"] & ~curves["response_out_of_range"]
    return curves


def coverage(curves, min_points=None, min_clusters=None, min_x_span=None, manifest=None):
    """group_a x group_b table from clean curves: points, curves, clusters, sweep span, pass flag."""
    pc = (manifest or {}).get("pair_coverage", {})
    min_points = pc.get("min_points", 0) if min_points is None else min_points
    min_clusters = pc.get("min_clusters", 1) if min_clusters is None else min_clusters
    min_x_span = pc.get("min_x_span", 0.0) if min_x_span is None else min_x_span
    c = curves[curves["clean"]]
    g = c.groupby(["group_a", "group_b"])
    t = pd.DataFrame({"curves": g.size(), "points": g["n_points"].sum(), "clusters": g["cluster"].nunique(),
                      "x_min": g["x_min"].min(), "x_max": g["x_max"].max()}).reset_index()
    t["x_span"] = t["x_max"] - t["x_min"]
    t["passes"] = (t["points"] >= min_points) & (t["clusters"] >= min_clusters) & (t["x_span"] >= min_x_span)
    return t


def sweep(curves, points_grid, clusters_grid, min_x_span=0.0):
    """Number of passing pairs for every (min_points, min_clusters) combination (the threshold slider)."""
    base = coverage(curves, 0, 1, 0.0)
    rows = []
    for p in points_grid:
        for k in clusters_grid:
            ok = (base["points"] >= p) & (base["clusters"] >= k) & (base["x_span"] >= min_x_span)
            rows.append({"min_points": p, "min_clusters": k, "pairs": int(ok.sum())})
    return pd.DataFrame(rows)


def run(df, manifest, mode_id=None):
    """Convenience: rows -> accounting, curves, coverage."""
    d = load_rows(df, manifest)
    d, acc = account_rows(d, manifest, mode_id)
    curves = build_curves(d, manifest, mode_id)
    return {"rows": d, "accounting": acc, "curves": curves, "coverage": coverage(curves, manifest=manifest)}
