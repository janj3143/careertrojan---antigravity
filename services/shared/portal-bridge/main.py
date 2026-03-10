from fastapi import FastAPI, HTTPException, Header, status
from loguru import logger
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import os

app = FastAPI(title="Portal Bridge", version="2.0.0")

# ── Shared JWT config — MUST match backend_api/utils/security.py ──────────
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dev-only bootstrap flag — never true in production
TEST_USER_BOOTSTRAP = os.getenv("TEST_USER_BOOTSTRAP_ENABLED", "false").lower() == "true"


def _get_db_connection():
    """Get a raw DB session for credential verification."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not configured for portal-bridge")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return Session(bind=engine)


def _create_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode["type"] = "access"
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


@app.get("/health")
async def health_check():
    db_ok = False
    try:
        from sqlalchemy import text
        sess = _get_db_connection()
        sess.execute(text("SELECT 1"))
        sess.close()
        db_ok = True
    except Exception:
        pass
    return {"status": "online", "service": "portal-bridge", "database": "connected" if db_ok else "disconnected"}


@app.post("/auth/login")
async def login(credentials: dict):
    """Authenticate against backend user DB, issue JWT.

    Phase-1 bootstrap only if TEST_USER_BOOTSTRAP_ENABLED=true
    and BOOTSTRAP_USER/BOOTSTRAP_PASS are set (dev-only).
    """
    username = credentials.get("username", "").strip()
    password = credentials.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")

    # Dev-only bootstrap path — gated behind env flag, disabled by default
    if TEST_USER_BOOTSTRAP:
        if username == os.getenv("BOOTSTRAP_USER") and password == os.getenv("BOOTSTRAP_PASS"):
            token = _create_token({"sub": username, "role": "premium"})
            return {"token": token, "user": username, "role": "premium", "warning": "bootstrap-mode"}

    # Real auth — query backend DB
    try:
        from sqlalchemy import text
        sess = _get_db_connection()
        row = sess.execute(
            text("SELECT id, email, hashed_password, role, is_active FROM users WHERE email = :email"),
            {"email": username},
        ).fetchone()
        sess.close()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, email, hashed_pw, role, is_active = row

        if not is_active:
            raise HTTPException(status_code=403, detail="Account disabled")

        if not pwd_context.verify(password, hashed_pw):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = _create_token({"sub": email, "user_id": user_id, "role": role or "user"})
        logger.info("portal-bridge: user {} authenticated (role={})", email, role)
        return {"token": token, "user": email, "role": role or "user", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("portal-bridge login DB error: {}", e)
        raise HTTPException(status_code=500, detail="Authentication service unavailable")


@app.post("/auth/masquerade")
async def masquerade(body: dict, authorization: Optional[str] = Header(None)):
    """Admin masquerade — requires valid admin JWT.

    Allows an admin to assume a user's identity for support purposes.
    Issues a short-lived token (5 min) for the target user.
    """
    # Require Authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.split(" ", 1)[1]
    try:
        payload = _decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Only admins can masquerade
    if payload.get("role") not in ("admin", "superuser"):
        raise HTTPException(status_code=403, detail="Admin role required for masquerade")

    target_email = body.get("target_user", "").strip()
    if not target_email:
        raise HTTPException(status_code=400, detail="target_user email required")

    # Verify target exists
    try:
        from sqlalchemy import text
        sess = _get_db_connection()
        row = sess.execute(
            text("SELECT id, email, role, is_active FROM users WHERE email = :email"),
            {"email": target_email},
        ).fetchone()
        sess.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"User {target_email} not found")

        target_id, target_email_db, target_role, target_active = row
        if not target_active:
            raise HTTPException(status_code=403, detail="Target account is disabled")

        # Issue short-lived masquerade token (5 min)
        masquerade_token = _create_token(
            {"sub": target_email_db, "user_id": target_id, "role": target_role or "user",
             "masquerade_by": payload.get("sub"), "masquerade": True},
            expires_minutes=5,
        )
        logger.warning("MASQUERADE: admin={} -> target={}", payload.get("sub"), target_email_db)
        return {
            "status": "active",
            "mode": "masquerade",
            "target": target_email_db,
            "target_role": target_role,
            "token": masquerade_token,
            "expires_minutes": 5,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("masquerade DB error: {}", e)
        raise HTTPException(status_code=500, detail="Masquerade service unavailable")


@app.post("/auth/verify")
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify a JWT token and return its payload — used by other micro-services."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = _decode_token(token)
        return {"valid": True, "payload": payload}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
