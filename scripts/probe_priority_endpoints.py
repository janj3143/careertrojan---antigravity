from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from services.backend_api.main import app
from services.backend_api.utils import security


PRIORITY_ENDPOINTS = [
    ("GET", "/api/admin/v1/integrations/status", None),
    ("POST", "/api/admin/v1/integrations/sendgrid/configure", {"api_key": "SG.x"}),
    ("POST", "/api/admin/v1/integrations/klaviyo/configure", {"api_key": "KLV.x"}),
    ("POST", "/api/admin/v1/email/send_test", {"to": "probe@example.com", "provider": "sendgrid"}),
    ("POST", "/api/admin/v1/email/send_bulk", {"recipients": ["a@example.com", "b@example.com"], "provider": "klaviyo"}),
    ("GET", "/api/admin/v1/email/logs", None),
    ("GET", "/api/admin/v1/email/analytics", None),
    ("GET", "/api/admin/integrations/status", None),
    ("POST", "/api/admin/integrations/sendgrid/configure", {"api_key": "SG.x"}),
    ("POST", "/api/admin/integrations/klaviyo/configure", {"api_key": "KLV.x"}),
    ("POST", "/api/admin/email/send_test", {"to": "probe@example.com"}),
    ("POST", "/api/admin/email/send_bulk", {"recipients": ["a@example.com"]}),
    ("GET", "/api/ai-data/v1/emails/summary", None),
    ("GET", "/api/ai-data/v1/emails/providers/sendgrid", None),
    ("GET", "/api/ai-data/v1/emails/providers/klaviyo", None),
    ("GET", "/api/ai-data/v1/emails/providers/sendgrid/guarded-payload", None),
    ("GET", "/api/ai-data/v1/emails/tracking/summary", None),
    ("GET", "/api/admin/v1/ai/content/status", None),
    ("POST", "/api/admin/v1/ai/content/run", {}),
    ("GET", "/api/admin/v1/ai/content/jobs", None),
    ("GET", "/api/mentorship/v1/links/mentor/sample", None),
    ("GET", "/api/mentorship/v1/links/user/sample", None),
    ("GET", "/api/mentorship/v1/notes/sample", None),
    ("GET", "/api/mentorship/v1/invoices/mentor/sample", None),
    ("GET", "/api/mentorship/v1/applications/pending", None),
]


def classify(code: int) -> str:
    if 200 <= code < 300:
        return "ok"
    if code in (401, 403):
        return "auth_required"
    if code == 404:
        return "missing"
    if code == 422:
        return "payload_or_param_required"
    if code >= 500:
        return "server_error"
    return "other"


def main() -> None:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d")
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    md_path = reports / f"PRIORITY_ENDPOINT_PROBE_{stamp}.md"
    json_path = reports / f"PRIORITY_ENDPOINT_PROBE_{stamp}.json"

    client = TestClient(app)
    token = security.create_access_token(data={"sub": "probe-admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    rows = []
    for method, path, payload in PRIORITY_ENDPOINTS:
        try:
            if method == "GET":
                r = client.get(path, headers=headers)
            else:
                r = client.post(path, headers=headers, json=payload or {})
            code = r.status_code
            detail = None
        except BaseException as exc:
            code = 599
            detail = str(exc)

        rows.append(
            {
                "method": method,
                "path": path,
                "status_code": code,
                "classification": classify(code),
                "error": detail,
            }
        )

    problems = [r for r in rows if r["classification"] in {"missing", "server_error", "other"}]

    json_path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "results": rows,
                "problems": problems,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        f"# Priority Endpoint Probe — {stamp}",
        "",
        f"Generated: `{now.isoformat()}`",
        "",
        "| Method | Path | Status | Classification |",
        "|---|---|---:|---|",
    ]
    for r in rows:
        lines.append(f"| {r['method']} | {r['path']} | {r['status_code']} | {r['classification']} |")

    lines.extend(["", "## Problem APIs", ""])
    if not problems:
        lines.append("- None")
    else:
        for p in problems:
            lines.append(f"- {p['method']} {p['path']} -> {p['status_code']} ({p['classification']})")

    lines.append("")
    lines.append(f"JSON: `{json_path.as_posix()}`")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(str(md_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
