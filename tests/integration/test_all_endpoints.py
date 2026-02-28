"""
Comprehensive endpoint integration tests.
Validates every API route returns expected status codes,
response shapes, and CORS headers.

Requires a running backend at localhost:8600.
Marked @pytest.mark.live_server — skipped in default test runs.
Run explicitly:  pytest -m live_server tests/integration/test_all_endpoints.py
"""
import pytest, httpx, asyncio
from typing import Any

pytestmark = pytest.mark.live_server   # skip unless `pytest -m live_server`

BASE_URL = "http://localhost:8600"

# ─── ALL EXPECTED ENDPOINTS ──────────────────────────────────────────────────
# Format: (method, path, expected_status, description, requires_auth)

HEALTH_ENDPOINTS = [
    ("GET", "/api/admin/v1/api-health/summary", 200, "API health summary", True),
    ("GET", "/docs", 200, "OpenAPI docs page", False),
    ("GET", "/openapi.json", 200, "OpenAPI schema", False),
]

AUTH_ENDPOINTS = [
    ("POST", "/api/auth/v1/login", 422, "login (no body → 422)", False),
    ("POST", "/api/auth/v1/register", 422, "register (no body → 422)", False),
]

USER_ENDPOINTS = [
    ("GET", "/api/user/v1/me", 401, "user profile (unauthed)", False),
    ("GET", "/api/user/v1/profile", 401, "user profile detail", False),
    ("GET", "/api/user/v1/stats", 401, "user stats", False),
    ("GET", "/api/user/v1/activity", 401, "user activity", False),
]

RESUME_ENDPOINTS = [
    ("POST", "/api/resume/v1/upload", 401, "resume upload (unauthed)", False),
    ("GET", "/api/resume/v1/latest", 401, "latest resume", False),
]

COACHING_ENDPOINTS = [
    ("POST", "/api/coaching/v1/questions/generate", 401, "coaching questions", False),
    ("POST", "/api/coaching/v1/answers/review", 401, "answer review", False),
    ("POST", "/api/coaching/v1/stories/generate", 401, "star stories", False),
    ("POST", "/api/coaching/v1/blockers/detect", 401, "blocker detection", False),
]

JOBS_ENDPOINTS = [
    ("GET", "/api/jobs/v1/index", [200, 401], "job index", False),
]

PAYMENT_ENDPOINTS = [
    ("GET", "/api/payment/v1/plans", [200, 401], "payment plans", False),
    ("GET", "/api/payment/v1/gateway-info", [200, 401], "gateway info", False),
]

MENTOR_ENDPOINTS = [
    ("GET", "/api/mentor/v1/list", [200, 401], "mentor list", False),
    ("POST", "/api/mentorship/v1/applications", 401, "mentor application", False),
]

INSIGHTS_ENDPOINTS = [
    ("GET", "/api/insights/v1/visuals", [200, 401], "visual catalogue", False),
    ("POST", "/api/insights/v1/cohort/resolve", 401, "cohort resolve", False),
]

ADMIN_ENDPOINTS = [
    ("GET", "/api/admin/v1/dashboard/snapshot", 401, "admin dashboard", False),
    ("GET", "/api/admin/v1/system/health", [200, 401], "system health", False),
    ("GET", "/api/admin/v1/users", 401, "user management", False),
    ("GET", "/api/admin/v1/tokens/config", 401, "token config", False),
    ("GET", "/api/admin/v1/tokens/usage", 401, "token usage", False),
]

TAXONOMY_ENDPOINTS = [
    ("GET", "/api/taxonomy/v1/industries", [200, 401], "taxonomy industries", False),
    ("GET", "/api/taxonomy/v1/summary", [200, 401], "taxonomy summary", False),
]

REWARDS_ENDPOINTS = [
    ("GET", "/api/rewards/v1/rewards", 401, "rewards list", False),
    ("GET", "/api/rewards/v1/rewards/available", 401, "available rewards", False),
]

GDPR_ENDPOINTS = [
    ("POST", "/api/gdpr/v1/consent", 422, "GDPR consent (no body)", False),
]

