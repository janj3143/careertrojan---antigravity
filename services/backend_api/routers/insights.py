
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

def get_loader():
    if not _HAS_LOADER:
        return None
    return DataLoader.get_instance()

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
def get_cooccurrence(term: Optional[str] = None):
    """
    Returns dummy co-occurrence data for the graph view.
    Real impl would analyze profile skill sets.
    """
    # Mock data for phase 2 demo
    nodes = []
    edges = []
    if term:
        # Generate some related terms
        related = [f"{term}_{i}" for i in range(5)]
        nodes = [{"id": term, "group": 1}] + [{"id": r, "group": 2} for r in related]
        edges = [{"source": term, "target": r, "weight": random.randint(1, 10)} for r in related]
    
    return {"nodes": nodes, "edges": edges}

@router.get("/graph")
def get_graph_data(loader: DataLoader = Depends(get_loader)):
    """
    Returns Cytoscape elements for Network Graph.
    Nodes: Profiles, Skills
    Edges: Profile -> Skill
    """
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
    return {"cohort_id": "CH_001", "count": 125}
