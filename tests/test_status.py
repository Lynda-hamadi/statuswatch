from fastapi.testclient import TestClient

from app.main import app
from app.models import Check, Target

client = TestClient(app)


def add_target(db, name="Site"):
    target = Target(name=name, url="https://example.com", interval_seconds=60)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def add_checks(db, target, *states):
    for is_up in states:
        db.add(
            Check(
                target_id=target.id,
                is_up=is_up,
                status_code=200 if is_up else None,
                response_ms=100,
            )
        )
    db.commit()


def test_cible_sans_verification_est_en_attente(db):
    add_target(db)
    item = client.get("/status").json()[0]
    assert item["status"] == "unknown"
    assert item["uptime_24h"] is None


def test_disponibilite_sur_24h(db):
    target = add_target(db)
    add_checks(db, target, True, True, True, False)
    item = client.get("/status").json()[0]
    assert item["status"] == "down"
    assert item["uptime_24h"] == 75.0


def test_la_page_echappe_le_html(db):
    add_target(db, name="<script>alert(1)</script>")
    page = client.get("/").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page