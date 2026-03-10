from __future__ import annotations

import inspect
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from fastapi.params import Depends as DependsParam
from fastapi.params import Header as HeaderParam
from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.backend_api.main import app


REPORTS_DIR = ROOT / "reports"
VERSION_SEGMENT_RE = re.compile(r"^v\d+$", re.IGNORECASE)
INVENTORY_GLOB = "FULL_ENDPOINT_INVENTORY_*.json"


@dataclass
class RouteRow:
    method: str
    path: str
    name: str
    tags: List[str]
    prefix_bucket: str
    semantic_path: str
    auth_signals: List[str]
    required_headers: List[str]
    source_function: str


def _iter_api_routes() -> Iterable[APIRoute]:
    for route in app.routes:
        if isinstance(route, APIRoute):
            yield route


def _route_methods(route: APIRoute) -> List[str]:
    methods = sorted(route.methods or [])
    return [method for method in methods if method not in {"HEAD", "OPTIONS"}]


def _prefix_bucket(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if not parts:
        return "/"
    if len(parts) == 1:
        return f"/{parts[0]}"
    return f"/{parts[0]}/{parts[1]}"


def _semantic_path(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    filtered = [part for part in parts if part.lower() != "api" and not VERSION_SEGMENT_RE.match(part)]
    return "/" + "/".join(filtered)


def _dependency_call_name(dep: Any) -> Optional[str]:
    call = getattr(dep, "call", None)
    if call is None:
        return None
    return getattr(call, "__name__", None) or str(call)


def _auth_signals(route: APIRoute) -> List[str]:
    signals: Set[str] = set()

    for dep in getattr(route.dependant, "dependencies", []):
        dep_name = (_dependency_call_name(dep) or "").lower()
        if not dep_name:
            continue
        if "require_admin" in dep_name:
            signals.add("admin_dependency")
        if "get_current_user" in dep_name:
            signals.add("user_dependency")
        if "oauth2" in dep_name or "security" in dep_name:
            signals.add("token_dependency")

    endpoint_name = f"{route.endpoint.__module__}.{route.endpoint.__name__}".lower()
    if "auth" in endpoint_name and route.path.startswith("/api/auth"):
        signals.add("auth_router")
    if route.path.startswith("/api/admin"):
        signals.add("admin_path")
    if route.path.startswith("/api/user"):
        signals.add("user_path")

    return sorted(signals)


def _required_headers(route: APIRoute, auth_signals: List[str]) -> List[str]:
    headers: Set[str] = set()

    for param in route.dependant.header_params:
        alias = getattr(param, "alias", None)
        name = getattr(param, "name", None)
        header_name = alias or name
        if header_name:
            headers.add(str(header_name))

    sig = inspect.signature(route.endpoint)
    for _, parameter in sig.parameters.items():
        default = parameter.default
        if isinstance(default, HeaderParam):
            alias = getattr(default, "alias", None)
            headers.add(alias or parameter.name)
        if isinstance(default, DependsParam):
            dependency = getattr(default, "dependency", None)
            dep_name = getattr(dependency, "__name__", "").lower() if dependency else ""
            if "oauth2" in dep_name:
                headers.add("Authorization")

    if route.path.startswith("/api/webhooks"):
        if "zendesk" in route.path and not any("zendesk" in h.lower() for h in headers):
            headers.add("x-zendesk-webhook-signature")
        if "stripe" in route.path and not any("stripe" in h.lower() for h in headers):
            headers.add("stripe-signature")

    needs_auth_header = any(
        signal in auth_signals for signal in ("admin_dependency", "user_dependency", "token_dependency")
    )
    if needs_auth_header and not route.path.startswith("/api/auth/"):
        headers.add("Authorization")

    return sorted(headers, key=lambda value: value.lower())


def _collect_rows() -> List[RouteRow]:
    rows: List[RouteRow] = []
    for route in _iter_api_routes():
        methods = _route_methods(route)
        if not methods:
            continue

        auth_signals = _auth_signals(route)
        required_headers = _required_headers(route, auth_signals)
        source_function = f"{route.endpoint.__module__}.{route.endpoint.__name__}"

        for method in methods:
            rows.append(
                RouteRow(
                    method=method,
                    path=route.path,
                    name=route.name,
                    tags=sorted(route.tags or []),
                    prefix_bucket=_prefix_bucket(route.path),
                    semantic_path=_semantic_path(route.path),
                    auth_signals=auth_signals,
                    required_headers=required_headers,
                    source_function=source_function,
                )
            )

    rows.sort(key=lambda item: (item.path, item.method))
    return rows


def _latest_inventory() -> Optional[Path]:
    candidates = sorted(REPORTS_DIR.glob(INVENTORY_GLOB))
    return candidates[-1] if candidates else None


def _load_inventory_set(path: Path) -> Set[Tuple[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    endpoints = payload.get("endpoints", [])
    return {
        (str(item.get("method", "")).upper(), str(item.get("path", "")))
        for item in endpoints
        if item.get("method") and item.get("path")
    }


def _build_prefix_churn(
    current: Set[Tuple[str, str]],
    previous: Set[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    added = current - previous
    removed = previous - current
    all_buckets = Counter()

    for _, path in current:
        all_buckets[_prefix_bucket(path)] += 1

    added_buckets = Counter(_prefix_bucket(path) for _, path in added)
    removed_buckets = Counter(_prefix_bucket(path) for _, path in removed)

    rows: List[Dict[str, Any]] = []
    for bucket in sorted(set(all_buckets) | set(added_buckets) | set(removed_buckets)):
        current_count = all_buckets[bucket]
        churn = added_buckets[bucket] + removed_buckets[bucket]
        churn_pct = round((churn / max(current_count, 1)) * 100, 2)
        rows.append(
            {
                "prefix_bucket": bucket,
                "current_count": current_count,
                "added": added_buckets[bucket],
                "removed": removed_buckets[bucket],
                "churn": churn,
                "churn_pct_vs_current": churn_pct,
                "high_churn": churn_pct >= 20.0,
            }
        )
    return rows


def _duplicate_semantic_routes(rows: List[RouteRow]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[RouteRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.method, row.semantic_path)].append(row)

    duplicates: List[Dict[str, Any]] = []
    for (method, semantic_path), items in grouped.items():
        unique_paths = sorted({item.path for item in items})
        if len(unique_paths) <= 1:
            continue
        duplicates.append(
            {
                "method": method,
                "semantic_path": semantic_path,
                "paths": unique_paths,
                "route_count": len(unique_paths),
            }
        )
    duplicates.sort(key=lambda item: (item["method"], item["semantic_path"]))
    return duplicates


def _header_coverage_summary(rows: List[RouteRow]) -> Dict[str, int]:
    summary = Counter()
    for row in rows:
        key = "has_required_headers" if row.required_headers else "no_explicit_required_headers"
        summary[key] += 1
        if any(h.lower() == "authorization" for h in row.required_headers):
            summary["authorization_required"] += 1
        if any("signature" in h.lower() for h in row.required_headers):
            summary["signature_header_required"] += 1
    return dict(summary)


def _write_markdown(
    md_path: Path,
    generated_at: str,
    total_routes: int,
    added: List[Tuple[str, str]],
    removed: List[Tuple[str, str]],
    prefix_churn: List[Dict[str, Any]],
    duplicates: List[Dict[str, Any]],
    header_summary: Dict[str, int],
    baseline_name: Optional[str],
) -> None:
    lines: List[str] = []
    lines.append("# Route Governance Report")
    lines.append("")
    lines.append(f"Generated: `{generated_at}`")
    lines.append(f"Total routes: **{total_routes}**")
    if baseline_name:
        lines.append(f"Baseline: `{baseline_name}`")
    lines.append("")

    lines.append("## Drift Summary")
    lines.append("")
    lines.append(f"- Added routes: **{len(added)}**")
    lines.append(f"- Removed routes: **{len(removed)}**")
    lines.append("")

    if added:
        lines.append("### Added")
        lines.append("")
        lines.append("| Method | Path |")
        lines.append("|---|---|")
        for method, path in sorted(added)[:100]:
            lines.append(f"| {method} | {path} |")
        lines.append("")

    if removed:
        lines.append("### Removed")
        lines.append("")
        lines.append("| Method | Path |")
        lines.append("|---|---|")
        for method, path in sorted(removed)[:100]:
            lines.append(f"| {method} | {path} |")
        lines.append("")

    lines.append("## Prefix Churn")
    lines.append("")
    lines.append("| Prefix | Current | Added | Removed | Churn % | High churn |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for row in prefix_churn:
        high_churn = "yes" if row["high_churn"] else "no"
        lines.append(
            f"| {row['prefix_bucket']} | {row['current_count']} | {row['added']} | {row['removed']} | {row['churn_pct_vs_current']} | {high_churn} |"
        )
    lines.append("")

    lines.append("## Header Coverage")
    lines.append("")
    for key, value in sorted(header_summary.items()):
        lines.append(f"- {key}: **{value}**")
    lines.append("")

    lines.append("## Duplicate Semantic Routes")
    lines.append("")
    if not duplicates:
        lines.append("- None")
    else:
        for item in duplicates:
            lines.append(f"- `{item['method']} {item['semantic_path']}` appears in:")
            for route_path in item["paths"]:
                lines.append(f"  - `{route_path}`")
    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d")

    rows = _collect_rows()
    current_set = {(row.method, row.path) for row in rows}

    baseline = _latest_inventory()
    baseline_set: Set[Tuple[str, str]] = set()
    baseline_name: Optional[str] = None
    if baseline:
        baseline_set = _load_inventory_set(baseline)
        baseline_name = baseline.name

    added = sorted(current_set - baseline_set) if baseline_set else sorted(current_set)
    removed = sorted(baseline_set - current_set) if baseline_set else []

    prefix_churn = _build_prefix_churn(current_set, baseline_set)
    duplicates = _duplicate_semantic_routes(rows)
    header_summary = _header_coverage_summary(rows)

    json_payload = {
        "generated_at": now.isoformat(),
        "total_routes": len(rows),
        "baseline": baseline_name,
        "added_count": len(added),
        "removed_count": len(removed),
        "added": [{"method": m, "path": p} for m, p in added],
        "removed": [{"method": m, "path": p} for m, p in removed],
        "prefix_churn": prefix_churn,
        "header_coverage": header_summary,
        "duplicate_semantic_routes": duplicates,
        "routes": [asdict(row) for row in rows],
    }

    json_path = REPORTS_DIR / f"ROUTE_GOVERNANCE_REPORT_{stamp}.json"
    md_path = REPORTS_DIR / f"ROUTE_GOVERNANCE_REPORT_{stamp}.md"

    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    _write_markdown(
        md_path=md_path,
        generated_at=now.isoformat(),
        total_routes=len(rows),
        added=added,
        removed=removed,
        prefix_churn=prefix_churn,
        duplicates=duplicates,
        header_summary=header_summary,
        baseline_name=baseline_name,
    )

    print(str(json_path))
    print(str(md_path))


if __name__ == "__main__":
    main()
