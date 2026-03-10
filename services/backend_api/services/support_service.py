"""
Support Service — Zendesk Bridge with Ticket Enrichment
========================================================

Handles support ticket creation, status tracking, and Zendesk integration.
Enriches tickets with user context (subscription, tokens, request IDs).

Author: CareerTrojan System
Date: 27 February 2026
"""

import os
import json
import uuid
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from base64 import b64encode
from pathlib import Path

from sqlalchemy.orm import Session

logger = logging.getLogger("support.service")

# ── Zendesk Configuration ────────────────────────────────────────────────────
ZENDESK_BASE_URL = os.getenv("ZENDESK_BASE_URL", "https://careertrojan.zendesk.com")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL", "")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN", "")
ZENDESK_DEFAULT_GROUP_ID = os.getenv("ZENDESK_DEFAULT_GROUP_ID", "")
ZENDESK_DEFAULT_FORM_ID = os.getenv("ZENDESK_DEFAULT_FORM_ID", "")
ZENDESK_WEBHOOK_SECRET = os.getenv("ZENDESK_WEBHOOK_SECRET", "")

# ── AI Agent Queue ────────────────────────────────────────────────────────────
# Only active when ZENDESK_AI_AGENT_ENABLED=true in .env
ZENDESK_AI_AGENT_ENABLED = os.getenv("ZENDESK_AI_AGENT_ENABLED", "false").lower() in ("true", "1", "yes")
# Production: /opt/careertrojan/api/queue
# Dev fallback: ./data/queue  (relative to project root)
AI_QUEUE_DIR = os.getenv(
    "ZENDESK_AI_QUEUE_DIR",
    "/opt/careertrojan/api/queue" if os.path.isdir("/opt") else str(
        Path(__file__).resolve().parents[3] / "data" / "queue"
    ),
)


def enqueue_ai_job(
    action: str,
    ticket_id: int,
    payload: Dict[str, Any],
) -> Optional[str]:
    """
    Write a job file to the AI agent queue directory.

    Returns None immediately if ZENDESK_AI_AGENT_ENABLED is not true.

    The AI agent watches this directory and picks up .json files to process
    (draft responses, classify tickets, enrich context, auto-triage, etc.).

    Args:
        action: Job type — "new_ticket", "admin_reply", "status_change", "classify"
        ticket_id: Local ticket ID
        payload: Full context for the AI agent

    Returns:
        job_id: Unique job identifier, or None if agent is disabled.
    """
    if not ZENDESK_AI_AGENT_ENABLED:
        return None

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    job_id = f"zendesk_{ts}_{uuid.uuid4().hex}"

    os.makedirs(AI_QUEUE_DIR, exist_ok=True)
    job_path = os.path.join(AI_QUEUE_DIR, f"{job_id}.json")

    job_envelope = {
        "job_id": job_id,
        "action": action,
        "ticket_id": ticket_id,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "payload": payload,
    }

    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(job_envelope, f, ensure_ascii=False, indent=2, default=str)

    logger.info("AI job queued: %s (action=%s, ticket=%s)", job_id, action, ticket_id)
    return job_id

# Category → Priority mapping
CATEGORY_PRIORITY_MAP = {
    "billing": "high",
    "login": "high",
    "ai_output": "normal",
    "bugs": "normal",
    "feature_request": "low",
}


