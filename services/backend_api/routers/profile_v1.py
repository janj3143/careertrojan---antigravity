from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.backend_api.routers.career_compass import _vector_from_text
from services.backend_api.routers.runtime_contract import respond
from services.shared.paths import CareerTrojanPaths


router = APIRouter(prefix="/api/v1/profile", tags=["profile-v1"])


class BuildProfileRequest(BaseModel):
    user_id: int
    resume_id: int
    differentiators: List[str] = Field(default_factory=list)


class BuildSignalsRequest(BaseModel):
    user_id: int
    resume_id: int
    profile_text: Optional[str] = None
    differentiators: List[str] = Field(default_factory=list)


def _profile_store_path(user_id: int, resume_id: int):
    base = CareerTrojanPaths().user_data / "profiles"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"profile_{user_id}_{resume_id}.json"


@router.post("/build")
def build_profile(payload: BuildProfileRequest):
    if not payload.differentiators:
        return respond(
            status="missing_profile_enrichment",
            message="Differentiator inputs are required to build profile text.",
            data={"profile_text": None},
            source_summary={
                "resume_id": str(payload.resume_id),
                "profile_response_count": 0,
            },
        )

    profile_text = " ".join([point.strip() for point in payload.differentiators if point.strip()])
    target_file = _profile_store_path(payload.user_id, payload.resume_id)
    target_file.write_text(
        json.dumps(
            {
                "user_id": payload.user_id,
                "resume_id": payload.resume_id,
                "profile_text": profile_text,
                "differentiators": payload.differentiators,
                "updated_at": datetime.utcnow().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return respond(
        status="ok",
        data={"profile_text": profile_text},
        source_summary={
            "resume_id": str(payload.resume_id),
            "profile_response_count": len(payload.differentiators),
        },
    )


@router.post("/signals")
def build_profile_signals(payload: BuildSignalsRequest):
    source_text = (payload.profile_text or "").strip()
    if not source_text and payload.differentiators:
        source_text = " ".join([value.strip() for value in payload.differentiators if value.strip()])

    if not source_text:
        return respond(
            status="missing_profile_enrichment",
            message="Profile text or differentiators are required for signal extraction.",
            data={"signals": {}},
            source_summary={
                "resume_id": str(payload.resume_id),
                "profile_response_count": 0,
            },
        )

    signals: Dict[str, float] = _vector_from_text(source_text)

    return respond(
        status="ok",
        data={"signals": signals},
        source_summary={
            "resume_id": str(payload.resume_id),
            "profile_response_count": len(payload.differentiators),
        },
    )
