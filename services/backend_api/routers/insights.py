
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
import logging
import statistics

logger = logging.getLogger(__name__)

# Try to import DataLoader — graceful fallback if not available
try:
    from services.ai_engine.data_loader import DataLoader
    _HAS_LOADER = True
except ImportError:
    _HAS_LOADER = False
    DataLoader = None  # type: ignore

router = APIRouter(prefix="/api/insights/v1", tags=["insights"])

# Visual registry path (shared with mapping router)
_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "visual_registry.json"

def get_loader():
    if not _HAS_LOADER:
        return None
    return DataLoader.get_instance()


STRUCTURAL_AXES: Dict[str, List[str]] = {
    "strategic": [
        "strategy_formulation",
        "vision_clarity",
        "long_term_thinking",
        "market_positioning",
        "risk_modelling",
        "resource_allocation",
        "sequencing_judgement",
        "influence_without_authority",
    ],
    "leadership": [
        "leadership_presence",
        "stakeholder_alignment",
        "communication_clarity",
        "delegation",
        "performance_calibration",
        "cultural_awareness",
        "conflict_handling",
        "executive_narrative",
    ],
    "operational": [
        "functional_expertise",
        "process_design",
        "kpi_literacy",
        "operational_scaling",
        "execution_discipline",
        "reporting_rigour",
        "compliance_understanding",
        "delivery_mechanics",
    ],
}

AXIS_KEYWORDS: Dict[str, List[str]] = {
    "strategy_formulation": ["strategy", "strategic", "roadmap", "positioning", "portfolio"],
    "vision_clarity": ["vision", "mission", "north star", "direction"],
    "long_term_thinking": ["long-term", "long term", "future", "multi-year", "horizon"],
    "market_positioning": ["market", "competitive", "positioning", "go-to-market", "gtm"],
    "risk_modelling": ["risk", "scenario", "sensitivity", "mitigation", "exposure"],
    "resource_allocation": ["allocation", "budget", "prioritization", "headcount", "capital"],
    "sequencing_judgement": ["sequencing", "phasing", "timeline", "dependencies", "milestones"],
    "influence_without_authority": ["influence", "cross-functional", "stakeholder", "alignment"],
    "leadership_presence": ["lead", "leadership", "director", "head of", "vp", "chief"],
    "stakeholder_alignment": ["stakeholder", "alignment", "consensus", "buy-in"],
    "communication_clarity": ["communication", "present", "storytelling", "narrative", "briefing"],
    "delegation": ["delegate", "delegation", "empower", "ownership transfer"],
    "performance_calibration": ["performance", "coaching", "feedback", "calibration", "okr"],
    "cultural_awareness": ["culture", "values", "inclusion", "team climate"],
    "conflict_handling": ["conflict", "resolve", "mediation", "escalation"],
    "executive_narrative": ["board", "executive", "narrative", "strategy update", "leadership team"],
    "functional_expertise": ["finance", "engineering", "marketing", "product", "operations", "sales"],
    "process_design": ["process", "workflow", "playbook", "sop", "design"],
    "kpi_literacy": ["kpi", "metric", "dashboard", "measure", "instrumentation"],
    "operational_scaling": ["scale", "scaling", "throughput", "capacity", "runbook"],
    "execution_discipline": ["execution", "delivery", "cadence", "deadline", "discipline"],
    "reporting_rigour": ["reporting", "governance", "status", "audit", "tracking"],
    "compliance_understanding": ["compliance", "regulation", "policy", "controls", "gdpr"],
    "delivery_mechanics": ["implementation", "rollout", "operations", "production", "qa"],
}


def _profile_text_blob(profile: Dict[str, Any]) -> str:
    parts: List[str] = [
        str(profile.get("summary") or ""),
        str(profile.get("role") or ""),
        str(profile.get("industry") or ""),
        " ".join([str(s) for s in (profile.get("skills") or [])]),
    ]

    exp = profile.get("experience") or profile.get("work_experience") or []
    if isinstance(exp, list):
        for item in exp:
            if isinstance(item, dict):
                parts.append(str(item.get("title") or ""))
                parts.append(str(item.get("description") or ""))
            else:
                parts.append(str(item))

    return " ".join([p for p in parts if p]).lower()


