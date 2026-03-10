"""
Route Governance Engine
=======================
Provides five capabilities against a running FastAPI `app`:

1. **Snapshot** — serialise every route to a canonical JSON manifest.
2. **Drift**   — diff the live manifest against a saved baseline.
3. **Policy**  — enforce configurable rules (auth required, naming, etc.).
4. **Audit**   — combine drift + policy into a single report.
5. **Summary** — one-line counts for dashboards / probes.

All functions are pure (no DB, no side-effects) except `save_snapshot`.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI
from fastapi.routing import APIRoute

# ── Where we persist the baseline snapshot ────────────────────────────────
_DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parents[3] / "data" / "governance"


# ─────────────────────────────────────────────────────────────────────────
#  Data structures
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class RouteRecord:
    """Canonical representation of a single HTTP endpoint."""
    method: str
    path: str
    name: str                     # FastAPI operation id / function name
    tags: List[str]               = field(default_factory=list)
    has_auth: bool                = False
    has_response_model: bool      = False
    deprecated: bool              = False
    path_params: List[str]        = field(default_factory=list)
    summary: Optional[str]        = None

    @property
    def key(self) -> str:
        return f"{self.method} {self.path}"


@dataclass
class PolicyViolation:
    """A single rule violation."""
    rule: str
    severity: str        # "error" | "warning" | "info"
    route_key: str       # "GET /api/..." or "" for global
    message: str


@dataclass
class DriftEntry:
    """One added / removed / changed route."""
    kind: str           # "added" | "removed" | "changed"
    route_key: str
    detail: str


@dataclass
class GovernanceReport:
    """Full governance output — serialisable to JSON."""
    generated_at: str
    total_routes: int
    violations: List[Dict[str, Any]]     = field(default_factory=list)
    drift: List[Dict[str, Any]]          = field(default_factory=list)
    summary: Dict[str, Any]              = field(default_factory=dict)
    route_manifest: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────
#  1) SNAPSHOT — extract every route from a running FastAPI app
# ─────────────────────────────────────────────────────────────────────────

def _has_auth_dependency(route: APIRoute) -> bool:
    """Heuristic: does this route (or its router) declare an auth dependency?"""
    deps = list(getattr(route, "dependencies", []) or [])
    deps += list(getattr(route, "dependant", None) and
                 getattr(route.dependant, "dependencies", []) or [])

    for dep in deps:
        dep_callable = getattr(dep, "dependency", None)
        if dep_callable is None:
            continue
        name = getattr(dep_callable, "__name__", "") or ""
        qual = getattr(dep_callable, "__qualname__", "") or ""
        combined = f"{name} {qual}".lower()
        if any(kw in combined for kw in ("current_user", "require_admin",
                                          "require_user", "get_current",
                                          "auth", "token")):
            return True

    # Also check the endpoint signature for Depends-injected auth params
    endpoint = getattr(route, "endpoint", None)
    if endpoint:
        import inspect
        sig = inspect.signature(endpoint)
        for param in sig.parameters.values():
            default = param.default
            dep_fn = getattr(default, "dependency", None)
            if dep_fn:
                dep_name = getattr(dep_fn, "__name__", "").lower()
                if any(kw in dep_name for kw in ("current_user", "require_admin",
                                                   "require_user", "get_current",
                                                   "user_id_from_token", "auth")):
                    return True
    return False


def extract_manifest(app: FastAPI) -> List[RouteRecord]:
    """Return a sorted list of every endpoint registered in *app*."""
    records: List[RouteRecord] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(route.methods - {"HEAD", "OPTIONS"})
        for method in methods:
            path_params = re.findall(r"\{(\w+)\}", route.path)
            rec = RouteRecord(
                method=method,
                path=route.path,
                name=route.name or "",
                tags=list(route.tags) if route.tags else [],
                has_auth=_has_auth_dependency(route),
                has_response_model=route.response_model is not None,
                deprecated=bool(getattr(route, "deprecated", False)),
                path_params=path_params,
                summary=getattr(route, "summary", None),
            )
            records.append(rec)
    records.sort(key=lambda r: (r.path, r.method))
    return records


def manifest_to_json(records: List[RouteRecord]) -> List[Dict[str, Any]]:
    return [asdict(r) for r in records]


def save_snapshot(app: FastAPI, directory: Optional[Path] = None) -> Path:
    """Persist the current route manifest as the governance baseline."""
    directory = directory or _DEFAULT_SNAPSHOT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    records = extract_manifest(app)
    payload = {
        "snapshot_time": datetime.now(timezone.utc).isoformat(),
        "total_routes": len(records),
        "checksum": _manifest_checksum(records),
        "routes": manifest_to_json(records),
    }
    path = directory / "route_baseline.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(directory: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Load the last saved baseline (or None)."""
    directory = directory or _DEFAULT_SNAPSHOT_DIR
    path = directory / "route_baseline.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_checksum(records: List[RouteRecord]) -> str:
    keys = sorted(r.key for r in records)
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────
#  2) DRIFT — compare live routes against saved baseline
# ─────────────────────────────────────────────────────────────────────────

