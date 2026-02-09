"""
Unit tests — App bootstrap & route inventory.
These verify the app boots cleanly and all expected routes are present.
"""

import sys
import os
import pytest
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


@pytest.mark.unit
class TestAppBootstrap:
    """Verify the FastAPI app loads without errors."""

    def test_app_imports_cleanly(self):
        from services.backend_api.main import app
        assert app is not None

    def test_app_has_routes(self):
        from services.backend_api.main import app
        routes = [r for r in app.routes if hasattr(r, "methods")]
        assert len(routes) >= 170, f"Expected ≥170 routes, got {len(routes)}"

    def test_openapi_schema_generates(self):
        from services.backend_api.main import app
        schema = app.openapi()
        assert "paths" in schema
        assert len(schema["paths"]) > 50


@pytest.mark.unit
class TestRouteInventory:
    """Verify all 11 Section 6.4 endpoints and critical routes exist."""

    @pytest.fixture(autouse=True)
    def _routes(self):
        from services.backend_api.main import app
        self.route_paths = set()
        for r in app.routes:
            if hasattr(r, "path"):
                self.route_paths.add(r.path)

    # ── Section 6.4 visual endpoints ─────────────────────────────────
    @pytest.mark.parametrize("path", [
        "/api/insights/v1/visuals",
        "/api/insights/v1/quadrant",
        "/api/insights/v1/skills/radar",
        "/api/insights/v1/graph",
        "/api/insights/v1/terms/cloud",
        "/api/insights/v1/terms/cooccurrence",
        "/api/insights/v1/cohort/resolve",
        "/api/touchpoints/v1/evidence",
        "/api/touchpoints/v1/touchnots",
        "/api/mapping/v1/graph",
        "/api/mapping/v1/endpoints",
        "/api/mapping/v1/registry",
    ])
    def test_visual_endpoint_exists(self, path):
        assert path in self.route_paths, f"Missing route: {path}"

    # ── Auth endpoints ───────────────────────────────────────────────
    @pytest.mark.parametrize("path", [
        "/api/auth/v1/register",
        "/api/auth/v1/login",
    ])
    def test_auth_endpoint_exists(self, path):
        assert path in self.route_paths, f"Missing route: {path}"

    # ── Core domain endpoints ────────────────────────────────────────
    @pytest.mark.parametrize("path", [
        "/api/user/v1/me",
        "/api/user/v1/profile",
        "/api/shared/v1/health",
        "/api/payment/v1/plans",
    ])
    def test_core_endpoint_exists(self, path):
        assert path in self.route_paths, f"Missing route: {path}"

    # ── No prefix collisions ─────────────────────────────────────────
    def test_no_duplicate_route_paths(self):
        from services.backend_api.main import app
        method_paths = []
        for r in app.routes:
            if hasattr(r, "methods"):
                for m in r.methods:
                    method_paths.append(f"{m} {r.path}")
        # Check for exact duplicates
        seen = set()
        dupes = []
        for mp in method_paths:
            if mp in seen:
                dupes.append(mp)
            seen.add(mp)
        assert len(dupes) == 0, f"Duplicate route+method combos: {dupes}"

    def test_all_prefixes_use_v1(self):
        """Every /api/... route should contain /v1/."""
        from services.backend_api.main import app
        bad = []
        for r in app.routes:
            if hasattr(r, "path") and r.path.startswith("/api/") and "/v1/" not in r.path and "/v1" not in r.path:
                bad.append(r.path)
        assert len(bad) == 0, f"Routes missing /v1: {bad}"
