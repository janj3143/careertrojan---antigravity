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
from sqlalchemy import func, desc
from services.backend_api.routers.auth import get_current_user
from services.backend_api.db.connection import get_db
from services.backend_api.db.models import (
    UserReward, UserReferral, UserSuggestion, 
    UserCompletedAction, RewardRedemption, User
)

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
# IN-MEMORY STORAGE (Deprecated - using database now)
# ============================================================================

# Legacy in-memory stores kept for migration compatibility
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


def _award_tokens(
    db: Session, 
    user_id: int, 
    reward_type: str, 
    tokens: int, 
    description: str,
    action_key: Optional[str] = None,
    source_id: Optional[str] = None
) -> UserReward:
    """Helper to award tokens to a user."""
    reward = UserReward(
        user_id=user_id,
        reward_type=reward_type,
        tokens=tokens,
        description=description,
        action_key=action_key,
        source_id=source_id,
        status="active",
        earned_at=datetime.utcnow()
    )
    db.add(reward)
    db.commit()
    db.refresh(reward)
    return reward


def _get_user_token_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """Get user's token statistics from database."""
    # Lifetime earned
    lifetime_earned = db.query(func.sum(UserReward.tokens)).filter(
        UserReward.user_id == user_id
    ).scalar() or 0
    
    # Available (active) tokens
    available_tokens = db.query(func.sum(UserReward.tokens)).filter(
        UserReward.user_id == user_id,
        UserReward.status == "active"
    ).scalar() or 0
    
    return {
        "lifetime_earned": lifetime_earned,
        "available_tokens": available_tokens
    }


def award_action_reward(db: Session, user_id: int, action_key: str) -> Optional[UserReward]:
    """
    Award tokens for completing a specific action (if not already completed).
    
    Returns the reward if awarded, None if already completed or invalid action.
    Can be called from other parts of the system.
    """
    if action_key not in REWARD_ACTIONS:
        return None
    
    # Check if already completed
    existing = db.query(UserCompletedAction).filter(
        UserCompletedAction.user_id == user_id,
        UserCompletedAction.action_key == action_key
    ).first()
    
    if existing:
        return None  # Already completed
    
    action = REWARD_ACTIONS[action_key]
    
    # Mark action as completed
    completed = UserCompletedAction(
        user_id=user_id,
        action_key=action_key
    )
    db.add(completed)
    
    # Award tokens
    reward = _award_tokens(
        db, user_id, "activity", action["tokens"],
        action["description"], action_key=action_key
    )
    
    logger.info(f"User {user_id} completed action '{action_key}' and earned {action['tokens']} tokens")
    return reward


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/rewards/award/{action_key}")
async def award_action(
    action_key: str,
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """
    Award tokens for completing a specific action.
    
    Actions are one-time only - repeated calls return already_completed.
    """
    if action_key not in REWARD_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {action_key}. Valid actions: {list(REWARD_ACTIONS.keys())}"
        )
    
    uid = int(user_id)
    reward = award_action_reward(db, uid, action_key)
    
    if reward is None:
        return {
            "success": False,
            "message": f"Action '{action_key}' already completed",
            "tokens_awarded": 0
        }
    
    return {
        "success": True,
        "message": f"Congratulations! You earned {reward.tokens} tokens for: {reward.description}",
        "tokens_awarded": reward.tokens,
        "action": action_key
    }

@router.get("/rewards", response_model=RewardsOut)
async def get_rewards(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """
    Get user's rewards and ownership tokens
    
    Returns:
    - Total tokens earned
    - Available tokens (not yet redeemed)
    - Ownership percentage
    - Tier status and progress
    """
    uid = int(user_id)
    
    # Get token stats from database
    stats = _get_user_token_stats(db, uid)
    lifetime_earned = stats["lifetime_earned"]
    available_tokens = stats["available_tokens"]
    
    # Get recent rewards
    recent_rewards = db.query(UserReward).filter(
        UserReward.user_id == uid
    ).order_by(desc(UserReward.earned_at)).limit(20).all()
    
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
        rewards=[
            RewardItem(
                id=str(r.id),
                type=RewardType(r.reward_type) if r.reward_type in [e.value for e in RewardType] else RewardType.ACTIVITY,
                tokens=r.tokens,
                description=r.description or "",
                earned_at=r.earned_at.isoformat() if r.earned_at else "",
                status=RewardStatus(r.status) if r.status in [e.value for e in RewardStatus] else RewardStatus.ACTIVE,
                expires_at=r.expires_at.isoformat() if r.expires_at else None
            )
            for r in recent_rewards
        ],
        ownership_percentage=round(ownership_pct, 6)
    )


