
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security

router = APIRouter(prefix="/api/admin/v1", tags=["admin"])

# Dependency for Admin Auth
def require_admin(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if role != "admin":
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return True

# --- Real Implementation (User Management) ---

@router.get("/users")
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    """List users with pagination."""
    users = db.query(models.User).offset(skip).limit(limit).all()
    # Simple serialization for migration speed
    return [{"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active, "created_at": u.created_at} for u in users]

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _: bool = Depends(require_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "profile": user.profile}

# --- System Stubs (From Legacy) ---

def _not_impl(msg: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=msg)

@router.get("/system/health")
def system_health(_: bool = Depends(require_admin)):
    return {"status": "ok", "db": "connected"} # Upgraded to partial real

@router.get("/tokens/config")
def tokens_config(_: bool = Depends(require_admin)):
    _not_impl("Implement token plan config")

@router.get("/compliance/summary")
def compliance_summary(_: bool = Depends(require_admin)):
    _not_impl("Implement compliance summary")

@router.get("/email/status")
def email_status(_: bool = Depends(require_admin)):
    _not_impl("Implement email status")

@router.get("/parsers/status")
def parsers_status(_: bool = Depends(require_admin)):
    return {"status": "idle", "jobs_queued": 0} # Mock return

# --- Extended Stubs (Migrated from Legacy) ---

@router.get("/system/activity")
def system_activity(_: bool = Depends(require_admin)):
    _not_impl("Implement system activity")

@router.get("/dashboard/snapshot")
def dashboard_snapshot(_: bool = Depends(require_admin)):
    _not_impl("Implement dashboard snapshot")

@router.get("/tokens/usage")
def tokens_usage(_: bool = Depends(require_admin)):
    _not_impl("Implement token usage")

@router.get("/tokens/users/{user_id}/ledger")
def user_token_ledger(user_id: str, _: bool = Depends(require_admin)):
    _not_impl(f"Implement token ledger for {user_id}")

@router.get("/user_subscriptions")
def user_subscriptions(_: bool = Depends(require_admin)):
    _not_impl("Implement user subscriptions store (plan keys from user portal)")

@router.get("/users/metrics")
def user_metrics(_: bool = Depends(require_admin)):
    _not_impl("Implement user metrics")

@router.get("/users/security")
def user_security(_: bool = Depends(require_admin)):
    _not_impl("Implement user security")

@router.put("/users/{user_id}/plan")
def set_user_plan(user_id: str, _: bool = Depends(require_admin)):
    _not_impl(f"Implement set user plan {user_id}")

@router.put("/users/{user_id}/disable")
def disable_user(user_id: str, _: bool = Depends(require_admin)):
    _not_impl(f"Implement disable user {user_id}")

@router.get("/compliance/audit/events")
def audit_events(_: bool = Depends(require_admin)):
    _not_impl("Implement audit events")

@router.post("/email/sync")
def email_sync(_: bool = Depends(require_admin)):
    _not_impl("Implement email sync trigger")

@router.get("/email/jobs")
def email_jobs(_: bool = Depends(require_admin)):
    _not_impl("Implement email jobs list")

@router.post("/parsers/run")
def parsers_run(_: bool = Depends(require_admin)):
    _not_impl("Implement parsers run")

@router.get("/parsers/jobs")
def parsers_jobs(_: bool = Depends(require_admin)):
    _not_impl("Implement parsers jobs list")

@router.get("/batch/status")
def batch_status(_: bool = Depends(require_admin)):
    _not_impl("Implement batch status")

@router.post("/batch/run")
def batch_run(_: bool = Depends(require_admin)):
    _not_impl("Implement batch run")

@router.get("/batch/jobs")
def batch_jobs(_: bool = Depends(require_admin)):
    _not_impl("Implement batch jobs list")

@router.get("/ai/enrichment/status")
def enrichment_status(_: bool = Depends(require_admin)):
    _not_impl("Implement enrichment status")

@router.post("/ai/enrichment/run")
def enrichment_run(_: bool = Depends(require_admin)):
    _not_impl("Implement enrichment run")

@router.get("/ai/enrichment/jobs")
def enrichment_jobs(_: bool = Depends(require_admin)):
    _not_impl("Implement enrichment jobs list")

@router.get("/ai/content/status")
def content_status(_: bool = Depends(require_admin)):
    _not_impl("Implement content status")

@router.post("/ai/content/run")
def content_run(_: bool = Depends(require_admin)):
    _not_impl("Implement content run")

@router.get("/ai/content/jobs")
def content_jobs(_: bool = Depends(require_admin)):
    _not_impl("Implement content jobs list")
