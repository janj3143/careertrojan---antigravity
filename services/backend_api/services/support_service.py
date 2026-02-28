"""
Support Service — Zendesk Bridge with Ticket Enrichment
========================================================

Handles support ticket creation, status tracking, and Zendesk integration.
Enriches tickets with user context (subscription, tokens, request IDs).

Author: CareerTrojan System
Date: 27 February 2026
"""

import os
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from base64 import b64encode

from sqlalchemy.orm import Session

logger = logging.getLogger("support.service")

# ── Zendesk Configuration ────────────────────────────────────────────────────
ZENDESK_BASE_URL = os.getenv("ZENDESK_BASE_URL", "https://careertrojan.zendesk.com")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL", "")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN", "")
ZENDESK_DEFAULT_GROUP_ID = os.getenv("ZENDESK_DEFAULT_GROUP_ID", "")
ZENDESK_DEFAULT_FORM_ID = os.getenv("ZENDESK_DEFAULT_FORM_ID", "")
ZENDESK_WEBHOOK_SECRET = os.getenv("ZENDESK_WEBHOOK_SECRET", "")

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


def verify_zendesk_webhook(signature: str, body: bytes) -> bool:
    """
    Verify Zendesk webhook signature (if configured).
    
    Zendesk webhooks can use:
    - Shared secret in header
    - HMAC signature
    
    For now, we use a simple shared secret approach.
    """
    if not ZENDESK_WEBHOOK_SECRET:
        # No secret configured — allow (development mode)
        return True

    # Simple shared secret check
    return signature == ZENDESK_WEBHOOK_SECRET
