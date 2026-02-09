"""
backend/api/routes/admin_tokens.py

Admin token configuration + usage endpoints.

NOTE: This file is a wiring scaffold for contracts + validation.
You MUST replace TokenStore with your real DB/meters immediately.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/admin/v1/tokens", tags=["admin-tokens"])

# REQUIRED plan keys (must match user portal)
PLAN_KEYS = ("free", "monthly", "annual", "elitepro")


@dataclass
class TokenStore:
    # Replace with DB tables:
    # - token_plans
    # - token_usage_ledger
    plans: Dict[str, Dict[str, Any]]
    # Replace with query results (monthly rollup)
    usage_rows: List[Dict[str, Any]]


# ---- IMPORTANT ----
# This store is empty by default and will throw 500 until you wire real storage.
STORE = TokenStore(plans={}, usage_rows=[])


def _require_plans() -> Dict[str, Any]:
    if not STORE.plans:
        raise HTTPException(
            status_code=500,
            detail="Token plans are not configured in backend storage yet.",
        )
    missing = [k for k in PLAN_KEYS if k not in STORE.plans]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Token plans missing required keys: {missing}",
        )
    return STORE.plans


@router.get("/config")
async def get_token_config() -> Dict[str, Any]:
    plans = _require_plans()
    return {"plans": plans, "as_of": datetime.utcnow().isoformat()}


@router.put("/config")
async def put_token_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    plans = payload.get("plans")
    if not isinstance(plans, dict) or not plans:
        raise HTTPException(status_code=400, detail="Payload must include non-empty 'plans' dict.")

    # Validate keys
    missing = [k for k in PLAN_KEYS if k not in plans]
    extra = [k for k in plans.keys() if k not in PLAN_KEYS]
    if missing:
        raise HTTPException(status_code=400, detail=f"Plans missing required keys: {missing}")
    if extra:
        raise HTTPException(status_code=400, detail=f"Plans include unknown keys: {extra}")

    # Basic value checks
    for k, cfg in plans.items():
        if int(cfg.get("included_tokens_per_month", 0)) < 0:
            raise HTTPException(status_code=400, detail=f"{k}.included_tokens_per_month must be >= 0")

    STORE.plans = plans
    return {"plans": STORE.plans, "saved_at": datetime.utcnow().isoformat()}


@router.get("/usage")
async def get_token_usage(month: Optional[str] = None) -> Dict[str, Any]:
    _require_plans()

    if not STORE.usage_rows:
        raise HTTPException(
            status_code=500,
            detail="Token usage ledger is empty/unwired. Populate from real metering store.",
        )

    rows = STORE.usage_rows
    if month:
        rows = [r for r in rows if str(r.get("month")) == month]

    if not rows:
        raise HTTPException(status_code=404, detail="No usage rows for requested month.")

    return {"orgs": rows, "month": month or "current"}
