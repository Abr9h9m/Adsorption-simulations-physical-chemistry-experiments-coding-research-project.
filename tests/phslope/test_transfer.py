"""Spec section 6 items 4 (planted transfer) and 5 (planted null transfer); cv metrics."""
import numpy as np
import pandas as pd
import pytest

from phslope.common import load_config
from phslope.cv import curve_metrics, paired_differences, run_cv, summarize
from phslope.synth import transfer_dataset
from phslope.transfer import rebuild

MODELS = ["global_mean", "sorbate_class_mean", "mineral_class_mean", "version_a"]


def _X(D):
    return {"version_a": D["t"][["d1", "d2"]].to_numpy(float), "version_b": D["t"][["d1", "d2"]].to_numpy(float)}


def test_rebuild_is_exact_for_logistic():
    u = np.arange(-6, 6.01, .25)
    s = 1 / (1 + np.exp(-u))
    grid = np.arange(2, 11.01, .25)
    g = rebuild(6.0, np.log(0.5), 0.9, s * (1 - s), u, grid)
    true = 0.9 / 0.5 * (lambda z: z * (1 - z))(1 / (1 + np.exp(-(grid - 6) / 0.5)))
    assert np.allclose(g, true, atol=0.01)


def test_curve_metrics_perfect_prediction():
    g = np.array([0.0, 0.2, 0.5, 0.2, 0.0])
    m = curve_metrics(g, g - .01, g + .01, g, np.ones(5, bool), g - .05, g + .05, 6.0, 6.0, 0.3, 0.9, "rising")
    assert m["p50_error"] == 0 and m["curve_error"] == 0 and m["shape_correct"] and m["sign_correct"]
    assert m["interval_coverage"] == 1.0 and m["p50_covered"]


@pytest.fixture(scope="module")
def planted():
    D = transfer_dataset(planted=True, seed=1)
    return D, run_cv(D, "study", MODELS + ["version_b"], _X(D), load_config()["fpca"])


def test_version_a_beats_baselines_on_planted_relationship(planted):
    D, pc = planted
    s = summarize(pc).set_index("model")
    for base in ("global_mean", "sorbate_class_mean", "mineral_class_mean"):
        assert s.loc["version_a", "median_p50_error"] < 0.6 * s.loc[base, "median_p50_error"], base
    diffs = paired_differences(pc, "version_a", ["global_mean"], B=200)
    assert diffs["p50_diff_hi"].iloc[0] < 0                          # whole interval below zero
    assert 0.7 <= s.loc["version_a", "p50_coverage"] <= 1.0


def test_version_b_runs_and_matches_a_on_logistic_shapes(planted):
    _, pc = planted
    s = summarize(pc).set_index("model")
    assert abs(s.loc["version_b", "median_p50_error"] - s.loc["version_a", "median_p50_error"]) < 1e-9
    assert s.loc["version_b", "median_curve_error"] < 1.5 * s.loc["version_a", "median_curve_error"]


def test_version_a_does_not_beat_global_mean_on_planted_null():
    D = transfer_dataset(planted=False, seed=2)
    pc = run_cv(D, "pair", ["global_mean", "version_a"], _X(D))
    diffs = paired_differences(pc, "version_a", ["global_mean"], B=200)
    assert diffs["p50_diff_lo"].iloc[0] < 0.0 < diffs["p50_diff_hi"].iloc[0] or diffs["p50_error_diff"].iloc[0] >= 0


def test_leave_pair_out_never_tests_on_a_training_pair():
    D = transfer_dataset(planted=True, seed=3, n_references=15)
    pc = run_cv(D, "pair", ["global_mean"], {})
    t = D["t"].set_index("curve_id")
    assert (pc["held_out"] == t.loc[pc["curve_id"], "pair"].to_numpy()).all()


def test_stage3_verdict_rules():
    from phslope.report import stage3_verdicts
    summ = pd.DataFrame([{"level": "study", "model": "version_a@x", "median_p50_error": 0.3, "interval_coverage": 0.9},
                         {"level": "study", "model": "version_b@x", "median_p50_error": 0.3, "interval_coverage": 0.6},
                         {"level": "study", "model": "global_mean", "median_p50_error": 1.0, "interval_coverage": 0.9}])
    diffs = pd.DataFrame([{"level": "study", "model": m, "baseline": "global_mean", "p50_diff_hi": -0.2,
                           "curve_diff_hi": -0.01} for m in ("version_a@x", "version_b@x")])
    thr = {"median_p50_error_max": 0.5, "coverage_min": 0.8, "coverage_max": 0.95, "margin_over_baseline": None}
    v = stage3_verdicts(summ, diffs, thr).set_index("model")
    assert v.loc["version_a@x", "verdict"] == "PASS" and v.loc["version_b@x", "verdict"] == "FAIL"


def test_freeze_status_reports_not_frozen():
    from phslope.stage3 import freeze_status
    ok, msg, _ = freeze_status()
    assert not ok and ("not frozen" in msg or "uncommitted" in msg)
