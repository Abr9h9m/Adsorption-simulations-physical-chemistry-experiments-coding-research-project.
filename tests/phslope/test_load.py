import numpy as np
import pytest

import data_audit as da
from phslope.load import (clean_observations, is_valid_label, pair_label, split_pair_label,
                          split_signature, standardise_labels)
from tests.phslope.conftest import make_raw


def test_split_signature_keeps_charges_inside_labels():
    assert split_signature("C(+4)+Cl(+7)+Na(+1)") == ["C(+4)", "Cl(+7)", "Na(+1)"]
    assert split_signature("Cl(-1)+Humic acid+Na(+1)") == ["Cl(-1)", "Humic acid", "Na(+1)"]
    assert split_signature("") == [] and split_signature(None) == []


def test_pair_label_roundtrip_with_negative_oxidation_state():
    # The old "2)" junk label came from splitting "mineral-...-Se(-2)" on "-".
    assert split_pair_label(pair_label("goethite", "Se(-2)")) == ("goethite", "Se(-2)")


def test_label_validity_rule():
    assert not is_valid_label("2)") and not is_valid_label("U") and not is_valid_label("  ")
    assert is_valid_label("U(+6)") and is_valid_label("Pu") and is_valid_label("Humic acid")


def test_junk_sorbate_label_is_rejected():
    raw = make_raw([{"set": "a_f1", "ref": "a", "sorbate": "2)", "pH": [3, 4, 5]}])
    with pytest.raises(ValueError, match="Junk sorbate"):
        standardise_labels(da.prepare_data(raw, da.CONFIG))


def test_no_junk_sorbate_labels_after_load(raw_small):
    obs = clean_observations(raw_small)
    assert obs["Sorbate"].map(is_valid_label).all()
    assert "Se(-2)" in set(obs["Sorbate"])


def test_bad_ph_flagged_not_dropped():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [3, 5, 60.2, np.nan]}])
    obs = clean_observations(raw)
    assert len(obs) == 4
    assert obs["bad_ph"].tolist() == [False, False, True, True]


def test_nmol_total_converted_before_fraction():
    # Sorbed is in mol/L; total given as 1000 nmol/L = 1e-6 mol/L -> fraction 0.5
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [4, 5], "tot": 1e-6}])
    raw["Sorbate_val"] = 1000.0
    raw["Sorbate_units"] = "nmol/L"
    obs = clean_observations(raw)
    assert np.allclose(obs["total_sorbate_mol_L"], 1e-6)
    assert np.allclose(obs["response"], 0.5)


def test_solids_units():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [4], "solids": 500, "solids_units": "mg/L"},
                    {"set": "b_f1", "ref": "b", "pH": [4], "solids": 2, "solids_units": "mg/mL"},
                    {"set": "c_f1", "ref": "c", "pH": [4], "solids": 40, "solids_units": "m2/L"},
                    {"set": "d_f1", "ref": "d", "pH": [4], "solids": 3, "solids_units": "L/kg"}])
    obs = clean_observations(raw).set_index("Set")
    assert obs.loc["a_f1", "solids_g_L"] == pytest.approx(0.5)
    assert obs.loc["b_f1", "solids_g_L"] == pytest.approx(2.0)
    assert np.isnan(obs.loc["c_f1", "solids_g_L"]) and obs.loc["c_f1", "solids_m2_L"] == 40
    assert np.isnan(obs.loc["d_f1", "solids_g_L"]) and np.isnan(obs.loc["d_f1", "solids_m2_L"])


def test_carbonate_flag_from_gas_and_electrolyte():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [4], "gas": "CO2(g)", "gas_val": 3.5e-4},
                    {"set": "b_f1", "ref": "b", "pH": [4], "e2": "C(+4)"},
                    {"set": "c_f1", "ref": "c", "pH": [4]}])
    obs = clean_observations(raw).set_index("Set")
    assert obs.loc["a_f1", "co2_present"] and obs.loc["b_f1", "co2_present"]
    assert not obs.loc["c_f1", "co2_present"]


def test_ionic_strength_uses_corrected_nitrate_charge():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [4], "I": 0.1}])   # NaNO3 0.1 M
    obs = clean_observations(raw)
    assert obs["ionic_strength"].iloc[0] == pytest.approx(0.1)


# --- real data (skipped if the file is absent) -------------------------------

def test_real_no_junk_labels(real_obs):
    assert real_obs["Sorbate"].dropna().map(is_valid_label).all()
    assert real_obs["Mineral"].dropna().map(is_valid_label).all()


@pytest.mark.parametrize("mineral,sig,sorbate,expected", [
    ("goethite", "Cl(-1)+Na(+1)+P(+5)", "Se(+4)", 104),
    ("ferrihydrite", "N(+5)+Na(+1)+P(+5)", "U(+6)", 105),
    ("montmorillonite", "Cl(-1)+Na(+1)", "U(+6)", 66),
    # The spec quotes 205: that was after run_pipeline's I-varying-reference filter. Raw group = 275.
    ("goethite", "N(+5)+Na(+1)", "U(+6)", 275),
])
def test_real_known_subset_row_counts(real_obs, mineral, sig, sorbate, expected):
    m = (real_obs["Mineral"] == mineral) & (real_obs["electrolyte_sig"] == sig) & (real_obs["Sorbate"] == sorbate)
    assert m.sum() == expected
