"""
CaReerTroJan Unified Credit System
==================================
Single credit currency replacing dual token/AI-call system.

Design Philosophy:
- FREE: Upload resume, see PREVIEWS, get hooked on value
- PAID: Unlock full functionality with graduated limits

Credit Costs Per Action (not per page entry):
- Actions that show value but don't deliver = FREE or PREVIEW
- Actions that deliver real results = COST CREDITS

Baseline: Monthly Pro supports ~20 full job applications/month

Author: CaReerTroJan System
Date: February 2, 2026
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# PLAN DEFINITIONS
# ============================================================================

class PlanTier(str, Enum):
    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ELITE = "elite"


@dataclass
class PlanConfig:
    """Plan configuration with credit allocations"""
    tier: PlanTier
    name: str
    credits_per_month: int
    price_monthly: float
    price_yearly: Optional[float]
    
    # Feature flags
    full_career_analysis: bool = False
    full_job_applications: bool = False
    resume_tuning: bool = False
    blocker_detection: bool = False
    coaching_access: bool = False
    mentorship_access: bool = False
    dual_career: bool = False
    api_access: bool = False
    
    # Limits
    max_applications_per_month: int = 0
    max_coaching_sessions: int = 0
    max_resumes_stored: int = 1


PLANS: Dict[PlanTier, PlanConfig] = {
    # -------------------------------------------------------------------------
    # FREE TIER: Upload resume, see PREVIEWS only
    # Goal: Hook them with value, show what they're missing
    # -------------------------------------------------------------------------
    PlanTier.FREE: PlanConfig(
        tier=PlanTier.FREE,
        name="Free Trial",
        credits_per_month=15,
        price_monthly=0.0,
        price_yearly=None,
        
        # Restricted features (preview mode)
        full_career_analysis=False,      # Gets PREVIEW only
        full_job_applications=False,     # Can search, sees count, but can't apply
        resume_tuning=False,             # Sees SAMPLE of what tuning looks like
        blocker_detection=False,         # Sees that blockers exist, not details
        coaching_access=False,
        mentorship_access=False,
        dual_career=False,
        api_access=False,
        
        max_applications_per_month=0,    # Can't actually apply
        max_coaching_sessions=0,
        max_resumes_stored=1,
    ),
    
    # -------------------------------------------------------------------------
    # MONTHLY PRO: ~20 full applications/month
    # 20 apps × 7 credits = 140 + buffer for coaching = 150
    # -------------------------------------------------------------------------
    PlanTier.MONTHLY: PlanConfig(
        tier=PlanTier.MONTHLY,
        name="Monthly Pro",
        credits_per_month=150,
        price_monthly=15.99,
        price_yearly=None,
        
        full_career_analysis=True,
        full_job_applications=True,
        resume_tuning=True,
        blocker_detection=True,
        coaching_access=True,
        mentorship_access=False,
        dual_career=False,
        api_access=False,
        
        max_applications_per_month=20,
        max_coaching_sessions=3,
        max_resumes_stored=5,
    ),
    
    # -------------------------------------------------------------------------
    # ANNUAL PRO: ~35 full applications/month
    # 35 apps × 7 = 245 + coaching + mentorship intro = 350
    # -------------------------------------------------------------------------
    PlanTier.ANNUAL: PlanConfig(
        tier=PlanTier.ANNUAL,
        name="Annual Pro",
        credits_per_month=350,
        price_monthly=12.49,  # Effective monthly (2 months free)
        price_yearly=149.99,
        
        full_career_analysis=True,
        full_job_applications=True,
        resume_tuning=True,
        blocker_detection=True,
        coaching_access=True,
        mentorship_access=True,          # Basic access
        dual_career=True,
        api_access=False,
        
        max_applications_per_month=35,
        max_coaching_sessions=10,
        max_resumes_stored=10,
    ),
    
    # -------------------------------------------------------------------------
    # ELITE PRO: Full 500 credits, unlimited everything
    # 500 credits = ~70 applications OR mix of premium features
    # -------------------------------------------------------------------------
    PlanTier.ELITE: PlanConfig(
        tier=PlanTier.ELITE,
        name="Elite Pro",
        credits_per_month=500,
        price_monthly=24.99,  # Effective monthly
        price_yearly=299.99,
        
        full_career_analysis=True,
        full_job_applications=True,
        resume_tuning=True,
        blocker_detection=True,
        coaching_access=True,
        mentorship_access=True,          # Full marketplace
        dual_career=True,
        api_access=True,
        
        max_applications_per_month=999,  # Effectively unlimited
        max_coaching_sessions=999,
        max_resumes_stored=50,
    ),
}


# ============================================================================
# ACTION CREDIT COSTS
# ============================================================================

@dataclass
class ActionCost:
    """Cost definition for a single action"""
    action_id: str
    name: str
    credits: int
    description: str
    preview_available: bool = False      # Can free users see a preview?
    preview_credits: int = 0             # Cost for preview (usually free)
    requires_plan: PlanTier = PlanTier.FREE


# Action costs - designed for ~20 apps/month on Monthly Pro (150 credits)
# 20 apps × 7 credits average = 140, leaves 10 for coaching/extras

ACTION_COSTS: Dict[str, ActionCost] = {
    # =========================================================================
    # FREE ACTIONS (Navigation, Account, Job Search)
    # =========================================================================
    "login": ActionCost(
        action_id="login",
        name="Login",
        credits=0,
        description="User authentication",
    ),
    "dashboard_view": ActionCost(
        action_id="dashboard_view", 
        name="View Dashboard",
        credits=0,
        description="View main dashboard",
    ),
    "profile_view": ActionCost(
        action_id="profile_view",
        name="View Profile",
        credits=0,
        description="View user profile",
    ),
    "profile_update": ActionCost(
        action_id="profile_update",
        name="Update Profile",
        credits=0,
        description="Update profile information",
    ),
    "job_search": ActionCost(
        action_id="job_search",
        name="Job Search",
        credits=0,
        description="Search and browse job listings (shows count & titles)",
    ),
    "job_view": ActionCost(
        action_id="job_view",
        name="View Job Details",
        credits=0,
        description="View full job description",
    ),
    
    # =========================================================================
    # RESUME ACTIONS
    # =========================================================================
    "resume_upload": ActionCost(
        action_id="resume_upload",
        name="Resume Upload",
        credits=0,                       # FREE - this is the hook
        description="Upload and parse resume (PDF/DOCX)",
    ),
    "resume_view": ActionCost(
        action_id="resume_view",
        name="View Parsed Resume",
        credits=0,
        description="View your parsed resume data",
    ),
    
    # =========================================================================
    # CAREER ANALYSIS (Preview for free, full for paid)
    # =========================================================================
    "career_analysis_preview": ActionCost(
        action_id="career_analysis_preview",
        name="Career Analysis Preview",
        credits=5,                       # Free tier can afford this once
        description="Basic career analysis with restricted insights",
        preview_available=True,
    ),
    "career_analysis_full": ActionCost(
        action_id="career_analysis_full",
        name="Full Career Analysis",
        credits=10,
        description="Complete AI career analysis with all insights",
        requires_plan=PlanTier.MONTHLY,
    ),

    # =========================================================================
    # VISUALIZATIONS (per-render where compute is heavier)
    # =========================================================================
    "visual_keyword_overlap": ActionCost(
        action_id="visual_keyword_overlap",
        name="Keyword Overlap Visual",
        credits=1,
        description="Venn/overlap visualization of your keywords vs target",
    ),
    "visual_job_suitability": ActionCost(
        action_id="visual_job_suitability",
        name="Job Suitability Gauge",
        credits=1,
        description="Gauge + bar breakdown for a single job fit",
    ),
    "visual_connected_cloud": ActionCost(
        action_id="visual_connected_cloud",
        name="Connected Word Cloud",
        credits=2,
        description="Graph-style keyword map with layout computation",
    ),
    "visual_multi_job_compare": ActionCost(
        action_id="visual_multi_job_compare",
        name="Multi-Job Suitability Compare",
        credits=2,
        description="Compare fit across multiple jobs (≤10 roles)",
    ),
    
    # =========================================================================
    # JOB APPLICATION WORKFLOW (Per-job costs)
    # Target: 7 credits per full application
    # =========================================================================
    "fit_analysis_preview": ActionCost(
        action_id="fit_analysis_preview",
        name="Fit Analysis Preview",
        credits=5,                       # Free tier can see ONE
        description="See fit score only (no details)",
        preview_available=True,
    ),
    "fit_analysis_full": ActionCost(
        action_id="fit_analysis_full",
        name="Full Fit Analysis",
        credits=2,                       # Per job
        description="Complete fit analysis with skill gaps & recommendations",
        requires_plan=PlanTier.MONTHLY,
    ),
    "blocker_detection_preview": ActionCost(
        action_id="blocker_detection_preview",
        name="Blocker Detection Preview",
        credits=5,                       # Free tier preview
        description="Shows blocker COUNT only (e.g., '3 blockers found')",
        preview_available=True,
    ),
    "blocker_detection_full": ActionCost(
        action_id="blocker_detection_full",
        name="Full Blocker Detection",
        credits=2,                       # Per job
        description="Complete blocker analysis with severity & fix strategies",
        requires_plan=PlanTier.MONTHLY,
    ),
    "resume_tuning_preview": ActionCost(
        action_id="resume_tuning_preview",
        name="Resume Tuning Preview",
        credits=0,                       # FREE preview - show WHAT it does
        description="Shows sample tuning suggestions (blurred/partial)",
        preview_available=True,
    ),
    "resume_tuning_full": ActionCost(
        action_id="resume_tuning_full",
        name="Full Resume Tuning",
        credits=3,                       # Per job - most valuable action
        description="Generate job-optimized resume variant",
        requires_plan=PlanTier.MONTHLY,
    ),
    
    # =========================================================================
    # APPLICATION TRACKING
    # =========================================================================
    "application_submit": ActionCost(
        action_id="application_submit",
        name="Track Application",
        credits=0,                       # Free to track
        description="Add job to application tracker",
        requires_plan=PlanTier.MONTHLY,  # But need paid to use tracker
    ),
    "application_update": ActionCost(
        action_id="application_update",
        name="Update Application Status",
        credits=0,
        description="Update application status/notes",
        requires_plan=PlanTier.MONTHLY,
    ),
    
    # =========================================================================
    # COACHING & INTERVIEW PREP
    # =========================================================================
    "coaching_session": ActionCost(
        action_id="coaching_session",
        name="AI Coaching Session",
        credits=8,
        description="Full AI interview coaching session",
        requires_plan=PlanTier.MONTHLY,
    ),
    "interview_questions": ActionCost(
        action_id="interview_questions",
        name="Generate Interview Questions",
        credits=3,
        description="AI-generated interview questions for specific job",
        requires_plan=PlanTier.MONTHLY,
    ),
    "star_story_builder": ActionCost(
        action_id="star_story_builder",
        name="STAR Story Builder",
        credits=5,
        description="Build STAR format stories from your experience",
        requires_plan=PlanTier.MONTHLY,
    ),
    
    # =========================================================================
    # MENTORSHIP
    # =========================================================================
    "mentor_search": ActionCost(
        action_id="mentor_search",
        name="Search Mentors",
        credits=0,                       # Free to browse
        description="Search and browse mentor profiles",
    ),
    "mentor_contact": ActionCost(
        action_id="mentor_contact",
        name="Contact Mentor",
        credits=15,
        description="Initiate contact with a mentor",
        requires_plan=PlanTier.ANNUAL,
    ),
    "mentorship_session": ActionCost(
        action_id="mentorship_session",
        name="Mentorship Session",
        credits=25,
        description="Book mentorship session",
        requires_plan=PlanTier.ANNUAL,
    ),
    
    # =========================================================================
    # PREMIUM FEATURES
    # =========================================================================
    "dual_career_analysis": ActionCost(
        action_id="dual_career_analysis",
        name="Dual Career Analysis",
        credits=15,
        description="Partner career optimization analysis",
        requires_plan=PlanTier.ANNUAL,
    ),
    "career_intelligence_report": ActionCost(
        action_id="career_intelligence_report",
        name="Career Intelligence Report",
        credits=20,
        description="Comprehensive market intelligence report",
        requires_plan=PlanTier.ANNUAL,
    ),
    "geo_career_analysis": ActionCost(
        action_id="geo_career_analysis",
        name="Geographic Career Analysis",
        credits=10,
        description="Location-based career opportunities",
        requires_plan=PlanTier.MONTHLY,
    ),
}


# ============================================================================
# CREDIT ACTION ENUM (for safer imports in pages)
# ============================================================================

class CreditAction(str, Enum):
    """Action identifiers for credit-gated features."""

    # Core flows
    JOB_SEARCH = "job_search"
    FIT_ANALYSIS = "fit_analysis_full"
    BLOCKER_DETECTION = "blocker_detection_full"
    RESUME_TUNING = "resume_tuning_full"
    INTERVIEW_PREP = "interview_questions"

    # Visualizations
    VISUAL_KEYWORD_OVERLAP = "visual_keyword_overlap"
    VISUAL_JOB_SUITABILITY = "visual_job_suitability"
    VISUAL_CONNECTED_CLOUD = "visual_connected_cloud"
    VISUAL_MULTI_JOB_COMPARE = "visual_multi_job_compare"


# ============================================================================
# CREDIT MANAGER CLASS
# ============================================================================

@dataclass
class UserCredits:
    """User's credit balance and usage tracking"""
    user_id: str
    plan: PlanTier
    credits_remaining: int
    credits_used_this_month: int
    month_start: datetime
    usage_history: List[Dict[str, Any]] = field(default_factory=list)


