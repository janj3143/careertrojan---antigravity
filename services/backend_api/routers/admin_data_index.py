"""
Admin Data Index Router — CaReerTroJan
=======================================
REST API endpoints for managing and querying the unified data index system.

Endpoints:
  GET  /api/admin/v1/index/summary       - Index dashboard summary
  GET  /api/admin/v1/index/health         - Freshness check
  POST /api/admin/v1/index/rebuild        - Rebuild one or both indexes
  GET  /api/admin/v1/index/search         - Filename search across indexes
  GET  /api/admin/v1/index/unparsed       - List unparsed CV documents
  GET  /api/admin/v1/index/categories     - Category breakdown
  GET  /api/admin/v1/index/parser/stats   - Parser source stats
  GET  /api/admin/v1/index/ai/stats       - AI data stats

Author: CaReerTroJan System
Date: February 26, 2026
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Any, Dict, List, Optional
import logging

from services.backend_api.utils.auth_deps import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/v1/index",
    tags=["admin-data-index"],
    dependencies=[Depends(require_admin)],
)


def _get_registry():
    from services.shared.data_index import get_index_registry
    return get_index_registry()


# ── Build status tracking ────────────────────────────────────

_build_status: Dict[str, Any] = {"running": False, "last_result": None}


def _do_rebuild(index_type: str, compute_hashes: bool):
    """Background task that rebuilds index(es)."""
    global _build_status
    _build_status["running"] = True
    _build_status["index_type"] = index_type
    _build_status["files_scanned"] = 0

    def progress(count):
        _build_status["files_scanned"] = count

    try:
        reg = _get_registry()
        if index_type == "parser_source":
            result = reg.rebuild_parser_index(compute_hashes=compute_hashes, progress_cb=progress)
            _build_status["last_result"] = {"parser_source": result.meta.total_files}
        elif index_type == "ai_data":
            result = reg.rebuild_ai_index(compute_hashes=compute_hashes, progress_cb=progress)
            _build_status["last_result"] = {"ai_data": result.meta.total_files}
        else:
            results = reg.rebuild_all(compute_hashes=compute_hashes, progress_cb=progress)
            _build_status["last_result"] = {k: v.meta.total_files for k, v in results.items()}
    except Exception as exc:
        logger.error("Index rebuild failed: %s", exc)
        _build_status["last_result"] = {"error": str(exc)}
    finally:
        _build_status["running"] = False


# ══════════════════════════════════════════════════════════════
# Endpoints
# ══════════════════════════════════════════════════════════════


@router.get("/summary")
def get_index_summary():
    """
    Dashboard-ready summary of both indexes.

    Returns file counts, size, category breakdowns, and parser coverage stats.
    """
    reg = _get_registry()
    summary = reg.get_summary()
    summary["build_status"] = _build_status
    return summary


@router.get("/health")
def get_index_health(max_age_hours: int = Query(24, ge=1, le=720)):
    """
    Check if indexes are fresh (within max_age_hours).

    Returns per-index freshness boolean.
    """
    reg = _get_registry()
    freshness = reg.is_fresh(max_age_hours=max_age_hours)
    all_fresh = all(freshness.values())
    return {
        "healthy": all_fresh,
        "freshness": freshness,
        "max_age_hours": max_age_hours,
    }


@router.post("/rebuild")
def rebuild_indexes(
    background_tasks: BackgroundTasks,
    index_type: str = Query("both", regex="^(parser_source|ai_data|both)$"),
    compute_hashes: bool = Query(False),
):
    """
    Trigger an index rebuild (runs in background).

    - `index_type`: "parser_source", "ai_data", or "both"
    - `compute_hashes`: compute MD5 prefix for integrity checks (slower)
    """
    if _build_status.get("running"):
        raise HTTPException(status_code=409, detail="Rebuild already in progress")

    background_tasks.add_task(_do_rebuild, index_type, compute_hashes)

    return {
        "message": f"Index rebuild started for: {index_type}",
        "compute_hashes": compute_hashes,
        "monitor_endpoint": "/api/admin/v1/index/summary",
    }


@router.get("/search")
def search_index(
    q: str = Query(..., min_length=2, description="Search query (filename/path)"),
    index_type: str = Query("both", regex="^(parser_source|ai_data|both)$"),
    limit: int = Query(50, ge=1, le=500),
):
    """Search across indexes by filename or path substring."""
    reg = _get_registry()
    results = reg.search(q, index_type=index_type, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@router.get("/unparsed")
def get_unparsed_files(
    category: Optional[str] = Query(None, description="Filter by category (e.g. cv_document)"),
    limit: int = Query(100, ge=1, le=5000),
):
    """
    List files in automated_parser/ that haven't been parsed yet.

    Cross-references parser source files against parsed output directories.
    """
    reg = _get_registry()
    if reg.parser_index is None:
        raise HTTPException(status_code=404, detail="Parser index not built — run /rebuild first")

    unparsed = reg.parser_index.get_unparsed_files()
    if category:
        unparsed = [f for f in unparsed if f.category == category]

    from dataclasses import asdict
    return {
        "total_unparsed": len(unparsed),
        "showing": min(limit, len(unparsed)),
        "files": [asdict(f) for f in unparsed[:limit]],
    }


@router.get("/categories")
def get_categories(index_type: str = Query("both", regex="^(parser_source|ai_data|both)$")):
    """
    Breakdown of file categories across indexes.
    """
    reg = _get_registry()
    result: Dict[str, Any] = {}

    if index_type in ("both", "parser_source") and reg.parser_index:
        result["parser_source"] = {
            "categories": reg.parser_index.meta.categories,
            "total_files": reg.parser_index.meta.total_files,
        }
    if index_type in ("both", "ai_data") and reg.ai_index:
        result["ai_data"] = {
            "categories": reg.ai_index.meta.categories,
            "total_files": reg.ai_index.meta.total_files,
        }

    return result


@router.get("/parser/stats")
def get_parser_stats():
    """
    Detailed parser source statistics.

    Shows: files per client folder, extension distribution, parse coverage.
    """
    reg = _get_registry()
    if reg.parser_index is None:
        raise HTTPException(status_code=404, detail="Parser index not built")

    # Group by subcategory (client folder)
    by_folder: Dict[str, Dict[str, int]] = {}
    for entry in reg.parser_index.entries:
        folder = entry.subcategory or "(root)"
        if folder not in by_folder:
            by_folder[folder] = {"files": 0, "size_mb": 0, "parsed": 0, "unparsed": 0}
        by_folder[folder]["files"] += 1
        by_folder[folder]["size_mb"] += entry.size_bytes
        if entry.parse_status == "parsed":
            by_folder[folder]["parsed"] += 1
        elif entry.parse_status == "unparsed":
            by_folder[folder]["unparsed"] += 1

    # Convert bytes to MB
    for v in by_folder.values():
        v["size_mb"] = round(v["size_mb"] / (1024 * 1024), 1)

    # Sort by file count descending
    sorted_folders = dict(sorted(by_folder.items(), key=lambda x: -x[1]["files"]))

    return {
        "total_files": reg.parser_index.meta.total_files,
        "total_size_mb": round(reg.parser_index.meta.total_size_bytes / (1024 * 1024), 1),
        "generated_at": reg.parser_index.meta.generated_at,
        "extensions": reg.parser_index.meta.extensions,
        "categories": reg.parser_index.meta.categories,
        "by_folder": sorted_folders,
    }


@router.get("/ai/stats")
def get_ai_data_stats():
    """
    Detailed AI data statistics.

    Shows: files per category directory, JSON record counts, freshness.
    """
    reg = _get_registry()
    if reg.ai_index is None:
        raise HTTPException(status_code=404, detail="AI data index not built")

    # Group by subcategory (directory)
    by_dir: Dict[str, Dict[str, Any]] = {}
    for entry in reg.ai_index.entries:
        d = entry.subcategory or "(root)"
        if d not in by_dir:
            by_dir[d] = {"files": 0, "size_mb": 0, "json_records": 0, "categories": set()}
        by_dir[d]["files"] += 1
        by_dir[d]["size_mb"] += entry.size_bytes
        if entry.record_count is not None:
            by_dir[d]["json_records"] += entry.record_count
        by_dir[d]["categories"].add(entry.category)

    # Serialize sets → lists, convert size
    for v in by_dir.values():
        v["size_mb"] = round(v["size_mb"] / (1024 * 1024), 1)
        v["categories"] = sorted(v["categories"])

    sorted_dirs = dict(sorted(by_dir.items(), key=lambda x: -x[1]["files"]))

    return {
        "total_files": reg.ai_index.meta.total_files,
        "total_size_mb": round(reg.ai_index.meta.total_size_bytes / (1024 * 1024), 1),
        "generated_at": reg.ai_index.meta.generated_at,
        "extensions": reg.ai_index.meta.extensions,
        "categories": reg.ai_index.meta.categories,
        "by_directory": sorted_dirs,
    }
