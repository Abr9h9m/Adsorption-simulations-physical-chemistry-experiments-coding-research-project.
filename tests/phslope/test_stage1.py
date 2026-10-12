import numpy as np
import pytest

from phslope.common import load_config, load_thresholds
from phslope.library import build_library, core_subset, load_library, save_library
from phslope.slope import make_grid
from phslope.stage1 import curve_seed, process_curve, run_synthetic


@pytest.fixture(scope="module")
def small_run():
    cfg = load_config()
    lib, scores, _ = run_synthetic(cfg, load_thresholds()["qc"], None, workers=1, B=30, n_per_shape=6)
    return lib, scores


def test_curve_seed_is_stable_and_distinct():
    assert curve_seed(1, "a_f1") == curve_seed(1, "a_f1") != curve_seed(1, "a_f2")


def test_synthetic_slope_error_below_stage1_line(small_run):
    _, scores = small_run
    line = load_thresholds()["stage1"]["synthetic_median_slope_error_frac"]
    assert scores.loc[scores.true_shape != "flat", "slope_error"].median() < line


def test_library_shapes_and_nan_outside_mask(small_run):
    lib, _ = small_run
    n, G = len(lib["curve_ids"]), len(lib["grid"])
    for k in ("G", "lower", "upper", "G_logistic", "G_spline", "fitted", "F_logistic", "F_spline"):
        assert lib[k].shape == (n, G)
        assert np.isnan(lib[k][~lib["mask"]]).all()
    assert lib["draws"].shape == lib["draws_spline"].shape == (n, 30, G)


def test_library_roundtrip(tmp_path, small_run):
    lib, _ = small_run
    save_library(lib, tmp_path)
    back = load_library(tmp_path, with_draws=True)
    assert (back["curve_ids"] == lib["curve_ids"]).all()
    assert np.array_equal(back["G"], lib["G"], equal_nan=True)
    assert (core_subset(back) == core_subset(lib)).all()


def test_failed_curve_is_reported_not_dropped():
    cfg, thr = load_config(), load_thresholds()["qc"]
    cfg["bootstrap"]["B"] = 5
    r = process_curve("x", np.array([3., 3., 4.]), np.array([.1, .2, .5]), cfg, thr, make_grid(cfg), seed=0)
    assert "fit_failed" in r["meta"]["qc_flags"] and not r["meta"]["in_core_library"]
    assert r["meta"]["fit_errors"]
    lib = build_library([r], make_grid(cfg))
    assert len(lib["curve_ids"]) == 1
