"""
CareerTrojan — React API Prefix Migration (Phase 4b)
Auto-discovers portal src directories and rewrites legacy API prefixes.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Migration rules ---
# Each rule: (regex_pattern, replacement, description)
RULES = [
    # Direct /v1/ without domain prefix → leave alone (already canonical if /api/X/v1)
    # Catch /api/v1/users → /api/users/v1
    (r'"/api/v1/(users|auth|profiles|sessions)', r'"/api/\1/v1', "Flatten /api/v1/{domain} → /api/{domain}/v1"),
    # Catch /api/v1/admin → /api/admin/v1
    (r'"/api/v1/(admin|mentor|payments|rewards|gdpr|shared|enrichment|matching|parsing|coaching|analytics|reports|notifications|settings|onboarding|search|upload|export|feedback|dashboard)',
     r'"/api/\1/v1', "Flatten /api/v1/{domain} → /api/{domain}/v1"),
    # Hardcoded localhost ports
    (r'http://localhost:(\d{4})/api/', r'/api/', "Remove hardcoded localhost port"),
    (r'http://127\.0\.0\.1:(\d{4})/api/', r'/api/', "Remove hardcoded 127.0.0.1 port"),
    # Legacy IntelliCV paths
    (r'/intellicv-api/', r'/api/', "Replace legacy /intellicv-api/ prefix"),
    (r'/intellicv/', r'/api/', "Replace legacy /intellicv/ prefix"),
]


def find_portal_src_dirs():
    """Auto-discover all src/ directories under apps/."""
    apps_dir = ROOT / "apps"
    if not apps_dir.exists():
        print(f"apps/ not found at {apps_dir}")
        return []

    src_dirs = []
    # Primary portals
    for portal in ("admin", "user", "mentor"):
        src = apps_dir / portal / "src"
        if src.exists():
            src_dirs.append(src)

    # Nested mentor sub-page src dirs
    mentor_pages = apps_dir / "mentor" / "src" / "pages"
    if mentor_pages.exists():
        for sub_src in mentor_pages.rglob("src"):
            if sub_src.is_dir() and "node_modules" not in str(sub_src):
                src_dirs.append(sub_src)

    # User components
    user_comp_src = apps_dir / "user" / "components" / "src"
    if user_comp_src.exists():
        src_dirs.append(user_comp_src)

    return src_dirs


def scan_and_migrate(check_only: bool = False) -> int:
    """Scan portal source files and apply migration rules. Returns count of changes."""
    src_dirs = find_portal_src_dirs()
    if not src_dirs:
        print("No portal src/ directories found. Nothing to migrate.")
        return 0

    total_changes = 0
    changed_files: list[str] = []

    for src_dir in src_dirs:
        print(f"Scanning: {src_dir}")
        for filepath in src_dir.rglob("*.ts*"):
            if "node_modules" in str(filepath):
                continue
            try:
                original = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            modified = original
            file_changes = 0

            for pattern, replacement, desc in RULES:
                new_text, count = re.subn(pattern, replacement, modified)
                if count > 0:
                    file_changes += count
                    modified = new_text
                    rel = filepath.relative_to(ROOT)
                    print(f"  [{rel}] {desc} ({count} hit{'s' if count > 1 else ''})")

            if file_changes > 0:
                total_changes += file_changes
                changed_files.append(str(filepath.relative_to(ROOT)))
                if not check_only:
                    filepath.write_text(modified, encoding="utf-8")

    # --- Report ---
    print(f"\n{'CHECK' if check_only else 'MIGRATION'} COMPLETE")
    print(f"  Files affected: {len(changed_files)}")
    print(f"  Total replacements: {total_changes}")

    if check_only and total_changes > 0:
        print("\n❌ Legacy prefixes detected. Run without --check to apply fixes.")
        return 1
    elif total_changes == 0:
        print("\n✅ All callsites already use canonical prefixes.")
    else:
        print("\n✅ All callsites migrated to canonical /api/{domain}/v1 prefixes.")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Migrate React API prefixes to canonical format")
    parser.add_argument("--check", action="store_true", help="Report only, do not modify files")
    args = parser.parse_args()
    sys.exit(scan_and_migrate(check_only=args.check))


if __name__ == "__main__":
    main()