def _axis_score(text: str, axis: str) -> float:
    keywords = AXIS_KEYWORDS.get(axis, [])
    if not keywords:
        return 0.0
    hits = sum(1 for kw in keywords if kw in text)
    # 0-10 scale with saturation
    return float(min(10.0, 2.0 + (hits * 1.5))) if hits else 0.0


def _domain_series_from_text(text: str) -> Dict[str, List[float]]:
    result: Dict[str, List[float]] = {}
    for domain, axes in STRUCTURAL_AXES.items():
        result[domain] = [round(_axis_score(text, axis), 2) for axis in axes]
    return result


def _percentile(value: float, cohort_values: List[float]) -> float:
    if not cohort_values:
        return 50.0
    lower = sum(1 for item in cohort_values if item <= value)
    return round((lower / max(len(cohort_values), 1)) * 100.0, 1)


def _shape_label(strategic: float, leadership: float, operational: float) -> str:
    if operational >= 7.5 and strategic <= 5.0:
        return "tactical_expert_strategic_underdeveloped"
    if strategic >= 7.5 and operational <= 5.0:
        return "visionary_without_grounding"
    if leadership <= 4.8 and operational >= 6.5:
        return "manager_not_leader"
    if leadership >= 7.0 and strategic <= 5.0 and operational <= 5.0:
        return "leader_without_structural_grounding"
    return "balanced_profile"


def _structural_response(
    profiles: List[Dict[str, Any]],
    profile_id: Optional[str] = None,
    target_role: Optional[str] = None,
    spider_option: str = "three_domain",
) -> Dict[str, Any]:
    if not profiles:
        return {
            "model": "structural_v1",
            "axes": ["Strategic", "Leadership", "Operational"],
            "series": [],
            "domains": {},
            "overview": {},
            "spider_options": [
                "three_domain",
                "leadership_strategy_vision_management",
                "operational_execution",
            ],
            "selected_spider_option": spider_option,
        }

    user_profile = None
    if profile_id:
        user_profile = next((p for p in profiles if p.get("id") == profile_id), None)
    if user_profile is None:
        user_profile = profiles[0]

    user_text = _profile_text_blob(user_profile)
    user_domains = _domain_series_from_text(user_text)

    cohort_domain_scores: Dict[str, List[float]] = {"strategic": [], "leadership": [], "operational": []}
    target_domain_scores: Dict[str, List[float]] = {"strategic": [], "leadership": [], "operational": []}

    target_needle = (target_role or "").strip().lower()

    for profile in profiles:
        text = _profile_text_blob(profile)
        domain_series = _domain_series_from_text(text)
        domain_means = {
            d: round(sum(vals) / max(len(vals), 1), 2)
            for d, vals in domain_series.items()
        }
        for domain in cohort_domain_scores:
            cohort_domain_scores[domain].append(domain_means[domain])

        role_value = str(profile.get("role") or "").strip().lower()
        if target_needle and target_needle in role_value:
            for domain in target_domain_scores:
                target_domain_scores[domain].append(domain_means[domain])

    peer_median = {
        domain: round(statistics.median(values), 2) if values else 0.0
        for domain, values in cohort_domain_scores.items()
    }
    target_median = {
        domain: round(statistics.median(values), 2) if values else peer_median[domain]
        for domain, values in target_domain_scores.items()
    }

    user_domain_mean = {
        domain: round(sum(values) / max(len(values), 1), 2)
        for domain, values in user_domains.items()
    }

    strategic_score = user_domain_mean["strategic"]
    leadership_score = user_domain_mean["leadership"]
    operational_score = user_domain_mean["operational"]
    imbalance = round(strategic_score - operational_score, 2)
    coherence = round(max(0.0, 10.0 - abs(imbalance)), 2)

    options_payload: Dict[str, Dict[str, Any]] = {
        "three_domain": {
            "axes": ["Strategic", "Leadership", "Operational"],
            "user_values": [strategic_score, leadership_score, operational_score],
            "peer_median": [peer_median["strategic"], peer_median["leadership"], peer_median["operational"]],
            "target_role_median": [target_median["strategic"], target_median["leadership"], target_median["operational"]],
        },
        "leadership_strategy_vision_management": {
            "axes": STRUCTURAL_AXES["strategic"] + STRUCTURAL_AXES["leadership"],
            "user_values": user_domains["strategic"] + user_domains["leadership"],
            "peer_median": [round(peer_median["strategic"], 2)] * len(STRUCTURAL_AXES["strategic"]) + [round(peer_median["leadership"], 2)] * len(STRUCTURAL_AXES["leadership"]),
            "target_role_median": [round(target_median["strategic"], 2)] * len(STRUCTURAL_AXES["strategic"]) + [round(target_median["leadership"], 2)] * len(STRUCTURAL_AXES["leadership"]),
        },
        "operational_execution": {
            "axes": STRUCTURAL_AXES["operational"],
            "user_values": user_domains["operational"],
            "peer_median": [round(peer_median["operational"], 2)] * len(STRUCTURAL_AXES["operational"]),
            "target_role_median": [round(target_median["operational"], 2)] * len(STRUCTURAL_AXES["operational"]),
        },
    }

    selected_option = spider_option if spider_option in options_payload else "three_domain"

    domains_payload = {}
    for domain, axes in STRUCTURAL_AXES.items():
        domains_payload[domain] = {
            "axes": axes,
            "user_values": user_domains[domain],
            "peer_median": [peer_median[domain]] * len(axes),
            "target_role_median": [target_median[domain]] * len(axes),
            "domain_score": user_domain_mean[domain],
            "percentile": _percentile(user_domain_mean[domain], cohort_domain_scores[domain]),
            "delta_vs_peer_median": round(user_domain_mean[domain] - peer_median[domain], 2),
            "delta_vs_target_role": round(user_domain_mean[domain] - target_median[domain], 2),
        }

    return {
        "model": "structural_v1",
        "profile_id": user_profile.get("id"),
        "axes": ["Strategic", "Leadership", "Operational"],
        "series": [
            {
                "label": str(user_profile.get("role") or "You"),
                "values": [strategic_score, leadership_score, operational_score],
            },
            {
                "label": "Peer Median",
                "values": [peer_median["strategic"], peer_median["leadership"], peer_median["operational"]],
            },
        ],
        "overview": {
            "strategic_score": strategic_score,
            "leadership_score": leadership_score,
            "operational_score": operational_score,
            "structural_coherence_score": coherence,
            "strategic_operational_gap": imbalance,
            "profile_shape": _shape_label(strategic_score, leadership_score, operational_score),
        },
        "domains": domains_payload,
        "spider_options": list(options_payload.keys()),
        "selected_spider_option": selected_option,
        "option_chart": options_payload[selected_option],
    }

