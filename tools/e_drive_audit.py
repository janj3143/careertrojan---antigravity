"""
E: Drive Isolation Audit
Scans all project files under C:\careertrojan for any E:\ drive references.
Excludes vendored SDKs, data dumps, and caches.
"""
import os
import re
import sys

ROOT = r"C:\careertrojan"
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "trained_models",
    "ai_data_final", "Klayiyo - sdk", ".venv", "venv",
    "data-mounts"  # exclude raw data dumps - they have email content with RE:\"
}
EXTS = {".py", ".yaml", ".yml", ".env", ".toml", ".cfg", ".ini", ".json", ".md", ".txt", ".sh", ".ps1", ".bat"}

# Match actual E:\ drive paths (E:\something), not regex fragments or email "RE:\""
pattern = re.compile(r'(?<![R])E:\\[A-Za-z]')

hits = []
scanned = 0

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for f in filenames:
        ext = os.path.splitext(f)[1].lower()
        if ext not in EXTS:
            continue
        fp = os.path.join(dirpath, f)
        scanned += 1
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if pattern.search(line):
                        rel = os.path.relpath(fp, ROOT)
                        hits.append((rel, i, line.strip()[:150]))
        except Exception:
            pass

print("=" * 70)
print("  E: DRIVE ISOLATION AUDIT")
print("=" * 70)
print(f"  Root:    {ROOT}")
print(f"  Scanned: {scanned} files")
print(f"  Hits:    {len(hits)}")
print("-" * 70)

if hits:
    for rel, ln, txt in hits:
        print(f"  {rel}:{ln}")
        print(f"    {txt}")
        print()
else:
    print("  ** ZERO E:\\ drive references found in project code **")

print("=" * 70)

# Now check Python sys.path
print("\n  PYTHON sys.path CHECK")
print("-" * 70)
e_in_path = [p for p in sys.path if p.upper().startswith("E:")]
if e_in_path:
    for p in e_in_path:
        print(f"  WARNING: {p}")
else:
    print("  ** No E:\\ entries in Python sys.path **")

# Check env vars
print("\n  ENVIRONMENT VARIABLE CHECK")
print("-" * 70)
e_env = [(k, v) for k, v in os.environ.items() if "E:\\" in v or "e:\\" in v]
if e_env:
    for k, v in e_env:
        print(f"  {k} = {v[:120]}")
else:
    print("  ** No E:\\ drive references in environment variables **")

print("\n" + "=" * 70)
print("  AUDIT COMPLETE")
print("=" * 70)
