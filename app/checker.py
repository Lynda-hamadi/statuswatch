import time

import httpx
from sqlalchemy.orm import Session

from app.models import Check, Target
from app.security import UnsafeTarget, assert_public_url

TIMEOUT_SECONDS = 10


def run_check(db: Session, target: Target) -> Check:
    start = time.perf_counter()
    status_code = None
    error = None
    is_up = False

    try:
        assert_public_url(target.url)
        # Pas de suivi des redirections : une redirection pourrait mener vers une adresse interne.
        # Un code 3xx est considéré comme « en ligne » (moins de 400).
        response = httpx.get(target.url, timeout=TIMEOUT_SECONDS, follow_redirects=False)
        status_code = response.status_code
        is_up = response.status_code < 400
    except UnsafeTarget as exc:
        error = f"Cible refusée : {exc}"[:300]
    except httpx.HTTPError as exc:
        error = f"{type(exc).__name__}: {exc}"[:300]

    response_ms = int((time.perf_counter() - start) * 1000)

    check = Check(
        target_id=target.id,
        status_code=status_code,
        response_ms=response_ms,
        is_up=is_up,
        error=error,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check