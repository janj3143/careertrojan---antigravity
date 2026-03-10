"""
Webhook Router — CareerTrojan
===============================
Receives and processes incoming webhooks from payment gateways and
third-party services:

  POST /api/webhooks/v1/braintree   — Braintree notifications
  POST /api/webhooks/v1/stripe      — Stripe events
  POST /api/webhooks/v1/zendesk     — Zendesk ticket updates

All events are:
  1. Signature-verified
  2. Logged to the webhook_events table (idempotency via event_id)
  3. Dispatched to the appropriate handler
  4. Marked processed / failed

Author: CareerTrojan System
Date:   March 1, 2026
"""

from __future__ import annotations

import hashlib
import hmac
import json

# AI agent queue — enqueue zendesk jobs for LLM processing
try:
    from services.backend_api.services.ai_queue_service import enqueue as ai_enqueue
except ImportError:
    ai_enqueue = None  # type: ignore
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db import models

# Braintree webhook parsing
try:
    import braintree
    from services.backend_api.services import braintree_service
    BRAINTREE_AVAILABLE = True
except ImportError:
    braintree = None  # type: ignore
    braintree_service = None  # type: ignore
    BRAINTREE_AVAILABLE = False

# Stripe configuration
try:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_AVAILABLE = bool(stripe.api_key)
except Exception:
    STRIPE_AVAILABLE = False

logger = logging.getLogger("webhooks")

router = APIRouter(prefix="/api/webhooks/v1", tags=["webhooks"])


# ============================================================================
# HELPERS
# ============================================================================

def _log_event(
    db: Session,
    *,
    event_id: str,
    source: str,
    event_type: str,
    payload: dict | None = None,
    status_val: str = "received",
) -> models.WebhookEvent:
    """Insert (or skip duplicate) a WebhookEvent row."""
    existing = db.query(models.WebhookEvent).filter(
        models.WebhookEvent.event_id == event_id
    ).first()
    if existing:
        logger.info("Webhook event %s already logged — skipping", event_id)
        raise HTTPException(
            status_code=200,
            detail=f"Event {event_id} already processed",
        )
    evt = models.WebhookEvent(
        event_id=event_id,
        source=source,
        event_type=event_type,
        payload=payload,
        status=status_val,
    )
    db.add(evt)
    db.flush()
    return evt


def _mark_event(db: Session, evt: models.WebhookEvent, status_val: str, error: str | None = None):
    evt.status = status_val
    if error:
        evt.error_message = error
    if status_val in ("processed", "failed"):
        evt.processed_at = datetime.now(timezone.utc)
    db.commit()


def _update_subscription_from_gateway(
    db: Session,
    gateway_subscription_id: str,
    new_status: str,
    extra: dict | None = None,
):
    """Find a Subscription row by its gateway ID and update status."""
    sub = db.query(models.Subscription).filter(
        models.Subscription.gateway_subscription_id == gateway_subscription_id
    ).first()
    if not sub:
        logger.warning("No subscription found for gateway ID %s", gateway_subscription_id)
        return None
    sub.status = new_status
    sub.updated_at = datetime.now(timezone.utc)
    if extra:
        if "cancelled_at" in extra:
            sub.cancelled_at = extra["cancelled_at"]
        if "current_period_end" in extra:
            sub.current_period_end = extra["current_period_end"]
    # Also update user's tier if we're cancelling / expiring
    if new_status in ("cancelled", "expired"):
        user = db.query(models.User).filter(models.User.id == sub.user_id).first()
        if user:
            user.subscription_tier = "free"
            user.subscription_id = None
    db.commit()
    return sub


# ============================================================================
# BRAINTREE WEBHOOKS
# ============================================================================

