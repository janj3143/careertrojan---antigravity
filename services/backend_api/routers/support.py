"""
Support Bridge Router — Zendesk Integration
=============================================

React → FastAPI (Support Bridge) → Zendesk API

Endpoints:
- POST /support/tickets — Create a ticket (logs internally + sends to Zendesk)
- GET /support/tickets — List user's tickets
- GET /support/tickets/{id} — Get ticket status
- POST /support/webhooks/zendesk — Receive Zendesk webhook events

Security:
- Token stays server-side
- Tickets enriched with user context
- Rate limited to prevent spam
- Webhook signature verification

Author: CareerTrojan System
Date: 27 February 2026
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.services.support_service import SupportService, verify_zendesk_webhook
from services.backend_api.routers.admin import require_admin

logger = logging.getLogger("support.router")
router = APIRouter(prefix="/api/support/v1", tags=["support"])

# Secondary router: matches the URL configured in Zendesk Admin webhook panel
# Zendesk → https://api.careertrojan.com/api/webhooks/v1/zendesk
webhooks_router = APIRouter(prefix="/api/webhooks/v1", tags=["webhooks"])


# ── Request / Response Models ────────────────────────────────────────────────

class CreateTicketRequest(BaseModel):
    """Request to create a support ticket."""
    subject: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10, max_length=10000)
    category: str = Field(..., description="billing, login, ai_output, bugs, feature_request")
    portal: str = Field(default="user_portal", description="user_portal, admin_portal, mentor_portal")
    request_id: Optional[str] = Field(None, description="Trace ID for specific AI run")
    resume_version_id: Optional[int] = Field(None, description="Resume version if relevant")
    extra_metadata: Optional[dict] = Field(None, description="Additional context")


class TicketResponse(BaseModel):
    """Response after creating a ticket."""
    ticket_id: int
    zendesk_ticket_id: Optional[int]
    zendesk_url: Optional[str]
    status: str
    priority: str


class TicketListItem(BaseModel):
    """Summary of a ticket for list views."""
    ticket_id: int
    zendesk_ticket_id: Optional[int]
    subject: str
    status: str
    priority: str
    category: str
    created_at: Optional[str]


class TicketDetailResponse(BaseModel):
    """Full ticket details."""
    ticket_id: int
    zendesk_ticket_id: Optional[int]
    zendesk_url: Optional[str]
    subject: str
    description: str
    status: str
    priority: str
    category: str
    portal: str
    created_at: Optional[str]
    updated_at: Optional[str]
    resolved_at: Optional[str]


class ZendeskWebhookPayload(BaseModel):
    """Zendesk webhook event payload."""
    ticket_id: Optional[int] = None
    status: Optional[str] = None
    event_type: Optional[str] = None
    comment_added: Optional[bool] = None
    timestamp: Optional[str] = None


class AdminReplyRequest(BaseModel):
    """Request to reply to a ticket as admin."""
    comment: str = Field(..., min_length=1, max_length=10000)
    public: bool = Field(True, description="Visible to requester?")
    new_status: Optional[str] = Field(None, description="Optionally change status: open, pending, solved, closed")


class AdminTicketListItem(BaseModel):
    """Enriched ticket summary for admin views."""
    ticket_id: int
    zendesk_ticket_id: Optional[int]
    zendesk_url: Optional[str]
    user_id: int
    user_email: Optional[str]
    subject: str
    status: str
    priority: str
    category: str
    portal: Optional[str]
    subscription_tier: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    resolved_at: Optional[str]
    last_comment_at: Optional[str]


# ── Dependency: Get current user ID ──────────────────────────────────────────

async def get_current_user_id(request: Request) -> int:
    """
    Extract user_id from JWT token.
    
    In production, this should validate the JWT and extract the user ID.
    For now, we check for user_id in request state (set by auth middleware).
    """
    # Try request.state (set by auth middleware)
    if hasattr(request.state, "user_id") and request.state.user_id:
        return request.state.user_id

    # Try header (for internal service-to-service calls)
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        try:
            return int(user_id_header)
        except ValueError:
            pass

    # For testing/development, allow query param
    user_id_param = request.query_params.get("user_id")
    if user_id_param:
        try:
            return int(user_id_param)
        except ValueError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


# ── Rate Limiting (simple in-memory) ─────────────────────────────────────────

from collections import defaultdict
from time import time

_ticket_rate_limit: dict = defaultdict(list)
RATE_LIMIT_WINDOW = 3600  # 1 hour
RATE_LIMIT_MAX_TICKETS = 10  # 10 tickets per hour per user


def check_rate_limit(user_id: int) -> bool:
    """Check if user is within rate limit for ticket creation."""
    now = time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _ticket_rate_limit[user_id] = [
        t for t in _ticket_rate_limit[user_id] if t > window_start
    ]

    # Check limit
    if len(_ticket_rate_limit[user_id]) >= RATE_LIMIT_MAX_TICKETS:
        return False

    # Record this attempt
    _ticket_rate_limit[user_id].append(now)
    return True


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: CreateTicketRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Create a support ticket.
    
    Creates a ticket in the local database AND sends to Zendesk.
    The ticket is enriched with user context:
    - user_id
    - subscription_tier (free/premium/elite)
    - tokens_remaining
    - portal (user_portal/admin_portal/mentor_portal)
    - request_id (for tracing AI runs)
    - resume_version_id (if relevant)
    """
    # Rate limit check
    if not check_rate_limit(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many tickets created. Please wait before creating more.",
            headers={"Retry-After": "3600"},
        )

    # Validate category
    valid_categories = {"billing", "login", "ai_output", "bugs", "feature_request"}
    if request.category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}",
        )

    # Validate portal
    valid_portals = {"user_portal", "admin_portal", "mentor_portal"}
    if request.portal not in valid_portals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid portal. Must be one of: {', '.join(valid_portals)}",
        )

    # Create ticket
    service = SupportService(db)
    try:
        result = await service.create_ticket(
            user_id=user_id,
            subject=request.subject,
            description=request.description,
            category=request.category,
            portal=request.portal,
            request_id=request.request_id,
            resume_version_id=request.resume_version_id,
            extra_metadata=request.extra_metadata,
        )
    except Exception as e:
        logger.exception("Failed to create ticket")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket",
        )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return TicketResponse(
        ticket_id=result["ticket_id"],
        zendesk_ticket_id=result.get("zendesk_ticket_id"),
        zendesk_url=result.get("zendesk_url"),
        status=result["status"],
        priority=result["priority"],
    )


