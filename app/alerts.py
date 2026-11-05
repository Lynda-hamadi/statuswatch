import logging
import os

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Check, Target

log = logging.getLogger("alerts")

WEBHOOK_URL = os.getenv("ALERT_WEBHOOK_URL")
FAILURES_BEFORE_ALERT = 2


def send_alert(message: str) -> None:
    log.warning("ALERTE : %s", message)
    if not WEBHOOK_URL:
        return
    try:
        # Format compatible avec les webhooks Discord
        httpx.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    except httpx.HTTPError:
        log.exception("Impossible d'envoyer l'alerte au webhook")


def evaluate(db: Session, target: Target) -> str | None:
    """Envoie une alerte si l'état du site vient de changer. Retourne 'down', 'recovered' ou None."""
    n = FAILURES_BEFORE_ALERT
    # Du plus récent au plus ancien : n vérifications, plus une pour détecter le changement
    recent = db.scalars(
        select(Check)
        .where(Check.target_id == target.id)
        .order_by(Check.id.desc())
        .limit(n + 1)
    ).all()

    if len(recent) < n:
        return None

    latest = recent[:n]
    if all(not c.is_up for c in latest) and (len(recent) == n or recent[n].is_up):
        reason = latest[0].error or f"code HTTP {latest[0].status_code}"
        send_alert(f"🔴 {target.name} est HORS SERVICE ({target.url}) : {reason}")
        return "down"

    if len(recent) == n + 1 and recent[0].is_up and all(not c.is_up for c in recent[1:]):
        send_alert(f"🟢 {target.name} est de nouveau disponible ({target.url})")
        return "recovered"

    return None