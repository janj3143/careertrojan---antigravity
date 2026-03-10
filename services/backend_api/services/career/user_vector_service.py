"""
User Vector Service — Generates and stores user skill vectors (spec §14).

Vector axes: Leadership, Commercial Insight, Technical Depth, Communication,
Delivery, Strategic Thinking, Domain Expertise, Innovation,
Stakeholder Influence, Problem Solving.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# In-memory store (upgrade to DB for production)
_vectors: Dict[str, dict] = {}

CORE_AXES = [
    "leadership", "commercial_insight", "technical_depth",
    "communication", "delivery", "strategic_thinking",
    "domain_expertise", "innovation", "stakeholder_influence",
    "problem_solving",
]

FEATURE_SET_VERSION = "1.0.0"
VECTOR_VERSION = "1"


class UserVectorService:
    """Compute, store, and retrieve user skill vectors."""

    async def get_current_vector(self, user_id: str = None, resume_id: str = None) -> dict:
        key = f"{user_id}:{resume_id}" if user_id and resume_id else None
        if key and key in _vectors:
            rec = _vectors[key]
            return {
                "status": "ok",
                "vector": rec["vector"],
                "confidence": rec["confidence"],
                "vector_version": rec["vector_version"],
                "feature_set_version": rec["feature_set_version"],
                "resume_id": rec["resume_id"],
                "computed_at": rec["computed_at"],
                "source_summary": {"resume_id": rec["resume_id"]},
            }
        return {
            "status": "missing_resume",
            "message": "No live user vector found. Please upload or select a processed resume to continue.",
            "vector": None,
            "confidence": None,
            "vector_version": None,
            "feature_set_version": None,
            "resume_id": resume_id,
            "computed_at": None,
            "source_summary": {"resume_id": resume_id},
        }

    async def update_vector(self, user_id: str, resume_id: str, signals: Dict[str, float]) -> dict:
        """Create or update user vector from signal extraction output."""
        vector: Dict[str, float] = {}
        confidence: Dict[str, float] = {}
        for axis in CORE_AXES:
            score = signals.get(axis, 0.0)
            vector[axis] = round(score, 3)
            confidence[axis] = round(min(score + 0.1, 1.0), 3) if score > 0 else 0.0

        key = f"{user_id}:{resume_id}"
        record = {
            "user_id": user_id,
            "resume_id": resume_id,
            "vector": vector,
            "confidence": confidence,
            "vector_version": VECTOR_VERSION,
            "feature_set_version": FEATURE_SET_VERSION,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        _vectors[key] = record
        logger.info("User vector updated: user=%s resume=%s", user_id, resume_id)
        return {
            "status": "ok",
            **record,
            "source_summary": {"resume_id": resume_id},
        }
