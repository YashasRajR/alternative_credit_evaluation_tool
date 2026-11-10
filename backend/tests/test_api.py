"""The REST API, against an in-memory MongoDB."""
import pytest

import app as app_module
from profiles import GOOD, RISKY


@pytest.fixture
def client():
    return app_module.app.test_client()


def test_api_flow(client):
    r = client.post("/api/assessments", json=GOOD)
    assert r.status_code == 201
    doc = r.get_json()
    assert doc["id"] and doc["farmer"]["name"] == "Lakshmi"
    assert client.get(f"/api/assessments/{doc['id']}").get_json()["score"] == doc["score"]

    client.post("/api/assessments", json=RISKY)
    listed = client.get("/api/assessments?q=laks").get_json()
    assert [d["farmer"]["name"] for d in listed] == ["Lakshmi"]

    stats = client.get("/api/stats").get_json()
    assert stats["total"] >= 2 and sum(stats["bands"].values()) == stats["total"]

    assert client.delete(f"/api/assessments/{doc['id']}").status_code == 204
    assert client.get(f"/api/assessments/{doc['id']}").status_code == 404


def test_api_preview_does_not_save(client):
    before = client.get("/api/stats").get_json()["total"]
    r = client.post("/api/assessments?save=0", json=GOOD)
    assert r.status_code == 200 and "id" not in r.get_json()
    assert client.get("/api/stats").get_json()["total"] == before


def test_api_validation_error(client):
    r = client.post("/api/assessments", json={"name": "X"})
    assert r.status_code == 400 and "land" in r.get_json()["error"]


def test_bad_id_is_404(client):
    assert client.get("/api/assessments/not-an-id").status_code == 404
