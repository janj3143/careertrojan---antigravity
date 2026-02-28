#!/usr/bin/env python3
"""
Deep Ingestion v3
=================
Phased deep-ingest utility that mines parser + ai_data_final sources and
merges extracted entries into collocation_data files.

- Uses canonical path resolution via CareerTrojanPaths
- Dry-run by default
- Writes run log + manifest summary on apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.paths import CareerTrojanPaths

TODAY = date.today().isoformat()
SOURCE_TAG = "deep-ingest-v3"

STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "have",
        "been",
        "into",
        "their",
        "about",
        "your",
        "will",
        "would",
        "could",
        "should",
        "they",
        "them",
        "our",
        "you",
        "are",
        "was",
        "were",
        "not",
    }
)

NOISE_RE = re.compile(r"^[\W_]+$")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+&'./-]{1,64}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}")


LABEL_TO_FILE = {
    "company": "companies.json",
    "job_title": "job_titles.json",
    "skill": "skills.json",
    "email": "emails.json",
    "phone": "phones.json",
    "keyword": "keywords.json",
}


@dataclass
class Entry:
    phrase: str
    label: str
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phrase": self.phrase,
            "label": self.label,
            "confidence": round(float(self.confidence), 4),
            "source": SOURCE_TAG,
            "created_at": TODAY,
        }


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def is_valid_phrase(text: str) -> bool:
    value = normalize(text)
    if len(value) < 2 or len(value) > 120:
        return False
    if NOISE_RE.match(value):
        return False
    if value in STOPWORDS:
        return False
    return True


def iter_text_from_json(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_text_from_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_text_from_json(item)


def make_entry(phrase: str, label: str, confidence: float = 0.8) -> Optional[Entry]:
    value = normalize(phrase)
    if not is_valid_phrase(value):
        return None
    return Entry(phrase=value, label=label, confidence=confidence)


def _extract_terms_from_text(text: str) -> List[Entry]:
    found: List[Entry] = []
    if not text:
        return found

    for email in EMAIL_RE.findall(text):
        item = make_entry(email, "email", 0.95)
        if item:
            found.append(item)

    for phone in PHONE_RE.findall(text):
        item = make_entry(phone, "phone", 0.9)
        if item:
            found.append(item)

    tokens = TOKEN_RE.findall(text)
    if not tokens:
        return found

    # n-gram style keyword capture (2-3 token phrases)
    lowered = [t.lower() for t in tokens]
    for n in (2, 3):
        for idx in range(0, len(lowered) - n + 1):
            phrase = " ".join(lowered[idx : idx + n])
            if any(tok in STOPWORDS for tok in phrase.split()):
                continue
            item = make_entry(phrase, "keyword", 0.72)
            if item:
                found.append(item)

    return found


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def mine_data_cloud_solutions(ai_data: Path, limit_files: int = 5000) -> List[Entry]:
    entries: List[Entry] = []
    root = ai_data / "data_cloud_solutions"
    if not root.exists():
        return entries

    count = 0
    for file_path in root.rglob("*.json"):
        try:
            payload = _load_json(file_path)
        except Exception:
            continue

        for text in iter_text_from_json(payload):
            entries.extend(_extract_terms_from_text(text))

        count += 1
        if count >= limit_files:
            break

    return entries


def mine_enhanced_job_titles_extended(ai_data: Path, limit_rows: int = 200000) -> List[Entry]:
    entries: List[Entry] = []
    candidate_files = [
        ai_data / "enhanced_job_titles_database.json",
        ai_data / "job_titles" / "enhanced_job_titles_database.json",
    ]

    for file_path in candidate_files:
        if not file_path.exists():
            continue
        try:
            payload = _load_json(file_path)
        except Exception:
            continue

        rows: Iterable[Any]
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("rows") or payload.get("data") or payload.values()
        else:
            rows = []

        count = 0
        for row in rows:
            if not isinstance(row, dict):
                continue
            title = row.get("job_title") or row.get("title") or row.get("name")
            if title:
                item = make_entry(str(title), "job_title", 0.92)
                if item:
                    entries.append(item)
            company = row.get("company") or row.get("employer")
            if company:
                item = make_entry(str(company), "company", 0.88)
                if item:
                    entries.append(item)
            skills = row.get("skills") or []
            if isinstance(skills, list):
                for skill in skills:
                    item = make_entry(str(skill), "skill", 0.85)
                    if item:
                        entries.append(item)

            count += 1
            if count >= limit_rows:
                break

    return entries


def mine_parsed_from_automated(paths: CareerTrojanPaths, limit_files: int = 10000) -> List[Entry]:
    entries: List[Entry] = []

    parser_roots = [
        paths.ai_data_final / "parsed_from_automated",
        paths.parser_root,
    ]

    scanned = 0
    for root in parser_roots:
        if not root.exists():
            continue

        # JSON mining
        for file_path in root.rglob("*.json"):
            try:
                payload = _load_json(file_path)
            except Exception:
                continue
            for text in iter_text_from_json(payload):
                entries.extend(_extract_terms_from_text(text))

            # known keys for company/title enrichment
            if isinstance(payload, dict):
                for key in ("company", "employer", "organization"):
                    if payload.get(key):
                        item = make_entry(str(payload[key]), "company", 0.86)
                        if item:
                            entries.append(item)
                for key in ("job_title", "title", "role"):
                    if payload.get(key):
                        item = make_entry(str(payload[key]), "job_title", 0.9)
                        if item:
                            entries.append(item)

            scanned += 1
            if scanned >= limit_files:
                return entries

        # CSV mining
        for file_path in root.rglob("*.csv"):
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            entries.extend(_extract_terms_from_text(text))
            scanned += 1
            if scanned >= limit_files:
                return entries

    return entries


def mine_text_glossaries_deep(paths: CareerTrojanPaths, limit_files: int = 200) -> List[Entry]:
    entries: List[Entry] = []

    candidate_dirs = [
        paths.app_root / "docs",
        paths.ai_data_final / "learning_library",
    ]
    scanned = 0
    for root in candidate_dirs:
        if not root.exists():
            continue
        for ext in ("*.md", "*.txt", "*.json"):
            for file_path in root.rglob(ext):
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                entries.extend(_extract_terms_from_text(text))
                scanned += 1
                if scanned >= limit_files:
                    return entries
    return entries


def mine_filename_companies_titles(paths: CareerTrojanPaths, limit_files: int = 20000) -> List[Entry]:
    entries: List[Entry] = []
    roots = [paths.parser_root, paths.ai_data_final / "parsed_cv_files", paths.ai_data_final / "cv_files"]

    company_hint_words = {"ltd", "limited", "plc", "inc", "llc", "group", "solutions"}

    scanned = 0
    for root in roots:
        if not root.exists():
            continue
        for file_path in root.rglob("*"):
            if not file_path.is_file():
                continue
            stem = normalize(file_path.stem.replace("_", " ").replace("-", " "))
            if not stem:
                continue

            words = stem.split()
            if len(words) >= 2:
                # crude title detection
                if any(word in {"engineer", "developer", "manager", "consultant", "analyst", "executive"} for word in words):
                    item = make_entry(stem, "job_title", 0.72)
                    if item:
                        entries.append(item)

                if any(word in company_hint_words for word in words):
                    item = make_entry(stem, "company", 0.7)
                    if item:
                        entries.append(item)

            scanned += 1
            if scanned >= limit_files:
                return entries

    return entries


def mine_ai_model_artefacts(paths: CareerTrojanPaths) -> List[Entry]:
    entries: List[Entry] = []
    models_root = paths.trained_models
    if not models_root.exists():
        return entries

    for file_path in models_root.rglob("*"):
        if not file_path.is_file():
            continue
        token = normalize(file_path.stem.replace("_", " "))
        item = make_entry(token, "keyword", 0.65)
        if item:
            entries.append(item)

    return entries


def load_collocation_file(path: Path) -> Tuple[List[Dict[str, Any]], Set[str]]:
    if not path.exists():
        return [], set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return [], set()

    if not isinstance(payload, list):
        return [], set()

    seen = set()
    rows: List[Dict[str, Any]] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        phrase = normalize(str(row.get("phrase") or ""))
        if phrase:
            seen.add(phrase)
            rows.append(row)
    return rows, seen


def merge_into_collocations(
    collocation_dir: Path,
    entries: List[Entry],
    apply: bool,
    verbose: bool = False,
) -> Dict[str, int]:
    collocation_dir.mkdir(parents=True, exist_ok=True)

    grouped: Dict[str, List[Entry]] = {}
    for entry in entries:
        grouped.setdefault(entry.label, []).append(entry)

    stats = Counter()

    for label, rows in grouped.items():
        target_name = LABEL_TO_FILE.get(label, f"{label}s.json")
        target_path = collocation_dir / target_name

        existing_rows, seen = load_collocation_file(target_path)
        merged = list(existing_rows)

        for item in rows:
            if item.phrase in seen:
                stats["skipped_existing"] += 1
                continue
            merged.append(item.to_dict())
            seen.add(item.phrase)
            stats["added"] += 1

        if apply:
            target_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
            if verbose:
                print(f"[WRITE] {target_path} ({len(merged)} records)")
        else:
            if verbose:
                print(f"[DRY] {target_path} (+{stats['added']} candidate additions)")

    stats["labels"] = len(grouped)
    stats["incoming"] = len(entries)
    return dict(stats)


def write_log(log_path: Path, payload: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def update_manifest(manifest_path: Path, results: Dict[str, Any], apply: bool) -> None:
    current = {}
    if manifest_path.exists():
        try:
            current = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            current = {}

    current["last_run"] = datetime.utcnow().isoformat() + "Z"
    current["source"] = SOURCE_TAG
    current["results"] = results

    if apply:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(current, indent=2), encoding="utf-8")


def dedupe_entries(entries: List[Entry]) -> List[Entry]:
    output: List[Entry] = []
    seen: Set[Tuple[str, str]] = set()
    for entry in entries:
        key = (entry.label, entry.phrase)
        if key in seen:
            continue
        seen.add(key)
        output.append(entry)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Deep ingest and collocation merge utility")
    parser.add_argument("--apply", action="store_true", help="Write merged collocation files")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--limit-files", type=int, default=10000, help="Per-phase file scan cap")
    args = parser.parse_args()

    started = time.time()
    paths = CareerTrojanPaths()

    collocation_dir = paths.ai_data_final / "collocation_data"
    log_path = paths.logs / "deep_ingest_v3_runs.jsonl"
    manifest_path = paths.ai_data_final / "metadata" / "deep_ingest_v3_manifest.json"

    phase_results: Dict[str, int] = {}
    all_entries: List[Entry] = []

    p1 = mine_data_cloud_solutions(paths.ai_data_final, limit_files=args.limit_files)
    phase_results["phase_1_data_cloud_solutions"] = len(p1)
    all_entries.extend(p1)

    p2 = mine_enhanced_job_titles_extended(paths.ai_data_final)
    phase_results["phase_2_enhanced_job_titles"] = len(p2)
    all_entries.extend(p2)

    p3 = mine_parsed_from_automated(paths, limit_files=args.limit_files)
    phase_results["phase_3_parsed_from_automated"] = len(p3)
    all_entries.extend(p3)

    p4 = mine_text_glossaries_deep(paths)
    phase_results["phase_4_text_glossaries"] = len(p4)
    all_entries.extend(p4)

    p5 = mine_filename_companies_titles(paths, limit_files=args.limit_files)
    phase_results["phase_5_filename_mining"] = len(p5)
    all_entries.extend(p5)

    p6 = mine_ai_model_artefacts(paths)
    phase_results["phase_6_model_artefacts"] = len(p6)
    all_entries.extend(p6)

    all_entries = dedupe_entries(all_entries)

    merge_stats = merge_into_collocations(
        collocation_dir=collocation_dir,
        entries=all_entries,
        apply=args.apply,
        verbose=args.verbose,
    )

    elapsed = round(time.time() - started, 3)
    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "apply": args.apply,
        "entries_total": len(all_entries),
        "phase_results": phase_results,
        "merge_stats": merge_stats,
        "elapsed_seconds": elapsed,
        "paths": {
            "ai_data_final": str(paths.ai_data_final),
            "parser_root": str(paths.parser_root),
            "collocation_dir": str(collocation_dir),
        },
    }

    write_log(log_path, result)
    update_manifest(manifest_path, result, apply=args.apply)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
