#!/usr/bin/env python3
"""
Internal Data Self-Miner
========================
Mines CareerTrojan's own ai_data_final JSON files to discover terms, job titles,
skills, and industry vocabulary that aren't yet in the gazetteers.

This is the "eat our own data" strategy: instead of only importing external glossaries,
we scan our own canonical data sources and extract unique multi-word terms, then merge
them into the appropriate gazetteers.

Sources mined:
  - career_advice.json           → soft_skills, methodologies
  - commute_analysis.json        → industry_terms
  - companies_clean_all.json     → industry_terms, job_titles
  - interview_questions.json     → soft_skills, tech_skills
  - job_market_data.json         → job_titles, tech_skills, industry_terms
  - skills_taxonomy.json         → tech_skills, soft_skills, certifications
  - salary_data.json             → job_titles, industry_terms
  - canonical_glossary.json      → ALL categories (fan-out)
  - call_script.json             → soft_skills
  - application_feedback.json    → soft_skills, tech_skills
  - ai_feedback.json             → methodologies, tech_skills

Usage:
    python scripts/mine_internal_data.py [--dry-run]
"""
import json, os, re, shutil, sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ─── PATHS ────────────────────────────────────────────────────────────────────
AI_DATA_DIR = Path(r"L:\antigravity_version_ai_data_final\ai_data_final")
GAZ_DIR = AI_DATA_DIR / "gazetteers"
GAZ_LOCAL = Path(r"C:\careertrojan\data\ai_data_final\gazetteers")

DRY_RUN = "--dry-run" in sys.argv

# ─── CATEGORY KEYWORDS ───────────────────────────────────────────────────────
# Maps keyword patterns to gazetteer filenames
CATEGORY_PATTERNS = {
    "tech_skills.json": [
        r"python|java\b|javascript|typescript|react|angular|vue|node\.?js",
        r"docker|kubernetes|aws|azure|gcp|terraform|ansible|jenkins",
        r"sql|postgresql|mongodb|redis|elasticsearch|graphql",
        r"machine learning|deep learning|neural network|data science",
        r"api|microservice|cloud|devops|ci.?cd|git\b",
        r"algorithm|framework|library|sdk|platform",
    ],
    "soft_skills.json": [
        r"leadership|communication|teamwork|collaboration|mentoring",
        r"problem.?solving|critical thinking|decision making|negotiation",
        r"presentation|interpersonal|analytical|organizational",
        r"adaptability|resilience|empathy|emotional intelligence",
    ],
    "job_titles.json": [
        r"manager|director|analyst|engineer|developer|designer|specialist",
        r"coordinator|supervisor|administrator|consultant|architect",
        r"officer|executive|assistant|technician|scientist|researcher",
    ],
    "industry_terms.json": [
        r"manufacturing|logistics|supply chain|procurement|operations",
        r"compliance|governance|audit|regulatory|quality assurance",
        r"strategy|business development|market|revenue|stakeholder",
    ],
    "certifications.json": [
        r"certified|certification|certificate|license|accreditation",
        r"iso \d+|pmp|scrum|itil|prince2|six sigma|aws certified",
    ],
    "methodologies.json": [
        r"agile|scrum|kanban|lean|waterfall|devops|test driven",
        r"risk assessment|root cause|failure mode|continuous improvement",
    ],
}


def normalize(term: str) -> str:
    """Lowercase, strip, collapse whitespace."""
    return " ".join(term.lower().strip().split())


def is_valid_term(term: str) -> bool:
    """A term must be 2+ words, 4+ chars, no garbage."""
    n = normalize(term)
    words = n.split()
    if len(words) < 2:
        return False
    if len(n) < 6:
        return False
    # Skip purely numeric, URLs, emails, file paths
    if re.match(r"^[\d\s.,-]+$", n):
        return False
    if any(c in n for c in ["@", "http", "www.", "\\", "//"]):
        return False
    # Skip if >6 words (likely a sentence, not a term)
    if len(words) > 6:
        return False
    return True


def classify_term(term: str) -> str | None:
    """Classify a term into a gazetteer category based on keyword patterns."""
    n = normalize(term)
    for gaz_file, patterns in CATEGORY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, n, re.IGNORECASE):
                return gaz_file
    return None


