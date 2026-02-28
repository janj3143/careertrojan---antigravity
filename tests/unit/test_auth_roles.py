"""
Unit tests — Role-Based Access Control & JWT Claims
====================================================

Tests that JWT tokens carry correct role claims and that
role-enforcement guards (require_admin, get_current_user,
get_current_active_admin) behave correctly for user / admin / mentor.

Uses the shared ``make_auth_headers`` and per-role fixtures from conftest.
"""

import sys
import os
import pytest
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")


# ==========================================================================
# 1. JWT Claim Integrity — every role embeds correct claims
# ==========================================================================

@pytest.mark.unit
class TestJWTRoleClaims:
    """Verify that tokens created for each role carry the right claims."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from services.backend_api.utils.security import (
            create_access_token, SECRET_KEY, ALGORITHM,
        )
        from jose import jwt as jose_jwt
        self.create = create_access_token
        self.decode = jose_jwt.decode
        self.secret = SECRET_KEY
        self.algo = ALGORITHM

    @pytest.mark.parametrize("role", ["user", "admin", "mentor"])
    def test_token_contains_role_claim(self, role):
        token = self.create(data={"sub": f"{role}@ct.com", "role": role, "user_id": 1})
        payload = self.decode(token, self.secret, algorithms=[self.algo])
        assert payload["role"] == role

    @pytest.mark.parametrize("role", ["user", "admin", "mentor"])
    def test_token_contains_sub_claim(self, role):
        email = f"{role}@ct.com"
        token = self.create(data={"sub": email, "role": role, "user_id": 1})
        payload = self.decode(token, self.secret, algorithms=[self.algo])
        assert payload["sub"] == email

    @pytest.mark.parametrize("role", ["user", "admin", "mentor"])
    def test_token_contains_user_id(self, role):
        token = self.create(data={"sub": f"{role}@ct.com", "role": role, "user_id": 42})
        payload = self.decode(token, self.secret, algorithms=[self.algo])
        assert payload["user_id"] == 42

    def test_token_contains_expiry(self):
        token = self.create(data={"sub": "a@b.com", "role": "user", "user_id": 1})
        payload = self.decode(token, self.secret, algorithms=[self.algo])
        assert "exp" in payload

    def test_expired_token_raises(self):
        from jose import jwt as jose_jwt
        token = self.create(
            data={"sub": "x@y.com", "role": "user", "user_id": 1},
            expires_delta=timedelta(seconds=-5),
        )
        with pytest.raises(jose_jwt.ExpiredSignatureError):
            self.decode(token, self.secret, algorithms=[self.algo])

    def test_wrong_secret_raises(self):
        from jose import jwt as jose_jwt
        token = self.create(data={"sub": "a@b.com", "role": "user", "user_id": 1})
        with pytest.raises(jose_jwt.JWTError):
            self.decode(token, "wrong-key", algorithms=[self.algo])


# ==========================================================================
# 2. Admin Guard — require_admin dependency
# ==========================================================================

@pytest.mark.unit
class TestAdminGuard:
    """
    Test the ``require_admin`` dependency from the admin router.
    Admin-only endpoints must reject user/mentor tokens with 403
    and accept admin tokens with 200 or appropriate success code.
    """

    def test_admin_can_access_admin_users(self, test_client, admin_headers):
        resp = test_client.get("/api/admin/v1/users", headers=admin_headers)
        # 200 or 500 (if no DB) — but NOT 401 or 403
        assert resp.status_code not in (401, 403), f"Admin denied: {resp.text}"

    def test_user_cannot_access_admin_users(self, test_client, user_headers):
        resp = test_client.get("/api/admin/v1/users", headers=user_headers)
        assert resp.status_code in (401, 403)

    def test_mentor_cannot_access_admin_users(self, test_client, mentor_headers):
        resp = test_client.get("/api/admin/v1/users", headers=mentor_headers)
        assert resp.status_code in (401, 403)

    def test_no_token_gets_401(self, test_client):
        resp = test_client.get("/api/admin/v1/users")
        assert resp.status_code == 401

    def test_expired_token_gets_401(self, test_client, expired_headers):
        resp = test_client.get("/api/admin/v1/users", headers=expired_headers)
        assert resp.status_code == 401

    def test_admin_can_access_system_health(self, test_client, admin_headers):
        resp = test_client.get("/api/admin/v1/system/health", headers=admin_headers)
        assert resp.status_code not in (401, 403)

    def test_user_cannot_access_system_health(self, test_client, user_headers):
        resp = test_client.get("/api/admin/v1/system/health", headers=user_headers)
        assert resp.status_code in (401, 403)

    def test_admin_can_access_dashboard(self, test_client, admin_headers):
        resp = test_client.get("/api/admin/v1/dashboard/snapshot", headers=admin_headers)
        assert resp.status_code not in (401, 403)

    def test_user_cannot_access_dashboard(self, test_client, user_headers):
        resp = test_client.get("/api/admin/v1/dashboard/snapshot", headers=user_headers)
        assert resp.status_code in (401, 403)


# ==========================================================================
# 3. Public vs Protected Endpoints — role matrix
# ==========================================================================

@pytest.mark.unit
class TestEndpointRoleMatrix:
    """
    Verify a matrix of endpoints × roles.
    Public endpoints should be accessible to all.
    Protected endpoints should enforce their guard.
    """

    # --- Public (no auth required) ---

    @pytest.mark.parametrize("path", [
        "/api/shared/v1/health",
        "/api/shared/v1/healthz",
        "/healthz",
    ])
    def test_public_health_endpoints(self, test_client, path):
        resp = test_client.get(path)
        assert resp.status_code == 200

    # --- Admin-only (all 3 should be gated) ---

    @pytest.mark.parametrize("admin_path", [
        "/api/admin/v1/users",
        "/api/admin/v1/system/health",
        "/api/admin/v1/compliance/summary",
    ])
    def test_admin_endpoints_reject_unauthenticated(self, test_client, admin_path):
        resp = test_client.get(admin_path)
        assert resp.status_code == 401

    @pytest.mark.parametrize("admin_path", [
        "/api/admin/v1/users",
        "/api/admin/v1/system/health",
        "/api/admin/v1/compliance/summary",
    ])
    def test_admin_endpoints_reject_user_role(self, test_client, user_headers, admin_path):
        resp = test_client.get(admin_path, headers=user_headers)
        assert resp.status_code in (401, 403)

    @pytest.mark.parametrize("admin_path", [
        "/api/admin/v1/users",
        "/api/admin/v1/system/health",
        "/api/admin/v1/compliance/summary",
    ])
    def test_admin_endpoints_reject_mentor_role(self, test_client, mentor_headers, admin_path):
        resp = test_client.get(admin_path, headers=mentor_headers)
        assert resp.status_code in (401, 403)

    @pytest.mark.parametrize("admin_path", [
        "/api/admin/v1/users",
        "/api/admin/v1/system/health",
        "/api/admin/v1/compliance/summary",
    ])
    def test_admin_endpoints_allow_admin(self, test_client, admin_headers, admin_path):
        resp = test_client.get(admin_path, headers=admin_headers)
        assert resp.status_code not in (401, 403)


# ==========================================================================
# 4. Token Manipulation Attacks
# ==========================================================================

@pytest.mark.unit
class TestTokenManipulation:
    """Edge-case / attack-vector tests for JWT handling."""

    def test_empty_bearer_token(self, test_client):
        resp = test_client.get(
            "/api/admin/v1/users",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401

    def test_garbage_token(self, test_client):
        resp = test_client.get(
            "/api/admin/v1/users",
            headers={"Authorization": "Bearer not.a.jwt"},
        )
        assert resp.status_code == 401

    def test_no_role_in_token(self, test_client):
        from services.backend_api.utils.security import create_access_token
        # Token with sub but no role claim
        token = create_access_token(data={"sub": "norole@ct.com"})
        resp = test_client.get(
            "/api/admin/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (401, 403)

    def test_role_escalation_attempt(self, test_client):
        """A user token with role=user should not be accepted as admin
        even if other fields look admin-like."""
        from conftest import make_auth_headers
        headers = make_auth_headers("sneaky@evil.com", role="user", user_id=1)
        resp = test_client.get("/api/admin/v1/users", headers=headers)
        assert resp.status_code in (401, 403)