@router.get("/tickets", response_model=List[TicketListItem])
async def list_tickets(
    status_filter: Optional[str] = None,
    limit: int = 20,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    List the current user's support tickets.
    
    Optionally filter by status: new, open, pending, hold, solved, closed
    """
    service = SupportService(db)
    tickets = await service.list_user_tickets(
        user_id=user_id,
        status=status_filter,
        limit=min(limit, 100),  # Cap at 100
    )

    return [TicketListItem(**t) for t in tickets]


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(
    ticket_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific ticket.
    
    Users can only view their own tickets.
    """
    service = SupportService(db)
    ticket = await service.get_ticket(ticket_id=ticket_id, user_id=user_id)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return TicketDetailResponse(**ticket)


# ============================================================================
# ADMIN ENDPOINTS — Ticket Queue + Reply
# ============================================================================

@router.get("/tickets/admin/all")
async def admin_list_all_tickets(
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin: List ALL tickets across all users with filters.

    Query params:
    - status_filter: new, open, pending, hold, solved, closed
    - category: billing, login, ai_output, bugs, feature_request
    - priority: low, normal, high, urgent
    - limit / offset: pagination
    """
    service = SupportService(db)
    result = await service.list_all_tickets(
        status_filter=status_filter,
        category=category,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return result


@router.get("/tickets/admin/{ticket_id}")
async def admin_get_ticket(
    ticket_id: int,
    _: bool = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin: Get full ticket details (no user_id filter — admin can see everything).
    """
    service = SupportService(db)
    ticket = await service.get_ticket(ticket_id=ticket_id, user_id=None)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    return ticket


@router.post("/tickets/{ticket_id}/reply")
async def admin_reply_to_ticket(
    ticket_id: int,
    request: AdminReplyRequest,
    admin_email: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Admin: Reply to a ticket — pushes comment to Zendesk and updates local record.

    - comment: Reply text (visible to user if public=true)
    - public: Whether the reply shows to the requester (default: true)
    - new_status: Optionally change ticket status (open, pending, solved, closed)
    """
    # Validate new_status if provided
    if request.new_status:
        valid = {"new", "open", "pending", "hold", "solved", "closed"}
        if request.new_status not in valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid)}",
            )

    service = SupportService(db)
    result = await service.admin_reply_to_ticket(
        ticket_id=ticket_id,
        comment=request.comment,
        admin_email=admin_email,
        public=request.public,
        new_status=request.new_status,
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )

    return result


# ============================================================================
# ADMIN ENDPOINTS — AI Agent Queue
# ============================================================================

@router.get("/ai/queue")
async def admin_ai_queue_status(
    _: str = Depends(require_admin),
):
    """
    Admin: List pending AI agent jobs in the queue directory.

    Returns job files sorted newest-first with their envelope metadata.
    """
    from services.backend_api.services.support_service import AI_QUEUE_DIR
    import json as _json
    from pathlib import Path as _Path

    queue_dir = _Path(AI_QUEUE_DIR)
    if not queue_dir.is_dir():
        return {"queue_dir": str(queue_dir), "jobs": [], "total": 0}

    jobs = []
    for f in sorted(queue_dir.glob("zendesk_*.json"), reverse=True):
        try:
            data = _json.loads(f.read_text(encoding="utf-8"))
            jobs.append({
                "job_id": data.get("job_id", f.stem),
                "action": data.get("action"),
                "ticket_id": data.get("ticket_id"),
                "queued_at": data.get("queued_at"),
                "status": data.get("status", "pending"),
            })
        except Exception:
            jobs.append({"job_id": f.stem, "error": "unreadable"})

    return {"queue_dir": str(queue_dir), "jobs": jobs, "total": len(jobs)}


@router.delete("/ai/queue/{job_id}")
async def admin_delete_ai_job(
    job_id: str,
    _: str = Depends(require_admin),
):
    """
    Admin: Remove a job from the AI agent queue (mark processed or discard).
    """
    from services.backend_api.services.support_service import AI_QUEUE_DIR
    from pathlib import Path as _Path

    job_path = _Path(AI_QUEUE_DIR) / f"{job_id}.json"
    if not job_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found in queue",
        )
    job_path.unlink()
    return {"ok": True, "deleted": job_id}


@router.post("/webhooks/zendesk", status_code=status.HTTP_200_OK)
async def zendesk_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_zendesk_webhook_signature: Optional[str] = Header(None),
):
    """
    Receive webhook events from Zendesk — single entry-point, three triggers.

    Zendesk triggers (configured separately in Zendesk Admin → Triggers):
        1️⃣  ticket.created       → Sync to DB + enqueue AI draft
        2️⃣  comment.added        → Update DB comment timestamp + AI follow-up
        3️⃣  status.changed       → Sync status + handle escalation / closure

    Loop-prevention:
        - If the acting user is our own API agent (ZENDESK_EMAIL) or the
          ``via.source`` is ``api``, we record the webhook but do NOT
          re-enqueue for AI processing.  This prevents the classic
          "AI writes note → webhook fires → AI writes note → …" infinite loop.

    The trigger type is identified from the payload in this order:
        1. ``event_type`` field (set by the Zendesk HTTP Target / Trigger body)
        2. Heuristic: ``comment`` present → comment.added;
           ``status`` differs from ``previous_status`` → status.changed;
           fallback → ticket.created
    """
    import json as _json

    # ── Verify signature ──────────────────────────────────────────
    body = await request.body()
    signature = (
        x_zendesk_webhook_signature
        or request.headers.get("X-Zendesk-Webhook-Signature", "")
    )
    timestamp = request.headers.get("X-Zendesk-Webhook-Signature-Timestamp", "")

    if not verify_zendesk_webhook(signature, body, timestamp):
        logger.warning("Invalid Zendesk webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # ── Parse payload ─────────────────────────────────────────────
    try:
        payload = _json.loads(body)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # ── Extract ticket ID ─────────────────────────────────────────
    zendesk_ticket_id = (
        payload.get("ticket", {}).get("id")
        or payload.get("ticket_id")
        or payload.get("id")
    )
    if not zendesk_ticket_id:
        logger.warning("Zendesk webhook missing ticket_id: %s", payload)
        return {"received": True, "processed": False, "reason": "No ticket_id"}

    zendesk_ticket_id = int(zendesk_ticket_id)

    # ── Loop detection ────────────────────────────────────────────
    from services.backend_api.services.support_service import ZENDESK_EMAIL as _agent_email

    is_self = _is_self_action(payload, _agent_email)

    # ── Determine event type ──────────────────────────────────────
    event_type = _resolve_event_type(payload)

    logger.info(
        "Zendesk webhook received: event=%s ticket_id=%s self=%s",
        event_type, zendesk_ticket_id, is_self,
    )

    # ── Dispatch to trigger handler ───────────────────────────────
    service = SupportService(db)

    if event_type == "ticket.created":
        result = await _handle_ticket_created(
            payload, zendesk_ticket_id, service, is_self,
        )
    elif event_type == "comment.added":
        result = await _handle_comment_added(
            payload, zendesk_ticket_id, service, is_self,
        )
    elif event_type == "status.changed":
        result = await _handle_status_changed(
            payload, zendesk_ticket_id, service, is_self,
        )
    else:
        # Unknown event — still record the webhook
        result = await service.update_from_webhook(
            zendesk_ticket_id=zendesk_ticket_id,
        )
        result["event_type"] = event_type

    result.setdefault("received", True)
    result.setdefault("event_type", event_type)
    result.setdefault("is_self_action", is_self)
    return result


# ============================================================================
# WEBHOOK INTERNAL HELPERS — Loop Detection + Event Resolution
# ============================================================================


def _is_self_action(payload: dict, agent_email: str) -> bool:
    """
    Detect whether this webhook was triggered by our own API user.

    Returns True when any of these conditions match:
    - ``payload.via.source.from.address`` == our agent email
    - ``payload.current_user.email`` == our agent email
    - ``payload.via.channel`` == "api"  AND  no human author (automated)
    - ``payload.comment.author.email`` == our agent email
    """
    if not agent_email:
        return False  # can't tell — treat as external

    agent_email_lower = agent_email.lower().strip()

    # Check via.source.from.address
    via_from = (
        payload.get("via", {})
        .get("source", {})
        .get("from", {})
        .get("address", "")
    )
    if via_from and via_from.lower().strip() == agent_email_lower:
        return True

    # Check current_user.email
    cu_email = payload.get("current_user", {}).get("email", "")
    if cu_email and cu_email.lower().strip() == agent_email_lower:
        return True

    # Check comment.author.email
    comment_author = (
        payload.get("comment", {}).get("author", {}).get("email", "")
    )
    if comment_author and comment_author.lower().strip() == agent_email_lower:
        return True

    # Check via.channel == "api" with no distinct human author
    via_channel = payload.get("via", {}).get("channel", "")
    if via_channel == "api":
        # If there's a current_user that's NOT our agent, it's a human via API
        if cu_email and cu_email.lower().strip() != agent_email_lower:
            return False
        return True  # API call with no human → self

    return False


def _resolve_event_type(payload: dict) -> str:
    """
    Determine the trigger event from the payload.

    Priority:
    1. Explicit ``event_type`` field (set in Zendesk Trigger JSON body)
    2. Heuristic detection from payload structure
    """
    explicit = payload.get("event_type") or payload.get("type")
    if explicit:
        # Normalize common aliases
        normalized = explicit.lower().strip()
        ALIASES = {
            "ticket_created": "ticket.created",
            "ticket.created": "ticket.created",
            "new_ticket": "ticket.created",
            "comment_added": "comment.added",
            "comment.added": "comment.added",
            "public_comment": "comment.added",
            "status_changed": "status.changed",
            "status.changed": "status.changed",
            "ticket.updated": "status.changed",   # Zendesk's generic update
            "ticket_updated": "status.changed",
        }
        return ALIASES.get(normalized, normalized)

    # Heuristic fallback
    if payload.get("comment"):
        return "comment.added"

    ticket = payload.get("ticket", {})
    if ticket.get("status") and ticket.get("previous_status"):
        return "status.changed"

    # If the ticket object has a created_at close to now, treat as created
    if ticket.get("created_at"):
        return "ticket.created"

    return "unknown"


# ============================================================================
# TRIGGER 1: TICKET CREATED
# ============================================================================

async def _handle_ticket_created(
    payload: dict,
    zendesk_ticket_id: int,
    service: SupportService,
    is_self: bool,
) -> dict:
    """
    Trigger 1️⃣ — A new ticket was created in Zendesk.

    Actions:
    - Upsert the ticket into the local support_tickets table
    - If NOT a self-action, enqueue an AI draft-reply job
    """
    from services.backend_api.services.support_service import enqueue_ai_job

    ticket = payload.get("ticket", {})
    new_status = ticket.get("status") or payload.get("status")

    # Sync to DB
    db_result = await service.update_from_webhook(
        zendesk_ticket_id=zendesk_ticket_id,
        status=new_status,
    )

    # Enqueue AI draft (skip self-actions to prevent loops)
    ai_job_id = None
    if not is_self:
        try:
            ai_job_id = enqueue_ai_job(
                action="ticket_created",
                ticket_id=db_result.get("ticket_id", 0),
                payload={
                    "zendesk_ticket_id": zendesk_ticket_id,
                    "subject": ticket.get("subject", ""),
                    "description": ticket.get("description", ""),
                    "status": new_status,
                    "priority": ticket.get("priority", "normal"),
                    "tags": ticket.get("tags", []),
                    "requester_id": ticket.get("requester_id"),
                    "event_type": "ticket.created",
                },
            )
        except Exception:
            logger.warning("Failed to enqueue AI job for new ticket %s", zendesk_ticket_id, exc_info=True)
    else:
        logger.info("Skipping AI enqueue for self-created ticket %s", zendesk_ticket_id)

    return {
        **db_result,
        "trigger": "ticket.created",
        "ai_job_id": ai_job_id,
    }


# ============================================================================
# TRIGGER 2: PUBLIC COMMENT ADDED
# ============================================================================

async def _handle_comment_added(
    payload: dict,
    zendesk_ticket_id: int,
    service: SupportService,
    is_self: bool,
) -> dict:
    """
    Trigger 2️⃣ — A public comment was added to a ticket.

    Actions:
    - Update last_comment_at in local DB
    - If NOT a self-action AND comment is public, enqueue AI follow-up
    - Skip internal notes from our own agent to prevent loops
    """
    from services.backend_api.services.support_service import enqueue_ai_job

    comment = payload.get("comment", {})
    ticket = payload.get("ticket", {})

    # Parse comment timestamp
    last_comment_at = None
    comment_ts = comment.get("created_at")
    if comment_ts:
        try:
            last_comment_at = datetime.fromisoformat(comment_ts.replace("Z", "+00:00"))
        except Exception:
            pass

    # Sync to DB
    db_result = await service.update_from_webhook(
        zendesk_ticket_id=zendesk_ticket_id,
        status=ticket.get("status"),
        last_comment_at=last_comment_at,
    )

    # Only enqueue AI follow-up for public, non-self comments
    ai_job_id = None
    is_public = comment.get("public", True)

    if not is_self and is_public:
        try:
            ai_job_id = enqueue_ai_job(
                action="comment_added",
                ticket_id=db_result.get("ticket_id", 0),
                payload={
                    "zendesk_ticket_id": zendesk_ticket_id,
                    "comment_body": comment.get("plain_body") or comment.get("body", ""),
                    "comment_author_id": comment.get("author_id"),
                    "is_public": is_public,
                    "subject": ticket.get("subject", ""),
                    "status": ticket.get("status", ""),
                    "priority": ticket.get("priority", "normal"),
                    "tags": ticket.get("tags", []),
                    "event_type": "comment.added",
                },
            )
        except Exception:
            logger.warning(
                "Failed to enqueue AI job for comment on ticket %s",
                zendesk_ticket_id, exc_info=True,
            )
    else:
        reason = "self-action" if is_self else "internal note"
        logger.info(
            "Skipping AI enqueue for comment on ticket %s (reason=%s)",
            zendesk_ticket_id, reason,
        )

    return {
        **db_result,
        "trigger": "comment.added",
        "comment_public": is_public,
        "ai_job_id": ai_job_id,
    }


# ============================================================================
# TRIGGER 3: TICKET STATUS CHANGED
# ============================================================================

async def _handle_status_changed(
    payload: dict,
    zendesk_ticket_id: int,
    service: SupportService,
    is_self: bool,
) -> dict:
    """
    Trigger 3️⃣ — Ticket status changed (e.g. new→open, open→pending, pending→solved).

    Actions:
    - Sync new status + resolved_at to local DB
    - If escalation (priority bumped to urgent), enqueue alert job
    - If solved/closed, enqueue satisfaction / follow-up job (non-self only)
    """
    from services.backend_api.services.support_service import enqueue_ai_job

    ticket = payload.get("ticket", {})
    new_status = ticket.get("status") or payload.get("status")
    previous_status = (
        ticket.get("previous_status")
        or payload.get("previous_status")
    )

    # Sync to DB
    db_result = await service.update_from_webhook(
        zendesk_ticket_id=zendesk_ticket_id,
        status=new_status,
    )

    # Enqueue jobs for non-self status changes
    ai_job_id = None
    if not is_self and new_status:
        try:
            ai_job_id = enqueue_ai_job(
                action="status_changed",
                ticket_id=db_result.get("ticket_id", 0),
                payload={
                    "zendesk_ticket_id": zendesk_ticket_id,
                    "new_status": new_status,
                    "previous_status": previous_status,
                    "subject": ticket.get("subject", ""),
                    "priority": ticket.get("priority", "normal"),
                    "tags": ticket.get("tags", []),
                    "event_type": "status.changed",
                },
            )
        except Exception:
            logger.warning(
                "Failed to enqueue AI job for status change on ticket %s",
                zendesk_ticket_id, exc_info=True,
            )
    elif is_self:
        logger.info(
            "Skipping AI enqueue for self-initiated status change on ticket %s (%s→%s)",
            zendesk_ticket_id, previous_status, new_status,
        )

    return {
        **db_result,
        "trigger": "status.changed",
        "previous_status": previous_status,
        "new_status": new_status,
        "ai_job_id": ai_job_id,
    }


# ── Health Check ─────────────────────────────────────────────────────────────

@router.get("/health")
async def support_health():
    """Check support service health and Zendesk connectivity."""
    from services.backend_api.services.support_service import zendesk_client

    return {
        "status": "ok",
        "zendesk_configured": zendesk_client.is_configured,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# WEBHOOK ALIAS — matches Zendesk Admin config
# Zendesk sends to: https://api.careertrojan.com/api/webhooks/v1/zendesk
# ============================================================================

@webhooks_router.post("/zendesk", status_code=status.HTTP_200_OK)
async def zendesk_webhook_alias(
    request: Request,
    db: Session = Depends(get_db),
    x_zendesk_webhook_signature: Optional[str] = Header(None),
):
    """
    Alias for the Zendesk webhook endpoint.
    
    Matches the URL configured in Zendesk Admin:
    POST https://api.careertrojan.com/api/webhooks/v1/zendesk
    
    Delegates to the main zendesk_webhook handler.
    """
    return await zendesk_webhook(
        request=request,
        db=db,
        x_zendesk_webhook_signature=x_zendesk_webhook_signature,
    )
