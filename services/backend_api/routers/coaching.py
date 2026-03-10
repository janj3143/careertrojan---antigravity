from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json

from services.backend_api.utils import security
from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.routers.runtime_contract import respond
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


PROFILE_COACH_SYSTEM_PROMPT = """You are a Profile Coach inside the CareerTrojan platform.
Your goal is to help the user enrich the “Profile” section of their CV by uncovering specific experiences, habits, and strengths that differentiate them from other candidates, including details they might consider trivial or obvious.
You must:

Ask one reflective question at a time about their work, achievements, habits, values, and impact.

Encourage the user to share small, concrete examples (e.g. a process they improved, a client they helped, feedback they often receive), not just big promotions or awards.

After each answer, briefly mirror back what you heard in 1–2 short bullet points, then ask a follow‑up that goes one level deeper (for example: “what changed as a result?”, “how did others respond?”, “what did this teach you?”).

Keep each question short (1–2 sentences), direct, and warm. Avoid jargon.

Remind the user occasionally that even “trivial” details can be the gold that differentiates them from their competitors.

When the user says they are finished or uses language like “that’s all” / “I’m done” / “enough for now”, stop asking new questions and instead summarise 4–6 key differentiators you’ve heard so far as short bullet points that can be used to write their CV Profile.
Tone:

Speak to the user by name when it is provided.

Sound like a thoughtful, encouraging coach, not a recruiter or marketer.

Prioritise clarity and depth over flattery."""


PROFILE_COACH_CONFIG = {
    "id": "profile_coach_v1",
    "name": "Profile Coach",
    "context": {
        "module": "cv_upload",
        "step": "profile",
        "ui_copy": {
            "header": "Let’s find the gold in your story",
            "intro": "{{user_name}}, this is where we look for the details that set you apart. Even the things that feel trivial or obvious to you might be the gold that differentiates you from other candidates. Take a moment to think deeply and add anything that shows how you work, what you care about, and where you’ve made a difference.",
            "hint": "Examples: a tough client you turned around, a process you improved, feedback you keep hearing, side projects that sharpen your skills.",
            "cta_primary": "Start reflecting",
            "cta_secondary": "Skip for now",
        },
    },
    "initial_questions": [
        "When you think about your last few roles, what are 2–3 moments you’re quietly proud of, even if they seemed small at the time?",
        "In your current or most recent role, what do colleagues or managers come to you for help with more than anyone else?",
        "Outside of your formal responsibilities, what problems have you taken ownership of because you couldn’t ignore them?",
    ],
    "interaction_rules": {
        "ask_one_question_at_a_time": True,
        "max_turns_default": 8,
        "stop_phrases": [
            "that's all",
            "that is all",
            "i'm done",
            "enough for now",
            "finish",
            "stop",
        ],
        "follow_up_style": "mirror_then_deepen",
        "include_reason_prompting": True,
    },
    "output_format": {
        "on_finish": "bullet_points",
        "bullet_point_count": {
            "min": 4,
            "max": 6,
        },
    },
}


class ProfileCoachTurnRequest(BaseModel):
    user_name: Optional[str] = None
    user_message: str = ""
    transcript: List[str] = Field(default_factory=list)
    turn_index: int = 0


class ProfileStepState(BaseModel):
    profile_headline: Optional[str] = None
    differentiators: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    impact_examples: List[str] = Field(default_factory=list)


