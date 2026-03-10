"""
Profile Builder Service — Transforms differentiators into CV Profile text (spec §27.3).
"""
from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ProfileBuilderService:
    """Accept differentiator bullets and compose a profile text block."""

    async def build_profile(self, payload) -> dict:
        if not payload.differentiators:
            return {
                "status": "missing_profile_enrichment",
                "profile_text": None,
                "source_summary": {
                    "resume_id": payload.resume_id,
                },
            }

        profile_text = self._compose_profile(payload.differentiators)

        return {
            "status": "ok",
            "profile_text": profile_text,
            "source_summary": {
                "resume_id": payload.resume_id,
            },
        }

    def _compose_profile(self, differentiators: List[str]) -> str:
        """Join differentiators into a professional profile narrative."""
        joined = " ".join(d.rstrip(".") + "." for d in differentiators if d.strip())
        return joined
