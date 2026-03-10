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

# Ensure sane env vars before any import touches the DB
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")


def _clear_rate_limiter_hits(app_instance):
    """Walk ASGI middleware stack and clear in-memory rate limiter counters."""
    obj = getattr(app_instance, "middleware_stack", app_instance)
    for _ in range(30):
        if hasattr(obj, "_hits"):
            obj._hits.clear()
            return
        obj = getattr(obj, "app", None)
        if obj is None:
            return


@pytest.fixture(scope="session")
def app():
    """Create the FastAPI app instance (session-scoped to avoid repeated boot)."""
    from services.backend_api.main import app as _app
    return _app


@pytest.fixture(scope="session", autouse=True)
def reset_test_database_schema():
    """Ensure test DB schema matches current models for each full test run."""
    from services.backend_api.db.models import Base
    from services.backend_api.db.connection import engine

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def reset_rate_limiter_between_tests(app):
    """Avoid cross-test throttling side effects from in-memory limiter state."""
    _clear_rate_limiter_hits(app)
    yield
    _clear_rate_limiter_hits(app)


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
