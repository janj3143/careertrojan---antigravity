"""
Integration tests for admin ticket management endpoints:
  GET  /api/support/v1/tickets/admin/all
  GET  /api/support/v1/tickets/admin/{ticket_id}
  POST /api/support/v1/tickets/{ticket_id}/reply
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from services.backend_api.db import models
from services.backend_api.utils.security import create_access_token, get_password_hash


# ── helpers ──────────────────────────────────────────────────────────────

def _admin_headers():
    token = create_access_token(data={"sub": "admin@careertrojan.com", "role": "admin", "user_id": 1})
    return {"Authorization": f"Bearer {token}"}


def _user_headers():
    token = create_access_token(data={"sub": "regular@careertrojan.com", "role": "user", "user_id": 100})
    return {"Authorization": f"Bearer {token}"}


def _seed_ticket(db, *, user_id: int, subject: str = "Test ticket",
                 status: str = "open", priority: str = "normal",
                 category: str = "bugs") -> models.SupportTicket:
    """Insert a SupportTicket row and return it."""
    ticket = models.SupportTicket(
        user_id=user_id,
        subject=subject,
        description=f"Description for {subject}",
        status=status,
        priority=priority,
        category=category,
        portal="user_portal",
        zendesk_ticket_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _ensure_user(db, email: str, role: str = "user", user_id: int = None):
    """Ensure a user row exists (needed for FK constraints)."""
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        full_name=f"Test {role.title()}",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── GET /tickets/admin/all ───────────────────────────────────────────────

class TestAdminListAllTickets:

    def test_returns_200_for_admin(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/all",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "tickets" in data
        assert "total" in data

    def test_returns_403_for_non_admin(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/all",
            headers=_user_headers(),
        )
        assert resp.status_code == 403

    def test_returns_401_without_auth(self, test_client):
        resp = test_client.get("/api/support/v1/tickets/admin/all")
        assert resp.status_code in (401, 403)

    def test_filter_by_status(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/all?status_filter=open",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        for ticket in data["tickets"]:
            assert ticket["status"] == "open"

    def test_filter_by_category(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/all?category=billing",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200

    def test_pagination(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/all?limit=2&offset=0",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 2
        assert data["offset"] == 0


# ── GET /tickets/admin/{ticket_id} ──────────────────────────────────────

class TestAdminGetTicket:

    def test_returns_ticket_for_admin(self, test_client):
        """Admin can fetch any ticket (even one belonging to a different user)."""
        from services.backend_api.db.connection import SessionLocal
        db = SessionLocal()
        try:
            user = _ensure_user(db, "ticketowner@careertrojan.com")
            ticket = _seed_ticket(db, user_id=user.id, subject="Admin can see this")
            ticket_id = ticket.id
        finally:
            db.close()

        resp = test_client.get(
            f"/api/support/v1/tickets/admin/{ticket_id}",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticket_id"] == ticket_id

    def test_returns_404_for_nonexistent_ticket(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/999999",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_returns_403_for_non_admin(self, test_client):
        resp = test_client.get(
            "/api/support/v1/tickets/admin/1",
            headers=_user_headers(),
        )
        assert resp.status_code == 403


# ── POST /tickets/{ticket_id}/reply ──────────────────────────────────────

class TestAdminReplyToTicket:

    def test_reply_success(self, test_client):
        """Admin can reply to a ticket; Zendesk call is mocked."""
        from services.backend_api.db.connection import SessionLocal
        db = SessionLocal()
        try:
            user = _ensure_user(db, "replyowner@careertrojan.com")
            ticket = _seed_ticket(db, user_id=user.id, subject="Reply test ticket")
            ticket_id = ticket.id
        finally:
            db.close()

        # Mock the Zendesk add_comment call so it doesn't hit a real server
        with patch(
            "services.backend_api.services.support_service.zendesk_client.add_comment",
            new_callable=AsyncMock,
            return_value={"ticket": {"id": 12345}},
        ):
            resp = test_client.post(
                f"/api/support/v1/tickets/{ticket_id}/reply",
                json={"comment": "Admin reply content", "public": True},
                headers=_admin_headers(),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("local_updated") is True
        assert "ticket_id" in data

    def test_reply_403_for_non_admin(self, test_client):
        resp = test_client.post(
            "/api/support/v1/tickets/1/reply",
            json={"comment": "Non-admin reply attempt"},
            headers=_user_headers(),
        )
        assert resp.status_code == 403

    def test_reply_invalid_status(self, test_client):
        resp = test_client.post(
            "/api/support/v1/tickets/1/reply",
            json={"comment": "Reply", "new_status": "invalid_status"},
            headers=_admin_headers(),
        )
        assert resp.status_code == 400

    def test_reply_ticket_not_found(self, test_client):
        """Reply to a non-existent ticket → 404."""
        with patch(
            "services.backend_api.services.support_service.zendesk_client.add_comment",
            new_callable=AsyncMock,
            return_value={"ticket": {"id": 12345}},
        ):
            resp = test_client.post(
                "/api/support/v1/tickets/999999/reply",
                json={"comment": "This ticket does not exist"},
                headers=_admin_headers(),
            )
        assert resp.status_code == 404

    def test_reply_with_status_change(self, test_client):
        """Admin can reply and change ticket status in one call."""
        from services.backend_api.db.connection import SessionLocal
        db = SessionLocal()
        try:
            user = _ensure_user(db, "statuschange@careertrojan.com")
            ticket = _seed_ticket(db, user_id=user.id, subject="Status change ticket", status="open")
            ticket_id = ticket.id
        finally:
            db.close()

        with patch(
            "services.backend_api.services.support_service.zendesk_client.add_comment",
            new_callable=AsyncMock,
            return_value={"ticket": {"id": 12345}},
        ):
            resp = test_client.post(
                f"/api/support/v1/tickets/{ticket_id}/reply",
                json={
                    "comment": "Closing this ticket.",
                    "public": True,
                    "new_status": "solved",
                },
                headers=_admin_headers(),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("local_updated") is True
        assert data.get("status") == "solved"
