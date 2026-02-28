"""
Integration tests — auth provider mode behavior (local/auth0) at HTTP layer.
"""

import sys
import os
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from starlette.testclient import TestClient
from services.backend_api.main import app
from services.backend_api.utils import security

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.integration
class TestAuthProviderModes:

    def test_admin_allows_auth0_scope(self, monkeypatch):
        monkeypatch.setattr(security, "get_auth_provider", lambda: "auth0")
        monkeypatch.setattr(
            security,
            "decode_access_token",
            lambda _token: {"sub": "auth0|user1", "permissions": ["admin:access"]},
        )

        r = client.get("/api/admin/v1/system/health", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 200

    def test_admin_denies_without_scope_or_role(self, monkeypatch):
        monkeypatch.setattr(security, "get_auth_provider", lambda: "auth0")
        monkeypatch.setattr(
            security,
            "decode_access_token",
            lambda _token: {"sub": "auth0|user2", "permissions": ["read:messages"]},
        )

        r = client.get("/api/admin/v1/system/health", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 403

    def test_admin_invalid_token_returns_401(self, monkeypatch):
        monkeypatch.setattr(security, "get_auth_provider", lambda: "auth0")

        def _raise(_token):
            raise security.TokenValidationError("bad token")

        monkeypatch.setattr(security, "decode_access_token", _raise)

        r = client.get("/api/admin/v1/system/health", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 401
