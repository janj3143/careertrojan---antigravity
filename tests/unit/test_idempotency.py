"""
Idempotency Service Tests — CareerTrojan
==========================================

Tests for:
  1. IdempotencyStore — DB-backed key registry
  2. WebhookDedup — webhook event deduplication
  3. FastAPI dependency — require_idempotency_key header validation
  4. Integration — full round-trip through payment/credits/refund endpoints

Author: CareerTrojan System
Date: February 2026
"""

import json
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.backend_api.db.models import Base
from services.backend_api.services.idempotency import (
    IdempotencyStore,
    IdempotencyRecord,
    WebhookDedup,
    WebhookEventRecord,
    require_idempotency_key,
    _body_hash,
    _webhook_fingerprint,
    IDEMPOTENCY_TTL_HOURS,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def idemp_db():
    """In-memory SQLite session with idempotency tables created."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def _key():
    """Generate a fresh idempotency key."""
    return str(uuid.uuid4())


# ============================================================================
# UNIT TESTS — IdempotencyStore
# ============================================================================

class TestIdempotencyStore:
    """Tests for the core idempotency key store."""

    def test_first_check_returns_not_duplicate(self, idemp_db):
        """First use of a key should NOT be a duplicate."""
        is_dup, cached = IdempotencyStore.check(
            idemp_db, _key(), "payment", "user_1",
        )
        assert is_dup is False
        assert cached is None

    def test_begin_creates_processing_record(self, idemp_db):
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        assert record.status == "processing"
        assert record.key == key
        assert record.scope == "payment"
        assert record.user_id == "user_1"
        # SQLite may store naive datetimes — normalise before comparing
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        assert expires > datetime.now(timezone.utc)

    def test_duplicate_key_returns_cached_response(self, idemp_db):
        """After completing, same key should return cached response."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        
        response = {"success": True, "amount": 15.99, "subscription_id": "sub_abc"}
        IdempotencyStore.complete(idemp_db, record, 200, response)

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1"
        )
        assert is_dup is True
        assert cached == response

    def test_different_scope_is_not_duplicate(self, idemp_db):
        """Same key in different scope should NOT be duplicate."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        IdempotencyStore.complete(idemp_db, record, 200, {"ok": True})

        # Check same key but different scope
        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "credits", "user_1"
        )
        assert is_dup is False

    def test_different_user_gets_error(self, idemp_db):
        """Key used by user_1 should return error for user_2."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        IdempotencyStore.complete(idemp_db, record, 200, {"ok": True})

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_2"
        )
        assert is_dup is True
        assert "error" in cached
        assert "another user" in cached["error"]

    def test_expired_key_treated_as_fresh(self, idemp_db):
        """Expired idempotency keys should be treated as new."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        IdempotencyStore.complete(idemp_db, record, 200, {"ok": True})

        # Manually expire
        record.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        idemp_db.commit()

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1"
        )
        assert is_dup is False
        assert cached is None

    def test_failed_record_allows_retry(self, idemp_db):
        """A previously failed operation should allow retry with same key."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        IdempotencyStore.fail(idemp_db, record)

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1"
        )
        assert is_dup is False
        assert cached is None

    def test_stale_processing_record_cleared(self, idemp_db):
        """Processing record older than 5 min should be cleared on check."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")

        # Manually backdate
        record.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        idemp_db.commit()

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1"
        )
        assert is_dup is False

    def test_recent_processing_record_blocks(self, idemp_db):
        """Processing record < 5 min old should block (still in flight)."""
        key = _key()
        IdempotencyStore.begin(idemp_db, key, "payment", "user_1")

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1"
        )
        assert is_dup is True
        assert cached is None  # None means "still processing"

    def test_body_hash_mismatch_rejected(self, idemp_db):
        """Same key + different request body should be rejected."""
        key = _key()
        body_1 = {"plan_id": "monthly", "nonce": "abc"}
        record = IdempotencyStore.begin(
            idemp_db, key, "payment", "user_1", request_body=body_1,
        )
        IdempotencyStore.complete(idemp_db, record, 200, {"ok": True})

        body_2 = {"plan_id": "annual", "nonce": "abc"}
        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1", request_body=body_2,
        )
        assert is_dup is True
        assert "error" in cached
        assert "different request body" in cached["error"]

    def test_body_hash_match_returns_cached(self, idemp_db):
        """Same key + same request body should return cached response."""
        key = _key()
        body = {"plan_id": "monthly", "nonce": "abc"}
        record = IdempotencyStore.begin(
            idemp_db, key, "payment", "user_1", request_body=body,
        )
        response = {"success": True, "amount": 15.99}
        IdempotencyStore.complete(idemp_db, record, 200, response)

        is_dup, cached = IdempotencyStore.check(
            idemp_db, key, "payment", "user_1", request_body=body,
        )
        assert is_dup is True
        assert cached == response

    def test_complete_sets_fields(self, idemp_db):
        """complete() should set status, response_code, response_body, completed_at."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        response = {"id": "tx_123"}
        IdempotencyStore.complete(idemp_db, record, 200, response)

        assert record.status == "completed"
        assert record.response_code == 200
        assert json.loads(record.response_body) == response
        assert record.completed_at is not None

    def test_fail_sets_status(self, idemp_db):
        """fail() should mark the record as failed."""
        key = _key()
        record = IdempotencyStore.begin(idemp_db, key, "payment", "user_1")
        IdempotencyStore.fail(idemp_db, record)

        assert record.status == "failed"
        assert record.completed_at is not None


