"""
Pydantic schemas for Career Compass + Profile Coach + User Vector modules.
Canonical envelope pattern per spec §4 / §15.1.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Shared Provenance Envelope ──────────────────────────────────────

class SourceSummary(BaseModel):
    """Provenance block attached to every analytical response (spec §23)."""
    request_id: Optional[str] = None
    resume_id: Optional[str] = None
    profile_response_count: Optional[int] = None
    cluster_record_count: Optional[int] = None
    job_records_analyzed: Optional[int] = None
    mentor_records_scanned: Optional[int] = None
    model_version: Optional[str] = None
    engine_version: Optional[str] = None


class StandardResponse(BaseModel):
    """Canonical API response envelope (spec §15.1)."""
    status: str = Field(
        ...,
        description=(
            "ok | processing | missing_resume | missing_profile_enrichment | "
            "missing_cluster | missing_market_data | missing_mentor_data | "
            "insufficient_live_records | model_unavailable | error"
        ),
    )
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    source_summary: Optional[SourceSummary] = None
    generated_at: Optional[str] = None


# ── Profile Coach Schemas (spec §10 / §12) ─────────────────────────

class ProfileCoachStartRequest(BaseModel):
    user_id: str
    resume_id: str
    user_name: Optional[str] = None


class ProfileCoachResponseRequest(BaseModel):
    user_id: str
    session_id: str
    answer: str


class ProfileCoachFinishRequest(BaseModel):
    user_id: str
    session_id: str


class ProfileCoachTurnResponse(BaseModel):
    status: str
    session_id: str
    question: Optional[str] = None
    mirrored_points: List[str] = []
    stop_detected: bool = False
    source_summary: Optional[SourceSummary] = None


class ProfileCoachFinishResponse(BaseModel):
    status: str
    session_id: str
    differentiators: List[str] = []
    source_summary: Optional[SourceSummary] = None


# ── Profile Builder Schemas (spec §27.3) ───────────────────────────

class BuildProfileRequest(BaseModel):
    user_id: str
    resume_id: str
    differentiators: List[str]


class BuildProfileResponse(BaseModel):
    status: str
    profile_text: Optional[str] = None
    source_summary: Optional[SourceSummary] = None


# ── User Vector Schemas (spec §14) ─────────────────────────────────

class UserVectorResponse(BaseModel):
    status: str
    vector: Optional[Dict[str, float]] = None
    confidence: Optional[Dict[str, float]] = None
    vector_version: Optional[str] = None
    feature_set_version: Optional[str] = None
    resume_id: Optional[str] = None
    computed_at: Optional[str] = None
    source_summary: Optional[SourceSummary] = None


# ── Career Compass Schemas (spec §9 / §15 / §16 / §17) ────────────

class CareerMapNode(BaseModel):
    cluster_id: str
    label: str
    route_type: Optional[str] = None  # natural_next_step | strategic_stretch | too_far_for_now
    x: float
    y: float


class CareerMapResponse(BaseModel):
    status: str
    nodes: List[CareerMapNode] = []
    source_summary: Optional[SourceSummary] = None
    generated_at: Optional[str] = None


class ClusterProfileResponse(BaseModel):
    status: str
    cluster_id: str
    title: Optional[str] = None
    summary: Optional[Dict[str, str]] = None
    vector: Optional[Dict[str, float]] = None
    source_summary: Optional[SourceSummary] = None


class SpiderOverlayRequest(BaseModel):
    user_id: str
    resume_id: str
    cluster_id: str


class SpiderOverlayResponse(BaseModel):
    status: str
    user_vector: Optional[Dict[str, float]] = None
    target_vector: Optional[Dict[str, float]] = None
    gap_vector: Optional[Dict[str, float]] = None
    strengths: List[str] = []
    gaps: List[str] = []
    source_summary: Optional[SourceSummary] = None


class CareerRoutesResponse(BaseModel):
    status: str
    natural_next_steps: List[str] = []
    strategic_stretch: List[str] = []
    too_far_for_now: List[str] = []
    source_summary: Optional[SourceSummary] = None


class CulDeSacCheckRequest(BaseModel):
    cluster_id: str


class CulDeSacCheckResponse(BaseModel):
    status: str
    risk_level: Optional[str] = None  # high_mobility | moderate_mobility | culdesac_risk
    reasons: List[str] = []
    source_summary: Optional[SourceSummary] = None


class SaveScenarioRequest(BaseModel):
    user_id: str
    resume_id: str
    cluster_id: str
    scenario_key: Optional[str] = None
    notes: Optional[str] = None


class SaveScenarioResponse(BaseModel):
    status: str
    scenario_id: Optional[str] = None
    source_summary: Optional[SourceSummary] = None


# ── Runway Schemas (spec §18 – Market Traction + Runway) ───────────

class CareerRunwayRequest(BaseModel):
    user_id: str
    resume_id: str
    cluster_id: str


class CareerRunwayStep(BaseModel):
    step_number: int
    title: str
    detail: str


class CareerRunwayResponse(BaseModel):
    status: str
    steps: List[CareerRunwayStep] = []
    source_summary: Optional[SourceSummary] = None


# ── Mentor Match Schemas (spec §17) ────────────────────────────────

class CareerMentorMatchRequest(BaseModel):
    user_id: str
    resume_id: str
    cluster_id: str


class CareerMentor(BaseModel):
    mentor_id: str
    name: str
    match_reason: Optional[str] = None


class CareerMentorMatchResponse(BaseModel):
    status: str
    mentors: List[CareerMentor] = []
    source_summary: Optional[SourceSummary] = None


# ── Market Signal Schemas (spec §16) ───────────────────────────────

class MarketSignalRequest(BaseModel):
    user_id: str
    cluster_id: str
    region: Optional[str] = None


class MarketSignalResponse(BaseModel):
    status: str
    metrics: Optional[Dict[str, float]] = None
    recurring_skills: List[str] = []
    source_summary: Optional[SourceSummary] = None


# ── Mentor Search Schemas ──────────────────────────────────────────

class MentorSearchRequest(BaseModel):
    user_id: str
    gap_axes: Optional[List[str]] = None
    region: Optional[str] = None


class MentorSearchResponse(BaseModel):
    status: str
    mentors: List[CareerMentor] = []
    source_summary: Optional[SourceSummary] = None


# ── Signal Extraction Schemas (spec §13) ───────────────────────────

class SignalExtractionRequest(BaseModel):
    user_id: str
    resume_id: str
    differentiators: List[str] = []


class SignalExtractionResponse(BaseModel):
    status: str
    signals: Dict[str, float] = {}
    source_summary: Optional[SourceSummary] = None
