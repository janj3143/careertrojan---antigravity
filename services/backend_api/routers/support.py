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

logger = logging.getLogger("support.router")
router = APIRouter(prefix="/api/support/v1", tags=["support"])


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


@router.post("/webhooks/zendesk", status_code=status.HTTP_200_OK)
async def zendesk_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_zendesk_webhook_signature: Optional[str] = Header(None),
):
    """
    Receive webhook events from Zendesk.
    
    Events handled:
    - ticket.updated — Status changed, comment added
    - ticket.solved — Ticket marked as solved
    - ticket.closed — Ticket closed
    
    The webhook updates the local support_tickets table to keep it in sync.
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify webhook signature
    signature = x_zendesk_webhook_signature or request.headers.get("X-Zendesk-Webhook-Signature", "")
    if not verify_zendesk_webhook(signature, body):
        logger.warning("Invalid Zendesk webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Parse payload
    try:
        import json
        payload = json.loads(body)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Extract ticket info (Zendesk webhook format varies by trigger)
    # Common patterns: payload.ticket.id, payload.id, payload.ticket_id
    zendesk_ticket_id = (
        payload.get("ticket", {}).get("id")
        or payload.get("ticket_id")
        or payload.get("id")
    )

    if not zendesk_ticket_id:
        logger.warning("Zendesk webhook missing ticket_id: %s", payload)
        return {"received": True, "processed": False, "reason": "No ticket_id"}

    # Extract status
    new_status = (
        payload.get("ticket", {}).get("status")
        or payload.get("status")
    )

    # Extract event type
    event_type = payload.get("event_type") or payload.get("type")

    # Extract comment timestamp if present
    last_comment_at = None
    if payload.get("comment"):
        comment_ts = payload["comment"].get("created_at")
        if comment_ts:
            try:
                last_comment_at = datetime.fromisoformat(comment_ts.replace("Z", "+00:00"))
            except Exception:
                pass

    logger.info(
        "Zendesk webhook received: ticket_id=%s, status=%s, event=%s",
        zendesk_ticket_id, new_status, event_type,
    )

    # Update local record
    service = SupportService(db)
    result = await service.update_from_webhook(
        zendesk_ticket_id=int(zendesk_ticket_id),
        status=new_status,
        last_comment_at=last_comment_at,
    )

    return {
        "received": True,
        "processed": result.get("updated", False),
        "ticket_id": result.get("ticket_id"),
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
