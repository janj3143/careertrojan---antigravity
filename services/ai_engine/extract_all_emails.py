#!/usr/bin/env python3
"""
extract_all_emails.py
=====================
Recursively scans JSON and text files across multiple data directories,
extracts email addresses via regex, deduplicates (case-insensitive),
prints the sorted list with a total count, and saves results to a
master JSON file.

Search directories:
  - parsed_resumes/
  - parsed_from_automated/
  - parsed_cv_files/
  - email_extracted/

Output:
  L:\antigravity_version_ai_data_final\ai_data_final\email_extracted\master_email_list.json

Usage:
    python extract_all_emails.py
"""

import json
import os
import re
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────
DATA_ROOT = Path(os.getenv("CAREERTROJAN_AI_DATA", os.path.join(os.getenv("CAREERTROJAN_DATA_ROOT", "./data"), "ai_data_final")))

SEARCH_DIRS = [
    DATA_ROOT / "parsed_resumes",
    DATA_ROOT / "parsed_from_automated",
    DATA_ROOT / "parsed_cv_files",
    DATA_ROOT / "email_extracted",
]

OUTPUT_FILE = DATA_ROOT / "email_extracted" / "master_email_list.json"

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# File extensions to scan
TEXT_EXTENSIONS = {".json", ".txt", ".csv", ".log", ".md", ".text"}

# Skip files larger than 10 MB (likely binary/garbage)
MAX_FILE_SIZE = 10 * 1024 * 1024


def extract_emails_from_file(filepath: Path) -> set[str]:
    """Read a file and return all email addresses found (lowercased)."""
    emails: set[str] = set()
    try:
        sz = filepath.stat().st_size
        if sz > MAX_FILE_SIZE or sz == 0:
            return emails
        # Read in binary mode (avoids codec hangs on weird files)
        raw = filepath.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        for match in EMAIL_REGEX.findall(text):
            emails.add(match.lower())
    except (OSError, PermissionError, MemoryError):
        pass  # silently skip unreadable files
    return emails


def _save_checkpoint(all_emails: set, dir_stats: dict, total_files: int, msg: str = "") -> None:
    """Save current progress to checkpoint file."""
    checkpoint = {
        "total_unique_emails": len(all_emails),
        "emails": sorted(all_emails),
        "per_directory_stats": dir_stats,
        "total_files_scanned": total_files,
        "checkpoint": True,
    }
    checkpoint_file = OUTPUT_FILE.parent / "email_extraction_checkpoint.json"
    try:
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2, ensure_ascii=False)
        if msg:
            print(f"  [CHECKPOINT] {msg} — {len(all_emails)} emails saved")
    except Exception as e:
        print(f"  [WARN] Checkpoint save failed: {e}")


def main() -> None:
    print("=" * 70)
    print("  Email Extraction Utility")
    print("=" * 70)

    all_emails: set[str] = set()
    total_files_scanned = 0
    files_with_emails = 0
    dir_stats: dict[str, dict] = {}

    try:
        for search_dir in SEARCH_DIRS:
            dir_name = search_dir.name
            print(f"\nScanning: {search_dir}")

            if not search_dir.exists():
                print(f"  WARNING: directory does not exist — skipping")
                dir_stats[dir_name] = {"exists": False, "files": 0, "emails_found": 0}
                continue

            dir_emails: set[str] = set()
            dir_files = 0
            skipped = 0

            try:
                for filepath in search_dir.rglob("*"):
                    if not filepath.is_file():
                        continue
                    if filepath.suffix.lower() not in TEXT_EXTENSIONS:
                        skipped += 1
                        continue
                    # Skip our own output file to avoid circular reads
                    if filepath == OUTPUT_FILE:
                        continue

                    dir_files += 1
                    total_files_scanned += 1
                    found = extract_emails_from_file(filepath)
                    if found:
                        files_with_emails += 1
                        dir_emails.update(found)

                    # Progress every 5000 files
                    if dir_files % 5000 == 0:
                        print(f"  ... {dir_files} text files scanned, {skipped} non-text skipped, {len(dir_emails)} emails so far")
                    
                    # Checkpoint every 10000 files
                    if total_files_scanned % 10000 == 0:
                        all_emails.update(dir_emails)
                        _save_checkpoint(all_emails, dir_stats, total_files_scanned, f"{total_files_scanned} files processed")

            except KeyboardInterrupt:
                print(f"\n  [INTERRUPTED] Saving progress...")
                all_emails.update(dir_emails)
                dir_stats[dir_name] = {
                    "exists": True, "files": dir_files, 
                    "emails_found": len(dir_emails), "skipped_non_text": skipped,
                    "interrupted": True,
                }
                _save_checkpoint(all_emails, dir_stats, total_files_scanned, "interrupted")
                raise

            all_emails.update(dir_emails)
            dir_stats[dir_name] = {
                "exists": True,
                "files": dir_files,
                "emails_found": len(dir_emails),
                "skipped_non_text": skipped,
            }
            print(f"  Files scanned: {dir_files}  (skipped {skipped} non-text)")
            print(f"  Unique emails in this dir: {len(dir_emails)}")
            
            # Save after each directory completes
            _save_checkpoint(all_emails, dir_stats, total_files_scanned, f"completed {dir_name}")

    except KeyboardInterrupt:
        print(f"\n[FINAL] Interrupted — checkpoint saved with {len(all_emails)} emails")
        return  # Exit early on interrupt

    # ── Sorted deduplicated list ───────────────────────────────────────────
    sorted_emails = sorted(all_emails)

    # Don't print all emails if there are too many
    print("\n" + "=" * 70)
    print(f"  TOTAL UNIQUE EMAILS: {len(sorted_emails)}")
    print("=" * 70)
    if len(sorted_emails) <= 100:
        for i, email in enumerate(sorted_emails, 1):
            print(f"  {i:4d}. {email}")
    else:
        print(f"  (Showing first 50 and last 50 of {len(sorted_emails)} emails)")
        for i, email in enumerate(sorted_emails[:50], 1):
            print(f"  {i:4d}. {email}")
        print("  ...")
        for i, email in enumerate(sorted_emails[-50:], len(sorted_emails) - 49):
            print(f"  {i:4d}. {email}")

    # ── Per-directory summary ──────────────────────────────────────────────
    print("\n" + "-" * 70)
    print("  PER-DIRECTORY SUMMARY")
    print("-" * 70)
    for dir_name, stats in dir_stats.items():
        status = "OK" if stats["exists"] else "MISSING"
        print(f"  {dir_name:30s}  [{status}]  files={stats['files']}  emails={stats['emails_found']}")
    print(f"\n  Total files scanned:    {total_files_scanned}")
    print(f"  Files containing emails: {files_with_emails}")
    print(f"  Total unique emails:     {len(sorted_emails)}")

    # ── Save to JSON ───────────────────────────────────────────────────────
    output = {
        "total_unique_emails": len(sorted_emails),
        "emails": sorted_emails,
        "source_directories": {k: str(SEARCH_DIRS[i]) for i, k in enumerate(dir_stats)},
        "per_directory_stats": dir_stats,
        "total_files_scanned": total_files_scanned,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to: {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
