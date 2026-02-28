"""
Root conftest.py — shared fixtures for all test tiers.
"""

import os
import sys
import pytest
from pathlib import Path
from datetime import timedelta

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file so tests pick up real credentials (Braintree, etc.)
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Mark test mode BEFORE any app import touches startup events
os.environ["TESTING"] = "1"

# Ensure sane env vars before any import touches the DB
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:8604/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")


# ==========================================================================
# Helpers
# ==========================================================================

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


def _clear_login_protection():
    """Reset brute-force login protection state between tests."""
    try:
        from services.backend_api.middleware.login_protection import login_protection
        login_protection.reset()
    except Exception:
        pass


# ==========================================================================
# Core App & Client Fixtures
# ==========================================================================

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
    _clear_login_protection()


@pytest.fixture(scope="session")
def test_client(app):
    """Starlette TestClient wrapping the FastAPI app."""
    # Ensure the DB schema exists before any request hits the DB
    from services.backend_api.db.connection import init_db
    init_db()

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


# ==========================================================================
# Test User Factory & Auth Helpers
# ==========================================================================

TEST_PASSWORD = "TestPassword123!"


def make_auth_headers(email: str, role: str = "user", user_id: int = 1) -> dict:
    """
    Create a Bearer token header for any role without touching the DB.
    Useful for unit tests that just need a valid JWT.
    """
    from services.backend_api.utils.security import create_access_token
    token = create_access_token(
        data={"sub": email, "role": role, "user_id": user_id},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


def create_test_user(db, *, email: str, role: str = "user", password: str = TEST_PASSWORD) -> "models.User":
    """
    Insert a user row into the given DB session.  Returns the ORM instance.
    If the user already exists (by email), return the existing row.
    """
    from services.backend_api.db import models
    from services.backend_api.utils.security import get_password_hash

    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return existing

    user = models.User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=f"Test {role.title()}",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --------------- Pre-built per-role fixtures ---------------

@pytest.fixture
def user_headers():
    """Bearer headers for a standard 'user' role."""
    return make_auth_headers("testuser@careertrojan.com", role="user", user_id=100)


@pytest.fixture
def admin_headers():
    """Bearer headers for an 'admin' role."""
    return make_auth_headers("admin@careertrojan.com", role="admin", user_id=1)


@pytest.fixture
def mentor_headers():
    """Bearer headers for a 'mentor' role."""
    return make_auth_headers("mentor@careertrojan.com", role="mentor", user_id=200)


@pytest.fixture
def expired_headers():
    """Bearer headers with an already-expired token."""
    from services.backend_api.utils.security import create_access_token
    token = create_access_token(
        data={"sub": "expired@careertrojan.com", "role": "user", "user_id": 999},
        expires_delta=timedelta(seconds=-10),
    )
    return {"Authorization": f"Bearer {token}"}
