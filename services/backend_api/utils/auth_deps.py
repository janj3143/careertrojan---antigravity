"""
Centralised Auth Dependencies — CareerTrojan
=============================================
Single import point for all authentication and authorisation dependencies.

Usage:
    from services.backend_api.utils.auth_deps import require_user, require_admin

    @router.get("/protected")
    def protected(user = Depends(require_user)):
        ...

    @router.get("/admin-only")
    def admin_only(_admin = Depends(require_admin)):
        ...

Author: CareerTrojan System
Date: February 2026
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security


# ============================================================================
# get_current_user — extracts User object from JWT bearer token
# ============================================================================

def get_current_user(
    token: str = Depends(security.oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Decode the JWT, look up the User row, and return it.

    Raises 401 if the token is missing/invalid/expired
    or the user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.decode_token(token)
        email: str | None = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if email is None or token_type != "access":
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


# Alias used by some routers
require_user = get_current_user


# ============================================================================
# require_admin — ensures the caller has role == "admin"
# ============================================================================

def require_admin(
    token: str = Depends(security.oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Same as get_current_user but also checks ``user.role == 'admin'``.

    Returns the User object so endpoints can use admin identity if needed.
    Raises 403 if not an admin.
    """
    user = get_current_user(token=token, db=db)
    if getattr(user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


# ============================================================================
# optional_user — returns User or None (for public endpoints with optional auth)
# ============================================================================

def optional_user(
    token: str | None = Depends(security.oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User | None:
    """
    Like get_current_user but returns None instead of raising
    when the token is missing or invalid.

    Use for endpoints that work for both anonymous and authenticated users
    but personalise output when a token is present.
    """
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None
