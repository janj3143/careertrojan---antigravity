"""
Payment API Routes - CaReerTroJan
=================================
REST API endpoints for payment processing:
- Subscription plans
- Payment processing (Braintree integration — sandbox + production)
- Payment methods (vault cards, PayPal via Drop-in UI)
- Plan upgrades/downgrades
- Payment history

Pricing Tiers:
- Free: $0 (limited features)
- Monthly Pro: $15.99/month
- Annual Pro: $149.99/year
- Elite Pro: $299.99/year

Gateway: Braintree (sandbox → production switchable via BRAINTREE_ENVIRONMENT)

Author: CaReerTroJan System
Date: February 2, 2026
Updated: February 9, 2026 — Braintree integration
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy.orm import Session
import logging
import uuid
import os

from services.backend_api.utils.auth_deps import get_current_user
from services.backend_api.db import models as db_models
from services.backend_api.db.connection import get_db
from services.backend_api.services.idempotency import (
    IdempotencyStore,
    require_idempotency_key,
)

# ── Canonical plan config (single source of truth) ──
from services.backend_api.services.plan_config import (
    PLANS as CANONICAL_PLANS,
    PlanTier as CanonicalPlanTier,
    PROMO_CODES,
)

# Gateway selection — Braintree is primary, Stripe is dormant fallback
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "braintree").lower()

try:
    from services.backend_api.services import braintree_service
    BRAINTREE_AVAILABLE = True
except ImportError:
    braintree_service = None  # type: ignore
    BRAINTREE_AVAILABLE = False

# Stripe is installed but dormant — kept as tested fallback
try:
    import stripe as _stripe_sdk
    _stripe_sdk.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_AVAILABLE = bool(_stripe_sdk.api_key)
except ImportError:
    _stripe_sdk = None  # type: ignore
    STRIPE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment/v1", tags=["payment"])


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class PlanTier(str, Enum):
    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ELITE = "elite"       # Canonical: "elite" (was "elitepro")


# Plan definitions — derived from canonical plan_config.py
PLANS = {}
for _tid, _cfg in CANONICAL_PLANS.items():
    PLANS[_tid] = {
        "id": _tid,
        "name": _cfg.name,
        "price": _cfg.price_annual_usd if _cfg.price_annual_usd else _cfg.price_monthly_usd,
        "currency": "USD",
        "interval": {"one_time": None, "monthly": "month", "annual": "year"}.get(_cfg.interval),
        "features": list(_cfg.features),
        "credits_per_month": _cfg.credits_per_month,
    }


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PlanOut(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    interval: Optional[str]
    features: List[str]
    credits_per_month: int


class PlansListOut(BaseModel):
    plans: List[PlanOut]
    current_plan: Optional[str] = None


class PaymentProcessIn(BaseModel):
    plan_id: str = Field(..., description="Plan to purchase: free, monthly, annual, elite")
    payment_method_nonce: Optional[str] = Field(None, description="Braintree payment method nonce (from Drop-in UI)")
    payment_method_token: Optional[str] = Field(None, description="Vaulted payment method token")
    promo_code: Optional[str] = Field(None, description="Optional promo code")


class PaymentProcessOut(BaseModel):
    success: bool
    subscription_id: Optional[str] = None
    plan_id: str
    message: str
    next_billing_date: Optional[str] = None
    amount_charged: float


class PaymentHistoryItem(BaseModel):
    transaction_id: str
    plan_id: str
    amount: float
    currency: str
    status: str
    created_at: str
    description: str


class PaymentHistoryOut(BaseModel):
    transactions: List[PaymentHistoryItem]
    total_spent: float


class CancelSubscriptionOut(BaseModel):
    success: bool
    message: str
    effective_date: Optional[str] = None


# ============================================================================
# DB HELPERS (subscriptions + payment history)
# ============================================================================


def _safe_user_int(user_id: str) -> int:
    """Convert user_id string to int for DB FK, raising 400 if invalid."""
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID",
        )


def _get_active_subscription(
    db: Session, user_id: str
) -> Optional[db_models.Subscription]:
    """Return the most recent active subscription for a user (or None)."""
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return None
    return (
        db.query(db_models.Subscription)
        .filter(
            db_models.Subscription.user_id == uid,
            db_models.Subscription.status.in_(["active", "past_due"]),
        )
        .order_by(db_models.Subscription.created_at.desc())
        .first()
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_user_id_from_token(
    current_user: db_models.User = Depends(get_current_user),
) -> str:
    """Extract user ID from authenticated JWT token."""
    return str(current_user.id)


def _process_braintree_payment(
    amount: float,
    payment_method_nonce: Optional[str] = None,
    payment_method_token: Optional[str] = None,
    customer_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process payment via Braintree.

    Uses real Braintree SDK when configured, otherwise falls back to stub.
    """
    if BRAINTREE_AVAILABLE and braintree_service.is_configured():
        # Ensure customer exists in Braintree vault
        if customer_id:
            braintree_service.find_or_create_customer(customer_id)

        result = braintree_service.create_sale(
            amount=f"{amount:.2f}",
            payment_method_nonce=payment_method_nonce,
            payment_method_token=payment_method_token,
            customer_id=customer_id,
            order_id=order_id,
        )
        return result
    else:
        # No Braintree credentials — reject the payment, never fake success
        logger.error("Braintree not configured — payment cannot be processed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured. Please contact support.",
        )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/plans", response_model=PlansListOut)
