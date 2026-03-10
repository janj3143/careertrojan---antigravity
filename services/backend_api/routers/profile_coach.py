"""
Profile Coach Router — Guided reflective AI coach (spec §10-§12, §20).

Routes:
  POST /api/profile-coach/v1/start    — begin a new coaching session
  POST /api/profile-coach/v1/respond  — submit user answer, get follow-up
  POST /api/profile-coach/v1/finish   — end session, get differentiators
  GET  /api/profile-coach/v1/config   — UI copy, initial questions, rules
  GET  /api/profile-coach/v1/prompt   — system prompt for LLM layer
"""
from __future__ import annotations

from fastapi import APIRouter
from services.backend_api.models.career_compass_schemas import (
    ProfileCoachStartRequest,
    ProfileCoachResponseRequest,
    ProfileCoachFinishRequest,
    ProfileCoachTurnResponse,
    ProfileCoachFinishResponse,
)
from services.backend_api.services.career.profile_coach_service import ProfileCoachService

router = APIRouter(prefix="/api/profile-coach/v1", tags=["profile-coach"])

_service = ProfileCoachService()

# ── System prompt (spec §11) ──────────────────────────────────────
PROFILE_COACH_SYSTEM_PROMPT = """You are a Profile Coach inside the CareerTrojan platform.
Your goal is to help the user enrich the "Profile" section of their CV by uncovering specific experiences, habits, and strengths that differentiate them from other candidates, including details they might consider trivial or obvious.
You must:
- Ask one reflective question at a time about their work, achievements, habits, values, and impact.
- Encourage the user to share small, concrete examples (e.g. a process they improved, a client they helped, feedback they often receive), not just big promotions or awards.
- After each answer, briefly mirror back what you heard in 1–2 short bullet points, then ask a follow‑up that goes one level deeper (for example: "what changed as a result?", "how did others respond?", "what did this teach you?").
- Keep each question short (1–2 sentences), direct, and warm. Avoid jargon.
- Remind the user occasionally that even "trivial" details can be the gold that differentiates them from their competitors.
- When the user says they are finished or uses language like "that's all" / "I'm done" / "enough for now", stop asking new questions and instead summarise 4–6 key differentiators you've heard so far as short bullet points that can be used to write their CV Profile.

Tone:
- Speak to the user by name when it is provided.
- Sound like a thoughtful, encouraging coach, not a recruiter or marketer.
- Prioritise clarity and depth over flattery."""

# ── Config object (spec §12) ──────────────────────────────────────
PROFILE_COACH_CONFIG = {
    "id": "profile_coach_v1",
    "name": "Profile Coach",
    "context": {
        "module": "cv_upload",
        "step": "profile",
        "ui_copy": {
            "header": "Let's find the gold in your story",
            "intro": "{{user_name}}, this is where we look for the details that set you apart. Even the things that feel trivial or obvious to you might be the gold that differentiates you from other candidates. Take a moment to think deeply and add anything that shows how you work, what you care about, and where you've made a difference.",
            "hint": "Examples: a tough client you turned around, a process you improved, feedback you keep hearing, side projects that sharpen your skills.",
            "cta_primary": "Start reflecting",
            "cta_secondary": "Skip for now",
        },
    },
    "initial_questions": [
        "When you think about your last few roles, what are 2\u20133 moments you're quietly proud of, even if they seemed small at the time?",
        "In your current or most recent role, what do colleagues or managers come to you for help with more than anyone else?",
        "Outside of your formal responsibilities, what problems have you taken ownership of because you couldn't ignore them?",
    ],
    "interaction_rules": {
        "ask_one_question_at_a_time": True,
        "max_turns_default": 8,
        "stop_phrases": ["that's all", "that is all", "i'm done", "enough for now", "finish", "stop"],
        "follow_up_style": "mirror_then_deepen",
        "include_reason_prompting": True,
    },
    "output_format": {
        "on_finish": "bullet_points",
        "bullet_point_count": {"min": 4, "max": 6},
    },
}


# ── Routes ─────────────────────────────────────────────────────────

@router.post("/start", response_model=ProfileCoachTurnResponse)
async def start_profile_coach(payload: ProfileCoachStartRequest):
    """Begin a new Profile Coach session (spec §20 /api/v1/profile-coach/start)."""
    return await _service.start(payload)


@router.post("/respond", response_model=ProfileCoachTurnResponse)
async def respond_profile_coach(payload: ProfileCoachResponseRequest):
    """Submit user answer and receive mirror + follow-up (spec §20)."""
    return await _service.respond(payload)


@router.post("/finish", response_model=ProfileCoachFinishResponse)
async def finish_profile_coach(payload: ProfileCoachFinishRequest):
    """End session and return 4-6 differentiator bullets (spec §20)."""
    return await _service.finish(payload)


@router.get("/config")
async def get_profile_coach_config():
    """Returns the frontend UI configuration and initial questions for the Profile Coach."""
    return PROFILE_COACH_CONFIG


@router.get("/prompt")
async def get_profile_coach_prompt():
    """Returns the system prompt for the Profile Coach."""
    return {"system_prompt": PROFILE_COACH_SYSTEM_PROMPT}
