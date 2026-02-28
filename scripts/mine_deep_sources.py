#!/usr/bin/env python3
"""
Deep Source Miner
=================
Mines ALL data sources that the original scripts missed:

1. ESCO dataset CSVs (automated_parser/)   → 3,039 occupations + 13,939 skills
2. Job title JSONs (ai_data_final/job_titles/) → 357 categorized titles
3. ai_data_final subdirectories (parsed_from_automated/, enrichment_results/, etc.)
4. collocation data.txt (automated_parser/)

This script covers the gaps: merge_mined_gazetteers.py was static/hardcoded,
and mine_internal_data.py only scanned root-level JSONs in ai_data_final/.

Usage:
    python scripts/mine_deep_sources.py [--dry-run]
"""
import csv, json, os, re, shutil, sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ─── PATHS ────────────────────────────────────────────────────────────────────
AI_DATA_DIR = Path(r"L:\antigravity_version_ai_data_final\ai_data_final")
PARSER_DIR  = Path(r"L:\antigravity_version_ai_data_final\automated_parser")
GAZ_DIR     = AI_DATA_DIR / "gazetteers"
GAZ_LOCAL   = Path(r"C:\careertrojan\data\ai_data_final\gazetteers")
ESCO_DIR    = PARSER_DIR / "ESCO dataset - v1.2.1 - classification - en - csv"

DRY_RUN = "--dry-run" in sys.argv

# ─── CATEGORY MAPPING for job_titles/*.json ───────────────────────────────────
JOB_TITLE_CATEGORY_TO_GAZ = {
    "Engineering & Technical": "job_titles.json",
    "Finance & Accounting":   "job_titles.json",
    "Hospitality & Service":  "job_titles.json",
    "Legal & Compliance":     "job_titles.json",
    "Management & Leadership":"job_titles.json",
    "Sales & Marketing":      "job_titles.json",
    "Science & Research":     "job_titles.json",
    "Technology & IT":        "job_titles.json",
    "Other":                  "job_titles.json",
}

# ─── ESCO SKILL TYPE → GAZETTEER MAPPING ─────────────────────────────────────
# ESCO skillType can be "skill/competence" or "knowledge"
# We classify based on the preferredLabel content
SKILL_CLASSIFY_PATTERNS = {
    "tech_skills.json": [
        r"programming|software|database|network|cyber|cloud|server|web\b",
        r"machine learning|artificial intelligence|data\s+\w+ing",
        r"computer|digital|system\s+admin|devops|automation|api\b",
        r"algorithm|blockchain|iot\b|robotic",
    ],
    "soft_skills.json": [
        r"communication|leadership|teamwork|coaching|mentoring",
        r"negotiat|motivat|empathy|listen|conflict|collaborat",
        r"problem.?solving|critical thinking|decision|present",
        r"adaptab|resilience|interpersonal",
    ],
    "methodologies.json": [
        r"agile|lean\b|kanban|six sigma|quality\s+management",
        r"project management|risk\s+management|change\s+management",
        r"continuous improvement|root cause|audit|compliance",
        r"assessment|analysis method|testing method",
    ],
    "certifications.json": [
        r"certif|accredit|license|iso\s+\d|qualification",
    ],
    "industry_terms.json": [
        r"manufactur|logistics|supply chain|procurement|retail",
        r"banking|insurance|real estate|telecom|energy|mining",
        r"healthcare|pharmaceutical|agriculture|construction",
        r"marketing|advertising|media|publishing|tourism",
    ],
    "oil_gas.json": [
        r"petroleum|refin|drilling|reservoir|subsea|offshore|pipeline",
        r"wellhead|blowout|cement|fracking|lng\b|upstream|downstream",
    ],
    "biotech_pharma.json": [
        r"pharma|biotech|clinical|drug|therapeutic|molecular|gene",
        r"biolog|biochem|immunolog|microbiol|epidemiol",
    ],
    "engineering.json": [
        r"mechanical|structural|civil|weld|metallurg|materials?\s+science",
        r"thermodynamic|fluid\s+mechanic|stress\s+analysis|corrosion",
    ],
    "manufacturing.json": [
        r"cnc|machining|injection\s+mold|assembly|production\s+line",
        r"tooling|casting|forging|stamping|extrusion|3d\s+print",
    ],
    "financial_services.json": [
        r"accounting|underwriting|actuarial|credit\s+risk|portfolio",
        r"investment\s+bank|asset\s+management|compliance\s+officer",
    ],
    "marketing.json": [
        r"seo|content\s+market|social\s+media\s+market|brand\s+strategy",
        r"digital\s+market|email\s+market|influencer",
    ],
    "hr_recruitment.json": [
        r"recruit|talent\s+acqui|onboard|workforce\s+plan|employee\s+engag",
        r"performance\s+apprais|compensation|succession\s+plan",
    ],
}


