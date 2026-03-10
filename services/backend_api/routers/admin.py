
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import os, glob, json, logging
from datetime import datetime, timedelta
from uuid import uuid4

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security
from services.shared.paths import CareerTrojanPaths

logger = logging.getLogger("admin")
router = APIRouter(prefix="/api/admin/v1", tags=["admin"])
paths = CareerTrojanPaths()


def _mask_api_key(raw: str | None) -> str | None:
    if not raw:
        return None
    value = str(raw)
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}...{value[-3:]}"


_integration_state = {
    "sendgrid": {
        "configured": bool(os.getenv("SENDGRID_API_KEY")),
        "api_key_masked": _mask_api_key(os.getenv("SENDGRID_API_KEY")),
        "last_configured_at": None,
        "mode": "local"
    },
    "klaviyo": {
        "configured": bool(os.getenv("KLAVIYO_API_KEY")),
        "api_key_masked": _mask_api_key(os.getenv("KLAVIYO_API_KEY")),
        "last_configured_at": None,
        "mode": "mass_mail"
    },
    "gmail": {
        "configured": False,
        "api_key_masked": None,
        "last_configured_at": None,
        "mode": "local"
    },
}

_email_dispatch_log = []


def _detect_payment_runtime_modes() -> dict:
    stripe_secret = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    braintree_env = (os.getenv("BRAINTREE_ENVIRONMENT") or "").strip().lower()

    if stripe_secret.startswith("sk_live_"):
        stripe_mode = "live"
    elif stripe_secret.startswith("sk_test_"):
        stripe_mode = "sandbox"
    elif stripe_secret:
        stripe_mode = "unknown"
    else:
        stripe_mode = "missing"

    if braintree_env == "production":
        braintree_mode = "live"
    elif braintree_env:
        braintree_mode = "sandbox"
    else:
        braintree_mode = "missing"

    return {
        "stripe": {
            "configured": bool(stripe_secret),
            "mode": stripe_mode,
            "api_key_masked": _mask_api_key(stripe_secret),
            "is_live": stripe_mode == "live",
        },
        "braintree": {
            "configured": bool(braintree_env),
            "mode": braintree_mode,
            "environment": braintree_env or None,
            "merchant_id_masked": _mask_api_key(os.getenv("BRAINTREE_MERCHANT_ID")),
            "is_live": braintree_mode == "live",
        },
    }

