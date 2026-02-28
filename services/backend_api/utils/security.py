
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from jose import jwt
from jose.exceptions import JWTError
from fastapi.security import OAuth2PasswordBearer
import os
import json
import urllib.request
import threading

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-me-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24))) # 24 hours
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "local").strip().lower()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "").strip()
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "").strip()
AUTH0_ISSUER = os.getenv("AUTH0_ISSUER", "").strip() or (f"https://{AUTH0_DOMAIN}/" if AUTH0_DOMAIN else "")
AUTH0_JWKS_URL = os.getenv("AUTH0_JWKS_URL", "").strip() or (f"https://{AUTH0_DOMAIN}/.well-known/jwks.json" if AUTH0_DOMAIN else "")
JWKS_CACHE_SECONDS = int(os.getenv("AUTH0_JWKS_CACHE_SECONDS", "300"))

_jwks_cache: Dict[str, Any] = {"expires_at": 0.0, "keys": []}
_jwks_lock = threading.Lock()


class TokenValidationError(Exception):
    pass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/v1/login")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_auth_provider() -> str:
    return AUTH_PROVIDER if AUTH_PROVIDER in {"local", "auth0"} else "local"


def _decode_local_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def _fetch_jwks_keys() -> List[Dict[str, Any]]:
    if not AUTH0_JWKS_URL:
        raise TokenValidationError("AUTH0_JWKS_URL is not configured")

    now_ts = datetime.now(timezone.utc).timestamp()
    with _jwks_lock:
        if _jwks_cache["keys"] and now_ts < float(_jwks_cache["expires_at"]):
            return _jwks_cache["keys"]

    try:
        with urllib.request.urlopen(AUTH0_JWKS_URL, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            keys = payload.get("keys", [])
            if not isinstance(keys, list):
                keys = []
    except Exception as exc:
        raise TokenValidationError(f"Failed to fetch Auth0 JWKS: {exc}")

    with _jwks_lock:
        _jwks_cache["keys"] = keys
        _jwks_cache["expires_at"] = now_ts + max(JWKS_CACHE_SECONDS, 30)

    return keys


def _decode_auth0_token(token: str) -> Dict[str, Any]:
    if not AUTH0_ISSUER:
        raise TokenValidationError("AUTH0_ISSUER is not configured")

    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        raise TokenValidationError(f"Invalid token header: {exc}")

    kid = header.get("kid")
    if not kid:
        raise TokenValidationError("Missing key id (kid) in token header")

    keys = _fetch_jwks_keys()
    signing_key = next((key for key in keys if key.get("kid") == kid), None)
    if not signing_key:
        raise TokenValidationError("No matching JWKS key for token kid")

    decode_kwargs: Dict[str, Any] = {
        "algorithms": ["RS256"],
        "issuer": AUTH0_ISSUER,
    }
    if AUTH0_AUDIENCE:
        decode_kwargs["audience"] = AUTH0_AUDIENCE
    else:
        decode_kwargs["options"] = {"verify_aud": False}

    try:
        return jwt.decode(token, signing_key, **decode_kwargs)
    except Exception as exc:
        raise TokenValidationError(f"Auth0 token validation failed: {exc}")


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        if get_auth_provider() == "auth0":
            return _decode_auth0_token(token)
        return _decode_local_token(token)
    except TokenValidationError:
        raise
    except JWTError as exc:
        raise TokenValidationError(str(exc))
    except Exception as exc:
        raise TokenValidationError(str(exc))


def get_token_scopes(payload: Dict[str, Any]) -> List[str]:
    scopes: List[str] = []

    scope_claim = payload.get("scope")
    if isinstance(scope_claim, str):
        scopes.extend([s for s in scope_claim.split() if s])

    permissions_claim = payload.get("permissions")
    if isinstance(permissions_claim, list):
        scopes.extend([str(item) for item in permissions_claim if item])

    deduped: List[str] = []
    seen = set()
    for item in scopes:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def token_has_scopes(payload: Dict[str, Any], required_scopes: List[str]) -> bool:
    if not required_scopes:
        return True
    scopes = set(get_token_scopes(payload))
    return all(scope in scopes for scope in required_scopes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
