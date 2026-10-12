import numpy as np
import pytest

from phslope import report
from phslope.common import load_config, load_thresholds
from phslope.stage1 import run_synthetic
from phslope.stage2 import analysis_table, attach_classes, part_a, part_b


@pytest.fixture(scope="module")
def synth_lib():
    cfg = load_config()
    lib, _, _ = run_synthetic(cfg, load_thresholds()["qc"], None, workers=1, B=20, n_per_shape=30)
    m = lib["meta"]
    rng = np.random.default_rng(0)
    m["mineral"] = rng.choice(["goethite", "quartz", "kaolinite"], len(m), p=[.45, .45, .1])
    m["sorbate"] = rng.choice(["U(+6)", "Se(+4)", "Ni(+2)"], len(m))
    m["reference"] = rng.choice([f"r{i}" for i in range(8)], len(m))
    m["solids_g_L"], m["total_sorbate_mol_L"], m["ionic_strength"] = 1.0, 1e-6, 0.1
    m["co2_present"], m["temp"] = False, np.nan
    return lib, cfg


def test_part_a_runs_and_writes_outputs(tmp_path, synth_lib):
    lib, cfg = synth_lib
    a = part_a(lib, cfg, str(tmp_path))
    assert a["fpca"]["n_components"] >= 1
    assert (tmp_path / "registration_and_scores.csv").exists() and (tmp_path / "registration_and_fpca.png").exists()
    assert 0 <= a["variance_removed"]["all"] <= 1


def test_part_b_runs_with_classes_and_reports_unassigned(tmp_path, synth_lib):
    lib, cfg = synth_lib
    a = part_a(lib, cfg, str(tmp_path))
    classes = {"minerals": {"goethite": "iron_oxide_hydroxide", "quartz": "silica"},
               "sorbates": {"U(+6)": "actinide", "Se(+4)": "oxyanion", "Ni(+2)": "divalent_cation"}}
    b = part_b(lib["meta"], classes, a["scores"], cfg, load_thresholds(), str(tmp_path), B=3, n_perm=50, seed=0)
    assert b["unassigned"]["minerals"] == ["kaolinite"]
    assert b["verdict"]["verdict"].startswith(("PASS", "FAIL"))
    report.stage2_summary(str(tmp_path), lib, a, b, load_thresholds(),
                          {"git_commit": "x", "config_hash": "y", "data_file": "z", "run_at_utc": "t"})
    assert "Go/no-go" in (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")


def test_unconfirmed_summary_says_not_run(tmp_path, synth_lib):
    lib, cfg = synth_lib
    a = part_a(lib, cfg, str(tmp_path))
    report.stage2_summary(str(tmp_path), lib, a, None, load_thresholds(),
                          {"git_commit": "x", "config_hash": "y", "data_file": "z", "run_at_utc": "t"})
    assert "**Not run.**" in (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")


def test_classes_yaml_covers_every_name_in_data():
    """Every mineral and sorbate that appears in a pH curve has a proposed class."""
    import os
    import pandas as pd
    from phslope.common import REPORTS_DIR, load_yaml
    path = os.path.join(REPORTS_DIR, "stage0", "curves.csv")
    if not os.path.exists(path):
        pytest.skip("stage0 outputs not present")
    c = pd.read_csv(path)
    c = c[c["kind"] == "ph_sweep"]
    cls = load_yaml("classes.yaml")
    _, un = attach_classes(c.assign(), cls)
    assert un == {"minerals": [], "sorbates": []}
    assert set(cls["minerals"].values()) <= set(cls["mineral_classes"])
    assert set(cls["sorbates"].values()) <= set(cls["sorbate_classes"])