class ZendeskClient:
    """HTTP client for Zendesk API v2."""

    def __init__(self):
        self.base_url = f"{ZENDESK_BASE_URL}/api/v2"
        self.auth_header = self._build_auth_header()

    def _build_auth_header(self) -> str:
        """Build Basic auth header: email/token:api_token (base64)."""
        if not ZENDESK_EMAIL or not ZENDESK_API_TOKEN:
            return ""
        credentials = f"{ZENDESK_EMAIL}/token:{ZENDESK_API_TOKEN}"
        encoded = b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @property
    def is_configured(self) -> bool:
        return bool(self.auth_header)

    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a ticket in Zendesk."""
        if not self.is_configured:
            logger.warning("Zendesk not configured — skipping ticket creation")
            return {"error": "Zendesk not configured"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/tickets.json",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                json={"ticket": ticket_data},
            )
            response.raise_for_status()
            return response.json()

    async def get_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """Get ticket details from Zendesk."""
        if not self.is_configured:
            return {"error": "Zendesk not configured"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/tickets/{ticket_id}.json",
                headers={"Authorization": self.auth_header},
            )
            response.raise_for_status()
            return response.json()

    async def add_comment(self, ticket_id: int, comment: str, public: bool = True) -> Dict[str, Any]:
        """Add a comment to a ticket."""
        if not self.is_configured:
            return {"error": "Zendesk not configured"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/tickets/{ticket_id}.json",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                json={
                    "ticket": {
                        "comment": {
                            "body": comment,
                            "public": public,
                        }
                    }
                },
            )
            response.raise_for_status()
            return response.json()

    async def update_ticket_status(self, ticket_id: int, status: str) -> Dict[str, Any]:
        """Update ticket status."""
        if not self.is_configured:
            return {"error": "Zendesk not configured"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/tickets/{ticket_id}.json",
                headers={
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json",
                },
                json={"ticket": {"status": status}},
            )
            response.raise_for_status()
            return response.json()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a Zendesk user profile (requester, agent, etc.)."""
        if not self.is_configured:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/users/{user_id}.json",
                headers={"Authorization": self.auth_header},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("user")

    async def get_ticket_comments(
        self, ticket_id: int, sort_order: str = "asc"
    ) -> List[Dict[str, Any]]:
        """Fetch comments on a ticket (oldest-first by default)."""
        if not self.is_configured:
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/tickets/{ticket_id}/comments.json",
                headers={"Authorization": self.auth_header},
                params={"sort_order": sort_order},
            )
            response.raise_for_status()
            return response.json().get("comments", [])

    async def search_articles(
        self, query: str, per_page: int = 3
    ) -> List[Dict[str, Any]]:
        """Search the Help Center for knowledge-base articles."""
        if not self.is_configured:
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{ZENDESK_BASE_URL}/api/v2/help_center/articles/search.json",
                headers={"Authorization": self.auth_header},
                params={"query": query, "per_page": per_page},
            )
            if response.status_code == 404:
                # Help Center may not be enabled
                return []
            response.raise_for_status()
            return response.json().get("results", [])


# Singleton client
zendesk_client = ZendeskClient()


