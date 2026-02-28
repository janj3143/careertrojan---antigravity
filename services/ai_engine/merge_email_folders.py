#!/usr/bin/env python3
"""
merge_email_folders.py
======================
Reads both email source directories, lists all files, identifies
duplicates by filename, and copies any unique files from emails/
into email_extracted/.

Source dirs:
  L:\antigravity_version_ai_data_final\ai_data_final\emails\
  L:\antigravity_version_ai_data_final\ai_data_final\email_extracted\

Usage:
    python merge_email_folders.py
"""

import os
import shutil
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────
DATA_ROOT = Path(os.getenv("CAREERTROJAN_AI_DATA", os.path.join(os.getenv("CAREERTROJAN_DATA_ROOT", "./data"), "ai_data_final")))
EMAILS_DIR = DATA_ROOT / "emails"
EMAIL_EXTRACTED_DIR = DATA_ROOT / "email_extracted"


def list_files(directory: Path) -> dict[str, Path]:
    """Return {filename: full_path} for every file directly in *directory*."""
    result: dict[str, Path] = {}
    if not directory.exists():
        print(f"  WARNING: directory does not exist: {directory}")
        return result
    for entry in directory.iterdir():
        if entry.is_file():
            result[entry.name] = entry
    return result


def main() -> None:
    print("=" * 70)
    print("  Email Folder Merge Utility")
    print("=" * 70)

    # ── 1. List files in each directory ────────────────────────────────────
    print(f"\nScanning: {EMAILS_DIR}")
    emails_files = list_files(EMAILS_DIR)
    print(f"  Files found: {len(emails_files)}")
    for name in sorted(emails_files):
        print(f"    • {name}  ({emails_files[name].stat().st_size:,} bytes)")

    print(f"\nScanning: {EMAIL_EXTRACTED_DIR}")
    extracted_files = list_files(EMAIL_EXTRACTED_DIR)
    print(f"  Files found: {len(extracted_files)}")
    for name in sorted(extracted_files):
        print(f"    • {name}  ({extracted_files[name].stat().st_size:,} bytes)")

    # ── 2. Identify duplicates and unique files ────────────────────────────
    duplicates = sorted(set(emails_files) & set(extracted_files))
    unique_to_emails = sorted(set(emails_files) - set(extracted_files))
    unique_to_extracted = sorted(set(extracted_files) - set(emails_files))

    print("\n" + "-" * 70)
    print(f"Duplicates (same filename in both dirs): {len(duplicates)}")
    for name in duplicates:
        src_size = emails_files[name].stat().st_size
        dst_size = extracted_files[name].stat().st_size
        tag = "SAME SIZE" if src_size == dst_size else f"DIFFER ({src_size:,} vs {dst_size:,})"
        print(f"    • {name}  [{tag}]")

    print(f"\nUnique to emails/: {len(unique_to_emails)}")
    for name in unique_to_emails:
        print(f"    • {name}")

    print(f"\nUnique to email_extracted/: {len(unique_to_extracted)}")
    for name in unique_to_extracted:
        print(f"    • {name}")

    # ── 3. Copy unique files from emails/ → email_extracted/ ───────────────
    copied = 0
    if unique_to_emails:
        print("\n" + "-" * 70)
        print("Copying unique files from emails/ → email_extracted/ ...")
        for name in unique_to_emails:
            src = emails_files[name]
            dst = EMAIL_EXTRACTED_DIR / name
            shutil.copy2(src, dst)
            print(f"    COPIED: {name}")
            copied += 1
    else:
        print("\nNo unique files to copy — emails/ is a subset of email_extracted/.")

    # ── 4. Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  emails/ files:              {len(emails_files)}")
    print(f"  email_extracted/ files:     {len(extracted_files)}")
    print(f"  Duplicates (by filename):   {len(duplicates)}")
    print(f"  Unique to emails/:          {len(unique_to_emails)}")
    print(f"  Unique to email_extracted/: {len(unique_to_extracted)}")
    print(f"  Files copied:               {copied}")
    print("=" * 70)


if __name__ == "__main__":
    main()
