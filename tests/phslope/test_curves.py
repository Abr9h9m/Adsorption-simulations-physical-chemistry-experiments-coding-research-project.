from phslope.curves import build_curves, signature_fragmentation
from phslope.load import clean_observations
from tests.phslope.conftest import make_raw


def test_curve_kinds(raw_small):
    curves, curve_obs = build_curves(clean_observations(raw_small))
    kinds = curves.set_index("curve_id")["kind"].to_dict()
    assert kinds == {"r1_f1": "ph_sweep", "r1_f2": "constant_ph", "r2_f1": "ph_sweep"}
    assert set(curve_obs["curve_id"]) == {"r1_f1", "r2_f1"}


def test_conditions_varying_inside_a_set_are_flagged():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [3, 5, 7, 9]}])
    raw.loc[2:, "Electrolyte1_val"] = 0.5          # ionic strength changes mid-curve
    curves, _ = build_curves(clean_observations(raw))
    assert curves["conditions_vary"].iloc[0]


def test_constant_conditions_not_flagged(raw_small):
    curves, _ = build_curves(clean_observations(raw_small))
    assert not curves.loc[curves["kind"] == "ph_sweep", "conditions_vary"].any()


def test_unit_mismatch_flag():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [3, 5, 7, 9], "sorbed_scale": 1000.0}])
    curves, _ = build_curves(clean_observations(raw))
    assert curves["unit_mismatch"].iloc[0]


def test_bad_ph_rows_not_used_in_curve():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [3, 5, 7, 70.3]}])
    curves, curve_obs = build_curves(clean_observations(raw))
    assert curves["n_points"].iloc[0] == 3 and curves["n_bad_ph"].iloc[0] == 1
    assert curve_obs["pH"].max() == 7


def test_cosolute_detection_ignores_background_salt():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [3, 5, 7]},                      # NaNO3
                    {"set": "b_f1", "ref": "a", "pH": [3, 5, 7], "e2": "P(+5)"}])     # Na + phosphate
    curves, _ = build_curves(clean_observations(raw))
    c = curves.set_index("curve_id")
    assert not c.loc["a_f1", "has_cosolute"]
    assert c.loc["b_f1", "has_cosolute"] and c.loc["b_f1", "cosolutes"] == "P(+5)"


def test_signature_fragmentation_counts():
    raw = make_raw([{"set": "a_f1", "ref": "a", "pH": [3, 5, 7]},
                    {"set": "a_f2", "ref": "a", "pH": [3, 5, 7], "e2": "S(+6)"}])
    curves, _ = build_curves(clean_observations(raw))
    frag = signature_fragmentation(None, curves)
    assert frag["n_signatures"].iloc[0] == 2 and frag["n_curves"].iloc[0] == 2


# --- real data ----------------------------------------------------------------

def test_real_sets_have_constant_conditions(real_obs):
    curves, _ = build_curves(real_obs)
    sweeps = curves[curves["kind"] == "ph_sweep"]
    assert len(sweeps) > 1000
    assert not sweeps["conditions_vary"].any()
