from fastapi.testclient import TestClient
import pytest

from services.backend_api.main import app
from services.backend_api.routers import admin as admin_router
from services.backend_api.utils import security


def _clear_rate_limiter(app_instance):
    obj = getattr(app_instance, "middleware_stack", app_instance)
    for _ in range(20):
        if hasattr(obj, "_hits"):
            obj._hits.clear()
            return
        obj = getattr(obj, "app", None)
        if obj is None:
            break


@pytest.fixture(autouse=True)
def _reset_state():
    _clear_rate_limiter(app)

    for provider in admin_router._integration_state:
        admin_router._integration_state[provider]["configured"] = False
        admin_router._integration_state[provider]["api_key_masked"] = None
        admin_router._integration_state[provider]["last_configured_at"] = None

    admin_router._email_dispatch_log.clear()

    yield

    _clear_rate_limiter(app)
    admin_router._email_dispatch_log.clear()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers():
    token = security.create_access_token(data={"sub": "integration-admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_headers():
    token = security.create_access_token(data={"sub": "integration-user", "role": "user"})
    return {"Authorization": f"Bearer {token}"}


def test_integrations_status_auth_required(client):
    response = client.get("/api/admin/v1/integrations/status")
    assert response.status_code in (401, 403)


def test_integrations_status_admin_ok(client, admin_headers):
    response = client.get("/api/admin/v1/integrations/status", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert "providers" in payload
    assert "sendgrid" in payload["providers"]
    assert "klaviyo" in payload["providers"]


def test_configure_sendgrid_and_send_test(client, admin_headers):
    configure = client.post(
        "/api/admin/v1/integrations/sendgrid/configure",
        headers=admin_headers,
        json={"api_key": "SG.xxxxxxxxxxxx"},
    )
    assert configure.status_code == 200

    send_test = client.post(
        "/api/admin/v1/email/send_test",
        headers=admin_headers,
        json={"to": "test@example.com", "subject": "Ping", "body": "Hello", "provider": "sendgrid"},
    )
    assert send_test.status_code == 200
    payload = send_test.json()
    assert payload["status"] == "queued"
    assert payload["provider"] == "sendgrid"


def test_configure_klaviyo_and_send_bulk(client, admin_headers):
    configure = client.post(
        "/api/admin/v1/integrations/klaviyo/configure",
        headers=admin_headers,
        json={"api_key": "KLV.xxxxxxxxxxxx"},
    )
    assert configure.status_code == 200

    send_bulk = client.post(
        "/api/admin/v1/email/send_bulk",
        headers=admin_headers,
        json={
            "recipients": ["a@example.com", "b@example.com"],
            "subject": "Update",
            "body": "Body",
            "provider": "klaviyo",
        },
    )
    assert send_bulk.status_code == 200
    payload = send_bulk.json()
    assert payload["status"] == "queued"
    assert payload["provider"] == "klaviyo"
    assert payload["recipient_count"] == 2


def test_disconnect_provider(client, admin_headers):
    response = client.post(
        "/api/admin/v1/integrations/sendgrid/disconnect",
        headers=admin_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "disconnected"
    assert payload["provider"] == "sendgrid"


def test_email_logs_and_analytics(client, admin_headers):
    client.post(
        "/api/admin/v1/integrations/sendgrid/configure",
        headers=admin_headers,
        json={"api_key": "SG.xxxxxxxxxxxx"},
    )
    client.post(
        "/api/admin/v1/email/send_test",
        headers=admin_headers,
        json={"to": "test@example.com", "subject": "Ping", "provider": "sendgrid"},
    )
    client.post(
        "/api/admin/v1/email/send_bulk",
        headers=admin_headers,
        json={"recipients": ["a@example.com", "b@example.com"], "subject": "Update", "provider": "sendgrid"},
    )

    logs = client.get("/api/admin/v1/email/logs", headers=admin_headers)
    assert logs.status_code == 200
    log_payload = logs.json()
    assert log_payload["count"] >= 2

    analytics = client.get("/api/admin/v1/email/analytics", headers=admin_headers)
    assert analytics.status_code == 200
    analytics_payload = analytics.json()
    assert analytics_payload["total_messages"] >= 2
    assert analytics_payload["by_provider"]["sendgrid"] >= 2


def test_non_admin_blocked_from_configure(client, user_headers):
    response = client.post(
        "/api/admin/v1/integrations/sendgrid/configure",
        headers=user_headers,
        json={"api_key": "SG.xxxxxxxxxxxx"},
    )
    assert response.status_code == 403
