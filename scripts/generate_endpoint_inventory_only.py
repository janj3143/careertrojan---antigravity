from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from services.backend_api.main import app


def main() -> None:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d")
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    md_path = reports / f"FULL_ENDPOINT_INVENTORY_{stamp}.md"
    json_path = reports / f"FULL_ENDPOINT_INVENTORY_{stamp}.json"

    spec = app.openapi()
    paths = spec.get("paths", {})

    rows = []
    for path, methods in sorted(paths.items()):
        for method in sorted(methods.keys()):
            method_u = method.upper()
            if method_u in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                rows.append({"method": method_u, "path": path})

    json_path.write_text(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "total_endpoints": len(rows),
                "endpoints": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lines = [
        f"# Full Endpoint Inventory — {stamp}",
        "",
        f"Generated: `{now.isoformat()}`",
        "",
        f"- Total endpoints: **{len(rows)}**",
        "",
        "| Method | Path |",
        "|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['method']} | {row['path']} |")

    lines.append("")
    lines.append(f"JSON: `{json_path.as_posix()}`")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(str(md_path))
    print(str(json_path))


if __name__ == "__main__":
    main()
