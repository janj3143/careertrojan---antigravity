
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os
import secrets

# Config — read from env, NEVER hardcode in production
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(64))
if SECRET_KEY == "super-secret-key-change-me-in-production":
    import warnings
    warnings.warn("⚠️  Using default SECRET_KEY — set SECRET_KEY env var in production!", stacklevel=2)

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # 30 min default
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Google OAuth2 (optional — only active when both vars are set)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a longer-lived refresh token (7 days default)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


async def verify_google_id_token(id_token: str) -> Optional[dict]:
    """
    Verify a Google OAuth2 ID token and return user info.
    
    Returns dict with {email, name, picture, sub} or None on failure.
    Requires GOOGLE_CLIENT_ID to be set.
    """
    if not GOOGLE_OAUTH_ENABLED:
        return None

    try:
        import httpx
        # Verify with Google's tokeninfo endpoint
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            )
            if resp.status_code != 200:
                return None

            payload = resp.json()
            # Verify audience matches our client ID
            if payload.get("aud") != GOOGLE_CLIENT_ID:
                return None

            return {
                "email": payload.get("email"),
                "name": payload.get("name", ""),
                "picture": payload.get("picture", ""),
                "sub": payload.get("sub"),  # Google user ID
                "email_verified": payload.get("email_verified", "false") == "true",
            }
    except Exception:
        return None