def extract_terms_from_value(value, terms: set):
    """Recursively extract candidate multi-word terms from JSON values."""
    if isinstance(value, str):
        # Split on common delimiters
        for chunk in re.split(r"[.!?\n;|]", value):
            chunk = chunk.strip()
            # Extract quoted phrases
            for m in re.finditer(r'"([^"]{4,80})"', chunk):
                candidate = m.group(1)
                if is_valid_term(candidate):
                    terms.add(normalize(candidate))
            # Extract capitalized multi-word phrases (Title Case terms)
            for m in re.finditer(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", chunk):
                candidate = m.group(1)
                if is_valid_term(candidate):
                    terms.add(normalize(candidate))
            # Extract uppercase abbreviation sequences
            for m in re.finditer(r"\b([A-Z]{2,6}(?:\s+[A-Z]{2,6})*)\b", chunk):
                candidate = m.group(1)
                if len(candidate) >= 4 and is_valid_term(candidate):
                    terms.add(normalize(candidate))
    elif isinstance(value, dict):
        # Extract keys that look like terms
        for k, v in value.items():
            if isinstance(k, str) and is_valid_term(k):
                terms.add(normalize(k))
            extract_terms_from_value(v, terms)
    elif isinstance(value, list):
        for item in value:
            extract_terms_from_value(item, terms)


def load_existing_terms(gaz_dir: Path) -> dict[str, set[str]]:
    """Load all existing gazetteer terms into a lookup."""
    existing = {}
    for f in gaz_dir.glob("*.json"):
        data = json.loads(f.read_text("utf-8"))
        terms = set()
        for t in data.get("terms", []):
            terms.add(normalize(t))
        for k in data.get("abbreviations", {}):
            terms.add(normalize(k))
        existing[f.name] = terms
    return existing


def mine_json_file(filepath: Path) -> set[str]:
    """Mine a single JSON file for candidate terms."""
    terms = set()
    try:
        data = json.loads(filepath.read_text("utf-8"))
        extract_terms_from_value(data, terms)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"  WARN: Could not parse {filepath.name}: {e}")
    return terms


def merge_into_gazetteer(gaz_path: Path, new_terms: list[str]) -> int:
    """Merge new terms into an existing gazetteer, return count added."""
    data = json.loads(gaz_path.read_text("utf-8"))
    existing = set(normalize(t) for t in data.get("terms", []))
    added = [t for t in new_terms if normalize(t) not in existing]

    if not added:
        return 0

    if DRY_RUN:
        return len(added)

    merged = sorted(existing | set(normalize(t) for t in added))
    data["terms"] = merged
    data["version"] = data.get("version", 1) + 1
    data["updated"] = datetime.now().strftime("%Y-%m-%d")
    data["source"] = data.get("source", "") + "+internal_self_mine"
    with open(gaz_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return len(added)


def main():
    print("=" * 70)
    print("INTERNAL DATA SELF-MINER")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print("=" * 70)

    # 1. Load existing gazetteer terms
    existing = load_existing_terms(GAZ_DIR)
    all_known = set()
    for terms in existing.values():
        all_known |= terms
    print(f"\n  Existing gazetteer terms: {len(all_known)}")

    # 2. Find curated JSON files in ai_data_final (exclude company DBs, gazetteers, raw uploads)
    SKIP_PATTERNS = {
        "companies_", "Companies_", "backfill_", "application_feedback",
        "user_", "resume_", "parsed_", "raw_", "test_", "debug_",
        "migration_", "report_", "log_", "cache_", "__",
    }
    data_files = []
    for f in AI_DATA_DIR.glob("*.json"):
        if any(f.name.startswith(p) for p in SKIP_PATTERNS):
            continue
        if f.stat().st_size > 5_000_000:  # Skip files > 5MB (likely company DBs)
            continue
        data_files.append(f)
    print(f"  Data files to mine: {len(data_files)}")

    # 3. Mine all files
    all_mined = set()
    per_file = {}
    for f in sorted(data_files):
        terms = mine_json_file(f)
        new_terms = terms - all_known
        if new_terms:
            per_file[f.name] = new_terms
            all_mined |= new_terms
            print(f"  {f.name:45s}  {len(terms):5d} raw  |  {len(new_terms):4d} new")

    print(f"\n  Total unique NEW candidates: {len(all_mined)}")

    # 4. Classify and merge
    categorized = defaultdict(list)
    unclassified = []

    for term in sorted(all_mined):
        cat = classify_term(term)
        if cat:
            categorized[cat].append(term)
        else:
            unclassified.append(term)

    print(f"\n  Categorized into gazetteers:")
    total_added = 0
    for gaz_file, terms in sorted(categorized.items()):
        gaz_path = GAZ_DIR / gaz_file
        if gaz_path.exists():
            added = merge_into_gazetteer(gaz_path, terms)
            total_added += added
            print(f"    {gaz_file:40s}  +{added:4d}")
        else:
            print(f"    {gaz_file:40s}  SKIP (file not found)")

    print(f"\n  Unclassified candidates: {len(unclassified)}")
    if unclassified and len(unclassified) <= 50:
        for t in sorted(unclassified)[:50]:
            print(f"    - {t}")

    # 5. Sync to local
    if not DRY_RUN and total_added > 0:
        print(f"\n  Syncing to {GAZ_LOCAL}...")
        os.makedirs(GAZ_LOCAL, exist_ok=True)
        count = 0
        for f in GAZ_DIR.iterdir():
            if f.is_file():
                dst = GAZ_LOCAL / f.name
                shutil.copy2(f, dst)
                count += 1
        print(f"  Synced {count} files.")

    print(f"\n{'=' * 70}")
    print(f"  TOTAL NEW TERMS ADDED: {total_added}")
    if DRY_RUN:
        print("  (DRY RUN — no files modified)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
