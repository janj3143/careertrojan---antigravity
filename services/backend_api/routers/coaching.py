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

# Interview coaching service (role detection, question bank, 90-day plans)
try:
    from services.backend_api.services.interview_coaching_service import (
        InterviewCoachingService,
        detect_role_function,
        get_interview_questions,
        get_90day_plan,
        ROLE_FUNCTIONS,
    )
    INTERVIEW_COACHING_AVAILABLE = True
except Exception:
    InterviewCoachingService = None  # type: ignore
    detect_role_function = None  # type: ignore
    get_interview_questions = None  # type: ignore
    get_90day_plan = None  # type: ignore
    ROLE_FUNCTIONS = {}  # type: ignore
    INTERVIEW_COACHING_AVAILABLE = False

# Company Intel service (interview prep company research)
try:
    from services.backend_api.services.company_intel_service import (
        company_intel_service,
        CompanyIntelService,
    )
    COMPANY_INTEL_AVAILABLE = True
except Exception:
    company_intel_service = None  # type: ignore
    CompanyIntelService = None  # type: ignore
    COMPANY_INTEL_AVAILABLE = False


router = APIRouter(
    prefix="/api/coaching/v1",
    tags=["coaching"],
)

# Import auth dependency
from services.backend_api.utils.auth_deps import get_current_user, optional_user
from services.backend_api.db import models as db_models


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


def get_current_user_id(
    current_user: db_models.User = Depends(get_current_user),
) -> str:
    """Get authenticated user ID from JWT token."""
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
        "interview_coaching": "available" if INTERVIEW_COACHING_AVAILABLE else "unavailable",
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


class RoleDetectionRequest(BaseModel):
    """Request for auto-detecting role function from job/resume context."""
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    resume_skills: Optional[List[str]] = None
    resume_experience: Optional[List[Dict[str, Any]]] = None


class SmartQuestionRequest(BaseModel):
    """Request for role-specific interview questions."""
    role_function: str = Field(..., description="Role function code (e.g., 'development', 'sales')")
    category: Optional[str] = Field(None, description="Question category filter")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    limit: int = Field(10, ge=1, le=50)


class NinetyDayPlanRequest(BaseModel):
    """Request for 30-60-90 day plan template."""
    role_function: str
    seniority: str = Field("mid", description="Entry, mid, senior, executive")


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


# ─── Intelligent Interview Coaching Endpoints ───────────────────────────────

@router.get("/role-functions")
async def list_role_functions():
    """List all available role functions with codes and display names."""
    return {
        "role_functions": [
            {"code": code, "display_name": name}
            for code, name in ROLE_FUNCTIONS.items()
        ]
    }


@router.post("/detect-role")
async def detect_role(payload: RoleDetectionRequest):
    """
    Auto-detect role function from job/resume context.
    
    Returns detected function, confidence, signals, and alternatives.
    Client should confirm with user if requires_confirmation=True.
    """
    if not INTERVIEW_COACHING_AVAILABLE or detect_role_function is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Interview coaching service is not available.",
        )
    
    result = detect_role_function(
        job_title=payload.job_title,
        job_description=payload.job_description,
        resume_skills=payload.resume_skills,
        resume_experience=payload.resume_experience,
    )
    return result


@router.post("/smart-questions")
async def get_smart_questions(payload: SmartQuestionRequest):
    """
    Get role-specific interview questions with purpose and frameworks.
    
    Questions include:
    - Closing questions (Good vs Great, 90-Day, Seal-the-Deal)
    - Role-specific questions customized for the function
    - Interview insight for why each question works
    """
    if not INTERVIEW_COACHING_AVAILABLE or get_interview_questions is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Interview coaching service is not available.",
        )
    
    questions = get_interview_questions(
        role_function=payload.role_function,
        category=payload.category,
        limit=payload.limit,
    )
    return {
        "role_function": payload.role_function,
        "category": payload.category,
        "count": len(questions),
        "questions": questions,
    }


@router.post("/90-day-plan")
async def get_ninety_day_plan(payload: NinetyDayPlanRequest):
    """
    Get 30-60-90 day plan template for a role function.
    
    Returns structured template with:
    - Day 30/60/90 actions
    - Success metrics per phase
    - SMART report suggestions
    - Strategic closing statement for interviews
    """
    if not INTERVIEW_COACHING_AVAILABLE or get_90day_plan is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Interview coaching service is not available.",
        )
    
    template = get_90day_plan(
        role_function=payload.role_function,
        seniority=payload.seniority,
    )
    return template


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


# --- Company Intel Endpoints for Interview Prep ---

class CompanyIntelRequest(BaseModel):
    """Request for company intelligence."""
    company_name: str = Field(..., min_length=1, description="Target company name")
    role_title: Optional[str] = Field(None, description="Role being interviewed for")


@router.get("/company-intel/health")
async def company_intel_health():
    """Check if company intel service is available."""
    return {
        "status": "ok" if COMPANY_INTEL_AVAILABLE else "unavailable",
        "service": "company_intel",
    }


@router.post("/company-intel/overview")
async def get_company_overview(payload: CompanyIntelRequest):
    """
    Get company overview for interview prep.
    
    Returns company description, industry, website, and key facts.
    """
    if not COMPANY_INTEL_AVAILABLE or company_intel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Company intelligence service is not available.",
        )
    
    try:
        result = await company_intel_service.get_company_overview(payload.company_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company overview: {e}",
        )


@router.post("/company-intel/hiring")
async def get_hiring_history(payload: CompanyIntelRequest):
    """
    Get company hiring history for similar roles.
    
    Returns hiring signals, growth indicators, and similar roles found.
    """
    if not COMPANY_INTEL_AVAILABLE or company_intel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Company intelligence service is not available.",
        )
    
    try:
        result = await company_intel_service.get_hiring_history(
            payload.company_name,
            payload.role_title,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hiring history: {e}",
        )


@router.post("/company-intel/news")
async def get_recent_news(payload: CompanyIntelRequest):
    """
    Get recent company news, appointments, and product launches.
    
    Returns categorized news items from the past 90 days.
    """
    if not COMPANY_INTEL_AVAILABLE or company_intel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Company intelligence service is not available.",
        )
    
    try:
        result = await company_intel_service.get_recent_news(payload.company_name)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company news: {e}",
        )


@router.post("/company-intel/talking-points")
async def get_talking_points(payload: CompanyIntelRequest):
    """
    Generate interview talking points based on company research.
    
    Returns actionable talking points and questions to ask.
    """
    if not COMPANY_INTEL_AVAILABLE or company_intel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Company intelligence service is not available.",
        )
    
    try:
        result = await company_intel_service.get_interview_talking_points(
            payload.company_name,
            payload.role_title,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate talking points: {e}",
        )


@router.post("/company-intel/full")
async def get_full_company_intel(payload: CompanyIntelRequest):
    """
    Get complete company intelligence package for interview prep.
    
    Includes overview, hiring history, news, and talking points.
    """
    if not COMPANY_INTEL_AVAILABLE or company_intel_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Company intelligence service is not available.",
        )
    
    try:
        result = await company_intel_service.get_full_company_intel(
            payload.company_name,
            payload.role_title,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company intel: {e}",
        )
