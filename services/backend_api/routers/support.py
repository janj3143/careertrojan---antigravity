from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security
from services.backend_api.services.helpdesk_stub_service import (
    build_helpdesk_sso_token,
    build_widget_bootstrap,
    get_helpdesk_config,
    get_helpdesk_readiness,
)
from services.backend_api.services.zendesk_bridge_service import (
    create_ticket as zendesk_create_ticket,
    get_ticket as zendesk_get_ticket,
    verify_webhook_signature,
)

router = APIRouter(prefix="/api/support/v1", tags=["support"])


class SupportTokenRequest(BaseModel):
    subject: str = "anonymous"
    email: str = ""
    name: str = ""
    ttl_seconds: int = 3600


class SupportTicketCreateRequest(BaseModel):
    subject: str
    description: str
    category: str
    requester_email: str
    requester_name: Optional[str] = None
    priority: Optional[str] = None
    portal: Optional[str] = None
    user_id: Optional[int] = None
    subscription_tier: Optional[str] = None
    tokens_remaining: Optional[int] = None
    request_id: Optional[str] = None
    resume_version_id: Optional[str] = None


def _resolve_user_from_token(db: Session, token: Optional[str]) -> Optional[models.User]:
    if not token:
        return None
    raw = token.replace("Bearer ", "").strip()
    if not raw:
        return None
    try:
        payload = security.decode_access_token(raw)
    except security.TokenValidationError:
        return None
    email = payload.get("sub")
    if not email:
        return None
    return db.query(models.User).filter(models.User.email == email).first()


def _ensure_support_table(db: Session) -> None:
    models.SupportTicket.__table__.create(bind=db.bind, checkfirst=True)


@router.get("/health")
def support_health() -> Dict[str, Any]:
    config = get_helpdesk_config()
    return {
        "status": "ok",
        "mode": config["mode"],
        "provider": config["provider"],
        "widget_enabled": config["widget_enabled"],
        "sso_enabled": config["sso_enabled"],
    }


@router.get("/status")
def support_status() -> Dict[str, Any]:
    config = get_helpdesk_config()
    return {
        "status": "ok",
        "mode": config["mode"],
        "provider": config["provider"],
        "config": config,
        "readiness": get_helpdesk_readiness(),
    }


@router.post("/token")
def issue_support_token(payload: SupportTokenRequest) -> Dict[str, Any]:
    config = get_helpdesk_config()
    token = build_helpdesk_sso_token(
        subject=payload.subject,
        email=payload.email,
        name=payload.name,
        ttl_seconds=payload.ttl_seconds,
    )
    return {
        "status": "ok",
        "mode": config["mode"],
        "provider": config["provider"],
        "token": token,
        "subject": payload.subject,
    }


@router.get("/widget-config")
def support_widget_config(
    portal: str = Query("user", min_length=2),
    user_id: Optional[str] = Query(None),
    user_email: Optional[str] = Query(None),
) -> Dict[str, Any]:
    user = {
        "id": user_id or "anonymous",
        "email": user_email or "",
    }
    return {
        "status": "ok",
        "mode": get_helpdesk_config()["mode"],
        "bootstrap": build_widget_bootstrap(portal=portal, user=user),
    }


@router.get("/wiring-test")
def support_wiring_test(portal: str = Query("admin", min_length=2)) -> Dict[str, Any]:
    config = get_helpdesk_config()
    sample = build_widget_bootstrap(portal=portal, user={"id": "wiring-test", "email": "wiring@test.local"})
    return {
        "status": "ok",
        "mode": config["mode"],
        "provider": config["provider"],
        "portal": portal,
        "checks": [
            "GET /api/support/v1/status",
            "GET /api/support/v1/widget-config?portal=<portal>",
            "window.__CAREERTROJAN_HELPDESK__ exists in portal runtime",
        ],
        "sample": sample,
    }


@router.get("/providers")
def support_providers() -> Dict[str, Any]:
    config = get_helpdesk_config()
    return {
        "status": "ok",
        "active": {
            "provider": config["provider"],
            "mode": config["mode"],
        },
        "available": [
            {
                "provider": "stub",
                "mode": "stub",
                "requires": ["HELPDESK_PROVIDER=stub"],
            },
            {
                "provider": "zendesk",
                "mode": "zendesk",
                "requires": [
                    "HELPDESK_PROVIDER=zendesk",
                    "ZENDESK_SHARED_SECRET",
                    "ZENDESK_SUBDOMAIN or ZENDESK_BASE_URL",
                ],
            },
        ],
    }


@router.get("/readiness")
def support_readiness() -> Dict[str, Any]:
    readiness = get_helpdesk_readiness()
    return {
        "status": "ok",
        "provider": readiness.get("provider"),
        "mode": readiness.get("mode"),
        "ready": readiness.get("ready"),
        "missing": readiness.get("missing"),
        "notes": readiness.get("notes"),
    }


