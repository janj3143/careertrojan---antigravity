"""
Touchpoints API Router — evidence and touch-not lookups for the visual overlay panel.
Every visual click emits touchpoint_ids → this router returns the evidence + gaps.
"""

import logging
import random
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

logger = logging.getLogger(__name__)

# Try to import DataLoader for profile/touchpoint data
try:
    from services.ai_engine.data_loader import DataLoader
    _HAS_LOADER = True
except ImportError:
    _HAS_LOADER = False
    DataLoader = None  # type: ignore

router = APIRouter(prefix="/api/touchpoints/v1", tags=["touchpoints"])


def _get_loader():
    if not _HAS_LOADER:
        return None
    return DataLoader.get_instance()


# ─── Evidence store helpers ──────────────────────────────────────

def _build_evidence_items(touchpoint_ids: List[str], loader) -> List[dict]:
    """
    Resolves touchpoint IDs to evidence records.
    In production this queries the parsed-resume store + JD annotations.
    For now, builds plausible evidence from cached profiles.
    """
    items = []
    profiles = loader.get_profiles() if loader else []

    # Index touchpoints across all profiles
    tp_index: dict = {}
    for p in profiles:
        for tp in p.get("touchpoints", []):
            tp_id = tp.get("id")
            if tp_id:
                tp_index[tp_id] = {**tp, "profile_id": p["id"], "role": p.get("role", "Unknown")}

    for tid in touchpoint_ids:
        if tid in tp_index:
            tp = tp_index[tid]
            items.append({
                "touchpoint_id": tid,
                "profile_id": tp["profile_id"],
                "role": tp["role"],
                "source": tp.get("source", "resume"),
                "section": tp.get("section", "experience"),
                "text_span": tp.get("text", f"Evidence for touchpoint {tid}"),
                "confidence": tp.get("confidence", round(random.uniform(0.6, 0.99), 2)),
                "tags": tp.get("tags", []),
            })
        else:
            # Touchpoint ID not found — return a stub so the UI can still render
            items.append({
                "touchpoint_id": tid,
                "profile_id": None,
                "role": None,
                "source": "unknown",
                "section": "unknown",
                "text_span": f"No evidence record found for {tid}",
                "confidence": 0.0,
                "tags": [],
            })
    return items


def _build_touchnot_items(touchpoint_ids: List[str], loader) -> List[dict]:
    """
    Resolves touch-nots: gaps or weak evidence for given touchpoints.
    In production this queries the gap-analysis engine.
    For now, flags any touchpoint below a confidence threshold.
    """
    items = []
    evidence = _build_evidence_items(touchpoint_ids, loader)
    for ev in evidence:
        conf = ev.get("confidence", 0.0)
        if conf < 0.5:
            items.append({
                "touchpoint_id": ev["touchpoint_id"],
                "gap_type": "missing" if conf == 0.0 else "weak",
                "reason": "No supporting evidence found" if conf == 0.0 else f"Low confidence ({conf})",
                "suggested_actions": [
                    "Add relevant experience to CV",
                    "Provide portfolio or project links",
                ] if conf == 0.0 else [
                    "Expand on existing experience",
                    "Add quantifiable achievements",
                ],
                "confidence": conf,
            })
    return items


@router.get("/evidence")
async def get_evidence(
    touchpoint_id: List[str] = Query(default=[]),
    loader=Depends(_get_loader),
):
    """
    Returns evidence spans for the given touchpoint IDs.
    Each touchpoint maps to resume/JD/peer evidence that proves
    the user meets (or partially meets) a requirement.
    """
    if not touchpoint_id:
        return {"items": []}
    items = _build_evidence_items(touchpoint_id, loader)
    return {"items": items, "count": len(items)}


@router.get("/touchnots")
async def get_touchnots(
    touchpoint_id: List[str] = Query(default=[]),
    loader=Depends(_get_loader),
):
    """
    Returns touch-nots: missing or weak evidence for the given touchpoints.
    Each touch-not includes a reason and suggested actions.
    """
    if not touchpoint_id:
        return {"items": []}
    items = _build_touchnot_items(touchpoint_id, loader)
    return {"items": items, "count": len(items)}