def normalize(term: str) -> str:
    return " ".join(term.lower().strip().split())


def is_valid_term(term: str, strict: bool = False) -> bool:
    n = normalize(term)
    words = n.split()
    if len(words) < 2 or len(n) < 6:
        return False
    if re.match(r"^[\d\s.,-]+$", n):
        return False
    if any(c in n for c in ["@", "http", "www.", "\\", "//", ".com", ".org"]):
        return False
    if len(words) > 5:
        return False
    # Skip generic ESCO verb-object patterns
    GENERIC_VERBS = (
        "use", "manage", "apply", "perform", "ensure", "maintain", "carry out",
        "work with", "provide", "support", "handle", "develop", "create",
        "prepare", "plan", "check", "identify", "select", "set up", "show",
        "follow", "keep", "make", "take", "deal with", "do", "give",
        "operate", "monitor", "assess", "evaluate", "advise on", "cooperate",
        "coordinate", "liaise", "report", "review", "organise", "organize",
        "arrange", "assist", "help", "attend", "deliver"
    )
    if re.match(r"^(" + "|".join(re.escape(v) for v in GENERIC_VERBS) + r")\s", n):
        return False
    # Skip single-letter words mixed terms
    if any(len(w) == 1 for w in words):
        return False
    # Strict mode: require at least one capitalized domain word or be 3+ words
    if strict:
        if len(words) < 2:
            return False
        # Must look like a proper noun or technical term
        if not re.search(r"[A-Z]", term) and len(words) < 3:
            return False
    return True


# Per-gazetteer cap to prevent bloat
MAX_NEW_PER_GAZ = 600


def classify_skill(label: str) -> str | None:
    n = normalize(label)
    for gaz_file, patterns in SKILL_CLASSIFY_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, n, re.IGNORECASE):
                return gaz_file
    return None


def load_existing_terms(gaz_dir: Path) -> dict[str, set[str]]:
    existing = {}
    all_terms = set()
    for f in gaz_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text("utf-8"))
            terms = set()
            for t in data.get("terms", []):
                terms.add(normalize(t))
            for k in data.get("abbreviations", {}):
                terms.add(normalize(k))
            existing[f.name] = terms
            all_terms |= terms
        except Exception:
            pass
    return existing, all_terms


