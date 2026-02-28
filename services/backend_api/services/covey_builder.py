from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import json
import math

from services.backend_api.models.spider_covey import (
    ActionBecause,
    CoveyAction,
    CoveyActionLens,
    SpiderAxis,
    SpiderProfile,
)

DEFAULT_QUADRANT_SPLIT_X = 50.0
DEFAULT_QUADRANT_SPLIT_Y = 50.0
DEFAULT_PEER_TARGET_PERCENTILE = 60.0
IMPACT_BASELINE = 10.0
IMPACT_SCALE = 0.015
EFFORT_TIME_WEIGHT = 0.55
EFFORT_COMPLEXITY_WEIGHT = 0.25
EFFORT_DEPENDENCY_WEIGHT = 0.20

DEFAULT_JOB_FAMILY_WEIGHTS: Dict[str, Dict[str, float]] = {
    "default": {
        "role_fit": 1.20,
        "domain_fit": 1.10,
        "evidence_strength": 1.30,
        "ats_coverage": 1.25,
        "clarity_structure": 1.15,
        "recency": 1.05,
        "leadership_scope": 1.10,
        "project_proof": 1.15,
        "consistency": 1.00,
    }
}


@dataclass(frozen=True)
class ActionTemplate:
    action_id: str
    title: str
    description: str
    axis_effects: Dict[str, int]
    steps: List[str]
    example_prompts: List[str]
    tags: List[str]
    meta: Dict[str, Any]


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def load_action_library_from_json(path: str | Path) -> List[ActionTemplate]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    raw = json.loads(file_path.read_text(encoding="utf-8"))
    templates: List[ActionTemplate] = []
    for item in raw:
        axis_effects = item.get("axis_effects") or {}
        if not axis_effects:
            continue
        templates.append(
            ActionTemplate(
                action_id=item["action_id"],
                title=item.get("title", item["action_id"]),
                description=item.get("description", ""),
                axis_effects=axis_effects,
                steps=item.get("steps", []),
                example_prompts=item.get("example_prompts", []),
                tags=item.get("tags", []),
                meta=item.get("meta", {}),
            )
        )
    return templates


def _index_spider_axes(spider: SpiderProfile) -> Dict[str, SpiderAxis]:
    return {axis.key: axis for axis in spider.axes}


def _get_job_family_weights(job_family: str) -> Dict[str, float]:
    return DEFAULT_JOB_FAMILY_WEIGHTS.get(job_family) or DEFAULT_JOB_FAMILY_WEIGHTS["default"]


def _gap_size_for_axis(axis: SpiderAxis, peer_target: float = DEFAULT_PEER_TARGET_PERCENTILE) -> float:
    if axis.peer_percentile is not None:
        gap = max(0.0, peer_target - float(axis.peer_percentile))
        return min(100.0, gap * (100.0 / peer_target))
    return float(max(0, 100 - axis.score))


def _confidence(axis: SpiderAxis) -> float:
    c = float(axis.confidence) if axis.confidence is not None else 0.6
    return min(1.0, max(0.05, c))


def _clip_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _compute_impact_potential(
    action: ActionTemplate,
    axes_index: Dict[str, SpiderAxis],
    axis_weights: Dict[str, float],
) -> Tuple[float, List[str], Dict[str, float], List[str]]:
    raw_sum = 0.0
    driving_axes: List[str] = []
    driving_peer_percentiles: Dict[str, float] = {}
    missing_union: List[str] = []

    for axis_key, effect in action.axis_effects.items():
        axis = axes_index.get(axis_key)
        if axis is None:
            continue

        gap = _gap_size_for_axis(axis)
        weight = float(axis_weights.get(axis_key, 1.0))
        confidence = _confidence(axis)
        effect_size = float(abs(effect))

        raw_sum += gap * weight * confidence * effect_size
        driving_axes.append(axis_key)

        if axis.peer_percentile is not None:
            driving_peer_percentiles[axis_key] = float(axis.peer_percentile)

        for missing in axis.missing_evidence:
            if missing not in missing_union:
                missing_union.append(missing)

    impact = 100.0 * (1.0 - math.exp(-IMPACT_SCALE * raw_sum))
    impact = _clip_0_100(IMPACT_BASELINE + impact)
    return impact, driving_axes, driving_peer_percentiles, missing_union


