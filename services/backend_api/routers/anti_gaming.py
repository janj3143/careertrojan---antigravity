from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.backend_api.services.abuse_policy_service import AbusePolicyService
from services.backend_api.services.resume_store import ResumeStore

router = APIRouter(prefix="/api/admin/v1/anti-gaming", tags=["anti-gaming"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # .../backend/api/routes -> project root
store = ResumeStore(PROJECT_ROOT)
policy = AbusePolicyService()


class GateIn(BaseModel):
    user_id: str
    account_type: str = "individual"
    raw_text: str = Field(..., min_length=50)
    parsed: Dict[str, Any] = Field(default_factory=dict)
    requested_status: str = "active"  # "active" | "master" | "pending"


class GateOut(BaseModel):
    decision: str
    risk_score: int
    reason_codes: list[str]
    cooldown_until: Optional[str] = None
    stored_status: str
    resume_id: str


@router.post("/check", response_model=GateOut)
def check(payload: GateIn):
    last_master = store.get_latest_by_status(payload.user_id, "master")
    last_active = store.get_latest_by_status(payload.user_id, "active")
    recent = store.list_upload_timestamps(payload.user_id)

    fp = policy.build_fingerprint(payload.raw_text, payload.parsed)
    decision = policy.evaluate(
        account_type=payload.account_type,
        new_fp=fp,
        recent_upload_timestamps=recent,
        last_master_fp=last_master.fingerprint if last_master else None,
        last_active_fp=last_active.fingerprint if last_active else None,
    )

    if decision.decision in ("quarantine", "cooldown"):
        stored_status = "pending"
    else:
        stored_status = payload.requested_status if payload.requested_status in ("active", "master") else "pending"

    stored = store.save(
        user_id=payload.user_id,
        status=stored_status,
        fingerprint=fp,
        abuse={
            "decision": decision.decision,
            "risk_score": decision.risk_score,
            "reason_codes": decision.reason_codes,
            "cooldown_until": decision.cooldown_until.isoformat() if decision.cooldown_until else None,
        },
        parsed=payload.parsed,
        raw_text=payload.raw_text,
    )

    return GateOut(
        decision=decision.decision,
        risk_score=decision.risk_score,
        reason_codes=decision.reason_codes,
        cooldown_until=decision.cooldown_until.isoformat() if decision.cooldown_until else None,
        stored_status=stored_status,
        resume_id=stored.resume_id,
    )