class SupportService:
    """
    Support ticket management with Zendesk integration.
    
    Features:
    - Creates tickets in Zendesk with full user enrichment
    - Tracks tickets locally for analytics & auditing
    - Syncs status updates from Zendesk webhooks
    """

    def __init__(self, db: Session):
        self.db = db

    async def create_ticket(
        self,
        user_id: int,
        subject: str,
        description: str,
        category: str,
        portal: str = "user_portal",
        request_id: Optional[str] = None,
        resume_version_id: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a support ticket (local + Zendesk).
        
        Enriches the ticket with:
        - user_id, subscription_tier, tokens_remaining
        - portal, request_id, resume_version_id
        """
        from services.backend_api.db.models import SupportTicket, User, Subscription

        # Fetch user info for enrichment
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}

        # Get subscription info
        subscription = (
            self.db.query(Subscription)
            .filter(Subscription.user_id == user_id, Subscription.status == "active")
            .first()
        )
        subscription_tier = subscription.plan_id if subscription else "free"

        # Get token balance (if available)
        tokens_remaining = getattr(user, "token_balance", None)

        # Determine priority from category
        priority = CATEGORY_PRIORITY_MAP.get(category, "normal")

        # Build Zendesk ticket payload with enrichment
        user_email = user.email
        user_name = getattr(user, "full_name", None) or user_email.split("@")[0]

        zendesk_tags = [
            "careertrojan",
            f"portal:{portal}",
            f"tier:{subscription_tier}",
            f"category:{category}",
        ]
        if request_id:
            zendesk_tags.append(f"request:{request_id[:20]}")

        zendesk_body = f"""{description}

---
**CareerTrojan Context**
- User ID: {user_id}
- Email: {user_email}
- Subscription: {subscription_tier}
- Tokens: {tokens_remaining or 'N/A'}
- Portal: {portal}
- Request ID: {request_id or 'N/A'}
- Resume Version: {resume_version_id or 'N/A'}
"""

        zendesk_payload = {
            "subject": subject,
            "comment": {"body": zendesk_body},
            "priority": priority,
            "tags": zendesk_tags,
            "requester": {
                "name": user_name,
                "email": user_email,
            },
        }

        # Add group/form if configured
        if ZENDESK_DEFAULT_GROUP_ID:
            zendesk_payload["group_id"] = int(ZENDESK_DEFAULT_GROUP_ID)
        if ZENDESK_DEFAULT_FORM_ID:
            zendesk_payload["ticket_form_id"] = int(ZENDESK_DEFAULT_FORM_ID)

        # Create in Zendesk
        zendesk_result = await zendesk_client.create_ticket(zendesk_payload)
        zendesk_ticket_id = zendesk_result.get("ticket", {}).get("id")
        zendesk_url = None
        if zendesk_ticket_id:
            zendesk_url = f"{ZENDESK_BASE_URL}/agent/tickets/{zendesk_ticket_id}"

        # Create local record
        local_ticket = SupportTicket(
            zendesk_ticket_id=zendesk_ticket_id,
            user_id=user_id,
            subject=subject,
            description=description,
            status="new",
            priority=priority,
            category=category,
            portal=portal,
            request_id=request_id,
            resume_version_id=resume_version_id,
            subscription_tier=subscription_tier,
            tokens_remaining=tokens_remaining,
            zendesk_url=zendesk_url,
            metadata_json=extra_metadata,
        )
        self.db.add(local_ticket)
        self.db.commit()
        self.db.refresh(local_ticket)

        logger.info(
            "Support ticket created: local_id=%s, zendesk_id=%s, user=%s, category=%s",
            local_ticket.id, zendesk_ticket_id, user_id, category,
        )

        # Queue for AI agent processing (auto-classify, draft response, etc.)
        try:
            enqueue_ai_job(
                action="new_ticket",
                ticket_id=local_ticket.id,
                payload={
                    "subject": subject,
                    "description": description,
                    "category": category,
                    "priority": priority,
                    "portal": portal,
                    "user_email": user_email,
                    "subscription_tier": subscription_tier,
                    "tokens_remaining": tokens_remaining,
                    "request_id": request_id,
                    "resume_version_id": resume_version_id,
                    "zendesk_ticket_id": zendesk_ticket_id,
                },
            )
        except Exception:
            logger.warning("Failed to enqueue AI job for ticket %s", local_ticket.id, exc_info=True)

        return {
            "ticket_id": local_ticket.id,
            "zendesk_ticket_id": zendesk_ticket_id,
            "zendesk_url": zendesk_url,
            "status": "new",
            "priority": priority,
        }

    async def get_ticket(self, ticket_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get ticket by local ID (optionally filtered by user for security)."""
        from services.backend_api.db.models import SupportTicket

        query = self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id)
        if user_id:
            query = query.filter(SupportTicket.user_id == user_id)

        ticket = query.first()
        if not ticket:
            return None

        return {
            "ticket_id": ticket.id,
            "zendesk_ticket_id": ticket.zendesk_ticket_id,
            "zendesk_url": ticket.zendesk_url,
            "subject": ticket.subject,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "portal": ticket.portal,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
        }

    async def get_ticket_by_zendesk_id(self, zendesk_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by Zendesk ticket ID."""
        from services.backend_api.db.models import SupportTicket

        ticket = self.db.query(SupportTicket).filter(
            SupportTicket.zendesk_ticket_id == zendesk_id
        ).first()
        if not ticket:
            return None

        return await self.get_ticket(ticket.id)

    async def list_user_tickets(
        self, user_id: int, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List tickets for a user."""
        from services.backend_api.db.models import SupportTicket

        query = self.db.query(SupportTicket).filter(SupportTicket.user_id == user_id)
        if status:
            query = query.filter(SupportTicket.status == status)
        
        tickets = query.order_by(SupportTicket.created_at.desc()).limit(limit).all()

        return [
            {
                "ticket_id": t.id,
                "zendesk_ticket_id": t.zendesk_ticket_id,
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "category": t.category,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ]

    async def update_from_webhook(
        self,
        zendesk_ticket_id: int,
        status: Optional[str] = None,
        last_comment_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Update local ticket from Zendesk webhook."""
        from services.backend_api.db.models import SupportTicket

        ticket = self.db.query(SupportTicket).filter(
            SupportTicket.zendesk_ticket_id == zendesk_ticket_id
        ).first()

        if not ticket:
            logger.warning("Webhook for unknown ticket: zendesk_id=%s", zendesk_ticket_id)
            return {"updated": False, "reason": "Ticket not found"}

        if status:
            ticket.status = status
            if status in ("solved", "closed"):
                ticket.resolved_at = datetime.now(timezone.utc)

        if last_comment_at:
            ticket.last_comment_at = last_comment_at

        ticket.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info(
            "Ticket updated from webhook: local_id=%s, zendesk_id=%s, status=%s",
            ticket.id, zendesk_ticket_id, status,
        )

        return {"updated": True, "ticket_id": ticket.id, "status": ticket.status}


    async def list_all_tickets(
        self,
        status_filter: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List all tickets (admin view) with optional filters."""
        from services.backend_api.db.models import SupportTicket, User

        query = self.db.query(SupportTicket)
        if status_filter:
            query = query.filter(SupportTicket.status == status_filter)
        if category:
            query = query.filter(SupportTicket.category == category)
        if priority:
            query = query.filter(SupportTicket.priority == priority)

        total = query.count()
        tickets = (
            query.order_by(SupportTicket.created_at.desc())
            .offset(offset)
            .limit(min(limit, 200))
            .all()
        )

        items = []
        for t in tickets:
            user = self.db.query(User).filter(User.id == t.user_id).first()
            items.append({
                "ticket_id": t.id,
                "zendesk_ticket_id": t.zendesk_ticket_id,
                "zendesk_url": t.zendesk_url,
                "user_id": t.user_id,
                "user_email": user.email if user else None,
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "category": t.category,
                "portal": t.portal,
                "subscription_tier": t.subscription_tier,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
                "last_comment_at": t.last_comment_at.isoformat() if t.last_comment_at else None,
            })

        return {"tickets": items, "total": total, "limit": limit, "offset": offset}

    async def admin_reply_to_ticket(
        self,
        ticket_id: int,
        comment: str,
        admin_email: str,
        public: bool = True,
        new_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Admin replies to a ticket — pushes comment to Zendesk and updates local record.

        Args:
            ticket_id: Local ticket ID
            comment: Reply text
            admin_email: For audit trail
            public: Whether the reply is visible to the requester
            new_status: Optionally change ticket status (e.g. 'pending', 'solved')
        """
        from services.backend_api.db.models import SupportTicket

        ticket = self.db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
        if not ticket:
            return {"error": "Ticket not found"}

        result = {"ticket_id": ticket.id, "local_updated": True}

        # Push to Zendesk if we have a linked ticket
        if ticket.zendesk_ticket_id:
            zendesk_resp = await zendesk_client.add_comment(
                ticket_id=ticket.zendesk_ticket_id,
                comment=comment,
                public=public,
            )
            if "error" in zendesk_resp:
                result["zendesk_error"] = zendesk_resp["error"]
            else:
                result["zendesk_synced"] = True

            # Optionally update status in Zendesk
            if new_status and "error" not in zendesk_resp:
                await zendesk_client.update_ticket_status(ticket.zendesk_ticket_id, new_status)

        # Update local record
        ticket.updated_at = datetime.now(timezone.utc)
        ticket.last_comment_at = datetime.now(timezone.utc)
        if new_status:
            ticket.status = new_status
            if new_status in ("solved", "closed"):
                ticket.resolved_at = datetime.now(timezone.utc)

        self.db.commit()

        logger.info(
            "Admin reply on ticket %s by %s (public=%s, status=%s)",
            ticket_id, admin_email, public, new_status,
        )

        # Queue for AI agent (log the reply for context, trigger follow-up analysis)
        try:
            enqueue_ai_job(
                action="admin_reply",
                ticket_id=ticket.id,
                payload={
                    "comment": comment,
                    "admin_email": admin_email,
                    "public": public,
                    "new_status": new_status,
                    "zendesk_ticket_id": ticket.zendesk_ticket_id,
                    "subject": ticket.subject,
                    "category": ticket.category,
                    "current_status": ticket.status,
                },
            )
        except Exception:
            logger.warning("Failed to enqueue AI job for reply on ticket %s", ticket_id, exc_info=True)

        result["status"] = ticket.status
        return result


def verify_zendesk_webhook(signature: str, body: bytes, timestamp: str = "") -> bool:
    """
    Verify Zendesk webhook signature using HMAC-SHA256.

    Zendesk signs webhooks by computing:
        HMAC-SHA256(signing_secret, timestamp + body)
    and sending the base64-encoded result in X-Zendesk-Webhook-Signature.
    The timestamp is sent in X-Zendesk-Webhook-Signature-Timestamp.

    See: https://developer.zendesk.com/documentation/webhooks/verifying/
    """
    import hashlib
    import hmac
    from base64 import b64decode, b64encode

    if not ZENDESK_WEBHOOK_SECRET:
        # No secret configured — allow (development mode)
        logger.warning("Zendesk webhook verification skipped — no secret configured")
        return True

    if not signature:
        logger.warning("Zendesk webhook missing signature header")
        return False

    try:
        # Zendesk HMAC: sign(secret, timestamp + body)
        signing_key = ZENDESK_WEBHOOK_SECRET.encode("utf-8")
        sign_payload = timestamp.encode("utf-8") + body
        expected = hmac.new(signing_key, sign_payload, hashlib.sha256).digest()
        expected_b64 = b64encode(expected).decode("utf-8")

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_b64, signature)
    except Exception:
        logger.exception("Zendesk webhook signature verification failed")
        return False
