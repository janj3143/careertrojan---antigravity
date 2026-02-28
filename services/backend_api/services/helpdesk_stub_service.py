from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _sign_hs256(message: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), message, digestmod=hashlib.sha256).digest()
    return _b64url(sig)


def _build_jwt(payload: Dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    msg = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig_b64 = _sign_hs256(msg, secret)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def get_helpdesk_config() -> Dict[str, Any]:
    provider = os.getenv("HELPDESK_PROVIDER", "stub").strip().lower()
    widget_enabled = _as_bool(os.getenv("HELPDESK_WIDGET_ENABLED"), default=True)
    sso_enabled = _as_bool(os.getenv("HELPDESK_SSO_ENABLED"), default=False)
    script_url = os.getenv("HELPDESK_WIDGET_SCRIPT_URL", "")
    support_base_url = os.getenv("HELPDESK_BASE_URL", "https://support.careertrojan.com")

    zendesk_subdomain = os.getenv("ZENDESK_SUBDOMAIN", "")
    zendesk_base_url = os.getenv("ZENDESK_BASE_URL", "")
    if not zendesk_base_url and zendesk_subdomain:
        zendesk_base_url = f"https://{zendesk_subdomain}.zendesk.com"

    if provider == "zendesk" and not script_url:
        # Web widget snippet endpoint can vary by Zendesk plan; keep overridable via env
        script_url = os.getenv("ZENDESK_WIDGET_SCRIPT_URL", "https://static.zdassets.com/ekr/snippet.js")

    return {
        "provider": provider,
        "mode": "zendesk" if provider == "zendesk" else "stub",
        "widget_enabled": widget_enabled,
        "sso_enabled": sso_enabled,
        "script_url": script_url,
        "support_base_url": zendesk_base_url or support_base_url,
        "queue_url": os.getenv("HELPDESK_QUEUE_URL", "https://support.careertrojan.com/agent/queue"),
        "macros_url": os.getenv("HELPDESK_MACROS_URL", "https://support.careertrojan.com/agent/macros"),
        "zendesk": {
            "subdomain": zendesk_subdomain,
            "base_url": zendesk_base_url,
            "jwt_claim_email": os.getenv("ZENDESK_JWT_EMAIL_CLAIM", "email"),
            "jwt_claim_name": os.getenv("ZENDESK_JWT_NAME_CLAIM", "name"),
            "external_id_claim": os.getenv("ZENDESK_JWT_EXTERNAL_ID_CLAIM", "external_id"),
        },
    }


def get_helpdesk_readiness() -> Dict[str, Any]:
    cfg = get_helpdesk_config()
    provider = cfg.get("provider", "stub")

    if provider != "zendesk":
        return {
            "provider": provider,
            "ready": True,
            "mode": cfg.get("mode", "stub"),
            "missing": [],
            "notes": ["Zendesk checks are skipped because provider is not set to zendesk."],
        }

    missing = []
    if not os.getenv("ZENDESK_SHARED_SECRET"):
        missing.append("ZENDESK_SHARED_SECRET")
    if not (os.getenv("ZENDESK_SUBDOMAIN") or os.getenv("ZENDESK_BASE_URL")):
        missing.append("ZENDESK_SUBDOMAIN or ZENDESK_BASE_URL")
    if not (os.getenv("HELPDESK_WIDGET_SCRIPT_URL") or os.getenv("ZENDESK_WIDGET_SCRIPT_URL")):
        missing.append("HELPDESK_WIDGET_SCRIPT_URL or ZENDESK_WIDGET_SCRIPT_URL")

    return {
        "provider": provider,
        "ready": len(missing) == 0,
        "mode": cfg.get("mode", "zendesk"),
        "missing": missing,
        "notes": [
            "Set HELPDESK_PROVIDER=zendesk for production Zendesk wiring.",
            "Use /api/support/v1/providers and /api/support/v1/readiness to validate deploy-time configuration.",
        ],
    }


def build_stub_sso_token(subject: str, email: str = "", ttl_seconds: int = 3600) -> str:
    issued_at = int(time.time())
    expires_at = issued_at + max(60, ttl_seconds)

    payload = {
        "iss": "careertrojan-backend",
        "sub": subject,
        "email": email,
        "provider": "stub",
        "iat": issued_at,
        "exp": expires_at,
    }

    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    secret = os.getenv("HELPDESK_STUB_SECRET", "careertrojan-helpdesk-stub-secret").encode("utf-8")
    signature = hmac.new(secret, raw, digestmod=hashlib.sha256).digest()

    return _b64url(raw) + "." + _b64url(signature)


def build_zendesk_sso_token(
    subject: str,
    email: str = "",
    name: str = "",
    ttl_seconds: int = 3600,
) -> str:
    issued_at = int(time.time())
    expires_at = issued_at + max(60, ttl_seconds)

    secret = os.getenv("ZENDESK_SHARED_SECRET", "")
    if not secret:
        raise RuntimeError("ZENDESK_SHARED_SECRET is required for zendesk SSO token mode")

    email_claim = os.getenv("ZENDESK_JWT_EMAIL_CLAIM", "email")
    name_claim = os.getenv("ZENDESK_JWT_NAME_CLAIM", "name")
    external_id_claim = os.getenv("ZENDESK_JWT_EXTERNAL_ID_CLAIM", "external_id")

    payload: Dict[str, Any] = {
        "iat": issued_at,
        "exp": expires_at,
        external_id_claim: subject,
    }
    if email:
        payload[email_claim] = email
    if name:
        payload[name_claim] = name

    return _build_jwt(payload, secret)


def build_helpdesk_sso_token(subject: str, email: str = "", name: str = "", ttl_seconds: int = 3600) -> str:
    cfg = get_helpdesk_config()
    if cfg["provider"] == "zendesk":
        return build_zendesk_sso_token(subject=subject, email=email, name=name, ttl_seconds=ttl_seconds)
    return build_stub_sso_token(subject=subject, email=email, ttl_seconds=ttl_seconds)


def build_widget_bootstrap(portal: str, user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = get_helpdesk_config()
    uid = str((user or {}).get("id") or "anonymous")
    email = str((user or {}).get("email") or "")
    name = str((user or {}).get("name") or "")
    token = build_helpdesk_sso_token(subject=uid, email=email, name=name)

    notes = ["Helpdesk widget wiring is active."]
    if config["mode"] == "stub":
        notes.append("This is a non-production helpdesk wiring stub.")
        notes.append("Set HELPDESK_PROVIDER=zendesk and Zendesk env vars to enable production mode.")
    else:
        notes.append("Zendesk mode enabled. Verify ZENDESK_SHARED_SECRET and widget snippet settings.")

    return {
        "portal": portal,
        "config": config,
        "session": {
            "token": token,
            "user": {
                "id": uid,
                "email": email,
            },
        },
        "notes": notes,
    }
