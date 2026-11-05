from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.checker import run_check
from app.database import Base, engine, get_db
from app.models import Check, Target
from app.schemas import CheckOut, TargetCreate, TargetOut

Base.metadata.create_all(bind=engine)

app = FastAPI(title="StatusWatch")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/targets", response_model=TargetOut, status_code=201)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)):
    target = Target(
        name=payload.name,
        url=str(payload.url),
        interval_seconds=payload.interval_seconds,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@app.get("/targets", response_model=list[TargetOut])
def list_targets(db: Session = Depends(get_db)):
    return db.scalars(select(Target).order_by(Target.id)).all()


@app.delete("/targets/{target_id}", status_code=204)
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Cible introuvable")
    db.delete(target)
    db.commit()


@app.post("/targets/{target_id}/check", response_model=CheckOut)
def check_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Cible introuvable")
    return run_check(db, target)


@app.get("/targets/{target_id}/checks", response_model=list[CheckOut])
def list_checks(
    target_id: int,
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if db.get(Target, target_id) is None:
        raise HTTPException(status_code=404, detail="Cible introuvable")
    return db.scalars(
        select(Check)
        .where(Check.target_id == target_id)
        .order_by(Check.id.desc())
        .limit(limit)
    ).all()