# ── B1: Visual catalogue endpoint ────────────────────────────────

@router.get("/visuals")
def get_visual_catalogue():
    """
    Returns the full visual registry catalogue.
    Used by VisualisationsHub to populate the sidebar dynamically.
    """
    if _REGISTRY_PATH.exists():
        with _REGISTRY_PATH.open("r", encoding="utf-8") as f:
            registry = json.load(f)
        return {"visuals": registry.get("visuals", [])}
    raise HTTPException(status_code=503, detail="Visual registry is not available")

# ── B2: Skills radar endpoint ────────────────────────────────────

@router.get("/skills/radar")
def get_skills_radar(
    loader=Depends(get_loader),
    profile_id: Optional[str] = None,
    model: str = Query("legacy", description="legacy | structural_v1"),
    spider_option: str = Query("three_domain", description="three_domain | leadership_strategy_vision_management | operational_execution"),
    target_role: Optional[str] = Query(None),
):
    """
    Returns radar / spider-chart data for a profile's skill coverage.
    Each axis = a skill category, value = normalised strength (0-100).
    If no profile_id given, returns aggregate cohort average.
    """
    if not isinstance(model, str):
        model = getattr(model, "default", "legacy")
    if not isinstance(spider_option, str):
        spider_option = getattr(spider_option, "default", "three_domain")
    if target_role is not None and not isinstance(target_role, str):
        target_role = getattr(target_role, "default", None)

    model_key = (model or "legacy").strip().lower()

    # Define canonical axes (top-level skill categories)
    axes = ["Technical", "Leadership", "Communication", "Domain", "Analytics", "Creativity"]

    if not loader:
        if model_key == "structural_v1":
            return _structural_response([], profile_id=profile_id, target_role=target_role, spider_option=spider_option)
        return {"axes": axes, "series": []}

    profiles = loader.get_profiles()

    if model_key == "structural_v1":
        return _structural_response(
            profiles=profiles,
            profile_id=profile_id,
            target_role=target_role,
            spider_option=spider_option,
        )

    if profile_id:
        profile = next((p for p in profiles if p["id"] == profile_id), None)
        if not profile:
            return {"axes": axes, "series": []}
        skills_set = {s.lower() for s in profile.get("skills", [])}
        # Simple heuristic: count skills that contain axis keyword
        values = [
            min(100, sum(1 for s in skills_set if ax.lower()[:4] in s) * 25)
            for ax in axes
        ]
        return {"axes": axes, "series": [{"label": profile.get("role", "You"), "values": values}]}

    # Aggregate: mean across all profiles
    totals = [0.0] * len(axes)
    n = max(len(profiles), 1)
    for p in profiles:
        skills_set = {s.lower() for s in p.get("skills", [])}
        for i, ax in enumerate(axes):
            totals[i] += sum(1 for s in skills_set if ax.lower()[:4] in s) * 25
    avg = [round(t / n, 1) for t in totals]
    return {"axes": axes, "series": [{"label": "Cohort Average", "values": avg}]}

