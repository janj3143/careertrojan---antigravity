"""Config-driven expert rule engine."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from admin_portal.config import AIConfig

try:
    import yaml
except ImportError:  # PyYAML optional
    yaml = None  # type: ignore

logger = logging.getLogger(__name__)


class ExpertRuleEngine:
    """Applies YAML-configured boosts and penalties to model scores."""

    def __init__(self, config: AIConfig, rules_path: Optional[Path] = None):
        self.config = config
        self.rules_path = rules_path or Path(__file__).parent.parent / "config" / "rules" / "scoring_rules.yaml"
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        if not self.rules_path.exists():
            logger.warning("Rule file missing: %s", self.rules_path)
            return {}

        if yaml is None:
            logger.warning("PyYAML not installed; cannot parse %s", self.rules_path)
            return {}

        with open(self.rules_path, 'r', encoding='utf-8') as handle:
            return yaml.safe_load(handle) or {}

    def adjust_score(
        self,
        base_score: float,
        candidate_profile: Dict[str, Any],
        job_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        score = base_score
        applied: List[str] = []

        penalties = self.rules.get('penalties', {})
        boosts = self.rules.get('boosts', {})

        score += self._apply_skill_rules(candidate_profile, job_profile, penalties, boosts, applied)
        score += self._apply_industry_boost(candidate_profile, job_profile, boosts, applied)
        score += self._apply_experience_rules(candidate_profile, applied)

        final_score = float(min(max(score, 0.0), 1.0))
        return {
            'final_score': final_score,
            'applied_rules': applied
        }

    def _apply_skill_rules(
        self,
        candidate_profile: Dict[str, Any],
        job_profile: Dict[str, Any],
        penalties: Dict[str, float],
        boosts: Dict[str, float],
        applied: List[str]
    ) -> float:
        must_have_map = self.rules.get('must_have_skills', {})
        job_key = self._job_key(job_profile)
        rule_skills = must_have_map.get(job_key, [])

        candidate_skills = self._collect_candidate_skills(candidate_profile)
        missing = [skill for skill in rule_skills if skill.lower() not in candidate_skills]

        adjustment = 0.0
        if missing:
            penalty = penalties.get('missing_must_have', 0)
            adjustment += penalty * len(missing)
            applied.append(f"Missing must-have skills: {', '.join(missing)}")
        elif rule_skills:
            boost = boosts.get('matching_seniority', 0)
            adjustment += boost
            applied.append("All must-have skills present")

        return adjustment

    def _apply_industry_boost(
        self,
        candidate_profile: Dict[str, Any],
        job_profile: Dict[str, Any],
        boosts: Dict[str, float],
        applied: List[str]
    ) -> float:
        candidate_industry = str(
            candidate_profile.get('career_insights', {}).get('industry_alignment', '')
        ).lower()
        job_industry = str(
            job_profile.get('industry_alignment') or job_profile.get('industry') or ''
        ).lower()

        if candidate_industry and job_industry and job_industry in candidate_industry:
            applied.append("Industry alignment boost")
            return boosts.get('matching_industry', 0.0)

        return 0.0

    def _apply_experience_rules(self, candidate_profile: Dict[str, Any], applied: List[str]) -> float:
        other_rules = self.rules.get('other_rules', {})
        penalties = self.rules.get('penalties', {})

        min_years = other_rules.get('min_years_experience')
        experience_years = candidate_profile.get('user_profile', {}).get('experience_years')

        if min_years is not None and experience_years is not None and experience_years < min_years:
            adjustment = penalties.get('many_short_jobs', -0.1)
            applied.append(f"Experience below threshold ({experience_years} < {min_years})")
            return adjustment

        return 0.0

    @staticmethod
    def _collect_candidate_skills(profile: Dict[str, Any]) -> set[str]:
        skills = profile.get('skills')
        if not skills:
            skills = profile.get('user_profile', {}).get('skills')
        if not skills:
            skills = profile.get('candidate_job_fit', {}).get('skills_match')

        if isinstance(skills, list):
            return {str(skill).lower() for skill in skills}
        return set()

    @staticmethod
    def _job_key(job_profile: Dict[str, Any]) -> str:
        for key in ('job_title', 'position', 'role_focus'):
            value = job_profile.get(key)
            if value:
                return str(value).lower().replace(' ', '_')
        return 'default'
