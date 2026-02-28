"""
Data Index Router
=================

API endpoints for the AI data indexing system.
Provides access to content indexes, parser status, and run history.
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from services.backend_api.services.ai_data_index_service import (
    get_ai_data_index_service,
    AIDataIndexSummary,
    ParserIndexSummary,
    FileIngestionRecord,
)

router = APIRouter(prefix="/api/data-index/v1", tags=["data-index"])


@router.get("/status")
def get_index_status() -> Dict[str, Any]:
    """
    Get current index status and health.
    Returns summary of indexed content without triggering a full reindex.
    """
    service = get_ai_data_index_service()
    state = service.get_state()

    ai_summary = state.ai_data_summary
    parser_summary = state.parser_summary

    return {
        "status": "ok",
        "last_full_index": state.last_full_index,
        "ai_data": {
            "indexed": ai_summary is not None,
            "total_files": ai_summary.total_files if ai_summary else 0,
            "total_size_bytes": ai_summary.total_size_bytes if ai_summary else 0,
            "unique_skills": ai_summary.unique_skills if ai_summary else 0,
            "unique_industries": ai_summary.unique_industries if ai_summary else 0,
            "unique_locations": ai_summary.unique_locations if ai_summary else 0,
            "indexed_at": ai_summary.indexed_at if ai_summary else None,
        },
        "parser": {
            "indexed": parser_summary is not None,
            "total_sources": parser_summary.total_sources if parser_summary else 0,
            "processed_count": parser_summary.processed_count if parser_summary else 0,
            "pending_count": parser_summary.pending_count if parser_summary else 0,
            "error_count": parser_summary.error_count if parser_summary else 0,
            "blocked_count": parser_summary.blocked_count if parser_summary else 0,
            "trap_flags": parser_summary.trap_flags if parser_summary else [],
            "indexed_at": parser_summary.indexed_at if parser_summary else None,
        },
        "run_history_count": len(state.parser_run_history),
    }


@router.post("/index/ai-data")
def trigger_ai_data_index(
    max_files_per_category: Optional[int] = Query(None, description="Max files per category (for faster indexing)")
) -> Dict[str, Any]:
    """
    Trigger a full index of ai_data_final content.
    Aggregates skills, industries, locations across all profiles.
    """
    service = get_ai_data_index_service()
    summary = service.index_ai_data(max_files_per_category=max_files_per_category)

    return {
        "status": "ok",
        "message": f"Indexed {summary.total_files} files across {len(summary.categories)} categories",
        "summary": asdict(summary),
    }


@router.post("/index/parser")
def trigger_parser_index() -> Dict[str, Any]:
    """
    Trigger a full index of automated_parser source files.
    Identifies pending, processed, errored, and blocked files.
    """
    service = get_ai_data_index_service()
    summary = service.index_parser_sources()

    return {
        "status": "ok",
        "message": f"Indexed {summary.total_sources} parser source files",
        "summary": asdict(summary),
    }


@router.post("/index/full")
def trigger_full_index(
    max_files_per_category: Optional[int] = Query(None, description="Max files per category")
) -> Dict[str, Any]:
    """
    Trigger a full index of both ai_data_final and automated_parser.
    """
    service = get_ai_data_index_service()
    state = service.full_index(max_files_per_category=max_files_per_category)

    return {
        "status": "ok",
        "message": "Full index completed",
        "last_full_index": state.last_full_index,
        "ai_data_files": state.ai_data_summary.total_files if state.ai_data_summary else 0,
        "parser_sources": state.parser_summary.total_sources if state.parser_summary else 0,
    }


@router.get("/ai-data/summary")
def get_ai_data_summary() -> Dict[str, Any]:
    """
    Get detailed AI data index summary.
    Returns category breakdown, skill/industry/location aggregations.
    """
    service = get_ai_data_index_service()
    summary = service.get_ai_data_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "message": "AI data has not been indexed yet. Call POST /index/ai-data first.",
        }

    return {
        "status": "ok",
        "summary": asdict(summary),
    }


@router.get("/ai-data/categories")
def get_ai_data_categories() -> Dict[str, Any]:
    """
    Get AI data category breakdown.
    """
    service = get_ai_data_index_service()
    summary = service.get_ai_data_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "categories": [],
        }

    return {
        "status": "ok",
        "total_files": summary.total_files,
        "total_size_bytes": summary.total_size_bytes,
        "categories": [asdict(c) for c in summary.categories],
    }


@router.get("/ai-data/skills")
def get_top_skills(
    limit: int = Query(100, description="Number of top skills to return", ge=1, le=500)
) -> Dict[str, Any]:
    """
    Get top indexed skills by frequency.
    """
    service = get_ai_data_index_service()
    summary = service.get_ai_data_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "skills": {},
        }

    # Re-slice if limit is different
    skills = dict(list(summary.top_skills.items())[:limit])

    return {
        "status": "ok",
        "unique_skills": summary.unique_skills,
        "top_skills": skills,
    }


@router.get("/ai-data/skills/search")
def search_skills(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Search indexed skills by substring match.
    """
    service = get_ai_data_index_service()
    results = service.search_skills(q, limit=limit)

    return {
        "status": "ok",
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/ai-data/industries")
def get_top_industries(
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Get top indexed industries by frequency.
    """
    service = get_ai_data_index_service()
    summary = service.get_ai_data_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "industries": {},
        }

    industries = dict(list(summary.top_industries.items())[:limit])

    return {
        "status": "ok",
        "unique_industries": summary.unique_industries,
        "top_industries": industries,
    }


@router.get("/ai-data/industries/search")
def search_industries(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Search indexed industries by substring match.
    """
    service = get_ai_data_index_service()
    results = service.search_industries(q, limit=limit)

    return {
        "status": "ok",
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/ai-data/locations")
def get_top_locations(
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Get top indexed locations by frequency.
    """
    service = get_ai_data_index_service()
    summary = service.get_ai_data_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "locations": {},
        }

    locations = dict(list(summary.top_locations.items())[:limit])

    return {
        "status": "ok",
        "unique_locations": summary.unique_locations,
        "top_locations": locations,
    }


@router.get("/ai-data/locations/search")
def search_locations(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=200)
) -> Dict[str, Any]:
    """
    Search indexed locations by substring match.
    """
    service = get_ai_data_index_service()
    results = service.search_locations(q, limit=limit)

    return {
        "status": "ok",
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/parser/summary")
def get_parser_summary() -> Dict[str, Any]:
    """
    Get parser source index summary.
    Shows pending, processed, errored, blocked file counts.
    """
    service = get_ai_data_index_service()
    summary = service.get_parser_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "message": "Parser sources have not been indexed yet. Call POST /index/parser first.",
        }

    return {
        "status": "ok",
        "summary": asdict(summary),
    }


@router.get("/parser/status")
def get_parser_status() -> Dict[str, Any]:
    """
    Get parser health status with trap flags.
    Use this for monitoring dashboards.
    """
    service = get_ai_data_index_service()
    summary = service.get_parser_summary()

    if not summary:
        return {
            "status": "unknown",
            "trap_flags": [],
            "message": "Parser has not been indexed.",
        }

    # Determine overall health
    if summary.trap_flags:
        health = "warning"
    elif summary.processed_count > 0 and summary.pending_count == 0:
        health = "healthy"
    else:
        health = "ok"

    return {
        "status": health,
        "parser_root": summary.parser_root,
        "output_root": summary.output_root,
        "processed_count": summary.processed_count,
        "pending_count": summary.pending_count,
        "error_count": summary.error_count,
        "blocked_count": summary.blocked_count,
        "trap_flags": summary.trap_flags,
        "indexed_at": summary.indexed_at,
    }


@router.get("/parser/file-types")
def get_parser_file_types() -> Dict[str, Any]:
    """
    Get file type distribution in parser sources.
    """
    service = get_ai_data_index_service()
    summary = service.get_parser_summary()

    if not summary:
        return {
            "status": "not_indexed",
            "file_types": {},
        }

    return {
        "status": "ok",
        "total_sources": summary.total_sources,
        "file_type_distribution": summary.file_type_distribution,
    }


@router.get("/parser/runs")
def get_parser_runs(
    limit: int = Query(50, ge=1, le=500)
) -> Dict[str, Any]:
    """
    Get parser run history.
    """
    service = get_ai_data_index_service()
    runs = service.get_parser_run_history(limit=limit)

    return {
        "status": "ok",
        "count": len(runs),
        "runs": [asdict(r) for r in runs],
    }


@router.post("/parser/runs")
def record_parser_run(
    run_id: str,
    started_at: str,
    completed_at: Optional[str] = None,
    total_files: int = 0,
    processed: int = 0,
    skipped: int = 0,
    errors: int = 0,
    duration_seconds: Optional[float] = None,
    file_types: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Record a parser execution run.
    Called by the automated parser at the end of each run.
    """
    service = get_ai_data_index_service()
    record = service.record_parser_run(
        run_id=run_id,
        started_at=started_at,
        completed_at=completed_at,
        total_files=total_files,
        processed=processed,
        skipped=skipped,
        errors=errors,
        duration_seconds=duration_seconds,
        file_types=file_types or {},
    )

    return {
        "status": "ok",
        "message": "Parser run recorded",
        "run": asdict(record),
    }


@router.get("/dependencies")
def get_optional_dependencies() -> Dict[str, Any]:
    """
    Get status of optional parsing dependencies.
    Shows which file types can be parsed.
    """
    service = get_ai_data_index_service()
    deps = service._detect_optional_dependencies()

    # Map to file types
    file_type_support = {
        ".pdf": deps.get("pdfplumber") or deps.get("pypdf2"),
        ".docx": deps.get("python_docx"),
        ".doc": deps.get("python_docx"),  # fallback method available
        ".xlsx": deps.get("openpyxl"),
        ".xls": deps.get("xlrd"),
        ".msg": deps.get("extract_msg"),
        ".csv": True,  # stdlib
        ".json": True,  # stdlib
        ".txt": True,  # stdlib
        ".xml": True,  # stdlib
        ".yaml": True,  # PyYAML usually installed
        ".html": True,  # stdlib
    }

    return {
        "status": "ok",
        "dependencies": deps,
        "file_type_support": file_type_support,
    }


# ---------------------------------------------------------------------------
# Timestamp-based Indexing Endpoints
# ---------------------------------------------------------------------------

@router.get("/files/since")
def get_files_since_timestamp(
    since: str = Query(..., description="ISO timestamp (e.g., 2026-02-27T00:00:00Z)"),
    source_type: Optional[str] = Query(None, description="Filter by 'ai_data_final' or 'automated_parser'"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    Get files ingested since a given timestamp.
    Useful for monitoring new data additions.
    """
    service = get_ai_data_index_service()
    files = service.get_files_since(since, source_type=source_type, category=category, limit=limit)

    return {
        "status": "ok",
        "query": {
            "since": since,
            "source_type": source_type,
            "category": category,
            "limit": limit,
        },
        "count": len(files),
        "files": files,
    }


@router.get("/files/new-data-summary")
def get_new_data_summary() -> Dict[str, Any]:
    """
    Quick summary of new data since last full index.
    Useful for dashboards and monitoring alerts.
    """
    service = get_ai_data_index_service()
    return service.get_new_data_summary()


@router.get("/files/manifest-stats")
def get_file_manifest_stats() -> Dict[str, Any]:
    """
    Get statistics about the tracked file manifest.
    Shows total files tracked, breakdown by category and source.
    """
    service = get_ai_data_index_service()
    return service.get_file_manifest_stats()


@router.post("/index/incremental")
def trigger_incremental_index() -> Dict[str, Any]:
    """
    Perform incremental indexing - only process new/changed files.
    Faster than full index for continuous data updates.
    """
    service = get_ai_data_index_service()
    result = service.incremental_index()

    return {
        "status": "ok",
        "message": f"Incremental index complete: {result['new_files_count']} new, {result['changed_files_count']} changed",
        "result": result,
    }


@router.get("/files/by-category/{category}")
def get_files_by_category(
    category: str,
    limit: int = Query(100, ge=1, le=1000),
    sort_by: str = Query("ingested_at", description="Sort by 'ingested_at' or 'modified_at'"),
    order: str = Query("desc", description="Sort order: 'asc' or 'desc'")
) -> Dict[str, Any]:
    """
    Get all tracked files in a specific category.
    """
    service = get_ai_data_index_service()
    files = []
    for rec in service._state.file_manifest.values():
        if rec.category == category:
            files.append(asdict(rec))
            if len(files) >= limit:
                break

    # Sort
    reverse = order == "desc"
    files.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

    return {
        "status": "ok",
        "category": category,
        "count": len(files),
        "files": files,
    }


@router.get("/health")
def get_index_health() -> Dict[str, Any]:
    """
    Health check for the indexing system.
    Returns overall health status and key metrics.
    """
    service = get_ai_data_index_service()
    state = service.get_state()

    # Check health indicators
    issues = []
    warnings = []

    if state.ai_data_summary is None:
        issues.append("AI data not indexed")
    if state.parser_summary is None:
        issues.append("Parser sources not indexed")

    if state.parser_summary:
        if state.parser_summary.error_count > 0:
            warnings.append(f"{state.parser_summary.error_count} parser errors")
        if state.parser_summary.blocked_count > 0:
            warnings.append(f"{state.parser_summary.blocked_count} blocked files (missing dependencies)")
        if state.parser_summary.pending_count > 10:
            warnings.append(f"{state.parser_summary.pending_count} files pending processing")

    status = "healthy" if not issues else "degraded" if not warnings else "unhealthy"

    return {
        "status": status,
        "last_full_index": state.last_full_index,
        "ai_data_indexed": state.ai_data_summary is not None,
        "parser_indexed": state.parser_summary is not None,
        "total_tracked_files": len(state.file_manifest),
        "issues": issues,
        "warnings": warnings,
    }
