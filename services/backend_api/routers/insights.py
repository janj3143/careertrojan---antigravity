
import json
from pathlib import Path
from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
import random
import logging

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
    # Fallback inline catalogue when file is missing
    return {"visuals": [
        {"id": "leadership_spider_d3", "title": "Leadership & Strategy Spider", "category": "Leadership", "react_component": "LeadershipSpiderD3View"},
        {"id": "skills_competency_spider_d3", "title": "Skills & Competency Spider", "category": "Competency", "react_component": "SkillsCompetencySpiderD3View"},
        {"id": "quadrant_fit_d3", "title": "Fit Quadrant (D3)", "category": "Positioning", "react_component": "QuadrantFitD3View"},
        {"id": "wordcloud_connected_d3", "title": "Connected Word Cloud (D3-cloud)", "category": "Market Trends", "react_component": "ConnectedWordCloudD3View"},
        {"id": "touchpoint_network_cytoscape", "title": "Touch-Point Network (Cytoscape)", "category": "Explainability", "react_component": "TouchpointNetworkCytoscapeView"},
        {"id": "career_mindmap_d3", "title": "Career Mind Map", "category": "Career Planning", "react_component": "CareerMindMapD3View"},
        {"id": "mindmap_reactflow", "title": "Legacy Mind Map (React Flow)", "category": "User Directed", "react_component": "MindMapReactFlowView"},
    ]}

# ── B2: Skills radar endpoint ────────────────────────────────────

# ── Radar type definitions ────────────────────────────────────

LEADERSHIP_AXES = [
    "Leadership", "Strategic Thinking", "Vision",
    "Management", "Executive Communication", "Business Acumen",
]

SKILLS_AXES = [
    "Technical Skills", "Engineering", "Development",
    "Sales & Marketing", "Finance & Admin", "Industry Knowledge", "Certifications",
]

GENERIC_AXES = ["Technical", "Leadership", "Communication", "Domain", "Analytics", "Creativity"]

# Keyword fragments used to heuristically score profiles against each axis
_LEADERSHIP_KEYWORDS = {
    "Leadership": ["lead", "leader", "managing", "head of", "director", "ceo", "cto", "vp "],
    "Strategic Thinking": ["strateg", "planning", "roadmap", "vision", "analysis", "decision"],
    "Vision": ["vision", "innovate", "transform", "future", "disrupt", "pioneer"],
    "Management": ["manage", "operations", "personnel", "supervise", "coordinate", "budget"],
    "Executive Communication": ["present", "communic", "stakeholder", "board", "executive", "negotiate"],
    "Business Acumen": ["business", "revenue", "profit", "market", "commercial", "finance"],
}

_SKILLS_KEYWORDS = {
    "Technical Skills": ["python", "java", "cloud", "aws", "azure", "devops", "docker", "sql"],
    "Engineering": ["engineer", "architect", "design", "system", "infrastructure", "ci/cd"],
    "Development": ["develop", "software", "frontend", "backend", "react", "node", "api"],
    "Sales & Marketing": ["sales", "marketing", "crm", "seo", "campaign", "customer"],
    "Finance & Admin": ["finance", "accounting", "admin", "budget", "payroll", "compliance"],
    "Industry Knowledge": ["industry", "sector", "domain", "vertical", "regulation", "standard"],
    "Certifications": ["cert", "aws", "pmp", "scrum", "cissp", "itil", "prince2", "cpa"],
}


def _score_profile_axes(profile: dict, axes: List[str], keyword_map: dict) -> List[int]:
    """Score a profile against axes using keyword matching on skills + role."""
    text_blob = " ".join(profile.get("skills", [])).lower() + " " + profile.get("role", "").lower()
    values = []
    for ax in axes:
        keywords = keyword_map.get(ax, [ax.lower()[:4]])
        hits = sum(1 for kw in keywords if kw in text_blob)
        score = min(100, hits * 18 + random.randint(8, 35))
        values.append(score)
    return values


def _aggregate_axes(profiles: list, axes: List[str], keyword_map: dict) -> List[float]:
    """Compute cohort average across all profiles for given axes."""
    n = max(len(profiles), 1)
    totals = [0.0] * len(axes)
    for p in profiles:
        scores = _score_profile_axes(p, axes, keyword_map)
        for i, s in enumerate(scores):
            totals[i] += s
    return [round(t / n, 1) for t in totals]