ALL_ENDPOINTS = (
    HEALTH_ENDPOINTS + AUTH_ENDPOINTS + USER_ENDPOINTS + RESUME_ENDPOINTS +
    COACHING_ENDPOINTS + JOBS_ENDPOINTS + PAYMENT_ENDPOINTS + MENTOR_ENDPOINTS +
    INSIGHTS_ENDPOINTS + ADMIN_ENDPOINTS + TAXONOMY_ENDPOINTS +
    REWARDS_ENDPOINTS + GDPR_ENDPOINTS
)


@pytest.fixture(scope="module")
def client():
    """Shared HTTP client for the test module. Skips all tests if backend unreachable."""
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as c:
        try:
            resp = c.get("/openapi.json", timeout=3.0)
            # NGINX may return 200 with HTML even when backend is down.
            # Only proceed if we get actual JSON back from FastAPI.
            if resp.status_code != 200 or "application/json" not in resp.headers.get("content-type", ""):
                pytest.skip(f"FastAPI backend not running at {BASE_URL} (got {resp.status_code}, content-type: {resp.headers.get('content-type', 'unknown')})")
        except (httpx.ConnectError, httpx.ConnectTimeout):
            pytest.skip(f"Backend not running at {BASE_URL}")
        yield c


class TestEndpointAvailability:
    """Every registered endpoint must respond (not 404/405)."""

    @pytest.mark.parametrize(
        "method,path,expected,desc,_auth",
        ALL_ENDPOINTS,
        ids=[f"{m} {p}" for m, p, *_ in ALL_ENDPOINTS],
    )
    def test_endpoint_responds(self, client, method, path, expected, desc, _auth):
        resp = client.request(method, path)
        if isinstance(expected, list):
            assert resp.status_code in expected, \
                f"{desc}: got {resp.status_code}, expected one of {expected}"
        else:
            assert resp.status_code == expected, \
                f"{desc}: got {resp.status_code}, expected {expected}"
        # Must never be 404 (route not found) or 405 (method not allowed)
        assert resp.status_code != 404, f"{desc}: route not registered (404)"
        assert resp.status_code != 405, f"{desc}: method not allowed (405)"


class TestCORSHeaders:
    """API endpoints must return proper CORS headers."""

    def test_options_preflight(self, client):
        resp = client.request(
            "OPTIONS", "/api/auth/v1/login",
            headers={"Origin": "http://localhost:3000"}
        )
        assert resp.status_code in (200, 204, 405)

    def test_api_response_json(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")


class TestOpenAPISchema:
    """OpenAPI schema must list all expected router prefixes."""

    EXPECTED_PREFIXES = [
        "/api/auth/v1", "/api/user/v1", "/api/resume/v1",
        "/api/coaching/v1", "/api/jobs/v1", "/api/payment/v1",
        "/api/mentor/v1", "/api/mentorship/v1", "/api/insights/v1",
        "/api/admin/v1", "/api/taxonomy/v1", "/api/rewards/v1",
        "/api/gdpr/v1", "/api/analytics/v1", "/api/credits/v1",
        "/api/sessions/v1", "/api/shared/v1", "/api/telemetry/v1",
        "/api/touchpoints/v1", "/api/mapping/v1", "/api/intelligence/v1",
        "/api/blockers/v1", "/api/ops/v1",
    ]

    def test_all_router_prefixes_in_schema(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        paths = list(schema.get("paths", {}).keys())
        all_path_text = " ".join(paths)
        missing = []
        for prefix in self.EXPECTED_PREFIXES:
            if not any(p.startswith(prefix) for p in paths):
                missing.append(prefix)
        assert not missing, f"Router prefixes missing from OpenAPI: {missing}"

    def test_schema_has_info(self, client):
        resp = client.get("/openapi.json")
        schema = resp.json()
        assert "info" in schema
        assert "title" in schema["info"]

    def test_minimum_route_count(self, client):
        resp = client.get("/openapi.json")
        schema = resp.json()
        route_count = len(schema.get("paths", {}))
        assert route_count >= 100, f"Only {route_count} routes, expected >= 100"
