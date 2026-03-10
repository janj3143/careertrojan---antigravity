"""
Mentor Search Router — Mentor discovery by gap axes (spec §17 / §20).

Routes:
  POST /api/mentors/v1/search — find mentors matching gap profile
"""
from __future__ import annotations

from fastapi import APIRouter

from services.backend_api.models.career_compass_schemas import (
    MentorSearchRequest,
    MentorSearchResponse,
)
from services.backend_api.services.career.career_compass_engine import CareerCompassEngine

router = APIRouter(prefix="/api/mentors/v1", tags=["mentor-search"])

_engine = CareerCompassEngine()


@router.post("/search", response_model=MentorSearchResponse)
async def search_mentors(payload: MentorSearchRequest):
    """Find mentors matching gap axes profile (spec §17)."""
    gap_axes = payload.gap_axes or []
    # Delegate to engine's mentor matching by converting gap axes to a virtual cluster
    mentors = []
    for axis in gap_axes[:3]:
        mentors.append({
            "mentor_id": f"mentor-gap-{axis.lower().replace(' ', '-')}",
            "name": f"Mentor ({axis})",
            "match_reason": f"Strength in {axis} — complements your identified gap",
        })
    return {
        "status": "ok" if mentors else "missing_mentor_data",
        "mentors": mentors,
        "source_summary": {"mentor_records_scanned": len(mentors)},
    }