@router.get("/quadrant")
def get_quadrant_data(
    loader=Depends(get_loader),
    industry: Optional[str] = None
):
    """
    Returns data for the Quadrant Chart (Positioning).
    X-Axis: Experience Years (0-100 normalized)
    Y-Axis: Match Score (0-100)
    """
    if not loader:
        return {
            "x_label": "Experience Level",
            "y_label": "Career Match Score",
            "x_threshold": 50,
            "y_threshold": 50,
            "points": [],
        }

    profiles = loader.get_profiles()
    
    # Filter
    if industry:
        profiles = [p for p in profiles if p.get("industry") == industry]

    points = []
    for p in profiles:
        # Normalize experience to 0-100 roughly (assume 20 years max for layout)
        exp_norm = min(100, (p["experience_years"] / 20) * 100)
        
        points.append({
            "id": p["id"],
            "label": p.get("role", "Candidate"),
            "x": exp_norm,
            "y": p["match_score"],
            "confidence": p.get("confidence", 0.8),
            "touchpoint_ids": [tp.get("id") for tp in p.get("touchpoints", [])]
        })

    return {
        "x_label": "Experience Level",
        "y_label": "Career Match Score",
        "x_threshold": 50,
        "y_threshold": 50,
        "points": points
    }

@router.get("/terms/cloud")
def get_term_cloud(loader: DataLoader = Depends(get_loader)):
    """
    Returns term frequency for Word Cloud.
    """
    if not loader:
        return {"terms": []}

    freq = loader.get_terms()
    # Convert to list
    terms = [{"text": k, "value": v} for k, v in freq.items()]
    # Sort and slice top 100
    terms.sort(key=lambda x: x["value"], reverse=True)
    return {"terms": terms[:100]}

@router.get("/terms/cooccurrence")
def get_cooccurrence(term: Optional[str] = None):
    """
    Returns co-occurrence data for the graph view.
    """
    return {"nodes": [], "edges": []}

@router.get("/graph")
def get_graph_data(loader: DataLoader = Depends(get_loader)):
    """
    Returns Cytoscape elements for Network Graph.
    Nodes: Profiles, Skills
    Edges: Profile -> Skill
    """
    if not loader:
        return []

    profiles = loader.get_profiles()[:20] # Limit for graph readability
    
    nodes = []
    edges = []
    
    # Add Profile Nodes
    for p in profiles:
        nodes.append({"data": {"id": p["id"], "label": p["role"], "type": "profile"}})
        
        # Add Skill Nodes and Edges
        for s in p.get("skills", [])[:5]:
            sid = f"skill_{s}"
            # Check if node exists (simple dedupe logic needed in prod, here we rely on cytoscape handling duplicates or just overwrite)
            nodes.append({"data": {"id": sid, "label": s, "type": "skill"}})
            edges.append({"data": {"source": p["id"], "target": sid, "label": "has_skill"}})

    return list({v['data']['id']:v for v in nodes}.values()) + edges # Dedupe nodes by ID

@router.post("/cohort/resolve")
def resolve_cohort(filters: Dict[str, Any]):
    return {"cohort_id": "cohort_empty", "count": 0}
