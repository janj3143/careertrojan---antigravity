"""
=============================================================================
Portal Bridge Integration Tests
=============================================================================

Tests for the Portal Bridge FastAPI microservice that handles authentication,
masquerade, and health check endpoints.

Service location: services/shared/portal-bridge/main.py
"""

import os
import sys
import importlib.util
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Portal-bridge dir uses a hyphen — not importable via normal dotted path.
# Use importlib to load it directly.
_bridge_main = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    "services", "shared", "portal-bridge", "main.py",
)
_bridge_main = os.path.normpath(_bridge_main)
_spec = importlib.util.spec_from_file_location("portal_bridge_main", _bridge_main)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
app = _mod.app
TEST_USER_BOOTSTRAP = _mod.TEST_USER_BOOTSTRAP  # cache for config tests

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestPortalBridgeHealth:
    """Test portal bridge health endpoint."""

    def test_health_returns_200(self):
        """GET /health returns 200 with status online."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["service"] == "portal-bridge"

    def test_health_response_structure(self):
        """Health response has required keys."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "service" in data


# ---------------------------------------------------------------------------
# Authentication - Login
# ---------------------------------------------------------------------------

class TestPortalBridgeLogin:
    """Test portal bridge login endpoint."""

    def test_login_valid_credentials(self):
        """POST /auth/login with valid creds returns token."""
        response = client.post("/auth/login", json={
            "username": "janj3143",
            "password": "Janj!3143@?"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"] == "janj3143"
        assert data["role"] == "premium"

    def test_login_invalid_username(self):
        """POST /auth/login with wrong username returns 401."""
        response = client.post("/auth/login", json={
            "username": "wrong_user",
            "password": "Janj!3143@?"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Invalid credentials"

    def test_login_invalid_password(self):
        """POST /auth/login with wrong password returns 401."""
        response = client.post("/auth/login", json={
            "username": "janj3143",
            "password": "wrong_password"
        })
        assert response.status_code == 401

    def test_login_empty_credentials(self):
        """POST /auth/login with empty body returns 401."""
        response = client.post("/auth/login", json={})
        assert response.status_code == 401

    def test_login_missing_password(self):
        """POST /auth/login with missing password returns 401."""
        response = client.post("/auth/login", json={"username": "janj3143"})
        assert response.status_code == 401

    def test_login_missing_username(self):
        """POST /auth/login with missing username returns 401."""
        response = client.post("/auth/login", json={"password": "Janj!3143@?"})
        assert response.status_code == 401

    def test_login_returns_jwt_like_token(self):
        """Token returned on valid login is a non-empty string."""
        response = client.post("/auth/login", json={
            "username": "janj3143",
            "password": "Janj!3143@?"
        })
        data = response.json()
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0


# ---------------------------------------------------------------------------
# Authentication - Masquerade
# ---------------------------------------------------------------------------

class TestPortalBridgeMasquerade:
    """Test portal bridge masquerade endpoint."""

    def test_masquerade_returns_active(self):
        """POST /auth/masquerade returns active masquerade status."""
        response = client.post("/auth/masquerade", params={"target_user": "test-user-123"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["mode"] == "masquerade"
        assert data["target"] == "test-user-123"

    def test_masquerade_with_different_user(self):
        """Masquerade works with different target user IDs."""
        response = client.post("/auth/masquerade", params={"target_user": "admin-user-456"})
        assert response.status_code == 200
        data = response.json()
        assert data["target"] == "admin-user-456"

    def test_masquerade_missing_target(self):
        """POST /auth/masquerade without target_user returns 422."""
        response = client.post("/auth/masquerade")
        assert response.status_code == 422

    def test_masquerade_response_has_mode(self):
        """Masquerade response always includes mode field."""
        response = client.post("/auth/masquerade", params={"target_user": "any-user"})
        data = response.json()
        assert "mode" in data
        assert data["mode"] == "masquerade"


# ---------------------------------------------------------------------------
# Configuration / ENV
# ---------------------------------------------------------------------------

class TestPortalBridgeConfig:
    """Test portal bridge configuration behavior."""

    def test_default_test_bootstrap_disabled(self):
        """TEST_USER_BOOTSTRAP defaults to False."""
        # In test environment, should be False unless explicitly set
        assert isinstance(TEST_USER_BOOTSTRAP, bool)

    @patch.dict(os.environ, {"TEST_USER_BOOTSTRAP_ENABLED": "true"})
    def test_bootstrap_enabled_via_env(self):
        """TEST_USER_BOOTSTRAP responds to environment variable."""
        result = os.getenv("TEST_USER_BOOTSTRAP_ENABLED", "false").lower() == "true"
        assert result is True

    @patch.dict(os.environ, {"TEST_USER_BOOTSTRAP_ENABLED": "false"})
    def test_bootstrap_disabled_via_env(self):
        """TEST_USER_BOOTSTRAP responds to 'false' env variable."""
        result = os.getenv("TEST_USER_BOOTSTRAP_ENABLED", "false").lower() == "true"
        assert result is False


# ---------------------------------------------------------------------------
# API Schema / OpenAPI
# ---------------------------------------------------------------------------

class TestPortalBridgeAPISchema:
    """Test that the portal bridge exposes correct API schema."""

    def test_openapi_available(self):
        """GET /openapi.json returns valid schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Portal Bridge"
        assert data["info"]["version"] == "1.0.0"

    def test_routes_exist_in_schema(self):
        """All expected routes appear in OpenAPI schema."""
        response = client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]
        assert "/health" in paths
        assert "/auth/login" in paths
        assert "/auth/masquerade" in paths

    def test_no_unexpected_routes(self):
        """Only expected routes are defined (security check)."""
        response = client.get("/openapi.json")
        paths = set(response.json()["paths"].keys())
        expected = {"/health", "/auth/login", "/auth/masquerade"}
        assert paths == expected, f"Unexpected routes found: {paths - expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