@router.get("/rewards/available", response_model=AvailableRewardsOut)
async def get_available_rewards(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get list of actions user can complete to earn rewards"""
    uid = int(user_id)
    
    # Get completed actions from database
    completed_actions = db.query(UserCompletedAction.action_key).filter(
        UserCompletedAction.user_id == uid
    ).all()
    completed = set(a[0] for a in completed_actions)
    
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
async def submit_suggestion(
    payload: SuggestionIn, 
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
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
    
    uid = int(user_id)
    now = datetime.utcnow()
    
    # Award tokens for submitting feedback
    tokens_awarded = REWARD_ACTIONS["feedback_submit"]["tokens"]
    
    # Create suggestion in database
    suggestion = UserSuggestion(
        user_id=uid,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status="submitted",
        tokens_awarded=tokens_awarded,
        submitted_at=now
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    
    # Award tokens for the suggestion
    _award_tokens(
        db, uid, "suggestion", tokens_awarded,
        f"Submitted suggestion: {payload.title[:50]}",
        action_key="feedback_submit",
        source_id=str(suggestion.id)
    )
    
    logger.info(f"User {user_id} submitted suggestion: {suggestion.id}")
    
    return SuggestionOut(
        id=str(suggestion.id),
        category=payload.category,
        title=payload.title,
        status="submitted",
        tokens_awarded=tokens_awarded,
        message=f"Thank you for your feedback! You earned {tokens_awarded} tokens.",
        submitted_at=now.isoformat()
    )


@router.get("/suggestions")
async def get_my_suggestions(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get user's submitted suggestions"""
    uid = int(user_id)
    
    suggestions = db.query(UserSuggestion).filter(
        UserSuggestion.user_id == uid
    ).order_by(desc(UserSuggestion.submitted_at)).all()
    
    return {
        "suggestions": [
            {
                "id": str(s.id),
                "category": s.category,
                "title": s.title,
                "description": s.description,
                "priority": s.priority,
                "status": s.status,
                "tokens_awarded": s.tokens_awarded,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None
            }
            for s in suggestions
        ],
        "total_submitted": len(suggestions),
        "accepted": sum(1 for s in suggestions if s.status == "accepted")
    }


@router.post("/rewards/redeem", response_model=RedeemOut)
async def redeem_rewards(
    payload: RedeemIn, 
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
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
    
    uid = int(user_id)
    option = redemption_options[payload.reward_type]
    
    # Check available tokens from database
    stats = _get_user_token_stats(db, uid)
    available_tokens = stats["available_tokens"]
    
    if available_tokens < option["cost"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient tokens. Need {option['cost']}, have {available_tokens}"
        )
    
    # Deduct tokens (mark oldest active rewards as redeemed)
    tokens_to_deduct = option["cost"]
    active_rewards = db.query(UserReward).filter(
        UserReward.user_id == uid,
        UserReward.status == "active"
    ).order_by(UserReward.earned_at).all()
    
    now = datetime.utcnow()
    for reward in active_rewards:
        if tokens_to_deduct <= 0:
            break
        if reward.tokens <= tokens_to_deduct:
            reward.status = "redeemed"
            reward.redeemed_at = now
            tokens_to_deduct -= reward.tokens
        else:
            # Partial redemption - reduce tokens on this reward
            reward.tokens -= tokens_to_deduct
            tokens_to_deduct = 0
    
    # Record the redemption
    redemption = RewardRedemption(
        user_id=uid,
        redemption_type=payload.reward_type,
        tokens_spent=option["cost"],
        description=option["description"],
        redeemed_at=now
    )
    db.add(redemption)
    db.commit()
    
    # Calculate remaining tokens
    remaining = db.query(func.sum(UserReward.tokens)).filter(
        UserReward.user_id == uid,
        UserReward.status == "active"
    ).scalar() or 0
    
    logger.info(f"User {user_id} redeemed {option['cost']} tokens for {payload.reward_type}")
    
    return RedeemOut(
        success=True,
        tokens_spent=option["cost"],
        tokens_remaining=remaining,
        reward_granted=option["description"],
        message=f"Successfully redeemed! {option['description']} has been added to your account."
    )


@router.get("/referral", response_model=ReferralCodeOut)
async def get_referral_code(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get user's unique referral code and stats"""
    uid = int(user_id)
    
    # Check if user has a referral code
    referral = db.query(UserReferral).filter(
        UserReferral.referrer_id == uid,
        UserReferral.referee_id == None  # Template referral code
    ).first()
    
    if not referral:
        # Generate and store new referral code
        code = _generate_referral_code(user_id)
        referral = UserReferral(
            referrer_id=uid,
            referral_code=code,
            status="active"
        )
        db.add(referral)
        db.commit()
        db.refresh(referral)
    
    code = referral.referral_code
    
    # Calculate referral stats from database
    total_referrals = db.query(UserReferral).filter(
        UserReferral.referrer_id == uid,
        UserReferral.referee_id != None
    ).count()
    
    pending_referrals = db.query(UserReferral).filter(
        UserReferral.referrer_id == uid,
        UserReferral.referee_id != None,
        UserReferral.status == "pending"
    ).count()
    
    tokens_from_referrals = db.query(func.sum(UserReferral.tokens_awarded)).filter(
        UserReferral.referrer_id == uid
    ).scalar() or 0
    
    return ReferralCodeOut(
        code=code,
        url=f"https://careertrojan.com/join?ref={code}",
        total_referrals=total_referrals,
        pending_referrals=pending_referrals,
        tokens_earned_from_referrals=tokens_from_referrals
    )


@router.post("/referral/claim")
async def claim_referral(code: str, db: Session = Depends(get_db)):
    """Claim a referral bonus (for new users with referral code)"""
    # Look up the referral code
    referral = db.query(UserReferral).filter(
        UserReferral.referral_code == code,
        UserReferral.referee_id == None  # Not yet claimed
    ).first()
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already claimed referral code"
        )
    
    # Note: The actual user assignment happens during registration
    # This endpoint validates the code and returns the bonus info
    return {
        "success": True,
        "message": "Referral code validated! You'll receive bonus tokens after completing registration.",
        "bonus_tokens": REWARD_ACTIONS["referral_signup"]["tokens"],
        "referrer_bonus": REWARD_ACTIONS["referral_signup"]["tokens"]
    }


@router.get("/leaderboard")
async def get_leaderboard(
    user_id: str = Depends(_get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get top token holders (ownership leaderboard)"""
    uid = int(user_id)
    
    # Get top users by lifetime tokens earned
    from sqlalchemy import literal_column
    
    # Subquery to sum tokens per user
    top_users = db.query(
        UserReward.user_id,
        func.sum(UserReward.tokens).label("total_tokens")
    ).group_by(UserReward.user_id).order_by(
        desc(func.sum(UserReward.tokens))
    ).limit(10).all()
    
    # Build leaderboard
    leaderboard = []
    for rank, (uid_entry, tokens) in enumerate(top_users, 1):
        user = db.query(User).filter(User.id == uid_entry).first()
        tier_name, _ = _calculate_tier(tokens)
        leaderboard.append({
            "rank": rank,
            "username": user.full_name or user.email.split("@")[0] if user else f"user_{uid_entry}",
            "tokens": tokens,
            "tier": tier_name
        })
    
    # Get current user's rank
    user_stats = _get_user_token_stats(db, uid)
    user_rank = None
    if user_stats["lifetime_earned"] > 0:
        users_ahead = db.query(func.count(UserReward.user_id.distinct())).filter(
            func.sum(UserReward.tokens) > user_stats["lifetime_earned"]
        ).scalar() or 0
        user_rank = users_ahead + 1
    
    # Get total participants
    total_participants = db.query(func.count(UserReward.user_id.distinct())).scalar() or 0
    
    return {
        "leaderboard": leaderboard,
        "user_rank": user_rank,
        "total_participants": total_participants
    }


@router.get("/ownership-stats")
async def get_ownership_stats(db: Session = Depends(get_db)):
    """Get overall ownership statistics"""
    # Calculate from database
    total_tokens_distributed = db.query(func.sum(UserReward.tokens)).scalar() or 0
    unique_holders = db.query(func.count(UserReward.user_id.distinct())).scalar() or 0
    
    total_supply = 100_000_000  # Fixed total supply
    distributed_pct = (total_tokens_distributed / total_supply) * 100 if total_supply > 0 else 0
    avg_tokens = total_tokens_distributed / unique_holders if unique_holders > 0 else 0
    
    return {
        "total_tokens_distributed": total_tokens_distributed,
        "total_token_supply": total_supply,
        "distributed_percentage": round(distributed_pct, 2),
        "unique_token_holders": unique_holders,
        "average_tokens_per_holder": round(avg_tokens, 2),
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
