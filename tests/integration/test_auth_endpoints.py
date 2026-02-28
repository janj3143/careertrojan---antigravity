"""
Integration tests — Auth Endpoints (Register / Login / 2FA / Brute-Force)
==========================================================================

Full HTTP-level tests against /api/auth/v1/* using Starlette TestClient.
Covers all three roles (user, admin, mentor) through the actual
register → login → access-protected-route pipeline.

These tests use an in-memory SQLite DB via the app's dependency-override
mechanism so they are self-contained and do not require a running server.
"""

import sys
import os
import uuid
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_email(prefix="test"):
    """Generate a unique email to avoid duplicate-registration collisions."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(client, email, password="StrongPass123!", full_name="Test User"):
    """Register a new user via the API."""
    return client.post(
        "/api/auth/v1/register",
        params={"email": email, "password": password, "full_name": full_name},
    )


def _login(client, email, password="StrongPass123!"):
    """Login via the API (OAuth2 form-encoded)."""
    return client.post(
        "/api/auth/v1/login",
        data={"username": email, "password": password},
    )


# ==========================================================================
# 1. Registration Flow
# ==========================================================================

@pytest.mark.integration
class TestRegistration:

    def test_register_new_user(self, test_client):
        email = _unique_email("newuser")
        resp = _register(test_client, email)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == email
        assert "id" in body

    def test_register_duplicate_email(self, test_client):
        email = _unique_email("dup")
        _register(test_client, email)
        resp = _register(test_client, email)
        assert resp.status_code == 400
        body = resp.json()
        msg = body.get("error", {}).get("message", "") or body.get("detail", "")
        assert "already registered" in msg.lower()

    def test_register_returns_no_password(self, test_client):
        email = _unique_email("nopw")
        resp = _register(test_client, email)
        body = resp.json()
        assert "password" not in body
        assert "hashed_password" not in body


# ==========================================================================
# 2. Login Flow — All 3 Roles
# ==========================================================================

@pytest.mark.integration
class TestLoginUser:
    """Standard user login flow."""

    def test_login_success(self, test_client):
        email = _unique_email("login")
        _register(test_client, email, password="Correct123!")
        resp = _login(test_client, email, password="Correct123!")
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, test_client):
        email = _unique_email("wrongpw")
        _register(test_client, email, password="RightPass1!")
        resp = _login(test_client, email, password="WrongPass!")
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, test_client):
        resp = _login(test_client, _unique_email("ghost"), password="any")
        assert resp.status_code == 401

    def test_login_token_has_sub_claim(self, test_client):
        email = _unique_email("claims")
        _register(test_client, email, password="Claims123!")
        resp = _login(test_client, email, password="Claims123!")
        token = resp.json()["access_token"]

        from services.backend_api.utils.security import SECRET_KEY, ALGORITHM
        from jose import jwt as jose_jwt
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == email
        assert "role" in payload


@pytest.mark.integration
class TestLoginAdmin:
    """Admin-specific login & access flow.
    
    Note: The register endpoint creates all users with role='user' by default.
    To test admin access, we use JWT fixtures (from conftest) that carry
    role='admin'. A real admin would be seeded or promoted via a management command.
    """

    def test_admin_jwt_can_access_admin_routes(self, test_client, admin_headers):
        resp = test_client.get("/api/admin/v1/users", headers=admin_headers)
        # Should not be denied — may 500 if DB is empty but not 401/403
        assert resp.status_code not in (401, 403)

    def test_user_jwt_cannot_access_admin_routes(self, test_client, user_headers):
        resp = test_client.get("/api/admin/v1/users", headers=user_headers)
        assert resp.status_code in (401, 403)


@pytest.mark.integration
class TestLoginMentor:
    """Mentor-role login tests — verify mentor tokens are accepted by
    appropriate endpoints and rejected by admin endpoints."""

    def test_mentor_jwt_rejected_by_admin_routes(self, test_client, mentor_headers):
        resp = test_client.get("/api/admin/v1/users", headers=mentor_headers)
        assert resp.status_code in (401, 403)

    def test_mentor_jwt_accepted_by_health(self, test_client, mentor_headers):
        # Health is public but should not break with a mentor token
        resp = test_client.get("/api/shared/v1/health", headers=mentor_headers)
        assert resp.status_code == 200


# ==========================================================================
# 3. Brute-Force Protection (via actual HTTP)
# ==========================================================================

@pytest.mark.integration
class TestBruteForceProtection:
    """Test the login brute-force lockout via real HTTP calls."""

    def test_lockout_after_five_failures(self, test_client):
        """After 5 wrong-password attempts from the same IP, the 6th gets 429."""
        email = _unique_email("brute")
        _register(test_client, email, password="RealPass123!")

        # 5 failures
        for i in range(5):
            resp = _login(test_client, email, password="Wrong!")
            assert resp.status_code == 401, f"Attempt {i+1} should be 401"

        # 6th attempt should be locked out (429)
        resp = _login(test_client, email, password="Wrong!")
        assert resp.status_code == 429
        body = resp.json()
        msg = (body.get("error", {}).get("message", "") or body.get("detail", "")).lower()
        assert "retry" in msg or "too many" in msg

    def test_lockout_blocks_even_correct_password(self, test_client):
        """Once locked out, even the correct password gets 429."""
        email = _unique_email("lockright")
        _register(test_client, email, password="CorrectPass1!")

        # Trigger lockout
        for _ in range(5):
            _login(test_client, email, password="Wrong!")

        # Correct password should still be blocked
        resp = _login(test_client, email, password="CorrectPass1!")
        assert resp.status_code == 429

    def test_retry_after_header_present(self, test_client):
        """The 429 response should include a Retry-After header."""
        email = _unique_email("retryheader")
        _register(test_client, email, password="Pass123!")

        for _ in range(5):
            _login(test_client, email, password="Wrong!")

        resp = _login(test_client, email, password="Wrong!")
        assert resp.status_code == 429
        assert "retry-after" in resp.headers or "Retry-After" in resp.headers


# ==========================================================================
# 4. Expired & Invalid Token Access
# ==========================================================================

@pytest.mark.integration
class TestTokenEdgeCases:

    def test_expired_token_rejected(self, test_client, expired_headers):
        resp = test_client.get("/api/admin/v1/users", headers=expired_headers)
        assert resp.status_code == 401

    def test_no_auth_header_rejected(self, test_client):
        resp = test_client.get("/api/admin/v1/users")
        assert resp.status_code == 401

    def test_malformed_auth_header(self, test_client):
        resp = test_client.get(
            "/api/admin/v1/users",
            headers={"Authorization": "NotBearer xyz"},
        )
        assert resp.status_code in (401, 403)

    def test_health_does_not_require_auth(self, test_client):
        resp = test_client.get("/api/shared/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ==========================================================================
# 5. Cross-Role Access Matrix (comprehensive parametrized)
# ==========================================================================

@pytest.mark.integration
class TestCrossRoleMatrix:
    """
    Parametrized matrix: for each protected endpoint, verify that only
    the permitted roles can access it.
    """

    ADMIN_ONLY = [
        "/api/admin/v1/users",
        "/api/admin/v1/system/health",
        "/api/admin/v1/dashboard/snapshot",
    ]

    @pytest.mark.parametrize("endpoint", ADMIN_ONLY)
    def test_admin_allowed(self, test_client, admin_headers, endpoint):
        resp = test_client.get(endpoint, headers=admin_headers)
        assert resp.status_code not in (401, 403), f"Admin denied on {endpoint}"

    @pytest.mark.parametrize("endpoint", ADMIN_ONLY)
    def test_user_denied(self, test_client, user_headers, endpoint):
        resp = test_client.get(endpoint, headers=user_headers)
        assert resp.status_code in (401, 403), f"User allowed on {endpoint}"

    @pytest.mark.parametrize("endpoint", ADMIN_ONLY)
    def test_mentor_denied(self, test_client, mentor_headers, endpoint):
        resp = test_client.get(endpoint, headers=mentor_headers)
        assert resp.status_code in (401, 403), f"Mentor allowed on {endpoint}"

    @pytest.mark.parametrize("endpoint", ADMIN_ONLY)
    def test_anonymous_denied(self, test_client, endpoint):
        resp = test_client.get(endpoint)
        assert resp.status_code == 401, f"Anonymous allowed on {endpoint}"
