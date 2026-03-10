"""
Tests for the Route Governance Engine
======================================
Covers: manifest extraction, policy checks, drift detection, admin API.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("TESTING", "1")

from fastapi import FastAPI, APIRouter, Depends
from fastapi.testclient import TestClient

from services.backend_api.governance.route_governance import (
    RouteRecord,
    PolicyViolation,
    DriftEntry,
    extract_manifest,
    manifest_to_json,
    check_policies,
    detect_drift,
    save_snapshot,
    load_snapshot,
    run_audit,
    quick_summary,
    _has_auth_dependency,
    _manifest_checksum,
)


# ── Fixtures ──────────────────────────────────────────────────────────────

def _fake_auth():
    """Simulates an auth dependency."""
    return {"user_id": "test"}


def _build_test_app() -> FastAPI:
    """Build a minimal FastAPI app with known routes for testing."""
    app = FastAPI()

    # Public health probe
    @app.get("/health", tags=["probes"])
    def health():
        return {"status": "ok"}

    # Auth-protected user endpoint
    user_router = APIRouter(prefix="/api/user/v1", tags=["user"])

    @user_router.get("/me")
    def me(user=Depends(_fake_auth)):
        return {"user": "test"}

    @user_router.get("/profile")
    def profile(user=Depends(_fake_auth)):
        return {"profile": "test"}

    app.include_router(user_router)

    # Unprotected admin endpoint (violation)
    admin_router = APIRouter(prefix="/api/admin/v1", tags=["admin"])

    @admin_router.get("/users")
    def list_users():  # No auth Depends — should violate AUTH_REQUIRED
        return []

    @admin_router.delete("/users/{user_id}")
    def delete_user(user_id: str):  # No auth — should violate MUTATING_NO_AUTH
        return {"deleted": user_id}

    app.include_router(admin_router)

    # Payment webhook (should be public, signature-verified)
    payment_router = APIRouter(prefix="/api/payment/v1", tags=["payment"])

    @payment_router.post("/webhooks")
    def webhook():
        return {"ok": True}

    @payment_router.post("/process")
    def process(user=Depends(_fake_auth)):
        return {"processed": True}

    app.include_router(payment_router)

    return app


@pytest.fixture
def test_app():
    return _build_test_app()


@pytest.fixture
def manifest(test_app):
    return extract_manifest(test_app)


@pytest.fixture
def tmp_snapshot_dir(tmp_path):
    return tmp_path / "governance"


# ── 1) Manifest Extraction ───────────────────────────────────────────────

class TestManifestExtraction:

    def test_extracts_all_routes(self, test_app, manifest):
        """Should find all user-defined routes (excluding HEAD/OPTIONS)."""
        keys = {r.key for r in manifest}
        assert "GET /health" in keys
        assert "GET /api/user/v1/me" in keys
        assert "GET /api/user/v1/profile" in keys
        assert "GET /api/admin/v1/users" in keys
        assert "DELETE /api/admin/v1/users/{user_id}" in keys
        assert "POST /api/payment/v1/webhooks" in keys
        assert "POST /api/payment/v1/process" in keys

    def test_records_sorted_by_path(self, manifest):
        paths = [r.path for r in manifest]
        assert paths == sorted(paths)

    def test_auth_detected_on_protected_routes(self, manifest):
        by_key = {r.key: r for r in manifest}
        assert by_key["GET /api/user/v1/me"].has_auth is True
        assert by_key["POST /api/payment/v1/process"].has_auth is True

    def test_auth_absent_on_unprotected_routes(self, manifest):
        by_key = {r.key: r for r in manifest}
        assert by_key["GET /health"].has_auth is False
        assert by_key["GET /api/admin/v1/users"].has_auth is False

    def test_path_params_extracted(self, manifest):
        by_key = {r.key: r for r in manifest}
        assert by_key["DELETE /api/admin/v1/users/{user_id}"].path_params == ["user_id"]

    def test_tags_captured(self, manifest):
        by_key = {r.key: r for r in manifest}
        assert "user" in by_key["GET /api/user/v1/me"].tags
        assert "probes" in by_key["GET /health"].tags

    def test_manifest_to_json(self, manifest):
        data = manifest_to_json(manifest)
        assert isinstance(data, list)
        assert all(isinstance(d, dict) for d in data)
        assert all("method" in d and "path" in d for d in data)

    def test_checksum_stable(self, manifest):
        c1 = _manifest_checksum(manifest)
        c2 = _manifest_checksum(manifest)
        assert c1 == c2
        assert len(c1) == 16


# ── 2) Policy Checks ────────────────────────────────────────────────────

class TestPolicyChecks:

    def test_auth_required_violation(self, manifest):
        violations = check_policies(manifest)
        auth_violations = [v for v in violations if v.rule == "AUTH_REQUIRED"]
        violating_keys = {v.route_key for v in auth_violations}
        assert "GET /api/admin/v1/users" in violating_keys

    def test_mutating_no_auth_violation(self, manifest):
        violations = check_policies(manifest)
        mut_violations = [v for v in violations
                         if v.rule == "MUTATING_NO_AUTH"]
        violating_keys = {v.route_key for v in mut_violations}
        assert "DELETE /api/admin/v1/users/{user_id}" in violating_keys

    def test_webhook_not_flagged_for_jwt(self, manifest):
        """Webhook endpoint without JWT should NOT be flagged as WEBHOOK_HAS_JWT."""
        violations = check_policies(manifest)
        webhook_jwt = [v for v in violations if v.rule == "WEBHOOK_HAS_JWT"]
        assert len(webhook_jwt) == 0

    def test_public_webhook_not_flagged_for_auth(self, manifest):
        """POST /api/payment/v1/webhooks is in SIGNATURE_VERIFIED_PATHS — should be exempt."""
        violations = check_policies(manifest)
        auth_viol = [v for v in violations
                     if v.rule == "AUTH_REQUIRED"
                     and "webhooks" in v.route_key]
        assert len(auth_viol) == 0

    def test_health_probe_exempt(self, manifest):
        violations = check_policies(manifest)
        health_violations = [v for v in violations
                            if "/health" in v.route_key and v.route_key.endswith("/health")]
        assert len(health_violations) == 0

    def test_strict_mode_adds_response_model_warnings(self, manifest):
        normal = check_policies(manifest, strict=False)
        strict = check_policies(manifest, strict=True)
        assert len(strict) > len(normal)
        model_violations = [v for v in strict if v.rule == "NO_RESPONSE_MODEL"]
        assert len(model_violations) > 0

    def test_severity_ordering(self, manifest):
        violations = check_policies(manifest, strict=True)
        # Errors should come before warnings, warnings before info
        seen_warning = False
        seen_info = False
        for v in violations:
            if v.severity == "error":
                assert not seen_warning and not seen_info
            elif v.severity == "warning":
                seen_warning = True
                assert not seen_info
            elif v.severity == "info":
                seen_info = True


# ── 3) Drift Detection ──────────────────────────────────────────────────

class TestDriftDetection:

    def test_no_baseline_returns_info(self, manifest):
        drifts = detect_drift(manifest, baseline=None)
        # When load_snapshot returns None, we pass None explicitly
        with patch("services.backend_api.governance.route_governance.load_snapshot", return_value=None):
            drifts = detect_drift(manifest)
        assert len(drifts) == 1
        assert drifts[0].kind == "info"
        assert "No baseline" in drifts[0].detail

    def test_no_drift_when_identical(self, manifest):
        baseline = {
            "routes": manifest_to_json(manifest),
            "total_routes": len(manifest),
        }
        drifts = detect_drift(manifest, baseline)
        assert len(drifts) == 0

    def test_detects_added_route(self, manifest):
        # Baseline is missing one route
        baseline_routes = manifest_to_json(manifest)[:-1]  # Drop last
        baseline = {"routes": baseline_routes, "total_routes": len(baseline_routes)}
        drifts = detect_drift(manifest, baseline)
        added = [d for d in drifts if d.kind == "added"]
        assert len(added) == 1

    def test_detects_removed_route(self, manifest):
        # Baseline has an extra route
        extra = manifest_to_json(manifest) + [{
            "method": "GET", "path": "/api/old/v1/gone",
            "name": "gone", "tags": [], "has_auth": False,
            "has_response_model": False, "deprecated": False,
            "path_params": [], "summary": None,
        }]
        baseline = {"routes": extra, "total_routes": len(extra)}
        drifts = detect_drift(manifest, baseline)
        removed = [d for d in drifts if d.kind == "removed"]
        assert len(removed) == 1
        assert "gone" in removed[0].route_key

    def test_detects_metadata_change(self, manifest):
        # Flip has_auth on one route
        baseline_data = manifest_to_json(manifest)
        for r in baseline_data:
            if r["path"] == "/api/user/v1/me":
                r["has_auth"] = False  # Was True → now baseline says False
                break
        baseline = {"routes": baseline_data, "total_routes": len(baseline_data)}
        drifts = detect_drift(manifest, baseline)
        changed = [d for d in drifts if d.kind == "changed"]
        assert len(changed) >= 1
        assert any("has_auth" in d.detail for d in changed)


# ── 4) Snapshot Persistence ──────────────────────────────────────────────

class TestSnapshotPersistence:

    def test_save_and_load(self, test_app, tmp_snapshot_dir):
        path = save_snapshot(test_app, tmp_snapshot_dir)
        assert path.exists()

        loaded = load_snapshot(tmp_snapshot_dir)
        assert loaded is not None
        assert loaded["total_routes"] > 0
        assert "checksum" in loaded
        assert "snapshot_time" in loaded
        assert len(loaded["routes"]) == loaded["total_routes"]

    def test_load_missing_returns_none(self, tmp_snapshot_dir):
        assert load_snapshot(tmp_snapshot_dir) is None

    def test_snapshot_roundtrip_drift_clean(self, test_app, tmp_snapshot_dir):
        save_snapshot(test_app, tmp_snapshot_dir)
        baseline = load_snapshot(tmp_snapshot_dir)
        live = extract_manifest(test_app)
        drifts = detect_drift(live, baseline)
        assert len(drifts) == 0  # No drift right after snapshot


# ── 5) Full Audit Report ─────────────────────────────────────────────────

class TestFullAudit:

    def test_audit_returns_report(self, test_app):
        report = run_audit(test_app)
        assert report.total_routes > 0
        assert "errors" in report.summary
        assert "warnings" in report.summary

    def test_audit_to_dict(self, test_app):
        report = run_audit(test_app)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "violations" in d
        assert "drift" in d
        assert "summary" in d

    def test_audit_with_manifest(self, test_app):
        report = run_audit(test_app, include_manifest=True)
        assert len(report.route_manifest) > 0

    def test_quick_summary(self, test_app):
        result = quick_summary(test_app)
        assert "total_routes" in result
        assert "policy_errors" in result
        assert "checksum" in result
        assert isinstance(result["healthy"], bool)


# ── 6) Integration: against real CareerTrojan app ────────────────────────

class TestRealApp:
    """Smoke tests against the actual CareerTrojan FastAPI app."""

    @pytest.fixture
    def real_app(self):
        from services.backend_api.main import app
        return app

    def test_real_app_manifest_has_routes(self, real_app):
        manifest = extract_manifest(real_app)
        assert len(manifest) > 100  # We know there are 377 routes

    def test_real_app_policy_errors_exist(self, real_app):
        """We know there are auth gaps — governance should catch them."""
        manifest = extract_manifest(real_app)
        violations = check_policies(manifest)
        errors = [v for v in violations if v.severity == "error"]
        # We expect some errors (known gaps in payment, credits, etc.)
        assert len(errors) > 0

    def test_real_app_quick_summary(self, real_app):
        result = quick_summary(real_app)
        assert result["total_routes"] > 100
        assert isinstance(result["checksum"], str)

    def test_real_app_full_audit(self, real_app):
        report = run_audit(real_app)
        assert report.total_routes > 100
        assert report.summary["errors"] >= 0
