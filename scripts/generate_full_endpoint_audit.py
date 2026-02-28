from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from services.backend_api.main import app
from services.backend_api.utils import security


SKIP_PATH_FRAGMENTS = {
    "/api/ai-data/v1/normalized",
    "/api/ai-data/v1/metadata",
}


def _classify_status(code: int) -> str:
    if 200 <= code < 300:
        return "ok"
    if code in (401, 403, 422):
        return "exists_requires_auth_or_payload"
    if code in (404, 405):
        return "missing_or_wrong_method"
    return "error"


def main() -> None:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d")

    root = Path(__file__).resolve().parents[1]
    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / f"FULL_ENDPOINT_AUDIT_{stamp}.json"
    md_path = report_dir / f"FULL_ENDPOINT_AUDIT_{stamp}.md"

    client = TestClient(app)
    token = security.create_access_token(data={"sub": "endpoint-audit-admin", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    route_rows: list[dict] = []

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        name = getattr(route, "name", "")
        if not path or not methods:
            continue
        if path in ("/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"):
            continue
        if any(fragment in path for fragment in SKIP_PATH_FRAGMENTS):
            route_rows.append(
                {
                    "method": "SKIP",
                    "path": path,
                    "name": name,
                    "status_code": 0,
                    "classification": "skipped_heavy",
                    "error": "Skipped due to known heavy endpoint",
                }
            )
            continue

        allowed = sorted([m for m in methods if m not in {"HEAD", "OPTIONS"}])
        for method in allowed:
            payload = {}
            if method in {"POST", "PUT", "PATCH"}:
                payload = {
                    "api_key": "x",
                    "to": "audit@example.com",
                    "recipients": ["audit@example.com", "audit2@example.com"],
                    "subject": "audit",
                    "body": "audit",
                    "provider": "sendgrid",
                }

            try:
                if method == "GET":
                    response = client.get(path, headers=headers)
                elif method == "POST":
                    response = client.post(path, headers=headers, json=payload)
                elif method == "PUT":
                    response = client.put(path, headers=headers, json=payload)
                elif method == "PATCH":
                    response = client.patch(path, headers=headers, json=payload)
                elif method == "DELETE":
                    response = client.delete(path, headers=headers)
                else:
                    continue
                status_code = response.status_code
            except BaseException as exc:
                status_code = 599
                response = None
                error = str(exc)
            else:
                error = None

            route_rows.append(
                {
                    "method": method,
                    "path": path,
                    "name": name,
                    "status_code": status_code,
                    "classification": _classify_status(status_code),
                    "error": error,
                }
            )

    by_class = defaultdict(int)
    for row in route_rows:
        by_class[row["classification"]] += 1

    failures = [
        r
        for r in route_rows
        if r["classification"] in {"missing_or_wrong_method", "error", "skipped_heavy"}
    ]

    result = {
        "generated_at": now.isoformat(),
        "total_probed": len(route_rows),
        "summary": dict(by_class),
        "failures": failures,
        "routes": route_rows,
    }

    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append(f"# Full Endpoint Audit — {stamp}")
    lines.append("")
    lines.append(f"Generated: `{now.isoformat()}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total probed: **{len(route_rows)}**")
    for k in sorted(by_class.keys()):
        lines.append(f"- {k}: **{by_class[k]}**")

    lines.append("")
    lines.append("## Endpoints With Problems")
    lines.append("")
    if not failures:
        lines.append("- None")
    else:
        lines.append("| Method | Path | Status | Classification |")
        lines.append("|---|---|---:|---|")
        for row in failures:
            lines.append(
                f"| {row['method']} | {row['path']} | {row['status_code']} | {row['classification']} |"
            )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `exists_requires_auth_or_payload` means the route exists but needs proper auth and/or domain-specific payload.")
    lines.append("- `missing_or_wrong_method` is the main breakage signal for route availability mismatches.")
    lines.append("")
    lines.append(f"JSON output: `{json_path.as_posix()}`")

    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json_path)
    print(md_path)


if __name__ == "__main__":
    main()
