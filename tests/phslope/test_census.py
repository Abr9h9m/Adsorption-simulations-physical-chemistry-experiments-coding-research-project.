import pandas as pd

from phslope.census import descriptor_templates, gap_list, pair_table
from phslope.common import load_thresholds

THR = {"pair_min_points": 10, "pair_min_ph_span": 4.0, "pair_min_references": 2, "min_passing_pairs": 1}


def _curves(rows):
    base = dict(kind="ph_sweep", unit_mismatch=False, conditions_vary=False, solids_reported=True,
                total_sorbate_reported=True, has_cosolute=False, co2_present=False)
    return pd.DataFrame([{**base, **r} for r in rows])


def test_pair_rule_needs_points_span_and_two_references():
    c = _curves([
        dict(mineral="g", sorbate="U", reference="r1", n_points=6, pH_min=3, pH_max=6),
        dict(mineral="g", sorbate="U", reference="r2", n_points=6, pH_min=5, pH_max=8),   # passes jointly
        dict(mineral="g", sorbate="Se", reference="r1", n_points=30, pH_min=3, pH_max=9),  # one reference
        dict(mineral="h", sorbate="U", reference="r1", n_points=30, pH_min=3, pH_max=5),
        dict(mineral="h", sorbate="U", reference="r2", n_points=30, pH_min=3, pH_max=5),   # span 2
    ])
    t = pair_table(c, THR).set_index(["mineral", "sorbate"])
    assert t.loc[("g", "U"), "passes"] and t.loc[("g", "U"), "pH_span"] == 5
    assert not t.loc[("g", "Se"), "passes"] and not t.loc[("h", "U"), "passes"]


def test_unclean_curves_not_counted():
    c = _curves([dict(mineral="g", sorbate="U", reference="r1", n_points=50, pH_min=3, pH_max=9),
                 dict(mineral="g", sorbate="U", reference="r2", n_points=50, pH_min=3, pH_max=9,
                      unit_mismatch=True)])
    t = pair_table(c, THR)
    assert t["n_references"].iloc[0] == 1 and not t["passes"].iloc[0]


def test_gap_list_includes_empty_cells():
    c = _curves([dict(mineral="g", sorbate="U", reference=r, n_points=20, pH_min=3, pH_max=9) for r in "ab"]
                + [dict(mineral="h", sorbate="Se", reference="a", n_points=5, pH_min=3, pH_max=9)])
    gaps, _, _ = gap_list(pair_table(c, THR), 2, 2, THR)
    cells = {(r.mineral, r.sorbate): r.reason for r in gaps.itertuples()}
    assert cells[("g", "Se")] == "empty" and cells[("h", "U")] == "empty"
    assert "references" in cells[("h", "Se")] and ("g", "U") not in cells


def test_descriptor_templates_never_overwrite_filled(tmp_path):
    c = pd.DataFrame({"mineral": ["goethite", "quartz"], "sorbate": ["U(+6)", "Se(+4)"]})
    descriptor_templates(c, tmp_path)
    filled = tmp_path / "mineral_descriptors.csv"
    filled.write_text("mineral,pzc_low\ngoethite,8.0\n")
    descriptor_templates(c, tmp_path)
    assert filled.read_text() == "mineral,pzc_low\ngoethite,8.0\n"
    t = pd.read_csv(tmp_path / "sorbate_descriptors_template.csv")
    assert list(t["sorbate"]) == ["Se(+4)", "U(+6)"] and t.drop(columns="sorbate").isna().all().all()


def test_thresholds_file_has_stage0_rule():
    thr = load_thresholds()["stage0"]
    assert thr == {"pair_min_points": 50, "pair_min_ph_span": 4.0, "pair_min_references": 2,
                   "min_passing_pairs": 60}
