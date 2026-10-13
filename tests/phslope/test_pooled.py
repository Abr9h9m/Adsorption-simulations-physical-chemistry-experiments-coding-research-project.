import numpy as np
import pandas as pd
import pytest

from phslope.common import load_config, load_thresholds
from phslope.pooled import band_labels, define_pools, residual_reference_r2, run
from phslope.schemes import load_schemes
from phslope.synth import logistic

BANDS = load_schemes()["condition_schemes"]["ionic_strength_band"]


def _data(study_sd, seed=0, n_refs=6, curves_per_ref=2, I_values=(0.1,)):
    """One mineral-sorbate pair; every paper shifts the edge by its own offset."""
    rng = np.random.default_rng(seed)
    rows, obs = [], []
    # evenly spaced paper offsets with SD ~= study_sd (random draws from 6 papers vary too much)
    offsets = study_sd * np.linspace(-1.5, 1.5, n_refs) / np.linspace(-1.5, 1.5, n_refs).std()
    for r in range(n_refs):
        off = offsets[r]
        for k in range(curves_per_ref):
            cid = f"r{r}_f{k}"
            I = I_values[(r + k) % len(I_values)]
            pH = np.sort(rng.uniform(3, 9, 14))
            y = logistic(pH, 0.02, 0.97, 6.0 + off, 0.35) + rng.normal(0, .02, 14)
            rows.append({"curve_id": cid, "reference": f"r{r}", "mineral": "goethite", "sorbate": "U(+6)",
                         "ionic_strength": I, "total_sorbate_mol_L": 1e-6, "solids_g_L": 1.0,
                         "co2_present": False, "has_cosolute": False})
            obs.append(pd.DataFrame({"curve_id": cid, "pH": pH, "response": y, "Reference": f"r{r}"}))
    curves = pd.DataFrame(rows)
    lib_meta = curves.assign(in_core_library=True, shape="rising", edge_pH=6.0, width=0.35)
    return curves, pd.concat(obs, ignore_index=True), lib_meta


def _cfg():
    cfg = load_config()
    cfg["pooled"] = {**cfg["pooled"], "point_bootstrap_B": 20, "cluster_bootstrap_B": 40}
    return cfg


def test_band_labels():
    assert list(band_labels(pd.Series([0.001, 0.05, 0.1, 1.0]), BANDS)) == [
        "low_below_0.01M", "medium_0.01_to_0.1M", "high_above_0.1M", "high_above_0.1M"]


def test_define_pools_by_band_and_all():
    curves, obs, _ = _data(0.0, I_values=(0.001, 0.5))
    band_pools, _ = define_pools(curves, obs, "pair_band", BANDS, load_config()["pooled"])
    all_pools, all_obs = define_pools(curves, obs, "pair_all", BANDS, load_config()["pooled"])
    assert len(band_pools) == 2 and len(all_pools) == 1
    assert all_pools["n_I_bands"].iloc[0] == 2 and all_pools["n_points"].iloc[0] == len(obs) == len(all_obs)
    assert all_pools["I_span_decades"].iloc[0] == pytest.approx(np.log10(500))


def test_residual_reference_r2():
    y = np.array([1., 1, 2, 2]); refs = np.array(["a", "a", "b", "b"])
    assert residual_reference_r2(y, np.zeros(4), refs) == pytest.approx(1.0)
    assert residual_reference_r2(np.array([1., 2, 1, 2]), np.zeros(4), refs) == pytest.approx(0.0)


def test_pooling_with_study_offsets_widens_edge_and_needs_cluster_interval():
    curves, obs, meta = _data(study_sd=0.8, seed=1)
    out = run(curves, obs, meta, _cfg(), load_thresholds()["qc"], BANDS, workers=1, modes=("pair_all",))
    t = out["pair_all"]["table"].iloc[0]
    assert t["width_ratio"] > 1.5
    assert t["resid_ref_R2"] > 0.25           # plateaus agree across papers, which dilutes the share
    assert (t["cluster_edge_hi"] - t["cluster_edge_lo"]) > 2 * (t["edge_hi"] - t["edge_lo"])


def test_pooling_without_offsets_is_harmless():
    curves, obs, meta = _data(study_sd=0.0, seed=2)
    out = run(curves, obs, meta, _cfg(), load_thresholds()["qc"], BANDS, workers=1, modes=("pair_all",))
    t = out["pair_all"]["table"].iloc[0]
    assert 0.7 < t["width_ratio"] < 1.3
    assert abs(t["edge_shift"]) < 0.15
    assert t["resid_ref_R2"] < 0.15