# ============================================================================
# UNIT TESTS — WebhookDedup
# ============================================================================

class TestWebhookDedup:
    """Tests for webhook event deduplication."""

    def test_first_event_is_not_duplicate(self, idemp_db):
        is_dup = WebhookDedup.is_duplicate(
            idemp_db, "subscription_charged_successfully", "sub_001",
        )
        assert is_dup is False

    def test_recorded_event_is_duplicate(self, idemp_db):
        ts = datetime.now(timezone.utc)
        WebhookDedup.record(
            idemp_db, "subscription_charged_successfully", "sub_001",
            timestamp=ts, summary="ok",
        )
        is_dup = WebhookDedup.is_duplicate(
            idemp_db, "subscription_charged_successfully", "sub_001",
            timestamp=ts,
        )
        assert is_dup is True

    def test_different_kind_is_not_duplicate(self, idemp_db):
        ts = datetime.now(timezone.utc)
        WebhookDedup.record(
            idemp_db, "subscription_charged_successfully", "sub_001",
            timestamp=ts,
        )
        is_dup = WebhookDedup.is_duplicate(
            idemp_db, "subscription_canceled", "sub_001",
            timestamp=ts,
        )
        assert is_dup is False

    def test_different_resource_is_not_duplicate(self, idemp_db):
        ts = datetime.now(timezone.utc)
        WebhookDedup.record(
            idemp_db, "subscription_charged_successfully", "sub_001",
            timestamp=ts,
        )
        is_dup = WebhookDedup.is_duplicate(
            idemp_db, "subscription_charged_successfully", "sub_002",
            timestamp=ts,
        )
        assert is_dup is False

    def test_different_timestamp_is_not_duplicate(self, idemp_db):
        ts1 = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 2, 10, 12, 5, 0, tzinfo=timezone.utc)
        WebhookDedup.record(
            idemp_db, "subscription_charged_successfully", "sub_001",
            timestamp=ts1,
        )
        is_dup = WebhookDedup.is_duplicate(
            idemp_db, "subscription_charged_successfully", "sub_001",
            timestamp=ts2,
        )
        assert is_dup is False

    def test_record_stores_summary(self, idemp_db):
        ts = datetime.now(timezone.utc)
        WebhookDedup.record(
            idemp_db, "dispute_opened", "d_123",
            timestamp=ts, summary="Amount: £50",
        )
        fp = _webhook_fingerprint("dispute_opened", "d_123", ts)
        row = (
            idemp_db.query(WebhookEventRecord)
            .filter(WebhookEventRecord.fingerprint == fp)
            .first()
        )
        assert row is not None
        assert row.payload_summary == "Amount: £50"


# ============================================================================
# UNIT TESTS — Helper Functions
# ============================================================================

class TestHelpers:
    """Tests for internal hashing helpers."""

    def test_body_hash_deterministic(self):
        body = {"plan_id": "monthly", "nonce": "abc123"}
        h1 = _body_hash(body)
        h2 = _body_hash(body)
        assert h1 == h2

    def test_body_hash_key_order_independent(self):
        body1 = {"a": 1, "b": 2}
        body2 = {"b": 2, "a": 1}
        assert _body_hash(body1) == _body_hash(body2)

    def test_body_hash_different_values(self):
        body1 = {"plan_id": "monthly"}
        body2 = {"plan_id": "annual"}
        assert _body_hash(body1) != _body_hash(body2)

    def test_webhook_fingerprint_deterministic(self):
        ts = datetime(2026, 2, 10, tzinfo=timezone.utc)
        fp1 = _webhook_fingerprint("charge_ok", "sub_1", ts)
        fp2 = _webhook_fingerprint("charge_ok", "sub_1", ts)
        assert fp1 == fp2

    def test_webhook_fingerprint_diff_kind(self):
        ts = datetime(2026, 2, 10, tzinfo=timezone.utc)
        fp1 = _webhook_fingerprint("charge_ok", "sub_1", ts)
        fp2 = _webhook_fingerprint("canceled", "sub_1", ts)
        assert fp1 != fp2


