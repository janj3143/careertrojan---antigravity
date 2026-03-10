"""
Career Compass Router — Core navigation engine (spec §9/§15/§16/§17/§18/§20).

Routes:
  GET  /api/career-compass/v1/map                — career map nodes
  GET  /api/career-compass/v1/cluster/{id}        — cluster profile detail
  POST /api/career-compass/v1/spider-overlay       — spider overlay (user vs target)
  GET  /api/career-compass/v1/routes              — route classification
  POST /api/career-compass/v1/culdesac-check       — cul-de-sac risk assessment
  POST /api/career-compass/v1/runway              — runway plan (gap → steps)
  POST /api/career-compass/v1/mentor-match        — mentor matching
  POST /api/career-compass/v1/save-scenario       — save/bookmark a scenario
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from services.backend_api.models.career_compass_schemas import (
    CareerMapResponse,
    ClusterProfileResponse,
    SpiderOverlayRequest,
    SpiderOverlayResponse,
    CareerRoutesResponse,
    CulDeSacCheckRequest,
    CulDeSacCheckResponse,
    CareerRunwayRequest,
    CareerRunwayResponse,
    CareerMentorMatchRequest,
    CareerMentorMatchResponse,
    SaveScenarioRequest,
    SaveScenarioResponse,
)
from services.backend_api.services.career.career_compass_engine import CareerCompassEngine

router = APIRouter(prefix="/api/career-compass/v1", tags=["career-compass"])

_engine = CareerCompassEngine()


@router.get("/map", response_model=CareerMapResponse)
async def get_career_map(
    user_id: str = Query(None),
    resume_id: str = Query(None),
):
    """Return career map with all cluster nodes (spec §9.1 / §20)."""
    return await _engine.get_map(user_id=user_id, resume_id=resume_id)


@router.get("/cluster/{cluster_id}", response_model=ClusterProfileResponse)
async def get_cluster_profile(cluster_id: str):
    """Return detailed profile of a single cluster (spec §9.2)."""
    return await _engine.get_cluster_profile(cluster_id)


@router.post("/spider-overlay", response_model=SpiderOverlayResponse)
async def get_spider_overlay(payload: SpiderOverlayRequest):
    """User vector vs cluster target — gap analysis (spec §9.3)."""
    return await _engine.get_spider_overlay(
        user_id=payload.user_id,
        resume_id=payload.resume_id,
        cluster_id=payload.cluster_id,
    )


@router.get("/routes", response_model=CareerRoutesResponse)
async def get_career_routes(
    user_id: str = Query(None),
    resume_id: str = Query(None),
):
    """Natural-next / strategic-stretch / too-far classification (spec §9.4)."""
    return await _engine.get_routes(user_id=user_id, resume_id=resume_id)


@router.post("/culdesac-check", response_model=CulDeSacCheckResponse)
async def check_culdesac(payload: CulDeSacCheckRequest):
    """Cul-de-sac risk assessment for a cluster (spec §9.5)."""
    return await _engine.check_culdesac(payload.cluster_id)


@router.post("/runway", response_model=CareerRunwayResponse)
async def get_runway(payload: CareerRunwayRequest):
    """Runway plan — concrete steps to close gap (spec §18)."""
    return await _engine.get_runway(
        user_id=payload.user_id,
        resume_id=payload.resume_id,
        cluster_id=payload.cluster_id,
    )


@router.post("/mentor-match", response_model=CareerMentorMatchResponse)
async def get_mentor_match(payload: CareerMentorMatchRequest):
    """Mentor matching for a target cluster (spec §17)."""
    return await _engine.get_mentor_matches(
        user_id=payload.user_id,
        resume_id=payload.resume_id,
        cluster_id=payload.cluster_id,
    )


@router.post("/save-scenario", response_model=SaveScenarioResponse)
async def save_scenario(payload: SaveScenarioRequest):
    """Bookmark / save a what-if scenario (spec §15.6)."""
    return await _engine.save_scenario(payload)