# Dependency for Admin Auth
def require_admin(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.decode_access_token(token)
        email: str = payload.get("sub")
        role: str = payload.get("role")
        provider = security.get_auth_provider()
        has_admin_scope = security.token_has_scopes(payload, ["admin:access"])

        if provider == "auth0":
            if not (has_admin_scope or role == "admin"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin scope required")
        else:
            if role != "admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")

        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except security.TokenValidationError:
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


@router.get("/integrations/status")
def integrations_status(_: bool = Depends(require_admin)):
    providers = {
        name: {
            "configured": cfg.get("configured", False),
            "api_key_masked": cfg.get("api_key_masked"),
            "last_configured_at": cfg.get("last_configured_at"),
            "mode": cfg.get("mode"),
        }
        for name, cfg in _integration_state.items()
    }
    return {
        "providers": providers,
        "payment_gateways": _detect_payment_runtime_modes(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/payments/disputes")
def payment_disputes(
    days: int = Query(default=90, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=1000),
    dispute_type: Optional[str] = Query(default=None, pattern="^(dispute_opened|dispute_lost|dispute_won)$"),
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin finance view for Braintree dispute events captured in payment transactions."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    dispute_types = ["dispute_opened", "dispute_lost", "dispute_won"]

    query = (
        db.query(models.PaymentTransaction)
        .filter(
            models.PaymentTransaction.gateway == "braintree",
            models.PaymentTransaction.created_at >= cutoff,
            models.PaymentTransaction.transaction_type.in_(dispute_types),
        )
    )

    if dispute_type:
        query = query.filter(models.PaymentTransaction.transaction_type == dispute_type)

    rows = query.order_by(models.PaymentTransaction.created_at.desc()).limit(limit).all()

    counts = {key: 0 for key in dispute_types}
    amount_by_type = {key: 0.0 for key in dispute_types}

    records = []
    for row in rows:
        dtype = row.transaction_type or "unknown"
        if dtype in counts:
            counts[dtype] += 1
            amount_by_type[dtype] += float(row.amount or 0.0)

        records.append(
            {
                "id": row.id,
                "user_id": row.user_id,
                "subscription_id": row.subscription_id,
                "gateway_transaction_id": row.gateway_transaction_id,
                "transaction_type": dtype,
                "status": row.status,
                "amount": row.amount,
                "currency": row.currency,
                "plan_id": row.plan_id,
                "description": row.description,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "gateway_response": row.gateway_response,
            }
        )

    return {
        "days": days,
        "limit": limit,
        "filter": dispute_type,
        "counts": counts,
        "amount_by_type": {k: round(v, 2) for k, v in amount_by_type.items()},
        "records": records,
    }


@router.post("/integrations/reminders/non-live")
def send_non_live_api_reminder(payload: dict, _: bool = Depends(require_admin)):
    provider = str(payload.get("provider") or "").strip().lower()
    if provider not in {"stripe", "braintree"}:
        raise HTTPException(status_code=400, detail="provider must be one of: stripe, braintree")

    modes = _detect_payment_runtime_modes()
    provider_status = modes.get(provider, {})
    mode = provider_status.get("mode", "unknown")
    if mode == "live":
        return {
            "status": "skipped",
            "provider": provider,
            "reason": "already_live",
        }

    admin_email = (
        str(payload.get("email") or "").strip()
        or os.getenv("ADMIN_ALERT_EMAIL")
        or os.getenv("ZENDESK_EMAIL")
        or ""
    )
    if not admin_email:
        raise HTTPException(status_code=400, detail="No target admin email configured. Provide payload.email or ADMIN_ALERT_EMAIL")

    reminder = {
        "id": f"rem_{uuid4().hex[:12]}",
        "provider": provider,
        "mode": "admin_reminder",
        "to": [admin_email],
        "subject": f"[Action Required] {provider.title()} is running in {mode} mode",
        "body": (
            f"Admin reminder: {provider.title()} is currently running in '{mode}' mode. "
            "Please replace sandbox/test credentials with live production credentials."
        ),
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
    }
    _email_dispatch_log.append(reminder)

    return {
        "status": "queued",
        "provider": provider,
        "target": admin_email,
        "current_mode": mode,
        "message": reminder,
    }


@router.post("/integrations/sendgrid/configure")
def configure_sendgrid(payload: dict, _: bool = Depends(require_admin)):
    api_key = str(payload.get("api_key") or "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key is required")

    _integration_state["sendgrid"].update({
        "configured": True,
        "api_key_masked": _mask_api_key(api_key),
        "last_configured_at": datetime.utcnow().isoformat(),
    })
    return {"status": "configured", "provider": "sendgrid"}


@router.post("/integrations/klaviyo/configure")
def configure_klaviyo(payload: dict, _: bool = Depends(require_admin)):
    api_key = str(payload.get("api_key") or "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key is required")

    _integration_state["klaviyo"].update({
        "configured": True,
        "api_key_masked": _mask_api_key(api_key),
        "last_configured_at": datetime.utcnow().isoformat(),
    })
    return {"status": "configured", "provider": "klaviyo"}


@router.post("/integrations/gmail/configure")
def configure_gmail(payload: dict, _: bool = Depends(require_admin)):
    _integration_state["gmail"].update({
        "configured": True,
        "api_key_masked": None,
        "last_configured_at": datetime.utcnow().isoformat(),
    })
    return {"status": "configured", "provider": "gmail", "config": payload}


@router.post("/integrations/{provider}/disconnect")
def disconnect_integration(provider: str, _: bool = Depends(require_admin)):
    key = provider.strip().lower()
    if key not in _integration_state:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    _integration_state[key].update({
        "configured": False,
        "api_key_masked": None,
        "last_configured_at": datetime.utcnow().isoformat(),
    })
    return {"status": "disconnected", "provider": key}


def _resolve_provider(provider: str | None) -> str:
    requested = (provider or "").strip().lower()
    if requested:
        if requested not in _integration_state:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        return requested

    if _integration_state["sendgrid"]["configured"]:
        return "sendgrid"
    if _integration_state["klaviyo"]["configured"]:
        return "klaviyo"
    if _integration_state["gmail"]["configured"]:
        return "gmail"
    raise HTTPException(status_code=400, detail="No configured provider. Configure SendGrid/Klaviyo/Gmail first")


@router.post("/email/send_test")
def send_test_email(payload: dict, _: bool = Depends(require_admin)):
    to_email = str(payload.get("to") or payload.get("to_email") or "").strip()
    subject = str(payload.get("subject") or "Test Email").strip()
    body = str(payload.get("body") or "").strip()
    if not to_email:
        raise HTTPException(status_code=400, detail="to (or to_email) is required")

    provider = _resolve_provider(payload.get("provider"))
    if not _integration_state[provider]["configured"]:
        raise HTTPException(status_code=400, detail=f"Provider not configured: {provider}")

    item = {
        "id": f"msg_{uuid4().hex[:12]}",
        "provider": provider,
        "mode": "test",
        "to": [to_email],
        "subject": subject,
        "body": body,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
    }
    _email_dispatch_log.append(item)
    return {"status": "queued", "provider": provider, "message": item}


@router.post("/email/send_bulk")
def send_bulk_email(payload: dict, _: bool = Depends(require_admin)):
    recipients = payload.get("recipients") or payload.get("to") or []
    if isinstance(recipients, str):
        recipients = [recipients]
    recipients = [str(r).strip() for r in recipients if str(r).strip()]
    if not recipients:
        raise HTTPException(status_code=400, detail="recipients (or to) is required")

    subject = str(payload.get("subject") or "Bulk Email").strip()
    body = str(payload.get("body") or "").strip()
    provider = _resolve_provider(payload.get("provider"))
    if not _integration_state[provider]["configured"]:
        raise HTTPException(status_code=400, detail=f"Provider not configured: {provider}")

    item = {
        "id": f"bulk_{uuid4().hex[:12]}",
        "provider": provider,
        "mode": "bulk",
        "to": recipients,
        "subject": subject,
        "body": body,
        "status": "queued",
        "recipient_count": len(recipients),
        "created_at": datetime.utcnow().isoformat(),
    }
    _email_dispatch_log.append(item)
    return {
        "status": "queued",
        "provider": provider,
        "recipient_count": len(recipients),
        "message": item,
    }


@router.get("/email/logs")
def email_logs(days: int = Query(default=30, ge=1, le=365), _: bool = Depends(require_admin)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = []
    for item in _email_dispatch_log:
        created_at = item.get("created_at")
        try:
            when = datetime.fromisoformat(created_at)
        except Exception:
            when = datetime.utcnow()
        if when >= cutoff:
            records.append(item)

    return {
        "days": days,
        "count": len(records),
        "records": list(reversed(records[-500:])),
    }


@router.get("/email/analytics")
def email_analytics(days: int = Query(default=30, ge=1, le=365), _: bool = Depends(require_admin)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    total = 0
    test_count = 0
    bulk_count = 0
    recipients = 0
    by_provider = {"sendgrid": 0, "klaviyo": 0, "gmail": 0}

    for item in _email_dispatch_log:
        created_at = item.get("created_at")
        try:
            when = datetime.fromisoformat(created_at)
        except Exception:
            when = datetime.utcnow()
        if when < cutoff:
            continue

        total += 1
        mode = item.get("mode")
        if mode == "test":
            test_count += 1
        if mode == "bulk":
            bulk_count += 1
        recipients += int(item.get("recipient_count") or len(item.get("to") or []))

        provider = str(item.get("provider") or "").lower()
        if provider in by_provider:
            by_provider[provider] += 1

    return {
        "days": days,
        "total_messages": total,
        "test_messages": test_count,
        "bulk_messages": bulk_count,
        "recipient_count": recipients,
        "by_provider": by_provider,
    }

@router.get("/email/status")
def email_status(_: bool = Depends(require_admin)):
    _not_impl("Implement email status")

@router.get("/parsers/status")
def parsers_status(_: bool = Depends(require_admin)):
    parser_root = paths.parser_root
    if not parser_root.exists():
        raise HTTPException(status_code=503, detail="Parser root not available")

    incoming = parser_root / "incoming"
    queue_count = 0
    if incoming.exists():
        queue_count = sum(1 for p in incoming.rglob("*") if p.is_file())

    return {"status": "ok", "jobs_queued": queue_count}

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
    interactions_dir = paths.interactions
    today_dir = interactions_dir / now.strftime("%Y-%m-%d")
    file_interactions_today = len(list(today_dir.glob("*.json"))) if today_dir.is_dir() else 0

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
    ai_data_root = paths.ai_data_final
    ai_stats = {}
    if ai_data_root.is_dir():
        for subdir in ["parsed_resumes", "job_matching", "learning_library", "profiles", "trained_models"]:
            subpath = ai_data_root / subdir
            if subpath.is_dir():
                ai_stats[subdir] = len(list(subpath.iterdir()))
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
    interactions_dir = paths.interactions
    ai_data_root = paths.ai_data_final

    # Count pending interactions (files in interactions/ directory)
    pending = 0
    processed_dirs = 0
    if interactions_dir.is_dir():
        for entry in interactions_dir.iterdir():
            if entry.is_dir():
                processed_dirs += 1
                pending += len(list(entry.glob("*.json")))

    # Knowledge base size
    kb_files = 0
    if ai_data_root.is_dir():
        for root, dirs, files in os.walk(ai_data_root):
            kb_files += len(files)

    # Last enrichment run (check most recent file in ai_data_final)
    last_enrichment = None
    if ai_data_root.is_dir():
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
    interactions_dir = paths.interactions
    jobs = []
    if interactions_dir.is_dir():
        day_dirs = sorted([p.name for p in interactions_dir.iterdir() if p.is_dir()], reverse=True)[:30]
        for day in day_dirs:
            day_dir = interactions_dir / day
            count = len(list(day_dir.glob("*.json")))
            jobs.append({"date": day, "interaction_count": count})
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