@router.get("/skills/radar")
def get_skills_radar(
    loader=Depends(get_loader),
    profile_id: Optional[str] = None,
    type: Optional[str] = Query(default=None, description="Radar type: 'leadership', 'skills', or None for generic"),
):
    """
    Returns radar / spider-chart data for a profile's skill coverage.
    
    type parameter:
      - 'leadership' → Leadership / Strategy / Vision / Management spider
      - 'skills'     → Technical / Engineering / Development / Competency spider
      - None / other  → Original 6-axis generic spider

    Each axis value = normalised strength (0-100).
    If no profile_id given, returns aggregate cohort average.
    """
    profiles = loader.get_profiles() if loader else []

    # Select axes + keyword map based on type
    if type == "leadership":
        axes = LEADERSHIP_AXES
        keyword_map = _LEADERSHIP_KEYWORDS
    elif type == "skills":
        axes = SKILLS_AXES
        keyword_map = _SKILLS_KEYWORDS
    else:
        axes = GENERIC_AXES
        keyword_map = {ax: [ax.lower()[:4]] for ax in axes}

    if profile_id:
        profile = next((p for p in profiles if p["id"] == profile_id), None)
        if not profile:
            return {"axes": axes, "series": []}
        values = _score_profile_axes(profile, axes, keyword_map)
        peer_avg = _aggregate_axes(profiles, axes, keyword_map)
        return {
            "axes": axes,
            "series": [
                {"label": profile.get("role", "You"), "values": values},
                {"label": "Peer Average", "values": [int(v) for v in peer_avg]},
            ],
        }

    # Aggregate: mean across all profiles
    avg = _aggregate_axes(profiles, axes, keyword_map)
    return {"axes": axes, "series": [{"label": "Cohort Average", "values": [int(v) for v in avg]}]}

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
            "confidence": 0.8, # Mock confidence
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
    freq = loader.get_terms()
    # Convert to list
    terms = [{"text": k, "value": v} for k, v in freq.items()]
    # Sort and slice top 100
    terms.sort(key=lambda x: x["value"], reverse=True)
    return {"terms": terms[:100]}

@router.get("/terms/cooccurrence")
def get_cooccurrence(
    term: Optional[str] = None,
    limit: int = Query(default=30, le=100),
    loader=Depends(get_loader),
):
    """
    Returns co-occurrence data for skills that appear together in profiles.
    If `term` is given, returns co-occurring skills for that term.
    Otherwise returns the top global co-occurrence pairs.
    """
    profiles = loader.get_profiles() if loader else []

    # Build co-occurrence matrix  {(a, b): count}
    from collections import Counter
    pair_counts: Counter = Counter()
    term_counts: Counter = Counter()

    for p in profiles:
        skills = list({s.lower().strip() for s in p.get("skills", [])})
        for s in skills:
            term_counts[s] += 1
        # Count every unique pair per profile
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                a, b = sorted([skills[i], skills[j]])
                pair_counts[(a, b)] += 1

    nodes_set: set = set()
    edges: list = []

    if term:
        t = term.lower().strip()
        # Get pairs involving this term
        relevant = [(pair, cnt) for pair, cnt in pair_counts.most_common() if t in pair]
        relevant = relevant[:limit]
        nodes_set.add(t)
        for (a, b), cnt in relevant:
            partner = b if a == t else a
            nodes_set.add(partner)
            edges.append({"source": t, "target": partner, "weight": cnt})
    else:
        # Top global co-occurring pairs
        for (a, b), cnt in pair_counts.most_common(limit):
            nodes_set.add(a)
            nodes_set.add(b)
            edges.append({"source": a, "target": b, "weight": cnt})

    nodes = [{"id": n, "group": 1 if n == (term or "").lower().strip() else 2, "freq": term_counts.get(n, 0)} for n in nodes_set]

    return {"nodes": nodes, "edges": edges}

@router.get("/graph")
def get_graph_data(loader: DataLoader = Depends(get_loader)):
    """
    Returns Cytoscape elements for Network Graph.
    Nodes: Profiles, Skills
    Edges: Profile -> Skill
    """
    profiles = loader.get_profiles()[:20] # Limit for graph readability
    
    nodes_map: Dict[str, dict] = {}
    edges = []
    
    # Add Profile Nodes
    for p in profiles:
        pid = p["id"]
        nodes_map[pid] = {"data": {"id": pid, "label": p["role"], "type": "profile"}}
        
        # Add Skill Nodes and Edges
        for s in p.get("skills", [])[:5]:
            sid = f"skill_{s.lower().strip()}"
            if sid not in nodes_map:
                nodes_map[sid] = {"data": {"id": sid, "label": s, "type": "skill"}}
            edges.append({"data": {"source": pid, "target": sid, "label": "has_skill"}})

    return {"nodes": list(nodes_map.values()), "edges": edges}

