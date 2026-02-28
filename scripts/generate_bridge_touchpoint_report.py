from __future__ import annotations

import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
TOPOLOGY_JSON = REPORTS / "ENDPOINT_TOPOLOGY_MAP.json"

TOKENS = [
    "portal_bridge",
    "shared_backend",
    "post_bridge_payload",
    "AdminFastAPIClient",
    "real_ai_connector",
]


def scan_touchpoints() -> dict[str, list[dict]]:
    findings: dict[str, list[dict]] = defaultdict(list)
    for file in ROOT.rglob("*.py"):
        rel = str(file.relative_to(ROOT)).replace("\\", "/")
        text = file.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            low = line.lower()
            for token in TOKENS:
                if token.lower() in low:
                    findings[token].append({"file": rel, "line": idx, "snippet": line.strip()[:180]})
    return findings


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    topology = json.loads(TOPOLOGY_JSON.read_text(encoding="utf-8")) if TOPOLOGY_JSON.exists() else {}

    coverage = topology.get("coverage", {}).get("portal_coverage", {})
    unmatched_admin = coverage.get("admin", {}).get("unmatched_paths", [])
    unmatched_user = coverage.get("user", {}).get("unmatched_paths", [])
    unmatched_mentor = coverage.get("mentor", {}).get("unmatched_paths", [])

    touches = scan_touchpoints()

    md = []
    md.append("# Endpoint Bridge Touchpoint Map")
    md.append("")
    md.append("## Coverage Mismatches From Topology")
    md.append(f"- Admin unmatched: {len(unmatched_admin)}")
    for p in unmatched_admin:
        md.append(f"  - `{p}`")
    md.append(f"- User unmatched: {len(unmatched_user)}")
    for p in unmatched_user:
        md.append(f"  - `{p}`")
    md.append(f"- Mentor unmatched: {len(unmatched_mentor)}")
    for p in unmatched_mentor:
        md.append(f"  - `{p}`")

    md.append("")
    md.append("## Bridge Touchpoint Inventory")
    for token in TOKENS:
        rows = touches.get(token, [])
        md.append(f"### `{token}` ({len(rows)} hits)")
        for row in rows[:80]:
            md.append(f"- `{row['file']}:{row['line']}` — {row['snippet']}")
        if len(rows) > 80:
            md.append(f"- ... {len(rows)-80} more")
        md.append("")

    md.append("## Immediate Remediation Focus")
    md.append("- Normalize mentor API calls to `/api/mentor/v1/*` and `/api/mentorship/v1/*`.")
    md.append("- Replace admin legacy calls under `/api/admin/*` with `/api/admin/v1/*` where missing.")
    md.append("- Validate taxonomy summary path usage against implemented taxonomy router paths.")
    md.append("- Keep bridge calls observable via `/api/mapping/v1/endpoints` and telemetry routes.")

    out_md = REPORTS / "ENDPOINT_BRIDGE_TOUCHPOINT_MAP.md"
    out_json = REPORTS / "ENDPOINT_BRIDGE_TOUCHPOINT_MAP.json"
    out_md.write_text("\n".join(md), encoding="utf-8")
    out_json.write_text(json.dumps(touches, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"WROTE_MD={out_md}")
    print(f"WROTE_JSON={out_json}")


if __name__ == "__main__":
    main()
