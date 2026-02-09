"""
Credits API Routes - CaReerTroJan
=================================
REST API endpoints for the unified credit system.

Replaces the dual token/AI-call system with single credit currency.

Author: CaReerTroJan System
Date: February 2, 2026
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

# Import credit system
try:
    from services.backend_api.services.credit_system import (
        get_credit_manager,
        CreditManager,
        PLANS,
        ACTION_COSTS,
        PlanTier,
        generate_free_tier_teaser,
    )
    CREDIT_SYSTEM_AVAILABLE = True
except ImportError:
    CREDIT_SYSTEM_AVAILABLE = False
    get_credit_manager = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credits/v1", tags=["credits"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PlanInfo(BaseModel):
    tier: str
    name: str
    credits_per_month: int
    price_monthly: float
    price_yearly: Optional[float]
    features: List[str]
    max_applications: int
    max_coaching: int


class PlansResponse(BaseModel):
    plans: List[PlanInfo]
    current_plan: Optional[str] = None


class ActionCostInfo(BaseModel):
    action_id: str
    name: str
    credits: int
    description: str
    preview_available: bool
    requires_plan: str


class BalanceResponse(BaseModel):
    user_id: str
    plan: str
    plan_name: str
    credits_total: int
    credits_remaining: int
    credits_used: int
    usage_percentage: float


class ConsumeRequest(BaseModel):
    action_id: str = Field(..., description="The action to consume credits for")
    is_preview: bool = Field(False, description="Request preview version (for free tier)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (job_id, etc)")


class ConsumeResponse(BaseModel):
    success: bool
    message: str
    credits_consumed: int
    credits_remaining: int
    upgrade_info: Optional[Dict[str, Any]] = None


class CanPerformResponse(BaseModel):
    can_perform: bool
    message: str
    credits_cost: int
    credits_remaining: int
    upgrade_info: Optional[Dict[str, Any]] = None
    preview_available: bool = False


class TeaserRequest(BaseModel):
    teaser_type: str
    params: Dict[str, Any]


class TeaserResponse(BaseModel):
    title: str
    content: str


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_user_id() -> str:
    """Get current user ID from auth - placeholder"""
    # TODO: Implement proper auth dependency
    return "user_demo"


def _ensure_credit_system():
    """Ensure credit system is available"""
    if not CREDIT_SYSTEM_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credit system not available"
        )


def _get_plan_features(plan_config) -> List[str]:
    """Extract feature list from plan config"""
    features = []
    if plan_config.full_career_analysis:
        features.append("Full career analysis")
    if plan_config.full_job_applications:
        features.append(f"Up to {plan_config.max_applications_per_month} job applications/month")
    if plan_config.resume_tuning:
        features.append("AI resume tuning")
    if plan_config.blocker_detection:
        features.append("Application blocker detection")
    if plan_config.coaching_access:
        features.append(f"Up to {plan_config.max_coaching_sessions} coaching sessions")
    if plan_config.mentorship_access:
        features.append("Mentorship marketplace access")
    if plan_config.dual_career:
        features.append("Dual career suite")
    if plan_config.api_access:
        features.append("API access")
    return features


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/plans", response_model=PlansResponse)
async def get_plans():
    """Get all available plans with credit allocations"""
    _ensure_credit_system()
    
    manager = get_credit_manager()
    user_id = _get_user_id()
    user_credits = manager.get_user_credits(user_id)
    
    plans_list = []
    for tier, config in PLANS.items():
        plans_list.append(PlanInfo(
            tier=tier.value,
            name=config.name,
            credits_per_month=config.credits_per_month,
            price_monthly=config.price_monthly,
            price_yearly=config.price_yearly,
            features=_get_plan_features(config),
            max_applications=config.max_applications_per_month,
            max_coaching=config.max_coaching_sessions,
        ))
    
    return PlansResponse(
        plans=plans_list,
        current_plan=user_credits.plan.value
    )


@router.get("/actions", response_model=List[ActionCostInfo])
async def get_action_costs():
    """Get all action costs"""
    _ensure_credit_system()
    
    actions = []
    for action_id, cost in ACTION_COSTS.items():
        actions.append(ActionCostInfo(
            action_id=action_id,
            name=cost.name,
            credits=cost.credits,
            description=cost.description,
            preview_available=cost.preview_available,
            requires_plan=cost.requires_plan.value,
        ))
    
    return actions


@router.get("/balance", response_model=BalanceResponse)
async def get_balance():
    """Get user's current credit balance and usage"""
    _ensure_credit_system()
    
    manager = get_credit_manager()
    user_id = _get_user_id()
    summary = manager.get_usage_summary(user_id)
    
    return BalanceResponse(
        user_id=summary["user_id"],
        plan=summary["plan"],
        plan_name=summary["plan_name"],
        credits_total=summary["credits_total"],
        credits_remaining=summary["credits_remaining"],
        credits_used=summary["credits_used"],
        usage_percentage=summary["usage_percentage"],
    )


