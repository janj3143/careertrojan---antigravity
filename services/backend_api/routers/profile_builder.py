"""
Profile Builder Router — Build CV Profile text from differentiators (spec §27.3 / §20).

Routes:
  POST /api/profile/v1/build   — transform differentiators into profile paragraph
  POST /api/profile/v1/signals — extract axis signals from differentiators
"""
from __future__ import annotations

from fastapi import APIRouter

from services.backend_api.models.career_compass_schemas import (
    BuildProfileRequest,
    BuildProfileResponse,
    SignalExtractionRequest,
    SignalExtractionResponse,
)
from services.backend_api.services.career.profile_builder_service import ProfileBuilderService
from services.backend_api.services.career.signal_extraction_service import SignalExtractionService

router = APIRouter(prefix="/api/profile/v1", tags=["profile-builder"])

_builder = ProfileBuilderService()
_signals = SignalExtractionService()


@router.post("/build", response_model=BuildProfileResponse)
async def build_profile(payload: BuildProfileRequest):
    """Transform differentiator bullets into a CV Profile paragraph (spec §27.3)."""
    return await _builder.build(payload)


@router.post("/signals", response_model=SignalExtractionResponse)
async def extract_signals(payload: SignalExtractionRequest):
    """Extract enriched signals from differentiators for vector generation (spec §13)."""
    return await _signals.extract(payload)
