"""Kd response variant (PHSLOPE_RESPONSE=kd): Kd = 1000 * Sorbed / (solids * Aq), response = Kd / (Kd + 1000)."""
import os
import subprocess
import sys
from io import StringIO

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run(code, mode):
    env = dict(os.environ, PHSLOPE_RESPONSE=mode)
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                          check=True).stdout.strip()


def test_output_dirs_are_separate():
    code = "from phslope.common import REPORTS_DIR, EXPORT_DIR; print(REPORTS_DIR); print(EXPORT_DIR)"
    frac, kd = _run(code, "fraction").splitlines(), _run(code, "kd").splitlines()
    assert frac[0].endswith(os.path.join("reports", "phslope")) and frac[1].endswith("export")
    assert kd[0].endswith(os.path.join("reports", "phslope_kd")) and kd[1].endswith("export_kd")


def test_kd_formula_and_response_identity():
    code = r"""
import pandas as pd, numpy as np
from phslope.load import add_kd_response
df = pd.DataFrame({"Sorbed_val": [6e-7, 9.9e-7, np.nan, 1e-6, 5e-7], "Aq_val": [4e-7, 1e-8, 2e-7, 0.0, 5e-7]})
out = pd.DataFrame({"total_sorbate_mol_L": [1e-6] * 5, "solids_g_L": [2.0, 0.5, 1.0, 1.0, np.nan],
                    "response": [0.6, 0.99, 0.8, 1.0, 0.5]})
add_kd_response(out, df)
print(out[["Kd_L_kg", "response", "kd_source"]].to_json(orient="split"))
"""
    r = pd.read_json(StringIO(_run(code, "kd")), orient="split")
    assert np.isclose(r["Kd_L_kg"][0], 1000 * 6e-7 / (2.0 * 4e-7))          # the formula as given
    assert np.isclose(r["response"][0], r["Kd_L_kg"][0] / (r["Kd_L_kg"][0] + 1000))
    assert np.isclose(r["response"][1], 9.9e-7 / (9.9e-7 + 1e-8 * 0.5))
    assert r["kd_source"][2] == "mass_balance" and np.isclose(r["Kd_L_kg"][2], 1000 * 8e-7 / 2e-7)
    assert r["response"][3] == 1.0 and pd.isna(r["Kd_L_kg"][3])              # Aq = 0: all sorbed, Kd infinite
    assert pd.isna(r["response"][4]) and r["kd_source"][4] == "none"          # no solids: missing, never zero


def test_solids_term_not_applied_twice():
    code = "import numpy as np; from phslope.common import solids_term; print(solids_term(np.array([0.5, np.nan])).tolist())"
    assert _run(code, "fraction") == "[0.5, nan]" and _run(code, "kd") == "[0.0, nan]"