def merge_into_gazetteer(gaz_path: Path, new_terms: list[str]) -> int:
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
    src = data.get("source", "")
    if "+deep_mine" not in src:
        data["source"] = src + "+deep_mine_esco_jobtitles_collocation"
    with open(gaz_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return len(added)


def mine_esco_occupations() -> dict[str, list[str]]:
    """Mine ESCO occupations_en.csv → job titles (preferredLabel only to avoid noise)."""
    results = defaultdict(list)
    csv_path = ESCO_DIR / "occupations_en.csv"
    if not csv_path.exists():
        print("  WARN: ESCO occupations CSV not found")
        return results

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("preferredLabel", "").strip()
            if label and is_valid_term(label):
                results["job_titles.json"].append(normalize(label))

    print(f"  ESCO occupations (preferredLabel only): {sum(len(v) for v in results.values())} terms")
    return results


def mine_esco_skills() -> dict[str, list[str]]:
    """Mine ESCO skills_en.csv → classify into appropriate gazetteers.
    Only preferredLabel, only terms that match a domain pattern (no catch-all dump)."""
    results = defaultdict(list)
    csv_path = ESCO_DIR / "skills_en.csv"
    if not csv_path.exists():
        print("  WARN: ESCO skills CSV not found")
        return results

    classified = 0
    skipped = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("preferredLabel", "").strip()
            if not label or not is_valid_term(label):
                continue
            n = normalize(label)
            gaz = classify_skill(label)
            if gaz:
                results[gaz].append(n)
                classified += 1
            else:
                skipped += 1  # Don't dump unclassified into industry_terms

    print(f"  ESCO skills: {classified} classified, {skipped} skipped (no domain match)")
    return results


def mine_esco_skill_groups() -> dict[str, list[str]]:
    """Mine ESCO skillGroups_en.csv for high-level skill categories."""
    results = defaultdict(list)
    csv_path = ESCO_DIR / "skillGroups_en.csv"
    if not csv_path.exists():
        return results

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row.get("preferredLabel", "").strip()
            if label and is_valid_term(label):
                gaz = classify_skill(label) or "industry_terms.json"
                results[gaz].append(normalize(label))

    print(f"  ESCO skill groups: {sum(len(v) for v in results.values())} terms")
    return results


def mine_job_title_jsons() -> dict[str, list[str]]:
    """Mine ai_data_final/job_titles/*.json for job title terms."""
    results = defaultdict(list)
    jt_dir = AI_DATA_DIR / "job_titles"
    if not jt_dir.exists():
        print("  WARN: job_titles directory not found")
        return results

    count = 0
    for f in sorted(jt_dir.glob("*.json")):
        if f.name == "databases" or f.name.startswith("."):
            continue
        try:
            data = json.loads(f.read_text("utf-8"))
            title = data.get("title", "").strip()
            if title and is_valid_term(title):
                results["job_titles.json"].append(normalize(title))
                count += 1
            # Also extract category if useful
            cat = data.get("category", "")
            if cat and is_valid_term(cat):
                results["industry_terms.json"].append(normalize(cat))
        except Exception:
            pass

    print(f"  Job title JSONs: {count} titles from {len(list(jt_dir.glob('*.json')))} files")
    return results


def mine_collocation_data() -> dict[str, list[str]]:
    """Mine collocation data.txt for multi-word professional terms."""
    results = defaultdict(list)
    txt_path = PARSER_DIR / "collocation data.txt"
    if not txt_path.exists():
        print("  WARN: collocation data.txt not found")
        return results

    try:
        text = txt_path.read_text("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN: Could not read collocation data.txt: {e}")
        return results

    # Extract multi-word terms: Title Case phrases, quoted phrases
    terms = set()
    for line in text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Quoted phrases
        for m in re.finditer(r'"([^"]{6,80})"', line):
            candidate = m.group(1)
            if is_valid_term(candidate):
                terms.add(normalize(candidate))
        # Title Case multi-word
        for m in re.finditer(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", line):
            candidate = m.group(1)
            if is_valid_term(candidate):
                terms.add(normalize(candidate))
        # Tab or comma separated terms (common in collocation files)
        for chunk in re.split(r"[\t,;|]", line):
            chunk = chunk.strip()
            if is_valid_term(chunk) and len(chunk.split()) >= 2:
                n = normalize(chunk)
                if not re.match(r"^[\d\s.,-]+$", n):
                    terms.add(n)

    # Classify
    classified = 0
    for term in terms:
        gaz = classify_skill(term)
        if gaz:
            results[gaz].append(term)
            classified += 1
        else:
            results["industry_terms.json"].append(term)

    print(f"  Collocation data: {len(terms)} terms ({classified} classified)")
    return results


def mine_subdirectory_jsons() -> dict[str, list[str]]:
    """Mine key ai_data_final subdirectories for terms."""
    results = defaultdict(list)
    subdirs = ["parsed_from_automated", "enrichment_results", "job_descriptions",
               "parsed_job_descriptions", "job_matches", "job_matching"]

    total = 0
    for subdir in subdirs:
        sub_path = AI_DATA_DIR / subdir
        if not sub_path.exists():
            continue
        file_count = 0
        for f in sub_path.glob("*.json"):
            if f.stat().st_size > 2_000_000:  # Skip files > 2MB
                continue
            file_count += 1
            if file_count > 100:  # Cap per directory
                break
            try:
                data = json.loads(f.read_text("utf-8"))
                terms = set()
                _extract_key_terms(data, terms, depth=0)
                for t in terms:
                    gaz = classify_skill(t) or "industry_terms.json"
                    results[gaz].append(t)
                    total += 1
            except Exception:
                pass

    print(f"  Subdirectory JSONs: {total} terms from {len(subdirs)} dirs")
    return results


def _extract_key_terms(value, terms: set, depth: int):
    """Extract key terms from JSON values, limited depth."""
    if depth > 3:
        return
    if isinstance(value, str):
        # Title Case multi-word
        for m in re.finditer(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", value):
            candidate = m.group(1)
            if is_valid_term(candidate):
                terms.add(normalize(candidate))
    elif isinstance(value, dict):
        # Interesting keys: title, skill, competence, certification, etc.
        interesting_keys = {"title", "skill", "skills", "competency", "competencies",
                           "certification", "certifications", "industry", "sector",
                           "methodology", "tool", "tools", "technology", "technologies",
                           "qualification", "role", "job_title", "position"}
        for k, v in value.items():
            if isinstance(v, str) and k.lower() in interesting_keys and is_valid_term(v):
                terms.add(normalize(v))
            elif isinstance(v, list) and k.lower() in interesting_keys:
                for item in v:
                    if isinstance(item, str) and is_valid_term(item):
                        terms.add(normalize(item))
            _extract_key_terms(v, terms, depth + 1)
    elif isinstance(value, list):
        for item in value[:50]:  # Cap list items
            _extract_key_terms(item, terms, depth + 1)


def main():
    print("=" * 70)
    print("DEEP SOURCE MINER")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print("=" * 70)

    # 1. Load existing gazetteer state
    existing, all_known = load_existing_terms(GAZ_DIR)
    print(f"\n  Existing gazetteer terms: {len(all_known)}")

    # 2. Mine all sources
    print(f"\n--- Mining ESCO Occupations ({ESCO_DIR.name}) ---")
    all_results = defaultdict(list)

    for source_fn in [mine_esco_occupations, mine_esco_skills,
                      mine_esco_skill_groups, mine_job_title_jsons,
                      mine_collocation_data, mine_subdirectory_jsons]:
        print(f"\n--- {source_fn.__name__} ---")
        results = source_fn()
        for gaz_file, terms in results.items():
            all_results[gaz_file].extend(terms)

    # 3. Deduplicate against existing
    print(f"\n{'=' * 70}")
    print("DEDUP & MERGE")
    print(f"{'=' * 70}")

    total_new = 0
    total_added = 0
    for gaz_file in sorted(all_results.keys()):
        raw_terms = all_results[gaz_file]
        # Deduplicate
        unique_new = set()
        for t in raw_terms:
            n = normalize(t)
            if n not in all_known and is_valid_term(n):
                unique_new.add(n)

        if not unique_new:
            continue

        # Cap per gazetteer to prevent bloat
        if len(unique_new) > MAX_NEW_PER_GAZ:
            # Prefer shorter, more specific terms
            sorted_terms = sorted(unique_new, key=lambda x: (len(x.split()), len(x)))
            unique_new = set(sorted_terms[:MAX_NEW_PER_GAZ])

        total_new += len(unique_new)
        gaz_path = GAZ_DIR / gaz_file
        if gaz_path.exists():
            added = merge_into_gazetteer(gaz_path, list(unique_new))
            total_added += added
            # Add to all_known to prevent cross-file duplication
            all_known |= unique_new
            print(f"  {gaz_file:40s}  +{added:5d} new (from {len(raw_terms)} raw)")
        else:
            print(f"  {gaz_file:40s}  SKIP (file not found)")

    # 4. Sync to local
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

    # 5. Summary
    print(f"\n{'=' * 70}")
    print(f"  TOTAL UNIQUE NEW: {total_new}")
    print(f"  TOTAL ADDED:      {total_added}")
    if DRY_RUN:
        print("  (DRY RUN — no files modified)")
    print(f"{'=' * 70}")

    # 6. Final count
    if not DRY_RUN:
        print("\n  Final gazetteer counts:")
        grand_total = 0
        for f in sorted(GAZ_DIR.glob("*.json")):
            data = json.loads(f.read_text("utf-8"))
            count = len(data.get("terms", []))
            if not count:
                count = len(data.get("abbreviations", {}))
            grand_total += count
            print(f"    {f.name:40s}  {count:5d}")
        print(f"    {'GRAND TOTAL':40s}  {grand_total:5d}")


if __name__ == "__main__":
    main()
