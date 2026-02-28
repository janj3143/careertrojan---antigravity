from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Dict, Optional

import requests


def _resolve_base_url() -> str:
    base_url = (os.getenv("ZENDESK_BASE_URL") or "").strip().rstrip("/")
    if base_url:
        return base_url

    subdomain = (os.getenv("ZENDESK_SUBDOMAIN") or "").strip()
    if subdomain:
        return f"https://{subdomain}.zendesk.com"

    raise RuntimeError("Zendesk is not configured: set ZENDESK_BASE_URL or ZENDESK_SUBDOMAIN")


def _resolve_auth() -> tuple[str, str]:
    email = (os.getenv("ZENDESK_EMAIL") or "").strip()
    api_token = (os.getenv("ZENDESK_API_TOKEN") or "").strip()

    if not email or not api_token:
        raise RuntimeError("Zendesk auth missing: set ZENDESK_EMAIL and ZENDESK_API_TOKEN")

    return f"{email}/token", api_token


def _ticket_tags(payload: Dict[str, Any]) -> list[str]:
    tags: list[str] = ["careertrojan", "support_bridge"]
    for key in ("portal", "category", "subscription_tier"):
        value = str(payload.get(key) or "").strip().lower()
        if value:
            tags.append(f"{key}:{value}")
    return tags


def _custom_fields(payload: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "user_id",
        "subscription_tier",
        "tokens_remaining",
        "portal",
        "request_id",
        "resume_version_id",
        "category",
    ]
    return {key: payload.get(key) for key in keys if payload.get(key) is not None}


def create_ticket(payload: Dict[str, Any]) -> Dict[str, Any]:
    base_url = _resolve_base_url()
    username, password = _resolve_auth()

    requester = {
        "name": str(payload.get("requester_name") or payload.get("requester_email") or "CareerTrojan User"),
        "email": str(payload.get("requester_email") or "support@careertrojan.com"),
    }

    comment_lines = [str(payload.get("description") or "").strip()]
    metadata = _custom_fields(payload)
    if metadata:
        comment_lines.append("\n\n---\nCareerTrojan Metadata:\n")
        for key, value in metadata.items():
            comment_lines.append(f"- {key}: {value}")

    ticket_body: Dict[str, Any] = {
        "ticket": {
            "subject": str(payload.get("subject") or "Support Request"),
            "comment": {"body": "\n".join(comment_lines).strip() or "No description provided."},
            "requester": requester,
            "tags": _ticket_tags(payload),
        }
    }

    priority = payload.get("priority")
    if priority:
        ticket_body["ticket"]["priority"] = str(priority)

    group_id = payload.get("group_id") or os.getenv("ZENDESK_DEFAULT_GROUP_ID")
    if group_id:
        ticket_body["ticket"]["group_id"] = int(group_id)

    form_id = payload.get("form_id") or os.getenv("ZENDESK_DEFAULT_FORM_ID")
    if form_id:
        ticket_body["ticket"]["ticket_form_id"] = int(form_id)

    response = requests.post(
        f"{base_url}/api/v2/tickets.json",
        json=ticket_body,
        auth=(username, password),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=20,
    )

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"Zendesk ticket create failed ({response.status_code}): {detail}")

    data = response.json().get("ticket", {})
    return {
        "zendesk_ticket_id": data.get("id"),
        "status": data.get("status"),
        "priority": data.get("priority"),
        "url": data.get("url"),
        "raw": data,
    }


def get_ticket(ticket_id: int) -> Dict[str, Any]:
    base_url = _resolve_base_url()
    username, password = _resolve_auth()

    response = requests.get(
        f"{base_url}/api/v2/tickets/{ticket_id}.json",
        auth=(username, password),
        headers={"Accept": "application/json"},
        timeout=20,
    )

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"Zendesk ticket fetch failed ({response.status_code}): {detail}")

    data = response.json().get("ticket", {})
    return {
        "zendesk_ticket_id": data.get("id"),
        "status": data.get("status"),
        "priority": data.get("priority"),
        "updated_at": data.get("updated_at"),
        "subject": data.get("subject"),
        "raw": data,
    }


def verify_webhook_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
    secret = (os.getenv("ZENDESK_WEBHOOK_SECRET") or os.getenv("ZENDESK_SHARED_SECRET") or "").strip()
    if not secret:
        return True

    if not signature_header:
        return False

    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    provided = signature_header.strip().lower().replace("sha256=", "")
    return hmac.compare_digest(digest, provided)
