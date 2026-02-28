"""
AI Gateway Router — REST API for unified AI operations
=======================================================

Exposes the AI Gateway through HTTP endpoints.

Endpoints:
  POST /ai/generate      - Text generation (LLM)
  POST /ai/score         - Candidate/resume scoring
  POST /ai/classify      - Category classification
  POST /ai/extract       - Entity extraction
  POST /ai/match         - Job-candidate matching
  POST /ai/feedback      - Record outcome for ground truth
  GET  /ai/health        - Gateway health status
  POST /ai/baseline      - Set drift detection baseline
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import logging

from services.backend_api.utils.auth_deps import get_current_user
from services.backend_api.db import models as db_models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Gateway"], dependencies=[Depends(get_current_user)])


# ── Credit enforcement helper ────────────────────────────────────────────

def _enforce_credits(user: db_models.User, action_id: str, context: dict | None = None) -> dict:
    """Consume credits for an AI action; raise HTTP 402 if insufficient."""
    from services.backend_api.services.credit_system import get_credit_manager
    mgr = get_credit_manager()
    result = mgr.consume_credits(str(user.id), action_id, context=context)
    if not result["success"]:
        raise HTTPException(status_code=402, detail=result)
    return result


# ══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ══════════════════════════════════════════════════════════════════════════

class GenerateRequest(BaseModel):
    """Request for text generation."""
    prompt: str = Field(..., description="The prompt to generate text from")
    provider: Optional[str] = Field(None, description="LLM provider (openai, anthropic, etc.)")
    max_tokens: int = Field(1000, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    context: Dict[str, Any] = Field(default_factory=dict)


class ScoreRequest(BaseModel):
    """Request for candidate scoring."""
    resume_text: str = Field(..., description="Full resume text")
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    education: Optional[str] = Field(None)
    job_description: Optional[str] = Field(None)


class ClassifyRequest(BaseModel):
    """Request for text classification."""
    text: str = Field(..., description="Text to classify")
    category_type: str = Field("industry", description="Type: industry, job_level, job_function")


class ExtractRequest(BaseModel):
    """Request for entity extraction."""
    text: str = Field(..., description="Text to extract from")
    extraction_type: str = Field("skills", description="Type: skills, entities, contact, experience")


class MatchRequest(BaseModel):
    """Request for job-candidate matching."""
    candidate: Dict[str, Any] = Field(..., description="Candidate profile")
    job: Dict[str, Any] = Field(..., description="Job requirements")


class FeedbackRequest(BaseModel):
    """Request to record outcome feedback."""
    ground_truth_id: str = Field(..., description="ID from original prediction")
    outcome_type: str = Field(..., description="Type: interview, ats_pass, user_accepted, hired")
    outcome_value: Any = Field(..., description="The actual outcome value")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GatewayResponseModel(BaseModel):
    """Standard gateway response."""
    request_id: str
    task_type: str
    result: Any
    confidence: float
    calibrated_confidence: float
    route_taken: str
    engines_consulted: List[str]
    ground_truth_id: Optional[str]
    drift_flags: List[str]
    warnings: List[str]
    success: bool
    error: Optional[str]
    latency_ms: float


# ══════════════════════════════════════════════════════════════════════════
# Gateway Instance
# ══════════════════════════════════════════════════════════════════════════

def get_ai_gateway():
    """Dependency to get the AI gateway instance."""
    try:
        from services.ai_engine.ai_gateway import ai_gateway
        return ai_gateway
    except ImportError as e:
        logger.error("Failed to import AI Gateway: %s", e)
        raise HTTPException(status_code=503, detail="AI Gateway not available")


# ══════════════════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.post("/generate", response_model=GatewayResponseModel)
async def generate(
    request: GenerateRequest,
    gateway = Depends(get_ai_gateway),
    user: db_models.User = Depends(get_current_user),
):
    """
    Generate text using LLM.
    
    Use cases:
      - Resume bullet improvement
      - Cover letter generation
      - Interview question suggestions
    """
    _enforce_credits(user, "ai_coaching_session", context={"prompt_len": len(request.prompt)})
    try:
        response = gateway.generate(
            prompt=request.prompt,
            context=request.context,
            provider=request.provider,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        return GatewayResponseModel(**response.to_dict())
    except Exception as e:
        logger.error("Generate failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score", response_model=GatewayResponseModel)
async def score_candidate(
    request: ScoreRequest,
    gateway = Depends(get_ai_gateway),
    user: db_models.User = Depends(get_current_user),
):
    """
    Score a candidate/resume using ensemble ML models.
    
    Returns:
      - match_score (0-100)
      - predicted_industry
      - predicted_seniority
      - quality_tier
      - recommendations
    """
    _enforce_credits(user, "fit_analysis_full")
    try:
        response = gateway.score_candidate(
            resume_text=request.resume_text,
            skills=request.skills,
            experience_years=request.experience_years,
            education=request.education,
            job_description=request.job_description,
        )
        return GatewayResponseModel(**response.to_dict())
    except Exception as e:
        logger.error("Score failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify", response_model=GatewayResponseModel)
async def classify(
    request: ClassifyRequest,
    gateway = Depends(get_ai_gateway),
    user: db_models.User = Depends(get_current_user),
):
    """
    Classify text into categories.
    
    Category types:
      - industry: Tech, Finance, Healthcare, etc.
      - job_level: Entry, Mid, Senior, Executive
      - job_function: Engineering, Sales, Marketing, etc.
    """
    _enforce_credits(user, "career_analysis_full")
    try:
        response = gateway.classify(
            text=request.text,
            category_type=request.category_type,
        )
        return GatewayResponseModel(**response.to_dict())
    except Exception as e:
        logger.error("Classify failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=GatewayResponseModel)
async def extract(
    request: ExtractRequest,
    gateway = Depends(get_ai_gateway),
    user: db_models.User = Depends(get_current_user),
):
    """
    Extract structured data from text.
    
    Extraction types:
      - skills: Technical and soft skills
      - entities: Named entities (companies, locations)
      - contact: Emails, phones
      - experience: Job history
    """
    _enforce_credits(user, "career_analysis_full")
    try:
        response = gateway.extract(
            text=request.text,
            extraction_type=request.extraction_type,
        )
        return GatewayResponseModel(**response.to_dict())
    except Exception as e:
        logger.error("Extract failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match", response_model=GatewayResponseModel)
async def match(
    request: MatchRequest,
    gateway = Depends(get_ai_gateway),
    user: db_models.User = Depends(get_current_user),
):
    """
    Match a candidate to job requirements.
    
    Returns:
      - match_score
      - skill_gaps
      - recommendations
    """
    _enforce_credits(user, "fit_analysis_full")
    try:
        response = gateway.match(
            candidate_profile=request.candidate,
            job_requirements=request.job,
        )
        return GatewayResponseModel(**response.to_dict())
    except Exception as e:
        logger.error("Match failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def record_feedback(
    request: FeedbackRequest,
    gateway = Depends(get_ai_gateway),
):
    """
    Record outcome feedback for ground truth loop.
    
    Call this when you learn the actual outcome of a prediction:
      - User accepted/rejected suggestion
      - Resume passed ATS
      - Candidate got interview
      - Candidate got hired
    
    This feedback improves model calibration over time.
    """
    try:
        success = gateway.record_outcome(
            ground_truth_id=request.ground_truth_id,
            outcome_type=request.outcome_type,
            outcome_value=request.outcome_value,
            metadata=request.metadata,
        )
        return {
            "success": success,
            "message": "Outcome recorded" if success else "Failed to record outcome",
        }
    except Exception as e:
        logger.error("Feedback failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health(
    gateway = Depends(get_ai_gateway),
):
    """
    Get gateway health and metrics.
    
    Returns:
      - Backend availability
      - Request/error counts
      - Average latency
      - Drift detection status
      - Ground truth stats
    """
    return gateway.health()


@router.post("/baseline")
async def set_baseline(
    gateway = Depends(get_ai_gateway),
):
    """
    Set drift detection baseline.
    
    Call this during healthy operation to capture baseline metrics.
    Future requests will be compared against this baseline to detect drift.
    """
    result = gateway.set_drift_baseline()
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {
        "success": True,
        "baseline": result,
    }


# ══════════════════════════════════════════════════════════════════════════
# Advanced Endpoints
# ══════════════════════════════════════════════════════════════════════════

@router.post("/batch/score")
async def batch_score(
    candidates: List[ScoreRequest] = Body(...),
    gateway = Depends(get_ai_gateway),
    user: db_models.User = Depends(get_current_user),
):
    """
    Score multiple candidates in batch.
    
    More efficient than individual calls for bulk operations.
    """
    # Enforce credits for each candidate in batch
    for _ in candidates:
        _enforce_credits(user, "fit_analysis_full")
    results = []
    for candidate in candidates:
        try:
            response = gateway.score_candidate(
                resume_text=candidate.resume_text,
                skills=candidate.skills,
                experience_years=candidate.experience_years,
                education=candidate.education,
                job_description=candidate.job_description,
            )
            results.append({"success": True, "data": response.to_dict()})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    return {
        "total": len(candidates),
        "successful": sum(1 for r in results if r["success"]),
        "results": results,
    }


@router.get("/routes")
async def get_routes():
    """
    Get current routing configuration.
    
    Shows which backends handle which task types.
    """
    try:
        from services.ai_engine.ai_gateway import ai_gateway
        return {
            "default_routes": {
                k.value: v for k, v in ai_gateway.routing_policy._default_routes.items()
            },
            "cost_weights": ai_gateway.routing_policy._cost_weights,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NOTE: /drift/stats moved to admin_ai_control_plane.py (canonical admin surface for drift monitoring)


@router.get("/calibration/curves")
async def get_calibration_curves(
    gateway = Depends(get_ai_gateway),
):
    """
    Get calibration curves learned from ground truth.
    """
    return {
        "curves": {
            k: [(float(r), float(c)) for r, c in v]
            for k, v in gateway.calibrator._calibration_curves.items()
        },
        "default_temperature": gateway.calibrator._default_temperature,
    }