def detect_drift(
    live: List[RouteRecord],
    baseline: Optional[Dict[str, Any]] = None,
) -> List[DriftEntry]:
    """Return list of diffs between *live* manifest and *baseline* JSON."""
    if baseline is None:
        baseline = load_snapshot()
    if baseline is None:
        return [DriftEntry("info", "", "No baseline snapshot found — run save_snapshot() first")]

    base_routes: Dict[str, Dict] = {
        f"{r['method']} {r['path']}": r for r in baseline.get("routes", [])
    }
    live_routes: Dict[str, Dict] = {
        r.key: asdict(r) for r in live
    }

    diffs: List[DriftEntry] = []

    # Added routes (in live but not baseline)
    for key in sorted(set(live_routes) - set(base_routes)):
        diffs.append(DriftEntry("added", key, "New route not in baseline"))

    # Removed routes (in baseline but not live)
    for key in sorted(set(base_routes) - set(live_routes)):
        diffs.append(DriftEntry("removed", key, "Route removed since baseline"))

    # Changed routes (present in both but metadata differs)
    for key in sorted(set(live_routes) & set(base_routes)):
        live_rec = live_routes[key]
        base_rec = base_routes[key]
        changes = []
        for field_name in ("has_auth", "has_response_model", "deprecated", "tags"):
            lv = live_rec.get(field_name)
            bv = base_rec.get(field_name)
            if lv != bv:
                changes.append(f"{field_name}: {bv!r} → {lv!r}")
        if changes:
            diffs.append(DriftEntry("changed", key, "; ".join(changes)))

    return diffs


# ─────────────────────────────────────────────────────────────────────────
#  3) POLICY — configurable rule checks
# ─────────────────────────────────────────────────────────────────────────

# Paths that are legitimately public (no auth expected)
PUBLIC_PATHS: Set[str] = {
    "/health", "/healthz", "/readyz",
    "/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect",
}

# Prefixes that must always have auth
AUTH_REQUIRED_PREFIXES: Tuple[str, ...] = (
    "/api/admin/",
    "/api/user/",
    "/api/payment/",
    "/api/credits/",
    "/api/gdpr/",
    "/api/mentorship/",
    "/api/mentor/",
    "/api/resume/",
    "/api/sessions/",
    "/api/rewards/",
)

# Prefixes where auth is recommended but not strictly required
AUTH_RECOMMENDED_PREFIXES: Tuple[str, ...] = (
    "/api/coaching/",
    "/api/intelligence/",
    "/api/jobs/",
    "/api/blockers/",
    "/api/insights/",
    "/api/contacts/",
    "/api/support/",
    "/api/ai-data/",
)