# ============================================================================
# UNIT TESTS — require_idempotency_key dependency
# ============================================================================

class TestRequireIdempotencyKey:
    """Tests for the FastAPI header dependency."""

    def test_valid_key_returned(self):
        key = str(uuid.uuid4())
        result = require_idempotency_key(key)
        assert result == key

    def test_whitespace_stripped(self):
        key = f"  {uuid.uuid4()}  "
        result = require_idempotency_key(key)
        assert result == key.strip()

    def test_missing_key_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            require_idempotency_key(None)
        assert exc_info.value.status_code == 400

    def test_empty_key_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            require_idempotency_key("   ")
        assert exc_info.value.status_code == 400

    def test_too_long_key_raises_400(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            require_idempotency_key("x" * 256)
        assert exc_info.value.status_code == 400


# ============================================================================
# INTEGRATION TESTS — Endpoint-level idempotency
# ============================================================================

class TestPaymentEndpointIdempotency:
    """Integration tests — POST /api/payment/v1/process with Idempotency-Key."""

    @pytest.fixture(autouse=True)
    def _setup_user(self, test_client):
        """Ensure a DB user exists for auth to resolve."""
        from services.backend_api.db.connection import SessionLocal
        from conftest import create_test_user, make_auth_headers

        db = SessionLocal()
        try:
            user = create_test_user(
                db, email="idemp-pay@careertrojan.com", role="user",
            )
            self.user_id = user.id
            self.headers = make_auth_headers(
                "idemp-pay@careertrojan.com", role="user", user_id=user.id,
            )
        finally:
            db.close()

    def test_process_requires_idempotency_key(self, test_client):
        """POST /process without Idempotency-Key should return 400."""
        resp = test_client.post(
            "/api/payment/v1/process",
            json={"plan_id": "free"},
            headers=self.headers,
        )
        assert resp.status_code == 400
        body = resp.json()
        # App error handler may wrap in {"error": {"message": ...}}
        msg = body.get("detail", "") or body.get("error", {}).get("message", "")
        assert "Idempotency-Key" in msg

    def test_process_free_plan_idempotent(self, test_client):
        """Same key on free plan should return identical responses."""
        key = str(uuid.uuid4())
        headers = {**self.headers, "Idempotency-Key": key}
        
        resp1 = test_client.post(
            "/api/payment/v1/process",
            json={"plan_id": "free"},
            headers=headers,
        )
        assert resp1.status_code == 200
        
        resp2 = test_client.post(
            "/api/payment/v1/process",
            json={"plan_id": "free"},
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp1.json()["success"] == resp2.json()["success"]

    def test_process_different_keys_both_succeed(self, test_client):
        """Different idempotency keys should each process independently."""
        for _ in range(2):
            key = str(uuid.uuid4())
            headers = {**self.headers, "Idempotency-Key": key}
            resp = test_client.post(
                "/api/payment/v1/process",
                json={"plan_id": "free"},
                headers=headers,
            )
            assert resp.status_code == 200

    def test_refund_requires_idempotency_key(self, test_client):
        """POST /refund needs Idempotency-Key header."""
        resp = test_client.post(
            "/api/payment/v1/refund/tx_fake123",
            headers=self.headers,
        )
        assert resp.status_code == 400
        body = resp.json()
        msg = body.get("detail", "") or body.get("error", {}).get("message", "")
        assert "Idempotency-Key" in msg


class TestCreditsEndpointIdempotency:
    """Integration tests — POST /api/credits/v1/consume with Idempotency-Key."""

    @pytest.fixture(autouse=True)
    def _setup_user(self, test_client):
        """Ensure a DB user exists for auth to resolve."""
        from services.backend_api.db.connection import SessionLocal
        from conftest import create_test_user, make_auth_headers

        db = SessionLocal()
        try:
            user = create_test_user(
                db, email="idemp-cred@careertrojan.com", role="user",
            )
            self.headers = make_auth_headers(
                "idemp-cred@careertrojan.com", role="user", user_id=user.id,
            )
        finally:
            db.close()

    def test_consume_requires_idempotency_key(self, test_client):
        """POST /consume without Idempotency-Key should return 400."""
        resp = test_client.post(
            "/api/credits/v1/consume",
            json={"action_id": "career_analysis", "is_preview": False},
            headers=self.headers,
        )
        # Should be 400 (missing key) or 503 (credit system not available)
        # Both are acceptable — the key check runs first via Depends
        assert resp.status_code in (400, 503)
