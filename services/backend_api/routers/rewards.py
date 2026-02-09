"""
User Rewards API Routes - CaReerTroJan
======================================
REST API endpoints for the fractional ownership and rewards system:
- Fractional ownership tokens
- Referral rewards
- Activity-based rewards
- Redemption
- Suggestions for earning more

Rewards Philosophy:
- Users earn tokens through engagement
- Tokens represent fractional ownership
- Tokens can be redeemed for premium features
- Top contributors get governance rights

Author: CaReerTroJan System
Date: February 2, 2026
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import logging
import uuid
from sqlalchemy.orm import Session
from services.backend_api.routers.auth import get_current_user
from services.backend_api.db.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rewards/v1", tags=["rewards"])


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class RewardType(str, Enum):
    REFERRAL = "referral"
    ACTIVITY = "activity"
    MILESTONE = "milestone"
    BONUS = "bonus"
    SUGGESTION = "suggestion"


class RewardStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REDEEMED = "redeemed"
    EXPIRED = "expired"


# Reward definitions
REWARD_ACTIONS = {
    "profile_complete": {"tokens": 50, "description": "Complete your profile"},
    "resume_upload": {"tokens": 25, "description": "Upload first resume"},
    "first_application": {"tokens": 30, "description": "Submit first job application"},
    "referral_signup": {"tokens": 100, "description": "Refer a new user who signs up"},
    "referral_subscribe": {"tokens": 250, "description": "Referred user subscribes to paid plan"},
    "weekly_login": {"tokens": 10, "description": "Log in during the week"},
    "interview_complete": {"tokens": 40, "description": "Complete interview coaching session"},
    "feedback_submit": {"tokens": 15, "description": "Submit product feedback"},
    "suggestion_accepted": {"tokens": 200, "description": "Your feature suggestion gets implemented"},
    "milestone_10_apps": {"tokens": 75, "description": "Submit 10 job applications"},
    "milestone_job_offer": {"tokens": 500, "description": "Receive a job offer through platform"},
}


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class RewardItem(BaseModel):
    id: str
    type: RewardType
    tokens: int
    description: str
    earned_at: str
    status: RewardStatus
    expires_at: Optional[str] = None


class RewardsOut(BaseModel):
    total_tokens: int
    available_tokens: int
    lifetime_earned: int
    current_tier: str
    tier_progress: float
    rewards: List[RewardItem]
    ownership_percentage: float


class AvailableReward(BaseModel):
    action: str
    tokens: int
    description: str
    completed: bool


class AvailableRewardsOut(BaseModel):
    available_actions: List[AvailableReward]
    total_potential_tokens: int


class SuggestionIn(BaseModel):
    category: str = Field(..., description="Category: feature, improvement, bug, other")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20, max_length=2000)
    priority: Optional[str] = Field("medium", description="low, medium, high")


class SuggestionOut(BaseModel):
    id: str
    category: str
    title: str
    status: str
    tokens_awarded: int
    message: str
    submitted_at: str


class RedeemIn(BaseModel):
    reward_type: str = Field(..., description="What to redeem for: premium_day, ai_boost, mentor_session")
    tokens_to_spend: int


class RedeemOut(BaseModel):
    success: bool
    tokens_spent: int
    tokens_remaining: int
    reward_granted: str
    message: str


class ReferralCodeOut(BaseModel):
    code: str
    url: str
    total_referrals: int
    pending_referrals: int
    tokens_earned_from_referrals: int


# ============================================================================
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================================================

_user_rewards: Dict[str, List[Dict[str, Any]]] = {}
_user_suggestions: Dict[str, List[Dict[str, Any]]] = {}
_user_referral_codes: Dict[str, str] = {}
_user_completed_actions: Dict[str, List[str]] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_user_id_from_token(user: Any = Depends(get_current_user)) -> str:
    """Extract user ID from auth token"""
    return str(user.id)


def _calculate_tier(total_tokens: int) -> tuple[str, float]:
    """Calculate user tier based on total tokens"""
    tiers = [
        (0, "Bronze", 500),
        (500, "Silver", 2000),
        (2000, "Gold", 5000),
        (5000, "Platinum", 15000),
        (15000, "Diamond", 50000),
        (50000, "Elite", float("inf"))
    ]
    
    for i, (threshold, name, next_threshold) in enumerate(tiers):
        if total_tokens < next_threshold:
            progress = (total_tokens - threshold) / (next_threshold - threshold) * 100
            return name, min(progress, 100.0)
    
    return "Elite", 100.0


def _generate_referral_code(user_id: str) -> str:
    """Generate unique referral code"""
    return f"CT-{uuid.uuid4().hex[:8].upper()}"


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/rewards", response_model=RewardsOut)
async def get_rewards(user_id: str = Depends(_get_user_id_from_token)):
    """
    Get user's rewards and ownership tokens
    
    Returns:
    - Total tokens earned
    - Available tokens (not yet redeemed)
    - Ownership percentage
    - Tier status and progress
    """
    rewards = _user_rewards.get(user_id, [])
    
    # Calculate totals
    lifetime_earned = sum(r["tokens"] for r in rewards)
    available_tokens = sum(
        r["tokens"] for r in rewards 
        if r["status"] == "active"
    )
    
    # Calculate tier
    tier_name, tier_progress = _calculate_tier(lifetime_earned)
    
    # Calculate ownership (simplified - 0.0001% per token)
    ownership_pct = lifetime_earned * 0.0001
    
    return RewardsOut(
        total_tokens=lifetime_earned,
        available_tokens=available_tokens,
        lifetime_earned=lifetime_earned,
        current_tier=tier_name,
        tier_progress=round(tier_progress, 1),
        rewards=[RewardItem(**r) for r in rewards[-20:]],  # Last 20 rewards
        ownership_percentage=round(ownership_pct, 6)
    )


@router.get("/rewards/available", response_model=AvailableRewardsOut)
async def get_available_rewards(user_id: str = Depends(_get_user_id_from_token)):
    """Get list of actions user can complete to earn rewards"""
    completed = set(_user_completed_actions.get(user_id, []))
    
    available = []
    total_potential = 0
    
    for action, details in REWARD_ACTIONS.items():
        is_completed = action in completed
        available.append(AvailableReward(
            action=action,
            tokens=details["tokens"],
            description=details["description"],
            completed=is_completed
        ))
        if not is_completed:
            total_potential += details["tokens"]
    
    return AvailableRewardsOut(
        available_actions=available,
        total_potential_tokens=total_potential
    )


@router.post("/suggestions", response_model=SuggestionOut)
async def submit_suggestion(payload: SuggestionIn, user_id: str = Depends(_get_user_id_from_token)):
    """
    Submit a feature suggestion or feedback
    
    Users earn tokens for helpful suggestions.
    Accepted suggestions earn bonus tokens.
    """
    valid_categories = ["feature", "improvement", "bug", "other"]
    if payload.category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category must be one of: {valid_categories}"
        )
    
    # Create suggestion
    suggestion_id = f"sug_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    
    suggestion = {
        "id": suggestion_id,
        "user_id": user_id,
        "category": payload.category,
        "title": payload.title,
        "description": payload.description,
        "priority": payload.priority,
        "status": "submitted",
        "submitted_at": now.isoformat(),
        "reviewed": False
    }
    
    # Store suggestion
    if user_id not in _user_suggestions:
        _user_suggestions[user_id] = []
    _user_suggestions[user_id].append(suggestion)
    
    # Award tokens for submitting feedback
    tokens_awarded = REWARD_ACTIONS["feedback_submit"]["tokens"]
    
    # Add reward
    if user_id not in _user_rewards:
        _user_rewards[user_id] = []
    
    _user_rewards[user_id].append({
        "id": f"rwd_{uuid.uuid4().hex[:12]}",
        "type": "suggestion",
        "tokens": tokens_awarded,
        "description": f"Submitted suggestion: {payload.title[:50]}",
        "earned_at": now.isoformat(),
        "status": "active",
        "expires_at": None
    })
    
    logger.info(f"User {user_id} submitted suggestion: {suggestion_id}")
    
    return SuggestionOut(
        id=suggestion_id,
        category=payload.category,
        title=payload.title,
        status="submitted",
        tokens_awarded=tokens_awarded,
        message=f"Thank you for your feedback! You earned {tokens_awarded} tokens.",
        submitted_at=now.isoformat()
    )


@router.get("/suggestions")
async def get_my_suggestions(user_id: str = Depends(_get_user_id_from_token)):
    """Get user's submitted suggestions"""
    suggestions = _user_suggestions.get(user_id, [])
    
    return {
        "suggestions": suggestions,
        "total_submitted": len(suggestions),
        "accepted": sum(1 for s in suggestions if s.get("status") == "accepted")
    }