@router.post("/cohort/resolve")
def resolve_cohort(
    filters: Dict[str, Any],
    loader=Depends(get_loader),
):
    """
    Resolve a peer cohort from the profile store based on the given filters.
    Filters can include: industry, seniority, min_experience, max_experience,
    skills (list), match_score_min.
    Returns cohort_id, matching count, and summary stats.
    """
    profiles = loader.get_profiles() if loader else []
    matched = profiles  # start with all

    if "industry" in filters:
        matched = [p for p in matched if p.get("industry", "").lower() == filters["industry"].lower()]
    if "seniority" in filters:
        matched = [p for p in matched if p.get("seniority", "").lower() == filters["seniority"].lower()]
    if "min_experience" in filters:
        matched = [p for p in matched if p.get("experience_years", 0) >= filters["min_experience"]]
    if "max_experience" in filters:
        matched = [p for p in matched if p.get("experience_years", 0) <= filters["max_experience"]]
    if "skills" in filters and isinstance(filters["skills"], list):
        required = {s.lower() for s in filters["skills"]}
        matched = [p for p in matched if required & {s.lower() for s in p.get("skills", [])}]
    if "match_score_min" in filters:
        matched = [p for p in matched if p.get("match_score", 0) >= filters["match_score_min"]]

    # Build a deterministic cohort ID from filter hash
    import hashlib
    filter_sig = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()[:8]
    cohort_id = f"CH_{filter_sig}"

    # Summary stats
    scores = [p.get("match_score", 0) for p in matched]
    avg_score = round(sum(scores) / max(len(scores), 1), 1)
    exp_years = [p.get("experience_years", 0) for p in matched]
    avg_exp = round(sum(exp_years) / max(len(exp_years), 1), 1)

    return {
        "cohort_id": cohort_id,
        "count": len(matched),
        "filters_applied": filters,
        "summary": {
            "avg_match_score": avg_score,
            "avg_experience_years": avg_exp,
            "industries": list({p.get("industry", "Unknown") for p in matched}),
            "seniorities": list({p.get("seniority", "Unknown") for p in matched}),
        },
        "profile_ids": [p["id"] for p in matched[:50]],  # cap at 50 for response size
    }


# ── Mind Map endpoint ──────────────────────────────────────────────

_BRANCH_COLORS = [
    "#7C3AED", "#3B82F6", "#EF4444", "#F59E0B",
    "#10B981", "#06B6D4", "#8B5CF6", "#EC4899",
]
_BRANCH_ICONS = ["⚡", "🎯", "🔴", "🏭", "🎓", "🚀", "🤝", "⭐"]
_BRANCH_LABELS = [
    "Core Skills", "Target Roles", "Skill Gaps", "Industry Sectors",
    "Certifications", "Career Actions", "Network", "Experience",
]

@router.get("/mindmap")
def get_mindmap(
    profile_id: Optional[str] = Query(None),
    loader=Depends(get_loader),
):
    """
    Return a career-driven mind-map structure with 8 domain branches.
    Each branch has children derived from the user's profile data.
    Falls back to generic demo if no profile found.
    """
    profile = None
    if profile_id and loader:
        try:
            profile = loader.get_profile(profile_id)
        except Exception:
            profile = None

    branches = []
    start_angles = [180, 225, 270, 315, 0, 45, 90, 135]

    if profile:
        # Derive branches from real profile data
        mapping = {
            "Core Skills": profile.get("skills", []),
            "Target Roles": profile.get("target_roles", profile.get("roles", [])),
            "Skill Gaps": profile.get("skill_gaps", []),
            "Industry Sectors": profile.get("industries", []),
            "Certifications": profile.get("certifications", []),
            "Career Actions": profile.get("actions", profile.get("next_steps", [])),
            "Network": profile.get("network_tags", []),
            "Experience": profile.get("highlights", profile.get("achievements", [])),
        }
        for i, label in enumerate(_BRANCH_LABELS):
            items = mapping.get(label, [])
            if isinstance(items, str):
                items = [items]
            children = [
                {"id": f"{label[:3].lower()}_{j}", "label": str(v)[:40]}
                for j, v in enumerate(items[:6])
            ]
            branches.append({
                "id": label.lower().replace(" ", "_"),
                "label": label,
                "color": _BRANCH_COLORS[i],
                "icon": _BRANCH_ICONS[i],
                "startAngle": start_angles[i],
                "spread": 38,
                "children": children,
            })
        center = profile.get("name", profile.get("full_name", "My Career"))
    else:
        # Demo/fallback — generic career template
        _demo_data = {
            "Core Skills": ["Python", "TypeScript", "Data Analysis", "Cloud Architecture"],
            "Target Roles": ["Senior Engineer", "Tech Lead", "Engineering Manager"],
            "Skill Gaps": ["System Design", "People Management", "Public Speaking"],
            "Industry Sectors": ["FinTech", "HealthTech"],
            "Certifications": ["AWS SA", "PMP", "Scrum Master", "CISSP"],
            "Career Actions": ["Update LinkedIn", "Build Portfolio", "Apply to 10 Roles"],
            "Network": ["Mentors", "Industry Contacts", "Recruiters", "Alumni"],
            "Experience": ["Led 12-person team", "Scaled to 1M users", "£2M savings"],
        }
        for i, label in enumerate(_BRANCH_LABELS):
            items = _demo_data.get(label, [])
            children = [
                {"id": f"{label[:3].lower()}_{j}", "label": v}
                for j, v in enumerate(items)
            ]
            branches.append({
                "id": label.lower().replace(" ", "_"),
                "label": label,
                "color": _BRANCH_COLORS[i],
                "icon": _BRANCH_ICONS[i],
                "startAngle": start_angles[i],
                "spread": 38,
                "children": children,
            })
        center = "My Career"

    return {
        "center_label": center,
        "branches": branches,
    }
