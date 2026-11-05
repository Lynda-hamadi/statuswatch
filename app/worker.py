import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.alerts import evaluate
from app.checker import run_check
from app.database import Base, SessionLocal, engine
from app.models import Check, Target

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

TICK_SECONDS = 5


def due_targets(db: Session) -> list[Target]:
    """Cibles dont la dernière vérification date de plus que leur intervalle."""
    now = datetime.now(timezone.utc)
    due = []
    for target in db.scalars(select(Target)):
        last = db.scalars(
            select(Check.checked_at)
            .where(Check.target_id == target.id)
            .order_by(Check.id.desc())
            .limit(1)
        ).first()
        if last is None:
            due.append(target)
            continue
        if last.tzinfo is None:  # SQLite renvoie des dates sans fuseau horaire
            last = last.replace(tzinfo=timezone.utc)
        if (now - last).total_seconds() >= target.interval_seconds:
            due.append(target)
    return due


def main() -> None:
    Base.metadata.create_all(bind=engine)
    log.info("Worker démarré (vérification toutes les %s s)", TICK_SECONDS)
    while True:
        try:
            with SessionLocal() as db:
                for target in due_targets(db):
                    check = run_check(db, target)
                    log.info(
                        "%s -> %s (%s ms)",
                        target.name,
                        "UP" if check.is_up else "DOWN",
                        check.response_ms,
                    )
                    evaluate(db, target)
        except Exception:
            # Une erreur imprévue ne doit jamais arrêter le worker
            log.exception("Erreur pendant le cycle de vérification")
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()