@router.post("/rewards/redeem", response_model=RedeemOut)
async def redeem_rewards(payload: RedeemIn, user_id: str = Depends(_get_user_id_from_token)):
    """
    Redeem tokens for rewards
    
    Options:
    - premium_day: 50 tokens = 1 day premium access
    - ai_boost: 25 tokens = 10 extra AI calls
    - mentor_session: 200 tokens = 30min mentor session
    """
    redemption_options = {
        "premium_day": {"cost": 50, "description": "1 day premium access"},
        "ai_boost": {"cost": 25, "description": "10 extra AI analysis calls"},
        "mentor_session": {"cost": 200, "description": "30-minute mentor session"}
    }
    
    if payload.reward_type not in redemption_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reward type. Options: {list(redemption_options.keys())}"
        )
    
    option = redemption_options[payload.reward_type]
    
    # Check available tokens
    rewards = _user_rewards.get(user_id, [])
    available_tokens = sum(
        r["tokens"] for r in rewards 
        if r["status"] == "active"
    )
    
    if available_tokens < option["cost"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient tokens. Need {option['cost']}, have {available_tokens}"
        )
    
    # Deduct tokens (mark oldest active rewards as redeemed)
    tokens_to_deduct = option["cost"]
    for reward in rewards:
        if reward["status"] == "active" and tokens_to_deduct > 0:
            if reward["tokens"] <= tokens_to_deduct:
                reward["status"] = "redeemed"
                tokens_to_deduct -= reward["tokens"]
            else:
                # Partial redemption - split the reward
                reward["tokens"] -= tokens_to_deduct
                tokens_to_deduct = 0
    
    # Calculate remaining
    remaining = sum(r["tokens"] for r in rewards if r["status"] == "active")
    
    logger.info(f"User {user_id} redeemed {option['cost']} tokens for {payload.reward_type}")
    
    return RedeemOut(
        success=True,
        tokens_spent=option["cost"],
        tokens_remaining=remaining,
        reward_granted=option["description"],
        message=f"Successfully redeemed! {option['description']} has been added to your account."
    )


