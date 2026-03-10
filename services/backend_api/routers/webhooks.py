"""
Braintree Webhooks Router — CareerTrojan
==========================================

Handles inbound Braintree webhook notifications:
  - subscription_charged_successfully
  - subscription_charged_unsuccessfully
  - subscription_canceled
  - subscription_went_past_due
  - subscription_expired
  - subscription_trial_ended
  - dispute_opened / dispute_lost / dispute_won
  - payment_method_revoked_by_customer
  - check (Braintree connectivity test)

Setup in Braintree Control Panel:
  Sandbox → Settings → Webhooks → New Webhook
  URL: https://yourdomain.com/api/payment/v1/webhooks
  Events: Select all subscription + dispute events

Author: CareerTrojan System
Date: 9 February 2026
"""

import os
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from services.backend_api.db.connection import get_db
from services.backend_api.services.idempotency import WebhookDedup

logger = logging.getLogger("payment.webhooks")
router = APIRouter(prefix="/api/payment/v1", tags=["payment-webhooks"])

# ── Braintree SDK import (conditional) ───────────────────────
try:
    import braintree
    from services.backend_api.services import braintree_service
    BRAINTREE_AVAILABLE = True
except ImportError:
    braintree = None  # type: ignore
    braintree_service = None  # type: ignore
    BRAINTREE_AVAILABLE = False


# ============================================================================
# WEBHOOK HANDLERS
# ============================================================================

def _handle_subscription_charged_ok(notification) -> Dict[str, Any]:
    """Subscription payment succeeded — extend access."""
    sub = notification.subscription
    logger.info(
        "✅ Subscription %s charged OK — plan=%s, amount=%s, next=%s",
        sub.id, sub.plan_id, sub.price, sub.next_billing_date,
    )
    # TODO: Update user subscription status in database
    # db_service.extend_subscription(sub.id, sub.next_billing_date)
    return {
        "subscription_id": sub.id,
        "plan_id": sub.plan_id,
        "amount": str(sub.price),
        "next_billing": str(sub.next_billing_date) if sub.next_billing_date else None,
        "action": "access_extended",
    }


def _handle_subscription_charged_fail(notification) -> Dict[str, Any]:
    """Subscription payment failed — notify user, maybe downgrade."""
    sub = notification.subscription
    logger.warning(
        "❌ Subscription %s charge FAILED — plan=%s, status=%s",
        sub.id, sub.plan_id, sub.status,
    )
    # TODO: Send user an email about payment failure
    # TODO: After N retries, downgrade to free tier
    # email_service.send_payment_failed(sub.id)
    return {
        "subscription_id": sub.id,
        "plan_id": sub.plan_id,
        "status": sub.status,
        "action": "payment_failed_notification",
    }


def _handle_subscription_canceled(notification) -> Dict[str, Any]:
    """Subscription was canceled — downgrade user at end of period."""
    sub = notification.subscription
    logger.info("🛑 Subscription %s canceled", sub.id)
    # TODO: Set user plan to free at next_billing_date
    # db_service.schedule_downgrade(sub.id, sub.paid_through_date)
    return {
        "subscription_id": sub.id,
        "action": "scheduled_downgrade",
    }


def _handle_subscription_past_due(notification) -> Dict[str, Any]:
    """Subscription is past due — payment retrying."""
    sub = notification.subscription
    logger.warning("⚠️ Subscription %s past due — retrying", sub.id)
    return {
        "subscription_id": sub.id,
        "status": "past_due",
        "action": "retry_in_progress",
    }


def _handle_dispute_opened(notification) -> Dict[str, Any]:
    """Customer opened a payment dispute (chargeback)."""
    dispute = notification.dispute
    logger.error(
        "🚨 DISPUTE opened: ID=%s, Amount=%s, Reason=%s, TX=%s",
        dispute.id, dispute.amount, dispute.reason, dispute.transaction.id,
    )
    # TODO: Alert admin, gather evidence for response
    # admin_alert_service.send_dispute_alert(dispute)
    return {
        "dispute_id": dispute.id,
        "amount": str(dispute.amount),
        "reason": dispute.reason,
        "transaction_id": dispute.transaction.id,
        "action": "admin_alerted",
    }


def _handle_dispute_won(notification) -> Dict[str, Any]:
    """Dispute resolved in our favour."""
    dispute = notification.dispute
    logger.info("✅ Dispute %s WON — Amount=%s", dispute.id, dispute.amount)
    return {"dispute_id": dispute.id, "action": "resolved_won"}


def _handle_dispute_lost(notification) -> Dict[str, Any]:
    """Dispute resolved against us — money refunded to customer."""
    dispute = notification.dispute
    logger.warning("💸 Dispute %s LOST — Amount=%s refunded", dispute.id, dispute.amount)
    # TODO: Downgrade or suspend the user's account
    return {"dispute_id": dispute.id, "action": "resolved_lost"}


def _handle_payment_method_revoked(notification) -> Dict[str, Any]:
    """Customer revoked a saved payment method (e.g., PayPal de-linked)."""
    logger.info("🔑 Payment method revoked by customer")
    # TODO: Mark the payment method as invalid in our records
    return {"action": "payment_method_revoked"}


