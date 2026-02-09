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
