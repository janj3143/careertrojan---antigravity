"""
Integration tests for GDPR endpoints and admin AI-loop endpoints.
Tests hit real HTTP endpoints via the test client.
"""
import pytest
from starlette.testclient import TestClient

from services.backend_api.main import app
from services.backend_api.db.connection import engine
from services.backend_api.db.models import Base
from services.backend_api.utils import security

# ── Setup ─────────────────────────────────────────────────────
# Create tables in the test DB (in-memory SQLite from conftest.py)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def _get_auth_headers(email: str = "gdpr-test@careertrojan.com", role: str = "user"):
    """Create a valid JWT for testing authenticated endpoints."""
    token = security.create_access_token(data={"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


def _get_admin_headers():
    return _get_auth_headers("admin@careertrojan.com", "admin")


def _ensure_user(db, email="gdpr-test@careertrojan.com", role="user"):
    """Create a test user in the DB if not present."""
    from services.backend_api.db.models import User
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, hashed_password="xxx", full_name="GDPR Test", role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ── GDPR Consent Tests ───────────────────────────────────────

@pytest.mark.integration
class TestGDPRConsent:

    def test_consent_requires_auth(self):
        r = client.get("/api/gdpr/v1/consent")
        assert r.status_code in (401, 403)

    def test_grant_consent(self):
        # First create the user in DB
        from services.backend_api.db.connection import SessionLocal
        db = SessionLocal()
        _ensure_user(db)
        db.close()

        headers = _get_auth_headers()
        r = client.post("/api/gdpr/v1/consent?consent_type=terms&granted=true", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "recorded"
        assert data["consent_type"] == "terms"
        assert data["granted"] is True

    def test_get_consent_records(self):
        headers = _get_auth_headers()
        r = client.get("/api/gdpr/v1/consent", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["consent_type"] == "terms"

    def test_invalid_consent_type(self):
        headers = _get_auth_headers()
        r = client.post("/api/gdpr/v1/consent?consent_type=invalid_type", headers=headers)
        assert r.status_code == 422


# ── GDPR Data Export Tests ────────────────────────────────────

@pytest.mark.integration
class TestGDPRExport:

    def test_export_requires_auth(self):
        r = client.get("/api/gdpr/v1/export")
        assert r.status_code in (401, 403)

    def test_export_returns_data_bundle(self):
        headers = _get_auth_headers()
        r = client.get("/api/gdpr/v1/export", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "export_date" in data
        assert "user" in data
        assert "profile" in data
        assert "resumes" in data
        assert "consent_records" in data
        assert "interactions" in data
        assert data["user"]["email"] == "gdpr-test@careertrojan.com"


# ── GDPR Audit Log Tests ─────────────────────────────────────

@pytest.mark.integration
class TestGDPRAuditLog:

    def test_audit_log_requires_auth(self):
        r = client.get("/api/gdpr/v1/audit-log")
        assert r.status_code in (401, 403)

    def test_audit_log_returns_entries(self):
        headers = _get_auth_headers()
        r = client.get("/api/gdpr/v1/audit-log", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        # Should have at least the consent_grant + data_export entries from previous tests
        assert len(data) >= 2
        actions = {e["action"] for e in data}
        assert "consent_grant" in actions
        assert "data_export" in actions


# ── GDPR Account Deletion Tests ──────────────────────────────

@pytest.mark.integration
class TestGDPRDeletion:

    def test_delete_requires_confirm(self):
        headers = _get_auth_headers()
        r = client.delete("/api/gdpr/v1/delete-account", headers=headers)
        assert r.status_code == 400
        assert "confirm=yes" in r.json()["detail"]

    def test_delete_account_full_erasure(self):
        """Create a fresh user, then delete them — verify all data is gone."""
        from services.backend_api.db.connection import SessionLocal
        from services.backend_api.db.models import User, ConsentRecord, AuditLog
        db = SessionLocal()

        # Create the delete-test user
        doomed_email = "delete-me@careertrojan.com"
        _ensure_user(db, doomed_email)
        doomed_user = db.query(User).filter(User.email == doomed_email).first()
        assert doomed_user is not None

        # Grant consent so there's something to delete
        headers = _get_auth_headers(doomed_email)
        client.post("/api/gdpr/v1/consent?consent_type=terms&granted=true", headers=headers)

        # Now delete
        r = client.delete(f"/api/gdpr/v1/delete-account?confirm=yes", headers=headers)
        assert r.status_code == 200
        assert r.json()["status"] == "deleted"

        # Verify user is anonymised
        db.expire_all()
        user = db.query(User).filter(User.id == doomed_user.id).first()
        assert user is not None  # row retained for referential integrity
        assert "anon" in user.email
        assert user.full_name is None
        assert user.is_active is False

        # Verify consent records are gone
        consents = db.query(ConsentRecord).filter(ConsentRecord.user_id == doomed_user.id).all()
        assert len(consents) == 0

        # Verify audit log still has the deletion entry (legal requirement)
        audit = db.query(AuditLog).filter(
            AuditLog.user_id == doomed_user.id,
            AuditLog.action == "account_delete"
        ).first()
        assert audit is not None

        db.close()


# ── Admin AI-Loop Endpoint Tests ──────────────────────────────

@pytest.mark.integration
class TestAdminAILoopEndpoints:

    def test_system_activity_requires_admin(self):
        r = client.get("/api/admin/v1/system/activity", headers=_get_auth_headers())
        # Regular user should get 401 or 403 depending on auth flow
        assert r.status_code in (401, 403)

    def test_system_activity_works_for_admin(self):
        from services.backend_api.db.connection import SessionLocal
        db = SessionLocal()
        _ensure_user(db, "admin@careertrojan.com", "admin")
        db.close()

        r = client.get("/api/admin/v1/system/activity", headers=_get_admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert "new_users_24h" in data
        assert "interactions_24h" in data
        assert "timestamp" in data

    def test_dashboard_snapshot(self):
        r = client.get("/api/admin/v1/dashboard/snapshot", headers=_get_admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert "users" in data
        assert "resumes" in data
        assert "ai_data" in data
        assert "recent_audit_events" in data

    def test_compliance_summary(self):
        r = client.get("/api/admin/v1/compliance/summary", headers=_get_admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert "consent_records" in data
        assert "data_export_requests" in data
        assert "account_deletions" in data

    def test_audit_events_admin(self):
        r = client.get("/api/admin/v1/compliance/audit/events", headers=_get_admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_enrichment_status(self):
        r = client.get("/api/admin/v1/ai/enrichment/status", headers=_get_admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert "pipeline_status" in data
        assert "knowledge_base_files" in data

    def test_enrichment_jobs(self):
        r = client.get("/api/admin/v1/ai/enrichment/jobs", headers=_get_admin_headers())
        assert r.status_code == 200
        data = r.json()
        assert "jobs" in data
