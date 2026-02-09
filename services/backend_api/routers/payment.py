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
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================================================

_user_subscriptions: Dict[str, Dict[str, Any]] = {}
_payment_history: Dict[str, List[Dict[str, Any]]] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_user_id_from_token() -> str:
    """Extract user ID from auth token - placeholder"""
    # TODO: Implement proper auth dependency
    return "user_demo"


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
        # Fallback stub for testing without Braintree credentials
        logger.warning("Braintree not configured — using payment stub")
        return {
            "success": True,
            "transaction_id": f"stub_{uuid.uuid4().hex[:16]}",
            "amount": f"{amount:.2f}",
            "status": "submitted_for_settlement",
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/plans", response_model=PlansListOut)
async def get_plans():
    """
    Get all available subscription plans
    
    Returns pricing, features, and token limits for each tier
    """
    plans_list = [PlanOut(**plan) for plan in PLANS.values()]
    
    # TODO: Get current user's plan from auth
    user_id = _get_user_id_from_token()
    current_plan = _user_subscriptions.get(user_id, {}).get("plan_id", "free")
    
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
async def process_payment(payload: PaymentProcessIn):
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
    user_id = _get_user_id_from_token()
    
    # Free tier - no payment needed
    if payload.plan_id == "free":
        _user_subscriptions[user_id] = {
            "plan_id": "free",
            "subscription_id": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "next_billing": None
        }
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
        # TODO: Validate promo code from database
        if payload.promo_code.upper() == "LAUNCH20":
            discount = plan["price"] * 0.20
        elif payload.promo_code.upper() == "CAREER10":
            discount = plan["price"] * 0.10
    
    final_amount = plan["price"] - discount
    
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
    
    # Store subscription
    _user_subscriptions[user_id] = {
        "plan_id": payload.plan_id,
        "subscription_id": subscription_id,
        "started_at": now.isoformat(),
        "next_billing": next_billing.isoformat() if next_billing else None,
        "braintree_transaction_id": payment_result.get("transaction_id")
    }
    
    # Store payment history
    if user_id not in _payment_history:
        _payment_history[user_id] = []
    
    _payment_history[user_id].append({
        "transaction_id": payment_result.get("transaction_id", f"tx_{uuid.uuid4().hex[:16]}"),
        "plan_id": payload.plan_id,
        "amount": final_amount,
        "currency": plan["currency"],
        "status": "completed",
        "created_at": now.isoformat(),
        "description": f"Subscription to {plan['name']}"
    })
    
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
async def get_payment_history():
    """Get user's payment history"""
    user_id = _get_user_id_from_token()
    transactions = _payment_history.get(user_id, [])
    
    total_spent = sum(t["amount"] for t in transactions if t["status"] == "completed")
    
    return PaymentHistoryOut(
        transactions=[PaymentHistoryItem(**t) for t in transactions],
        total_spent=total_spent
    )


@router.get("/subscription")
async def get_current_subscription():
    """Get user's current subscription details"""
    user_id = _get_user_id_from_token()
    subscription = _user_subscriptions.get(user_id)
    
    if not subscription:
        return {
            "plan_id": "free",
            "plan_name": "Free Trial",
            "active": True,
            "next_billing": None
        }
    
    plan = PLANS.get(subscription["plan_id"], PLANS["free"])
    
    return {
        "plan_id": subscription["plan_id"],
        "plan_name": plan["name"],
        "subscription_id": subscription.get("subscription_id"),
        "active": True,
        "started_at": subscription["started_at"],
        "next_billing": subscription.get("next_billing"),
        "features": plan["features"],
        "token_limit": plan["token_limit"]
    }


@router.post("/cancel", response_model=CancelSubscriptionOut)
async def cancel_subscription():
    """Cancel current subscription (effective at end of billing period)"""
    user_id = _get_user_id_from_token()
    subscription = _user_subscriptions.get(user_id)
    
    if not subscription or subscription["plan_id"] == "free":
        return CancelSubscriptionOut(
            success=False,
            message="No active paid subscription to cancel"
        )
    
    # Mark for cancellation (stays active until next_billing)
    subscription["cancelled"] = True
    subscription["cancelled_at"] = datetime.now(timezone.utc).isoformat()
    
    return CancelSubscriptionOut(
        success=True,
        message="Subscription cancelled. Access continues until end of billing period.",
        effective_date=subscription.get("next_billing")
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
async def get_client_token():
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
    user_id = _get_user_id_from_token()
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
async def add_payment_method(nonce: str):
    """
    Vault a payment method (card, PayPal) using a nonce from the Drop-in UI.
    """
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway not configured")

    user_id = _get_user_id_from_token()
    try:
        braintree_service.find_or_create_customer(user_id)
        method = braintree_service.create_payment_method(user_id, nonce)
        return {"ok": True, "payment_method": method}
    except Exception as e:
        logger.error("Payment method creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/methods")
async def list_payment_methods():
    """List all saved payment methods for the current user."""
    if not BRAINTREE_AVAILABLE or not braintree_service.is_configured():
        return {"methods": []}

    user_id = _get_user_id_from_token()
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
