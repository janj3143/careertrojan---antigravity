"""
Signal Extraction Service — Extracts enriched signals from differentiators
and parsed resume data for downstream vector generation (spec §13).
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

# Keyword → axis mapping (spec §14.1 universal core dimensions)
_AXIS_KEYWORDS: Dict[str, List[str]] = {
    "leadership": ["led", "managed", "directed", "mentored", "coached", "supervised", "headed"],
    "commercial_insight": ["revenue", "sales", "business", "profit", "growth", "client", "commercial", "market"],
    "technical_depth": ["built", "developed", "engineered", "coded", "designed", "implemented", "architecture"],
    "communication": ["presented", "communicated", "wrote", "published", "spoke", "negotiated", "facilitated"],
    "delivery": ["shipped", "delivered", "launched", "deployed", "completed", "released", "milestone"],
    "strategic_thinking": ["strategy", "strategic", "planned", "roadmap", "vision", "long-term", "initiative"],
    "domain_expertise": ["specialist", "expert", "certified", "deep knowledge", "domain", "authority"],
    "innovation": ["innovated", "created", "invented", "novel", "new approach", "improved", "automated"],
    "stakeholder_influence": ["stakeholder", "influence", "persuaded", "aligned", "executive", "board", "c-suite"],
    "problem_solving": ["solved", "resolved", "troubleshot", "debugged", "diagnosed", "fixed", "root cause"],
}


class SignalExtractionService:
    """Extract axis signals from text / differentiators."""

    async def extract(self, payload) -> dict:
        text_sources: List[str] = list(payload.differentiators) if payload.differentiators else []

        if not text_sources:
            return {
                "status": "missing_profile_enrichment",
                "signals": {},
                "source_summary": {"resume_id": payload.resume_id},
            }

        combined = " ".join(text_sources).lower()
        signals = self._score_axes(combined)

        return {
            "status": "ok",
            "signals": signals,
            "source_summary": {"resume_id": payload.resume_id},
        }

    def _score_axes(self, text: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for axis, keywords in _AXIS_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            scores[axis] = min(round(count / max(len(keywords), 1), 2), 1.0)
        return scores
