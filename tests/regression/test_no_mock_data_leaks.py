import json
import pytest


SUSPICIOUS_TOKENS = ("mock", "fake", "fabricated", "stub")


def _contains_suspicious_text(value):
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in SUSPICIOUS_TOKENS)
    if isinstance(value, dict):
        return any(_contains_suspicious_text(k) or _contains_suspicious_text(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_contains_suspicious_text(item) for item in value)
    return False


@pytest.mark.regression
def test_ops_stats_payload_has_no_mock_strings(test_client):
    response = test_client.get("/api/ops/v1/stats/public")
    assert response.status_code == 200

    payload = response.json()
    assert not _contains_suspicious_text(payload), json.dumps(payload)


@pytest.mark.regression
def test_market_payload_has_no_mock_strings(test_client):
    response = test_client.get("/api/intelligence/v1/market")
    assert response.status_code == 200

    payload = response.json()
    assert not _contains_suspicious_text(payload), json.dumps(payload)
