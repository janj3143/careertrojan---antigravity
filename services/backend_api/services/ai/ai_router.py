# -*- coding: utf-8 -*-
"""
AI Router — Intelligent Workload Distribution (via llm_gateway)
================================================================
Routes AI workloads to the most appropriate engine based on:
- Task type (parsing, chat, market intelligence)
- Privacy requirements (GDPR compliance → Ollama local)
- Cost optimization
- Performance needs

ALL LLM calls delegate to ``llm_gateway.generate()``.
No direct HTTP calls, no subprocess, no broken imports.

Author: IntelliCV Platform
Refactored: Wired through llm_gateway
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# ── Single import: everything goes through the gateway ────────────────
try:
    from services.ai_engine.llm_gateway import llm_gateway, LLMResponse
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from services.ai_engine.llm_gateway import llm_gateway, LLMResponse

try:
    from services.backend_api.services.ai.ai_chat_service import get_ai_chat_service
except ImportError:
    get_ai_chat_service = None  # Will be detected in _detect_engines


class AIRouter:
    """Intelligently routes AI workloads — all LLM calls go through llm_gateway."""

    def __init__(self):
        self.engines_available = self._detect_engines()
        logger.info("AIRouter initialized — engines: %s", self.engines_available)

    def _detect_engines(self) -> Dict[str, bool]:
        """Detect which AI engines are available via the gateway's health check."""
        health = llm_gateway.health_check()

        engines = {
            "openai": health.get("openai", False),
            "anthropic": health.get("anthropic", False),
            "perplexity": health.get("perplexity", False),
            "gemini": health.get("gemini", False),
            "ollama": health.get("ollama", False),
            "vllm": health.get("vllm", False),
        }

        # Internal AI engine (Bayesian/NLP/Fuzzy models)
        try:
            from services.ai_engine.unified_ai_engine import unified_ai_engine
            self._internal_engine = unified_ai_engine
            engines["internal"] = True
        except Exception:
            self._internal_engine = None
            engines["internal"] = False

        # AI chat service (uses gateway under the hood now)
        try:
            if get_ai_chat_service:
                self.ai_chat = get_ai_chat_service()
                engines["chat_service"] = True
            else:
                self.ai_chat = None
                engines["chat_service"] = False
        except Exception:
            self.ai_chat = None
            engines["chat_service"] = False

        return engines

    def route_cv_analysis(self, cv_text: str, privacy_mode: bool = False) -> Dict[str, Any]:
        """
        Route CV analysis to appropriate engine.
        privacy_mode=True → use only local Ollama (GDPR compliant).
        """
        if privacy_mode and self.engines_available.get("ollama"):
            return self._analyze_with_ollama(cv_text)

        if self._internal_engine and self.engines_available.get("internal"):
            return self._analyze_with_internal(cv_text)

        if self.engines_available.get("ollama"):
            return self._analyze_with_ollama(cv_text)

        # Last resort: cloud LLM via gateway (not GDPR-safe for private CVs)
        if not privacy_mode:
            resp = llm_gateway.generate(
                f"Extract from this CV: job titles, years of experience, top 5 skills. "
                f"Be concise.\n\n{cv_text[:2000]}",
            )
            if resp.success:
                return {"analysis": resp.text, "engine": f"gateway_{resp.provider}", "privacy_compliant": False}

        return {"error": "No CV analysis engine available", "engine": "none"}

    def route_market_intelligence(self, query: str) -> Dict[str, Any]:
        """Route market intelligence queries — Perplexity preferred for web search."""
        if self.ai_chat and self.engines_available.get("chat_service"):
            return self.ai_chat.get_job_market_insights(query)

        # Direct gateway call to Perplexity
        if self.engines_available.get("perplexity"):
            resp = llm_gateway.generate(query, provider="perplexity")
            if resp.success:
                return {"insights": resp.text, "source": "perplexity", "web_grounded": True}

        return {"insights": "Real-time market data unavailable. Configure Perplexity API.", "source": "unavailable"}

    def route_career_advice(self, user_profile: Dict) -> Dict[str, Any]:
        """Route personalized career advice."""
        if self.ai_chat and self.engines_available.get("chat_service"):
            return self.ai_chat.get_career_advice(
                user_skills=user_profile.get("skills", {}),
                career_patterns=user_profile.get("patterns", []),
                target_role=user_profile.get("target_role"),
            )

        # Fallback: direct gateway call
        prompt = (
            f"Provide career advice for a professional with skills: "
            f"{user_profile.get('skills', {})} and target role: {user_profile.get('target_role', 'unspecified')}."
        )
        resp = llm_gateway.generate(prompt)
        if resp.success:
            return {"advice": resp.text, "source": resp.provider}

        return {"advice": "AI advisory services unavailable", "source": "none"}

    def _analyze_with_internal(self, cv_text: str) -> Dict[str, Any]:
        """Analyze CV with internal NLP engine (Bayesian/NLP/Fuzzy)."""
        if self._internal_engine is None:
            return {"error": "Internal engine not loaded", "engine": "internal_ai"}
        try:
            result = self._internal_engine.analyze(cv_text)
            result["engine"] = "internal_ai"
            return result
        except Exception as e:
            logger.error("Internal engine analysis failed: %s", e)
            return {"error": str(e), "engine": "internal_ai"}

    def _analyze_with_ollama(self, cv_text: str) -> Dict[str, Any]:
        """Analyze CV with local Ollama via llm_gateway (privacy-first)."""
        prompt = (
            "Extract from this CV: job titles, years of experience, top 5 skills. "
            f"Be concise.\n\n{cv_text[:2000]}"
        )
        resp: LLMResponse = llm_gateway.generate(prompt, provider="ollama")
        if resp.success:
            return {"analysis": resp.text, "engine": "ollama_local", "privacy_compliant": True}
        return {"error": f"Ollama failed: {resp.error}", "engine": "ollama_local", "privacy_compliant": True}

    def get_engine_status(self) -> Dict[str, bool]:
        """Get status of all engines (live health check)."""
        self.engines_available = self._detect_engines()
        return self.engines_available


# Singleton instance
_router_instance = None

def get_ai_router() -> AIRouter:
    """Get singleton AI router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = AIRouter()
    return _router_instance
