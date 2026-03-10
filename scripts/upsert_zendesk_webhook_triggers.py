from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


@dataclass
class ZendeskClient:
    base_url: str
    auth_user: str
    auth_token: str

    @property
    def auth(self) -> tuple[str, str]:
        return self.auth_user, self.auth_token

    def get(self, path: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}{path}", auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{path}",
            auth=self.auth,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def put(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.put(
            f"{self.base_url}{path}",
            auth=self.auth,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


def _preflight_admin_permissions(client: ZendeskClient) -> None:
    me = client.get("/api/v2/users/me.json").get("user", {})
    role = str(me.get("role") or "").strip().lower()
    email = str(me.get("email") or "unknown")
    user_id = me.get("id")

    if role != "admin":
        raise RuntimeError(
            "Zendesk preflight failed: trigger management requires an admin account. "
            f"Current principal: {email} (id={user_id}, role={role or 'unknown'})."
        )

    print(f"[OK] Zendesk preflight: admin principal verified ({email}).")


def _build_payload(event_name: str) -> str:
    payload = {
        "source": "zendesk",
        "event_type": event_name,
        "timestamp": "{{ticket.updated_at}}",
        "ticket": {
            "id": "{{ticket.id}}",
            "subject": "{{ticket.title}}",
            "status": "{{ticket.status}}",
            "priority": "{{ticket.priority}}",
            "created_at": "{{ticket.created_at}}",
            "updated_at": "{{ticket.updated_at}}",
            "requester": {
                "name": "{{ticket.requester.name}}",
                "email": "{{ticket.requester.email}}",
            },
            "assignee": {
                "name": "{{ticket.assignee.name}}",
                "email": "{{ticket.assignee.email}}",
            },
            "latest_comment": "{{ticket.latest_comment}}",
            "tags": "{{ticket.tags}}",
        },
    }
    return json.dumps(payload, indent=2)


def _trigger_specs(webhook_id: str) -> List[Dict[str, Any]]:
    return [
        {
            "title": "CT | Webhook | Ticket Created",
            "active": True,
            "conditions": {
                "all": [
                    {"field": "update_type", "operator": "is", "value": "Create"},
                ],
                "any": [],
            },
            "actions": [
                {
                    "field": "notification_webhook",
                    "value": [webhook_id, _build_payload("ticket_created")],
                }
            ],
        },
        {
            "title": "CT | Webhook | Public Comment Added",
            "active": True,
            "conditions": {
                "all": [
                    {"field": "update_type", "operator": "is", "value": "Change"},
                    {"field": "comment_is_public", "operator": "is", "value": True},
                ],
                "any": [],
            },
            "actions": [
                {
                    "field": "notification_webhook",
                    "value": [webhook_id, _build_payload("public_comment_added")],
                }
            ],
        },
        {
            "title": "CT | Webhook | Ticket Status Changed",
            "active": True,
            "conditions": {
                "all": [
                    {"field": "update_type", "operator": "is", "value": "Change"},
                    {"field": "status", "operator": "changed", "value": None},
                ],
                "any": [],
            },
            "actions": [
                {
                    "field": "notification_webhook",
                    "value": [webhook_id, _build_payload("ticket_status_changed")],
                }
            ],
        },
    ]


def _find_webhook_id(client: ZendeskClient, preferred_url: str) -> str:
    webhooks = client.get("/api/v2/webhooks").get("webhooks", [])
    if not webhooks:
        raise RuntimeError("No Zendesk webhooks found. Create webhook endpoint first.")

    preferred = preferred_url.strip().rstrip("/") if preferred_url else ""
    chosen: Optional[Dict[str, Any]] = None
    for webhook in webhooks:
        endpoint = webhook.get("endpoint")
        endpoint_url = endpoint if isinstance(endpoint, str) else (endpoint or {}).get("url")
        if str(endpoint_url or "").rstrip("/") == preferred:
            chosen = webhook
            break

    if not chosen:
        available = []
        for webhook in webhooks:
            endpoint = webhook.get("endpoint")
            endpoint_url = endpoint if isinstance(endpoint, str) else (endpoint or {}).get("url")
            available.append(str(endpoint_url or ""))
        raise RuntimeError(
            "Exact webhook URL not found in Zendesk. "
            f"Expected: {preferred} | Available: {available}"
        )

    webhook_id = chosen.get("id")
    if not webhook_id:
        raise RuntimeError("Webhook found but missing id.")

    endpoint = chosen.get("endpoint")
    endpoint_url = endpoint if isinstance(endpoint, str) else (endpoint or {}).get("url")
    print(f"[INFO] Using webhook id={webhook_id} name={chosen.get('name')} url={endpoint_url}")
    return str(webhook_id)


def _upsert_trigger(client: ZendeskClient, spec: Dict[str, Any]) -> str:
    triggers = client.get("/api/v2/triggers").get("triggers", [])
    existing = next((t for t in triggers if t.get("title") == spec["title"]), None)

    if existing:
        trigger_id = existing["id"]
        client.put(f"/api/v2/triggers/{trigger_id}", {"trigger": spec})
        print(f"[UPDATED] {spec['title']} ({trigger_id})")
        return str(trigger_id)

    created = client.post("/api/v2/triggers", {"trigger": spec}).get("trigger", {})
    trigger_id = created.get("id")
    print(f"[CREATED] {spec['title']} ({trigger_id})")
    return str(trigger_id)


def _disable_legacy_sync_trigger(client: ZendeskClient, title: str) -> None:
    triggers = client.get("/api/v2/triggers").get("triggers", [])
    legacy = next((t for t in triggers if t.get("title") == title), None)
    if not legacy:
        print(f"[INFO] Legacy trigger not found: {title}")
        return

    if not legacy.get("active", True):
        print(f"[OK] Legacy trigger already inactive: {title}")
        return

    legacy_payload = {
        "title": legacy.get("title"),
        "active": False,
        "conditions": legacy.get("conditions") or {"all": [], "any": []},
        "actions": legacy.get("actions") or [],
    }
    client.put(f"/api/v2/triggers/{legacy['id']}", {"trigger": legacy_payload})
    print(f"[DISABLED] Legacy trigger: {title} ({legacy['id']})")


def main() -> None:
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    base_url = (os.getenv("ZENDESK_BASE_URL") or "").strip().rstrip("/")
    email = (os.getenv("ZENDESK_ADMIN_EMAIL") or os.getenv("ZENDESK_EMAIL") or "").strip()
    api_token = (os.getenv("ZENDESK_ADMIN_API_TOKEN") or os.getenv("ZENDESK_API_TOKEN") or "").strip()

    if not base_url or not email or not api_token:
        raise RuntimeError(
            "Missing Zendesk env config: ZENDESK_BASE_URL and admin-capable credentials. "
            "Use ZENDESK_ADMIN_EMAIL + ZENDESK_ADMIN_API_TOKEN (preferred) "
            "or ZENDESK_EMAIL + ZENDESK_API_TOKEN."
        )

    preferred_webhook_url = (
        os.getenv("ZENDESK_WEBHOOK_TARGET_URL")
        or "https://api.careertrojan.com/api/webhooks/v1/zendesk"
    )

    client = ZendeskClient(
        base_url=base_url,
        auth_user=f"{email}/token",
        auth_token=api_token,
    )

    _preflight_admin_permissions(client)

    webhook_id = _find_webhook_id(client, preferred_webhook_url)

    for spec in _trigger_specs(webhook_id):
        _upsert_trigger(client, spec)

    _disable_legacy_sync_trigger(client, "CareerTrojan – Ticket Sync")
    print("[OK] Zendesk trigger upsert complete.")


if __name__ == "__main__":
    main()
