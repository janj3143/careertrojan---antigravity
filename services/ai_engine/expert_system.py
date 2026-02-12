"""
CareerTrojan — Expert System Engine (AI Engine Layer)
======================================================

Rule-based inference engine referenced in config/models.yaml as:
    expert_system.career_rules   → CareerRules
    expert_system.skill_matcher  → SkillMatcher

Loads rules from YAML files in config/expert_rules/ and provides:
  1. Career path validation (experience, skill gaps, certifications)
  2. Weighted skill matching (exact + semantic + transferable + certs)
  3. Explainability: every decision returns a human-readable reason

The inference orchestrator in unified_ai_engine.py calls:
    expert_system.career_rules.evaluate(context)
    expert_system.skill_matcher.score(user_skills, role_requirements)

Usage:
    from services.ai_engine.expert_system import career_rules, skill_matcher

    result = career_rules.evaluate({
        "target_role": "Senior Data Scientist",
        "years_experience": 3,
        "career_pivot": False,
        "has_relevant_certifications": True,
    })

    score = skill_matcher.score(
        user_skills=["python", "machine learning", "sql"],
        role_requirements=["data science", "deep learning", "python", "cloud computing"],
    )
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(os.getenv("CAREERTROJAN_PROJECT_ROOT", r"C:\careertrojan"))
RULES_DIR = _PROJECT_ROOT / "config" / "expert_rules"


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file (falls back to empty dict)."""
    if not path.exists():
        logger.warning("Expert rules file missing: %s", path)
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: parse simple YAML-like structure manually
        logger.warning("PyYAML not installed — expert rules may not load correctly")
        return {}
    except Exception as e:
        logger.error("Failed to load %s: %s", path, e)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# Career Rules Engine
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RuleResult:
    """Result of evaluating a single rule against a context."""
    rule_id: str
    name: str
    triggered: bool
    action: str
    message: str
    adjustment: float = 0.0
    priority: int = 5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "triggered": self.triggered,
            "action": self.action,
            "message": self.message,
            "adjustment": self.adjustment,
            "priority": self.priority,
        }


