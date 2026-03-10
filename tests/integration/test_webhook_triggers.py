"""
Integration tests for Zendesk webhook triggers and loop prevention.

Tests the three distinct trigger handlers:
  1️⃣  ticket.created   — Sync to DB + enqueue AI draft
  2️⃣  comment.added    — Update comment timestamp + AI follow-up
  3️⃣  status.changed   — Sync status + handle escalation / closure

Plus loop-prevention logic that skips AI enqueue when the action
was triggered by our own API agent (prevents infinite loops).
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from services.backend_api.db import models
from services.backend_api.db.connection import SessionLocal
from services.backend_api.utils.security import create_access_token, get_password_hash
from services.backend_api.routers.support import (
    _is_self_action,
    _resolve_event_type,
)


# ── Helpers ──────────────────────────────────────────────────────────────

AGENT_EMAIL = "api@careertrojan.com"
WEBHOOK_URL = "/api/webhooks/v1/zendesk"
SUPPORT_WEBHOOK_URL = "/api/support/v1/webhooks/zendesk"


def _get_db():
    """Get a fresh DB session from the app's SessionLocal."""
    db = SessionLocal()
    return db


def _ensure_user(db, email="user@example.com", role="user"):
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


def _seed_ticket(db, user_id, zendesk_ticket_id=999, status="open"):
    """Insert or return existing ticket — idempotent for re-runs."""
    existing = db.query(models.SupportTicket).filter(
        models.SupportTicket.zendesk_ticket_id == zendesk_ticket_id
    ).first()
    if existing:
        existing.status = status
        existing.user_id = user_id
        existing.resolved_at = None
        db.commit()
        db.refresh(existing)
        return existing

    ticket = models.SupportTicket(
        user_id=user_id,
        zendesk_ticket_id=zendesk_ticket_id,
        subject="Test ticket",
        description="Test description",
        status=status,
        priority="normal",
        category="bugs",
        portal="user_portal",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _post_webhook(client, payload: dict, url: str = WEBHOOK_URL):
    """Post a webhook payload (HMAC bypassed by autouse fixture below)."""
    return client.post(
        url,
        content=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "X-Zendesk-Webhook-Signature": "test",
            "X-Zendesk-Webhook-Signature-Timestamp": "0",
        },
    )


@pytest.fixture(autouse=True)
def _bypass_webhook_signature():
    """Bypass HMAC verification for all tests in this module.

    Individual tests that need to assert rejection (e.g.
    test_signature_rejected_when_secret_configured) patch the same
    target with return_value=False, which overrides this fixture.
    """
    with patch(
        "services.backend_api.routers.support.verify_zendesk_webhook",
        return_value=True,
    ):
        yield


# ============================================================================
# UNIT TESTS: _is_self_action
# ============================================================================

class TestIsSelfAction:
    """Loop detection — identifies when a webhook was triggered by our own agent."""

    def test_via_source_from_address_matches(self):
        payload = {"via": {"source": {"from": {"address": AGENT_EMAIL}}}}
        assert _is_self_action(payload, AGENT_EMAIL) is True

    def test_via_source_from_address_case_insensitive(self):
        payload = {"via": {"source": {"from": {"address": "API@CareerTrojan.COM"}}}}
        assert _is_self_action(payload, AGENT_EMAIL) is True

    def test_current_user_email_matches(self):
        payload = {"current_user": {"email": AGENT_EMAIL}}
        assert _is_self_action(payload, AGENT_EMAIL) is True

    def test_comment_author_email_matches(self):
        payload = {"comment": {"author": {"email": AGENT_EMAIL}}}
        assert _is_self_action(payload, AGENT_EMAIL) is True

    def test_via_channel_api_no_human(self):
        payload = {"via": {"channel": "api"}}
        assert _is_self_action(payload, AGENT_EMAIL) is True

    def test_via_channel_api_with_different_human(self):
        payload = {
            "via": {"channel": "api"},
            "current_user": {"email": "human@example.com"},
        }
        assert _is_self_action(payload, AGENT_EMAIL) is False

    def test_external_user_via_web(self):
        payload = {
            "via": {"channel": "web", "source": {"from": {"address": "customer@example.com"}}},
            "current_user": {"email": "customer@example.com"},
        }
        assert _is_self_action(payload, AGENT_EMAIL) is False

    def test_empty_payload(self):
        assert _is_self_action({}, AGENT_EMAIL) is False

    def test_empty_agent_email(self):
        payload = {"via": {"source": {"from": {"address": AGENT_EMAIL}}}}
        assert _is_self_action(payload, "") is False

    def test_none_agent_email(self):
        assert _is_self_action({}, None) is False


# ============================================================================
# UNIT TESTS: _resolve_event_type
# ============================================================================

