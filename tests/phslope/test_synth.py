import numpy as np
import pytest

from phslope.synth import (known_edge_set, planted_class_structure, random_truth, truth_response,
                           truth_slope)


@pytest.mark.parametrize("shape", ["rising", "falling", "bell", "two_step", "flat"])
def test_truth_slope_matches_numerical_derivative(shape):
    truth = random_truth(shape, np.random.default_rng(1))
    p = np.linspace(2, 11, 400)
    num = np.gradient(truth_response(truth, p), p)
    assert np.allclose(truth_slope(truth, p)[5:-5], num[5:-5], atol=2e-3)


def test_shapes_have_expected_direction():
    rng = np.random.default_rng(0)
    p = np.linspace(2, 11, 200)
    up = truth_response(random_truth("rising", rng), p)
    down = truth_response(random_truth("falling", rng), p)
    bell = truth_response(random_truth("bell", rng), p)
    assert up[-1] - up[0] > .7 and down[0] - down[-1] > .7
    assert bell.max() - bell[0] > .6 and bell.max() - bell[-1] > .6


def test_known_edge_set_is_reproducible_and_uneven():
    c1, o1, _ = known_edge_set(n_per_shape=3, seed=5)
    c2, o2, _ = known_edge_set(n_per_shape=3, seed=5)
    assert o1.equals(o2) and c1.equals(c2)
    gaps = np.diff(o1[o1.curve_id == c1.curve_id[0]]["pH"].to_numpy())
    assert gaps.std() > 0.05                          # uneven spacing
    assert set(c1["shape"]) == {"rising", "falling", "bell", "two_step", "flat"}


def test_planted_structure_shares_sum_to_one_and_null_has_no_class_effect():
    curves, planted = planted_class_structure(seed=0)
    assert abs(sum(planted["share"].values()) - 1) < 1e-12
    assert {"p50", "reference", "mineral_class", "sorbate_class"} <= set(curves.columns)
    # every mineral belongs to one class
    assert (curves.groupby("mineral")["mineral_class"].nunique() == 1).all()
    _, null = planted_class_structure(mineral_sd=0, sorbate_sd=0, interaction_sd=0, seed=0)
    assert null["share"]["mineral_class"] == 0 and np.all(null["effects"]["mineral_class"] == 0)
