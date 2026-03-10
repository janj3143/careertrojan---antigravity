#!/usr/bin/env python3
"""Generate discovery-first orchestrator reports for CareerTrojan."""

from __future__ import annotations

import datetime as dt
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "discovery"


def now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def walk_files(base: Path) -> list[Path]:
    items: list[Path] = []
    for p in base.rglob("*"):
        if p.is_file() and "node_modules" not in str(p):
            items.append(p)
    return items


def py_files(base: Path) -> list[Path]:
    return [p for p in walk_files(base) if p.suffix == ".py"]


def tsx_ts_files(base: Path) -> list[Path]:
    return [p for p in walk_files(base) if p.suffix in {".ts", ".tsx"}]


def count_router_decorators(router_dir: Path) -> int:
    total = 0
    for p in py_files(router_dir):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for token in ("@router.get(", "@router.post(", "@router.put(", "@router.patch(", "@router.delete("):
            total += txt.count(token)
    return total


def list_entrypoints() -> dict[str, list[str]]:
    py_mains = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in ROOT.rglob("main.py") if "node_modules" not in str(p))
    fe_entries = []
    for pattern in ("apps/**/src/main.tsx", "apps/**/src/App.tsx"):
        for p in ROOT.glob(pattern):
            if "node_modules" not in str(p):
                fe_entries.append(str(p.relative_to(ROOT)).replace("\\", "/"))
    return {"python_main": sorted(py_mains), "frontend_entries": sorted(set(fe_entries))}


def fastapi_routes() -> tuple[int, list[str], list[str]]:
    try:
        import sys

        sys.path.insert(0, str(ROOT))
        from services.backend_api.main import app  # type: ignore

        routes = sorted({getattr(r, "path", "") for r in app.routes if getattr(r, "path", None)})
        return len(routes), routes[:120], routes[-20:]
    except Exception as exc:  # pragma: no cover
        return 0, [f"ERROR: {exc}"], []


