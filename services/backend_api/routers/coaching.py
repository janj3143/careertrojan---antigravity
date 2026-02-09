from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

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


def get_current_user_id() -> str:
    return "demo-user-id"


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


# Deterministic fallback (Ported from Legacy)
BASE_QUESTIONS = {
    "General competency": [
        "Tell me about yourself.",
        "What is your greatest strength?",
        "What is your greatest development area and how are you working on it?",
        "Describe a time you had to adapt to a major change.",
        "Where do you see yourself in 5 years?",
    ],
    "Role-specific": [
        "Walk me through a recent project that best reflects your fit for this role.",
        "How do you stay up to date with developments in this field?",
        "Describe a time you solved a role-specific problem from end to end.",
        "What tools and technologies do you prefer for this type of work?",
    ],
    "Culture & values": [
        "What kind of environment do you do your best work in?",
        "Tell me about a time you contributed to a positive team culture.",
        "Describe a time you disagreed with a decision and how you handled it.",
        "What values are most important to you in a workplace?",
    ],
    "Leadership": [
        "Tell me about a time you led a team through a challenging situation.",
        "How do you motivate others, even when you have no formal authority?",
        "Describe a difficult decision you had to make as a leader.",
        "How do you handle conflict within a team?",
    ],
    "Problem-solving": [
        "Describe a complex problem you faced and how you approached it.",
        "Tell me about a time something went wrong and you had to fix it quickly.",
        "Walk me through your process for diagnosing and resolving issues.",
        "Give an example of a creative solution you implemented.",
    ],
}

@router.post("/questions/generate")
async def generate_questions(payload: QuestionGenRequest):
    # In a full vLLM setup, we would call the LLM here.
    # For now, we return high-quality deterministic patterns + optional logic
    
    # Simple logic: If we have job context, maybe prepend a custom one
    pool = BASE_QUESTIONS.get(payload.question_type, BASE_QUESTIONS["General competency"])[:]
    
    if payload.job and "title" in payload.job:
        pool.insert(0, f"Why do you think you are a good fit for the {payload.job['title']} role?")
        
    return pool[:payload.count]


@router.post("/answers/review")
async def review_answer(payload: AnswerReviewRequest):
    # Simulated Feedback logic
    # In vLLM, we would prompt the model.
    
    length = len(payload.answer.split())
    if length < 20:
        return {
            "summary": "Your answer is quite short. Try to expand on the details.",
            "suggestions": ["Use the STAR method (Situation, Task, Action, Result).", "Provide specific metrics or outcomes."],
            "engine": "rule-based"
        }
    
    return {
        "summary": "Solid attempt. The structure is clear.",
        "suggestions": [
            "Ensure you clearly state your personal contribution ('I' vs 'We').",
            "Quantify the result if possible (e.g., 'improved by 20%')."
        ],
        "engine": "rule-based"
    }

@router.post("/stories/generate")
async def generate_stories(payload: StarStoryRequest):
    # Simulated STAR extraction
    return [
        {
            "title": "Project Leadership",
            "situation": "In my previous role, we faced a tight deadline...",
            "task": "I needed to coordinate across three teams...",
            "action": "I implemented a daily standup and used Jira...",
            "result": "We delivered on time and under budget.",
            "source": "simulated"
        },
        {
            "title": "Technical Problem Solving",
            "situation": "Our system was experiencing high latency...",
            "task": "I needed to identify the bottleneck...",
            "action": "I profiled the database queries and added indexes...",
            "result": "Latency dropped by 50%.",
            "source": "simulated"
        }
    ]