class TestResolveEventType:
    """Event type resolution from payload."""

    def test_explicit_ticket_created(self):
        assert _resolve_event_type({"event_type": "ticket.created"}) == "ticket.created"

    def test_explicit_ticket_created_underscore(self):
        assert _resolve_event_type({"event_type": "ticket_created"}) == "ticket.created"

    def test_explicit_comment_added(self):
        assert _resolve_event_type({"event_type": "comment.added"}) == "comment.added"

    def test_explicit_public_comment(self):
        assert _resolve_event_type({"event_type": "public_comment"}) == "comment.added"

    def test_explicit_status_changed(self):
        assert _resolve_event_type({"event_type": "status.changed"}) == "status.changed"

    def test_explicit_ticket_updated_maps_to_status_changed(self):
        assert _resolve_event_type({"event_type": "ticket.updated"}) == "status.changed"

    def test_heuristic_comment_present(self):
        payload = {"comment": {"body": "Hello"}}
        assert _resolve_event_type(payload) == "comment.added"

    def test_heuristic_status_change(self):
        payload = {"ticket": {"status": "solved", "previous_status": "open"}}
        assert _resolve_event_type(payload) == "status.changed"

    def test_heuristic_ticket_created(self):
        payload = {"ticket": {"created_at": "2026-03-05T10:00:00Z"}}
        assert _resolve_event_type(payload) == "ticket.created"

    def test_empty_payload_unknown(self):
        assert _resolve_event_type({}) == "unknown"

    def test_type_field_also_works(self):
        assert _resolve_event_type({"type": "new_ticket"}) == "ticket.created"


# ============================================================================
# INTEGRATION TESTS: Trigger 1 — Ticket Created
# ============================================================================

