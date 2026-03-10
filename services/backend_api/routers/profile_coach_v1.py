from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.backend_api.routers import coaching
from services.backend_api.routers.runtime_contract import respond
from services.shared.paths import CareerTrojanPaths


router = APIRouter(prefix="/api/v1/profile-coach", tags=["profile-coach-v1"])


class ProfileCoachStartRequest(BaseModel):
    user_id: int
    resume_id: int
    user_name: Optional[str] = None


class ProfileCoachRespondRequest(BaseModel):
    user_id: int
    session_id: str
    answer: str


class ProfileCoachFinishRequest(BaseModel):
    user_id: int
    session_id: str


class _StoredSession(BaseModel):
    session_id: str
    user_id: int
    resume_id: int
    user_name: Optional[str] = None
    started_at: str
    updated_at: str
    ended_at: Optional[str] = None
    turn_index: int = 0
    user_messages: List[str] = Field(default_factory=list)
    mirrored_points: List[List[str]] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    stop_detected: bool = False
    differentiator_summary: List[str] = Field(default_factory=list)


def _session_dir() -> Any:
    path = CareerTrojanPaths().user_data / "profile_coach_sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _session_path(session_id: str) -> Any:
    return _session_dir() / f"{session_id}.json"


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _load_session(session_id: str) -> Optional[_StoredSession]:
    file_path = _session_path(session_id)
    if not file_path.exists():
        return None
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    return _StoredSession(**payload)


def _save_session(session: _StoredSession) -> None:
    file_path = _session_path(session.session_id)
    file_path.write_text(json.dumps(session.dict(), ensure_ascii=False, indent=2), encoding="utf-8")


@router.post("/start")
def start_profile_coach(payload: ProfileCoachStartRequest):
    first_question = coaching.PROFILE_COACH_CONFIG["initial_questions"][0]
    session = _StoredSession(
        session_id=str(uuid.uuid4()),
        user_id=payload.user_id,
        resume_id=payload.resume_id,
        user_name=payload.user_name,
        started_at=_now_iso(),
        updated_at=_now_iso(),
    )
    session.follow_up_questions.append(first_question)
    _save_session(session)

    return respond(
        status="ok",
        data={
            "session_id": session.session_id,
            "question": first_question,
            "mirrored_points": [],
            "stop_detected": False,
        },
        source_summary={
            "resume_id": str(payload.resume_id),
            "profile_response_count": 0,
        },
    )


@router.post("/respond")
def respond_profile_coach(payload: ProfileCoachRespondRequest):
    session = _load_session(payload.session_id)
    if session is None or session.user_id != payload.user_id:
        return respond(
            status="error",
            message="Profile coach session was not found for this user.",
            data={},
            source_summary={"profile_response_count": 0},
            http_status=404,
        )

    answer = payload.answer.strip()
    if not answer:
        return respond(
            status="missing_profile_enrichment",
            message="An answer is required to continue profile coaching.",
            data={
                "session_id": session.session_id,
                "question": coaching.PROFILE_COACH_CONFIG["initial_questions"][0],
                "mirrored_points": [],
                "stop_detected": False,
            },
            source_summary={
                "resume_id": str(session.resume_id),
                "profile_response_count": len(session.user_messages),
            },
        )

    session.user_messages.append(answer)
    session.turn_index += 1
    session.updated_at = _now_iso()

    if coaching._contains_stop_phrase(answer):
        summary = coaching._finish_summary(session.user_messages[:-1], answer)
        session.stop_detected = True
        session.ended_at = _now_iso()
        session.differentiator_summary = summary
        _save_session(session)
        return respond(
            status="ok",
            data={
                "session_id": session.session_id,
                "question": None,
                "mirrored_points": [],
                "stop_detected": True,
                "differentiators": summary,
            },
            source_summary={
                "resume_id": str(session.resume_id),
                "profile_response_count": len(session.user_messages),
            },
        )

    mirrored = coaching._mirror_points(answer)
    follow_up = coaching._next_question(session.turn_index, session.user_name)
    session.mirrored_points.append(mirrored)
    session.follow_up_questions.append(follow_up)
    _save_session(session)

    return respond(
        status="ok",
        data={
            "session_id": session.session_id,
            "question": follow_up,
            "mirrored_points": mirrored,
            "stop_detected": False,
        },
        source_summary={
            "resume_id": str(session.resume_id),
            "profile_response_count": len(session.user_messages),
        },
    )


@router.post("/finish")
def finish_profile_coach(payload: ProfileCoachFinishRequest):
    session = _load_session(payload.session_id)
    if session is None or session.user_id != payload.user_id:
        return respond(
            status="error",
            message="Profile coach session was not found for this user.",
            data={},
            source_summary={"profile_response_count": 0},
            http_status=404,
        )

    if not session.differentiator_summary:
        session.differentiator_summary = coaching._finish_summary(session.user_messages, "")
    session.ended_at = session.ended_at or _now_iso()
    session.updated_at = _now_iso()
    session.stop_detected = True
    _save_session(session)

    return respond(
        status="ok",
        data={
            "session_id": session.session_id,
            "differentiators": session.differentiator_summary,
            "stop_detected": True,
        },
        source_summary={
            "resume_id": str(session.resume_id),
            "profile_response_count": len(session.user_messages),
        },
    )
