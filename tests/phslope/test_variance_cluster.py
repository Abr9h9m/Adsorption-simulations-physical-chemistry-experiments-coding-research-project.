"""Spec section 6, items 2 (planted structure), 3 (null control), 6 (study-effect swamp)."""
import numpy as np
import pandas as pd
import pytest

from phslope.cluster import ari_test, permanova, pseudo_f
from phslope.synth import planted_class_structure
from phslope.variance import (cell_share, fit_components, shares, stage2_verdict, variance_split,
                              within_reference_permutation_test)

BIG = dict(n_mineral_classes=8, n_sorbate_classes=8, minerals_per_class=2, sorbates_per_class=2,
           n_references=120, pairs_per_reference=(2, 4))


def test_cell_share_basic():
    assert cell_share([1, 1, 3, 3], np.array([0, 0, 1, 1])) == pytest.approx(1.0)
    assert cell_share([1, 3, 1, 3], np.array([0, 0, 1, 1])) == pytest.approx(0.0)


def test_variance_split_recovers_planted_shares():
    curves, planted = planted_class_structure(mineral_sd=0.8, sorbate_sd=0.8, interaction_sd=0.3, study_sd=0.4,
                                              residual_sd=0.2, seed=3, **BIG)
    sh = shares(fit_components(curves, "p50")["components"])
    # compare with the shares implied by the REALIZED effects (8 levels each is too few to hit
    # the population values); tolerance 0.15 absolute
    eff = planted["effects"]
    realized = {"mineral_class": np.var(eff["mineral_class"]), "sorbate_class": np.var(eff["sorbate_class"]),
                "mineral_sorbate": np.var(eff["interaction"]), "reference": np.var(eff["reference"]),
                "residual": planted["sd"]["residual"] ** 2}
    tot = sum(realized.values())
    for k, v in realized.items():
        assert abs(sh[k] - v / tot) < 0.15, (k, sh[k], v / tot)


def test_permutation_test_detects_planted_classes():
    curves, _ = planted_class_structure(seed=4, **BIG)
    r = within_reference_permutation_test(curves, "p50", n_perm=300, seed=0)
    assert r["p_value"] < 0.05 and r["n_refs_shufflable"] > 0


@pytest.mark.slow
def test_null_control_false_positive_rate_near_nominal():
    """Item 3: no class effects, real study offsets -> rejections near 5%."""
    rejections = []
    for rep in range(100):
        curves, _ = planted_class_structure(mineral_sd=0, sorbate_sd=0, interaction_sd=0, study_sd=0.8,
                                            seed=1000 + rep)
        rejections.append(within_reference_permutation_test(curves, "p50", n_perm=200, seed=rep)["p_value"] < 0.05)
    assert np.mean(rejections) <= 0.10


def test_study_swamp_is_reported_as_study_dominates():
    """Item 6: study offsets much larger than class effects -> Stage 2 stops."""
    curves, _ = planted_class_structure(mineral_sd=0.15, sorbate_sd=0.15, interaction_sd=0.05, study_sd=2.0,
                                        seed=5, **BIG)
    split = variance_split(curves, "p50", B=0)
    perm = within_reference_permutation_test(curves, "p50", n_perm=200, seed=0)
    v = stage2_verdict(split, perm, 0.05)
    assert v["verdict"] == "FAIL (study dominates)"


def test_planted_classes_pass_verdict():
    curves, _ = planted_class_structure(study_sd=0.2, seed=6, **BIG)
    v = stage2_verdict(variance_split(curves, "p50", B=0),
                       within_reference_permutation_test(curves, "p50", n_perm=200, seed=0), 0.05)
    assert v["verdict"] == "PASS"


def test_bootstrap_intervals_bracket_point_share():
    curves, _ = planted_class_structure(seed=7)
    s = variance_split(curves, "p50", B=15, seed=0)
    ok = s.dropna(subset=["share_lo"])
    assert len(ok) and s.attrs["n_boot"] >= 10
    assert ((ok["share_lo"] <= ok["share"] + 0.05) & (ok["share"] <= ok["share_hi"] + 0.05)).all()


def test_ari_and_permanova_detect_structure_and_respect_null():
    rng = np.random.default_rng(0)
    labels = np.repeat(["a", "b", "c"], 40)
    refs = np.tile(np.arange(20), 6).astype(str)          # every paper has every class
    centers = {"a": [0, 0], "b": [4, 0], "c": [0, 4]}
    X = np.array([centers[l] for l in labels]) + rng.normal(0, .7, (120, 2))
    assert ari_test(X, labels, refs, n_perm=200)["p_value"] < 0.05
    assert permanova(X, labels, refs, n_perm=200)["p_value"] < 0.05
    Xnull = rng.normal(0, 1, (120, 2))
    assert permanova(Xnull, labels, refs, n_perm=200)["p_value"] > 0.01


def test_pseudo_f_matches_one_way_anova_for_euclidean_1d():
    x = np.array([1., 2, 3, 7, 8, 9])
    lab = np.array([0, 0, 0, 1, 1, 1])
    F, _ = pseudo_f((x[:, None] - x[None, :]) ** 2, lab)
    ssb = 3 * ((2 - 5) ** 2 + (8 - 5) ** 2)
    ssw = 2 + 2
    assert F == pytest.approx((ssb / 1) / (ssw / 4))


def test_fast_reml_matches_statsmodels():
    from phslope.variance import fit_components_statsmodels
    curves, _ = planted_class_structure(n_references=25, seed=8)
    fast = fit_components(curves, "p50")["components"]
    slow = fit_components_statsmodels(curves, "p50")["components"]
    for k in fast:
        assert fast[k] == pytest.approx(slow[k], rel=0.05, abs=1e-3), (k, fast[k], slow[k])
