import numpy as np
import pandas as pd

from phslope.experiments.e03_audit import duplicate_pairs, lineage_clusters, match_share

CFG = {"match_pH": 0.02, "match_f": 0.01, "match_share": 0.8}


def test_match_share_uses_shorter_curve():
    a = np.array([[4.0, .1], [5.0, .5], [6.0, .9]])
    b = np.vstack([a + [0.01, 0.005], [[7.0, .95], [8.0, .97]]])
    assert match_share(a, b, .02, .01) == 1.0
    assert match_share(a, a + [0.05, 0], .02, .01) == 0.0


def _curves_obs():
    base = np.array([[4.0, .1], [5.0, .5], [6.0, .9], [7.0, .95]])
    rows, obs = [], []
    for cid, ref, shift in [("A1", "pA", 0), ("B1", "pB", 0.001), ("C1", "pC", 0.3), ("D1", "pD", 0.002)]:
        rows.append({"curve_id": cid, "reference": ref, "mineral": "goethite", "sorbate": "U(+6)"})
        obs.append(pd.DataFrame({"curve_id": cid, "pH": base[:, 0] + shift, "response": base[:, 1]}))
    return pd.DataFrame(rows), pd.concat(obs)


def test_duplicates_and_lineage_clusters():
    curves, obs = _curves_obs()
    dup = duplicate_pairs(curves, obs, CFG)
    linked = {frozenset((r.reference_a, r.reference_b)) for r in dup.itertuples()}
    assert linked == {frozenset(("pA", "pB")), frozenset(("pA", "pD")), frozenset(("pB", "pD"))}
    lin = lineage_clusters(["pA", "pB", "pC", "pD"], dup).set_index("reference")
    assert lin.loc["pA", "lineage_cluster"] == lin.loc["pB", "lineage_cluster"] == lin.loc["pD", "lineage_cluster"]
    assert lin.loc["pC", "cluster_size"] == 1 and lin.loc["pA", "cluster_size"] == 3
