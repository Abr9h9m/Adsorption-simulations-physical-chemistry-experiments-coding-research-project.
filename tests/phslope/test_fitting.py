"""Tests for fit_edge, fit_smooth, slope, bootstrap (spec section 6, item 1)."""
import numpy as np
import pytest

from phslope import fit_edge, fit_smooth
from phslope.bootstrap import bootstrap_curve
from phslope.common import load_config
from phslope.slope import edge_summary, make_grid, observed_mask, on_grid
from phslope.synth import logistic, random_truth, sample_curve, truth_response, truth_slope

CFG = load_config()


def test_grid_is_spec_default():
    g = make_grid(CFG)
    assert len(g) == 37 and g[0] == 2.0 and g[-1] == 11.0 and np.allclose(np.diff(g), 0.25)


def test_no_extrapolation_outside_observed_range():
    g = make_grid(CFG)
    m = observed_mask(g, 4.1, 7.9)
    out = on_grid(lambda p: p * 0 + 1, g, m)
    assert np.isnan(out[g < 4.1]).all() and np.isnan(out[g > 7.9]).all() and (out[m] == 1).all()


@pytest.mark.parametrize("shape", ["rising", "falling"])
def test_logistic_recovers_p50_and_falling_edges(shape):
    rng = np.random.default_rng(3)
    errs = []
    for _ in range(15):
        t = random_truth(shape, rng)
        pH, y = sample_curve(t, rng, 15, 0.03)
        f = fit_edge.fit_logistic(pH, y, CFG["fit"], seed=1)
        errs.append(abs(f["p50"] - t["params"]["p50"]))
        assert (f["hi"] < f["lo"]) == (shape == "falling")
    assert np.median(errs) < 0.1


def test_logistic_slope_is_analytic():
    f = {"lo": 0.1, "hi": 0.9, "p50": 6.0, "w": 0.5}
    assert fit_edge.slope(f, 6.0) == pytest.approx(0.8 / (4 * 0.5))


def test_logistic_fails_loudly_with_too_few_ph_values():
    with pytest.raises(fit_edge.EdgeFitError):
        fit_edge.fit_logistic([3, 3, 4, 5], [0, .1, .5, .9], CFG["fit"])


def test_logistic_bounds_respected():
    pH = np.linspace(3, 9, 12)
    f = fit_edge.fit_logistic(pH, logistic(pH, 0, 1, 6, 0.01), CFG["fit"])   # step steeper than w_min
    assert f["w"] >= CFG["fit"]["w_min"] - 1e-12 and 2 <= f["p50"] <= 10


def test_smoother_tracks_bell_shape_and_needs_enough_levels():
    rng = np.random.default_rng(0)
    t = random_truth("bell", rng)
    pH, y = sample_curve(t, rng, 30, 0.02, ph_range=(2.5, 10.5), uneven=False)
    s = fit_smooth.fit_spline(pH, y, CFG["smooth"])
    p = np.linspace(3, 10, 50)
    assert np.sqrt(np.mean((fit_smooth.predict(s, p) - truth_response(t, p)) ** 2)) < 0.05
    with pytest.raises(fit_smooth.SmoothFitError):
        fit_smooth.fit_spline([3, 4, 5, 6], [0, .2, .6, .9], CFG["smooth"])


def test_replicates_are_averaged_with_weights():
    x, y, w = fit_smooth.aggregate_replicates([3, 3, 4, 5.001], [0.1, 0.3, 0.5, 0.7], 2)
    assert list(x) == [3, 4, 5] and np.allclose(y, [0.2, 0.5, 0.7]) and list(w) == [2, 1, 1]


def test_edge_summary_matches_p50_for_logistic():
    q = dict(lo=0.05, hi=0.95, p50=5.3, w=0.4)
    e = edge_summary(lambda p: logistic(p, **q), lambda p: fit_edge.slope(q, p), 2, 10)
    assert e["edge_pH"] == pytest.approx(5.3, abs=0.02) and e["sign"] == 1


def test_edge_summary_tracks_requested_edge_of_bell():
    t = random_truth("bell", np.random.default_rng(2))
    full = edge_summary(lambda p: truth_response(t, p), lambda p: truth_slope(t, p), 2, 11)
    q = t["params"]
    rise_level = q["lo"] + q["h"] / 2
    tracked = edge_summary(lambda p: truth_response(t, p), lambda p: truth_slope(t, p), 2, 11,
                           track=(rise_level, 1, q["p50"], 1.0))
    assert tracked["edge_pH"] == pytest.approx(q["p50"], abs=0.15)
    assert full["edge_pH"] in (pytest.approx(q["p50"], abs=0.3), pytest.approx(q["p50b"], abs=0.3))


def test_bootstrap_counts_failures_and_reports_percentiles():
    rng = np.random.default_rng(4)
    t = random_truth("rising", rng)
    pH, y = sample_curve(t, rng, 12, 0.03)
    grid = make_grid(CFG)
    mask = observed_mask(grid, pH.min(), pH.max())
    lf = fit_edge.fit_logistic(pH, y, CFG["fit"])
    sf = fit_smooth.fit_spline(pH, y, CFG["smooth"])
    b = bootstrap_curve(pH, y, lf, sf, grid, mask, CFG, B=40, seed=0)
    for k in ("logistic", "spline"):
        o = b[k]
        assert o["slopes"].shape == (40, len(grid)) and 0 <= o["n_fail"] <= 40
        lo, mid, hi = o["slope_pct"]
        assert np.all((lo[mask] <= mid[mask] + 1e-12) & (mid[mask] <= hi[mask] + 1e-12))
        assert np.isnan(lo[~mask]).all()


@pytest.mark.slow
def test_logistic_bootstrap_interval_covers_true_p50_about_nominally():
    rng = np.random.default_rng(11)
    grid = make_grid(CFG)
    hits = []
    for i in range(40):
        t = random_truth("rising", rng)
        pH, y = sample_curve(t, rng, 15, 0.03)
        lf = fit_edge.fit_logistic(pH, y, CFG["fit"], seed=i)
        b = bootstrap_curve(pH, y, lf, None, grid, observed_mask(grid, pH.min(), pH.max()), CFG, B=60, seed=i)
        lo, _, hi = b["logistic"]["edge_pct"]
        hits.append(lo <= t["params"]["p50"] <= hi)
    assert 0.8 <= np.mean(hits) <= 1.0
