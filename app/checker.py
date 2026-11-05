import time

import httpx
from sqlalchemy.orm import Session

from app.models import Check, Target

TIMEOUT_SECONDS = 10


def run_check(db: Session, target: Target) -> Check:
    start = time.perf_counter()
    status_code = None
    error = None
    is_up = False

    try:
        response = httpx.get(target.url, timeout=TIMEOUT_SECONDS, follow_redirects=True)
        status_code = response.status_code
        is_up = response.status_code < 400
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