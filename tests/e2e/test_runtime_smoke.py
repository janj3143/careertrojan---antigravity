"""
E2E smoke tests for the J-drive CareerTrojan runtime.
These validate a full user-facing API journey through the assembled stack.
"""

import pytest


@pytest.mark.e2e
def test_api_journey_health_to_touchpoints(test_client):
    """
    Validate a realistic end-to-end API flow:
    health -> insights catalogue -> cohort resolve -> touchpoint evidence.
    """
    health = test_client.get("/api/shared/v1/health")
    assert health.status_code == 200
    assert health.json().get("status") == "ok"
    assert health.headers.get("x-request-id")

    visuals = test_client.get("/api/insights/v1/visuals")
    assert visuals.status_code == 200
    visuals_payload = visuals.json()
    assert "visuals" in visuals_payload
    assert len(visuals_payload["visuals"]) >= 4

    cohort = test_client.post(
        "/api/insights/v1/cohort/resolve",
        json={"industry": "tech"},
    )
    assert cohort.status_code == 200
    cohort_payload = cohort.json()
    assert cohort_payload.get("cohort_id")
    assert isinstance(cohort_payload.get("count"), int)

    evidence = test_client.get(
        "/api/touchpoints/v1/evidence",
        params=[("touchpoint_id", "tp1"), ("touchpoint_id", "tp2")],
    )
    assert evidence.status_code == 200
    evidence_payload = evidence.json()
    assert evidence_payload.get("count") == 2
    assert len(evidence_payload.get("items", [])) == 2

    touchnots = test_client.get("/api/touchpoints/v1/touchnots")
    assert touchnots.status_code == 200
    assert isinstance(touchnots.json().get("items"), list)


@pytest.mark.e2e
def test_openapi_contains_critical_runtime_routes(test_client):
    """Ensure runtime OpenAPI schema exposes critical production routes."""
    response = test_client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    paths = schema["paths"]

    required_paths = [
        "/api/shared/v1/health",
        "/api/insights/v1/visuals",
        "/api/insights/v1/cohort/resolve",
        "/api/touchpoints/v1/evidence",
        "/api/touchpoints/v1/touchnots",
    ]

    for path in required_paths:
        assert path in paths, f"Missing OpenAPI path: {path}"
