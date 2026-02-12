"""
CareerTrojan - Diagnose FastAPI import and sample React callsites.
"""
import json
import re
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

print("=== FastAPI Import Diagnosis ===\n")

# Try the known path
candidates = [
    ("services.backend_api.main", "app"),
    ("services.shared_backend.main", "app"),
]

for mod_path, attr in candidates:
    print(f"Trying: {mod_path}.{attr}")
    try:
        parts = mod_path.rsplit(".", 1)
        module = __import__(parts[0], fromlist=[parts[1]])
        sub = getattr(module, parts[1])
        app = getattr(sub, attr, None)
        if app:
            route_count = sum(1 for r in app.routes if hasattr(r, "methods"))
            print(f"  SUCCESS - {route_count} routes found\n")
        else:
            print(f"  Module loaded but no '{attr}' attribute\n")
    except Exception as e:
        print(f"  FAILED: {type(e).__name__}: {e}")
        traceback.print_exc()
        print()

# Check what main.py actually contains
main_py = ROOT / "services" / "backend_api" / "main.py"
if main_py.exists():
    print(f"\n=== {main_py} (first 50 lines) ===")
    lines = main_py.read_text(encoding="utf-8", errors="ignore").splitlines()[:50]
    for i, line in enumerate(lines, 1):
        print(f"  {i:3}: {line}")
else:
    print(f"\n{main_py} NOT FOUND")

# Check for __init__.py files needed for import
print("\n=== Module init files ===")
for check in [
    ROOT / "services" / "__init__.py",
    ROOT / "services" / "backend_api" / "__init__.py",
]:
    exists = check.exists()
    icon = "OK" if exists else "MISSING"
    print(f"  [{icon}] {check}")

# Sample React callsite URLs
print("\n=== Sample React API callsites (first 20) ===")
pattern = re.compile(
    r"""(?:fetch|axios\.(?:get|post|put|patch|delete)|api\.(?:get|post|put|patch|delete)|baseURL|apiUrl|API_URL|endpoint|url)\s*[:=(\s]+\s*[`"']([^`"'\s][^`"']*)[`"']""",
    re.IGNORECASE,
)

samples = []
for portal in ("admin", "user", "mentor"):
    src = ROOT / "apps" / portal / "src"
    if not src.exists():
        continue
    for f in src.rglob("*.ts*"):
        if "node_modules" in str(f):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in pattern.finditer(content):
            url = m.group(1)
            if "/" in url and not url.startswith("//"):
                samples.append({
                    "portal": portal,
                    "file": str(f.relative_to(ROOT)),
                    "url": url,
                })
                if len(samples) >= 40:
                    break
        if len(samples) >= 40:
            break

# Deduplicate URLs and show
seen_urls = {}
for s in samples:
    if s["url"] not in seen_urls:
        seen_urls[s["url"]] = s

for i, (url, s) in enumerate(list(seen_urls.items())[:20], 1):
    print(f"  {i:2}. [{s['portal']}] {url}")
    print(f"       {s['file']}")

print(f"\nTotal unique URL patterns found: {len(seen_urls)}")
