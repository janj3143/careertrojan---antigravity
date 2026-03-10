import pytest


@pytest.mark.contract
def test_shared_health_contract(test_client):
    response = test_client.get("/api/shared/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert set(["status"]).issubset(payload.keys())


@pytest.mark.contract
def test_visuals_contract_shape(test_client):
    response = test_client.get("/api/insights/v1/visuals")
    assert response.status_code == 200

    payload = response.json()
    assert "visuals" in payload
    assert isinstance(payload["visuals"], list)
