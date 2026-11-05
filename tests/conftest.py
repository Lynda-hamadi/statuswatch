import os

# Doit être défini AVANT l'import de l'application
os.environ["DATABASE_URL"] = "sqlite:///./test_statuswatch.db"
os.environ.pop("ALERT_WEBHOOK_URL", None)

import pytest

from app.database import Base, SessionLocal, engine


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()