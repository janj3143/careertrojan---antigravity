"""
GDPR Compliance Router — Data Rights Endpoints
================================================

Implements UK GDPR / EU GDPR data-subject rights:
 - Art. 15  Right of access (view personal data)
 - Art. 17  Right to erasure (delete account + all data)
 - Art. 20  Right to data portability (export as JSON)
 - Art. 7   Consent management (grant / revoke / view)

All endpoints require authentication (current user).
"""

import json
import os
import shutil
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security

logger = logging.getLogger("gdpr")
router = APIRouter(prefix="/api/gdpr/v1", tags=["gdpr"])


# ── Dependency: authenticated user ────────────────────────────

def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _audit(db: Session, user_id: int, actor_id: int, action: str, resource_type: str,
           resource_id: str = None, detail: str = None, ip: str = None):
    """Write an immutable audit-log entry."""
    entry = models.AuditLog(
        user_id=user_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()


# ── Art. 7 — Consent ─────────────────────────────────────────

@router.get("/consent")
def get_consent(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all consent records for the authenticated user."""
    records = (
        db.query(models.ConsentRecord)
        .filter(models.ConsentRecord.user_id == current_user.id)
        .order_by(models.ConsentRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "consent_type": r.consent_type,
            "granted": r.granted,
            "version": r.version,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "revoked_at": r.revoked_at.isoformat() if r.revoked_at else None,
        }
        for r in records
    ]


@router.post("/consent")
def grant_consent(
    consent_type: str,
    granted: bool = True,
    request: Request = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record explicit consent (or revocation) for a processing purpose."""
    valid_types = {"terms", "marketing", "data_processing", "cookies", "analytics"}
    if consent_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"consent_type must be one of {valid_types}")

    ip = request.client.host if request and request.client else None

    record = models.ConsentRecord(
        user_id=current_user.id,
        consent_type=consent_type,
        granted=granted,
        ip_address=ip,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(record)
    db.commit()

    _audit(db, current_user.id, current_user.id,
           "consent_grant" if granted else "consent_revoke",
           "consent", str(record.id), f"type={consent_type} granted={granted}", ip)

    return {"status": "recorded", "consent_type": consent_type, "granted": granted}


# ── Art. 15 / 20 — Data Export ────────────────────────────────

@router.get("/export")
def export_my_data(
    request: Request = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export ALL personal data as a JSON bundle.
    Returns the data inline (for small datasets).
    For large datasets, a background job + download link pattern is preferred.
    """
    ip = request.client.host if request and request.client else None

    # Gather profile
    profile_data = None
    if current_user.profile:
        p = current_user.profile
        profile_data = {
            "bio": p.bio,
            "linkedin_url": p.linkedin_url,
            "github_url": p.github_url,
            "website_url": p.website_url,
            "phone_number": p.phone_number,
            "location": p.location,
        }

    # Gather resumes (metadata only — not binary files)
    resumes = [
        {"id": r.id, "file_path": r.file_path, "version": r.version,
         "is_primary": r.is_primary, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in current_user.resumes
    ]

    # Gather mentorship data
    mentorships = [
        {"id": m.id, "mentor_id": m.mentor_id, "status": m.status,
         "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
         "notes": m.notes, "created_at": m.created_at.isoformat() if m.created_at else None}
        for m in current_user.mentorship_requests
    ]

    # Gather consent records
    consents = [
        {"consent_type": c.consent_type, "granted": c.granted,
         "version": c.version, "created_at": c.created_at.isoformat() if c.created_at else None,
         "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None}
        for c in (db.query(models.ConsentRecord)
                  .filter(models.ConsentRecord.user_id == current_user.id).all())
    ]

    # Gather interactions (last 10,000 for inline response)
    interactions = [
        {"action_type": i.action_type, "method": i.method, "path": i.path,
         "status_code": i.status_code, "created_at": i.created_at.isoformat() if i.created_at else None}
        for i in (db.query(models.Interaction)
                  .filter(models.Interaction.user_id == current_user.id)
                  .order_by(models.Interaction.created_at.desc())
                  .limit(10000).all())
    ]

    export_bundle = {
        "export_date": datetime.utcnow().isoformat(),
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "profile": profile_data,
        "resumes": resumes,
        "mentorships": mentorships,
        "consent_records": consents,
        "interactions": interactions,
    }

    # Record the export in audit log
    _audit(db, current_user.id, current_user.id, "data_export",
           "user", str(current_user.id), "Full personal data export", ip)

    # Track the export request
    export_req = models.DataExportRequest(
        user_id=current_user.id,
        status="completed",
        completed_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(export_req)
    db.commit()

    return export_bundle


# ── Art. 17 — Right to Erasure ────────────────────────────────

@router.delete("/delete-account")
def delete_my_account(
    confirm: str = "no",
    request: Request = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete all personal data for the authenticated user.
    Requires `confirm=yes` query param as a safety gate.

    This will:
    1. Delete consent records, interactions, mentorships, resumes, profile
    2. Anonymise the user row (email → deleted_{id}@anon, name → null)
    3. Purge file-based interaction data for this user
    4. Write a final audit-log entry (retained for legal compliance)
    """
    if confirm != "yes":
        raise HTTPException(
            status_code=400,
            detail="Pass ?confirm=yes to confirm permanent account deletion."
        )

    ip = request.client.host if request and request.client else None
    uid = current_user.id

    # 1. Delete related records
    db.query(models.ConsentRecord).filter(models.ConsentRecord.user_id == uid).delete()
    db.query(models.Interaction).filter(models.Interaction.user_id == uid).delete()
    db.query(models.DataExportRequest).filter(models.DataExportRequest.user_id == uid).delete()

    # Delete mentorship notes linked through mentorships
    mentorship_ids = [m.id for m in current_user.mentorship_requests]
    if mentorship_ids:
        db.query(models.MentorNote).filter(models.MentorNote.link_id.in_(mentorship_ids)).delete(synchronize_session=False)
    db.query(models.Mentorship).filter(models.Mentorship.mentee_id == uid).delete()

    # Delete resumes
    db.query(models.Resume).filter(models.Resume.user_id == uid).delete()

    # Delete profile
    db.query(models.UserProfile).filter(models.UserProfile.user_id == uid).delete()

    # Delete blocker data
    db.query(models.BlockerImprovementPlan).filter(models.BlockerImprovementPlan.user_id == uid).delete()
    db.query(models.ApplicationBlocker).filter(models.ApplicationBlocker.user_id == uid).delete()

    # 2. Anonymise the user row (keep for referential integrity but strip PII)
    current_user.email = f"deleted_{uid}@anon.careertrojan.com"
    current_user.full_name = None
    current_user.hashed_password = "DELETED"
    current_user.is_active = False
    current_user.otp_secret = None

    # 3. Purge file-based interactions for this user
    interactions_dir = os.path.join(os.getcwd(), "interactions")
    if os.path.isdir(interactions_dir):
        _purge_user_interaction_files(interactions_dir, uid)

    # 4. Final audit entry (retained for legal compliance — no PII)
    _audit(db, uid, uid, "account_delete", "user", str(uid),
           "Account permanently deleted per GDPR Art. 17", ip)

    db.commit()
    logger.info(f"GDPR erasure completed for user_id={uid}")

    return {"status": "deleted", "detail": "All personal data has been permanently erased."}


def _purge_user_interaction_files(base_dir: str, user_id: int):
    """Remove file-based interaction JSON files that reference this user."""
    purged = 0
    try:
        for root, dirs, files in os.walk(base_dir):
            for fname in files:
                if not fname.endswith(".json"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("user_id") == user_id or data.get("user_id") == str(user_id):
                        os.remove(fpath)
                        purged += 1
                except (json.JSONDecodeError, OSError):
                    continue
    except OSError:
        pass
    logger.info(f"Purged {purged} interaction files for user_id={user_id}")


# ── Art. 15 — Audit Log (user's own) ─────────────────────────

@router.get("/audit-log")
def my_audit_log(
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the user's own audit trail (who accessed/exported/deleted their data)."""
    entries = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.user_id == current_user.id)
        .order_by(models.AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "action": e.action,
            "resource_type": e.resource_type,
            "detail": e.detail,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
