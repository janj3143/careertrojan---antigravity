from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json

from services.backend_api.utils import security
from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.services.career.interview_coach_service import (
    generate_interview_questions,
    review_interview_answer,
    generate_star_stories,
    infer_role_family,
    record_interview_feedback,
    get_learning_profile,
)
from services.backend_api.services.interview_coaching_service import (
    get_interview_coaching_service,
)

try:
    from services.backend_api.services.career.career_coach import (
        get_career_coach_recommendations,
    )
    COACH_SERVICE_AVAILABLE = True
except Exception:
    get_career_coach_recommendations = None  # type: ignore
    COACH_SERVICE_AVAILABLE = False

try:
    import services.backend_api.services.industry_taxonomy_service as _tax
    _TAXONOMY_AVAILABLE = True
except Exception:
    _tax = None  # type: ignore
    _TAXONOMY_AVAILABLE = False


router = APIRouter(
    prefix="/api/coaching/v1",
    tags=["coaching"],
)


class ApplicationEntry(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None


class CoachingRequest(BaseModel):
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    resume_data: Dict[str, Any] = Field(default_factory=dict)
    job_data: Optional[Dict[str, Any]] = None
    applications: Optional[List[ApplicationEntry]] = None


class CoachingResponse(BaseModel):
    recommendations: Dict[str, Any]
    insights: Optional[Any] = None


def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except security.TokenValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_id(current_user: models.User = Depends(get_current_user)) -> str:
    return str(current_user.id)


def build_taxonomy_context_from_resume(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    if not _TAXONOMY_AVAILABLE or not resume_data:
        return {}

    roles = (
        resume_data.get("work_experience")
        or resume_data.get("roles")
        or resume_data.get("experience")
        or []
    )
    if not isinstance(roles, list) or not roles:
        return {}

    titles: List[str] = []
    for r in roles:
        title = (r.get("title") or "").strip()
        if title:
            titles.append(title)

    if not titles:
        return {}

    try:
        inferred_industries = _tax.infer_industries_from_titles(titles)  # type: ignore[attr-defined]
    except Exception:
        inferred_industries = []

    try:
        primary_naics = _tax.map_job_title_to_naics(titles[0], max_results=5)  # type: ignore[attr-defined]
    except Exception:
        primary_naics = []

    return {
        "recent_titles": titles,
        "inferred_industries": inferred_industries,
        "primary_naics": primary_naics,
    }


@router.post(
    "/bundle",
    response_model=CoachingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_coaching_bundle(
    payload: CoachingRequest,
    user_id: str = Depends(get_current_user_id),
) -> CoachingResponse:
    if not COACH_SERVICE_AVAILABLE or get_career_coach_recommendations is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Career coach service is not available on this deployment.",
        )

    applications: List[Dict[str, Any]] = [
        a.dict() for a in (payload.applications or [])
    ]

    taxonomy_context = build_taxonomy_context_from_resume(payload.resume_data)

    try:
        result = get_career_coach_recommendations(
            user_profile=payload.user_profile,
            resume_data=payload.resume_data,
            job_data=payload.job_data,
            applications=applications,
            extras={"taxonomy_context": taxonomy_context},
        )
    except TypeError:
        result = get_career_coach_recommendations(
            user_profile=payload.user_profile,
            resume_data=payload.resume_data,
            job_data=payload.job_data,
            applications=applications,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Career coaching failed: {e}",
        )

    if isinstance(result, dict) and "recommendations" in result:
        return CoachingResponse(
            recommendations=result.get("recommendations") or {},
            insights=result.get("insights"),
        )

    return CoachingResponse(
        recommendations=result or {},
        insights=None,
    )


@router.get("/health", status_code=status.HTTP_200_OK)
async def coaching_health() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "career_coaching",
        "taxonomy": "available" if _TAXONOMY_AVAILABLE else "unavailable",
        "coach_service": "available" if COACH_SERVICE_AVAILABLE else "unavailable",
    }


@router.get("/history")
def get_coaching_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interactions = (
        db.query(models.Interaction)
        .filter(
            models.Interaction.user_id == current_user.id,
            models.Interaction.action_type.in_(["coaching_session", "coaching"]),
        )
        .order_by(models.Interaction.created_at.desc())
        .limit(limit)
        .all()
    )

    history = []
    for entry in interactions:
        try:
            metadata = json.loads(entry.metadata_json) if entry.metadata_json else None
        except Exception:
            metadata = None

        history.append({
            "id": entry.id,
            "action_type": entry.action_type,
            "path": entry.path,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "metadata": metadata,
        })

    return {"history": history}

# --- Expanded Endpoints for Coaching Hub ---

class QuestionGenRequest(BaseModel):
    question_type: str
    count: int = 5
    resume: Optional[Dict[str, Any]] = None
    job: Optional[Dict[str, Any]] = None
    fit: Optional[Dict[str, Any]] = None

class AnswerReviewRequest(BaseModel):
    question: str
    answer: str
    resume: Optional[Dict[str, Any]] = None
    job: Optional[Dict[str, Any]] = None

class StarStoryRequest(BaseModel):
    focus_areas: List[str]
    resume: Optional[Dict[str, Any]] = None
    job: Optional[Dict[str, Any]] = None


class InterviewLearningFeedbackRequest(BaseModel):
    question_type: str = "Role-specific"
    question: str
    helpful: Optional[bool] = None
    answer_score: Optional[int] = None
    session_outcome: Optional[str] = None
    resume: Optional[Dict[str, Any]] = None
    job: Optional[Dict[str, Any]] = None


class RoleDetectionRequest(BaseModel):
    job_data: Optional[Dict[str, Any]] = None
    resume_data: Optional[Dict[str, Any]] = None
    resume_experience: Optional[List[Dict[str, Any]]] = None


class NinetyDayPlanRequest(BaseModel):
    role_function: str = "EXEC"
    seniority: str = "mid"


def _require_ai_service():
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Coaching AI service is not configured",
    )

