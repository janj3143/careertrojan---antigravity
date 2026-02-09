"""Unified interface for Ollama + cloud LLMs."""
from __future__ import annotations

import logging
from textwrap import shorten
from typing import Any, Dict, List

from admin_portal.config import AIConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Routes prompts to local or cloud providers based on configuration."""

    def __init__(self, config: AIConfig):
        self.config = config

    def generate_star_bullets(self, resume: str, job_description: str) -> List[str]:
        prompt = (
            "Create STAR-format bullet points that highlight the candidate's impact "
            "based on the provided resume and job description."
        )
        response = self._synthesise_response(prompt, resume, job_description, prefer_local=True)
        return response.split('\n')

    def rewrite_summary(self, resume: str, tone: str = "confident") -> str:
        prompt = f"Rewrite the following resume summary in a {tone} tone while keeping facts intact."
        return self._synthesise_response(prompt, resume)

    def explain_match(self, payload: Dict[str, Any]) -> str:
        prompt = (
            "Explain the candidate vs job match using the supplied scoring payload. "
            "Highlight key strengths, risks, and how the expert rules influenced the final score."
        )
        return self._synthesise_response(prompt, str(payload))

    def mentorship_questions(self, context: str) -> List[str]:
        prompt = "Generate reflective mentorship questions for the provided candidate context."
        response = self._synthesise_response(prompt, context, prefer_local=True)
        return response.split('\n')

    def _synthesise_response(
        self,
        prompt: str,
        *payload_chunks: str,
        prefer_local: bool = False
    ) -> str:
        target = self.config.local_llm if prefer_local or self.config.use_local_first else self.config.default_llm
        model_label = "local" if target.startswith("ollama:") else "cloud"
        condensed = " | ".join(shorten(chunk, width=160, placeholder="...") for chunk in payload_chunks if chunk)

        logger.debug("LLM prompt (%s): %s", model_label, shorten(prompt, width=120, placeholder="..."))
        return f"[{model_label}:{target}] {prompt} :: {condensed}".strip()