class CreditManager:
    """
    Manages user credits and action authorization.
    
    Usage:
        manager = CreditManager()
        
        # Check if user can perform action
        can_do, message = manager.can_perform_action(user_id, "fit_analysis_full")
        
        # Consume credits for action
        result = manager.consume_credits(user_id, "fit_analysis_full", context={"job_id": "123"})
    """
    
    def __init__(self):
        # In-memory storage (replace with database)
        self._user_credits: Dict[str, UserCredits] = {}
    
    def get_user_credits(self, user_id: str) -> UserCredits:
        """Get or initialize user credits"""
        if user_id not in self._user_credits:
            # Default to free plan
            self._user_credits[user_id] = UserCredits(
                user_id=user_id,
                plan=PlanTier.FREE,
                credits_remaining=PLANS[PlanTier.FREE].credits_per_month,
                credits_used_this_month=0,
                month_start=datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0),
            )
        return self._user_credits[user_id]
    
    def set_user_plan(self, user_id: str, plan: PlanTier) -> UserCredits:
        """Update user's plan and reset credits"""
        user = self.get_user_credits(user_id)
        user.plan = plan
        user.credits_remaining = PLANS[plan].credits_per_month
        user.credits_used_this_month = 0
        user.month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        return user
    
    def get_action_cost(self, action_id: str, is_preview: bool = False) -> Optional[ActionCost]:
        """Get cost for an action"""
        if action_id not in ACTION_COSTS:
            return None
        
        action = ACTION_COSTS[action_id]
        
        # If requesting preview and available, return preview cost
        if is_preview and action.preview_available:
            return ActionCost(
                action_id=f"{action_id}_preview",
                name=f"{action.name} (Preview)",
                credits=action.preview_credits,
                description=action.description,
                preview_available=True,
            )
        
        return action
    
    def can_perform_action(
        self, 
        user_id: str, 
        action_id: str,
        is_preview: bool = False
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Check if user can perform an action.
        
        Returns:
            (can_perform, message, upgrade_info)
        """
        user = self.get_user_credits(user_id)
        action = ACTION_COSTS.get(action_id)
        
        if not action:
            return False, f"Unknown action: {action_id}", None
        
        plan_config = PLANS[user.plan]
        
        # Check plan requirement
        plan_order = [PlanTier.FREE, PlanTier.MONTHLY, PlanTier.ANNUAL, PlanTier.ELITE]
        user_plan_idx = plan_order.index(user.plan)
        required_plan_idx = plan_order.index(action.requires_plan)
        
        if user_plan_idx < required_plan_idx:
            # User needs higher plan
            required_plan = PLANS[action.requires_plan]
            return False, f"Requires {required_plan.name} plan", {
                "required_plan": action.requires_plan.value,
                "required_plan_name": required_plan.name,
                "price": required_plan.price_monthly,
                "upgrade_url": f"/payment?plan={action.requires_plan.value}"
            }
        
        # Check if preview available for free users
        if user.plan == PlanTier.FREE and action.preview_available and not is_preview:
            return False, "Preview available - upgrade for full access", {
                "preview_available": True,
                "preview_action": f"{action_id}_preview",
                "upgrade_url": "/payment"
            }
        
        # Check credit balance
        cost = action.credits
        if is_preview and action.preview_available:
            cost = action.preview_credits
        
        if user.credits_remaining < cost:
            return False, f"Insufficient credits ({user.credits_remaining} remaining, need {cost})", {
                "credits_remaining": user.credits_remaining,
                "credits_needed": cost,
                "upgrade_url": "/payment"
            }
        
        return True, f"OK - costs {cost} credits", None
    
    def consume_credits(
        self,
        user_id: str,
        action_id: str,
        context: Optional[Dict[str, Any]] = None,
        is_preview: bool = False
    ) -> Dict[str, Any]:
        """
        Consume credits for an action.
        
        Returns result dict with success status, remaining credits, etc.
        """
        can_perform, message, upgrade_info = self.can_perform_action(user_id, action_id, is_preview)
        
        if not can_perform:
            return {
                "success": False,
                "message": message,
                "upgrade_info": upgrade_info,
                "credits_consumed": 0,
            }
        
        user = self.get_user_credits(user_id)
        action = ACTION_COSTS[action_id]
        
        cost = action.credits
        if is_preview and action.preview_available:
            cost = action.preview_credits
        
        # Deduct credits
        user.credits_remaining -= cost
        user.credits_used_this_month += cost
        
        # Log usage
        usage_entry = {
            "action_id": action_id,
            "action_name": action.name,
            "credits": cost,
            "is_preview": is_preview,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context or {},
        }
        user.usage_history.append(usage_entry)
        
        logger.info(f"User {user_id} consumed {cost} credits for {action_id}")
        
        return {
            "success": True,
            "message": f"Consumed {cost} credits for {action.name}",
            "credits_consumed": cost,
            "credits_remaining": user.credits_remaining,
            "credits_used_this_month": user.credits_used_this_month,
        }
    
    def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's credit usage summary"""
        user = self.get_user_credits(user_id)
        plan = PLANS[user.plan]
        
        # Calculate usage by category
        usage_by_action = {}
        for entry in user.usage_history:
            action = entry["action_id"]
            if action not in usage_by_action:
                usage_by_action[action] = {"count": 0, "credits": 0}
            usage_by_action[action]["count"] += 1
            usage_by_action[action]["credits"] += entry["credits"]
        
        return {
            "user_id": user_id,
            "plan": user.plan.value,
            "plan_name": plan.name,
            "credits_total": plan.credits_per_month,
            "credits_remaining": user.credits_remaining,
            "credits_used": user.credits_used_this_month,
            "usage_percentage": round((user.credits_used_this_month / plan.credits_per_month) * 100, 1),
            "usage_by_action": usage_by_action,
            "month_start": user.month_start.isoformat(),
        }


# ============================================================================
# FREE TIER TEASER RESPONSES
# ============================================================================

FREE_TIER_TEASERS = {
    "job_search": {
        "title": "🎯 We Found Your Matches!",
        "template": """
## {job_count} Jobs Match Your Profile!

Based on your resume, we identified **{job_count} potential opportunities** including:

{job_previews}

### What You're Missing (Upgrade to Unlock):
- ✅ **Fit Analysis** - See exactly how you match each role
- ✅ **Blocker Detection** - Identify gaps before you apply  
- ✅ **Resume Tuning** - AI-optimized resume for each job
- ✅ **Application Tracker** - Manage your entire job search

**[Upgrade to Monthly Pro - $15.99/mo →](/payment?plan=monthly)**
""",
    },
    "fit_analysis_preview": {
        "title": "📊 Your Fit Score",
        "template": """
## Fit Score: {score}% 

Your resume shows **{match_level}** alignment with this role.

### What's Included (Blurred):
- Matching Skills: ████ ████ ████
- Missing Skills: ████ ████
- Keyword Overlap: ██%
- Recommendations: ████████████

**[See Full Analysis - Upgrade Now →](/payment?plan=monthly)**
""",
    },
    "blocker_preview": {
        "title": "🚫 Application Blockers Detected",
        "template": """
## {blocker_count} Blockers Found

We detected **{critical} critical** and **{major} major** blockers that could prevent your application from succeeding.

### Blocker Categories:
- 🔴 Critical: {critical} found
- 🟠 Major: {major} found  
- 🟡 Moderate: {moderate} found

### To See Full Details & Fix Strategies:
**[Upgrade to Monthly Pro →](/payment?plan=monthly)**
""",
    },
    "resume_tuning_preview": {
        "title": "✨ Resume Enhancement Preview",
        "template": """
## Your Resume Could Be {improvement}% Stronger

Our AI identified **{suggestion_count} improvements** for this specific job:

### Sample Enhancement:
> **Before:** {before_sample}
> 
> **After:** ████████████████████████

### What You'd Get:
- Job-specific keyword optimization
- Achievement quantification
- Skills alignment improvements
- ATS compatibility boost

**[Generate Full Tuned Resume →](/payment?plan=monthly)**
""",
    },
}


def generate_free_tier_teaser(teaser_type: str, **kwargs) -> str:
    """Generate teaser content for free tier users"""
    if teaser_type not in FREE_TIER_TEASERS:
        return "Upgrade to access this feature"
    
    teaser = FREE_TIER_TEASERS[teaser_type]
    return teaser["template"].format(**kwargs)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_credit_manager: Optional[CreditManager] = None


def get_credit_manager() -> CreditManager:
    """Get singleton credit manager instance"""
    global _credit_manager
    if _credit_manager is None:
        _credit_manager = CreditManager()
    return _credit_manager
