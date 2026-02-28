"""
CareerTrojan — Expert System
============================
Rule-based consistency checks and explainability helpers for AI predictions.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import logging


logger = logging.getLogger("ExpertSystem")


@dataclass
class Rule:
    rule_id: str
    name: str
    category: str
    priority: int
    enabled: bool
    condition: Dict[str, Any]
    action: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExpertSystemEngine:
    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = Path(rules_path) if rules_path else Path(__file__).resolve().parent / "expert_rules.json"
        self.rules: List[Rule] = []
        self._load_or_initialize_rules()

    def _load_or_initialize_rules(self) -> None:
        if self.rules_path.exists():
            try:
                payload = json.loads(self.rules_path.read_text(encoding="utf-8"))
                self.rules = [Rule(**item) for item in payload if isinstance(item, dict)]
                return
            except Exception as exc:
                logger.warning("Failed loading expert rules from %s: %s", self.rules_path, exc)

        self.rules = self._default_rules()
        self.save_rules()

    def _default_rules(self) -> List[Rule]:
        return [
            Rule(
                rule_id="ES001",
                name="Senior requires experience",
                category="job_title",
                priority=9,
                enabled=True,
                condition={"prediction_contains": ["senior"], "experience_lt": 5},
                action="lower_confidence",
                message="Prediction includes senior but candidate experience is below 5 years.",
            ),
            Rule(
                rule_id="ES002",
                name="Developer requires core technical skills",
                category="skills",
                priority=8,
                enabled=True,
                condition={"prediction_contains": ["developer", "engineer"], "skills_any": ["python", "java", "javascript", "sql"]},
                action="flag_missing_skills",
                message="Technical role predicted without expected technical skills evidence.",
            ),
            Rule(
                rule_id="ES003",
                name="Sales profile contamination trap",
                category="contamination",
                priority=10,
                enabled=True,
                condition={"profile_contains": ["sales", "account executive", "business development"], "prediction_contains": ["python developer", "machine learning engineer"]},
                action="reject_prediction",
                message="Sales profile appears contaminated by technical fallback classes.",
            ),
        ]

    def save_rules(self) -> None:
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [rule.to_dict() for rule in self.rules]
        self.rules_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list_rules(self, category: Optional[str] = None, enabled_only: bool = False) -> List[Dict[str, Any]]:
        selected = self.rules
        if category:
            selected = [rule for rule in selected if rule.category == category]
        if enabled_only:
            selected = [rule for rule in selected if rule.enabled]
        return [rule.to_dict() for rule in sorted(selected, key=lambda r: r.priority, reverse=True)]

    def evaluate_prediction(
        self,
        prediction: str,
        profile_text: str = "",
        skills: Optional[List[str]] = None,
        experience_years: int = 0,
    ) -> Dict[str, Any]:
        prediction_l = (prediction or "").lower()
        profile_l = (profile_text or "").lower()
        skills_l = {str(skill).lower() for skill in (skills or [])}

        triggered: List[Dict[str, Any]] = []
        confidence_modifier = 1.0
        hard_reject = False

        for rule in sorted([rule for rule in self.rules if rule.enabled], key=lambda r: r.priority, reverse=True):
            condition = rule.condition
            matched = True

            contains_prediction = condition.get("prediction_contains", [])
            if contains_prediction and not any(token in prediction_l for token in contains_prediction):
                matched = False

            contains_profile = condition.get("profile_contains", [])
            if matched and contains_profile and not any(token in profile_l for token in contains_profile):
                matched = False

            experience_lt = condition.get("experience_lt")
            if matched and experience_lt is not None and not (experience_years < int(experience_lt)):
                matched = False

            expected_skills = condition.get("skills_any", [])
            if matched and expected_skills and not any(skill in skills_l for skill in expected_skills):
                matched = False

            if not matched:
                continue

            triggered.append(
                {
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "action": rule.action,
                    "message": rule.message,
                    "priority": rule.priority,
                }
            )

            if rule.action == "lower_confidence":
                confidence_modifier *= 0.8
            elif rule.action == "flag_missing_skills":
                confidence_modifier *= 0.75
            elif rule.action == "reject_prediction":
                hard_reject = True

        return {
            "valid": not hard_reject,
            "confidence_modifier": round(confidence_modifier, 4),
            "triggered_rules": triggered,
        }


def get_expert_system(rules_path: Optional[str] = None) -> ExpertSystemEngine:
    return ExpertSystemEngine(rules_path=rules_path)