# Paths that must be public (webhooks — verified by signature, not JWT)
SIGNATURE_VERIFIED_PATHS: Set[str] = {
    "/api/support/v1/webhooks/zendesk",
    "/api/webhooks/v1/zendesk",
    "/api/payment/v1/webhooks",
}

# Naming conventions
PATH_PATTERN = re.compile(r"^(/[a-z0-9\-]+(/\{[a-z_]+\})?)+$|^/$")

# Admin-only operations
ADMIN_ONLY_METHODS: Dict[str, Set[str]] = {
    "DELETE": {"/api/payment/v1/methods/{token}"},
    "POST": {"/api/payment/v1/refund/{transaction_id}"},
}


def check_policies(
    records: List[RouteRecord],
    *,
    strict: bool = False,
) -> List[PolicyViolation]:
    """Run all governance rules against the manifest. Returns violations."""
    violations: List[PolicyViolation] = []

    for rec in records:
        # ── Rule 1: Auth required on sensitive prefixes ─────────
        if rec.path.startswith(AUTH_REQUIRED_PREFIXES) and not rec.has_auth:
            if rec.path in SIGNATURE_VERIFIED_PATHS:
                continue  # signature-verified webhooks are fine
            if rec.path.endswith("/health"):
                continue  # health probes are fine public
            violations.append(PolicyViolation(
                rule="AUTH_REQUIRED",
                severity="error",
                route_key=rec.key,
                message=f"Sensitive prefix requires auth but none detected",
            ))

        # ── Rule 2: Auth recommended on other API paths ────────
        if strict and rec.path.startswith(AUTH_RECOMMENDED_PREFIXES) and not rec.has_auth:
            violations.append(PolicyViolation(
                rule="AUTH_RECOMMENDED",
                severity="warning",
                route_key=rec.key,
                message=f"API endpoint lacks auth; recommended for production",
            ))

        # ── Rule 3: Public paths that SHOULD NOT have auth ─────
        # (informational only)

        # ── Rule 4: Naming convention — lowercase-kebab paths ──
        # Skip paths with path params — they use {snake_case}
        clean = re.sub(r"\{[^}]+\}", "{x}", rec.path)
        if not PATH_PATTERN.match(clean) and rec.path not in PUBLIC_PATHS:
            violations.append(PolicyViolation(
                rule="NAMING_CONVENTION",
                severity="warning",
                route_key=rec.key,
                message=f"Path does not follow lowercase-kebab convention",
            ))

        # ── Rule 5: Mutating endpoints should have auth ────────
        if rec.method in ("POST", "PUT", "PATCH", "DELETE") and not rec.has_auth:
            if rec.path in PUBLIC_PATHS or rec.path in SIGNATURE_VERIFIED_PATHS:
                continue
            violations.append(PolicyViolation(
                rule="MUTATING_NO_AUTH",
                severity="error" if rec.method == "DELETE" else "warning",
                route_key=rec.key,
                message=f"{rec.method} endpoint has no auth — mutation risk",
            ))

        # ── Rule 6: Admin-only operations check ────────────────
        admin_paths = ADMIN_ONLY_METHODS.get(rec.method, set())
        if rec.path in admin_paths and not rec.has_auth:
            violations.append(PolicyViolation(
                rule="ADMIN_ONLY",
                severity="error",
                route_key=rec.key,
                message=f"Admin-sensitive operation missing auth: {rec.method} {rec.path}",
            ))

        # ── Rule 7: Response model declared ────────────────────
        if strict and not rec.has_response_model:
            violations.append(PolicyViolation(
                rule="NO_RESPONSE_MODEL",
                severity="info",
                route_key=rec.key,
                message="No Pydantic response_model declared — schema contract is implicit",
            ))

    # ── Rule 8: Duplicate route detection ──────────────────────
    seen_keys: Dict[str, int] = {}
    for rec in records:
        seen_keys[rec.key] = seen_keys.get(rec.key, 0) + 1
    for key, count in seen_keys.items():
        if count > 1:
            violations.append(PolicyViolation(
                rule="DUPLICATE_ROUTE",
                severity="error",
                route_key=key,
                message=f"Route registered {count} times — routing conflict",
            ))

    # ── Rule 9: Prefix collision check ─────────────────────────
    prefixes: Dict[str, Set[str]] = {}
    for rec in records:
        parts = rec.path.strip("/").split("/")
        if len(parts) >= 2:
            prefix = "/" + "/".join(parts[:2])
            tags_str = ",".join(rec.tags) if rec.tags else rec.name
            prefixes.setdefault(prefix, set()).add(tags_str)
    for prefix, tag_sets in prefixes.items():
        if len(tag_sets) > 2:
            violations.append(PolicyViolation(
                rule="PREFIX_COLLISION",
                severity="warning",
                route_key=prefix,
                message=f"Prefix shared by {len(tag_sets)} distinct tag groups: {tag_sets}",
            ))

    # ── Rule 10: Webhook endpoints must be public (no JWT) ─────
    for rec in records:
        if "webhook" in rec.path.lower() and rec.has_auth:
            violations.append(PolicyViolation(
                rule="WEBHOOK_HAS_JWT",
                severity="warning",
                route_key=rec.key,
                message="Webhook endpoints should use signature verification, not JWT auth",
            ))

    # Sort: errors first, then warnings, then info
    severity_order = {"error": 0, "warning": 1, "info": 2}
    violations.sort(key=lambda v: (severity_order.get(v.severity, 9), v.route_key))
    return violations


