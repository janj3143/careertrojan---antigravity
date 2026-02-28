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
import json
import logging
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# PLAN DEFINITIONS — imported from canonical single source of truth
# ============================================================================

from services.backend_api.services.plan_config import (
    PlanTier,
    PLANS,
    ACTION_COSTS as _CANONICAL_ACTION_COSTS,
    CreditAction,
    get_plan,
    get_action_config,
    user_can_access,
    plan_rank,
)

# Re-export so existing `from credit_system import PLANS, PlanTier` still works
__all__ = [
    "PlanTier", "PLANS", "ACTION_COSTS", "CreditAction",
    "CreditManager", "get_credit_manager", "generate_free_tier_teaser",
]

# Backwards-compat alias: old code imported ActionCost from credit_system
ActionCost = _CANONICAL_ACTION_COSTS  # type: ignore  # It's a dict but keeps the name importable


# ============================================================================
# CREDIT MANAGER CLASS — DB-backed via UserCreditBalance / CreditUsageLog
# ============================================================================



# Re-export ACTION_COSTS from canonical source under the old name
ACTION_COSTS = _CANONICAL_ACTION_COSTS


# ============================================================================
# DB-BACKED CREDIT MANAGER
# ============================================================================

@dataclass
class UserCredits:
    """In-process representation of user's credit balance (hydrated from DB)."""
    user_id: str
    plan: PlanTier
    credits_remaining: int
    credits_used_this_month: int
    month_start: datetime
    credits_total: int = 15


def _get_db_session():
    """Obtain a new DB session (caller must close)."""
    from services.backend_api.db.connection import SessionLocal
    return SessionLocal()


