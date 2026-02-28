from __future__ import annotations

import json
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
ROUTERS_DIR = ROOT / "services" / "backend_api" / "routers"
APPS_DIR = ROOT / "apps"
REPORTS_DIR = ROOT / "reports"

ROUTE_DECORATOR_RE = re.compile(r"@router\.(get|post|put|delete|patch)\(\s*[\"']([^\"']*)[\"']")
PREFIX_RE = re.compile(r"APIRouter\((?:.|\n)*?prefix\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)
APP_ROUTE_RE = re.compile(r"Route\s+path=\"([^\"]+)\"")
FETCH_LITERAL_RE = re.compile(r"fetch\(\s*[\"']([^\"']+)[\"']")
API_PATH_IN_TEXT_RE = re.compile(r"(/api/[A-Za-z0-9_\-/{}:.]+|/mentor/[A-Za-z0-9_\-/{}:.]+|/user/[A-Za-z0-9_\-/{}:.]+)")


def normalize_path(value: str) -> str:
    v = value.strip()
    if not v:
        return v
    if not v.startswith("/"):
        v = "/" + v
    v = re.sub(r"/+", "/", v)
    return v


def collect_backend_endpoints() -> list[dict]:
    endpoints: list[dict] = []
    for file in sorted(ROUTERS_DIR.glob("*.py")):
        if file.name == "__init__.py":
            continue
        text = file.read_text(encoding="utf-8", errors="ignore")
        prefix_match = PREFIX_RE.search(text)
        prefix = prefix_match.group(1) if prefix_match else ""
        prefix = normalize_path(prefix)

        for method, route in ROUTE_DECORATOR_RE.findall(text):
            full = normalize_path(prefix.rstrip("/") + "/" + route.lstrip("/"))
            endpoints.append(
                {
                    "method": method.upper(),
                    "prefix": prefix,
                    "route": normalize_path(route) if route else "/",
                    "path": full,
                    "router_file": str(file.relative_to(ROOT)).replace("\\", "/"),
                }
            )
    return endpoints


def collect_portal_routes() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for portal in ["admin", "user", "mentor"]:
        app = APPS_DIR / portal / "src" / "App.tsx"
        text = app.read_text(encoding="utf-8", errors="ignore") if app.exists() else ""
        result[portal] = sorted({normalize_path(p) for p in APP_ROUTE_RE.findall(text)})
    return result


def collect_frontend_api_calls() -> dict[str, list[dict]]:
    calls: dict[str, list[dict]] = defaultdict(list)
    for portal in ["admin", "user", "mentor"]:
        portal_root = APPS_DIR / portal / "src"
        for file in portal_root.rglob("*.tsx"):
            text = file.read_text(encoding="utf-8", errors="ignore")
            rel = str(file.relative_to(ROOT)).replace("\\", "/")

            for literal in FETCH_LITERAL_RE.findall(text):
                if literal.startswith("http://") or literal.startswith("https://"):
                    continue
                if "/api/" in literal or literal.startswith("/mentor/") or literal.startswith("/user/"):
                    calls[portal].append({"path": normalize_path(literal), "source": rel, "kind": "fetch_literal"})

            for hit in API_PATH_IN_TEXT_RE.findall(text):
                if "/api/" in hit or hit.startswith("/mentor/") or hit.startswith("/user/"):
                    calls[portal].append({"path": normalize_path(hit), "source": rel, "kind": "path_ref"})

        uniq = {(c["path"], c["source"], c["kind"]) for c in calls[portal]}
        calls[portal] = [
            {"path": p, "source": s, "kind": k}
            for (p, s, k) in sorted(uniq)
        ]
    return calls


def coverage_analysis(backend_endpoints: list[dict], frontend_calls: dict[str, list[dict]]) -> dict:
    backend_paths = sorted({e["path"] for e in backend_endpoints})

    portal_cov = {}
    for portal, calls in frontend_calls.items():
        call_paths = sorted({c["path"] for c in calls if c["path"].startswith("/api/")})
        matched = []
        unmatched = []
        for cp in call_paths:
            if cp in backend_paths:
                matched.append(cp)
            else:
                rough = [bp for bp in backend_paths if bp.startswith(cp.rstrip("/")) or cp.startswith(bp.rstrip("/"))]
                if rough:
                    matched.append(cp)
                else:
                    unmatched.append(cp)
        portal_cov[portal] = {
            "api_call_paths": call_paths,
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "unmatched_paths": unmatched,
        }

    return {
        "backend_unique_path_count": len(backend_paths),
        "backend_paths": backend_paths,
        "portal_coverage": portal_cov,
    }


def write_reports(payload: dict) -> tuple[Path, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "ENDPOINT_TOPOLOGY_MAP.json"
    md_path = REPORTS_DIR / "ENDPOINT_TOPOLOGY_MAP.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# Endpoint Topology Map")
    lines.append("")
    lines.append(f"Generated from: `{ROOT}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Backend unique API paths: {payload['coverage']['backend_unique_path_count']}")
    for portal in ["admin", "user", "mentor"]:
        cov = payload["coverage"]["portal_coverage"].get(portal, {})
        route_count = len(payload["portal_routes"].get(portal, []))
        call_count = len(cov.get("api_call_paths", []))
        lines.append(
            f"- {portal.title()}: routes={route_count}, api_call_paths={call_count}, unmatched={cov.get('unmatched_count', 0)}"
        )

    lines.append("")
    lines.append("## Portal Route Surfaces")
    for portal in ["admin", "user", "mentor"]:
        lines.append(f"### {portal.title()}")
        for route in payload["portal_routes"].get(portal, []):
            lines.append(f"- `{route}`")
        lines.append("")

    lines.append("## Frontend API Call Mismatches")
    for portal in ["admin", "user", "mentor"]:
        cov = payload["coverage"]["portal_coverage"].get(portal, {})
        lines.append(f"### {portal.title()}")
        unmatched = cov.get("unmatched_paths", [])
        if not unmatched:
            lines.append("- None detected")
        else:
            for p in unmatched:
                lines.append(f"- `{p}`")
        lines.append("")

    lines.append("## Backend Router Inventory")
    by_file: dict[str, list[str]] = defaultdict(list)
    for ep in payload["backend_endpoints"]:
        by_file[ep["router_file"]].append(f"{ep['method']} {ep['path']}")
    for router_file in sorted(by_file):
        lines.append(f"### `{router_file}`")
        for entry in sorted(set(by_file[router_file])):
            lines.append(f"- `{entry}`")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    backend_endpoints = collect_backend_endpoints()
    portal_routes = collect_portal_routes()
    frontend_calls = collect_frontend_api_calls()
    coverage = coverage_analysis(backend_endpoints, frontend_calls)

    payload = {
        "generated_at": "2026-02-24",
        "backend_endpoints": backend_endpoints,
        "portal_routes": portal_routes,
        "frontend_calls": frontend_calls,
        "coverage": coverage,
    }

    json_path, md_path = write_reports(payload)
    print(f"WROTE_JSON={json_path}")
    print(f"WROTE_MD={md_path}")
    print(f"BACKEND_UNIQUE_PATHS={coverage['backend_unique_path_count']}")
    for portal in ["admin", "user", "mentor"]:
        cov = coverage["portal_coverage"][portal]
        print(
            f"{portal.upper()}_ROUTES={len(portal_routes[portal])} {portal.upper()}_CALLS={len(cov['api_call_paths'])} {portal.upper()}_UNMATCHED={cov['unmatched_count']}"
        )


if __name__ == "__main__":
    main()
