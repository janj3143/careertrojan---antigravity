"""
FastAPI Introspection Exporter
- Imports your FastAPI app and exports:
  - endpoints_from_fastapi.json  (method/path/name/tags)
Usage:
  python tools/fastapi_introspect_routes.py --app-import "app.main:app" --out "./exports"
"""
import argparse, json, importlib
from datetime import datetime
from typing import Any, Dict, List

def import_app(app_import: str):
    mod_path, attr = app_import.split(":")
    mod = importlib.import_module(mod_path)
    return getattr(mod, attr)

def normalize_path(p: str) -> str:
    # Ensure /api prefix is preserved if your app sits behind /api in gateway
    return p

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-import", required=True, help="e.g. app.main:app")
    ap.add_argument("--out", required=True, help="output folder")
    args = ap.parse_args()

    app = import_app(args.app_import)

    endpoints: List[Dict[str, Any]] = []
    for r in getattr(app, "routes", []):
        methods = sorted(list(getattr(r, "methods", []) or []))
        path = getattr(r, "path", None)
        name = getattr(r, "name", None)
        tags = getattr(r, "tags", None)
        if not path or not methods:
            continue
        # ignore docs assets
        if path.startswith("/openapi") or path.startswith("/docs") or path.startswith("/redoc"):
            continue
        for m in methods:
            if m in ("HEAD", "OPTIONS"):
                continue
            endpoints.append({
                "method": m,
                "path": normalize_path(path),
                "name": name,
                "tags": tags or [],
            })

    out = {
        "generated": datetime.utcnow().strftime("%Y-%m-%d"),
        "source": args.app_import,
        "count": len(endpoints),
        "endpoints": sorted(endpoints, key=lambda x: (x["path"], x["method"]))
    }

    import os
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "endpoints_from_fastapi.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"[OK] Exported {len(endpoints)} routes -> {args.out}/endpoints_from_fastapi.json")

if __name__ == "__main__":
    main()
