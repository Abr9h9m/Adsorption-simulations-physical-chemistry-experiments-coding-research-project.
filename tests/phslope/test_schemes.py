import numpy as np
import pandas as pd
import pytest

from phslope.schemes import (bh_adjust, build_groupings, condition_labels, load_mineral_properties,
                             load_schemes, merge_small, mineral_scheme_labels, evaluate_grouping)

CFG = load_schemes()


def _props_cfg(tmp_path, rows):
    cols = ["Mineral", "Silicates", "Iron-containing", "Oxyhydroxides", "Carbonate minerals"]
    df = pd.DataFrame(rows, columns=cols)
    df.index = df["Mineral"].to_numpy()
    path = tmp_path / "props.csv"
    df.to_csv(path)
    cfg = {"mineral_properties": {**CFG["mineral_properties"], "file": str(path),
                                  "exclude_rows": {"Calcite": "test"}}}
    return cfg


def test_property_codes_aliases_and_exclusions(tmp_path):
    cfg = _props_cfg(tmp_path, [["Goethite", "F", "T", "T", "F"], ["Lepidocrocite", "F", "TO", "T", "F"],
                                ["Calcite", "F", "F", "F", "F"], ["Clay ", "T", "O", "F", "F"]])
    props, rep = load_mineral_properties(cfg, ["goethite", "lepidocrosite", "calcite", "clay", "hematite"])
    assert props.loc["goethite", "Iron-containing"] == 1.0
    assert np.isnan(props.loc["lepidocrosite", "Iron-containing"])          # TO -> missing
    assert props.loc["calcite"].isna().all()                                 # excluded row
    assert np.isnan(props.loc["clay", "Iron-containing"]) and props.loc["clay", "Silicates"] == 1.0
    assert rep["data_minerals_without_row"] == ["hematite"]


def test_scheme_takes_first_true_property_in_order():
    props = pd.DataFrame({"Silicates": [1.0, 0.0, 0.0, np.nan], "Iron-containing": [1.0, 1.0, 0.0, np.nan]},
                         index=["iron clay", "goethite", "quartzish", "excluded"])
    lab = mineral_scheme_labels(props, {"from_properties": {"Silicates": "silicate", "Iron-containing": "iron"}})
    assert lab.to_dict()["iron clay"] == "silicate" and lab["goethite"] == "iron" and lab["quartzish"] == "other"
    assert np.isnan(lab["excluded"])


def test_condition_labels():
    t = pd.DataFrame({"ionic_strength": [0.001, 0.05, 0.5, 0.1],
                      "electrolyte_sig": ["N(+5)+Na(+1)", "Cl(-1)+Na(+1)", "Cl(-1)+N(+5)+Na(+1)", "Na(+1)"],
                      "co2_present": [True, False, False, True], "has_cosolute": [False, False, True, False]})
    lab = condition_labels(t, CFG)
    assert list(lab["ionic_strength_band"]) == ["low_below_0.01M", "medium_0.01_to_0.1M", "high_above_0.1M",
                                                "high_above_0.1M"]
    assert list(lab["background_anion"]) == ["nitrate", "chloride", "mixed", "no_simple_anion"]
    assert list(lab["carbonate"]) == ["carbonate_present", "no_carbonate", "no_carbonate", "carbonate_present"]


def test_merge_small_groups():
    s = pd.Series(["a"] * 6 + ["b"] * 2 + ["c"] * 1)
    assert merge_small(s, 5).value_counts().to_dict() == {"a": 6, "other": 3}


def test_bh_adjust_matches_known_values():
    q = bh_adjust([0.01, 0.04, 0.03, 0.2, np.nan])
    # sorted p: .01 .03 .04 .2 -> raw .04 .06 .0533 .2 -> step-up minimum -> .04 .0533 .0533 .2
    assert np.allclose(q[:4], [0.04, 0.16 / 3, 0.16 / 3, 0.2])
    assert np.isnan(q[4])


def test_grouping_detects_planted_condition_effect_within_papers():
    rng = np.random.default_rng(0)
    n_ref, per = 30, 6
    refs = np.repeat([f"r{i}" for i in range(n_ref)], per)
    grp = np.tile(["low", "high"], n_ref * per // 2)                 # every paper has both groups
    y = rng.normal(0, 0.3, n_ref * per) + np.repeat(rng.normal(0, 1, n_ref), per) + (grp == "high") * 0.8
    t = pd.DataFrame({"reference": refs, "edge_pH": y})
    r = evaluate_grouping(t, pd.Series(grp), "edge_pH", n_perm=300, seed=0)
    assert r["p_value"] < 0.01 and r["group_share"] > 0.05
    null = evaluate_grouping(t.assign(edge_pH=y - (grp == "high") * 0.8), pd.Series(grp), "edge_pH", 300, 0)
    assert null["p_value"] > 0.01


def test_every_sorbate_scheme_label_is_a_known_sorbate():
    import os
    from phslope.common import REPORTS_DIR
    path = os.path.join(REPORTS_DIR, "stage0", "curves.csv")
    if not os.path.exists(path):
        pytest.skip("stage0 outputs not present")
    sorbates = set(pd.read_csv(path)["sorbate"].dropna())
    for name, mapping in CFG["sorbate_schemes"].items():
        assert set(mapping) <= sorbates, (name, set(mapping) - sorbates)


def test_build_groupings_drops_single_group_schemes():
    t = pd.DataFrame({"mineral": ["a"] * 10, "sorbate": ["U(+6)"] * 10, "ionic_strength": [0.1] * 10,
                      "electrolyte_sig": ["N(+5)+Na(+1)"] * 10, "co2_present": [False] * 10,
                      "has_cosolute": [False] * 10})
    names = [g["name"] for g in build_groupings(t, CFG, None)]
    assert names == []


def test_prespecified_classes_are_reference_rows_outside_fdr():
    from phslope.schemes import run_exploratory
    rng = np.random.default_rng(1)
    n = 120
    t = pd.DataFrame({"mineral": rng.choice(["goethite", "quartz"], n), "sorbate": rng.choice(["U(+6)", "Se(+4)"], n),
                      "reference": rng.choice([f"r{i}" for i in range(15)], n), "ionic_strength": 0.1,
                      "electrolyte_sig": "N(+5)+Na(+1)", "co2_present": rng.random(n) < .5,
                      "has_cosolute": False, "edge_pH": rng.normal(6, 1, n), "log_width": 0.0, "height": 1.0})
    classes = {"minerals": {"goethite": "iron_oxide_hydroxide", "quartz": "silica"},
               "sorbates": {"U(+6)": "actinide", "Se(+4)": "oxyanion"}}
    res, _ = run_exploratory(t, CFG, None, n_perm=50, seed=0, classes=classes)
    pre = res[res["kind"] == "prespecified_class"]
    assert set(pre["grouping"]) == {"mineral_class (classes.yaml)", "sorbate_class (classes.yaml)"}
    assert pre["q_value"].isna().all() and pre["p_value"].notna().all()
    assert res.loc[res["kind"] != "prespecified_class", "q_value"].notna().any()
