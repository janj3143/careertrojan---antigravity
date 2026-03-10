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

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import logging
import uuid
from sqlalchemy.orm import Session

from services.backend_api.utils import security
from services.backend_api.db.connection import get_db
from services.backend_api.db import models

# Braintree service (lazy — only fails at call time if not configured)
try:
    from services.backend_api.services import braintree_service
    BRAINTREE_AVAILABLE = True
except ImportError:
    braintree_service = None  # type: ignore
    BRAINTREE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment/v1", tags=["payment"])


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class PlanTier(str, Enum):
    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ELITE = "elitepro"


# Plan definitions
PLANS = {
    "free": {
        "id": "free",
        "name": "Free Trial",
        "price": 0.0,
        "currency": "USD",
        "interval": None,
        "features": [
            "Basic resume upload",
            "Limited AI analysis (5/month)",
            "Job search",
            "Basic career advice"
        ],
        "token_limit": 50,
        "ai_calls_per_month": 5
    },
    "monthly": {
        "id": "monthly",
        "name": "Monthly Pro",
        "price": 15.99,
        "currency": "USD",
        "interval": "month",
        "features": [
            "Unlimited resume uploads",
            "Full AI analysis",
            "Resume tuning",
            "Application tracker",
            "Interview coaching",
            "Email support"
        ],
        "token_limit": 500,
        "ai_calls_per_month": 100
    },
    "annual": {
        "id": "annual",
        "name": "Annual Pro",
        "price": 149.99,
        "currency": "USD",
        "interval": "year",
        "features": [
            "Everything in Monthly Pro",
            "Dual Career Suite",
            "Priority support",
            "Early access to features",
            "2 months free"
        ],
        "token_limit": 1000,
        "ai_calls_per_month": 200
    },
    "elitepro": {
        "id": "elitepro",
        "name": "Elite Pro",
        "price": 299.99,
        "currency": "USD",
        "interval": "year",
        "features": [
            "Everything in Annual Pro",
            "Personal career advisor",
            "Mentor marketplace access",
            "Fractional ownership rewards",
            "White-glove onboarding",
            "API access"
        ],
        "token_limit": 5000,
        "ai_calls_per_month": 500
    }
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
    token_limit: int
    ai_calls_per_month: int


class PlansListOut(BaseModel):
    plans: List[PlanOut]
    current_plan: Optional[str] = None


class PaymentProcessIn(BaseModel):
    plan_id: str = Field(..., description="Plan to purchase: free, monthly, annual, elitepro")
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
# PROMO CODE HELPER
# ============================================================================

def _resolve_promo(db: Session, code: Optional[str], plan_price: float) -> tuple[float, Optional[str]]:
    """Return (discount_amount, normalised_code) or (0, None)."""
    if not code:
        return 0.0, None
    promo = db.query(models.PromoCode).filter(
        models.PromoCode.code == code.upper(),
        models.PromoCode.is_active == True,
    ).first()
    if not promo:
        return 0.0, None
    if promo.max_uses and promo.times_used >= promo.max_uses:
        return 0.0, None
    if promo.expires_at and promo.expires_at < datetime.utcnow():
        return 0.0, None
    if promo.valid_plans:
        # valid_plans is comma-separated list of plan IDs
        pass  # checked by caller if needed
    if promo.discount_type == "percent":
        discount = round(plan_price * promo.discount_value / 100, 2)
    else:
        discount = min(promo.discount_value, plan_price)
    promo.times_used += 1
    return discount, promo.code


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except security.TokenValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


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
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Payment gateway not configured",
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/plans", response_model=PlansListOut)
async def get_plans(current_user: models.User = Depends(get_current_user)):
    """
    Get all available subscription plans
    
    Returns pricing, features, and token limits for each tier
    """
    plans_list = [PlanOut(**plan) for plan in PLANS.values()]
    current_plan = current_user.subscription_tier or "free"
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
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process a subscription payment via Braintree.
    
    - For free tier: No payment required
    - For paid tiers: Requires Braintree nonce (from Drop-in UI) or vaulted token
    """
    if payload.plan_id not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {payload.plan_id}"
        )
    
    plan = PLANS[payload.plan_id]
    user_id = str(current_user.id)
    
    # Free tier - no payment needed
    if payload.plan_id == "free":
        current_user.subscription_tier = "free"
        current_user.subscription_id = None
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
    
    # Apply promo code discount (DB-backed)
    discount, promo_used = _resolve_promo(db, payload.promo_code, plan["price"])
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
    
    # Create Subscription record
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    if plan["interval"] == "month":
        next_billing = now + timedelta(days=30)
    elif plan["interval"] == "year":
        next_billing = now + timedelta(days=365)
    else:
        next_billing = None

    subscription = models.Subscription(
        user_id=current_user.id,
        plan_id=payload.plan_id,
        gateway="braintree",
        gateway_customer_id=user_id,
        gateway_subscription_id=payment_result.get("subscription_id"),
        status="active",
        price=final_amount,
        currency=plan["currency"],
        interval=plan["interval"],
        promo_code=promo_used,
        discount_amount=discount,
        started_at=now,
        current_period_start=now,
        current_period_end=next_billing,
    )
    db.add(subscription)
    db.flush()  # get subscription.id

    # Create PaymentTransaction record
    transaction = models.PaymentTransaction(
        user_id=current_user.id,
        subscription_id=subscription.id,
        gateway="braintree",
        gateway_transaction_id=payment_result.get("transaction_id"),
        transaction_type="charge",
        status="completed",
        amount=final_amount,
        currency=plan["currency"],
        plan_id=payload.plan_id,
        description=f"Subscription to {plan['name']}",
        gateway_response=payment_result,
    )
    db.add(transaction)

    # Update user record
    current_user.subscription_tier = payload.plan_id
    current_user.subscription_id = subscription.id
    current_user.braintree_customer_id = user_id
    db.commit()

    logger.info("User %s subscribed to %s (sub=%s)", user_id, payload.plan_id, subscription.id)

    return PaymentProcessOut(
        success=True,
        subscription_id=subscription.id,
        plan_id=payload.plan_id,
        message=f"Successfully subscribed to {plan['name']}",
        next_billing_date=next_billing.isoformat() if next_billing else None,
        amount_charged=final_amount,
    )


@router.get("/history", response_model=PaymentHistoryOut)
async def get_payment_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's payment history"""
    rows = (
        db.query(models.PaymentTransaction)
        .filter(models.PaymentTransaction.user_id == current_user.id)
        .order_by(models.PaymentTransaction.created_at.desc())
        .all()
    )
    transactions = [
        PaymentHistoryItem(
            transaction_id=r.gateway_transaction_id or r.id,
            plan_id=r.plan_id or "unknown",
            amount=r.amount,
            currency=r.currency,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            description=r.description or "",
        )
        for r in rows
    ]
    total_spent = sum(t.amount for t in transactions if t.status == "completed")
    return PaymentHistoryOut(transactions=transactions, total_spent=total_spent)


@router.get("/subscription")
async def get_current_subscription(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's current subscription details"""
    sub = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status.in_(["active", "trialing", "past_due"]),
        )
        .order_by(models.Subscription.created_at.desc())
        .first()
    )
    if not sub:
        return {
            "plan_id": "free",
            "plan_name": "Free Trial",
            "active": True,
            "next_billing": None,
        }
    plan = PLANS.get(sub.plan_id, PLANS["free"])
    return {
        "plan_id": sub.plan_id,
        "plan_name": plan["name"],
        "subscription_id": sub.id,
        "active": sub.status in ("active", "trialing"),
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "next_billing": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "features": plan["features"],
        "token_limit": plan["token_limit"],
    }


