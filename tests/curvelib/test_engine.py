"""P0-P1 tests (WEB_INTERFACE_PROTOCOL.md sections 5-6)."""
import copy
import os

import numpy as np
import pandas as pd
import pytest

from curvelib import engine as E
from curvelib import manifest as M

SORPTION = "packs/sorption/manifest.yaml"


def generic_manifest(names):
    """A non-sorption manifest with arbitrary column names (property test helper)."""
    g1, g2, cl, se, x, y = names
    return {"schema_version": 1, "dataset": {"id": "demo_x", "title": "demo", "source": "synthetic", "status": "demo"},
            "columns": [{"name": g1, "role": "group_a"}, {"name": g2, "role": "group_b"},
                        {"name": cl, "role": "cluster"}, {"name": se, "role": "series"},
                        {"name": x, "role": "sweep_x"}, {"name": y, "role": "value"}],
            "response_modes": [{"id": "raw", "column": y, "range": [0, 1]},
                               {"id": "scaled", "expr": f"`{y}` * 100"}],
            "curve": {"key": [cl, se], "x": x, "min_x_levels": 3, "min_x_span": 1.0},
            "pair_coverage": {"min_points": 10, "min_clusters": 2, "min_x_span": 2.0}}


def synthetic_rows(names, seed=0):
    from phslope.synth import random_truth, sample_curve
    g1, g2, cl, se, x, y = names
    rng = np.random.default_rng(seed)
    rows = []
    for k in range(40):
        t = random_truth(rng.choice(["rising", "falling"]), rng)
        xs, ys = sample_curve(t, rng, int(rng.integers(5, 12)), 0.02)
        for xv, yv in zip(xs, ys):
            rows.append({g1: f"A{k % 4}", g2: f"B{k % 3}", cl: f"c{k % 10}", se: f"s{k}", x: xv, y: yv})
    return pd.DataFrame(rows)


def test_sorption_manifest_is_valid():
    m = M.load(SORPTION)
    assert M.column(m, "cluster") == "Reference"


@pytest.mark.parametrize("mutate,msg", [
    (lambda m: m["columns"].append({"name": "x", "role": "nonsense"}), "is not one of"),
    (lambda m: m["columns"].pop(0), "group_a"),
    (lambda m: m["columns"].append({"name": "Q", "role": "covariate", "convert_to": "g/L"}), "units_from"),
    (lambda m: m["columns"].append({"name": "Q", "role": "covariate", "units_from": "u", "convert_to": "zz"}), "no unit_conversions"),
    (lambda m: m["curve"].update({"key": ["Nope"]}), "curve/key"),
    (lambda m: m.update({"surprise": 1}), "Additional properties"),
])
def test_invalid_manifests_rejected_with_clear_errors(mutate, msg):
    m = copy.deepcopy(M.load(SORPTION))
    mutate(m)
    with pytest.raises(M.ManifestError, match=msg):
        M.validate(m)


@pytest.mark.parametrize("names", [("mat", "subst", "lab", "run", "dose", "resp"),
                                   ("Région", "x2", "study id", "series", "T_K", "y value")])
def test_generic_dataset_round_trips_with_any_column_names(names):
    m = M.validate(generic_manifest(names))
    df = synthetic_rows(names)
    r = E.run(df, m)
    assert r["accounting"]["rows"].sum() == len(df)
    assert len(r["curves"]) == 40
    cov = r["coverage"]
    assert cov["curves"].sum() == r["curves"]["clean"].sum()
    scaled, _ = E.response(r["rows"], m, "scaled")
    assert np.allclose(scaled, r["rows"]["_y"] * 100, equal_nan=True)
    s = E.sweep(r["curves"], [0, 10, 1000], [1, 2])
    assert s.set_index(["min_points", "min_clusters"]).loc[(1000, 2), "pairs"] == 0


def test_row_accounting_buckets():
    names = ("a", "b", "c", "s", "x", "y")
    m = M.validate(generic_manifest(names) | {"curve": {"key": ["c", "s"], "x": "x", "x_valid_range": [0, 14]}})
    df = synthetic_rows(names).head(30)
    df.loc[0, "y"] = np.nan
    df.loc[1, "x"] = 99
    df.loc[2, "c"] = np.nan
    d, acc = E.account_rows(E.load_rows(df, m), m)
    a = acc.set_index("status")["rows"]
    assert a["response missing"] == 1 and a["sweep value missing or outside valid range"] == 1
    assert a["curve key missing"] == 1 and a.sum() == 30


def test_census_parity_on_real_file(real_file):
    m = M.load(SORPTION)
    r = E.run(pd.read_csv(real_file, low_memory=False), m)
    c, cov = r["curves"], r["coverage"]
    assert int(c["is_sweep"].sum()) == 1704 and int(c["clean"].sum()) == 1680
    assert len(cov) == 277 and int(cov["passes"].sum()) == 76
    s0 = os.path.join("reports", "phslope", "stage0", "pair_table.csv")
    if os.path.exists(s0):
        t = pd.read_csv(s0).merge(cov, left_on=["mineral", "sorbate"], right_on=["group_a", "group_b"])
        assert len(t) == 277 and (t["n_points"] == t["points"]).all() and (t["n_references"] == t["clusters"]).all()
