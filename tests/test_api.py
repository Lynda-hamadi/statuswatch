from fastapi.testclient import TestClient

from app import checker
from app.main import app

client = TestClient(app)


class FakeResponse:
    status_code = 200


def test_creer_puis_lister_une_cible(db):
    created = client.post("/targets", json={"name": "Google", "url": "https://www.google.com"})
    assert created.status_code == 201
    listed = client.get("/targets")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Google"


def test_url_invalide_est_refusee(db):
    response = client.post("/targets", json={"name": "Test", "url": "pas-une-url"})
    assert response.status_code == 422


def test_supprimer_une_cible_inconnue(db):
    assert client.delete("/targets/999").status_code == 404


def test_verifier_une_cible(db, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", lambda *a, **k: FakeResponse())
    target_id = client.post(
        "/targets", json={"name": "Google", "url": "https://www.google.com"}
    ).json()["id"]
    response = client.post(f"/targets/{target_id}/check")
    assert response.status_code == 200
    assert response.json()["is_up"] is True