"""Career Coach Service – Hybrid AI Orchestrator
=================================================
This module provides a *backend* career coaching engine that plugs
directly into the existing hybrid AI stack in `admin_portal.ai`.

It is deliberately **data-first**:
- No dummy fixtures or fake cohorts
- All insights are derived from the real resume / job / UMarketU data
- LLM is used only for *explanations* / narrative, not for scoring

Typical usage (from FastAPI router or portal bridge):

    from admin_portal.services.career.career_coach import get_career_coach_recommendations

    bundle = get_career_coach_recommendations(
        user_profile=user_profile_dict,
        resume_data=resume_json,
        job_data=job_json,
        applications=applications_list,
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Optional

from admin_portal.config import AIConfig
from admin_portal.ai.nlp_engine import NLPEngine
from admin_portal.ai.embeddings_engine import EmbeddingEngine
from admin_portal.ai.bayesian_engine import BayesianJobClassifier
from admin_portal.ai.regression_models import MatchScoreRegressor
from admin_portal.ai.neural_matcher import NeuralMatchModelWrapper
from admin_portal.ai.expert_rules import ExpertRuleEngine
from admin_portal.ai.llm_client import LLMClient


@dataclass
class CareerCoachInputs:
    user_profile: Dict[str, Any]
    resume_data: Dict[str, Any]
    job_data: Optional[Dict[str, Any]] = None
    applications: Optional[List[Dict[str, Any]]] = None


class CareerCoachService:
    """Thin orchestration layer over the hybrid AI stack."""

    def __init__(self, config: Optional[AIConfig] = None) -> None:
        self.config = config or AIConfig()

        # Core engines
        self.nlp = NLPEngine(self.config)
        self.emb = EmbeddingEngine(self.config)
        self.bayes = BayesianJobClassifier(self.config)
        self.regressor = MatchScoreRegressor(self.config)
        self.neural = NeuralMatchModelWrapper(self.config)
        self.rules = ExpertRuleEngine(self.config)
        self.llm = LLMClient(self.config)

    # --------------------------
    # Public API
    # --------------------------
    def build_coaching_bundle(self, payload: CareerCoachInputs) -> Dict[str, Any]:
        """Return a single JSON bundle that Coaching Hub can consume."""
        resume_text = self._extract_resume_text(payload.resume_data)
        job_text = self._extract_job_text(payload.job_data)
        skills = self._extract_skills(payload.resume_data)
        years = self._extract_years_experience(payload.resume_data, payload.user_profile)

        # 1) Hybrid similarity + match scoring
        bayes_category = self.bayes.predict_category(job_text or resume_text)
        neural_score = self.neural.score_pair(resume_text, job_text or resume_text)
        regressor_score = self.regressor.predict_match_score(
            resume_text=resume_text,
            job_text=job_text or "",
            skills=skills,
            years_experience=years,
        )

        # Expert rules can flag obvious issues (e.g., missing core skills)
        rule_findings = self.rules.evaluate_resume_vs_job(
            resume_data=payload.resume_data,
            job_data=payload.job_data or {},
        )

        # 2) Application‑level signals (UMarketU thread)
        app_stats = self._summarise_applications(payload.applications or [])

        # 3) Narrative explanation via LLM
        explanation = self.llm._synthesise_response(  # use public helper; no fake text
            "Provide short coaching insights on this candidate's trajectory, "
            "strengths and gaps based purely on the structured analysis.",
            f"bayes_category={bayes_category}, neural_score={neural_score:.3f}, "
            f"regressor_score={regressor_score:.1f}, years_experience={years}, "
            f"applications={app_stats}",
            prefer_local=self.config.use_local_first,
        )

        return {
            "meta": {
                "category": bayes_category,
                "years_experience": years,
                "skills_detected": len(skills),
            },
            "scores": {
                "neural_match_score": neural_score,
                "regressor_match_score": regressor_score,
            },
            "rules": rule_findings,
            "applications": app_stats,
            "explanation": explanation,
        }

    # --------------------------
    # Helpers
    # --------------------------
    @staticmethod
    def _extract_resume_text(resume_data: Dict[str, Any]) -> str:
        for key in ("raw_text", "content", "full_text"):
            value = resume_data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        # Fallback: stitch together headings + experience
        chunks: List[str] = []
        meta = resume_data.get("metadata") or {}
        for key in ("summary", "headline"):
            v = meta.get(key)
            if isinstance(v, str) and v.strip():
                chunks.append(v.strip())

        experience = resume_data.get("experience") or resume_data.get("work_experience") or []
        if isinstance(experience, list):
            for entry in experience[:4]:
                if not isinstance(entry, dict):
                    continue
                for field in ("title", "summary", "description"):
                    v = entry.get(field)
                    if isinstance(v, str) and v.strip():
                        chunks.append(v.strip())
        return "\n".join(chunks)

    @staticmethod
    def _extract_job_text(job_data: Optional[Dict[str, Any]]) -> str:
        if not isinstance(job_data, dict):
            return ""
        for key in ("full_text", "description", "jd_text", "raw_text"):
            v = job_data.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return ""

    @staticmethod
    def _extract_skills(resume_data: Dict[str, Any]) -> List[str]:
        skills = resume_data.get("skills") or resume_data.get("metadata", {}).get("skills")
        if isinstance(skills, list):
            return [s for s in skills if isinstance(s, str)]
        return []

    @staticmethod
    def _extract_years_experience(resume_data: Dict[str, Any], profile: Dict[str, Any]) -> float:
        meta = resume_data.get("metadata") or {}
        years = meta.get("total_years_experience") or profile.get("years_experience")
        try:
            return float(years) if years is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _summarise_applications(applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not applications:
            return {"total": 0, "offers": 0, "interviews": 0, "success_rate": None}

        total = len(applications)
        offers = 0
        interviews = 0
        for app in applications:
            status = str(app.get("status", "")).lower()
            if "offer" in status:
                offers += 1
            timeline = app.get("timeline") or []
            if isinstance(timeline, list):
                for event in timeline:
                    label = str(event.get("event", "")).lower()
                    if "interview" in label:
                        interviews += 1
                        break

        success_rate = offers / total * 100 if total else None
        return {
            "total": total,
            "offers": offers,
            "interviews": interviews,
            "success_rate": success_rate,
        }


# Singleton-style helper for compatibility with existing placeholder
_service = CareerCoachService()


def get_career_coach_recommendations(
    user_profile: Dict[str, Any],
    job_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    applications: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Backward-compatible functional entrypoint.

    The previous implementation returned:
        {"recommendations": [], "insights": []}

    We now return a richer bundle but keep the top-level keys for safety.
    """
    inputs = CareerCoachInputs(
        user_profile=user_profile or {},
        resume_data=resume_data or {},
        job_data=job_data or {},
        applications=applications or [],
    )
    bundle = _service.build_coaching_bundle(inputs)

    # Preserve original contract while exposing richer payload
    return {
        "recommendations": bundle,
        "insights": bundle.get("explanation"),
    }
