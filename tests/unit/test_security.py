"""
Unit tests — Security utilities (hashing, JWT, auth helpers).
"""

import sys
import os
import pytest
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


@pytest.mark.unit
class TestPasswordHashing:

    def test_hash_and_verify(self):
        from services.backend_api.utils.security import get_password_hash, verify_password
        plain = "SuperSecret123!"
        hashed = get_password_hash(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self):
        from services.backend_api.utils.security import get_password_hash, verify_password
        hashed = get_password_hash("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_hash_is_bcrypt(self):
        from services.backend_api.utils.security import get_password_hash
        hashed = get_password_hash("test")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


@pytest.mark.unit
class TestJWT:

    def test_create_and_decode_token(self):
        from services.backend_api.utils.security import create_access_token, SECRET_KEY, ALGORITHM
        from jose import jwt as jose_jwt

        token = create_access_token(data={"sub": "user@example.com"})
        payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "user@example.com"
        assert "exp" in payload

    def test_token_expires(self):
        from services.backend_api.utils.security import create_access_token, SECRET_KEY, ALGORITHM
        from jose import jwt as jose_jwt

        token = create_access_token(
            data={"sub": "user@example.com"},
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        with pytest.raises(jose_jwt.ExpiredSignatureError):
            jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_invalid_secret_fails(self):
        from services.backend_api.utils.security import create_access_token, ALGORITHM
        from jose import jwt as jose_jwt

        token = create_access_token(data={"sub": "user@example.com"})
        with pytest.raises(jose_jwt.JWTError):
            jose_jwt.decode(token, "wrong-secret", algorithms=[ALGORITHM])

    def test_decode_access_token_local_provider(self):
        from services.backend_api.utils import security

        token = security.create_access_token(data={"sub": "local-user@example.com", "scope": "read:messages"})
        payload = security.decode_access_token(token)
        assert payload["sub"] == "local-user@example.com"

    def test_scope_helpers(self):
        from services.backend_api.utils import security

        payload = {
            "scope": "read:messages write:messages",
            "permissions": ["admin:access"],
        }
        scopes = security.get_token_scopes(payload)
        assert "read:messages" in scopes
        assert "admin:access" in scopes
        assert security.token_has_scopes(payload, ["read:messages", "admin:access"])
        assert not security.token_has_scopes(payload, ["billing:write"])

    def test_decode_access_token_auth0_provider_with_mocked_jwks(self, monkeypatch):
        from services.backend_api.utils import security

        monkeypatch.setattr(security, "AUTH_PROVIDER", "auth0")
        monkeypatch.setattr(security, "AUTH0_ISSUER", "https://tenant.example/")
        monkeypatch.setattr(security, "AUTH0_AUDIENCE", "https://api.example.com")

        monkeypatch.setattr(security, "_fetch_jwks_keys", lambda: [{"kid": "k1", "kty": "RSA", "n": "x", "e": "AQAB"}])
        monkeypatch.setattr(security.jwt, "get_unverified_header", lambda _token: {"kid": "k1"})

        def _fake_decode(token, signing_key, **kwargs):
            assert token == "auth0-token"
            assert signing_key.get("kid") == "k1"
            assert kwargs.get("issuer") == "https://tenant.example/"
            assert kwargs.get("audience") == "https://api.example.com"
            return {"sub": "auth0|abc", "permissions": ["admin:access"]}

        monkeypatch.setattr(security.jwt, "decode", _fake_decode)

        payload = security.decode_access_token("auth0-token")
        assert payload["sub"] == "auth0|abc"

    def test_decode_access_token_auth0_missing_kid(self, monkeypatch):
        from services.backend_api.utils import security

        monkeypatch.setattr(security, "AUTH_PROVIDER", "auth0")
        monkeypatch.setattr(security, "AUTH0_ISSUER", "https://tenant.example/")
        monkeypatch.setattr(security.jwt, "get_unverified_header", lambda _token: {})

        with pytest.raises(security.TokenValidationError):
            security.decode_access_token("bad-token")
