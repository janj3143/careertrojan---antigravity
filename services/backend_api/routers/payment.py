"""
Payment API Routes - CaReerTroJan
=================================
REST API endpoints for payment processing:
- Subscription plans
- Payment processing (Stripe integration)
- Plan upgrades/downgrades
- Payment history

Pricing Tiers:
- Free: $0 (limited features)
- Monthly Pro: $15.99/month
- Annual Pro: $149.99/year
- Elite Pro: $299.99/year

Author: CaReerTroJan System
Date: February 2, 2026
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import logging
import uuid

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
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    stripe_token: Optional[str] = Field(None, description="Stripe card token")
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


def _process_stripe_payment(amount: float, payment_method_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Process payment via Stripe
    
    TODO: Implement actual Stripe integration
    """
    # Placeholder - in production, use Stripe SDK
    return {
        "success": True,
        "charge_id": f"ch_{uuid.uuid4().hex[:16]}",
        "payment_intent_id": f"pi_{uuid.uuid4().hex[:16]}"
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
    Process a subscription payment
    
    - For free tier: No payment required
    - For paid tiers: Requires Stripe payment method or token
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
    if not payload.payment_method_id and not payload.stripe_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment method required for paid plans"
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
    
    # Process payment
    payment_result = _process_stripe_payment(
        amount=final_amount,
        payment_method_id=payload.payment_method_id or payload.stripe_token or "",
        customer_id=user_id
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
        "stripe_charge_id": payment_result["charge_id"]
    }
    
    # Store payment history
    if user_id not in _payment_history:
        _payment_history[user_id] = []
    
    _payment_history[user_id].append({
        "transaction_id": payment_result["charge_id"],
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
    return {
        "status": "healthy",
        "service": "payment-api",
        "plans_available": len(PLANS),
        "stripe_configured": False  # TODO: Check Stripe API key
    }
