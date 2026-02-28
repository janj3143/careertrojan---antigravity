"""
Purge garbage entries from learned_collocations.json (L: drive and local copies).
Keeps only valid phrases according to CollocationEngine._is_valid_phrase().
"""
import os
import sys
import json
import re
from pathlib import Path

# --- Quality gate logic (must match CollocationEngine._is_valid_phrase) ---
_VALID_PHRASE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9 &/'-]{2,80}[a-zA-Z0-9]$")
def is_valid_phrase(phrase):
    if not isinstance(phrase, str):
        return False
    if not (4 <= len(phrase) <= 80):
        return False
    if not _VALID_PHRASE_RE.match(phrase):
        return False
    alpha = sum(c.isalpha() for c in phrase)
    if alpha / max(len(phrase), 1) < 0.6:
        return False
    if '\\x00' in phrase or '\\x01' in phrase or '\\x02' in phrase:
        return False
    if len(phrase.split()) < 2:
        return False
    return True

# --- File locations ---
L_PATH = Path(r"L:/antigravity_version_ai_data_final/ai_data_final/gazetteers/learned_collocations.json")
LOCAL_PATHS = [
    Path("c:/careertrojan/data-mounts/learned_collocations.json"),
    Path("c:/careertrojan/ai_data_final/gazetteers/learned_collocations.json"),
]

# --- Purge function ---
def purge_file(path):
    if not path.exists():
        print(f"[SKIP] {path} does not exist.")
        return
    print(f"[PROCESS] {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            phrases = list(data.keys())
        elif isinstance(data, list):
            phrases = data
        else:
            print(f"[ERROR] Unknown format in {path}")
            return
        valid = [p for p in phrases if is_valid_phrase(p)]
        print(f"  Loaded: {len(phrases):,} | Valid: {len(valid):,} | Purged: {len(phrases)-len(valid):,}")
        # Write back as sorted list
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sorted(valid), f, indent=2, ensure_ascii=False)
        print(f"  [OK] Cleaned file written: {path}")
    except Exception as e:
        print(f"[ERROR] Failed to process {path}: {e}")

if __name__ == "__main__":
    purge_file(L_PATH)
    for p in LOCAL_PATHS:
        purge_file(p)
    print("Done.")
