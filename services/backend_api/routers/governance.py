"""
Route Governance — Admin API Endpoints
=======================================
Exposes the governance engine as admin-protected API endpoints:

  GET  /api/admin/v1/governance/summary   — quick health probe
  GET  /api/admin/v1/governance/audit     — full audit (drift + policy)
  POST /api/admin/v1/governance/snapshot  — save current routes as baseline
  GET  /api/admin/v1/governance/drift     — drift-only against baseline
  GET  /api/admin/v1/governance/manifest  — raw route manifest (JSON)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query

from services.backend_api.routers.auth import get_current_active_admin as require_admin
from services.backend_api.governance.route_governance import (
    extract_manifest,
    manifest_to_json,
    run_audit,
    quick_summary,
    save_snapshot,
    load_snapshot,
    detect_drift,
    check_policies,
)

router = APIRouter(
    prefix="/api/admin/v1/governance",
    tags=["governance"],
    dependencies=[Depends(require_admin)],
)


@router.get("/summary")
def governance_summary(request: Request):
    """Lightweight governance probe — returns route count, error count, checksum."""
    return quick_summary(request.app)


@router.get("/audit")
def governance_audit(
    request: Request,
    strict: bool = Query(False, description="Include info-level rules (response_model, etc.)"),
    include_manifest: bool = Query(False, description="Embed full route manifest in response"),
):
    """Full governance report: policy violations + drift detection."""
    report = run_audit(request.app, strict=strict, include_manifest=include_manifest)
    return report.to_dict()


@router.post("/snapshot")
def governance_snapshot(request: Request):
    """Save the current route manifest as the governance baseline.

    Future drift checks will compare against this snapshot.
    """
    path = save_snapshot(request.app)
    snapshot = load_snapshot()
    return {
        "status": "saved",
        "path": str(path),
        "total_routes": snapshot["total_routes"] if snapshot else 0,
        "checksum": snapshot.get("checksum", ""),
        "snapshot_time": snapshot.get("snapshot_time", ""),
    }


@router.get("/drift")
def governance_drift(request: Request):
    """Compare live routes against the saved baseline snapshot."""
    live = extract_manifest(request.app)
    baseline = load_snapshot()
    if baseline is None:
        return {
            "status": "no_baseline",
            "message": "No baseline snapshot found. POST /api/admin/v1/governance/snapshot first.",
            "drift": [],
        }
    drifts = detect_drift(live, baseline)
    return {
        "baseline_time": baseline.get("snapshot_time"),
        "baseline_routes": baseline.get("total_routes", 0),
        "live_routes": len(live),
        "drift_count": len(drifts),
        "drift": [
            {"kind": d.kind, "route_key": d.route_key, "detail": d.detail}
            for d in drifts
        ],
    }


@router.get("/manifest")
def governance_manifest(request: Request):
    """Raw route manifest — every registered endpoint with metadata."""
    records = extract_manifest(request.app)
    return {
        "total_routes": len(records),
        "routes": manifest_to_json(records),
    }


@router.get("/violations")
def governance_violations(
    request: Request,
    severity: str = Query("all", description="Filter: error, warning, info, all"),
    strict: bool = Query(False, description="Include info-level rules"),
):
    """Policy violations only (no drift), optionally filtered by severity."""
    records = extract_manifest(request.app)
    violations = check_policies(records, strict=strict)
    if severity != "all":
        violations = [v for v in violations if v.severity == severity]
    return {
        "total_violations": len(violations),
        "filter": severity,
        "violations": [
            {"rule": v.rule, "severity": v.severity,
             "route_key": v.route_key, "message": v.message}
            for v in violations
        ],
    }