@router.post("/questions/generate")
async def generate_questions(payload: QuestionGenRequest):
    try:
        questions = generate_interview_questions(
            question_type=payload.question_type,
            count=payload.count,
            resume=payload.resume,
            job=payload.job,
            fit=payload.fit,
        )
        return questions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question generation failed: {e}",
        )


@router.post("/answers/review")
async def review_answer(payload: AnswerReviewRequest):
    try:
        feedback = review_interview_answer(
            question=payload.question,
            answer=payload.answer,
            resume=payload.resume,
            job=payload.job,
        )
        return feedback
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Answer review failed: {e}",
        )

@router.post("/stories/generate")
async def generate_stories(payload: StarStoryRequest):
    try:
        stories = generate_star_stories(
            focus_areas=payload.focus_areas,
            resume=payload.resume,
            job=payload.job,
        )
        return stories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STAR story generation failed: {e}",
        )


@router.post("/learning/feedback")
async def submit_interview_learning_feedback(
    payload: InterviewLearningFeedbackRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        role_family = infer_role_family(payload.resume, payload.job)
        return record_interview_feedback(
            role_family=role_family,
            question_type=payload.question_type,
            question=payload.question,
            answer_score=payload.answer_score,
            helpful=payload.helpful,
            session_outcome=payload.session_outcome,
            user_id=user_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Learning feedback failed: {e}",
        )


@router.get("/learning/profile")
async def fetch_interview_learning_profile(
    role_family: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
):
    try:
        return {
            "user_id": user_id,
            "profile": get_learning_profile(role_family=role_family),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Learning profile fetch failed: {e}",
        )


@router.post("/role/detect")
async def detect_role(payload: RoleDetectionRequest):
    try:
        service = get_interview_coaching_service()
        return service.detect_role_function(
            job_data=payload.job_data,
            resume_data=payload.resume_data,
            resume_experience=payload.resume_experience,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Role detection failed: {e}",
        )


@router.post("/plan/90day")
async def generate_90day_plan(payload: NinetyDayPlanRequest):
    try:
        service = get_interview_coaching_service()
        return service.get_90day_plan(
            role_function=payload.role_function,
            seniority=payload.seniority,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"90-day plan generation failed: {e}",
        )