class ProfileBridgeLockstepRequest(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    session_id: Optional[str] = None
    cv_upload_id: Optional[str] = None
    source_portal: str = "user"
    profile_state: ProfileStepState = Field(default_factory=ProfileStepState)
    transcript: List[str] = Field(default_factory=list)
    turn_index: int = 0
    last_user_message: str = ""


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _contains_stop_phrase(text: str) -> bool:
    text_l = text.lower().strip()
    return any(phrase in text_l for phrase in PROFILE_COACH_CONFIG["interaction_rules"]["stop_phrases"])


def _bulletize(text: str, max_items: int) -> List[str]:
    segments = [segment.strip(" -•\t\n") for segment in text.replace("\n", ".").split(".")]
    segments = [segment for segment in segments if segment]
    return segments[:max_items]


def _mirror_points(answer: str) -> List[str]:
    bullets = _bulletize(answer, 2)
    if bullets:
        return bullets
    fallback = answer.strip()
    return [fallback[:140]] if fallback else []


def _next_question(turn_index: int, user_name: Optional[str]) -> str:
    deeper = [
        "What changed as a result of that?",
        "How did others respond when you did that?",
        "What did that teach you about how you work best?",
        "What part of that outcome would be hardest for someone else to replicate?",
    ]
    prompt = deeper[turn_index % len(deeper)]
    if user_name:
        return f"{user_name}, {prompt}"
    return prompt


def _finish_summary(transcript: List[str], latest: str) -> List[str]:
    merged = [entry for entry in transcript if entry.strip()]
    if latest.strip():
        merged.append(latest.strip())
    all_text = ". ".join(merged)
    bullets = _bulletize(all_text, 6)
    if len(bullets) >= 4:
        return bullets[:6]
    while len(bullets) < 4:
        bullets.append("Demonstrates practical impact through specific actions and outcomes.")
    return bullets[:6]


def _profile_step_missing_fields(profile_state: ProfileStepState) -> List[str]:
    missing: List[str] = []
    if not profile_state.profile_headline or not profile_state.profile_headline.strip():
        missing.append("profile_headline")
    if not profile_state.differentiators:
        missing.append("differentiators")
    if not profile_state.impact_examples:
        missing.append("impact_examples")
    return missing


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


@router.get("/profile/system-prompt")
def get_profile_coach_system_prompt() -> Dict[str, Any]:
    return respond(
        status="ok",
        data={
            "id": PROFILE_COACH_CONFIG["id"],
            "name": PROFILE_COACH_CONFIG["name"],
            "system_prompt": PROFILE_COACH_SYSTEM_PROMPT,
        },
        source_summary={"module": "cv_upload", "step": "profile"},
    )


@router.get("/profile/config")
def get_profile_coach_config(user_name: Optional[str] = None) -> Dict[str, Any]:
    config = dict(PROFILE_COACH_CONFIG)
    context = dict(config["context"])
    ui_copy = dict(context["ui_copy"])
    intro = ui_copy["intro"]
    ui_copy["intro"] = intro.replace("{{user_name}}", user_name or "You")
    context["ui_copy"] = ui_copy
    config["context"] = context
    return respond(
        status="ok",
        data={"config": config},
        source_summary={"module": "cv_upload", "step": "profile"},
    )


@router.post("/profile/reflect")
def profile_coach_reflect(payload: ProfileCoachTurnRequest) -> Dict[str, Any]:
    message = payload.user_message.strip()

    if not message:
        return respond(
            status="ok",
            data={
                "mode": "question",
                "question": PROFILE_COACH_CONFIG["initial_questions"][0],
            },
            source_summary={"profile_response_count": len(payload.transcript)},
        )

    if _contains_stop_phrase(message):
        return respond(
            status="ok",
            data={
                "mode": "finished",
                "summary_bullets": _finish_summary(payload.transcript, message),
            },
            source_summary={"profile_response_count": len(payload.transcript) + 1},
        )

    mirror = _mirror_points(message)
    follow_up = _next_question(payload.turn_index, payload.user_name)
    reminder = "Even small details can be the gold that differentiates you from other candidates."

    return respond(
        status="ok",
        data={
            "mode": "continue",
            "mirror_bullets": mirror,
            "follow_up_question": follow_up,
            "reminder": reminder if payload.turn_index % 2 == 1 else None,
        },
        source_summary={"profile_response_count": len(payload.transcript) + 1},
    )


@router.get("/profile/cv-upload-step")
def get_profile_cv_upload_step_contract(user_name: Optional[str] = None) -> Dict[str, Any]:
    return respond(
        status="ok",
        data={
            "module": "cv_upload",
            "step": "profile",
            "contract_version": "1.0",
            "ui": {
                "header": PROFILE_COACH_CONFIG["context"]["ui_copy"]["header"],
                "intro": PROFILE_COACH_CONFIG["context"]["ui_copy"]["intro"].replace("{{user_name}}", user_name or "You"),
                "hint": PROFILE_COACH_CONFIG["context"]["ui_copy"]["hint"],
            },
            "endpoints": {
                "system_prompt": "/api/coaching/v1/profile/system-prompt",
                "config": "/api/coaching/v1/profile/config",
                "reflect": "/api/coaching/v1/profile/reflect",
                "lockstep": "/api/coaching/v1/profile/bridge-lockstep",
            },
        },
        source_summary={"module": "cv_upload", "step": "profile"},
    )


@router.post("/profile/bridge-lockstep")
def build_profile_bridge_lockstep(payload: ProfileBridgeLockstepRequest) -> Dict[str, Any]:
    missing = _profile_step_missing_fields(payload.profile_state)
    is_ready = len(missing) == 0

    summary_bullets = _finish_summary(payload.transcript, payload.last_user_message)
    if not is_ready:
        summary_bullets = summary_bullets[:4]

    next_actions = []
    if not is_ready:
        next_actions.append("keep_reflecting")
    next_actions.append("persist_profile_step")
    next_actions.append("sync_portal_bridge")

    bridge_payload = {
        "contract_version": "1.0",
        "event_type": "profile_coach.step_sync",
        "module": "cv_upload",
        "step": "profile",
        "source_portal": payload.source_portal,
        "target_service": "portal_bridge",
        "user": {
            "user_id": payload.user_id,
            "user_name": payload.user_name,
        },
        "session": {
            "session_id": payload.session_id,
            "cv_upload_id": payload.cv_upload_id,
            "turn_index": payload.turn_index,
        },
        "profile_state": payload.profile_state.dict(),
        "summary_bullets": summary_bullets,
        "is_ready": is_ready,
        "missing_fields": missing,
        "generated_at": _now_iso(),
    }

    return respond(
        status="ok",
        data={
            "lockstep": {
                "is_ready": is_ready,
                "missing_fields": missing,
                "next_actions": next_actions,
            },
            "bridge_event": bridge_payload,
        },
        source_summary={
            "module": "cv_upload",
            "step": "profile",
            "profile_response_count": len(payload.transcript),
        },
    )


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
