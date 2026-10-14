"""P2 API tests (WEB_INTERFACE_PROTOCOL.md section 6). Uses the real file; skipped if absent."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(real_file):
    from curvelib.api import create_app
    return TestClient(create_app(data_path=real_file))


def test_meta_carries_status_and_versions(client):
    r = client.get("/api/meta").json()
    assert r["status"] == "exploratory" and r["schema_version"] == 1 and len(r["data_version"]) == 16
    assert r["data"]["rows"] == 38906 and r["data"]["has_picker"] and r["data"]["has_predict"]


def test_coverage_reproduces_census(client):
    t = client.get("/api/coverage").json()["data"]
    assert len(t) == 277 and sum(x["passes"] for x in t) == 76
    t2 = client.get("/api/coverage?min_points=0&min_clusters=1&min_x_span=0").json()["data"]
    assert sum(x["passes"] for x in t2) == 277


def test_sweep_monotone(client):
    s = client.get("/api/sweep?points=0,50,500&clusters=1,2").json()["data"]
    p = {(x["min_points"], x["min_clusters"]): x["pairs"] for x in s}
    assert p[(0, 1)] >= p[(50, 1)] >= p[(500, 1)] and p[(50, 1)] >= p[(50, 2)]


def test_periodic_table_counts_match_curves_endpoint(client):
    e = client.get("/api/entities").json()["data"]
    assert e["type"] == "periodic_table"
    u = next(c for c in e["cells"] if c["id"] == "U")
    cur = client.get("/api/curves", params=[("group_b", m) for m in u["members"]]).json()["data"]
    assert u["curves"] == len(cur) and u["papers"] == len({c["cluster"] for c in cur})
    assert not next(c for c in e["cells"] if c["id"] == "He")["has_data"]
    assert "Oxalic acid" in e["needs_review"]


def test_points_have_provenance_and_only_usable_rows(client):
    cur = client.get("/api/curves?group_a=goethite&group_b=U(%2B6)").json()["data"]
    pts = client.get("/api/points", params=[("curve_id", cur[0]["curve_id"])]).json()["data"]
    assert len(pts) == cur[0]["n_points"]
    assert {"x", "y", "Reference", "Mineral", "Sorbate", "Ionic_strength"} <= set(pts[0])


def test_fit_single_and_pooled(client):
    cur = client.get("/api/curves?group_a=goethite&group_b=U(%2B6)").json()["data"]
    one = client.get("/api/fit", params=[("curve_id", cur[0]["curve_id"])]).json()["data"]
    assert one["warning"] is None and one["n_clusters"] == 1 and set(one["params"]) == {"lo", "hi", "p50", "w"}
    papers = {}
    for c in cur:
        papers.setdefault(c["cluster"], c["curve_id"])
    ids = list(papers.values())[:3]
    pooled = client.get("/api/fit", params=[("curve_id", i) for i in ids]).json()["data"]
    assert pooled["n_clusters"] == len(ids) and "pooling" in pooled["warning"]
    assert pooled["intervals"] and pooled["intervals"]["p50"][0] <= pooled["params"]["p50"] <= pooled["intervals"]["p50"][1] + 1e-9


def test_fit_refused_on_too_few_points(client):
    r = client.get("/api/fit", params=[("curve_id", "nope||nope")])
    assert r.status_code == 400


def test_predict_and_leakage_guard(client):
    r = client.get("/api/predict", params={"group_a": "goethite", "group_b": "U(+6)", "solids_g_L": 1,
                                           "total_sorbate_mol_L": 1e-6, "ionic_strength": 0.1}).json()["data"]
    assert len(r["grid"]) == len(r["fraction"]) and any("EXPLORATORY" in n for n in r["notes"])
    from phslope.experiments.registry import read_locked
    from phslope.predictor import load_model
    m, _ = load_model()
    assert not set(m.train["reference"]) & read_locked()          # the model never saw a locked paper


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Curve Library" in r.text