def _compute_effort_friction(action: ActionTemplate) -> float:
    meta = action.meta or {}
    time_minutes = float(meta.get("time_minutes", 45))
    complexity = float(meta.get("complexity", 2.5))
    dependency = float(meta.get("dependency", 0.2))

    time_score = _clip_0_100((time_minutes / 180.0) * 100.0)
    complexity_score = _clip_0_100(((complexity - 1.0) / 4.0) * 100.0)
    dependency_score = _clip_0_100(dependency * 100.0)

    return _clip_0_100(
        EFFORT_TIME_WEIGHT * time_score
        + EFFORT_COMPLEXITY_WEIGHT * complexity_score
        + EFFORT_DEPENDENCY_WEIGHT * dependency_score
    )


def _assign_quadrant(effort: float, impact: float, split_x: float, split_y: float) -> str:
    high_effort = effort >= split_x
    high_impact = impact >= split_y

    if high_impact and not high_effort:
        return "Q1"
    if high_impact and high_effort:
        return "Q2"
    if (not high_impact) and (not high_effort):
        return "Q3"
    return "Q4"


def _action_to_covey_action(
    action: ActionTemplate,
    spider: SpiderProfile,
    axes_index: Dict[str, SpiderAxis],
    axis_weights: Dict[str, float],
    split_x: float,
    split_y: float,
) -> CoveyAction:
    impact, driving_axes, driving_peer_percentiles, missing_union = _compute_impact_potential(
        action=action,
        axes_index=axes_index,
        axis_weights=axis_weights,
    )
    effort = _compute_effort_friction(action)
    quadrant = _assign_quadrant(effort, impact, split_x, split_y)

    confidence_values = [_confidence(axes_index[k]) for k in driving_axes if k in axes_index]
    action_confidence = (sum(confidence_values) / len(confidence_values)) if confidence_values else 0.65

    because = ActionBecause(
        gap_axis_keys=driving_axes,
        gap_peer_percentiles=driving_peer_percentiles,
        missing_evidence=missing_union[:12],
        notes=[
            f"Job family: {spider.job_family}",
            "This action is plotted because it improves the spider axes listed above.",
        ],
    )

    return CoveyAction(
        action_id=action.action_id,
        title=action.title,
        description=action.description,
        effort_friction=effort,
        impact_potential=impact,
        quadrant=quadrant,
        axis_effects=action.axis_effects,
        steps=action.steps,
        example_prompts=action.example_prompts,
        confidence=max(0.0, min(1.0, action_confidence)),
        because=because,
        tags=action.tags,
        meta=action.meta,
    )


def build_covey_action_lens(
    spider: SpiderProfile,
    action_templates: List[ActionTemplate],
    *,
    lens_id: str = "covey_relevance_actions",
    title: str = "Relevance Covey (Spider to Actions)",
    split_x: float = DEFAULT_QUADRANT_SPLIT_X,
    split_y: float = DEFAULT_QUADRANT_SPLIT_Y,
    top_n: int = 30,
) -> CoveyActionLens:
    axes_index = _index_spider_axes(spider)
    axis_weights = _get_job_family_weights(spider.job_family)

    actions: List[CoveyAction] = []
    for template in action_templates:
        if not template.axis_effects:
            continue
        if not any(axis in axes_index for axis in template.axis_effects):
            continue

        actions.append(
            _action_to_covey_action(
                action=template,
                spider=spider,
                axes_index=axes_index,
                axis_weights=axis_weights,
                split_x=split_x,
                split_y=split_y,
            )
        )

    actions.sort(key=lambda action: (-action.impact_potential, action.effort_friction))
    if top_n > 0:
        actions = actions[:top_n]

    return CoveyActionLens(
        lens_id=lens_id,
        title=title,
        spider_profile_id=spider.profile_id,
        cohort_id=spider.cohort_id,
        job_family=spider.job_family,
        actions=actions,
        created_at_iso=_utc_now_iso(),
    )
