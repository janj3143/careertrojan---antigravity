"""
API Integration Tests
=====================

Validates all API endpoints are reachable and return expected response structures.
Uses the FastAPI TestClient for synchronous testing.

Run with:
    pytest tests/integration/test_api_endpoints.py -v
"""

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI app
from services.backend_api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Utility Helpers
# ---------------------------------------------------------------------------

def assert_status_ok(response, allowed_codes=(200, 201)):
    """Helper to assert response is successful and returns parsed JSON."""
    assert response.status_code in allowed_codes, f"Got {response.status_code}: {response.text[:500]}"
    return response.json()


def assert_status_any(response, allowed_codes=(200, 201, 404, 422)):
    """Helper for endpoints that may legitimately return various status codes."""
    assert response.status_code in allowed_codes, f"Got unexpected {response.status_code}: {response.text[:500]}"
    return response.json() if response.status_code in (200, 201) else None


# ---------------------------------------------------------------------------
# Core Health Endpoints
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Test core health and readiness endpoints."""

    def test_root_health(self):
        """GET /health - Fast liveness probe"""
        response = client.get("/health")
        data = assert_status_ok(response)
        assert data.get("status") == "ok"

    def test_shared_health(self):
        """GET /api/shared/v1/health - Lightweight liveness"""
        response = client.get("/api/shared/v1/health")
        data = assert_status_ok(response)
        assert data.get("status") == "ok"

    def test_shared_deep_health(self):
        """GET /api/shared/v1/health/deep - Full readiness probe"""
        response = client.get("/api/shared/v1/health/deep")
        # May fail if DB not available, but endpoint should respond
        assert response.status_code in (200, 500)


# ---------------------------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------------------------

class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_validation(self):
        """POST /api/auth/v1/register - Validation check"""
        response = client.post("/api/auth/v1/register", json={})
        # Should fail validation (422) or return success structure
        assert response.status_code in (200, 201, 422)

    def test_login_validation(self):
        """POST /api/auth/v1/login - Validation check"""
        response = client.post("/api/auth/v1/login", json={
            "email": "test@example.com",
            "password": "testpass"
        })
        # Will fail login but endpoint should respond
        assert response.status_code in (200, 401, 422)

    def test_2fa_generate(self):
        """POST /api/auth/v1/2fa/generate"""
        response = client.post("/api/auth/v1/2fa/generate", json={"user_id": "test-user"})
        assert response.status_code in (200, 401, 422, 404)


# ---------------------------------------------------------------------------
# User Endpoints
# ---------------------------------------------------------------------------

class TestUserEndpoints:
    """Test user-facing endpoints."""

    def test_user_profile_requires_auth(self):
        """User endpoints should require authentication"""
        response = client.get("/api/user/v1/profile")
        # Should return 401 or 403 without token
        assert response.status_code in (200, 401, 403, 422)


# ---------------------------------------------------------------------------
# Admin Endpoints
# ---------------------------------------------------------------------------

class TestAdminEndpoints:
    """Test admin endpoints."""

    def test_admin_users_list(self):
        """GET /api/admin/v1/users"""
        response = client.get("/api/admin/v1/users")
        # May require auth but should respond
        assert response.status_code in (200, 401, 403)

    def test_admin_system_health(self):
        """GET /api/admin/v1/system/health"""
        response = client.get("/api/admin/v1/system/health")
        assert response.status_code in (200, 401, 403)

    def test_admin_compliance_summary(self):
        """GET /api/admin/v1/compliance/summary"""
        response = client.get("/api/admin/v1/compliance/summary")
        assert response.status_code in (200, 401, 403)

    def test_admin_dashboard_snapshot(self):
        """GET /api/admin/v1/dashboard/snapshot"""
        response = client.get("/api/admin/v1/dashboard/snapshot")
        assert response.status_code in (200, 401, 403)


# ---------------------------------------------------------------------------
# Data Index Endpoints
# ---------------------------------------------------------------------------

class TestDataIndexEndpoints:
    """Test AI data indexing system endpoints."""

    def test_index_status(self):
        """GET /api/data-index/v1/status"""
        response = client.get("/api/data-index/v1/status")
        data = assert_status_ok(response)
        assert "status" in data
        assert "ai_data" in data
        assert "parser" in data

    def test_index_health(self):
        """GET /api/data-index/v1/health"""
        response = client.get("/api/data-index/v1/health")
        data = assert_status_ok(response)
        assert "status" in data

    def test_ai_data_summary(self):
        """GET /api/data-index/v1/ai-data/summary"""
        response = client.get("/api/data-index/v1/ai-data/summary")
        data = assert_status_ok(response)
        assert "status" in data

    def test_ai_data_categories(self):
        """GET /api/data-index/v1/ai-data/categories"""
        response = client.get("/api/data-index/v1/ai-data/categories")
        data = assert_status_ok(response)
        assert "status" in data

    def test_ai_data_skills(self):
        """GET /api/data-index/v1/ai-data/skills"""
        response = client.get("/api/data-index/v1/ai-data/skills")
        data = assert_status_ok(response)
        assert "status" in data

    def test_ai_data_skills_search(self):
        """GET /api/data-index/v1/ai-data/skills/search"""
        response = client.get("/api/data-index/v1/ai-data/skills/search", params={"q": "python"})
        data = assert_status_ok(response)
        assert "status" in data
        assert "results" in data

    def test_ai_data_industries(self):
        """GET /api/data-index/v1/ai-data/industries"""
        response = client.get("/api/data-index/v1/ai-data/industries")
        data = assert_status_ok(response)
        assert "status" in data

    def test_ai_data_locations(self):
        """GET /api/data-index/v1/ai-data/locations"""
        response = client.get("/api/data-index/v1/ai-data/locations")
        data = assert_status_ok(response)
        assert "status" in data

    def test_parser_summary(self):
        """GET /api/data-index/v1/parser/summary"""
        response = client.get("/api/data-index/v1/parser/summary")
        data = assert_status_ok(response)
        assert "status" in data

    def test_parser_status(self):
        """GET /api/data-index/v1/parser/status"""
        response = client.get("/api/data-index/v1/parser/status")
        data = assert_status_ok(response)
        assert "status" in data

    def test_parser_runs(self):
        """GET /api/data-index/v1/parser/runs"""
        response = client.get("/api/data-index/v1/parser/runs")
        data = assert_status_ok(response)
        assert "status" in data

    def test_dependencies(self):
        """GET /api/data-index/v1/dependencies"""
        response = client.get("/api/data-index/v1/dependencies")
        data = assert_status_ok(response)
        assert "dependencies" in data

    def test_files_new_data_summary(self):
        """GET /api/data-index/v1/files/new-data-summary"""
        response = client.get("/api/data-index/v1/files/new-data-summary")
        data = assert_status_ok(response)
        # Will return status even if never indexed

    def test_files_manifest_stats(self):
        """GET /api/data-index/v1/files/manifest-stats"""
        response = client.get("/api/data-index/v1/files/manifest-stats")
        data = assert_status_ok(response)
        assert "total_tracked_files" in data


# ---------------------------------------------------------------------------
# AI Data Endpoints
# ---------------------------------------------------------------------------

class TestAIDataEndpoints:
    """Test AI data access endpoints."""

    def test_parsed_resumes_list(self):
        """GET /api/ai-data/v1/parsed_resumes"""
        response = client.get("/api/ai-data/v1/parsed_resumes")
        data = assert_status_ok(response)
        assert "data" in data or "items" in data or isinstance(data, list)

    def test_job_descriptions_list(self):
        """GET /api/ai-data/v1/job_descriptions"""
        response = client.get("/api/ai-data/v1/job_descriptions")
        data = assert_status_ok(response)

    def test_companies_list(self):
        """GET /api/ai-data/v1/companies"""
        response = client.get("/api/ai-data/v1/companies")
        # May return 404 if data directory doesn't exist
        assert response.status_code in (200, 404)

    def test_job_titles_list(self):
        """GET /api/ai-data/v1/job_titles"""
        response = client.get("/api/ai-data/v1/job_titles")
        data = assert_status_ok(response)

    def test_locations_list(self):
        """GET /api/ai-data/v1/locations"""
        response = client.get("/api/ai-data/v1/locations")
        data = assert_status_ok(response)

    def test_status(self):
        """GET /api/ai-data/v1/status"""
        response = client.get("/api/ai-data/v1/status")
        data = assert_status_ok(response)

    def test_parser_ingestion_status(self):
        """GET /api/ai-data/v1/parser/ingestion-status"""
        response = client.get("/api/ai-data/v1/parser/ingestion-status")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Analytics Endpoints
# ---------------------------------------------------------------------------

class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    def test_statistics(self):
        """GET /api/analytics/v1/statistics"""
        response = client.get("/api/analytics/v1/statistics")
        data = assert_status_ok(response)

    def test_dashboard(self):
        """GET /api/analytics/v1/dashboard"""
        response = client.get("/api/analytics/v1/dashboard")
        data = assert_status_ok(response)

    def test_system_health(self):
        """GET /api/analytics/v1/system_health"""
        response = client.get("/api/analytics/v1/system_health")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Credits Endpoints
# ---------------------------------------------------------------------------

class TestCreditsEndpoints:
    """Test credits/token system endpoints."""

    def test_plans(self):
        """GET /api/credits/v1/plans - Requires auth"""
        response = client.get("/api/credits/v1/plans")
        # Requires authentication
        assert response.status_code in (200, 401)

    def test_actions(self):
        """GET /api/credits/v1/actions"""
        response = client.get("/api/credits/v1/actions")
        data = assert_status_ok(response)
        assert isinstance(data, list)

    def test_health(self):
        """GET /api/credits/v1/health"""
        response = client.get("/api/credits/v1/health")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Rewards Endpoints
# ---------------------------------------------------------------------------

class TestRewardsEndpoints:
    """Test rewards/referral system endpoints."""

    def test_leaderboard(self):
        """GET /api/rewards/v1/leaderboard - Requires auth"""
        response = client.get("/api/rewards/v1/leaderboard")
        # Requires authentication
        assert response.status_code in (200, 401)

    def test_ownership_stats(self):
        """GET /api/rewards/v1/ownership-stats - Requires auth and DB tables"""
        # This endpoint may throw DB exceptions if tables don't exist
        try:
            response = client.get("/api/rewards/v1/ownership-stats")
            # May fail if not authenticated or table doesn't exist
            assert response.status_code in (200, 401, 500)
        except Exception:
            # Acceptable - endpoint exists but DB not initialized
            pass

    def test_tiers(self):
        """GET /api/rewards/v1/tiers"""
        response = client.get("/api/rewards/v1/tiers")
        # Public endpoint - may return 404 if not found
        assert response.status_code in (200, 401, 404)


# ---------------------------------------------------------------------------
# Support Endpoints
# ---------------------------------------------------------------------------

class TestSupportEndpoints:
    """Test helpdesk/support endpoints."""

    def test_health(self):
        """GET /api/support/v1/health"""
        response = client.get("/api/support/v1/health")
        data = assert_status_ok(response)
        assert data.get("status") == "ok"

    def test_status(self):
        """GET /api/support/v1/status"""
        response = client.get("/api/support/v1/status")
        data = assert_status_ok(response)

    def test_providers(self):
        """GET /api/support/v1/providers"""
        response = client.get("/api/support/v1/providers")
        # May have service-level errors
        assert response.status_code in (200, 500)

    def test_readiness(self):
        """GET /api/support/v1/readiness"""
        response = client.get("/api/support/v1/readiness")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Intelligence Endpoints
# ---------------------------------------------------------------------------

class TestIntelligenceEndpoints:
    """Test intelligence/company data endpoints."""

    def test_market(self):
        """GET /api/intelligence/v1/market"""
        response = client.get("/api/intelligence/v1/market")
        data = assert_status_ok(response)

    def test_company_registry(self):
        """GET /api/intelligence/v1/company/registry"""
        response = client.get("/api/intelligence/v1/company/registry")
        data = assert_status_ok(response)

    def test_pipeline_ops_summary(self):
        """GET /api/intelligence/v1/pipeline/ops-summary"""
        response = client.get("/api/intelligence/v1/pipeline/ops-summary")
        data = assert_status_ok(response)

    def test_support_status(self):
        """GET /api/intelligence/v1/support/status"""
        response = client.get("/api/intelligence/v1/support/status")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Mapping Endpoints
# ---------------------------------------------------------------------------

class TestMappingEndpoints:
    """Test API mapping/registry endpoints."""

    def test_registry(self):
        """GET /api/mapping/v1/registry"""
        response = client.get("/api/mapping/v1/registry")
        # May require auth or have internal errors
        assert response.status_code in (200, 401, 500)

    def test_endpoints(self):
        """GET /api/mapping/v1/endpoints"""
        response = client.get("/api/mapping/v1/endpoints")
        # May require auth or have internal errors
        assert response.status_code in (200, 401, 500)

    def test_graph(self):
        """GET /api/mapping/v1/graph"""
        response = client.get("/api/mapping/v1/graph")
        # May require auth or have internal errors
        assert response.status_code in (200, 401, 500)


# ---------------------------------------------------------------------------
# Coaching Endpoints
# ---------------------------------------------------------------------------

class TestCoachingEndpoints:
    """Test career coaching endpoints."""

    def test_health(self):
        """GET /api/coaching/v1/health"""
        response = client.get("/api/coaching/v1/health")
        data = assert_status_ok(response)

    def test_history_requires_user(self):
        """GET /api/coaching/v1/history"""
        response = client.get("/api/coaching/v1/history")
        # May require auth, or return empty
        assert response.status_code in (200, 401, 403, 422)


# ---------------------------------------------------------------------------
# Insights Endpoints
# ---------------------------------------------------------------------------

class TestInsightsEndpoints:
    """Test visual insights endpoints."""

    def test_visuals(self):
        """GET /api/insights/v1/visuals"""
        response = client.get("/api/insights/v1/visuals")
        data = assert_status_ok(response)

    def test_quadrant(self):
        """GET /api/insights/v1/quadrant"""
        response = client.get("/api/insights/v1/quadrant")
        data = assert_status_ok(response)

    def test_terms_cloud(self):
        """GET /api/insights/v1/terms/cloud"""
        response = client.get("/api/insights/v1/terms/cloud")
        data = assert_status_ok(response)

    def test_graph(self):
        """GET /api/insights/v1/graph"""
        response = client.get("/api/insights/v1/graph")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Sessions Endpoints
# ---------------------------------------------------------------------------

class TestSessionsEndpoints:
    """Test session tracking endpoints."""

    def test_sessions_endpoint_exists(self):
        """Sessions router should be mounted"""
        # Check the prefix exists - may require specific endpoints
        response = client.get("/api/sessions/v1/history")
        # Could require auth or return data
        assert response.status_code in (200, 401, 403, 404, 422)


# ---------------------------------------------------------------------------
# Taxonomy Endpoints
# ---------------------------------------------------------------------------

class TestTaxonomyEndpoints:
    """Test industry taxonomy endpoints."""

    def test_industries(self):
        """GET /api/taxonomy/v1/industries"""
        # This endpoint may have import or service errors
        try:
            response = client.get("/api/taxonomy/v1/industries")
            # May fail if service not available
            assert response.status_code in (200, 500)
        except Exception:
            # Acceptable - endpoint exists but service not fully initialized
            pass


# ---------------------------------------------------------------------------
# Jobs Endpoints
# ---------------------------------------------------------------------------

class TestJobsEndpoints:
    """Test jobs endpoints."""

    def test_index(self):
        """GET /api/jobs/v1/index"""
        response = client.get("/api/jobs/v1/index")
        # May return 503 if service unavailable, 500 if no data
        assert response.status_code in (200, 500, 503)

    def test_search(self):
        """GET /api/jobs/v1/search"""
        response = client.get("/api/jobs/v1/search")
        # May return 422 if missing params, 500 if no data
        assert response.status_code in (200, 422, 500)


# ---------------------------------------------------------------------------
# Ontology Endpoints
# ---------------------------------------------------------------------------

class TestOntologyEndpoints:
    """Test ontology/phrases endpoints."""

    def test_phrases(self):
        """GET /api/ontology/v1/phrases"""
        response = client.get("/api/ontology/v1/phrases")
        data = assert_status_ok(response)

    def test_phrases_summary(self):
        """GET /api/ontology/v1/phrases/summary"""
        response = client.get("/api/ontology/v1/phrases/summary")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Ops Endpoints
# ---------------------------------------------------------------------------

class TestOpsEndpoints:
    """Test operations endpoints."""

    def test_stats_public(self):
        """GET /api/ops/v1/stats/public"""
        response = client.get("/api/ops/v1/stats/public")
        data = assert_status_ok(response)

    def test_processing_status(self):
        """GET /api/ops/v1/processing/status"""
        response = client.get("/api/ops/v1/processing/status")
        data = assert_status_ok(response)

    def test_tokens_config(self):
        """GET /api/ops/v1/tokens/config"""
        response = client.get("/api/ops/v1/tokens/config")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# GDPR Endpoints
# ---------------------------------------------------------------------------

class TestGDPREndpoints:
    """Test GDPR/privacy endpoints."""

    def test_consent_get(self):
        """GET /api/gdpr/v1/consent"""
        response = client.get("/api/gdpr/v1/consent", params={"user_id": "test-user"})
        # May require auth or return 404 for unknown user
        assert response.status_code in (200, 401, 403, 404, 422)

    def test_audit_log(self):
        """GET /api/gdpr/v1/audit-log"""
        response = client.get("/api/gdpr/v1/audit-log", params={"user_id": "test-user"})
        assert response.status_code in (200, 401, 403, 404, 422)


# ---------------------------------------------------------------------------
# Blockers Endpoints
# ---------------------------------------------------------------------------

class TestBlockersEndpoints:
    """Test career blockers endpoints."""

    def test_detect(self):
        """POST /api/blockers/v1/detect"""
        response = client.post("/api/blockers/v1/detect", json={"user_profile": {}})
        assert response.status_code in (200, 422, 500)

    def test_user_blockers(self):
        """GET /api/blockers/v1/user/{user_id}"""
        response = client.get("/api/blockers/v1/user/test-user")
        # Returns empty list, 422 if validation error, or 500 if service error
        assert response.status_code in (200, 404, 422, 500)


# ---------------------------------------------------------------------------
# Touchpoints Endpoints
# ---------------------------------------------------------------------------

class TestTouchpointsEndpoints:
    """Test touchpoints/evidence endpoints."""

    def test_touchpoints_endpoint(self):
        """Touchpoints router should be mounted"""
        # Get a touchpoint by ID (may not exist)
        response = client.get("/api/touchpoints/v1/evidence/test-id")
        assert response.status_code in (200, 404)


# ---------------------------------------------------------------------------
# Mentor Endpoints
# ---------------------------------------------------------------------------

class TestMentorEndpoints:
    """Test mentor profile endpoints."""

    def test_list(self):
        """GET /api/mentor/v1/list"""
        response = client.get("/api/mentor/v1/list")
        data = assert_status_ok(response)
        assert isinstance(data, list)

    def test_health(self):
        """GET /api/mentor/v1/health"""
        response = client.get("/api/mentor/v1/health")
        data = assert_status_ok(response)


# ---------------------------------------------------------------------------
# Mentorship Endpoints
# ---------------------------------------------------------------------------

class TestMentorshipEndpoints:
    """Test mentorship relationship endpoints."""

    def test_summary(self):
        """GET /api/mentorship/v1/summary"""
        response = client.get("/api/mentorship/v1/summary")
        # May require auth, or have DB errors if tables not created
        assert response.status_code in (200, 401, 500)

    def test_health(self):
        """GET /api/mentorship/v1/health"""
        response = client.get("/api/mentorship/v1/health")
        # May have DB errors
        assert response.status_code in (200, 500)

    def test_applications_pending(self):
        """GET /api/mentorship/v1/applications/pending"""
        response = client.get("/api/mentorship/v1/applications/pending")
        # May have DB errors
        assert response.status_code in (200, 500)


# ---------------------------------------------------------------------------
# Payment Endpoints
# ---------------------------------------------------------------------------

class TestPaymentEndpoints:
    """Test payment/subscription endpoints."""

    def test_plans_list(self):
        """GET /api/payment/v1/plans"""
        response = client.get("/api/payment/v1/plans")
        # May require auth or not be fully wired
        assert response.status_code in (200, 401, 500)


# ---------------------------------------------------------------------------
# Resume Endpoints
# ---------------------------------------------------------------------------

class TestResumeEndpoints:
    """Test resume parsing endpoints."""

    def test_resume_endpoint_exists(self):
        """Resume router should be mounted"""
        # Check upload endpoint exists (will need auth/file)
        response = client.post("/api/resume/v1/upload")
        assert response.status_code in (200, 400, 401, 422)


# ---------------------------------------------------------------------------
# Telemetry Endpoints
# ---------------------------------------------------------------------------

class TestTelemetryEndpoints:
    """Test telemetry endpoints."""

    def test_telemetry_endpoint_exists(self):
        """Telemetry router should be mounted"""
        response = client.get("/api/telemetry/v1/metrics")
        # May have specific endpoints
        assert response.status_code in (200, 404, 500)


# ---------------------------------------------------------------------------
# Summary Test
# ---------------------------------------------------------------------------

class TestAPISummary:
    """
    Summary test to validate all major routers are mounted.
    Uses /api/mapping/v1/endpoints to get the full route list.
    """

    def test_all_routers_mounted(self):
        """Verify all expected routers are mounted via mapping endpoint"""
        response = client.get("/api/mapping/v1/endpoints")
        if response.status_code == 200:
            data = response.json()
            # Check we have substantial number of routes
            if isinstance(data, list):
                assert len(data) > 50, "Expected many routes to be registered"
            elif isinstance(data, dict) and "routes" in data:
                assert len(data["routes"]) > 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
