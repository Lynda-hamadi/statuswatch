import pytest

from app import alerts
from app.models import Check, Target


def make_target(db) -> Target:
    target = Target(name="Site", url="https://example.com", interval_seconds=60)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def add_checks(db, target, *states):
    """Ajoute des vérifications, de la plus ancienne à la plus récente."""
    for is_up in states:
        db.add(
            Check(
                target_id=target.id,
                is_up=is_up,
                status_code=200 if is_up else None,
                error=None if is_up else "boom",
            )
        )
    db.commit()


@pytest.fixture()
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr(alerts, "send_alert", messages.append)
    return messages


def test_une_seule_panne_ne_declenche_pas_d_alerte(db, sent):
    target = make_target(db)
    add_checks(db, target, False)
    assert alerts.evaluate(db, target) is None
    assert sent == []


def test_deux_pannes_consecutives_declenchent_une_alerte(db, sent):
    target = make_target(db)
    add_checks(db, target, False, False)
    assert alerts.evaluate(db, target) == "down"
    assert len(sent) == 1


def test_une_panne_qui_continue_ne_renvoie_pas_d_alerte(db, sent):
    target = make_target(db)
    add_checks(db, target, False, False, False)
    assert alerts.evaluate(db, target) is None
    assert sent == []


def test_le_retour_en_ligne_declenche_une_alerte(db, sent):
    target = make_target(db)
    add_checks(db, target, False, False, True)
    assert alerts.evaluate(db, target) == "recovered"
    assert len(sent) == 1


def test_un_raté_isolé_ne_declenche_aucune_alerte(db, sent):
    target = make_target(db)
    add_checks(db, target, True, False, True)
    assert alerts.evaluate(db, target) is None
    assert sent == []