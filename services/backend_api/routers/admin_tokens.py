"""
backend/api/routes/admin_tokens.py

Admin token configuration + usage endpoints.
Wired to canonical plan_config.py for plan data and
credit_system.CreditManager for usage data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from services.backend_api.utils.auth_deps import require_admin
from services.backend_api.db.connection import get_db
from services.backend_api.db import models

router = APIRouter(prefix="/api/admin/v1/tokens", tags=["admin-tokens"], dependencies=[Depends(require_admin)])


def _get_plans_from_config() -> Dict[str, Dict[str, Any]]:
    """Load plans from the canonical plan_config source of truth."""
    try:
        from services.backend_api.services.plan_config import PLANS
    except ImportError:
        raise HTTPException(status_code=503, detail="Plan config module not available.")
    result: Dict[str, Dict[str, Any]] = {}
    for key, cfg in PLANS.items():
        result[key] = {
            "tier": cfg.tier.value if hasattr(cfg.tier, "value") else str(cfg.tier),
            "name": cfg.name,
            "included_tokens_per_month": cfg.credits_per_month,
            "price_monthly_usd": cfg.price_monthly_usd,
            "price_annual_usd": cfg.price_annual_usd,
            "interval": cfg.interval,
            "max_applications": cfg.max_applications,
            "max_coaching_sessions": cfg.max_coaching_sessions,
            "max_resumes_stored": cfg.max_resumes_stored,
            "features": cfg.features,
        }
    return result


@router.get("/config")
async def get_token_config() -> Dict[str, Any]:
    plans = _get_plans_from_config()
    return {"plans": plans, "as_of": datetime.now(timezone.utc).isoformat()}


@router.put("/config")
async def put_token_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate submitted plan config against canonical plan_config.py.
    NOTE: Plans are defined in plan_config.py; this endpoint validates
    but does not persist overrides (future: DB-backed plan overrides).
    """
    plans = payload.get("plans")
    if not isinstance(plans, dict) or not plans:
        raise HTTPException(status_code=400, detail="Payload must include non-empty 'plans' dict.")

    canonical = _get_plans_from_config()
    plan_keys = tuple(canonical.keys())
    missing = [k for k in plan_keys if k not in plans]
    extra = [k for k in plans.keys() if k not in plan_keys]
    if missing:
        raise HTTPException(status_code=400, detail=f"Plans missing required keys: {missing}")
    if extra:
        raise HTTPException(status_code=400, detail=f"Plans include unknown keys: {extra}")

    for k, cfg in plans.items():
        if int(cfg.get("included_tokens_per_month", 0)) < 0:
            raise HTTPException(status_code=400, detail=f"{k}.included_tokens_per_month must be >= 0")

    return {"plans": plans, "validated_at": datetime.now(timezone.utc).isoformat(), "note": "Plan definitions are managed in plan_config.py"}


@router.get("/usage")
async def get_token_usage(month: Optional[str] = None, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Query credit usage from the DB-backed CreditUsageLog."""
    _get_plans_from_config()  # ensure plans are loadable

    query = db.query(models.CreditUsageLog)
    if month:
        query = query.filter(models.CreditUsageLog.created_at.like(f"{month}%"))
    rows = query.order_by(models.CreditUsageLog.created_at.desc()).limit(500).all()

    usage = []
    for r in rows:
        usage.append({
            "user_id": r.user_id,
            "action_id": r.action_id,
            "credits_consumed": r.credits_consumed,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"usage": usage, "count": len(usage), "month": month or "all"}
