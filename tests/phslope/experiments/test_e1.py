"""E1 synthetic tests (protocol E1): planted level/slope, paper offsets, direction-specific solids
effect, loading hinge, partial-edge sampling; and a planted null."""
import numpy as np
import pandas as pd
import pytest

from phslope.experiments.e01_logk_mixed import E1Model, cross_validate
from phslope.experiments.kd import line_fit
from phslope.experiments.registry import load_exp_config

CFG = load_exp_config()["e1"]


def synth_curves(seed=0, solids_r=-0.8, solids_f=0.8, hinge=-0.5, paper_sd=0.3, n_pairs=12, n_papers=30,
                 partial_frac=0.3):
    """Curve table in the E1 format. log10K = a_c + b (pH - 6) with
    a_c = pair + paper + solids(direction) * log10 S + hinge * max(log10 L + 5, 0) + noise."""
    rng = np.random.default_rng(seed)
    pairs = [(f"m{i}", f"s{i}", "rising" if i % 3 else "falling") for i in range(n_pairs)]
    pair_eff = rng.normal(0, 0.8, n_pairs)
    pair_b = np.array([rng.uniform(0.8, 1.4) if p[2] == "rising" else -rng.uniform(0.5, 0.9) for p in pairs])
    paper_eff = rng.normal(0, paper_sd, n_papers)
    rows, obs = [], []
    for k in range(n_papers):
        for _ in range(rng.integers(2, 5)):
            j = rng.integers(n_pairs)
            m, s, shape = pairs[j]
            logS = rng.uniform(-1, 1)
            logT = rng.uniform(-7, -3)
            logL = logT - logS
            sol = solids_r if shape == "rising" else solids_f
            a_c = pair_eff[j] + paper_eff[k] + sol * logS + hinge * max(logL + 5, 0) + rng.normal(0, 0.15)
            b = pair_b[j] + rng.normal(0, 0.05)
            edge = 6 - a_c / b
            if rng.random() < partial_frac:      # sampled on one side of the edge only
                lo = edge + 0.2 if rng.random() < .5 else edge - 2.0
                pH = np.sort(rng.uniform(lo, lo + 1.8, 8))
            else:
                pH = np.sort(rng.uniform(edge - 1.5, edge + 1.5, 10))
            y = a_c + b * (pH - 6) + rng.normal(0, 0.05, len(pH))
            f = line_fit(pH, y)
            cid = f"c{len(rows)}"
            rows.append({"curve_id": cid, "reference": f"p{k}", "unit": f"p{k}", "mineral": m, "sorbate": s,
                         "shape": shape, "pair": f"{m} | {s}", "sorbate_class": f"S{j % 3}",
                         "a": f["a"], "b": f["b"], "pH_native": -f["a"] / f["b"], "true_edge": edge,
                         "partial": bool(pH.min() > edge or pH.max() < edge),
                         "log10_solids": logS, "log10_total": logT, "log10L": logL, "log10_I": -1.0,
                         "cosolute": 0.0, "co2": float(rng.random() < .5)})
            obs.append(pd.DataFrame({"curve_id": cid, "pH": pH, "log10K": y, "mid": True}))
    c = pd.DataFrame(rows)
    c["falling"] = (c["shape"] == "falling").astype(float)
    c["class_dir"] = c["sorbate_class"] + "|" + c["shape"]
    c["pair_dir"] = c["pair"] + "|" + c["shape"]
    return c, pd.concat(obs, ignore_index=True)


def test_recovers_planted_coefficients():
    c, _ = synth_curves(seed=1)
    m = E1Model(CFG).fit(c)
    beta = dict(zip(["intercept"] + m.level_fixed, m.fa["beta"]))
    se = dict(zip(["intercept"] + m.level_fixed, np.sqrt(np.diag(m.cov_a))))
    # pH_c differs from 6 per pair, which shifts levels but not the solids terms
    assert beta["solids_r"] == pytest.approx(-0.8, abs=max(3 * se["solids_r"], 0.15))
    assert beta["solids_f"] == pytest.approx(0.8, abs=max(3 * se["solids_f"], 0.25))
    assert m.bp == pytest.approx(-5.0, abs=0.75)


@pytest.fixture(scope="module")
def cv_run():
    c, obs = synth_curves(seed=2)
    return c, cross_validate(c, obs, CFG, covariates=True, seed=0)


def test_heldout_coverage_near_nominal(cv_run):
    _, P = cv_run
    cov = ((P["true_edge"] >= P["edge_lo"]) & (P["true_edge"] <= P["edge_hi"])).mean()
    assert 0.8 <= cov <= 0.99


def test_partial_edge_curves_unbiased_with_wider_intervals(cv_run):
    _, P = cv_run
    err = P["pred_edge"] - P["true_edge"]
    width = P["edge_hi"] - P["edge_lo"]
    assert abs(err[P["partial"]].median()) < 0.3
    # the partial curves' OWN line edge is an extrapolation; the model edge does not depend on it
    assert P["partial"].sum() >= 10 and width.median() > 0


def test_null_solids_effect_not_detected_too_often():
    hits = 0
    for seed in range(10):
        c, _ = synth_curves(seed=100 + seed, solids_r=0.0, solids_f=0.0, hinge=0.0)
        m = E1Model(CFG).fit(c)
        names = ["intercept"] + m.level_fixed
        i = names.index("solids_r")
        hits += abs(m.fa["beta"][i]) > 1.96 * np.sqrt(m.cov_a[i, i])
    assert hits <= 2
