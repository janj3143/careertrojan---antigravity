"""
ai_chat_service.py
==================
Unified AI Chat Service — Delegates all LLM calls through llm_gateway.

Provides intelligent career guidance, job market insights, and personalized
recommendations.  Instead of managing API keys and HTTP calls itself, this
service calls ``llm_gateway.generate()`` which reads config/models.yaml,
handles fallback chains, and returns a unified ``LLMResponse``.

Priority order (configurable in models.yaml):
  Perplexity → Gemini → OpenAI → Anthropic → Ollama

Author: IntelliCV Platform
Created: November 17, 2025
Refactored: Wired through llm_gateway
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Single import: ALL LLM calls go through this gateway ──────────────
try:
    from services.ai_engine.llm_gateway import llm_gateway, LLMResponse
except ImportError:
    # Fallback for direct-module execution
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from services.ai_engine.llm_gateway import llm_gateway, LLMResponse

# System prompt shared across career-related queries
_CAREER_SYSTEM_PROMPT = (
    "You are a career advisor with deep knowledge of job markets, skill development, "
    "and career transitions. Provide specific, actionable advice grounded in current "
    "market data."
)


class AIChatService:
    """Unified interface for AI-powered career chat — all calls via llm_gateway."""

    def __init__(self):
        """Initialize — availability is determined by the gateway's provider health."""
        health = llm_gateway.health_check()
        self.perplexity_available = health.get("perplexity", False)
        self.gemini_available = health.get("gemini", False)
        self._any_available = any(health.values())

        if not self._any_available:
            logger.warning("No AI chat providers reachable — check API keys in .env")

    def get_career_advice(self,
                          user_skills: Dict,
                          career_patterns: List[str],
                          target_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Get personalized career advice using AI

        Args:
            user_skills: Dictionary of user skills and experience
            career_patterns: List of detected career patterns
            target_role: Optional target role for guidance

        Returns:
            Dictionary with advice, resources, and next steps
        """
        # Build prompt
        prompt = self._build_career_advice_prompt(user_skills, career_patterns, target_role)

        # Try Perplexity first (web-grounded)
        if self.perplexity_available:
            try:
                response = self._query_perplexity(prompt)
                if response:
                    return {
                        'advice': response,
                        'source': 'perplexity',
                        'web_grounded': True,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Perplexity API error: {e}")

        # Fallback to Gemini
        if self.gemini_available:
            try:
                response = self._query_gemini(prompt)
                if response:
                    return {
                        'advice': response,
                        'source': 'gemini',
                        'web_grounded': False,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Gemini API error: {e}")

        # No fabricated responses permitted.
        return self._unavailable_response(
            "No AI chat providers are configured or reachable. Configure PERPLEXITY_API_KEY or GEMINI_API_KEY."
        )

    def _unavailable_response(self, message: str) -> Dict[str, Any]:
        return {
            'advice': None,
            'source': 'unavailable',
            'web_grounded': False,
            'timestamp': datetime.now().isoformat(),
            'error': message,
        }

    def get_skill_development_plan(self,
                                    current_skills: Dict,
                                    target_skills: Dict,
                                    timeline: str = "6 months") -> Dict[str, Any]:
        """
        Get personalized skill development plan

        Args:
            current_skills: Current skill levels
            target_skills: Target skill levels
            timeline: Development timeline (e.g., "3 months", "1 year")

        Returns:
            Development plan with resources and milestones
        """
        prompt = f"""
        Based on the following skill assessment, create a personalized skill development plan:

        Current Skills:
        {json.dumps(current_skills, indent=2)}

        Target Skills:
        {json.dumps(target_skills, indent=2)}

        Timeline: {timeline}

        Provide:
        1. Priority skills to develop
        2. Recommended learning resources (courses, books, projects)
        3. Milestone checkpoints
        4. Estimated time investment per skill
        5. Real-world application opportunities

        Focus on practical, actionable advice with specific resources.
        """

        # Try Perplexity (will include current market resources)
        if self.perplexity_available:
            try:
                response = self._query_perplexity(prompt)
                if response:
                    return {
                        'plan': response,
                        'source': 'perplexity',
                        'timeline': timeline,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error getting development plan: {e}")

        # Gemini fallback
        if self.gemini_available:
            try:
                response = self._query_gemini(prompt)
                if response:
                    return {
                        'plan': response,
                        'source': 'gemini',
                        'timeline': timeline,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Error with Gemini: {e}")

        return {
            'plan': "AI service unavailable. Please check API configuration.",
            'source': 'error',
            'timestamp': datetime.now().isoformat()
        }

    def get_job_market_insights(self,
                                job_title: str,
                                location: Optional[str] = None,
                                skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get current job market insights for a role

        Args:
            job_title: Target job title
            location: Optional location
            skills: Optional list of relevant skills

        Returns:
            Market insights including demand, salaries, trends
        """
        location_str = f" in {location}" if location else ""
        skills_str = f"\nRelevant skills: {', '.join(skills)}" if skills else ""

        prompt = f"""
        Provide current job market analysis for:

        Role: {job_title}{location_str}{skills_str}

        Include:
        1. Current demand level (high/medium/low)
        2. Average salary range (if applicable for location)
        3. Top companies hiring for this role
        4. Key skills in demand
        5. Career growth trajectory
        6. Market trends (growing/stable/declining)

        Provide data-driven insights based on current market conditions.
        """

        # Perplexity is ideal for this (web search)
        if self.perplexity_available:
            try:
                response = self._query_perplexity(prompt)
                if response:
                    return {
                        'insights': response,
                        'source': 'perplexity',
                        'job_title': job_title,
                        'location': location,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"Market insights error: {e}")

        return {
            'insights': "Market data unavailable. Enable Perplexity API for real-time job market insights.",
            'source': 'unavailable',
            'timestamp': datetime.now().isoformat()
        }

    def _query_perplexity(self, prompt: str, model: Optional[str] = None) -> Optional[str]:
        """Query Perplexity via llm_gateway (web-grounded answers)."""
        messages = [
            {"role": "system", "content": _CAREER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        resp: LLMResponse = llm_gateway.generate(
            prompt, provider="perplexity", messages=messages, max_tokens=1500, temperature=0.7,
        )
        if resp.success and resp.text:
            return resp.text
        logger.warning("Perplexity via gateway failed: %s", resp.error)
        return None

    def _query_gemini(self, prompt: str) -> Optional[str]:
        """Query Gemini via llm_gateway."""
        full_prompt = (
            f"You are a career advisor. {prompt}\n\n"
            "Provide practical, actionable advice focusing on:\n"
            "- Specific next steps\n- Resource recommendations\n"
            "- Realistic timelines\n- Market-relevant skills"
        )
        resp: LLMResponse = llm_gateway.generate(
            full_prompt, provider="gemini", max_tokens=1500, temperature=0.7,
        )
        if resp.success and resp.text:
            return resp.text
        logger.warning("Gemini via gateway failed: %s", resp.error)
        return None

    def _build_career_advice_prompt(self,
                                     user_skills: Dict,
                                     career_patterns: List[str],
                                     target_role: Optional[str]) -> str:
        """Build career advice prompt, enriched with evolution lineage context."""

        top_skills = sorted(
            [(k, v) for k, v in user_skills.items() if k != 'years_experience'],
            key=lambda x: x[1],
            reverse=True
        )[:3]

        years_exp = user_skills.get('years_experience', 0)

        pattern_desc = ", ".join(career_patterns) if career_patterns else "traditional career path"
        target_str = f"\nTarget role: {target_role}" if target_role else ""

        # ── Inject term evolution context ────────────────────────────────
        # If the user's skills or target role appear in an evolution chain,
        # tell the AI about the lineage so it can give smarter advice.
        evolution_context = ""
        try:
            from services.ai_engine.term_evolution_engine import evolution_engine
            all_terms = [s[0] for s in top_skills]
            if target_role:
                all_terms.append(target_role)
            all_terms.extend(career_patterns)

            seen_chains = set()
            evo_blocks = []
            for term in all_terms:
                chain = evolution_engine.resolve(term)
                if chain and chain.get("chain_id") not in seen_chains:
                    seen_chains.add(chain["chain_id"])
                    block = evolution_engine.format_for_ai_context(term)
                    if block:
                        evo_blocks.append(block)

            if evo_blocks:
                evolution_context = (
                    "\n\n--- INDUSTRY EVOLUTION CONTEXT (use this to inform your advice) ---\n"
                    + "\n\n".join(evo_blocks[:3])  # Max 3 chains to keep prompt focused
                    + "\n--- END EVOLUTION CONTEXT ---\n"
                )
        except Exception:
            pass  # Non-fatal — evolution engine may not be loaded

        prompt = f"""
        Provide personalized career advice for a professional with the following profile:

        Experience: {years_exp} years
        Top Skills: {', '.join([f"{s[0]} ({s[1]:.1f})" for s in top_skills])}
        Career Pattern: {pattern_desc}{target_str}
        {evolution_context}
        Provide:
        1. Career strengths and unique value proposition
        2. Recommended career paths or next roles
        3. Skill gaps to address for advancement
        4. Industry trends relevant to their background
        5. Specific action items for next 6 months

        IMPORTANT: If evolution context is provided above, use it to show the user
        how their existing skills connect to emerging roles and industry trends.
        Highlight transferable skills and career pivots they may not have considered.

        Be specific and actionable, referencing current market conditions.
        """

        return prompt

    def _generate_fallback_advice(self,
                                   user_skills: Dict,
                                   career_patterns: List[str],
                                   target_role: Optional[str]) -> str:
        raise RuntimeError(
            "Fallback advice generation is disabled. Configure an AI provider or connect the web-research pipeline."
        )

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service availability status"""
        return {
            'perplexity': {
                'available': self.perplexity_available,
                'api_key_set': bool(self.perplexity_api_key),
                'capabilities': ['web_search', 'current_data', 'market_insights']
            },
            'gemini': {
                'available': self.gemini_available,
                'api_key_set': bool(self.gemini_api_key),
                'capabilities': ['analysis', 'recommendations', 'planning']
            },
            'any_available': self.perplexity_available or self.gemini_available
        }


# Singleton instance
_ai_chat_service_instance = None

def get_ai_chat_service() -> AIChatService:
    """Get singleton instance of AI chat service"""
    global _ai_chat_service_instance
    if _ai_chat_service_instance is None:
        _ai_chat_service_instance = AIChatService()
    return _ai_chat_service_instance
