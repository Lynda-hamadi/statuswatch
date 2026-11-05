import os
import socket

# Doit être défini AVANT l'import de l'application
os.environ["DATABASE_URL"] = "sqlite:///./test_statuswatch.db"
os.environ.pop("ALERT_WEBHOOK_URL", None)
os.environ.pop("ALLOW_PRIVATE_TARGETS", None)

import pytest

from app import security
from app.database import Base, SessionLocal, engine


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    """Par défaut, tous les noms de domaine se résolvent vers une adresse publique."""
    monkeypatch.setattr(
        security.socket,
        "getaddrinfo",
        lambda host, port, *a, **k: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ],
    )


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()