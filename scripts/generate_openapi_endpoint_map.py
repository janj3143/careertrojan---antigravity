from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from services.backend_api.main import app
from services.backend_api.utils import security

SKIP_HEAVY = {
    "/api/ai-data/v1/normalized",
    "/api/ai-data/v1/metadata",
    "/api/ai-data/v1/email_extracted",
    "/api/ai-data/v1/parsed_resumes",
    "/api/ai-data/v1/job_descriptions",
    "/api/ai-data/v1/job_titles",
    "/api/ai-data/v1/locations",
}

PROBE_PREFIXES = (
    "/api/admin/v1/",
    "/api/ai-data/v1/emails",
    "/api/shared/v1/health",
    "/api/mentorship/v1/",
)

PARAM_RE = re.compile(r"\{[^}]+\}")


def fill_path(path: str) -> str:
    return PARAM_RE.sub("sample", path)


def classify(code: int) -> str:
    if 200 <= code < 300:
        return "ok"
    if code in (401, 403, 422):
        return "exists_requires_auth_or_payload"
    if code in (404, 405):
        return "missing_or_wrong_method"
    if code == 0:
        return "skipped_heavy"
    if code == -1:
        return "mapped_not_probed"
    return "error"


def main() -> None:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d")

    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    md_path = reports / f"FULL_ENDPOINT_MAP_{stamp}.md"
    json_path = reports / f"FULL_ENDPOINT_MAP_{stamp}.json"

    spec = app.openapi()
    paths = spec.get("paths", {})

    token = security.create_access_token(data={"sub": "endpoint-map-admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    client = TestClient(app)

    rows = []
    for path, methods in sorted(paths.items()):
        for method in sorted(methods.keys()):
            method_u = method.upper()
            if method_u not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue

            call_path = fill_path(path)
            should_probe = path.startswith(PROBE_PREFIXES)
            if path in SKIP_HEAVY:
                status = 0
                err = "Skipped heavy endpoint"
            elif not should_probe:
                status = -1
                err = "Mapped from OpenAPI; not included in targeted probe scope"
            else:
                payload = {
                    "api_key": "x",
                    "to": "probe@example.com",
                    "recipients": ["probe@example.com", "probe2@example.com"],
                    "subject": "probe",
                    "body": "probe",
                    "provider": "sendgrid",
                }
                try:
                    if method_u == "GET":
                        r = client.get(call_path, headers=headers)
                    elif method_u == "POST":
                        r = client.post(call_path, headers=headers, json=payload)
                    elif method_u == "PUT":
                        r = client.put(call_path, headers=headers, json=payload)
                    elif method_u == "PATCH":
                        r = client.patch(call_path, headers=headers, json=payload)
                    else:
                        r = client.delete(call_path, headers=headers)
                    status = r.status_code
                    err = None
                except BaseException as exc:
                    status = 599
                    err = str(exc)

            rows.append(
                {
                    "method": method_u,
                    "path": path,
                    "probe_path": call_path,
                    "status_code": status,
                    "classification": classify(status),
                    "error": err,
                }
            )

    counts = Counter(r["classification"] for r in rows)
    problems = [r for r in rows if r["classification"] in {"missing_or_wrong_method", "error", "skipped_heavy"}]

    json_path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "total_endpoints": len(rows),
                "summary": dict(counts),
                "problems": problems,
                "endpoints": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = []
    lines.append(f"# Full Endpoint Map & Probe — {stamp}")
    lines.append("")
    lines.append(f"Generated: `{now.isoformat()}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total endpoints: **{len(rows)}**")
    for key in sorted(counts):
        lines.append(f"- {key}: **{counts[key]}**")

    lines.append("")
    lines.append("## API Problems To Fix/Test")
    lines.append("")
    if not problems:
        lines.append("- None")
    else:
        lines.append("| Method | Path | Probe Status | Classification |")
        lines.append("|---|---|---:|---|")
        for p in problems:
            lines.append(f"| {p['method']} | {p['path']} | {p['status_code']} | {p['classification']} |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `422` is treated as route existing with payload/schema mismatch during generic probe.")
    lines.append("- `401/403` is treated as route existing but auth-gated.")
    lines.append("- `404/405` indicates likely path/method mismatch or removed route.")
    lines.append("")
    lines.append(f"JSON: `{json_path.as_posix()}`")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(str(md_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
