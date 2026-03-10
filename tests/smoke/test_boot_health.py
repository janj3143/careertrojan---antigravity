import pytest


@pytest.mark.smoke
def test_shared_health_boot_ok(test_client):
    response = test_client.get("/api/shared/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
    assert response.headers.get("x-request-id")


@pytest.mark.smoke
def test_openapi_boot_ok(test_client):
    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "paths" in payload