def duplicate_filenames(scope_dirs: list[str]) -> list[tuple[str, int]]:
    files: list[Path] = []
    for d in scope_dirs:
        p = ROOT / d
        if p.exists():
            files.extend(walk_files(p))
    counts = Counter(f.name for f in files)
    dups = [(name, count) for name, count in counts.items() if count > 1]
    dups.sort(key=lambda x: x[1], reverse=True)
    return dups[:50]


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    all_files = walk_files(ROOT)
    py = py_files(ROOT)
    router_dir = ROOT / "services" / "backend_api" / "routers"
    route_decorators = count_router_decorators(router_dir) if router_dir.exists() else 0
    route_count, route_head, route_tail = fastapi_routes()
    entries = list_entrypoints()
    ai_engine_files = sorted(
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in py_files(ROOT / "services" / "ai_engine")
    ) if (ROOT / "services" / "ai_engine").exists() else []
    tests = [
        p for p in all_files if p.name.startswith("test_") or "test" in p.name.lower() or p.name in {"pytest.ini", "conftest.py"}
    ]

    stubs = 0
    orchestrator_mentions = 0
    for p in py:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        stubs += txt.count("NotImplementedError") + txt.count("status_code=501") + txt.count("status_code = 501")
        orchestrator_mentions += txt.lower().count("orchestrator")

    visual_hits = []
    for p in tsx_ts_files(ROOT / "apps") if (ROOT / "apps").exists() else []:
        t = p.read_text(encoding="utf-8", errors="ignore").lower()
        if any(k in t for k in ("spider", "covey", "heatmap", "chart", "visual")):
            visual_hits.append(str(p.relative_to(ROOT)).replace("\\", "/"))

    duplicates = duplicate_filenames(["apps", "services", "scripts", "config", "infra"])

    generated = now_iso()

    write(
        OUT / "system_inventory.md",
        f"# System Inventory\n\nGenerated: {generated}\n\n"
        f"- Total files (excluding node_modules): {len(all_files)}\n"
        f"- Python files: {len(py)}\n"
        f"- Router files: {len(list(py_files(router_dir)))}\n"
        f"- Frontend TS/TSX files: {len(tsx_ts_files(ROOT / 'apps')) if (ROOT / 'apps').exists() else 0}\n"
        f"- Test-related files: {len(tests)}\n"
        "\n## Top-Level Modules\n"
        "- apps\n- services\n- scripts\n- config\n- infra\n- tests\n- docs\n- reports\n"
        "\n## Runtime Entrypoints\n"
        + "\n".join(f"- {x}" for x in entries["python_main"][:20])
        + "\n\n## Frontend Entrypoints (sample)\n"
        + "\n".join(f"- {x}" for x in entries["frontend_entries"][:25])
        + "\n",
    )

    write(
        OUT / "endpoint_inventory.md",
        f"# Endpoint Inventory\n\nGenerated: {generated}\n\n"
        f"- Route decorators in routers: {route_decorators}\n"
        f"- FastAPI mounted routes discovered: {route_count}\n"
        "\n## Mounted Route Sample (head)\n"
        + "\n".join(f"- {r}" for r in route_head)
        + "\n\n## Mounted Route Sample (tail)\n"
        + "\n".join(f"- {r}" for r in route_tail)
        + "\n",
    )

    write(
        OUT / "service_dependency_map.md",
        f"# Service Dependency Map\n\nGenerated: {generated}\n\n"
        "## Core Runtime Flow\n"
        "- routers -> services/backend_api/services -> db/models\n"
        "- routers -> services/ai_engine (selected routes)\n"
        "- middleware stack in services/backend_api/main.py wraps all API calls\n"
        "\n## Key Hubs\n"
        "- services/backend_api/main.py (router composition)\n"
        "- services/backend_api/routers/* (route layer)\n"
        "- services/backend_api/services/* (business logic)\n"
        "- services/ai_engine/* (training/analysis engines)\n"
        "\n## Discovery Notes\n"
        "- This report is structural; call-graph expansion should be added in phase-2 discovery.\n",
    )

    write(
        OUT / "ai_model_registry.md",
        f"# AI Model Registry\n\nGenerated: {generated}\n\n"
        f"- AI engine python modules: {len(ai_engine_files)}\n"
        f"- Orchestrator keyword mentions in Python code: {orchestrator_mentions}\n"
        "\n## AI Engine Modules\n"
        + "\n".join(f"- {m}" for m in ai_engine_files)
        + "\n\n## Initial Classification\n"
        "- Training and orchestration modules exist.\n"
        "- Discovery phase-2 should trace runtime invocation from API routes to these modules.\n",
    )

    write(
        OUT / "feature_input_matrix.md",
        f"# Feature Input Matrix\n\nGenerated: {generated}\n\n"
        "## Canonical Feature Families (target)\n"
        "- skills_vector\n- title_embedding\n- industry_embedding\n- experience_years\n"
        "- quantification_score\n- semantic_alignment_score\n- confidence_features\n"
        "\n## Current State\n"
        "- Feature generation appears distributed across parser, intelligence, and lens routes.\n"
        "- Discovery phase-2: map exact request model -> feature function -> model input.\n",
    )

    write(
        OUT / "routing_trace_report.md",
        f"# Routing Trace Report\n\nGenerated: {generated}\n\n"
        "## FastAPI Composition\n"
        "- Router mounting occurs in services/backend_api/main.py\n"
        f"- Mounted routes observed: {route_count}\n"
        "\n## Critical Route Families\n"
        "- /api/ops/v1/*\n- /api/intelligence/v1/*\n- /api/lenses/v1/*\n- /api/payment/v1/*\n- /api/mentor/v1/*\n"
        "\n## Trace Focus for Next Pass\n"
        "- upload -> parsing -> feature generation -> inference -> explanation -> visual payload\n",
    )

    write(
        OUT / "duplicate_and_dead_code_report.md",
        f"# Duplicate And Dead Code Report\n\nGenerated: {generated}\n\n"
        f"- Stub signal count (NotImplemented/501 patterns): {stubs}\n"
        "\n## Duplicate Filename Indicators (first-party scope)\n"
        + "\n".join(f"- {name}: {count}" for name, count in duplicates)
        + "\n\n## Interpretation\n"
        "- High duplication in mentor page template components suggests shared scaffolding clones.\n"
        "- Further pass needed to determine semantic duplicates vs intentional module reuse.\n",
    )

    write(
        OUT / "visualisation_data_binding_report.md",
        f"# Visualisation Data Binding Report\n\nGenerated: {generated}\n\n"
        f"- Visual keyword hits in apps source: {len(visual_hits)}\n"
        "\n## Key Evidence\n"
        "- apps/user/src/lib/api.ts exposes /api/lenses/v1/spider integration.\n"
        "- apps/user/src/lib/chartLensTypes.ts defines spider and covey contracts.\n"
        "- apps/user/src/pages/VisualisationsHub.tsx is routed in user app.\n"
        "\n## Sample Visual Files\n"
        + "\n".join(f"- {x}" for x in visual_hits[:40])
        + "\n\n## Verification Target\n"
        "- Confirm every visual consumes live payloads, not placeholders, in runtime traces.\n",
    )

    write(
        OUT / "test_coverage_gap_report.md",
        f"# Test Coverage Gap Report\n\nGenerated: {generated}\n\n"
        f"- Test-related file count: {len(tests)}\n"
        "\n## Present\n"
        "- E2E harnesses exist for golden path and braintree path.\n"
        "- Smoke and route governance scripts exist under scripts/.\n"
        "\n## Gaps\n"
        "- Need deterministic route->service->model orchestration integration tests.\n"
        "- Need visualization payload contract tests (spider/covey/heatmap).\n"
        "- Need model contribution logging assertions in CI.\n",
    )

    write(
        OUT / "implementation_readiness_report.md",
        f"# Implementation Readiness Report\n\nGenerated: {generated}\n\n"
        "## Keep\n"
        "- Existing router surface and active API contracts.\n"
        "- Current Dockerized runtime and E2E harnesses on port 8600.\n"
        "\n## Rewire\n"
        "- Centralize model dispatch through a single orchestrator interface.\n"
        "- Standardize decision object contract across analytics routes.\n"
        "\n## Merge\n"
        "- Consolidate duplicated mentor/page scaffolds where behavior overlaps.\n"
        "\n## Retire\n"
        "- Residual non-runtime training/legacy files not called by active routes (after trace validation).\n"
        "\n## Build Next\n"
        "- Route-to-model trace map with confidence logging.\n"
        "- Feature input registry linked to each active route.\n"
        "- CI gate for orchestration integrity and placeholder-leak checks.\n",
    )

    write(
        OUT / "discovery_manifest.json",
        json.dumps(
            {
                "generated": generated,
                "file_count": len(all_files),
                "python_files": len(py),
                "router_decorators": route_decorators,
                "mounted_routes": route_count,
                "ai_engine_modules": len(ai_engine_files),
                "test_related_files": len(tests),
                "stub_signals": stubs,
                "out_dir": str(OUT.relative_to(ROOT)).replace("\\", "/"),
            },
            indent=2,
        ) + "\n",
    )

    print(f"Discovery pack generated in: {OUT}")
    print("Artifacts: 10 markdown reports + discovery_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