@router.post("/tickets")
def create_support_ticket(
    payload: SupportTicketCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _ensure_support_table(db)

    current_user = _resolve_user_from_token(db, authorization)
    cfg = get_helpdesk_config()
    request_id = payload.request_id or request.headers.get("x-request-id")

    metadata = {
        "subscription_tier": payload.subscription_tier,
        "tokens_remaining": payload.tokens_remaining,
        "portal": payload.portal,
        "request_id": request_id,
        "resume_version_id": payload.resume_version_id,
        "requester_email": payload.requester_email,
    }

    zendesk_ticket_id = None
    zendesk_status = "queued"
    zendesk_priority = payload.priority
    zendesk_url = None

    if cfg.get("provider") == "zendesk":
        try:
            zendesk_result = zendesk_create_ticket(
                {
                    "subject": payload.subject,
                    "description": payload.description,
                    "category": payload.category,
                    "requester_email": payload.requester_email,
                    "requester_name": payload.requester_name,
                    "priority": payload.priority,
                    "portal": payload.portal,
                    "subscription_tier": payload.subscription_tier,
                    "tokens_remaining": payload.tokens_remaining,
                    "request_id": request_id,
                    "resume_version_id": payload.resume_version_id,
                    "user_id": payload.user_id or (current_user.id if current_user else None),
                }
            )
            zendesk_ticket_id = str(zendesk_result.get("zendesk_ticket_id") or "")
            zendesk_status = zendesk_result.get("status") or "new"
            zendesk_priority = zendesk_result.get("priority") or payload.priority
            zendesk_url = zendesk_result.get("url")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Zendesk bridge error: {exc}")

    ticket = models.SupportTicket(
        zendesk_ticket_id=zendesk_ticket_id,
        user_id=payload.user_id or (current_user.id if current_user else None),
        subject=payload.subject,
        status=zendesk_status,
        priority=zendesk_priority,
        category=payload.category,
        request_id=request_id,
        portal=payload.portal,
        metadata_json=metadata,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {
        "status": "ok",
        "provider": cfg.get("provider"),
        "mode": cfg.get("mode"),
        "ticket": {
            "id": ticket.id,
            "zendesk_ticket_id": ticket.zendesk_ticket_id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "request_id": ticket.request_id,
            "portal": ticket.portal,
            "zendesk_url": zendesk_url,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        },
    }


@router.get("/tickets/{ticket_id}")
def get_support_ticket(
    ticket_id: int,
    refresh_from_provider: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    _ensure_support_table(db)

    ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")

    provider_status = None
    if refresh_from_provider and ticket.zendesk_ticket_id and get_helpdesk_config().get("provider") == "zendesk":
        try:
            provider_data = zendesk_get_ticket(int(ticket.zendesk_ticket_id))
            provider_status = provider_data.get("status")
            ticket.status = provider_status or ticket.status
            ticket.priority = provider_data.get("priority") or ticket.priority
            db.commit()
            db.refresh(ticket)
        except Exception as exc:
            provider_status = f"error: {exc}"

    return {
        "status": "ok",
        "ticket": {
            "id": ticket.id,
            "zendesk_ticket_id": ticket.zendesk_ticket_id,
            "subject": ticket.subject,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "portal": ticket.portal,
            "request_id": ticket.request_id,
            "last_comment_at": ticket.last_comment_at.isoformat() if ticket.last_comment_at else None,
            "metadata": ticket.metadata_json,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            "provider_status": provider_status,
        },
    }


@router.post("/webhooks/zendesk")
async def zendesk_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_zendesk_webhook_signature: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _ensure_support_table(db)

    raw_body = await request.body()
    if not verify_webhook_signature(raw_body, x_zendesk_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid Zendesk webhook signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON webhook payload")

    ticket_data = payload.get("ticket") or payload
    zendesk_ticket_id = str(ticket_data.get("id") or payload.get("ticket_id") or "").strip()
    if not zendesk_ticket_id:
        raise HTTPException(status_code=400, detail="Missing Zendesk ticket id")

    ticket = (
        db.query(models.SupportTicket)
        .filter(models.SupportTicket.zendesk_ticket_id == zendesk_ticket_id)
        .order_by(models.SupportTicket.id.desc())
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found for webhook")

    if ticket_data.get("status"):
        ticket.status = str(ticket_data.get("status"))
    if ticket_data.get("priority"):
        ticket.priority = str(ticket_data.get("priority"))

    updated_at = ticket_data.get("updated_at") or payload.get("updated_at")
    if updated_at:
        try:
            ticket.last_comment_at = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
        except Exception:
            ticket.last_comment_at = datetime.utcnow()

    current_meta = ticket.metadata_json or {}
    current_meta["last_webhook_event"] = payload.get("event") or payload.get("type") or "ticket_update"
    current_meta["last_webhook_payload"] = payload
    ticket.metadata_json = current_meta

    db.commit()
    db.refresh(ticket)

    return {
        "status": "ok",
        "ticket_id": ticket.id,
        "zendesk_ticket_id": ticket.zendesk_ticket_id,
        "updated_status": ticket.status,
    }
