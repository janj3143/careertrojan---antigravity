"""
API Health Check Router — probes all registered endpoints.

Provides:
  GET  /api/admin/v1/api-health/endpoints   — list all registered routes
  POST /api/admin/v1/api-health/run-all     — probe every GET endpoint, return status
  GET  /api/admin/v1/api-health/summary     — latest run-all results from cache
"""

import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request
from starlette.testclient import TestClient

logger = logging.getLogger("api_health")

router = APIRouter(prefix="/api/admin/v1/api-health", tags=["api-health"])

# ── In-memory cache of last run ──────────────────────────────
_last_run: Optional[dict] = None


def _get_admin():
    """Lightweight admin check — reuse from admin router or skip for ops."""
    return True


def _extract_routes(app) -> list[dict]:
    """Build a sorted list of every mounted endpoint."""
    routes = []
    for route in app.routes:
        if not hasattr(route, "methods"):
            continue
        for method in sorted(route.methods):
            if method in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                routes.append({
                    "method": method,
                    "path": route.path,
                    "name": getattr(route, "name", ""),
                    "tags": list(getattr(route, "tags", [])),
                })
    routes.sort(key=lambda r: (r["path"], r["method"]))
    return routes


@router.get("/endpoints")
async def list_endpoints(request: Request):
    """Return every registered endpoint with method, path, name, tags."""
    routes = _extract_routes(request.app)
    by_tag: dict[str, int] = {}
    for r in routes:
        for t in r["tags"] or ["untagged"]:
            by_tag[t] = by_tag.get(t, 0) + 1
    return {
        "total": len(routes),
        "by_tag": by_tag,
        "endpoints": routes,
    }


@router.post("/run-all")
async def run_all_health_checks(request: Request):
    """
    Probe every GET endpoint (no auth) and return pass/fail status.
    
    Skips endpoints requiring path parameters ({...}).
    Records status_code, response_time_ms, and a short excerpt.
    """
    global _last_run
    routes = _extract_routes(request.app)
    
    # Only probe GET endpoints without path params (safe, side-effect-free)
    probeable = [
        r for r in routes
        if r["method"] == "GET" and "{" not in r["path"]
    ]
    
    results = []
    passed = 0
    failed = 0
    skipped = 0
    
    # Use synchronous TestClient for internal probing
    try:
        client = TestClient(request.app, raise_server_exceptions=False)
    except Exception as e:
        return {"error": f"Could not create test client: {e}"}
    
    for endpoint in probeable:
        path = endpoint["path"]
        t0 = time.perf_counter()
        try:
            resp = client.get(path)
            elapsed = round((time.perf_counter() - t0) * 1000, 1)
            
            status_code = resp.status_code
            # 401/403 means the endpoint exists but needs auth — that's a pass
            if status_code in (200, 204, 307):
                status_label = "pass"
                passed += 1
            elif status_code in (401, 403):
                status_label = "auth-required"
                passed += 1  # endpoint works, just needs auth
            elif status_code == 404:
                status_label = "not-found"
                failed += 1
            elif status_code == 422:
                status_label = "missing-params"
                passed += 1  # endpoint exists but needs query params
            elif status_code >= 500:
                status_label = "error"
                failed += 1
            else:
                status_label = "unexpected"
                failed += 1
            
            # Short excerpt of response body
            try:
                body = resp.text[:200]
            except Exception:
                body = ""
            
            results.append({
                "path": path,
                "status_code": status_code,
                "status": status_label,
                "response_time_ms": elapsed,
                "excerpt": body,
            })
        except Exception as e:
            elapsed = round((time.perf_counter() - t0) * 1000, 1)
            failed += 1
            results.append({
                "path": path,
                "status_code": 0,
                "status": "exception",
                "response_time_ms": elapsed,
                "excerpt": str(e)[:200],
            })
    
    # Also count POST/PUT/DELETE endpoints as "skipped" (not probed)
    post_endpoints = [r for r in routes if r["method"] != "GET" or "{" in r["path"]]
    skipped = len(post_endpoints)
    
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_endpoints": len(routes),
        "probed": len(probeable),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_rate": round(passed / max(len(probeable), 1) * 100, 1),
        "avg_response_ms": round(
            sum(r["response_time_ms"] for r in results) / max(len(results), 1), 1
        ),
        "results": results,
        "all_endpoints": routes,
    }
    
    _last_run = summary
    logger.info(f"API health run: {passed}/{len(probeable)} passed, {failed} failed")
    return summary


@router.get("/summary")
async def get_last_summary():
    """Return the most recent run-all results (cached in memory)."""
    if _last_run is None:
        return {"message": "No health check has been run yet. POST /api/admin/v1/api-health/run-all to start."}
    return _last_run