class CareerRules:
    """
    Rule engine for career path validation.
    Evaluates user context against YAML-defined business rules and returns
    triggered rules with actions, adjustments, and explanations.
    """

    def __init__(self, rules_path: Optional[Path] = None):
        self._raw = _load_yaml(rules_path or RULES_DIR / "career_rules.yaml")
        self._rules = self._raw.get("rules", [])
        logger.info("CareerRules loaded %d rules from %s", len(self._rules),
                     rules_path or RULES_DIR / "career_rules.yaml")

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate all rules against the provided context.

        Args:
            context: Dict with keys like target_role, years_experience,
                     career_pivot, has_relevant_certifications, skills, etc.

        Returns:
            {
                "triggered_rules": [RuleResult, ...],
                "confidence_adjustment": float,    # net adjustment to apply
                "recommendations": [str, ...],
                "warnings": [str, ...],
            }
        """
        triggered = []
        total_adjustment = 0.0
        recommendations = []
        warnings = []

        # Provide safe defaults for optional context keys
        ctx = {
            "target_role": "",
            "years_experience": 0,
            "career_pivot": False,
            "transferable_skill_count": 0,
            "has_relevant_certifications": False,
            "expected_salary_percentile": 50,
            "industry_switch": False,
            "years_in_current_industry": 0,
            "prefers_remote": False,
            "role_supports_remote": True,
            "skills": [],
        }
        ctx.update(context)

        for rule in self._rules:
            try:
                condition = rule.get("condition", "False")
                # Safe eval with only the context namespace
                result = eval(condition, {"__builtins__": {}}, ctx)  # noqa: S307
            except Exception as e:
                logger.debug("Rule %s condition error: %s", rule.get("id"), e)
                result = False

            if result:
                adj = rule.get("adjustment", 0.0)
                action = rule.get("action", "info")
                msg = rule.get("message", "")
                rr = RuleResult(
                    rule_id=rule.get("id", "?"),
                    name=rule.get("name", "unnamed"),
                    triggered=True,
                    action=action,
                    message=msg,
                    adjustment=adj,
                    priority=rule.get("priority", 5),
                )
                triggered.append(rr)
                total_adjustment += adj

                if action.startswith("flag_") or action.startswith("adjust_confidence_down"):
                    warnings.append(msg)
                elif action.startswith("recommend") or action.startswith("add_"):
                    recommendations.append(msg)

        return {
            "triggered_rules": [r.to_dict() for r in sorted(triggered, key=lambda r: -r.priority)],
            "confidence_adjustment": round(total_adjustment, 3),
            "recommendations": recommendations,
            "warnings": warnings,
            "rules_evaluated": len(self._rules),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Skill Matcher Engine
# ═══════════════════════════════════════════════════════════════════════════

class SkillMatcher:
    """
    Weighted scoring system for matching user skills to role requirements.
    Supports exact match, transferable skills, and certification credit.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self._raw = _load_yaml(config_path or RULES_DIR / "skill_matcher.yaml")
        self._scoring = self._raw.get("scoring", {})
        self._weights = self._scoring.get("weights", {
            "exact_skill_match": 0.35,
            "semantic_similarity": 0.25,
            "transferable_skills": 0.15,
            "certification_bonus": 0.10,
            "experience_depth": 0.15,
        })
        self._thresholds = self._scoring.get("thresholds", {
            "strong_match": 0.80,
            "moderate_match": 0.55,
            "weak_match": 0.30,
        })
        self._transferable = self._raw.get("transferable_skills", {})
        self._cert_mappings = self._raw.get("certification_mappings", {})
        logger.info("SkillMatcher loaded (%d transferable skill groups, %d cert mappings)",
                     len(self._transferable), len(self._cert_mappings))

    def score(self,
              user_skills: List[str],
              role_requirements: List[str],
              certifications: Optional[List[str]] = None,
              experience_years: float = 0.0) -> Dict[str, Any]:
        """
        Score how well user_skills match role_requirements.

        Returns:
            {
                "overall_score": float [0..1],
                "grade": "Strong Match" | "Good Match" | "Possible Match" | "Skill Gap",
                "matched_skills": [...],
                "transferable_credits": [...],
                "certification_credits": [...],
                "missing_skills": [...],
                "breakdown": { component: score },
            }
        """
        certifications = certifications or []
        user_set = {s.lower().strip() for s in user_skills}
        req_set = {s.lower().strip() for s in role_requirements}
        cert_set = {c.lower().strip().replace(" ", "_") for c in certifications}

        # 1. Exact match
        exact_matches = user_set & req_set
        exact_score = len(exact_matches) / max(len(req_set), 1)

        # 2. Transferable skill credit
        transferable_credits = []
        transfer_score = 0.0
        for user_skill in user_set - exact_matches:
            key = user_skill.replace(" ", "_")
            mappings = self._transferable.get(key, [])
            for mapping in mappings:
                target = mapping.get("skill", "").lower()
                weight = mapping.get("weight", 0.0)
                if target in req_set and target not in exact_matches:
                    transferable_credits.append({"from": user_skill, "to": target, "weight": weight})
                    transfer_score += weight

        transfer_score = min(transfer_score / max(len(req_set), 1), 1.0)

        # 3. Certification bonus
        cert_credits = []
        cert_score = 0.0
        for cert in cert_set:
            mappings = self._cert_mappings.get(cert, [])
            for mapping in mappings:
                target = mapping.get("skill", "").lower()
                credit = mapping.get("credit", 0.0)
                if target in req_set:
                    cert_credits.append({"cert": cert, "skill": target, "credit": credit})
                    cert_score += credit

        cert_score = min(cert_score / max(len(req_set), 1), 1.0)

        # 4. Experience depth (simple linear scale, caps at 10 years)
        exp_score = min(experience_years / 10.0, 1.0)

        # 5. Semantic similarity placeholder (returns 0 unless embeddings are available)
        semantic_score = 0.0  # TODO: wire to embedding engine when available

        # Weighted overall score
        overall = (
            self._weights.get("exact_skill_match", 0.35) * exact_score
            + self._weights.get("semantic_similarity", 0.25) * semantic_score
            + self._weights.get("transferable_skills", 0.15) * transfer_score
            + self._weights.get("certification_bonus", 0.10) * cert_score
            + self._weights.get("experience_depth", 0.15) * exp_score
        )

        # Grade
        if overall >= self._thresholds.get("strong_match", 0.80):
            grade = "Strong Match"
        elif overall >= self._thresholds.get("moderate_match", 0.55):
            grade = "Good Match"
        elif overall >= self._thresholds.get("weak_match", 0.30):
            grade = "Possible Match"
        else:
            grade = "Skill Gap"

        missing = req_set - exact_matches - {tc["to"] for tc in transferable_credits}

        return {
            "overall_score": round(overall, 3),
            "grade": grade,
            "matched_skills": sorted(exact_matches),
            "transferable_credits": transferable_credits,
            "certification_credits": cert_credits,
            "missing_skills": sorted(missing),
            "breakdown": {
                "exact_skill_match": round(exact_score, 3),
                "semantic_similarity": round(semantic_score, 3),
                "transferable_skills": round(transfer_score, 3),
                "certification_bonus": round(cert_score, 3),
                "experience_depth": round(exp_score, 3),
            },
        }


# ── Module-level singletons ─────────────────────────────────────────────
career_rules = CareerRules()
skill_matcher = SkillMatcher()