@router.get("/can-perform/{action_id}", response_model=CanPerformResponse)
async def can_perform_action(action_id: str, is_preview: bool = False):
    """Check if user can perform an action"""
    _ensure_credit_system()
    
    manager = get_credit_manager()
    user_id = _get_user_id()
    
    can_perform, message, upgrade_info = manager.can_perform_action(
        user_id, action_id, is_preview
    )
    
    user_credits = manager.get_user_credits(user_id)
    action = ACTION_COSTS.get(action_id)
    
    credits_cost = 0
    preview_available = False
    if action:
        credits_cost = action.preview_credits if is_preview and action.preview_available else action.credits
        preview_available = action.preview_available
    
    return CanPerformResponse(
        can_perform=can_perform,
        message=message,
        credits_cost=credits_cost,
        credits_remaining=user_credits.credits_remaining,
        upgrade_info=upgrade_info,
        preview_available=preview_available,
    )


@router.post("/consume", response_model=ConsumeResponse)
async def consume_credits(request: ConsumeRequest):
    """Consume credits for an action"""
    _ensure_credit_system()
    
    manager = get_credit_manager()
    user_id = _get_user_id()
    
    result = manager.consume_credits(
        user_id=user_id,
        action_id=request.action_id,
        context=request.context,
        is_preview=request.is_preview,
    )
    
    return ConsumeResponse(
        success=result["success"],
        message=result["message"],
        credits_consumed=result["credits_consumed"],
        credits_remaining=result.get("credits_remaining", 0),
        upgrade_info=result.get("upgrade_info"),
    )


@router.get("/usage")
async def get_usage_details():
    """Get detailed usage breakdown"""
    _ensure_credit_system()
    
    manager = get_credit_manager()
    user_id = _get_user_id()
    
    return manager.get_usage_summary(user_id)


@router.post("/teaser", response_model=TeaserResponse)
async def get_teaser(request: TeaserRequest):
    """Generate teaser content for free tier users"""
    _ensure_credit_system()
    
    from services.backend_api.services.credit_system import FREE_TIER_TEASERS
    
    if request.teaser_type not in FREE_TIER_TEASERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown teaser type: {request.teaser_type}"
        )
    
    teaser_config = FREE_TIER_TEASERS[request.teaser_type]
    content = generate_free_tier_teaser(request.teaser_type, **request.params)
    
    return TeaserResponse(
        title=teaser_config["title"],
        content=content,
    )


@router.post("/upgrade/{plan_tier}")
async def upgrade_plan(plan_tier: str):
    """Upgrade user to a new plan (simplified - would integrate with payment)"""
    _ensure_credit_system()
    
    try:
        tier = PlanTier(plan_tier)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan tier: {plan_tier}"
        )
    
    manager = get_credit_manager()
    user_id = _get_user_id()
    
    # In production, this would be called AFTER successful payment
    user_credits = manager.set_user_plan(user_id, tier)
    plan = PLANS[tier]
    
    return {
        "success": True,
        "message": f"Upgraded to {plan.name}",
        "new_plan": tier.value,
        "credits_available": user_credits.credits_remaining,
    }


@router.get("/health")
async def health_check():
    """Health check for credit service"""
    return {
        "status": "healthy",
        "service": "credits-api",
        "credit_system_available": CREDIT_SYSTEM_AVAILABLE,
        "plans_defined": len(PLANS) if CREDIT_SYSTEM_AVAILABLE else 0,
        "actions_defined": len(ACTION_COSTS) if CREDIT_SYSTEM_AVAILABLE else 0,
    }