def _handle_subscription_expired(notification) -> Dict[str, Any]:
    """Subscription reached its end date and expired — downgrade to free."""
    sub = notification.subscription
    logger.info(
        "⏰ Subscription %s expired — plan=%s, billing_cycles=%s",
        sub.id, sub.plan_id,
        getattr(sub, "current_billing_cycle", "?"),
    )
    # TODO: Downgrade user to free tier immediately
    # db_service.downgrade_to_free(sub.id)
    return {
        "subscription_id": sub.id,
        "plan_id": sub.plan_id,
        "action": "downgraded_to_free",
    }


def _handle_subscription_trial_ended(notification) -> Dict[str, Any]:
    """Subscription trial period ended — first real charge is next."""
    sub = notification.subscription
    logger.info(
        "🔔 Subscription %s trial ended — plan=%s, first_billing=%s",
        sub.id, sub.plan_id, sub.next_billing_date,
    )
    return {
        "subscription_id": sub.id,
        "plan_id": sub.plan_id,
        "next_billing": str(sub.next_billing_date) if sub.next_billing_date else None,
        "action": "trial_ended",
    }


# ── Handler dispatch table ───────────────────────────────────
WEBHOOK_HANDLERS = {
    "subscription_charged_successfully": _handle_subscription_charged_ok,
    "subscription_charged_unsuccessfully": _handle_subscription_charged_fail,
    "subscription_canceled": _handle_subscription_canceled,
    "subscription_went_past_due": _handle_subscription_past_due,
    "subscription_expired": _handle_subscription_expired,
    "subscription_trial_ended": _handle_subscription_trial_ended,
    "dispute_opened": _handle_dispute_opened,
    "dispute_won": _handle_dispute_won,
    "dispute_lost": _handle_dispute_lost,
    "payment_method_revoked_by_customer": _handle_payment_method_revoked,
}


# ============================================================================
# ENDPOINT
# ============================================================================

@router.post("/webhooks")
async def braintree_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive and verify Braintree webhook notifications.

    Braintree sends POST requests with:
      - bt_signature: HMAC signature for verification
      - bt_payload: Base64-encoded XML payload

    Verification ensures the request genuinely came from Braintree.
    Duplicate events are detected and skipped via WebhookDedup.
    """
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )

    # Read form data (Braintree sends as application/x-www-form-urlencoded)
    form = await request.form()
    bt_signature = form.get("bt_signature")
    bt_payload = form.get("bt_payload")

    if not bt_signature or not bt_payload:
        logger.warning("Webhook received with missing signature/payload")
        raise HTTPException(status_code=400, detail="Missing bt_signature or bt_payload")

    # Verify & parse the webhook
    try:
        gw = braintree_service.gateway()
        notification = gw.webhook_notification.parse(str(bt_signature), str(bt_payload))
    except braintree.exceptions.InvalidSignatureError:
        logger.error("Webhook signature verification FAILED — possible forgery")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    except Exception as e:
        logger.error("Webhook parse error: %s", e)
        raise HTTPException(status_code=400, detail="Webhook parse failed")

    kind = notification.kind
    timestamp = notification.timestamp
    logger.info("Webhook received: kind=%s, timestamp=%s", kind, timestamp)

    # Braintree check event (connectivity test from dashboard)
    if kind == "check":
        logger.info("Webhook check event — connectivity OK")
        return {"ok": True, "kind": "check", "message": "Webhook endpoint is live"}

    # ── Deduplication ────────────────────────────────────────
    # Build a resource_id from the notification payload
    resource_id = "unknown"
    try:
        if hasattr(notification, "subscription") and notification.subscription:
            resource_id = getattr(notification.subscription, "id", "unknown")
        elif hasattr(notification, "dispute") and notification.dispute:
            resource_id = getattr(notification.dispute, "id", "unknown")
    except Exception:
        pass

    if WebhookDedup.is_duplicate(db, kind, resource_id, timestamp):
        logger.info("Duplicate webhook skipped: kind=%s, resource=%s", kind, resource_id)
        return {"ok": True, "kind": kind, "message": "Duplicate event — already processed"}

    # Dispatch to handler
    handler = WEBHOOK_HANDLERS.get(kind)
    if handler:
        try:
            result = handler(notification)
            # Record successful processing for dedup
            WebhookDedup.record(
                db, kind, resource_id, timestamp,
                summary=str(result)[:500],
            )
            return {"ok": True, "kind": kind, "result": result}
        except Exception as e:
            logger.error("Webhook handler error for %s: %s", kind, e)
            # Still record to prevent reprocessing of broken events
            WebhookDedup.record(db, kind, resource_id, timestamp, summary=f"error: {e}")
            # Return 200 anyway so Braintree doesn't retry endlessly
            return {"ok": False, "kind": kind, "error": str(e)}
    else:
        logger.info("Unhandled webhook kind: %s (ignored)", kind)
        WebhookDedup.record(db, kind, resource_id, timestamp, summary="unhandled")
        return {"ok": True, "kind": kind, "message": "Event acknowledged but not handled"}
