"""
plan_config.py — Single source of truth for CareerTrojan plan definitions.

EVERY file that references plan tiers, pricing, or credit allocations MUST
import from here instead of defining its own constants.

Canonical system: System C (credit_system.py) — single-credit currency,
action-based costs, preview/teaser gating, per-action feature flags.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PlanTier(str, Enum):
    """Canonical plan tier IDs. Used EVERYWHERE."""
    FREE = "free"
    MONTHLY = "monthly"
    ANNUAL = "annual"
    ELITE = "elite"


@dataclass(frozen=True)
class PlanConfig:
    tier: PlanTier
    name: str
    credits_per_month: int
    price_monthly_usd: float
    price_annual_usd: Optional[float]
    interval: str                   # "one_time" | "monthly" | "annual"
    max_applications: int           # gated limit (0 = disabled, 999 = unlimited)
    max_coaching_sessions: int
    max_resumes_stored: int
    features: List[str] = field(default_factory=list)
    braintree_plan_id: Optional[str] = None  # Set via env vars at runtime


# ── Canonical Plan Definitions ─────────────────────────────────

PLANS: Dict[str, PlanConfig] = {
    "free": PlanConfig(
        tier=PlanTier.FREE,
        name="Free Trial",
        credits_per_month=15,
        price_monthly_usd=0.00,
        price_annual_usd=None,
        interval="one_time",
        max_applications=0,
        max_coaching_sessions=0,
        max_resumes_stored=1,
        features=[
            "Career Analysis Preview",
            "Resume Upload & Parse",
            "Job Search (results only)",
            "Dashboard",
        ],
    ),
    "monthly": PlanConfig(
        tier=PlanTier.MONTHLY,
        name="Monthly Pro",
        credits_per_month=150,
        price_monthly_usd=15.99,
        price_annual_usd=None,
        interval="monthly",
        max_applications=20,
        max_coaching_sessions=3,
        max_resumes_stored=5,
        features=[
            "Full Career Analysis",
            "Full Job Applications",
            "Resume Tuning",
            "Blocker Detection",
            "AI Coaching (3 sessions)",
            "Geo Career Analysis",
        ],
    ),
    "annual": PlanConfig(
        tier=PlanTier.ANNUAL,
        name="Annual Pro",
        credits_per_month=350,
        price_monthly_usd=12.49,   # effective per-month
        price_annual_usd=149.99,
        interval="annual",
        max_applications=35,
        max_coaching_sessions=10,
        max_resumes_stored=10,
        features=[
            "Everything in Monthly",
            "Basic Mentorship",
            "Dual Career Analysis",
            "Career Intelligence Reports",
            "Priority Support",
        ],
    ),
    "elite": PlanConfig(
        tier=PlanTier.ELITE,
        name="Elite Pro",
        credits_per_month=500,
        price_monthly_usd=24.99,   # effective per-month
        price_annual_usd=299.99,
        interval="annual",
        max_applications=999,
        max_coaching_sessions=999,
        max_resumes_stored=50,
        features=[
            "Everything in Annual",
            "Full Mentorship",
            "API Access",
            "Unlimited Applications",
            "Unlimited Coaching",
            "White-Glove Onboarding",
        ],
    ),
}


# ── Action Cost Definitions ────────────────────────────────────
# credit cost per action — used by credit_system.py to debit user balances

class CreditAction(str, Enum):
    """Every gated action in the platform."""
    # Free actions (0 cost)
    LOGIN = "login"
    DASHBOARD = "dashboard"
    PROFILE_VIEW = "profile_view"
    PROFILE_UPDATE = "profile_update"
    JOB_SEARCH = "job_search"
    JOB_VIEW = "job_view"
    RESUME_UPLOAD = "resume_upload"
    RESUME_VIEW = "resume_view"

    # Career Analysis
    CAREER_ANALYSIS_PREVIEW = "career_analysis_preview"
    CAREER_ANALYSIS_FULL = "career_analysis_full"

    # Visualizations
    KEYWORD_OVERLAP_VISUAL = "keyword_overlap_visual"
    JOB_SUITABILITY_GAUGE = "job_suitability_gauge"
    CONNECTED_WORD_CLOUD = "connected_word_cloud"
    MULTI_JOB_COMPARE = "multi_job_compare"

    # Job Application Workflow
    FIT_ANALYSIS_PREVIEW = "fit_analysis_preview"
    FIT_ANALYSIS_FULL = "fit_analysis_full"
    BLOCKER_DETECTION_PREVIEW = "blocker_detection_preview"
    BLOCKER_DETECTION_FULL = "blocker_detection_full"
    RESUME_TUNING_PREVIEW = "resume_tuning_preview"
    RESUME_TUNING_FULL = "resume_tuning_full"

    # Application Tracking
    TRACK_APPLICATION = "track_application"
    UPDATE_APPLICATION_STATUS = "update_application_status"

    # Coaching
    AI_COACHING_SESSION = "ai_coaching_session"
    INTERVIEW_QUESTIONS = "interview_questions"
    STAR_STORY_BUILDER = "star_story_builder"

    # Mentorship
    SEARCH_MENTORS = "search_mentors"
    CONTACT_MENTOR = "contact_mentor"
    MENTORSHIP_SESSION = "mentorship_session"

    # Premium
    DUAL_CAREER_ANALYSIS = "dual_career_analysis"
    CAREER_INTELLIGENCE_REPORT = "career_intelligence_report"
    GEO_CAREER_ANALYSIS = "geo_career_analysis"


@dataclass(frozen=True)
class ActionConfig:
    action: CreditAction
    cost: int
    label: str
    requires_plan: PlanTier  # minimum plan required to even attempt this action
    is_preview: bool = False


ACTION_COSTS: Dict[str, ActionConfig] = {
    # Free actions (0 cost, any plan)
    CreditAction.LOGIN: ActionConfig(CreditAction.LOGIN, 0, "Login", PlanTier.FREE),
    CreditAction.DASHBOARD: ActionConfig(CreditAction.DASHBOARD, 0, "Dashboard", PlanTier.FREE),
    CreditAction.PROFILE_VIEW: ActionConfig(CreditAction.PROFILE_VIEW, 0, "View Profile", PlanTier.FREE),
    CreditAction.PROFILE_UPDATE: ActionConfig(CreditAction.PROFILE_UPDATE, 0, "Update Profile", PlanTier.FREE),
    CreditAction.JOB_SEARCH: ActionConfig(CreditAction.JOB_SEARCH, 0, "Search Jobs", PlanTier.FREE),
    CreditAction.JOB_VIEW: ActionConfig(CreditAction.JOB_VIEW, 0, "View Job", PlanTier.FREE),
    CreditAction.RESUME_UPLOAD: ActionConfig(CreditAction.RESUME_UPLOAD, 0, "Upload Resume", PlanTier.FREE),
    CreditAction.RESUME_VIEW: ActionConfig(CreditAction.RESUME_VIEW, 0, "View Resume", PlanTier.FREE),

    # Career Analysis
    CreditAction.CAREER_ANALYSIS_PREVIEW: ActionConfig(CreditAction.CAREER_ANALYSIS_PREVIEW, 5, "Career Analysis Preview", PlanTier.FREE, is_preview=True),
    CreditAction.CAREER_ANALYSIS_FULL: ActionConfig(CreditAction.CAREER_ANALYSIS_FULL, 10, "Career Analysis Full", PlanTier.MONTHLY),

    # Visualizations
    CreditAction.KEYWORD_OVERLAP_VISUAL: ActionConfig(CreditAction.KEYWORD_OVERLAP_VISUAL, 1, "Keyword Overlap", PlanTier.FREE),
    CreditAction.JOB_SUITABILITY_GAUGE: ActionConfig(CreditAction.JOB_SUITABILITY_GAUGE, 1, "Job Suitability", PlanTier.FREE),
    CreditAction.CONNECTED_WORD_CLOUD: ActionConfig(CreditAction.CONNECTED_WORD_CLOUD, 2, "Word Cloud", PlanTier.FREE),
    CreditAction.MULTI_JOB_COMPARE: ActionConfig(CreditAction.MULTI_JOB_COMPARE, 2, "Multi-Job Compare", PlanTier.FREE),

    # Job Application Workflow (~7 credits per full application)
    CreditAction.FIT_ANALYSIS_PREVIEW: ActionConfig(CreditAction.FIT_ANALYSIS_PREVIEW, 5, "Fit Analysis Preview", PlanTier.FREE, is_preview=True),
    CreditAction.FIT_ANALYSIS_FULL: ActionConfig(CreditAction.FIT_ANALYSIS_FULL, 2, "Fit Analysis Full", PlanTier.MONTHLY),
    CreditAction.BLOCKER_DETECTION_PREVIEW: ActionConfig(CreditAction.BLOCKER_DETECTION_PREVIEW, 5, "Blocker Detection Preview", PlanTier.FREE, is_preview=True),
    CreditAction.BLOCKER_DETECTION_FULL: ActionConfig(CreditAction.BLOCKER_DETECTION_FULL, 2, "Blocker Detection Full", PlanTier.MONTHLY),
    CreditAction.RESUME_TUNING_PREVIEW: ActionConfig(CreditAction.RESUME_TUNING_PREVIEW, 0, "Resume Tuning Preview", PlanTier.FREE, is_preview=True),
    CreditAction.RESUME_TUNING_FULL: ActionConfig(CreditAction.RESUME_TUNING_FULL, 3, "Resume Tuning Full", PlanTier.MONTHLY),

    # Tracking (free but gated)
    CreditAction.TRACK_APPLICATION: ActionConfig(CreditAction.TRACK_APPLICATION, 0, "Track Application", PlanTier.MONTHLY),
    CreditAction.UPDATE_APPLICATION_STATUS: ActionConfig(CreditAction.UPDATE_APPLICATION_STATUS, 0, "Update Status", PlanTier.MONTHLY),

    # Coaching
    CreditAction.AI_COACHING_SESSION: ActionConfig(CreditAction.AI_COACHING_SESSION, 8, "AI Coaching", PlanTier.MONTHLY),
    CreditAction.INTERVIEW_QUESTIONS: ActionConfig(CreditAction.INTERVIEW_QUESTIONS, 3, "Interview Questions", PlanTier.MONTHLY),
    CreditAction.STAR_STORY_BUILDER: ActionConfig(CreditAction.STAR_STORY_BUILDER, 5, "STAR Story Builder", PlanTier.MONTHLY),

    # Mentorship
    CreditAction.SEARCH_MENTORS: ActionConfig(CreditAction.SEARCH_MENTORS, 0, "Search Mentors", PlanTier.FREE),
    CreditAction.CONTACT_MENTOR: ActionConfig(CreditAction.CONTACT_MENTOR, 15, "Contact Mentor", PlanTier.ANNUAL),
    CreditAction.MENTORSHIP_SESSION: ActionConfig(CreditAction.MENTORSHIP_SESSION, 25, "Mentorship Session", PlanTier.ANNUAL),

    # Premium
    CreditAction.DUAL_CAREER_ANALYSIS: ActionConfig(CreditAction.DUAL_CAREER_ANALYSIS, 15, "Dual Career Analysis", PlanTier.ANNUAL),
    CreditAction.CAREER_INTELLIGENCE_REPORT: ActionConfig(CreditAction.CAREER_INTELLIGENCE_REPORT, 20, "Career Intelligence Report", PlanTier.ANNUAL),
    CreditAction.GEO_CAREER_ANALYSIS: ActionConfig(CreditAction.GEO_CAREER_ANALYSIS, 10, "Geo Career Analysis", PlanTier.MONTHLY),
}


# ── Promo Codes ────────────────────────────────────────────────

PROMO_CODES: Dict[str, dict] = {
    "LAUNCH20": {"discount_percent": 20, "description": "Launch 20% off"},
    "CAREER10": {"discount_percent": 10, "description": "Career 10% off"},
}


# ── Helpers ────────────────────────────────────────────────────

PLAN_HIERARCHY = [PlanTier.FREE, PlanTier.MONTHLY, PlanTier.ANNUAL, PlanTier.ELITE]


def plan_rank(tier: PlanTier) -> int:
    """Return numeric rank for plan comparison."""
    return PLAN_HIERARCHY.index(tier)


def user_can_access(user_plan: PlanTier, required_plan: PlanTier) -> bool:
    """Check if user's plan meets or exceeds the required plan level."""
    return plan_rank(user_plan) >= plan_rank(required_plan)


def get_plan(tier_id: str) -> Optional[PlanConfig]:
    """Lookup plan config by tier ID string."""
    return PLANS.get(tier_id)


def get_action_config(action: CreditAction) -> Optional[ActionConfig]:
    """Lookup action cost config."""
    return ACTION_COSTS.get(action)
