import numpy as np
import pytest

from phslope import qc
from phslope.common import load_config, load_thresholds
from phslope.synth import random_truth, truth_response, truth_slope

CFG, THR = load_config()["shape"], load_thresholds()["qc"]
P = np.linspace(2, 11, 200)


@pytest.mark.parametrize("shape,expected", [("rising", "rising"), ("falling", "falling"), ("bell", "bell"),
                                            ("two_step", "multi_step"), ("flat", "flat")])
def test_shape_class_on_true_curves(shape, expected):
    rng = np.random.default_rng(7)
    for _ in range(5):
        t = random_truth(shape, rng)
        assert qc.shape_class(P, truth_response(t, P), truth_slope(t, P), CFG) == expected


def test_noise_wiggles_do_not_create_moves():
    f = 0.5 + 0.05 * np.sin(P * 5)
    assert qc.shape_class(P, f, np.gradient(f, P), CFG) == "flat"
    rising = 1 / (1 + np.exp(-(P - 6) / .4)) + 0.04 * np.sin(P * 7)
    assert qc.shape_class(P, rising, np.gradient(rising, P), CFG) == "rising"


def test_trough_is_unclassified():
    f = 1 - np.exp(-((P - 6) ** 2))
    assert qc.shape_class(P, f, np.gradient(f, P), CFG) == "unclassified"


def test_replicate_scatter_needs_enough_groups():
    assert np.isnan(qc.replicate_scatter([3, 3, 4, 5], [.1, .2, .5, .9], 2, 2))
    s = qc.replicate_scatter([3, 3, 4, 4, 5], [.1, .3, .5, .7, .9], 2, 2)
    assert s == pytest.approx(np.std([.1, .3], ddof=1))


def test_poor_fit_limit_uses_replicates_or_ceiling():
    assert qc.poor_fit_limit(0.02, THR) == pytest.approx(0.04)
    assert qc.poor_fit_limit(np.nan, THR) == THR["poor_fit_ceiling"]


def test_edge_bracketing():
    assert qc.edge_bracketed([4, 5.8, 6.3, 8], 6.0, 0.5)
    assert not qc.edge_bracketed([4, 5, 7, 8], 6.0, 0.5)


def _info(**kw):
    base = dict(n_points=12, pH_span=5, unit_mismatch=False, shape="rising", edge_pH=6.0,
                pH=np.array([3, 4, 5, 5.8, 6.2, 7, 8, 9.]), rmse=0.02, rep_scatter=np.nan, edge_ci_width=0.3,
                boot_fail_frac=0.0, fit_failed=False)
    return {**base, **kw}


def test_clean_curve_has_no_flags_and_enters_core():
    assert qc.flags_for(_info(), THR) == []
    assert qc.in_core_library([], "rising") and not qc.in_core_library([], "unclassified")


@pytest.mark.parametrize("kw,flag", [
    (dict(n_points=6), "too_few_points"), (dict(pH_span=2), "narrow_span"),
    (dict(unit_mismatch=True), "unit_mismatch"), (dict(edge_pH=8.9), "edge_not_bracketed"),
    (dict(rmse=0.2), "poor_fit"), (dict(edge_ci_width=1.5), "wide_interval"),
    (dict(edge_ci_width=np.nan), "wide_interval"), (dict(boot_fail_frac=0.3), "bootstrap_unstable"),
])
def test_each_flag_fires(kw, flag):
    assert flag in qc.flags_for(_info(**kw), THR)


def test_flat_curves_skip_edge_flags():
    f = qc.flags_for(_info(shape="flat", edge_pH=np.nan, edge_ci_width=np.nan), THR)
    assert "edge_not_bracketed" not in f and "wide_interval" not in f