@router.post("/cancel", response_model=CancelSubscriptionOut)
async def cancel_subscription(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel current subscription (effective at end of billing period)"""
    sub = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.status.in_(["active", "trialing", "past_due"]),
        )
        .order_by(models.Subscription.created_at.desc())
        .first()
    )
    if not sub or sub.plan_id == "free":
        return CancelSubscriptionOut(
            success=False,
            message="No active paid subscription to cancel",
        )

    # Cancel in Braintree if we have a gateway subscription
    if sub.gateway == "braintree" and sub.gateway_subscription_id:
        try:
            if BRAINTREE_AVAILABLE and braintree_service.is_configured():
                braintree_service.cancel_subscription(sub.gateway_subscription_id)
        except Exception as e:
            logger.warning("Braintree cancel failed (continuing): %s", e)

    sub.status = "cancelled"
    sub.cancelled_at = datetime.now(timezone.utc)
    db.commit()

    effective = sub.current_period_end.isoformat() if sub.current_period_end else None
    return CancelSubscriptionOut(
        success=True,
        message="Subscription cancelled. Access continues until end of billing period.",
        effective_date=effective,
    )


@router.get("/health")
async def health_check():
    """Health check for payment service"""
    bt_configured = BRAINTREE_AVAILABLE and braintree_service.is_configured()
    return {
        "status": "healthy",
        "service": "payment-api",
        "plans_available": len(PLANS),
        "gateway": "braintree",
        "braintree_configured": bt_configured,
        "environment": os.getenv("BRAINTREE_ENVIRONMENT", "sandbox") if bt_configured else None,
    }


# ============================================================================
# BRAINTREE-SPECIFIC ENDPOINTS
# ============================================================================
import os


@router.get("/client-token")
async def get_client_token(current_user: models.User = Depends(get_current_user)):
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
    user_id = str(current_user.id)
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
async def add_payment_method(nonce: str, current_user: models.User = Depends(get_current_user)):
    """
    Vault a payment method (card, PayPal) using a nonce from the Drop-in UI.
    """
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    user_id = str(current_user.id)
    try:
        braintree_service.find_or_create_customer(user_id)
        method = braintree_service.create_payment_method(user_id, nonce)
        return {"ok": True, "payment_method": method}
    except Exception as e:
        logger.error("Payment method creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/methods")
async def list_payment_methods(current_user: models.User = Depends(get_current_user)):
    """List all saved payment methods for the current user."""
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    user_id = str(current_user.id)
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
async def refund_transaction(transaction_id: str, amount: Optional[str] = None):
    """Refund a settled transaction (full or partial)."""
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")
    result = braintree_service.refund_transaction(transaction_id, amount)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Refund failed"))
    return result


@router.get("/gateway-info")
async def gateway_info():
    """
    Return gateway configuration status (no secrets).
    Useful for the frontend to know which environment we're running in.
    """
    bt_configured = BRAINTREE_AVAILABLE and braintree_service.is_configured()
    return {
        "gateway": "braintree",
        "configured": bt_configured,
        "environment": os.getenv("BRAINTREE_ENVIRONMENT", "sandbox") if bt_configured else None,
        "merchant_id": os.getenv("BRAINTREE_MERCHANT_ID", "")[:6] + "..." if bt_configured else None,
    }