class TestTriggerTicketCreated:
    """Webhook trigger 1️⃣ — ticket.created."""

    def test_ticket_created_syncs_to_db(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            ticket = _seed_ticket(db, user.id, zendesk_ticket_id=1001)
        finally:
            db.close()

        payload = {
            "event_type": "ticket.created",
            "ticket": {
                "id": 1001,
                "subject": "New issue",
                "description": "Something broke",
                "status": "new",
                "priority": "high",
                "tags": ["careertrojan"],
                "requester_id": 12345,
            },
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_123") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["trigger"] == "ticket.created"
        assert data["received"] is True

    def test_ticket_created_enqueues_ai_job(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=1002)
        finally:
            db.close()

        payload = {
            "event_type": "ticket.created",
            "ticket": {"id": 1002, "subject": "Help me", "status": "new"},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_456") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        mock_enqueue.assert_called_once()
        call_kwargs = mock_enqueue.call_args
        assert call_kwargs[1]["action"] == "ticket_created" or call_kwargs[0][0] == "ticket_created"

    def test_ticket_created_self_action_skips_ai(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=1003)
        finally:
            db.close()

        payload = {
            "event_type": "ticket.created",
            "ticket": {"id": 1003, "subject": "Auto-created", "status": "new"},
            "via": {"channel": "api"},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_self_action"] is True
        mock_enqueue.assert_not_called()


# ============================================================================
# INTEGRATION TESTS: Trigger 2 — Comment Added
# ============================================================================

class TestTriggerCommentAdded:
    """Webhook trigger 2️⃣ — comment.added."""

    def test_public_comment_updates_db(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=2001)
        finally:
            db.close()

        payload = {
            "event_type": "comment.added",
            "ticket": {"id": 2001, "status": "open"},
            "comment": {
                "body": "Customer reply",
                "public": True,
                "author_id": 99999,
                "created_at": "2026-03-05T12:00:00Z",
                "author": {"email": "customer@example.com"},
            },
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_c1"):
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["trigger"] == "comment.added"
        assert data["comment_public"] is True

    def test_public_comment_enqueues_ai_followup(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=2002)
        finally:
            db.close()

        payload = {
            "event_type": "comment.added",
            "ticket": {"id": 2002, "status": "open"},
            "comment": {
                "body": "I still need help",
                "public": True,
                "author_id": 88888,
                "author": {"email": "customer@example.com"},
            },
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_c2") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args
        assert args[1]["action"] == "comment_added" or args[0][0] == "comment_added"

    def test_self_comment_skips_ai(self, test_client):
        """Our own agent's comment → no AI enqueue (loop prevention)."""
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=2003)
        finally:
            db.close()

        payload = {
            "event_type": "comment.added",
            "ticket": {"id": 2003, "status": "open"},
            "comment": {
                "body": "AI draft posted",
                "public": False,
                "author": {"email": AGENT_EMAIL},
            },
            "current_user": {"email": AGENT_EMAIL},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_self_action"] is True
        mock_enqueue.assert_not_called()

    def test_internal_note_from_external_skips_ai(self, test_client):
        """Internal note (public=false) from non-agent → still no AI enqueue."""
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=2004)
        finally:
            db.close()

        payload = {
            "event_type": "comment.added",
            "ticket": {"id": 2004, "status": "open"},
            "comment": {
                "body": "Internal discussion",
                "public": False,
                "author": {"email": "admin@careertrojan.com"},
            },
            "current_user": {"email": "admin@careertrojan.com"},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        data = resp.json()
        # Not public → AI should not enqueue even if not self
        mock_enqueue.assert_not_called()

    def test_heuristic_detects_comment(self, test_client):
        """No explicit event_type — heuristic detects comment from payload."""
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=2005)
        finally:
            db.close()

        payload = {
            "ticket": {"id": 2005, "status": "open"},
            "comment": {"body": "Follow up", "public": True},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_h"):
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        assert resp.json()["event_type"] == "comment.added"


# ============================================================================
# INTEGRATION TESTS: Trigger 3 — Status Changed
# ============================================================================

class TestTriggerStatusChanged:
    """Webhook trigger 3️⃣ — status.changed."""

    def test_status_change_syncs_to_db(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=3001, status="open")
        finally:
            db.close()

        payload = {
            "event_type": "status.changed",
            "ticket": {
                "id": 3001,
                "status": "pending",
                "previous_status": "open",
            },
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_s1"):
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        data = resp.json()
        assert data["trigger"] == "status.changed"
        assert data["new_status"] == "pending"
        assert data["previous_status"] == "open"

    def test_solved_sets_resolved_at(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=3002, status="open")
        finally:
            db.close()

        payload = {
            "event_type": "status.changed",
            "ticket": {
                "id": 3002,
                "status": "solved",
                "previous_status": "open",
            },
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_s2"):
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200

        # Verify resolved_at was set in DB
        db = _get_db()
        try:
            db_ticket = db.query(models.SupportTicket).filter(
                models.SupportTicket.zendesk_ticket_id == 3002
            ).first()
            assert db_ticket.status == "solved"
            assert db_ticket.resolved_at is not None
        finally:
            db.close()

    def test_self_status_change_skips_ai(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=3003, status="new")
        finally:
            db.close()

        payload = {
            "event_type": "status.changed",
            "ticket": {"id": 3003, "status": "open", "previous_status": "new"},
            "via": {"channel": "api"},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job") as mock_enqueue:
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        assert resp.json()["is_self_action"] is True
        mock_enqueue.assert_not_called()

    def test_heuristic_detects_status_change(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=3004, status="pending")
        finally:
            db.close()

        payload = {
            "ticket": {
                "id": 3004,
                "status": "solved",
                "previous_status": "pending",
            },
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="job_h2"):
            resp = _post_webhook(test_client, payload)

        assert resp.status_code == 200
        assert resp.json()["event_type"] == "status.changed"


# ============================================================================
# INTEGRATION TESTS: Webhook Security + Edge Cases
# ============================================================================

class TestWebhookSecurity:
    """Signature verification, malformed payloads, missing data."""

    def test_missing_ticket_id_returns_not_processed(self, test_client):
        payload = {"event_type": "ticket.created", "ticket": {}}
        resp = _post_webhook(test_client, payload)
        assert resp.status_code == 200
        assert resp.json()["processed"] is False

    def test_invalid_json_returns_400(self, test_client):
        resp = test_client.post(
            WEBHOOK_URL,
            content="not-json",
            headers={
                "Content-Type": "application/json",
                "X-Zendesk-Webhook-Signature": "test",
                "X-Zendesk-Webhook-Signature-Timestamp": "0",
            },
        )
        assert resp.status_code == 400

    def test_unknown_event_still_records(self, test_client):
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=9001)
        finally:
            db.close()

        payload = {
            "event_type": "ticket.deleted",
            "ticket": {"id": 9001},
        }

        resp = _post_webhook(test_client, payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == "ticket.deleted"

    def test_alias_url_delegates_correctly(self, test_client):
        """POST /api/webhooks/v1/zendesk delegates to same handler."""
        db = _get_db()
        try:
            user = _ensure_user(db)
            _seed_ticket(db, user.id, zendesk_ticket_id=9002)
        finally:
            db.close()

        payload = {
            "event_type": "ticket.created",
            "ticket": {"id": 9002, "status": "new"},
        }

        with patch("services.backend_api.services.support_service.enqueue_ai_job", return_value="j"):
            resp = _post_webhook(test_client, payload, url=WEBHOOK_URL)
            resp2 = _post_webhook(test_client, payload, url=SUPPORT_WEBHOOK_URL)

        assert resp.status_code == 200
        assert resp2.status_code == 200
        # Both should produce the same trigger
        assert resp.json()["trigger"] == resp2.json()["trigger"] == "ticket.created"

    def test_signature_rejected_when_secret_configured(self, test_client):
        """When ZENDESK_WEBHOOK_SECRET is set, bad signature → 401."""
        payload = json.dumps({"ticket": {"id": 9999}})

        with patch("services.backend_api.routers.support.verify_zendesk_webhook", return_value=False):
            resp = test_client.post(
                WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Zendesk-Webhook-Signature": "bad-sig",
                    "X-Zendesk-Webhook-Signature-Timestamp": "123",
                },
            )

        assert resp.status_code == 401
