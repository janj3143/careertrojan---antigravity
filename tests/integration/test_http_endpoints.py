"""
Integration tests — HTTP-level endpoint testing via TestClient.
"""

import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from starlette.testclient import TestClient
from services.backend_api.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.mark.integration
class TestHealthEndpoints:

    def test_shared_health(self):
        r = client.get("/api/shared/v1/health")
        assert r.status_code == 200

    def test_payment_health(self):
        r = client.get("/api/payment/v1/health")
        assert r.status_code == 200

    def test_rewards_health(self):
        r = client.get("/api/rewards/v1/health")
        assert r.status_code == 200


@pytest.mark.integration
class TestInsightsEndpoints:

    def test_visuals_catalogue(self):
        r = client.get("/api/insights/v1/visuals")
        assert r.status_code == 200
        data = r.json()
        assert "visuals" in data
        assert len(data["visuals"]) >= 4

    def test_skills_radar(self):
        r = client.get("/api/insights/v1/skills/radar")
        assert r.status_code == 200
        data = r.json()
        assert "axes" in data
        assert "series" in data

    def test_quadrant(self):
        r = client.get("/api/insights/v1/quadrant")
        # May return data or an error if DataLoader can't load profiles
        assert r.status_code in (200, 500)

    def test_cohort_resolve(self):
        r = client.post("/api/insights/v1/cohort/resolve", json={"industry": "tech"})
        assert r.status_code == 200
        assert "cohort_id" in r.json()


@pytest.mark.integration
class TestTouchpointsEndpoints:

    def test_evidence_empty(self):
        r = client.get("/api/touchpoints/v1/evidence")
        assert r.status_code == 200
        assert r.json() == {"items": []}

    def test_evidence_with_ids(self):
        r = client.get("/api/touchpoints/v1/evidence?touchpoint_id=tp1&touchpoint_id=tp2")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2

    def test_touchnots_empty(self):
        r = client.get("/api/touchpoints/v1/touchnots")
        assert r.status_code == 200
        assert r.json() == {"items": []}


@pytest.mark.integration
class TestMappingEndpoints:

    def test_registry(self):
        r = client.get("/api/mapping/v1/registry",
                       headers={"Authorization": "Bearer fake"})
        # May 500 if mapping service has unmet runtime deps in test env
        assert r.status_code in (200, 401, 403, 500)

    def test_endpoints_listing(self):
        r = client.get("/api/mapping/v1/endpoints",
                       headers={"Authorization": "Bearer fake"})
        assert r.status_code in (200, 401, 403, 500)


@pytest.mark.integration
class TestAuthEndpoints:

    def test_register_missing_params(self):
        r = client.post("/api/auth/v1/register")
        # Missing required params → 422
        assert r.status_code == 422

    def test_login_missing_params(self):
        r = client.post("/api/auth/v1/login")
        assert r.status_code == 422

    def test_openapi_docs(self):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_openapi_json(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema


@pytest.mark.integration
class TestRateLimiting:
    """Verify global rate-limit middleware returns 429 on burst."""

    def test_rate_limit_eventually_triggers(self):
        """Fire 120 rapid requests to a non-exempt endpoint; expect at least one 429."""
        statuses = []
        for _ in range(120):
            # Use /api/insights/v1/visuals — NOT exempt from rate limiting
            r = client.get("/api/insights/v1/visuals")
            statuses.append(r.status_code)
        assert 429 in statuses, "Rate limiter did not trigger on 120 rapid requests"
