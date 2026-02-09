from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

try:
    # Import the central taxonomy service
    import services.backend_api.services.industry_taxonomy_service as tax
    TAXONOMY_AVAILABLE = True
except ImportError:
    tax = None  # type: ignore
    TAXONOMY_AVAILABLE = False


router = APIRouter(
    prefix="/api/taxonomy/v1",
    tags=["taxonomy"],
)


def _require_taxonomy():
    if not TAXONOMY_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="industry_taxonomy_service not available on PYTHONPATH.",
        )


@router.get("/industries")
async def list_industries() -> Dict[str, Any]:
    """
    List high-level industries (used by Profile, UMarketU, Coaching, Mentorship).

    These are backed by `HIGH_LEVEL_INDUSTRIES` in industry_taxonomy_service.
    """
    _require_taxonomy()
    industries = tax.list_high_level_industries()
    return {"data": industries, "meta": {"count": len(industries)}}


@router.get("/industries/{high_level}/subindustries")
async def list_subindustries(
    high_level: str,
) -> Dict[str, Any]:
    """
    List sub-industries / verticals for a given high-level bucket.
    """
    _require_taxonomy()
    subs = tax.list_subindustries_for(high_level)
    return {"data": subs, "meta": {"count": len(subs), "parent": high_level}}


@router.get("/job-titles/search")
async def search_job_titles(
    q: str = Query(..., min_length=1, description="Free-text job title search"),
    max_results: int = Query(25, ge=1, le=100),
) -> Dict[str, Any]:
    """
    Search across normalized job titles from the enhanced job DB.

    Uses `search_job_titles` from industry_taxonomy_service.
    """
    _require_taxonomy()
    titles = tax.search_job_titles(q, max_results=max_results)
    return {"data": titles, "meta": {"count": len(titles), "query": q}}


@router.get("/job-titles/metadata")
async def job_title_metadata(
    title: str = Query(..., min_length=1),
) -> Dict[str, Any]:
    """
    Fetch metadata for a specific job title (industries, skills, NAICS suggestions, etc.).
    """
    _require_taxonomy()
    meta = tax.get_job_title_metadata(title)
    return {"data": meta, "meta": {"title": title}}


@router.get("/job-titles/infer-industries")
async def infer_industries(
    titles: List[str] = Query(..., description="One or more job titles to infer industries from"),
) -> Dict[str, Any]:
    """
    Infer industries from a list of job titles.

    Uses `infer_industries_from_titles` – this is particularly useful for:
      - UMarketU
      - Coaching Hub
      - Mentorship taxonomies
    """
    _require_taxonomy()
    industries = tax.infer_industries_from_titles(titles)
    return {"data": industries, "meta": {"count": len(industries)}}


@router.get("/naics/search")
async def search_naics(
    phrase: str = Query(..., min_length=1),
    max_results: int = Query(20, ge=1, le=200),
) -> Dict[str, Any]:
    """
    NAICS search endpoint – uses `search_naics_by_phrase`.
    """
    _require_taxonomy()
    results = tax.search_naics_by_phrase(phrase, max_results=max_results)
    return {"data": results, "meta": {"count": len(results), "query": phrase}}


@router.get("/naics/title")
async def naics_title(
    code: str = Query(..., min_length=2),
) -> Dict[str, Any]:
    """
    Get NAICS title for a specific code via `get_naics_title`.
    """
    _require_taxonomy()
    title = tax.get_naics_title(code)
    return {"data": {"code": code, "title": title}, "meta": {}}


@router.get("/job-titles/naics-mapping")
async def job_title_to_naics(
    title: str = Query(..., min_length=1),
    max_results: int = Query(5, ge=1, le=50),
) -> Dict[str, Any]:
    """
    Bridge endpoint: map a job title to one or more NAICS suggestions.

    Uses `map_job_title_to_naics` from industry_taxonomy_service.
    """
    _require_taxonomy()
    mapping = tax.map_job_title_to_naics(title, max_results=max_results)
    return {"data": mapping, "meta": {"title": title, "count": len(mapping)}}
