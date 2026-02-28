import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from services.backend_api.main import app
    return TestClient(app, raise_server_exceptions=False)


def test_create_support_ticket_stub_mode(client: TestClient):
    payload = {
        "subject": "Login issue",
        "description": "Unable to login after password reset",
        "category": "Login",
        "requester_email": "user@example.com",
        "portal": "user_portal",
    }

    response = client.post("/api/support/v1/tickets", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["ticket"]["id"] > 0
    assert body["ticket"]["subject"] == "Login issue"


def test_create_support_ticket_zendesk_mode_monkeypatched(client: TestClient, monkeypatch):
    from services.backend_api.routers import support as support_router

    monkeypatch.setattr(
        support_router,
        "get_helpdesk_config",
        lambda: {"provider": "zendesk", "mode": "zendesk"},
    )
    monkeypatch.setattr(
        support_router,
        "zendesk_create_ticket",
        lambda payload: {
            "zendesk_ticket_id": 123456,
            "status": "new",
            "priority": payload.get("priority"),
            "url": "https://careertrojan.zendesk.com/agent/tickets/123456",
        },
    )

    payload = {
        "subject": "Billing discrepancy",
        "description": "Charged twice",
        "category": "Billing",
        "requester_email": "billing@example.com",
        "priority": "normal",
        "portal": "user_portal",
        "subscription_tier": "premium",
        "tokens_remaining": 42,
        "request_id": "req-123",
    }

    response = client.post("/api/support/v1/tickets", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["ticket"]["zendesk_ticket_id"] == "123456"
    assert body["ticket"]["status"] == "new"


def test_get_support_ticket(client: TestClient):
    create_response = client.post(
        "/api/support/v1/tickets",
        json={
            "subject": "Feature request",
            "description": "Need bulk upload",
            "category": "Feature Request",
            "requester_email": "feature@example.com",
        },
    )
    ticket_id = create_response.json()["ticket"]["id"]

    fetch_response = client.get(f"/api/support/v1/tickets/{ticket_id}")
    assert fetch_response.status_code == 200
    body = fetch_response.json()
    assert body["ticket"]["id"] == ticket_id


def test_zendesk_webhook_updates_ticket(client: TestClient):
    create_response = client.post(
        "/api/support/v1/tickets",
        json={
            "subject": "Webhook test",
            "description": "Testing webhook updates",
            "category": "Bugs",
            "requester_email": "webhook@example.com",
        },
    )
    ticket_id = create_response.json()["ticket"]["id"]

    from services.backend_api.db.connection import SessionLocal
    from services.backend_api.db import models

    db = SessionLocal()
    ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
    ticket.zendesk_ticket_id = "999999"
    db.commit()
    db.close()

    webhook_payload = {
        "ticket": {
            "id": 999999,
            "status": "solved",
            "priority": "high",
            "updated_at": "2026-02-27T10:00:00Z",
        },
        "event": "ticket.updated",
    }

    webhook_response = client.post("/api/support/v1/webhooks/zendesk", json=webhook_payload)
    assert webhook_response.status_code == 200
    body = webhook_response.json()
    assert body["updated_status"] == "solved"
