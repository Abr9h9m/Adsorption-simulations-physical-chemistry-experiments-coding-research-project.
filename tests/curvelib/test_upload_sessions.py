from fastapi.testclient import TestClient

from curvelib.api import create_app


def test_app_starts_empty_and_upload_isolated_per_browser():
    app = create_app()
    first = TestClient(app)
    second = TestClient(app)

    assert first.get("/api/meta").json()["data"]["loaded"] is False
    assert first.get("/api/curves").status_code == 409

    raw = b"x,y\n1,2\n2,4\n3,6\n"
    response = first.post(
        "/api/upload",
        params={"name": "demo", "group_a": "__all__", "group_b": "__all__", "cluster": "__all__",
                "x": "x", "y": "y", "filename": "demo.csv"},
        content=raw,
    )
    assert response.status_code == 200, response.text
    assert first.get("/api/meta").json()["data"]["loaded"] is True
    assert len(first.get("/api/curves").json()["data"]) == 1

    assert second.get("/api/meta").json()["data"]["loaded"] is False
    assert second.get("/api/curves").status_code == 409