@router.post("/braintree")
async def braintree_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive Braintree webhook notifications.

    Braintree sends POST with `bt_signature` and `bt_payload` form fields.
    Verification uses the Braintree SDK's `WebhookNotification.parse()`.
    """
    if not BRAINTREE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Braintree SDK not available")

    form = await request.form()
    bt_signature = form.get("bt_signature", "")
    bt_payload = form.get("bt_payload", "")

    if not bt_signature or not bt_payload:
        raise HTTPException(status_code=400, detail="Missing bt_signature or bt_payload")

    # ── Verify & parse ───────────────────────────────────────
    try:
        gw = braintree_service.gateway()
        notification = gw.webhook_notification.parse(str(bt_signature), str(bt_payload))
    except Exception as e:
        logger.error("Braintree webhook signature verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid Braintree webhook signature")

    event_id = f"bt_{notification.timestamp.isoformat()}_{notification.kind}"
    event_type = notification.kind
    payload_dict = {
        "kind": notification.kind,
        "timestamp": notification.timestamp.isoformat() if notification.timestamp else None,
    }

    # ── Log event ────────────────────────────────────────────
    evt = _log_event(
        db,
        event_id=event_id,
        source="braintree",
        event_type=event_type,
        payload=payload_dict,
    )

    # ── Handle by kind ───────────────────────────────────────
    try:
        sub_obj = notification.subscription if hasattr(notification, "subscription") else None
        gw_sub_id = sub_obj.id if sub_obj else None

        if event_type == "subscription_charged_successfully":
            _update_subscription_from_gateway(db, gw_sub_id, "active")
            # Record the transaction (only if we can resolve the user)
            uid = _user_id_for_gateway_sub(db, gw_sub_id)
            if sub_obj and uid:
                tx = models.PaymentTransaction(
                    user_id=uid,
                    subscription_id=_local_sub_id(db, gw_sub_id),
                    gateway="braintree",
                    gateway_transaction_id=getattr(sub_obj, "transactions", [{}])[0].id if sub_obj.transactions else None,
                    transaction_type="charge",
                    status="completed",
                    amount=float(sub_obj.price) if sub_obj.price else 0,
                    currency="USD",
                    plan_id=sub_obj.plan_id if sub_obj else None,
                    description=f"Recurring charge — {sub_obj.plan_id}",
                )
                db.add(tx)

        elif event_type == "subscription_charged_unsuccessfully":
            _update_subscription_from_gateway(db, gw_sub_id, "past_due")

        elif event_type in ("subscription_canceled", "subscription_expired"):
            status_val = "cancelled" if "canceled" in event_type else "expired"
            _update_subscription_from_gateway(
                db, gw_sub_id, status_val,
                extra={"cancelled_at": datetime.now(timezone.utc)},
            )

        elif event_type == "subscription_went_past_due":
            _update_subscription_from_gateway(db, gw_sub_id, "past_due")

        elif event_type == "subscription_trial_ended":
            _update_subscription_from_gateway(db, gw_sub_id, "active")

        elif event_type == "dispute_won":
            dispute_obj = notification.dispute if hasattr(notification, "dispute") else None
            original_tx = getattr(dispute_obj, "transaction", None) if dispute_obj else None
            original_tx_id = getattr(original_tx, "id", None)
            amount_val = getattr(dispute_obj, "amount", None) if dispute_obj else None

            linked_tx = None
            if original_tx_id:
                linked_tx = (
                    db.query(models.PaymentTransaction)
                    .filter(models.PaymentTransaction.gateway_transaction_id == original_tx_id)
                    .order_by(models.PaymentTransaction.created_at.desc())
                    .first()
                )

            if linked_tx:
                tx = models.PaymentTransaction(
                    user_id=linked_tx.user_id,
                    subscription_id=linked_tx.subscription_id,
                    gateway="braintree",
                    gateway_transaction_id=original_tx_id,
                    transaction_type="dispute_won",
                    status="completed",
                    amount=float(amount_val) if amount_val is not None else linked_tx.amount,
                    currency=linked_tx.currency or "USD",
                    plan_id=linked_tx.plan_id,
                    description=f"Dispute won for transaction {original_tx_id}",
                    gateway_response={
                        "event_type": event_type,
                        "dispute_id": getattr(dispute_obj, "id", None) if dispute_obj else None,
                        "reason": getattr(dispute_obj, "reason", None) if dispute_obj else None,
                    },
                )
                db.add(tx)
            else:
                logger.warning("dispute_won received but no matching transaction found: %s", original_tx_id)

        elif event_type in ("dispute_opened", "dispute_lost"):
            dispute_obj = notification.dispute if hasattr(notification, "dispute") else None
            original_tx = getattr(dispute_obj, "transaction", None) if dispute_obj else None
            original_tx_id = getattr(original_tx, "id", None)
            amount_val = getattr(dispute_obj, "amount", None) if dispute_obj else None

            linked_tx = None
            if original_tx_id:
                linked_tx = (
                    db.query(models.PaymentTransaction)
                    .filter(models.PaymentTransaction.gateway_transaction_id == original_tx_id)
                    .order_by(models.PaymentTransaction.created_at.desc())
                    .first()
                )

            if linked_tx:
                tx = models.PaymentTransaction(
                    user_id=linked_tx.user_id,
                    subscription_id=linked_tx.subscription_id,
                    gateway="braintree",
                    gateway_transaction_id=original_tx_id,
                    transaction_type=event_type,
                    status="pending" if event_type == "dispute_opened" else "failed",
                    amount=float(amount_val) if amount_val is not None else linked_tx.amount,
                    currency=linked_tx.currency or "USD",
                    plan_id=linked_tx.plan_id,
                    description=f"{event_type.replace('_', ' ').title()} for transaction {original_tx_id}",
                    gateway_response={
                        "event_type": event_type,
                        "dispute_id": getattr(dispute_obj, "id", None) if dispute_obj else None,
                        "reason": getattr(dispute_obj, "reason", None) if dispute_obj else None,
                    },
                )
                db.add(tx)
            else:
                logger.warning("%s received but no matching transaction found: %s", event_type, original_tx_id)

        else:
            logger.info("Unhandled Braintree event: %s", event_type)

        _mark_event(db, evt, "processed")

    except Exception as e:
        logger.exception("Error processing Braintree webhook %s", event_type)
        _mark_event(db, evt, "failed", error=str(e))

    return {"status": "ok", "event": event_type}


def _user_id_for_gateway_sub(db: Session, gateway_sub_id: str | None) -> int | None:
    if not gateway_sub_id:
        return None
    sub = db.query(models.Subscription).filter(
        models.Subscription.gateway_subscription_id == gateway_sub_id
    ).first()
    return sub.user_id if sub else None


def _local_sub_id(db: Session, gateway_sub_id: str | None) -> str | None:
    if not gateway_sub_id:
        return None
    sub = db.query(models.Subscription).filter(
        models.Subscription.gateway_subscription_id == gateway_sub_id
    ).first()
    return sub.id if sub else None


# ============================================================================
# STRIPE WEBHOOKS
# ============================================================================

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
):
    """
    Receive Stripe webhook events.

    Verifies signature via STRIPE_WEBHOOK_SECRET, then dispatches by event type.
    """
    if not STRIPE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET not set")

    raw_body = await request.body()

    # ── Verify signature ─────────────────────────────────────
    try:
        event = stripe.Webhook.construct_event(
            payload=raw_body,
            sig_header=stripe_signature or "",
            secret=webhook_secret,
        )
    except stripe.error.SignatureVerificationError:
        logger.error("Stripe webhook signature verification failed")
        raise HTTPException(status_code=401, detail="Invalid Stripe signature")
    except Exception as e:
        logger.error("Stripe webhook parse error: %s", e)
        raise HTTPException(status_code=400, detail="Invalid Stripe payload")

    event_id = event["id"]
    event_type = event["type"]
    payload_dict = event.get("data", {})

    # ── Log event ────────────────────────────────────────────
    evt = _log_event(
        db,
        event_id=event_id,
        source="stripe",
        event_type=event_type,
        payload=payload_dict,
    )

    # ── Handle by type ───────────────────────────────────────
    try:
        obj = payload_dict.get("object", {})

        if event_type == "checkout.session.completed":
            _handle_stripe_checkout(db, obj)

        elif event_type == "invoice.payment_succeeded":
            _handle_stripe_invoice_paid(db, obj)

        elif event_type == "invoice.payment_failed":
            sub_id = obj.get("subscription")
            if sub_id:
                _update_subscription_from_gateway(db, sub_id, "past_due")

        elif event_type == "customer.subscription.deleted":
            sub_id = obj.get("id")
            if sub_id:
                _update_subscription_from_gateway(
                    db, sub_id, "cancelled",
                    extra={"cancelled_at": datetime.now(timezone.utc)},
                )

        elif event_type == "customer.subscription.updated":
            sub_id = obj.get("id")
            stripe_status = obj.get("status", "active")
            status_map = {
                "active": "active",
                "past_due": "past_due",
                "canceled": "cancelled",
                "unpaid": "past_due",
                "trialing": "trialing",
            }
            if sub_id:
                _update_subscription_from_gateway(
                    db, sub_id, status_map.get(stripe_status, stripe_status),
                )

        elif event_type in ("payment_intent.succeeded", "charge.succeeded"):
            logger.info("Stripe %s received — transaction logged", event_type)

        else:
            logger.info("Unhandled Stripe event: %s", event_type)

        _mark_event(db, evt, "processed")

    except Exception as e:
        logger.exception("Error processing Stripe webhook %s", event_type)
        _mark_event(db, evt, "failed", error=str(e))

    return {"status": "ok", "event": event_type}


def _handle_stripe_checkout(db: Session, obj: dict):
    """Handle checkout.session.completed — create subscription record if needed."""
    customer = obj.get("customer")
    sub_id = obj.get("subscription")
    amount_total = (obj.get("amount_total") or 0) / 100  # cents → dollars

    if customer and sub_id:
        user = db.query(models.User).filter(
            models.User.stripe_customer_id == customer
        ).first()
        if user:
            tx = models.PaymentTransaction(
                user_id=user.id,
                gateway="stripe",
                gateway_transaction_id=obj.get("payment_intent"),
                transaction_type="charge",
                status="completed",
                amount=amount_total,
                currency=(obj.get("currency") or "usd").upper(),
                description="Stripe checkout session",
            )
            db.add(tx)
            db.commit()


def _handle_stripe_invoice_paid(db: Session, obj: dict):
    """Handle invoice.payment_succeeded — update subscription, log transaction."""
    sub_id = obj.get("subscription")
    if sub_id:
        _update_subscription_from_gateway(db, sub_id, "active")
    customer = obj.get("customer")
    amount = (obj.get("amount_paid") or 0) / 100
    user = db.query(models.User).filter(
        models.User.stripe_customer_id == customer
    ).first() if customer else None
    if user:
        tx = models.PaymentTransaction(
            user_id=user.id,
            gateway="stripe",
            gateway_transaction_id=obj.get("payment_intent"),
            transaction_type="charge",
            status="completed",
            amount=amount,
            currency=(obj.get("currency") or "usd").upper(),
            description="Stripe invoice payment",
        )
        db.add(tx)
        db.commit()


# ============================================================================
# ZENDESK WEBHOOKS (moved from support.py)
# ============================================================================

def _verify_zendesk_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """HMAC-SHA256 signature check for Zendesk webhooks."""
    secret = (os.getenv("ZENDESK_WEBHOOK_SECRET") or os.getenv("ZENDESK_SHARED_SECRET") or "").strip()
    if not secret:
        return True  # no secret configured — allow (dev mode)
    if not signature_header:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.strip().lower().replace("sha256=", "")
    return hmac.compare_digest(digest, provided)

def _zendesk_event_type(payload: Dict[str, Any]) -> str:
    return str(payload.get("event_type") or payload.get("event") or payload.get("type") or "ticket_update")

def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

def _build_zendesk_event_id(payload: Dict[str, Any], raw_body: bytes) -> str:
    ticket_data = payload.get("ticket") or payload
    ticket_id = str(ticket_data.get("id") or payload.get("ticket_id") or "unknown")
    event_type = _zendesk_event_type(payload)

    audit_id = payload.get("audit_id") or payload.get("ticket_event_id") or payload.get("event_id")
    if audit_id:
        return f"zd_{ticket_id}_{event_type}_{audit_id}"

    updated_at = ticket_data.get("updated_at") or payload.get("updated_at")
    if updated_at:
        return f"zd_{ticket_id}_{event_type}_{updated_at}"

    latest_comment = str(ticket_data.get("latest_comment") or payload.get("latest_comment") or "").strip()
    if latest_comment:
        return f"zd_{ticket_id}_{event_type}_c{_short_hash(latest_comment)}"

    return f"zd_{ticket_id}_{event_type}_b{hashlib.sha256(raw_body).hexdigest()[:24]}"

@router.post("/zendesk")
async def zendesk_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_zendesk_webhook_signature: Optional[str] = Header(default=None),
):
    """
    Receive Zendesk webhook notifications for ticket updates.
    """
    raw_body = await request.body()
    if not _verify_zendesk_signature(raw_body, x_zendesk_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid Zendesk webhook signature")

    try:
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON webhook payload")

    event_type = _zendesk_event_type(payload)
    event_id = _build_zendesk_event_id(payload, raw_body)

    evt = _log_event(
        db,
        event_id=event_id,
        source="zendesk",
        event_type=event_type,
        payload=payload,
    )

    try:
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
            logger.warning("Zendesk ticket %s not found locally — ignoring", zendesk_ticket_id)
            _mark_event(db, evt, "ignored", error=f"Ticket {zendesk_ticket_id} not found")
            return {"status": "ok", "message": "Ticket not tracked locally"}

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
        current_meta["last_webhook_event"] = event_type
        current_meta["last_webhook_event_id"] = event_id
        current_meta["last_webhook_payload"] = payload
        ticket.metadata_json = current_meta

        _mark_event(db, evt, "processed")

        # ── Enqueue AI agent job for triage + draft reply ─────────
        ai_job_id = None
        enqueue_events = {"ticket_created", "public_comment_added", "ticket_update", "ticket_updated"}
        if (
            ai_enqueue
            and os.getenv("ZENDESK_AI_AGENT_ENABLED", "true").lower() in ("1", "true", "yes")
            and event_type in enqueue_events
        ):
            try:
                ai_job_id = ai_enqueue(
                    payload,
                    kind="draft_reply",
                    source="zendesk",
                )
                logger.info("AI agent job enqueued: %s for ticket %s", ai_job_id, zendesk_ticket_id)
            except Exception as eq:
                logger.warning("Failed to enqueue AI job for ticket %s: %s", zendesk_ticket_id, eq)

        return {
            "status": "ok",
            "ticket_id": ticket.id,
            "zendesk_ticket_id": ticket.zendesk_ticket_id,
            "updated_status": ticket.status,
            "ai_job_id": ai_job_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing Zendesk webhook")
        _mark_event(db, evt, "failed", error=str(e))
        return {"status": "error", "message": str(e)}


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
async def webhook_health():
    """Health check — reports which webhook sources are configured."""
    return {
        "status": "healthy",
        "service": "webhooks",
        "braintree_available": BRAINTREE_AVAILABLE and braintree_service.is_configured() if BRAINTREE_AVAILABLE else False,
        "stripe_available": STRIPE_AVAILABLE and bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
        "zendesk_available": bool(os.getenv("ZENDESK_WEBHOOK_SECRET") or os.getenv("ZENDESK_SHARED_SECRET")),
    }
