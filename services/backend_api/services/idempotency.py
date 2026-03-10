"""
Idempotency Service — CareerTrojan
====================================

Prevents duplicate payment charges, credit consumption, refunds,
and webhook processing.

Three layers:
  1. **IdempotencyStore** — DB-backed registry for client-supplied keys.
     The client sends `Idempotency-Key: <uuid>` on mutating payment
     endpoints.  If the key was seen before, the stored response is
     returned immediately without re-processing.

  2. **WebhookEventLog** — DB table that records every Braintree
     webhook event ID.  Duplicate deliveries are detected and skipped.

  3. **FastAPI dependency helpers** — `require_idempotency_key()` and
     `check_idempotency()` for use in endpoint signatures.

Storage:  Both tables live in the main database alongside the rest of
the CareerTrojan schema.  `init_db()` (via `Base.metadata.create_all`)
picks them up automatically.

Author: CareerTrojan System
Date: February 2026
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import Column, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import Session

from services.backend_api.db.models import Base
from services.backend_api.db.connection import SessionLocal

logger = logging.getLogger("payment.idempotency")

# ── TTL for idempotency keys (24 h — covers Braintree retry window) ──
IDEMPOTENCY_TTL_HOURS = 24


# ============================================================================
# ORM MODELS
# ============================================================================

class IdempotencyRecord(Base):
    """Stores idempotency keys and their cached responses."""
    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    scope = Column(String(64), nullable=False)         # "payment", "credits", "refund"
    user_id = Column(String(64), nullable=False, index=True)
    request_hash = Column(String(64), nullable=True)   # SHA-256 of the request body
    status = Column(String(16), nullable=False, default="processing")  # processing | completed | failed
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)        # JSON-serialised response
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_idemp_key_scope", "key", "scope"),
    )


class WebhookEventRecord(Base):
    """Tracks every processed webhook event for deduplication."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_kind = Column(String(128), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False)  # subscription_id or dispute_id
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256(kind+resource_id+timestamp)
    payload_summary = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============================================================================
# IDEMPOTENCY STORE
# ============================================================================

class IdempotencyStore:
    """DB-backed idempotency key registry."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def check(
        db: Session,
        key: str,
        scope: str,
        user_id: str,
        request_body: Optional[dict] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check whether *key* was already used for *scope*.

        Returns
        -------
        (is_duplicate, cached_response_or_None)
            - ``(False, None)`` → first time — caller should proceed
            - ``(True, {...})`` → replay the cached JSON response
            - ``(True, None)``  → previous request is still *processing*
        """
        record = (
            db.query(IdempotencyRecord)
            .filter(
                IdempotencyRecord.key == key,
                IdempotencyRecord.scope == scope,
            )
            .first()
        )

        if record is None:
            return False, None

        # Expired? treat as fresh
        # Handle both naive and aware datetimes (SQLite stores naive)
        now = datetime.now(timezone.utc)
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            db.delete(record)
            db.commit()
            return False, None

        # Mismatched user → reject (don't leak responses across users)
        if record.user_id != user_id:
            logger.warning(
                "Idempotency key %s used by user %s but belongs to %s",
                key, user_id, record.user_id,
            )
            return True, {"error": "Idempotency key belongs to another user"}

        # Body hash mismatch → same key for different payload
        if request_body is not None and record.request_hash:
            current_hash = _body_hash(request_body)
            if current_hash != record.request_hash:
                return True, {"error": "Idempotency key reused with different request body"}

        if record.status == "completed":
            return True, json.loads(record.response_body) if record.response_body else None

        if record.status == "failed":
            # Let the caller retry on previous failure
            db.delete(record)
            db.commit()
            return False, None

        # Still processing (race condition / previous crash)
        # If older than 5 min, clear it so the retry goes through
        created = record.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created < datetime.now(timezone.utc) - timedelta(minutes=5):
            db.delete(record)
            db.commit()
            return False, None

        return True, None  # still in flight

    @staticmethod
    def begin(
        db: Session,
        key: str,
        scope: str,
        user_id: str,
        request_body: Optional[dict] = None,
    ) -> IdempotencyRecord:
        """Create a *processing* record — call BEFORE doing the real work."""
        record = IdempotencyRecord(
            key=key,
            scope=scope,
            user_id=user_id,
            request_hash=_body_hash(request_body) if request_body else None,
            status="processing",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=IDEMPOTENCY_TTL_HOURS),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def complete(
        db: Session,
        record: IdempotencyRecord,
        response_code: int,
        response_body: Any,
    ) -> None:
        """Mark the record as *completed* and cache the response."""
        record.status = "completed"
        record.response_code = response_code
        record.response_body = json.dumps(response_body, default=str)
        record.completed_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def fail(db: Session, record: IdempotencyRecord) -> None:
        """Mark the record as *failed* — allows retry on next call."""
        record.status = "failed"
        record.completed_at = datetime.now(timezone.utc)
        db.commit()


# ============================================================================
# WEBHOOK DEDUP
# ============================================================================

class WebhookDedup:
    """Prevents double-processing of Braintree webhook notifications."""

    @staticmethod
    def is_duplicate(
        db: Session,
        kind: str,
        resource_id: str,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Return True if this exact webhook was already processed."""
        fp = _webhook_fingerprint(kind, resource_id, timestamp)
        exists = (
            db.query(WebhookEventRecord.id)
            .filter(WebhookEventRecord.fingerprint == fp)
            .first()
        )
        return exists is not None

    @staticmethod
    def record(
        db: Session,
        kind: str,
        resource_id: str,
        timestamp: Optional[datetime] = None,
        summary: Optional[str] = None,
    ) -> None:
        """Record a processed webhook event."""
        fp = _webhook_fingerprint(kind, resource_id, timestamp)
        event = WebhookEventRecord(
            event_kind=kind,
            resource_id=resource_id,
            fingerprint=fp,
            payload_summary=summary,
        )
        db.add(event)
        db.commit()


# ============================================================================
# FASTAPI DEPENDENCY HELPERS
# ============================================================================

from fastapi import Header, HTTPException, status as http_status, Depends
from services.backend_api.db.connection import get_db


def require_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> str:
    """
    FastAPI dependency — extracts and validates the ``Idempotency-Key``
    header.  Returns the key string.

    Usage::

        @router.post("/process")
        async def process_payment(
            ...,
            idempotency_key: str = Depends(require_idempotency_key),
        ):
    """
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for this endpoint",
        )
    key = idempotency_key.strip()
    if len(key) > 255:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must be at most 255 characters",
        )
    return key


def get_idempotency_db() -> Session:
    """Yield a dedicated DB session for idempotency checks."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# INTERNAL HELPERS
# ============================================================================

def _body_hash(body: dict) -> str:
    """SHA-256 of the canonical JSON representation of *body*."""
    canonical = json.dumps(body, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _webhook_fingerprint(
    kind: str,
    resource_id: str,
    timestamp: Optional[datetime] = None,
) -> str:
    """Deterministic fingerprint for a webhook event."""
    ts_str = timestamp.isoformat() if timestamp else "none"
    raw = f"{kind}:{resource_id}:{ts_str}"
    return hashlib.sha256(raw.encode()).hexdigest()
