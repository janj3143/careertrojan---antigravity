import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from services.backend_api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_support_health(client: TestClient):
    response = client.get('/api/support/v1/health')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['mode'] in ('stub', 'zendesk')  # Mode depends on env config


def test_support_widget_config(client: TestClient):
    response = client.get('/api/support/v1/widget-config?portal=admin&user_id=tester&user_email=test@example.com')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['bootstrap']['portal'] == 'admin'
    assert payload['bootstrap']['session']['user']['id'] == 'tester'


def test_support_status_includes_readiness(client: TestClient):
    response = client.get('/api/support/v1/status')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'readiness' in payload
    assert 'ready' in payload['readiness']


def test_support_wiring_test(client: TestClient):
    response = client.get('/api/support/v1/wiring-test?portal=user')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['portal'] == 'user'
    assert isinstance(payload['checks'], list)


def test_support_providers_map(client: TestClient):
    response = client.get('/api/support/v1/providers')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['active']['provider'] in {'stub', 'zendesk'}
    providers = {item['provider'] for item in payload['available']}
    assert 'stub' in providers
    assert 'zendesk' in providers


def test_support_readiness_endpoint(client: TestClient):
    response = client.get('/api/support/v1/readiness')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'ready' in payload
    assert 'missing' in payload
