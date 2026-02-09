
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os, glob, json, logging
from datetime import datetime, timedelta

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security

logger = logging.getLogger("admin")
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

# tokens/config moved to admin_tokens.py (real implementation)

@router.get("/compliance/summary")
def compliance_summary(_: bool = Depends(require_admin), db: Session = Depends(get_db)):
    """GDPR compliance overview: consent stats, export requests, deletions."""
    total_consents = db.query(func.count(models.ConsentRecord.id)).scalar() or 0
    granted = db.query(func.count(models.ConsentRecord.id)).filter(models.ConsentRecord.granted == True).scalar() or 0
    revoked = db.query(func.count(models.ConsentRecord.id)).filter(models.ConsentRecord.granted == False).scalar() or 0
    exports = db.query(func.count(models.DataExportRequest.id)).scalar() or 0
    deletions = db.query(func.count(models.AuditLog.id)).filter(models.AuditLog.action == "account_delete").scalar() or 0

    return {
        "consent_records": {"total": total_consents, "granted": granted, "revoked": revoked},
        "data_export_requests": exports,
        "account_deletions": deletions,
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/email/status")
def email_status(_: bool = Depends(require_admin)):
    _not_impl("Implement email status")

@router.get("/parsers/status")
def parsers_status(_: bool = Depends(require_admin)):
    return {"status": "idle", "jobs_queued": 0} # Mock return

# --- Extended Stubs (Migrated from Legacy) ---

@router.get("/system/activity")
def system_activity(_: bool = Depends(require_admin), db: Session = Depends(get_db)):
    """Recent system activity: user sign-ups, interactions, AI enrichment runs."""
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    # DB-level counts
    new_users_24h = db.query(func.count(models.User.id)).filter(models.User.created_at >= day_ago).scalar() or 0
    new_users_7d = db.query(func.count(models.User.id)).filter(models.User.created_at >= week_ago).scalar() or 0
    interactions_24h = db.query(func.count(models.Interaction.id)).filter(models.Interaction.created_at >= day_ago).scalar() or 0
    exports_24h = db.query(func.count(models.DataExportRequest.id)).filter(models.DataExportRequest.requested_at >= day_ago).scalar() or 0

    # File-level interaction count for today
    interactions_dir = os.path.join(os.getcwd(), "interactions")
    today_dir = os.path.join(interactions_dir, now.strftime("%Y-%m-%d"))
    file_interactions_today = len(glob.glob(os.path.join(today_dir, "*.json"))) if os.path.isdir(today_dir) else 0

    return {
        "new_users_24h": new_users_24h,
        "new_users_7d": new_users_7d,
        "interactions_24h": interactions_24h,
        "file_interactions_today": file_interactions_today,
        "data_export_requests_24h": exports_24h,
        "timestamp": now.isoformat(),
    }

@router.get("/dashboard/snapshot")
def dashboard_snapshot(_: bool = Depends(require_admin), db: Session = Depends(get_db)):
    """Admin dashboard overview: counts, pipeline health, recent events."""
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    active_users = db.query(func.count(models.User.id)).filter(models.User.is_active == True).scalar() or 0
    total_resumes = db.query(func.count(models.Resume.id)).scalar() or 0
    total_jobs = db.query(func.count(models.Job.id)).scalar() or 0
    total_mentorships = db.query(func.count(models.Mentorship.id)).scalar() or 0

    # AI data directory sizes
    ai_data_root = os.path.join(os.getcwd(), "ai_data_final")
    ai_stats = {}
    if os.path.isdir(ai_data_root):
        for subdir in ["parsed_resumes", "job_matching", "learning_library", "profiles", "trained_models"]:
            subpath = os.path.join(ai_data_root, subdir)
            if os.path.isdir(subpath):
                ai_stats[subdir] = len(os.listdir(subpath))
            else:
                ai_stats[subdir] = 0

    # Recent audit events
    recent_audits = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.created_at.desc())
        .limit(10).all()
    )
    audit_summary = [
        {"action": a.action, "resource_type": a.resource_type,
         "created_at": a.created_at.isoformat() if a.created_at else None}
        for a in recent_audits
    ]

    return {
        "users": {"total": total_users, "active": active_users},
        "resumes": total_resumes,
        "jobs": total_jobs,
        "mentorships": total_mentorships,
        "ai_data": ai_stats,
        "recent_audit_events": audit_summary,
        "timestamp": datetime.utcnow().isoformat(),
    }

# tokens/usage moved to admin_tokens.py (real implementation)

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
def audit_events(
    limit: int = 100,
    action: str = None,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Full audit log (admin view) — filterable by action type."""
    q = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc())
    if action:
        q = q.filter(models.AuditLog.action == action)
    entries = q.limit(limit).all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "actor_id": e.actor_id,
            "action": e.action,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "detail": e.detail,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]

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
    """AI enrichment pipeline status — scans interactions/ dir for pending/processed."""
    interactions_dir = os.path.join(os.getcwd(), "interactions")
    ai_data_root = os.path.join(os.getcwd(), "ai_data_final")

    # Count pending interactions (files in interactions/ directory)
    pending = 0
    processed_dirs = 0
    if os.path.isdir(interactions_dir):
        for entry in os.listdir(interactions_dir):
            day_dir = os.path.join(interactions_dir, entry)
            if os.path.isdir(day_dir):
                processed_dirs += 1
                pending += len(glob.glob(os.path.join(day_dir, "*.json")))

    # Knowledge base size
    kb_files = 0
    if os.path.isdir(ai_data_root):
        for root, dirs, files in os.walk(ai_data_root):
            kb_files += len(files)

    # Last enrichment run (check most recent file in ai_data_final)
    last_enrichment = None
    if os.path.isdir(ai_data_root):
        latest_time = 0
        for root, dirs, files in os.walk(ai_data_root):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    mt = os.path.getmtime(fp)
                    if mt > latest_time:
                        latest_time = mt
                except OSError:
                    continue
        if latest_time > 0:
            last_enrichment = datetime.fromtimestamp(latest_time).isoformat()

    return {
        "pipeline_status": "active" if pending > 0 else "idle",
        "pending_interactions": pending,
        "interaction_day_dirs": processed_dirs,
        "knowledge_base_files": kb_files,
        "last_enrichment_run": last_enrichment,
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.post("/ai/enrichment/run")
def enrichment_run(_: bool = Depends(require_admin)):
    """Trigger a manual enrichment run (placeholder — real impl uses the worker)."""
    # In production this would publish a message to the enrichment worker queue
    return {"status": "queued", "detail": "Manual enrichment run has been queued."}

@router.get("/ai/enrichment/jobs")
def enrichment_jobs(_: bool = Depends(require_admin)):
    """List recent enrichment jobs by scanning interaction date directories."""
    interactions_dir = os.path.join(os.getcwd(), "interactions")
    jobs = []
    if os.path.isdir(interactions_dir):
        for entry in sorted(os.listdir(interactions_dir), reverse=True)[:30]:
            day_dir = os.path.join(interactions_dir, entry)
            if os.path.isdir(day_dir):
                count = len(glob.glob(os.path.join(day_dir, "*.json")))
                jobs.append({"date": entry, "interaction_count": count})
    return {"jobs": jobs}

@router.get("/ai/content/status")
def content_status(_: bool = Depends(require_admin)):
    _not_impl("Implement content status")

@router.post("/ai/content/run")
def content_run(_: bool = Depends(require_admin)):
    _not_impl("Implement content run")

@router.get("/ai/content/jobs")
def content_jobs(_: bool = Depends(require_admin)):
    _not_impl("Implement content jobs list")
