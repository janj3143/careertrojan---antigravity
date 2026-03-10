"""
Tests for Webhook Router — CareerTrojan
========================================

Tests cover:
  - Health endpoint availability
  - Braintree webhook signature verification stub
  - Stripe webhook signature verification stub
  - Zendesk HMAC verification stub
  - Idempotent event logging (duplicate rejection)
  - Subscription status updates from webhook events
"""

import json
import hmac
import hashlib
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Fresh TestClient for webhook tests."""
    from services.backend_api.main import app
    _clear_rate_limiter(app)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def db_engine():
    """In-memory SQLite engine + tables for webhook DB operations.
    
    Uses StaticPool so all connections share the same in-memory database.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from services.backend_api.db.models import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Session from the in-memory engine."""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client_with_db(db_engine):
    """TestClient that overrides get_db so webhook handlers use in-memory SQLite."""
    from sqlalchemy.orm import sessionmaker
    from services.backend_api.main import app
    from services.backend_api.db.connection import get_db

    TestSession = sessionmaker(bind=db_engine)

    def _override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    _clear_rate_limiter(app)
    c = TestClient(app, raise_server_exceptions=False)
    yield c
    app.dependency_overrides.pop(get_db, None)


def _clear_rate_limiter(app):
    """Walk the ASGI app stack to find and reset the rate limiter."""
    obj = getattr(app, "middleware_stack", app)
    for _ in range(20):
        if hasattr(obj, "_hits"):
            obj._hits.clear()
            return
        obj = getattr(obj, "app", None)
        if obj is None:
            break


# ============================================================================
# HEALTH
# ============================================================================

class TestWebhookHealth:
    def test_health_endpoint(self, client):
        """Webhook health endpoint should return 200 with service info."""
        res = client.get("/api/webhooks/v1/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "webhooks"
        assert "braintree_available" in data
        assert "stripe_available" in data
        assert "zendesk_available" in data


# ============================================================================
# BRAINTREE WEBHOOK
# ============================================================================

class TestBraintreeWebhook:
    def test_missing_signature_returns_400(self, client):
        """Braintree webhook without bt_signature should fail with 400."""
        res = client.post(
            "/api/webhooks/v1/braintree",
            data={"bt_payload": "some-payload"},
        )
        assert res.status_code == 400

    def test_missing_payload_returns_400(self, client):
        """Braintree webhook without bt_payload should fail with 400."""
        res = client.post(
            "/api/webhooks/v1/braintree",
            data={"bt_signature": "some-sig"},
        )
        assert res.status_code == 400

    @patch("services.backend_api.routers.webhooks.braintree_service")
    @patch("services.backend_api.routers.webhooks.BRAINTREE_AVAILABLE", True)
    def test_invalid_signature_returns_401(self, mock_bt, client):
        """Braintree webhook with invalid signature should return 401."""
        mock_gw = MagicMock()
        mock_gw.webhook_notification.parse.side_effect = Exception("Invalid signature")
        mock_bt.gateway.return_value = mock_gw

        res = client.post(
            "/api/webhooks/v1/braintree",
            data={"bt_signature": "bad-sig", "bt_payload": "bad-payload"},
        )
        assert res.status_code == 401

    @patch("services.backend_api.routers.webhooks.braintree_service")
    @patch("services.backend_api.routers.webhooks.BRAINTREE_AVAILABLE", True)
    def test_valid_subscription_charged(self, mock_bt, client_with_db):
        """Successful subscription_charged_successfully should return 200."""
        mock_notification = MagicMock()
        mock_notification.kind = "subscription_charged_successfully"
        mock_notification.timestamp = datetime.now(timezone.utc)
        mock_notification.subscription = MagicMock()
        mock_notification.subscription.id = "sub_test_123"
        mock_notification.subscription.status = "Active"
        mock_notification.subscription.price = "15.99"
        mock_notification.subscription.plan_id = "monthly"
        mock_notification.subscription.transactions = []

        mock_gw = MagicMock()
        mock_gw.webhook_notification.parse.return_value = mock_notification
        mock_bt.gateway.return_value = mock_gw
        mock_bt.is_configured.return_value = True

        res = client_with_db.post(
            "/api/webhooks/v1/braintree",
            data={"bt_signature": "valid-sig", "bt_payload": "valid-payload"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["event"] == "subscription_charged_successfully"

    @patch("services.backend_api.routers.webhooks.braintree_service")
    @patch("services.backend_api.routers.webhooks.BRAINTREE_AVAILABLE", True)
    def test_dispute_won_is_handled(self, mock_bt, client_with_db):
        """dispute_won event should be handled explicitly (not fall through)."""
        mock_notification = MagicMock()
        mock_notification.kind = "dispute_won"
        mock_notification.timestamp = datetime.now(timezone.utc)
        mock_notification.subscription = None
        mock_notification.dispute = MagicMock()
        mock_notification.dispute.id = "dp_test_1"
        mock_notification.dispute.reason = "fraud"
        mock_notification.dispute.amount = "15.99"
        mock_notification.dispute.transaction = MagicMock()
        mock_notification.dispute.transaction.id = "bt_tx_original_1"

        mock_gw = MagicMock()
        mock_gw.webhook_notification.parse.return_value = mock_notification
        mock_bt.gateway.return_value = mock_gw
        mock_bt.is_configured.return_value = True

        res = client_with_db.post(
            "/api/webhooks/v1/braintree",
            data={"bt_signature": "valid-sig", "bt_payload": "valid-payload"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["event"] == "dispute_won"

    @pytest.mark.parametrize("dispute_event", ["dispute_opened", "dispute_lost"])
    @patch("services.backend_api.routers.webhooks.braintree_service")
    @patch("services.backend_api.routers.webhooks.BRAINTREE_AVAILABLE", True)
    def test_dispute_events_are_handled(self, mock_bt, client_with_db, dispute_event):
        """dispute_opened/dispute_lost should be handled explicitly (not fall through)."""
        mock_notification = MagicMock()
        mock_notification.kind = dispute_event
        mock_notification.timestamp = datetime.now(timezone.utc)
        mock_notification.subscription = None
        mock_notification.dispute = MagicMock()
        mock_notification.dispute.id = "dp_test_2"
        mock_notification.dispute.reason = "chargeback"
        mock_notification.dispute.amount = "15.99"
        mock_notification.dispute.transaction = MagicMock()
        mock_notification.dispute.transaction.id = "bt_tx_original_2"

        mock_gw = MagicMock()
        mock_gw.webhook_notification.parse.return_value = mock_notification
        mock_bt.gateway.return_value = mock_gw
        mock_bt.is_configured.return_value = True

        res = client_with_db.post(
            "/api/webhooks/v1/braintree",
            data={"bt_signature": "valid-sig", "bt_payload": "valid-payload"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["event"] == dispute_event


# ============================================================================
# STRIPE WEBHOOK
# ============================================================================

class TestStripeWebhook:
    def test_missing_signature_returns_401(self, client):
        """Stripe webhook without signature header → SignatureVerificationError → 401."""
        res = client.post(
            "/api/webhooks/v1/stripe",
            content=json.dumps({"type": "test"}),
            headers={"Content-Type": "application/json"},
        )
        # Without signature, construct_event raises SignatureVerificationError → 401
        assert res.status_code in (401, 503)  # 503 if Stripe not configured in env

    @patch("services.backend_api.routers.webhooks.stripe")
    @patch("services.backend_api.routers.webhooks.STRIPE_AVAILABLE", True)
    @patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": "whsec_test"})
    def test_invalid_signature_returns_401(self, mock_stripe, client):
        """Stripe webhook with bad signature should return 401."""
        mock_stripe.error = type("error", (), {
            "SignatureVerificationError": type("SignatureVerificationError", (Exception,), {})
        })()
        mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError("Bad sig")

        res = client.post(
            "/api/webhooks/v1/stripe",
            content=b'{"type":"test"}',
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=badsig",
            },
        )
        assert res.status_code == 401

    @patch("services.backend_api.routers.webhooks.stripe")
    @patch("services.backend_api.routers.webhooks.STRIPE_AVAILABLE", True)
    @patch.dict("os.environ", {"STRIPE_WEBHOOK_SECRET": "whsec_test"})
    def test_valid_checkout_completed(self, mock_stripe, client_with_db):
        """Valid checkout.session.completed event should return 200."""
        event = {
            "id": "evt_test_checkout",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test",
                    "subscription": "sub_stripe_test",
                    "metadata": {},
                }
            },
        }
        mock_stripe.error = type("error", (), {
            "SignatureVerificationError": type("SignatureVerificationError", (Exception,), {})
        })()
        mock_stripe.Webhook.construct_event.return_value = event

        res = client_with_db.post(
            "/api/webhooks/v1/stripe",
            content=json.dumps(event).encode(),
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=goodsig",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["event"] == "checkout.session.completed"


# ============================================================================
# ZENDESK WEBHOOK
# ============================================================================

class TestZendeskWebhook:
    @patch.dict("os.environ", {"ZENDESK_WEBHOOK_SECRET": "", "ZENDESK_SHARED_SECRET": ""})
    def test_zendesk_no_secret_passes_verification(self, client):
        """When no Zendesk secret is set, signature verification passes."""
        # The handler will still try DB ops which may error — we only check
        # that we don't get a 401 (i.e. verification is skipped).
        res = client.post(
            "/api/webhooks/v1/zendesk",
            json={"ticket": {"id": 1, "status": "open"}},
        )
        # Should NOT be 401 — verification is skipped when no secret is configured
        assert res.status_code != 401

    @patch.dict("os.environ", {"ZENDESK_WEBHOOK_SECRET": "zd_secret_123", "ZENDESK_SHARED_SECRET": ""})
    def test_zendesk_bad_signature_returns_401(self, client):
        """Zendesk webhook with wrong HMAC should return 401."""
        res = client.post(
            "/api/webhooks/v1/zendesk",
            content=b'{"ticket":{"id":1}}',
            headers={
                "Content-Type": "application/json",
                "X-Zendesk-Webhook-Signature": "badsig",
            },
        )
        assert res.status_code == 401


# ============================================================================
# DB HELPERS — WebhookEvent idempotency
# ============================================================================

class TestWebhookEventIdempotency:
    def test_duplicate_event_id_rejected(self, db_session):
        """Inserting same event_id twice should be blocked by unique constraint."""
        from services.backend_api.db.models import WebhookEvent

        evt1 = WebhookEvent(
            event_id="evt_dup_test",
            source="stripe",
            event_type="invoice.payment_succeeded",
            status="processed",
        )
        db_session.add(evt1)
        db_session.commit()

        evt2 = WebhookEvent(
            event_id="evt_dup_test",
            source="stripe",
            event_type="invoice.payment_succeeded",
            status="received",
        )
        db_session.add(evt2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_different_event_ids_accepted(self, db_session):
        """Different event IDs should both be insertable."""
        from services.backend_api.db.models import WebhookEvent

        for i in range(3):
            evt = WebhookEvent(
                event_id=f"evt_unique_{i}",
                source="braintree",
                event_type="subscription_charged_successfully",
                status="processed",
            )
            db_session.add(evt)
        db_session.commit()

        count = db_session.query(WebhookEvent).filter(
            WebhookEvent.event_id.like("evt_unique_%")
        ).count()
        assert count == 3


# ============================================================================
# DB HELPERS — Subscription model
# ============================================================================

class TestSubscriptionModel:
    def test_create_subscription_record(self, db_session):
        """Should be able to create and query a Subscription."""
        from services.backend_api.db.models import Subscription

        sub = Subscription(
            user_id=999,
            plan_id="monthly",
            gateway="braintree",
            status="active",
            price=15.99,
            currency="USD",
            interval="month",
        )
        db_session.add(sub)
        db_session.commit()

        fetched = db_session.query(Subscription).filter(
            Subscription.user_id == 999
        ).first()
        assert fetched is not None
        assert fetched.plan_id == "monthly"
        assert fetched.price == 15.99

    def test_cancel_subscription(self, db_session):
        """Cancelling should update status and cancelled_at."""
        from services.backend_api.db.models import Subscription

        sub = Subscription(
            user_id=998,
            plan_id="annual",
            gateway="braintree",
            status="active",
            price=149.99,
        )
        db_session.add(sub)
        db_session.commit()

        sub.status = "cancelled"
        sub.cancelled_at = datetime.now(timezone.utc)
        db_session.commit()

        fetched = db_session.query(Subscription).filter(
            Subscription.user_id == 998
        ).first()
        assert fetched.status == "cancelled"
        assert fetched.cancelled_at is not None


class TestPaymentTransactionModel:
    def test_create_transaction(self, db_session):
        """Should be able to create a PaymentTransaction."""
        from services.backend_api.db.models import PaymentTransaction

        tx = PaymentTransaction(
            user_id=999,
            gateway="braintree",
            gateway_transaction_id="bt_tx_test123",
            transaction_type="charge",
            status="completed",
            amount=15.99,
            currency="USD",
            plan_id="monthly",
            description="Test charge",
        )
        db_session.add(tx)
        db_session.commit()

        fetched = db_session.query(PaymentTransaction).filter(
            PaymentTransaction.gateway_transaction_id == "bt_tx_test123"
        ).first()
        assert fetched is not None
        assert fetched.amount == 15.99
        assert fetched.status == "completed"
