"""
Market Signal Router — Live market traction data (spec §16 / §20).

Routes:
  POST /api/market/v1/signal — return market demand signals for a cluster
"""
from __future__ import annotations

from fastapi import APIRouter

from services.backend_api.models.career_compass_schemas import (
    MarketSignalRequest,
    MarketSignalResponse,
)
from services.backend_api.services.career.career_compass_engine import CareerCompassEngine

router = APIRouter(prefix="/api/market/v1", tags=["market-signal"])

_engine = CareerCompassEngine()


@router.post("/signal", response_model=MarketSignalResponse)
async def get_market_signal(payload: MarketSignalRequest):
    """Return market demand metrics for a target cluster (spec §16)."""
    return await _engine.get_market_signal(
        user_id=payload.user_id,
        cluster_id=payload.cluster_id,
        region=payload.region,
    )
