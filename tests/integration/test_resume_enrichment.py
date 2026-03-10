"""
Integration test for POST /api/resume/v1/enrich
Verifies that enrichment:
  - 404s when the user has no resume
  - 200s with the expected { ok, data.enrichment.keywords } shape
    when a resume exists in the JSON DB
"""
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from services.backend_api.main import app
from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _ensure_user(email="testuser@example.com"):
    """Make sure a User row exists for the given email and return its id."""
    db = next(get_db())
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            hashed_password=security.get_password_hash("Test1234!"),
            full_name="Test User",
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def _make_token(email="testuser@example.com", role="user"):
    return security.create_access_token(data={"sub": email, "role": role})


# A minimal resume record matching the shape written by upload_resume()
_RESUME_RECORD = {
    "resume_id": "test-resume-001",
    "user_id": "PLACEHOLDER",          # filled at runtime
    "filename": "test_cv.pdf",
    "uploaded_at": "2025-06-01T00:00:00Z",
    "raw_text": "Python developer with 5 years of experience in FastAPI and ML.",
    "parsed_json": {
        "name": "Test User",
        "skills": ["Python", "FastAPI", "Machine Learning"],
        "experience": [{"title": "Software Engineer", "company": "Acme"}],
        "education": [{"degree": "BSc Computer Science"}],
        "certifications": [],
        "job_titles": ["Software Engineer", "ML Engineer"],
    },
    "skills": ["Python", "FastAPI", "Machine Learning"],
    "word_count": 12,
}


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
class TestResumeEnrich:
    """POST /api/resume/v1/enrich"""

    def test_enrich_no_resume_returns_404(self):
        """When user has no resume → 404."""
        user = _ensure_user()
        headers = {"Authorization": f"Bearer {_make_token()}"}
        client = TestClient(app)

        # Patch load_resume_db to return empty DB
        with patch("services.backend_api.routers.resume.load_resume_db", return_value={}):
            resp = client.post("/api/resume/v1/enrich", headers=headers)

        assert resp.status_code == 404

    def test_enrich_returns_enrichment_payload(self):
        """When user has a resume → 200 with enrichment data."""
        user = _ensure_user()
        headers = {"Authorization": f"Bearer {_make_token()}"}
        client = TestClient(app)

        record = {**_RESUME_RECORD, "user_id": str(user.id)}
        fake_db = {"test-resume-001": record}

        with patch("services.backend_api.routers.resume.load_resume_db", return_value=fake_db):
            resp = client.post("/api/resume/v1/enrich", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert "enrichment" in body["data"]

        enrichment = body["data"]["enrichment"]
        # keywords should be present (might be a list or dict depending on models)
        assert "keywords" in enrichment
        # skills_detected must always be present (normalisation fallback)
        assert "skills_detected" in enrichment

    def test_enrich_graceful_on_orchestrator_failure(self):
        """If the orchestrator throws, endpoint still returns 200 with partial data."""
        user = _ensure_user()
        headers = {"Authorization": f"Bearer {_make_token()}"}
        client = TestClient(app)

        record = {**_RESUME_RECORD, "user_id": str(user.id)}
        fake_db = {"test-resume-001": record}

        # Make the lazy import inside enrich() raise by temporarily removing
        # the orchestrator module from sys.modules and making re-import fail.
        import sys
        key = "services.backend_api.services.enrichment.ai_enrichment_orchestrator"
        saved = sys.modules.pop(key, None)
        # Insert a broken module stub so the import inside enrich() blows up
        import types
        broken = types.ModuleType(key)
        broken.AIEnrichmentOrchestrator = type(
            "AIEnrichmentOrchestrator", (), {
                "__init__": lambda self, *a, **kw: None,
                "get_dashboard_enrichment": lambda self, *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
            },
        )
        sys.modules[key] = broken

        try:
            with patch("services.backend_api.routers.resume.load_resume_db", return_value=fake_db):
                resp = client.post("/api/resume/v1/enrich", headers=headers)
        finally:
            # restore
            sys.modules.pop(key, None)
            if saved is not None:
                sys.modules[key] = saved

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        enrichment = body["data"]["enrichment"]
        assert enrichment["keywords"] == []
        assert "error" in enrichment
