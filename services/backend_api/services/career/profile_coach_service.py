"""
Profile Coach Service — Guided reflective AI coach (spec §10/§11/§12).

Manages conversation state, stop-phrase detection, mirror-then-deepen
follow-ups, and 4-6 differentiator summarisation on finish.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# ── In-memory session store (swap for Redis/DB in production) ──────
_sessions: Dict[str, dict] = {}

STOP_PHRASES = [
    "that's all", "that is all", "i'm done", "enough for now",
    "finish", "stop",
]

INITIAL_QUESTIONS = [
    "When you think about your last few roles, what are 2–3 moments you're quietly proud of, even if they seemed small at the time?",
    "In your current or most recent role, what do colleagues or managers come to you for help with more than anyone else?",
    "Outside of your formal responsibilities, what problems have you taken ownership of because you couldn't ignore them?",
]


class ProfileCoachService:
    """Stateful conversation service for Profile Coach."""

    # ── start ─────────────────────────────────────────────────
    async def start(self, payload) -> dict:
        session_id = str(uuid4())
        name = payload.user_name or "there"
        question = self._personalise(INITIAL_QUESTIONS[0], name)

        _sessions[session_id] = {
            "user_id": payload.user_id,
            "resume_id": payload.resume_id,
            "user_name": name,
            "turn_index": 0,
            "user_messages": [],
            "mirror_points": [],
            "follow_up_questions": [question],
            "stop_detected": False,
            "differentiator_summary": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": None,
        }
        logger.info("Profile coach session started: %s (user=%s)", session_id, payload.user_id)
        return {
            "status": "ok",
            "session_id": session_id,
            "question": question,
            "mirrored_points": [],
            "stop_detected": False,
            "source_summary": {"resume_id": payload.resume_id},
        }

    # ── respond ───────────────────────────────────────────────
    async def respond(self, payload) -> dict:
        sess = _sessions.get(payload.session_id)
        if not sess:
            return {"status": "error", "session_id": payload.session_id, "question": None, "mirrored_points": [], "stop_detected": False}

        sess["user_messages"].append(payload.answer)
        sess["turn_index"] += 1
        sess["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Stop-phrase detection (spec §12 interaction_rules.stop_phrases)
        if self._detect_stop(payload.answer):
            sess["stop_detected"] = True
            sess["ended_at"] = datetime.now(timezone.utc).isoformat()
            differentiators = self._summarise_differentiators(sess)
            sess["differentiator_summary"] = differentiators
            return {
                "status": "ok",
                "session_id": payload.session_id,
                "question": None,
                "mirrored_points": [],
                "stop_detected": True,
                "source_summary": {
                    "resume_id": sess["resume_id"],
                    "profile_response_count": len(sess["user_messages"]),
                },
            }

        # Mirror-then-deepen (spec §11)
        mirrored = self._mirror_answer(payload.answer)
        sess["mirror_points"].extend(mirrored)

        follow_up = self._build_follow_up(payload.answer, sess["turn_index"])
        sess["follow_up_questions"].append(follow_up)

        return {
            "status": "ok",
            "session_id": payload.session_id,
            "question": follow_up,
            "mirrored_points": mirrored,
            "stop_detected": False,
            "source_summary": {
                "resume_id": sess["resume_id"],
                "profile_response_count": len(sess["user_messages"]),
            },
        }

    # ── finish ────────────────────────────────────────────────
    async def finish(self, payload) -> dict:
        sess = _sessions.get(payload.session_id)
        if not sess:
            return {"status": "error", "session_id": payload.session_id, "differentiators": []}

        # Idempotent (spec §15.5)
        if sess.get("differentiator_summary"):
            return {
                "status": "ok",
                "session_id": payload.session_id,
                "differentiators": sess["differentiator_summary"],
                "source_summary": {
                    "resume_id": sess["resume_id"],
                    "profile_response_count": len(sess["user_messages"]),
                },
            }

        sess["ended_at"] = datetime.now(timezone.utc).isoformat()
        differentiators = self._summarise_differentiators(sess)
        sess["differentiator_summary"] = differentiators

        return {
            "status": "ok",
            "session_id": payload.session_id,
            "differentiators": differentiators,
            "source_summary": {
                "resume_id": sess["resume_id"],
                "profile_response_count": len(sess["user_messages"]),
            },
        }

    # ── Helpers ───────────────────────────────────────────────
    def _personalise(self, text: str, name: str) -> str:
        if name and name.lower() not in ("user", "there", ""):
            return f"{name}, {text[0].lower()}{text[1:]}"
        return text

    def _detect_stop(self, answer: str) -> bool:
        lower = answer.lower().strip()
        return any(phrase in lower for phrase in STOP_PHRASES)

    def _mirror_answer(self, answer: str) -> List[str]:
        sentences = [s.strip() for s in re.split(r'[.!?]+', answer) if s.strip()]
        bullets: List[str] = []
        for s in sentences[:3]:
            if len(s) > 15:
                bullets.append(s if s[0].isupper() else s.capitalize())
        return bullets[:2]  # max 2 bullets per spec

    def _build_follow_up(self, answer: str, turn: int) -> str:
        deepeners = [
            "What changed as a result of that?",
            "How did others respond when you did that?",
            "What did this teach you about yourself?",
            "Can you give me a specific example of when that happened?",
            "What impact did that have on your team or organisation?",
            "What would someone who worked with you say about this?",
            "Remember, even the details that feel trivial to you can be the gold that sets you apart. What else comes to mind?",
            "What's something you do differently from your peers that you rarely talk about?",
        ]
        return deepeners[turn % len(deepeners)]

    def _summarise_differentiators(self, sess: dict) -> List[str]:
        """Build 4-6 differentiator bullets from mirror points and messages."""
        raw = sess.get("mirror_points", [])
        if len(raw) < 4:
            # Pad with shortened user messages
            for msg in sess.get("user_messages", []):
                short = msg[:120].rstrip(". ") + "."
                raw.append(short)
                if len(raw) >= 6:
                    break
        # Dedupe + cap
        seen: set = set()
        bullets: List[str] = []
        for item in raw:
            key = item.lower().strip()
            if key not in seen:
                seen.add(key)
                bullets.append(item)
            if len(bullets) >= 6:
                break
        return bullets[:6]