@router.get("/referral", response_model=ReferralCodeOut)
async def get_referral_code(user_id: str = Depends(_get_user_id_from_token)):
    """Get user's unique referral code and stats"""
    
    # Generate code if not exists
    if user_id not in _user_referral_codes:
        _user_referral_codes[user_id] = _generate_referral_code(user_id)
    
    code = _user_referral_codes[user_id]
    
    # TODO: Calculate actual referral stats from database
    return ReferralCodeOut(
        code=code,
        url=f"https://careertrojan.com/join?ref={code}",
        total_referrals=0,
        pending_referrals=0,
        tokens_earned_from_referrals=0
    )


@router.post("/referral/claim")
async def claim_referral(code: str):
    """Claim a referral bonus (for new users with referral code)"""
    # TODO: Implement referral claim logic
    return {
        "success": True,
        "message": "Referral code applied! You'll receive bonus tokens after completing registration.",
        "bonus_tokens": 50
    }


@router.get("/leaderboard")
async def get_leaderboard():
    """Get top token holders (ownership leaderboard)"""
    # TODO: Implement actual leaderboard from database
    return {
        "leaderboard": [
            {"rank": 1, "username": "top_earner", "tokens": 15000, "tier": "Platinum"},
            {"rank": 2, "username": "active_user", "tokens": 8500, "tier": "Gold"},
            {"rank": 3, "username": "referral_king", "tokens": 6200, "tier": "Gold"},
        ],
        "user_rank": None,  # TODO: Get actual user rank
        "total_participants": 1247
    }


@router.get("/ownership-stats")
async def get_ownership_stats():
    """Get overall ownership statistics"""
    # TODO: Calculate from database
    return {
        "total_tokens_distributed": 2_500_000,
        "total_token_supply": 100_000_000,
        "distributed_percentage": 2.5,
        "unique_token_holders": 1247,
        "average_tokens_per_holder": 2005,
        "governance_threshold": 10000,  # Tokens needed for governance rights
        "next_distribution_date": "2026-03-01"
    }


@router.get("/health")
async def health_check():
    """Health check for rewards service"""
    return {
        "status": "healthy",
        "service": "rewards-api",
        "reward_actions_defined": len(REWARD_ACTIONS)
    }
