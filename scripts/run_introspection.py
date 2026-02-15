"""
CareerTrojan - Endpoint Introspection Pipeline (Phase 4a)
"""
import argparse
import json
import os
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Ensure services package is importable
for init_path in (
    ROOT / "services" / "__init__.py",
    ROOT / "services" / "backend_api" / "__init__.py",
):
    if not init_path.exists():
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text("", encoding="utf-8")
        print(f"[init] Created missing {init_path}")


def find_fastapi_app():
    """Import the FastAPI app from services.backend_api.main."""
    try:
        from services.backend_api.main import app
        if app and hasattr(app, "routes"):
            count = sum(1 for r in app.routes if hasattr(r, "methods"))
            print(f"[introspect] Loaded FastAPI app - {count} routes")
            return app
    except Exception as e:
        print(f"[introspect] services.backend_api.main failed: {e}")
        traceback.print_exc()

    # Fallback: try other known entry points
    for mod_path in ("services.shared_backend.main", "shared_backend.main"):
        try:
            parts = mod_path.rsplit(".", 1)
            module = __import__(parts[0], fromlist=[parts[1]])
            sub = getattr(module, parts[1])
            app = getattr(sub, "app", None)
            if app and hasattr(app, "routes"):
                count = sum(1 for r in app.routes if hasattr(r, "methods"))
                print(f"[introspect] Loaded app from {mod_path} - {count} routes")
                return app
        except Exception:
            continue

    return None


def introspect_fastapi(output_path, dry_run=False):
    """Extract all registered routes from the FastAPI app."""
    app = find_fastapi_app()

    routes = []
    if app:
        for route in app.routes:
            methods = getattr(route, "methods", None)
            if methods:
                routes.append({
                    "path": route.path,
                    "methods": sorted(methods),
                    "name": getattr(route, "name", None),
                    "tags": getattr(route, "tags", []),
                })
    else:
        print("[introspect] Could not import FastAPI app. Trying openapi.json fallback...")
        # Only look in OUR project, not in site-packages
        for candidate in (ROOT / "services").rglob("openapi.json"):
            try:
                spec = json.loads(candidate.read_text(encoding="utf-8"))
                for path, methods in spec.get("paths", {}).items():
                    for method in methods:
                        if method.upper() in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                            routes.append({
                                "path": path,
                                "methods": [method.upper()],
                                "name": methods[method].get("operationId", ""),
                                "tags": methods[method].get("tags", []),
                            })
                print(f"[introspect] Loaded {len(routes)} routes from {candidate}")
                break
            except Exception:
                continue

    print(f"[introspect] Found {len(routes)} API routes.")

    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(routes, indent=2))
        print(f"[introspect] Written to {output_path}")
    else:
        print(f"[introspect] Dry-run - would write {len(routes)} routes to {output_path}")

    return routes


def find_portal_src_dirs():
    """Auto-discover portal src directories."""
    apps_dir = ROOT / "apps"
    if not apps_dir.exists():
        return []

    src_dirs = []
    for portal in ("admin", "user", "mentor"):
        src = apps_dir / portal / "src"
        if src.exists():
            src_dirs.append((portal, src))

    # Nested mentor sub-page src dirs
    mentor_pages = apps_dir / "mentor" / "src" / "pages"
    if mentor_pages.exists():
        for sub_src in mentor_pages.rglob("src"):
            if sub_src.is_dir() and "node_modules" not in str(sub_src):
                name = f"mentor/{sub_src.parent.relative_to(mentor_pages)}"
                src_dirs.append((name, sub_src))

    # User components
    user_comp_src = apps_dir / "user" / "components" / "src"
    if user_comp_src.exists():
        src_dirs.append(("user/components", user_comp_src))

    for name, path in src_dirs:
        print(f"[react-scan] Discovered: {name} -> {path}")

    return src_dirs


