import numpy as np
import pandas as pd
import pytest

from phslope.experiments import kd
from phslope.experiments.registry import (choose_locked, drop_locked, final_papers, load_exp_config, locked_hash,
                                          read_locked)

CFG = load_exp_config()


def _obs(f, sorbed=None, aq=None, total=1e-6, solids=1.0):
    f = np.asarray(f, float)
    sorbed = f * total if sorbed is None else sorbed
    aq = (1 - f) * total if aq is None else aq
    return pd.DataFrame({"response": f, "Sorbed_val": sorbed, "Aq_val": aq, "total_sorbate_mol_L": total,
                         "solids_g_L": solids})


def test_k_identity_under_mass_balance():
    o = kd.add_kd(_obs([0.1, 0.5, 0.9]), CFG)
    assert np.allclose(o["K"], [0.1 / 0.9, 1.0, 9.0]) and (o["K_source"] == "reported").all()
    assert np.allclose(o["logit_f"], np.log([0.1 / 0.9, 1, 9]))


def test_inconsistent_aq_falls_back_to_mass_balance():
    o = kd.add_kd(_obs([0.5], aq=[0.9e-6]), CFG)       # aq disagrees with total - sorbed
    assert not o["mass_balance_ok"].iloc[0] and o["K_source"].iloc[0] == "mass_balance" and o["K"].iloc[0] == 1.0


def test_f_outside_unit_interval_gives_nan_not_leak():
    o = kd.add_kd(_obs([0.0, 1.0, 1.02], sorbed=[np.nan] * 3, aq=[np.nan] * 3), CFG)
    assert o["K"].isna().all() and o["logit_f"].isna().all() and (o["K_source"] == "none").all()


def test_missing_solids_gives_nan_kd():
    o = kd.add_kd(_obs([0.5], solids=np.nan), CFG)
    assert np.isnan(o["Kd_L_per_g"].iloc[0]) and np.isnan(o["log10L"].iloc[0])
    o2 = kd.add_kd(_obs([0.5], solids=2.0), CFG)
    assert o2["Kd_L_per_g"].iloc[0] == pytest.approx(0.5) and o2["loading_mol_per_g"].iloc[0] == pytest.approx(5e-7)


def test_mid_range_flag():
    o = kd.add_kd(_obs([0.02, 0.5, 0.98]), CFG)
    assert list(o["mid"]) == [False, True, False]


def test_line_fit():
    pH = np.array([4., 5, 6, 7])
    f = kd.line_fit(pH, 1.2 * pH - 6)
    assert f["a"] == pytest.approx(-6) and f["b"] == pytest.approx(1.2) and f["r2"] == pytest.approx(1)


def test_choose_locked_is_seeded_stratified_and_sized():
    papers = pd.DataFrame({"reference": [f"p{i}" for i in range(50)], "stratum": ["a"] * 30 + ["b"] * 20})
    a = choose_locked(papers, 0.2, 1)
    assert a == choose_locked(papers, 0.2, 1) and len(a) == 10
    assert sum(p in set(papers.reference[:30]) for p in a) == 6


def test_locked_set_exists_and_is_guarded():
    locked = read_locked()
    assert len(locked) == 24 and len(locked_hash()) == 12
    df = pd.DataFrame({"reference": sorted(locked)[:2] + ["not_locked_x"]})
    assert list(drop_locked(df)["reference"]) == ["not_locked_x"]
    with pytest.raises(PermissionError):
        final_papers()


@pytest.mark.slow
def test_harness_reproduces_followup_benchmark(real_file):
    from phslope.experiments import harness as H
    from phslope.experiments.data import build
    curves, _ = build(include_locked=True, purpose="test: harness regression check")
    c = H.benchmark_population(curves)
    got = H.benchmark_table(c, H.baseline_predictions(c))
    b, tol = CFG["e0"]["benchmark"], CFG["e0"]["benchmark"]["tolerance"]
    assert got["n_curves"] == b["n_curves"] and got["matched_subset_n"] == b["matched_subset_n"]
    for k_got, k_ref in [("B0_all_other", "all_other_median"), ("B1_nearest1", "nearest1_median"),
                         ("B2_nearest3", "nearest3_median"), ("B3_matched_fb", "matched_fb_median"),
                         ("matched_subset_plain", "matched_subset_plain_median"),
                         ("matched_subset_matched", "matched_subset_matched_median")]:
        assert abs(got[k_got] - b[k_ref]) <= tol, (k_got, got[k_got], b[k_ref])