# ─────────────────────────────────────────────────────────────────────────
#  4) AUDIT — combined report
# ─────────────────────────────────────────────────────────────────────────

def run_audit(
    app: FastAPI,
    *,
    strict: bool = False,
    include_manifest: bool = False,
) -> GovernanceReport:
    """Full governance audit: snapshot + drift + policies."""
    live = extract_manifest(app)
    violations = check_policies(live, strict=strict)
    drift = detect_drift(live)

    error_count = sum(1 for v in violations if v.severity == "error")
    warning_count = sum(1 for v in violations if v.severity == "warning")
    info_count = sum(1 for v in violations if v.severity == "info")

    authed = sum(1 for r in live if r.has_auth)
    unauthed = len(live) - authed

    # Group routes by prefix
    prefix_groups: Dict[str, int] = {}
    for r in live:
        parts = r.path.strip("/").split("/")
        prefix = "/" + "/".join(parts[:3]) if len(parts) >= 3 else r.path
        prefix_groups[prefix] = prefix_groups.get(prefix, 0) + 1

    report = GovernanceReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_routes=len(live),
        violations=[asdict(v) for v in violations],
        drift=[asdict(d) for d in drift],
        summary={
            "total_routes": len(live),
            "authenticated": authed,
            "unauthenticated": unauthed,
            "errors": error_count,
            "warnings": warning_count,
            "info": info_count,
            "drift_entries": len(drift),
            "prefix_groups": dict(sorted(prefix_groups.items(),
                                         key=lambda kv: -kv[1])),
        },
    )
    if include_manifest:
        report.route_manifest = manifest_to_json(live)

    return report


# ─────────────────────────────────────────────────────────────────────────
#  5) SUMMARY — compact one-liner for probes / CI
# ─────────────────────────────────────────────────────────────────────────

def quick_summary(app: FastAPI) -> Dict[str, Any]:
    """Lightweight governance check — suitable for /healthz-style probes."""
    live = extract_manifest(app)
    violations = check_policies(live, strict=False)
    errors = [v for v in violations if v.severity == "error"]
    return {
        "total_routes": len(live),
        "policy_errors": len(errors),
        "policy_warnings": sum(1 for v in violations if v.severity == "warning"),
        "checksum": _manifest_checksum(live),
        "healthy": len(errors) == 0,
    }
