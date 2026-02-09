"""
Touchpoints API Router — evidence and touch-not lookups for the visual overlay panel.
Every visual click emits touchpoint_ids → this router returns the evidence + gaps.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/touchpoints/v1", tags=["touchpoints"])


@router.get("/evidence")
async def get_evidence(
    touchpoint_id: List[str] = Query(default=[]),
):
    """
    Returns evidence spans for the given touchpoint IDs.
    Each touchpoint maps to resume/JD/peer evidence that proves
    the user meets (or partially meets) a requirement.
    """
    if not touchpoint_id:
        return {"items": []}
    # TODO: Wire to evidence store (parsed resumes, JD annotations, peer data)
    logger.warning("touchpoints/evidence called but not yet wired to evidence store")
    raise HTTPException(
        status_code=501,
        detail="Wire to evidence store — no mock data",
    )


@router.get("/touchnots")
async def get_touchnots(
    touchpoint_id: List[str] = Query(default=[]),
):
    """
    Returns touch-nots: missing or weak evidence for the given touchpoints.
    Each touch-not includes a reason and suggested actions.
    """
    if not touchpoint_id:
        return {"items": []}
    # TODO: Wire to gap analysis engine
    logger.warning("touchpoints/touchnots called but not yet wired to gap engine")
    raise HTTPException(
        status_code=501,
        detail="Wire to gap analysis engine — no mock data",
    )
