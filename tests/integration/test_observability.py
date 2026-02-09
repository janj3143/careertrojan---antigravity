"""
Integration tests for Tier 3 — Health checks, request correlation, structured logging.
"""
import pytest
from starlette.testclient import TestClient

from services.backend_api.main import app
from services.backend_api.db.connection import engine
from services.backend_api.db.models import Base

Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.mark.integration
class TestHealthEndpointsDeep:

    def test_light_health(self):
        r = client.get("/api/shared/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_deep_health(self):
        r = client.get("/api/shared/v1/health/deep")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "disk" in data["checks"]
        assert "directories" in data["checks"]
        # DB should be reachable in test env
        assert data["checks"]["database"]["status"] == "ok"
        assert "latency_ms" in data["checks"]["database"]

    def test_deep_health_disk_info(self):
        r = client.get("/api/shared/v1/health/deep")
        disk = r.json()["checks"]["disk"]
        assert "free_gb" in disk
        assert "total_gb" in disk
        assert disk["free_gb"] > 0


@pytest.mark.integration
class TestRequestCorrelation:

    def test_response_has_request_id_header(self):
        """Every response should include X-Request-ID."""
        r = client.get("/api/shared/v1/health")
        assert "x-request-id" in r.headers

    def test_custom_request_id_echoed(self):
        """If client sends X-Request-ID, it should be echoed back."""
        r = client.get("/api/shared/v1/health", headers={"X-Request-ID": "test-123"})
        assert r.headers.get("x-request-id") == "test-123"

    def test_request_id_unique_per_request(self):
        """Two requests should get different request IDs."""
        r1 = client.get("/api/shared/v1/health")
        r2 = client.get("/api/shared/v1/health")
        assert r1.headers["x-request-id"] != r2.headers["x-request-id"]
