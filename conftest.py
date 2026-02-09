"""
Root conftest.py — shared fixtures for all test tiers.
"""

import os
import sys
import pytest
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file so tests pick up real credentials (Braintree, etc.)
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Ensure sane env vars before any import touches the DB
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")


def _clear_rate_limiter(app):
    """Walk the ASGI middleware stack to find and reset the rate limiter."""
    obj = getattr(app, "middleware_stack", app)
    for _ in range(20):
        if hasattr(obj, "_hits"):
            obj._hits.clear()
            return
        obj = getattr(obj, "app", None)
        if obj is None:
            break


@pytest.fixture(scope="session")
def app():
    """Create the FastAPI app instance (session-scoped to avoid repeated boot)."""
    from services.backend_api.main import app as _app
    return _app


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Auto-reset the rate limiter before every test so no test hits 429."""
    from services.backend_api.main import app as _app
    _clear_rate_limiter(_app)


@pytest.fixture(scope="session")
def test_client(app):
    """Starlette TestClient wrapping the FastAPI app."""
    from starlette.testclient import TestClient
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def db_session():
    """Provide a SQLAlchemy session backed by an in-memory SQLite database."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from services.backend_api.db.models import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()
