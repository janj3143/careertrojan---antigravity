"""
Purge learned_collocations.json — streaming cleanup
====================================================

The learned collocation file has ~1.3M garbage entries (corrupted binary
fragments, single-word tokens, control characters, etc.).  This script:

  1. Reads the JSON in a single pass
  2. Applies the same ``_is_valid_phrase()`` quality gate used at runtime
  3. Writes only valid phrases back to disk
  4. Creates a timestamped backup before overwriting

Usage:
    python purge_learned_collocations.py          # dry-run (default)
    python purge_learned_collocations.py --apply   # overwrite in-place
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ── Locate the learned collocations file ──────────────────────────────
_DATA_ROOT = Path(os.getenv(
    "CAREERTROJAN_DATA_ROOT",
    "./data",
))
LEARNED_PHRASES_PATH = _DATA_ROOT / "ai_data_final" / "gazetteers" / "learned_collocations.json"

# Also clean the local mirror if it exists
LOCAL_MIRROR = Path(r"C:\careertrojan\services\ai_engine\trained_models\gazetteers\learned_collocations.json")

# ── Quality gate (stricter than runtime — this is a one-time deep purge) ──
_VALID_PHRASE_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9 &/'-]{2,80}[a-zA-Z0-9]$")

_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "of", "in", "on", "at", "to",
    "for", "is", "it", "by", "as", "be", "was", "are", "this", "that",
    "from", "with", "will", "can", "has", "had", "have", "not", "no",
    "we", "you", "he", "she", "they", "its", "our", "your", "their",
    "all", "any", "some", "if", "so", "do", "did", "does", "been",
    "were", "being", "am", "would", "could", "should", "may", "might",
    "shall", "must", "very", "also", "just", "than", "then", "now",
    "here", "there", "when", "where", "how", "what", "which", "who",
    "whom", "whose", "why", "each", "every", "both", "such", "more",
    "most", "other", "into", "over", "after", "before", "between",
    "under", "above", "below", "up", "down", "out", "off", "about",
    "through", "during", "while", "until", "since", "because", "only",
    "get", "got", "set", "let", "per", "via", "etc", "new", "old",
})


def _is_valid_phrase_strict(phrase: str) -> bool:
    """Strict purge-grade quality gate for deep cleanup.

    Much stricter than the runtime gate — rejects:
      - All runtime rejects (too short, binary, single-word, etc.)
      - Phrases with > 5 words
      - Phrases where every word is a stop word
      - Phrases with duplicate words ("data data", "and and")
      - Phrases where no word is >= 4 chars (filters random letter combos)
      - Phrases starting or ending with a stop word
    """
    if not phrase or len(phrase) < 4 or len(phrase) > 80:
        return False
    if " " not in phrase:
        return False
    if not _VALID_PHRASE_RE.match(phrase):
        return False
    alpha = sum(1 for c in phrase if c.isalpha())
    if alpha < len(phrase) * 0.6:
        return False

    words = phrase.lower().split()
    # Max 5 words
    if len(words) > 5:
        return False
    # At least 2 words
    if len(words) < 2:
        return False
    # No duplicate words
    if len(set(words)) < len(words):
        return False
    # Not all stop words
    non_stop = [w for w in words if w not in _STOP_WORDS]
    if not non_stop:
        return False
    # At least one substantive word (>= 4 chars, not a stop word)
    if not any(len(w) >= 4 and w not in _STOP_WORDS for w in words):
        return False
    # First or last word shouldn't be a filler stop word
    # (allow "of", "and" in the middle: "director of engineering" is valid)
    filler_starts = {"a", "an", "the", "and", "or", "but", "is", "it", "be",
                     "was", "are", "were", "do", "did", "does", "has", "had",
                     "have", "we", "you", "he", "she", "they", "if", "so",
                     "will", "can", "would", "could", "should", "may", "might"}
    if words[0] in filler_starts or words[-1] in filler_starts:
        return False
    return True


# Methods worth keeping (curated sources, not random word pairs)
_KEEP_METHODS = frozenset({"skill_extract", "job_title_extract", "ngram", "nltk",
                           "cooccurrence", "manual"})


def _should_keep(key: str, meta: dict) -> bool:
    """Decide if a learned phrase survives the deep purge.

    Strategy:
    - PMI entries are ALL freq-1 noise from a single mining run.
      Discard them entirely — they're just adjacent word pairs.
    - For curated methods (skill_extract, job_title_extract, ngram, nltk,
      cooccurrence), apply the strict quality gate.
    """
    method = meta.get("method", "unknown")
    if method == "pmi":
        return False  # 1.07M entries, all freq=1 noise
    if method not in _KEEP_METHODS:
        return False
    return _is_valid_phrase_strict(key.lower().strip())


def purge(path: Path, apply: bool = False) -> dict:
    if not path.exists():
        print(f"  [SKIP] File not found: {path}")
        return {"skipped": True}

    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"\n  Reading {path}  ({size_mb:.1f} MB) ...")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    phrases = data.get("phrases", {})
    original_count = len(phrases)
    print(f"  Original entries: {original_count:,}")

    clean = {}
    for key, meta in phrases.items():
        if _should_keep(key, meta):
            clean[key] = meta

    kept = len(clean)
    removed = original_count - kept
    print(f"  Valid entries:    {kept:,}")
    print(f"  Garbage removed: {removed:,}")

    if apply:
        # Create timestamped backup
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f".bak_{ts}.json")
        shutil.copy2(path, backup_path)
        print(f"  Backup created:  {backup_path}")

        data["phrases"] = clean
        data["purge_metadata"] = {
            "purged_at": datetime.now().isoformat(),
            "original_entries": original_count,
            "kept_entries": kept,
            "removed_entries": removed,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)

        new_size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  Rewritten:       {new_size_mb:.1f} MB (was {size_mb:.1f} MB)")
    else:
        print("  [DRY-RUN] No changes written.  Pass --apply to overwrite.")

    return {
        "path": str(path),
        "original": original_count,
        "kept": kept,
        "removed": removed,
    }


def main():
    apply = "--apply" in sys.argv
    print("=" * 60)
    print("LEARNED COLLOCATIONS PURGE")
    print("=" * 60)
    if not apply:
        print("  Mode: DRY-RUN  (pass --apply to write changes)")
    else:
        print("  Mode: APPLY  (will overwrite files)")

    results = []
    for p in [LEARNED_PHRASES_PATH, LOCAL_MIRROR]:
        results.append(purge(p, apply))

    print("\n" + "=" * 60)
    print("SUMMARY")
    for r in results:
        if r.get("skipped"):
            continue
        print(f"  {r['path']}")
        print(f"    {r['original']:>10,} → {r['kept']:>10,}  (removed {r['removed']:,})")
    print("=" * 60)


if __name__ == "__main__":
    main()