async def get_plans(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Get all available subscription plans
    
    Returns pricing, features, and token limits for each tier
    """
    plans_list = [PlanOut(**plan) for plan in PLANS.values()]
    
    sub = _get_active_subscription(db, user_id)
    current_plan = sub.plan_id if sub else "free"
    
    return PlansListOut(plans=plans_list, current_plan=current_plan)


@router.get("/plans/{plan_id}", response_model=PlanOut)
async def get_plan(plan_id: str):
    """Get details for a specific plan"""
    if plan_id not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found"
        )
    return PlanOut(**PLANS[plan_id])


@router.post("/process", response_model=PaymentProcessOut)
async def process_payment(
    payload: PaymentProcessIn,
    user_id: str = Depends(_get_user_id_from_token),
    idempotency_key: str = Depends(require_idempotency_key),
    db: Session = Depends(get_db),
):
    """
    Process a subscription payment via Braintree.
    
    Requires ``Idempotency-Key`` header to prevent double charges.
    
    - For free tier: No payment required
    - For paid tiers: Requires Braintree nonce (from Drop-in UI) or vaulted token
    """
    # ── Idempotency check ────────────────────────────────────
    is_dup, cached = IdempotencyStore.check(
        db, idempotency_key, "payment", user_id,
        request_body=payload.model_dump(),
    )
    if is_dup:
        if cached and "error" in cached:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=cached["error"])
        if cached is not None:
            return JSONResponse(content=cached, status_code=200)
        # Still processing — tell client to wait
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is already being processed",
        )

    idemp_record = IdempotencyStore.begin(
        db, idempotency_key, "payment", user_id,
        request_body=payload.model_dump(),
    )

    try:
        result = await _do_process_payment(payload, user_id, db)
        # Cache the successful response
        IdempotencyStore.complete(db, idemp_record, 200, result.model_dump())
        return result
    except HTTPException:
        IdempotencyStore.fail(db, idemp_record)
        raise
    except Exception:
        IdempotencyStore.fail(db, idemp_record)
        raise


async def _do_process_payment(
    payload: PaymentProcessIn,
    user_id: str,
    db: Session = None,
) -> PaymentProcessOut:
    """Core payment logic — extracted so idempotency wrapper stays clean."""
    if payload.plan_id not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {payload.plan_id}"
        )
    
    plan = PLANS[payload.plan_id]
    
    # Free tier - no payment needed
    if payload.plan_id == "free":
        # Deactivate any existing paid subscription
        if db:
            old = _get_active_subscription(db, user_id)
            if old:
                old.status = "canceled"
                old.canceled_at = datetime.now(timezone.utc)
            # Create a free-tier subscription row
            new_sub = db_models.Subscription(
                user_id=_safe_user_int(user_id),
                plan_id="free",
                gateway="none",
                status="active",
                amount=0.0,
                started_at=datetime.now(timezone.utc),
            )
            db.add(new_sub)
            db.commit()
        return PaymentProcessOut(
            success=True,
            subscription_id=None,
            plan_id="free",
            message="Free plan activated",
            amount_charged=0.0
        )
    
    # Paid tier - require payment method
    if not payload.payment_method_nonce and not payload.payment_method_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method required for paid plans. Provide payment_method_nonce (from Drop-in UI) or payment_method_token (vaulted)."
        )
    
    # Apply promo code discount
    discount = 0.0
    if payload.promo_code:
        promo = PROMO_CODES.get(payload.promo_code.upper())
        if promo:
            discount = plan["price"] * (promo["discount_percent"] / 100)
    
    final_amount = round(plan["price"] - discount, 2)
    
    # Process payment via Braintree
    payment_result = _process_braintree_payment(
        amount=final_amount,
        payment_method_nonce=payload.payment_method_nonce,
        payment_method_token=payload.payment_method_token,
        customer_id=user_id,
        order_id=f"order_{uuid.uuid4().hex[:8]}",
    )
    
    if not payment_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment failed"
        )
    
    # Create subscription
    subscription_id = f"sub_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)
    
    # Calculate next billing date
    if plan["interval"] == "month":
        from datetime import timedelta
        next_billing = now + timedelta(days=30)
    elif plan["interval"] == "year":
        from datetime import timedelta
        next_billing = now + timedelta(days=365)
    else:
        next_billing = None
    
    # Persist subscription to DB
    if db:
        old = _get_active_subscription(db, user_id)
        if old:
            old.status = "canceled"
            old.canceled_at = now

        new_sub = db_models.Subscription(
            user_id=_safe_user_int(user_id),
            plan_id=payload.plan_id,
            gateway="braintree",
            gateway_subscription_id=subscription_id,
            gateway_customer_id=user_id,
            status="active",
            amount=final_amount,
            currency=plan["currency"],
            interval=plan["interval"],
            started_at=now,
            next_billing_date=next_billing,
        )
        db.add(new_sub)

        # Persist payment transaction
        tx = db_models.PaymentTransaction(
            user_id=_safe_user_int(user_id),
            gateway="braintree",
            gateway_transaction_id=payment_result.get("transaction_id", f"tx_{uuid.uuid4().hex[:16]}"),
            transaction_type="charge",
            amount=final_amount,
            currency=plan["currency"],
            status="submitted_for_settlement",
            plan_id=payload.plan_id,
            promo_code=payload.promo_code,
            description=f"Subscription to {plan['name']}",
        )
        db.add(tx)
        db.commit()
    
    # ── CRITICAL: Allocate credits after successful payment ──
    try:
        from services.backend_api.services.credit_system import get_credit_manager
        credit_mgr = get_credit_manager()
        credit_mgr.set_user_plan(user_id, CanonicalPlanTier(payload.plan_id))
        logger.info(f"Credits allocated for {user_id} on plan {payload.plan_id}")
    except Exception as e:
        logger.error(f"Failed to allocate credits for {user_id}: {e}")
        # Payment succeeded — don't fail the response; admin can reconcile
    
    logger.info(f"User {user_id} subscribed to {payload.plan_id}")
    
    return PaymentProcessOut(
        success=True,
        subscription_id=subscription_id,
        plan_id=payload.plan_id,
        message=f"Successfully subscribed to {plan['name']}",
        next_billing_date=next_billing.isoformat() if next_billing else None,
        amount_charged=final_amount
    )


@router.get("/history", response_model=PaymentHistoryOut)
async def get_payment_history(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Get user's payment history"""
    rows = (
        db.query(db_models.PaymentTransaction)
        .filter(db_models.PaymentTransaction.user_id == _safe_user_int(user_id))
        .order_by(db_models.PaymentTransaction.created_at.desc())
        .limit(200)
        .all()
    )
    transactions = [
        PaymentHistoryItem(
            transaction_id=r.gateway_transaction_id or str(r.id),
            plan_id=r.plan_id or "",
            amount=r.amount,
            currency=r.currency or "USD",
            status=r.status or "unknown",
            created_at=r.created_at.isoformat() if r.created_at else "",
            description=r.description or "",
        )
        for r in rows
    ]
    total_spent = sum(t.amount for t in transactions if t.status in ("completed", "submitted_for_settlement", "settled"))
    
    return PaymentHistoryOut(
        transactions=transactions,
        total_spent=total_spent
    )


@router.get("/subscription")
async def get_current_subscription(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Get user's current subscription details"""
    sub = _get_active_subscription(db, user_id)
    
    if not sub:
        plan = PLANS.get("free", {})
        return {
            "plan_id": "free",
            "plan_name": plan.get("name", "Free Trial"),
            "active": True,
            "next_billing": None,
            "features": plan.get("features", []),
            "credits_per_month": plan.get("credits_per_month", 15),
        }
    
    plan = PLANS.get(sub.plan_id, PLANS.get("free", {}))
    
    return {
        "plan_id": sub.plan_id,
        "plan_name": plan.get("name", sub.plan_id),
        "subscription_id": sub.gateway_subscription_id,
        "active": sub.status == "active",
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "next_billing": sub.next_billing_date.isoformat() if sub.next_billing_date else None,
        "features": plan.get("features", []),
        "credits_per_month": plan.get("credits_per_month", 15),
    }


@router.post("/cancel", response_model=CancelSubscriptionOut)
async def cancel_subscription(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """Cancel current subscription (effective at end of billing period)"""
    sub = _get_active_subscription(db, user_id)
    
    if not sub or sub.plan_id == "free":
        return CancelSubscriptionOut(
            success=False,
            message="No active paid subscription to cancel"
        )
    
    sub.status = "canceled"
    sub.canceled_at = datetime.now(timezone.utc)
    db.commit()
    
    return CancelSubscriptionOut(
        success=True,
        message="Subscription cancelled. Access continues until end of billing period.",
        effective_date=sub.next_billing_date.isoformat() if sub.next_billing_date else None,
    )


@router.get("/health")
async def health_check():
    """Health check for payment service"""
    bt_configured = BRAINTREE_AVAILABLE and braintree_service.is_configured()
    return {
        "status": "healthy",
        "service": "payment-api",
        "plans_available": len(PLANS),
        "primary_gateway": PAYMENT_GATEWAY,
        "braintree_configured": bt_configured,
        "stripe_available": STRIPE_AVAILABLE,
        "environment": os.getenv("BRAINTREE_ENVIRONMENT", "sandbox") if bt_configured else None,
    }


# ============================================================================
# BRAINTREE-SPECIFIC ENDPOINTS
# ============================================================================
import os


@router.get("/client-token")
async def get_client_token(user_id: str = Depends(_get_user_id_from_token)):
    """
    Generate a Braintree client token for the Drop-in UI.

    The frontend uses this token to render the payment form
    (credit card, PayPal, Apple Pay, etc.).
    """
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured"
        )
    try:
        # Try with customer_id for returning users (pre-fills saved methods)
        try:
            token = braintree_service.generate_client_token(customer_id=user_id)
        except Exception:
            token = braintree_service.generate_client_token()
        return {"client_token": token}
    except Exception as e:
        logger.error("Client token generation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate client token")


@router.post("/methods")
async def add_payment_method(nonce: str, user_id: str = Depends(_get_user_id_from_token)):
    """
    Vault a payment method (card, PayPal) using a nonce from the Drop-in UI.
    """
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")
    try:
        braintree_service.find_or_create_customer(user_id)
        method = braintree_service.create_payment_method(user_id, nonce)
        return {"ok": True, "payment_method": method}
    except Exception as e:
        logger.error("Payment method creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/methods")
async def list_payment_methods(user_id: str = Depends(_get_user_id_from_token)):
    """List all saved payment methods for the current user."""
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        return {"methods": []}
    methods = braintree_service.list_payment_methods(user_id)
    return {"methods": methods}


@router.delete("/methods/{token}")
async def remove_payment_method(token: str):
    """Remove a vaulted payment method."""
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")
    success = braintree_service.delete_payment_method(token)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove payment method")
    return {"ok": True, "message": "Payment method removed"}


@router.get("/transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    """Look up a Braintree transaction by ID."""
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")
    tx = braintree_service.find_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.post("/refund/{transaction_id}")
async def refund_transaction(
    transaction_id: str,
    amount: Optional[str] = None,
    user_id: str = Depends(_get_user_id_from_token),
    idempotency_key: str = Depends(require_idempotency_key),
    db: Session = Depends(get_db),
):
    """Refund a settled transaction (full or partial).
    
    Requires authentication and ``Idempotency-Key`` header.
    """
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    # ── Idempotency check ────────────────────────────────────
    req_body = {"transaction_id": transaction_id, "amount": amount}
    is_dup, cached = IdempotencyStore.check(
        db, idempotency_key, "refund", user_id, request_body=req_body,
    )
    if is_dup:
        if cached and "error" in cached:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=cached["error"])
        if cached is not None:
            return JSONResponse(content=cached, status_code=200)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is already being processed",
        )

    idemp_record = IdempotencyStore.begin(
        db, idempotency_key, "refund", user_id, request_body=req_body,
    )

    try:
        result = braintree_service.refund_transaction(transaction_id, amount)
        if not result["success"]:
            IdempotencyStore.fail(db, idemp_record)
            raise HTTPException(status_code=400, detail=result.get("error", "Refund failed"))
        IdempotencyStore.complete(db, idemp_record, 200, result)
        return result
    except HTTPException:
        raise
    except Exception:
        IdempotencyStore.fail(db, idemp_record)
        raise


@router.get("/gateway-info")
async def gateway_info():
    """
    Return gateway configuration status (no secrets).
    Useful for the frontend to know which environment we're running in.
    """
    bt_configured = BRAINTREE_AVAILABLE and braintree_service.is_configured()
    return {
        "primary_gateway": PAYMENT_GATEWAY,
        "braintree": {
            "configured": bt_configured,
            "environment": os.getenv("BRAINTREE_ENVIRONMENT", "sandbox") if bt_configured else None,
            "merchant_id": os.getenv("BRAINTREE_MERCHANT_ID", "")[:6] + "..." if bt_configured else None,
            "methods": ["card", "paypal", "apple_pay", "google_pay", "venmo"] if bt_configured else [],
        },
        "stripe": {
            "available": STRIPE_AVAILABLE,
            "status": "dormant_fallback",
        },
        # For frontend sandbox indicator
        "environment": os.getenv("BRAINTREE_ENVIRONMENT", "sandbox") if bt_configured else None,
    }
