import httpx

from app import checker
from app.models import Target


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


def make_target(db) -> Target:
    target = Target(name="Site", url="https://example.com", interval_seconds=60)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def test_site_disponible(db, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", lambda *a, **k: FakeResponse(200))
    check = checker.run_check(db, make_target(db))
    assert check.is_up is True
    assert check.status_code == 200
    assert check.error is None


def test_erreur_http_est_une_panne(db, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", lambda *a, **k: FakeResponse(500))
    check = checker.run_check(db, make_target(db))
    assert check.is_up is False
    assert check.status_code == 500


def test_site_injoignable_ne_fait_pas_planter_le_verificateur(db, monkeypatch):
    def refuse(*args, **kwargs):
        raise httpx.ConnectError("connexion refusée")

    monkeypatch.setattr(checker.httpx, "get", refuse)
    check = checker.run_check(db, make_target(db))
    assert check.is_up is False
    assert check.status_code is None
    assert "ConnectError" in check.error