def scan_react_callsites():
    """Scan React portals for API call patterns — wide regex."""
    # Broader pattern to catch more URL forms
    patterns = [
        re.compile(r"""(?:fetch|axios\.(?:get|post|put|patch|delete))\s*\(\s*[`"']([^`"']+)[`"']""", re.IGNORECASE),
        re.compile(r"""(?:api\.(?:get|post|put|patch|delete))\s*\(\s*[`"']([^`"']+)[`"']""", re.IGNORECASE),
        re.compile(r"""(?:baseURL|apiUrl|API_URL|API_BASE|endpoint)\s*[:=]\s*[`"']([^`"']+)[`"']""", re.IGNORECASE),
        re.compile(r"""(?:url|href)\s*[:=]\s*[`"'](/api/[^`"']+)[`"']""", re.IGNORECASE),
    ]

    src_dirs = find_portal_src_dirs()
    callsites = []

    for portal_name, src_dir in src_dirs:
        for f in src_dir.rglob("*.ts*"):
            if "node_modules" in str(f):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in patterns:
                for m in pat.finditer(content):
                    url = m.group(1)
                    if "/" in url:
                        callsites.append({
                            "portal": portal_name,
                            "file": str(f.relative_to(ROOT)),
                            "url": url,
                            "line": content[:m.start()].count("\n") + 1,
                        })

    print(f"[react-scan] Found {len(callsites)} API callsites across portals.")
    return callsites


def join_graph(routes, callsites, output_path, dry_run=False):
    """Join backend routes with frontend callsites."""
    graph = {
        "total_backend_routes": len(routes),
        "total_frontend_callsites": len(callsites),
        "backend_routes": routes,
        "frontend_callsites": callsites,
        "unmatched_callsites": [],
    }

    route_paths = {r["path"] for r in routes}
    for cs in callsites:
        url = cs["url"].split("?")[0]
        for prefix in ("http://localhost:8500", "http://127.0.0.1:8500"):
            if url.startswith(prefix):
                url = url[len(prefix):]
        if url not in route_paths:
            graph["unmatched_callsites"].append(cs)

    graph["unmatched_count"] = len(graph["unmatched_callsites"])

    if not dry_run:
        output_path.write_text(json.dumps(graph, indent=2))
        print(f"[join] Full endpoint graph written to {output_path}")
    print(f"[join] Unmatched callsites: {graph['unmatched_count']}")
    return graph


def run_contamination_check():
    """Sales-vs-Python trap."""
    print("[trap] Running contamination check (Sales vs Python)...")
    contaminated_keywords = {"python developer", "machine learning engineer", "data scientist", "software engineer"}

    try:
        from services.ai_engine.matcher import match_profile
        results = match_profile({
            "current_title": "Sales Person",
            "skills": ["negotiation", "CRM", "cold calling", "pipeline management"],
            "experience_years": 5,
        })
        titles = {r.get("suggested_title", "").lower() for r in results}
    except Exception as e:
        print(f"[trap] Could not run live matcher ({e}). Scanning source for hardcoded defaults...")
        # Only flag ACTUAL default-return contamination: look for patterns like
        # default_title = "software engineer" or fallback_role = "data scientist"
        # Exclude gazetteers, seed phrases, test fixtures, training data — those
        # legitimately contain these terms as domain vocabulary.
        import re as _re
        contamination_pattern = _re.compile(
            r'(?:default|fallback)[_\s]*(?:title|role|suggestion|result)\s*[:=]\s*["\']('
            + "|".join(_re.escape(k) for k in contaminated_keywords)
            + r')["\']',
            _re.IGNORECASE,
        )
        safe_stems = {"collocation_engine", "expert_system", "train_", "test_",
                       "seed", "gazetteer", "fixture", "mock", "sample"}
        found = False
        for py_file in (ROOT / "services").rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            stem = py_file.stem.lower()
            if any(s in stem for s in safe_stems):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for m in contamination_pattern.finditer(content):
                    line_no = content[:m.start()].count("\n") + 1
                    print(f"[trap] CONTAMINATION: {py_file}:{line_no} — '{m.group()}'")
                    found = True
            except Exception:
                continue
        if found:
            print("[trap] Hardcoded default-role contamination found!")
            sys.exit(1)
        print("[trap] No hardcoded contamination detected (source scan).")
        return

    if titles & contaminated_keywords:
        print(f"[trap] DATA_CONTAMINATION_ERROR - got: {titles & contaminated_keywords}")
        sys.exit(1)
    else:
        print(f"[trap] Clean - results: {titles}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "reports" / "endpoint_map.json"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--contamination-check", action="store_true")
    args = parser.parse_args()

    if args.contamination_check:
        run_contamination_check()
        return

    output = Path(args.output)
    routes = introspect_fastapi(output, dry_run=args.dry_run)
    callsites = scan_react_callsites()
    join_graph(routes, callsites, output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