class CreditManager:
    """
    DB-backed credit manager.

    Reads/writes ``UserCreditBalance`` and ``CreditUsageLog`` via SQLAlchemy.
    Falls back to in-memory for resilience when the DB is unreachable.
    """

    # --- public helpers (unchanged API surface) ---------------------------

    def get_user_credits(self, user_id: str) -> UserCredits:
        """Load balance from DB; auto-create a free-tier row if missing."""
        from services.backend_api.db.models import UserCreditBalance

        db = _get_db_session()
        try:
            row = db.query(UserCreditBalance).filter(
                UserCreditBalance.user_id == int(user_id)
            ).first()

            if row is None:
                # First time — create free-tier balance
                plan_cfg = get_plan(PlanTier.FREE)
                now = datetime.now(timezone.utc)
                row = UserCreditBalance(
                    user_id=int(user_id),
                    plan_tier=PlanTier.FREE.value,
                    credits_total=plan_cfg.credits_per_month,
                    credits_remaining=plan_cfg.credits_per_month,
                    credits_used=0,
                    period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                )
                db.add(row)
                db.commit()
                db.refresh(row)

            return UserCredits(
                user_id=str(row.user_id),
                plan=PlanTier(row.plan_tier),
                credits_remaining=row.credits_remaining,
                credits_used_this_month=row.credits_used,
                credits_total=row.credits_total,
                month_start=row.period_start or datetime.now(timezone.utc),
            )
        except Exception:
            db.rollback()
            logger.warning("DB read failed for user %s — returning free-tier default", user_id)
            plan_cfg = get_plan(PlanTier.FREE)
            return UserCredits(
                user_id=user_id,
                plan=PlanTier.FREE,
                credits_remaining=plan_cfg.credits_per_month,
                credits_used_this_month=0,
                credits_total=plan_cfg.credits_per_month,
                month_start=datetime.now(timezone.utc),
            )
        finally:
            db.close()

    def set_user_plan(self, user_id: str, plan: PlanTier) -> UserCredits:
        """Upgrade/downgrade user plan and reset credits for this period."""
        from services.backend_api.db.models import UserCreditBalance

        plan_cfg = get_plan(plan)
        db = _get_db_session()
        try:
            row = db.query(UserCreditBalance).filter(
                UserCreditBalance.user_id == int(user_id)
            ).first()

            now = datetime.now(timezone.utc)
            if row is None:
                row = UserCreditBalance(
                    user_id=int(user_id),
                    plan_tier=plan.value,
                    credits_total=plan_cfg.credits_per_month,
                    credits_remaining=plan_cfg.credits_per_month,
                    credits_used=0,
                    period_start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                )
                db.add(row)
            else:
                row.plan_tier = plan.value
                row.credits_total = plan_cfg.credits_per_month
                row.credits_remaining = plan_cfg.credits_per_month
                row.credits_used = 0
                row.period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            db.commit()
            db.refresh(row)
            return self.get_user_credits(user_id)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_action_cost(self, action_id: str, is_preview: bool = False) -> Optional[Any]:
        """Look up canonical action config."""
        return ACTION_COSTS.get(action_id)

    def can_perform_action(
        self,
        user_id: str,
        action_id: str,
        is_preview: bool = False,
    ) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """Check if user has plan + credits for the action."""
        user = self.get_user_credits(user_id)
        action = ACTION_COSTS.get(action_id)

        if not action:
            return False, f"Unknown action: {action_id}", None

        # Plan-gate check
        if not user_can_access(user.plan, action.requires_plan):
            req_plan = get_plan(action.requires_plan)
            return False, f"Requires {req_plan.name} plan", {
                "required_plan": action.requires_plan.value,
                "required_plan_name": req_plan.name,
                "price": req_plan.price_monthly,
                "upgrade_url": f"/payment?plan={action.requires_plan.value}",
            }

        # Credit check
        cost = action.cost
        if user.credits_remaining < cost:
            return False, f"Insufficient credits ({user.credits_remaining} remaining, need {cost})", {
                "credits_remaining": user.credits_remaining,
                "credits_needed": cost,
                "upgrade_url": "/payment",
            }

        return True, f"OK - costs {cost} credits", None

    def consume_credits(
        self,
        user_id: str,
        action_id: str,
        context: Optional[Dict[str, Any]] = None,
        is_preview: bool = False,
    ) -> Dict[str, Any]:
        """Deduct credits and write an immutable usage log row."""
        from services.backend_api.db.models import UserCreditBalance, CreditUsageLog

        can_do, message, upgrade_info = self.can_perform_action(user_id, action_id, is_preview)
        if not can_do:
            return {"success": False, "message": message, "upgrade_info": upgrade_info, "credits_consumed": 0}

        action = ACTION_COSTS[action_id]
        cost = action.cost

        db = _get_db_session()
        try:
            row = db.query(UserCreditBalance).filter(
                UserCreditBalance.user_id == int(user_id)
            ).with_for_update().first()

            if row is None or row.credits_remaining < cost:
                return {"success": False, "message": "Balance changed — retry", "credits_consumed": 0}

            row.credits_remaining -= cost
            row.credits_used += cost

            log = CreditUsageLog(
                user_id=int(user_id),
                action_id=action_id,
                action_name=action.label,
                credits_consumed=cost,
                credits_remaining_after=row.credits_remaining,
                is_preview=is_preview,
                context_json=json.dumps(context) if context else None,
            )
            db.add(log)
            db.commit()

            logger.info("User %s consumed %d credits for %s", user_id, cost, action_id)
            return {
                "success": True,
                "message": f"Consumed {cost} credits for {action.label}",
                "credits_consumed": cost,
                "credits_remaining": row.credits_remaining,
                "credits_used_this_month": row.credits_used,
            }
        except Exception as exc:
            db.rollback()
            logger.error("Credit consumption failed for user %s: %s", user_id, exc)
            return {"success": False, "message": "Internal error", "credits_consumed": 0}
        finally:
            db.close()

    def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Return credit usage summary including per-action breakdown."""
        from services.backend_api.db.models import CreditUsageLog

        user = self.get_user_credits(user_id)
        plan_cfg = get_plan(user.plan)

        usage_by_action: Dict[str, Dict[str, int]] = {}
        db = _get_db_session()
        try:
            logs = (
                db.query(CreditUsageLog)
                .filter(CreditUsageLog.user_id == int(user_id))
                .order_by(CreditUsageLog.created_at.desc())
                .limit(500)
                .all()
            )
            for log in logs:
                key = log.action_id
                if key not in usage_by_action:
                    usage_by_action[key] = {"count": 0, "credits": 0}
                usage_by_action[key]["count"] += 1
                usage_by_action[key]["credits"] += log.credits_consumed
        except Exception:
            pass
        finally:
            db.close()

        total = plan_cfg.credits_per_month or 1
        return {
            "user_id": user_id,
            "plan": user.plan.value,
            "plan_name": plan_cfg.name,
            "credits_total": total,
            "credits_remaining": user.credits_remaining,
            "credits_used": user.credits_used_this_month,
            "usage_percentage": round((user.credits_used_this_month / total) * 100, 1),
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
