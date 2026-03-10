"""
User Vector Router — Skill vector retrieval (spec §14 / §20).

Routes:
  GET /api/user-vector/v1/current — return current user skill vector (10 axes)
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from services.backend_api.models.career_compass_schemas import UserVectorResponse
from services.backend_api.services.career.user_vector_service import UserVectorService

router = APIRouter(prefix="/api/user-vector/v1", tags=["user-vector"])

_svc = UserVectorService()


@router.get("/current", response_model=UserVectorResponse)
async def get_user_vector(
    user_id: str = Query(...),
    resume_id: str = Query(...),
):
    """Return current 10-axis user skill vector with confidence (spec §14)."""
    return await _svc.get_current_vector(user_id=user_id, resume_id=resume_id)
