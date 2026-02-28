"""
CareerTrojan — Schema Adapter
==============================
Bridges the REAL data schemas in ai_data_final/ with the normalised
record format expected by the trainer pipeline.

Problem solved:
  profiles/         → has "Qualifications", "Career Summary", "Personal Details"
  cv_files/         → has "skills" (list), "education" (list[dict]), "experience" (list[dict])
  parsed_resumes/   → has "job_titles" (list), "skills" (list), "companies" (list)
  parsed_from_automated/ → same as parsed_resumes
  core_databases/   → has "Job Title", "Company", "Firstname", "Surname"

All trainers expect:
  text, job_title, skills (list[str]), experience_years (int),
  education (str), industry (str), salary (float|None)

This module normalises ANY of those schemas into a unified record.

Author: CareerTrojan System
Date: February 2026
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SchemaAdapter")

# ── Industry keyword maps ────────────────────────────────────────────────

_INDUSTRY_KEYWORDS = {
    "Oil & Gas": [
        "oil", "gas", "petroleum", "drilling", "subsea", "offshore",
        "upstream", "downstream", "midstream", "refinery", "pipeline",
        "wellhead", "completions", "reservoir", "lng", "fpso",
    ],
    "Technology": [
        "software", "developer", "programmer", "data scientist", "devops",
        "cloud", "sre", "frontend", "backend", "machine learning", "ai",
        "python", "java", "react", "kubernetes", "aws", "azure",
    ],
    "Finance": [
        "accountant", "financial", "analyst", "banker", "investment",
        "actuarial", "compliance", "audit", "treasury", "risk",
        "hedge fund", "private equity", "capital markets",
    ],
    "Engineering": [
        "mechanical", "electrical", "civil", "structural", "chemical",
        "process engineer", "piping", "instrumentation", "control systems",
        "design engineer", "project engineer", "cad", "autocad",
    ],
    "Healthcare": [
        "doctor", "nurse", "physician", "medical", "healthcare",
        "pharmaceutical", "clinical", "hospital", "nhs", "patient",
    ],
    "Sales & Marketing": [
        "sales", "marketing", "business development", "account manager",
        "advertising", "brand", "digital marketing", "seo", "crm",
    ],
    "Human Resources": [
        "hr", "human resources", "recruiter", "talent", "payroll",
        "compensation", "benefits", "workforce", "staffing",
    ],
    "Construction": [
        "construction", "site manager", "quantity surveyor", "foreman",
        "scaffolding", "bricklayer", "plumber", "electrician",
    ],
    "Education": [
        "teacher", "professor", "instructor", "educator", "lecturer",
        "curriculum", "training", "academic",
    ],
    "Management": [
        "manager", "director", "executive", "chief", "head of",
        "vp", "vice president", "ceo", "cto", "cfo",
    ],
}

# ── Experience extraction regex ──────────────────────────────────────────

_EXPERIENCE_PATTERNS = [
    re.compile(r"(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", re.I),
    re.compile(r"(?:experience|exp)\s*[:\-–]?\s*(\d{1,2})\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"over\s+(\d{1,2})\s*(?:years?|yrs?)", re.I),
]

_EDUCATION_LEVEL_MAP = {
    "phd": "PhD", "doctorate": "PhD", "d.phil": "PhD",
    "msc": "Master", "mba": "Master", "master": "Master", "m.sc": "Master",
    "ma": "Master", "m.a": "Master", "m.eng": "Master",
    "bsc": "Bachelor", "ba": "Bachelor", "b.sc": "Bachelor",
    "b.eng": "Bachelor", "bachelor": "Bachelor", "degree": "Bachelor",
    "hnd": "HND", "hnc": "HNC", "diploma": "Diploma",
    "associate": "Associate", "nvq": "NVQ", "btec": "BTEC",
    "a-level": "A-Level", "gcse": "GCSE", "high school": "High School",
}


def _extract_experience_years(text: str) -> int:
    """Extract years of experience from free text."""
    for pat in _EXPERIENCE_PATTERNS:
        m = pat.search(text)
        if m:
            return int(m.group(1))
    return 0


def _extract_education_level(text: str) -> str:
    """Return highest education level found in text."""
    text_lower = text.lower()
    # Check from highest to lowest
    priority = ["PhD", "Master", "Bachelor", "HND", "HNC", "Diploma",
                "Associate", "NVQ", "BTEC", "A-Level", "GCSE", "High School"]
    for level in priority:
        for keyword, mapped in _EDUCATION_LEVEL_MAP.items():
            if mapped == level and keyword in text_lower:
                return level
    return "Unknown"


def _infer_industry(text: str) -> str:
    """Infer industry from text using keyword scoring."""
    text_lower = text.lower()
    scores: Dict[str, int] = {}
    for industry, keywords in _INDUSTRY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[industry] = score
    if scores:
        return max(scores, key=scores.get)
    return "Unknown"


def _extract_skills_from_text(text: str) -> List[str]:
    """Simple skill extraction from free text using known patterns."""
    skills = set()
    text_lower = text.lower()

    # Known high-value terms
    known = [
        "python", "java", "javascript", "react", "angular", "vue",
        "sql", "postgresql", "mysql", "mongodb", "redis",
        "docker", "kubernetes", "aws", "azure", "gcp",
        "machine learning", "deep learning", "data analysis",
        "project management", "agile", "scrum",
        "excel", "word", "powerpoint", "sharepoint",
        "autocad", "solidworks", "matlab", "sap",
        "leadership", "team management", "budgeting",
        "health and safety", "risk assessment", "iso 9001",
        "six sigma", "lean manufacturing", "kaizen",
        "business development", "account management", "negotiation",
        "compliance", "audit", "financial analysis",
        "recruitment", "talent acquisition", "onboarding",
    ]
    for skill in known:
        if skill in text_lower:
            skills.add(skill.title())
    return sorted(skills)


def _extract_job_titles_from_career_summary(text: str) -> List[str]:
    """Extract job title-like phrases from Career Summary text."""
    titles = []
    # Look for patterns like "Position: ...", role names at start of lines
    patterns = [
        re.compile(r"(?:position|role|title|job)\s*[:\-–]\s*(.+?)(?:\n|$)", re.I),
        re.compile(r"(?:^|\n)\s*([A-Z][A-Za-z\s&/]+(?:Manager|Engineer|Director|Analyst|Consultant|Supervisor|Coordinator|Officer|Specialist|Lead|Executive|Administrator))", re.M),
    ]
    for pat in patterns:
        for m in pat.finditer(text):
            title = m.group(1).strip()[:80]
            if len(title) > 3:
                titles.append(title)
    return titles[:5]


# ══════════════════════════════════════════════════════════════════════════
# Public adapter functions — one per source schema
# ══════════════════════════════════════════════════════════════════════════

def adapt_profile(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    """
    Adapt a record from ai_data_final/profiles/ (the real schema).

    Real fields: ID, Number, Firstname, Surname, DateOfBirth, Address,
                 Home Tel, Mobile Tel, Personal Details, Qualifications,
                 Career Summary, Comments, Created
    """
    # Build full text from all available text fields
    parts = []
    for field in ("Personal Details", "Qualifications", "Career Summary",
                  "Comments", "Firstname", "Surname", "Address"):
        val = data.get(field, "")
        if val and isinstance(val, str):
            parts.append(val)
    full_text = " ".join(parts).strip()

    # Job title: try Career Summary extraction, fall back to Comments
    career = data.get("Career Summary", "")
    titles = _extract_job_titles_from_career_summary(career)
    job_title = titles[0] if titles else ""

    # If no title found, try the comments field (recruiters often note the role)
    if not job_title:
        comments = data.get("Comments", "")
        titles = _extract_job_titles_from_career_summary(comments)
        job_title = titles[0] if titles else ""

    # Skills: extract from Qualifications + Career Summary
    quals = data.get("Qualifications", "")
    skills = _extract_skills_from_text(quals + " " + career)

    # Experience years: extract from Career Summary text
    experience_years = _extract_experience_years(career)

    # Education: from Qualifications
    education = _extract_education_level(quals)

    # Industry: from Career Summary + Qualifications
    industry = _infer_industry(career + " " + quals)

    return {
        "id": file_stem or str(data.get("ID", "")),
        "text": full_text,
        "job_title": job_title,
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "industry": industry,
        "salary": None,  # profiles never contain salary
        "source": "profile",
        # Preserve original rich fields
        "name": f"{data.get('Firstname', '')} {data.get('Surname', '')}".strip(),
        "qualifications_raw": quals,
        "career_summary_raw": career,
    }


def adapt_cv_file(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    """
    Adapt a record from ai_data_final/cv_files/.

    Real fields: cv_id, user_id, ingested_at, source, data_type,
                 enrichment_status, source_file, file_name, processed_date,
                 extraction_method, emails, phones, potential_names,
                 skills (list[str]), education (list[dict]),
                 experience (list[dict]), raw_text, text_length
    """
    raw_text = data.get("raw_text", "")

    # Skills — already a list of strings
    skills = data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    # Experience — list of dicts with "job_title", "raw_text"
    experience = data.get("experience", [])
    job_title = ""
    if experience and isinstance(experience, list):
        first = experience[0] if experience else {}
        job_title = first.get("job_title", "") if isinstance(first, dict) else ""

    # Education — list of dicts with "degree_level", "field", "raw_text"
    education_list = data.get("education", [])
    education = "Unknown"
    if education_list and isinstance(education_list, list):
        first_edu = education_list[0] if education_list else {}
        if isinstance(first_edu, dict):
            education = first_edu.get("degree_level", "Unknown")
    elif isinstance(education_list, str):
        education = _extract_education_level(education_list)

    # Experience years from raw text
    experience_years = _extract_experience_years(raw_text)

    # Industry from raw text
    industry = _infer_industry(raw_text)

    return {
        "id": file_stem or data.get("cv_id", ""),
        "text": raw_text,
        "job_title": job_title,
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "industry": industry,
        "salary": None,
        "source": "cv_file",
    }


def adapt_parsed_resume(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    """
    Adapt a record from ai_data_final/parsed_resumes/ or parsed_from_automated/.

    Real fields: source_file, file_hash, doc_type, raw_text, text_length,
                 job_titles (list[str]), skills (list[str]),
                 companies (list[str]), contact_info (dict),
                 parsed_at, file_extension, file_size_kb
    """
    # PIPELINE FIX: automated_parser_engine wraps its output in
    # {"extracted_data": {"text": "...", ...}}.  Unwrap so we can reach
    # the actual text and fields underneath.
    if "extracted_data" in data and isinstance(data["extracted_data"], dict):
        inner = data["extracted_data"]
        # Merge inner keys into data (inner wins on conflict, but keep
        # top-level metadata like file_hash, source_file, etc.)
        merged = {**data, **inner}
        merged.pop("extracted_data", None)
        data = merged

    raw_text = data.get("raw_text", data.get("text", ""))

    # job_titles is a list — take first as primary
    job_titles = data.get("job_titles", [])
    job_title = job_titles[0] if job_titles else ""

    skills = data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    experience_years = _extract_experience_years(raw_text)
    education = _extract_education_level(raw_text)
    industry = _infer_industry(raw_text)

    return {
        "id": file_stem or data.get("file_hash", ""),
        "text": raw_text,
        "job_title": job_title,
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "industry": industry,
        "salary": None,
        "source": "parsed_resume",
        "companies": data.get("companies", []),
        "doc_type": data.get("doc_type", "unknown"),
    }


def adapt_merged_candidate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapt a record from core_databases/Candidate_database_merged.json.

    Real fields: ID, Number, Firstname, Surname, DateOfBirth, Address,
                 Home Tel, Mobile Tel, Personal Email, Job Title, Company
                 (and sometimes Qualifications, Career Summary, Personal Details)
    """
    # Many merged records are minimal (just name/contact), some are rich
    parts = []
    for field in ("Firstname", "Surname", "Job Title", "Company",
                  "Personal Details", "Qualifications", "Career Summary",
                  "Comments", "Address"):
        val = data.get(field, "")
        if val and isinstance(val, str):
            parts.append(val)
    full_text = " ".join(parts).strip()

    job_title = data.get("Job Title", "")
    career = data.get("Career Summary", "")
    quals = data.get("Qualifications", "")

    # Extract skills from Qualifications + Career Summary if available
    skills = _extract_skills_from_text(quals + " " + career + " " + full_text)

    experience_years = _extract_experience_years(career + " " + full_text)
    education = _extract_education_level(quals + " " + full_text)
    industry = _infer_industry(full_text)

    return {
        "id": str(data.get("ID", "")),
        "text": full_text,
        "job_title": job_title,
        "skills": skills,
        "experience_years": experience_years,
        "education": education,
        "industry": industry,
        "salary": None,
        "source": "merged_db",
        "name": f"{data.get('Firstname', '')} {data.get('Surname', '')}".strip(),
        "company": data.get("Company", ""),
    }


def adapt_any(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    """
    Auto-detect the schema and route to the correct adapter.
    """
    # cv_files/ schema — has cv_id + extraction_method
    if "cv_id" in data or "extraction_method" in data:
        return adapt_cv_file(data, file_stem)

    # parsed_resumes / parsed_from_automated schema — has file_hash + job_titles
    if "file_hash" in data or "job_titles" in data:
        return adapt_parsed_resume(data, file_stem)

    # Profile schema — has "Career Summary" or "Qualifications" or "Personal Details"
    if any(k in data for k in ("Career Summary", "Qualifications", "Personal Details")):
        return adapt_profile(data, file_stem)

    # Merged DB schema — has "Job Title" (title case) + "Firstname"
    if "Job Title" in data or ("Firstname" in data and "Surname" in data):
        return adapt_merged_candidate(data)

    # Unknown schema — do best-effort
    raw_text = data.get("raw_text", data.get("text", data.get("body", "")))
    return {
        "id": file_stem or str(data.get("id", data.get("ID", ""))),
        "text": raw_text if isinstance(raw_text, str) else str(raw_text),
        "job_title": data.get("job_title", data.get("Job Title", "")),
        "skills": data.get("skills", []),
        "experience_years": _extract_experience_years(raw_text) if isinstance(raw_text, str) else 0,
        "education": _extract_education_level(raw_text) if isinstance(raw_text, str) else "Unknown",
        "industry": _infer_industry(raw_text) if isinstance(raw_text, str) else "Unknown",
        "salary": data.get("salary", None),
        "source": "unknown",
    }


# ══════════════════════════════════════════════════════════════════════════
# Batch loading helpers
# ══════════════════════════════════════════════════════════════════════════

def load_and_adapt_directory(
    directory: Path,
    limit: int = 50000,
    min_text_length: int = 50,
) -> List[Dict[str, Any]]:
    """
    Load all JSON files from a directory, auto-detect schema, adapt to
    the unified training format. Returns list of normalised records.
    """
    if not directory.exists():
        logger.warning("Directory not found: %s", directory)
        return []

    files = list(directory.glob("*.json"))
    logger.info("Loading from %s: %d files (limit %d)", directory.name, len(files), limit)

    records = []
    errors = 0
    for f in files[:limit]:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # Handle files that contain an array of records
            if isinstance(data, list):
                for item in data:
                    rec = adapt_any(item, f.stem)
                    if len(rec.get("text", "")) >= min_text_length:
                        records.append(rec)
            else:
                rec = adapt_any(data, f.stem)
                if len(rec.get("text", "")) >= min_text_length:
                    records.append(rec)
        except Exception:
            errors += 1

    logger.info(
        "Loaded %d records from %s (%d files, %d errors)",
        len(records), directory.name, len(files[:limit]), errors,
    )
    return records


def load_merged_database(db_path: Path, limit: int = 50000) -> List[Dict[str, Any]]:
    """Load and adapt the merged candidate database."""
    if not db_path.exists():
        logger.warning("Merged database not found: %s", db_path)
        return []

    with open(db_path, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    if isinstance(candidates, dict):
        candidates = candidates.get("candidates", list(candidates.values()))

    records = []
    for c in candidates[:limit]:
        rec = adapt_merged_candidate(c)
        if len(rec.get("text", "")) >= 30:
            records.append(rec)

    logger.info("Loaded %d records from merged database", len(records))
    return records


def load_all_training_data(
    ai_data_dir: Path,
    limit_per_source: int = 20000,
    min_text_length: int = 50,
) -> List[Dict[str, Any]]:
    """
    Master loader: pulls from ALL data sources, deduplicates, and returns
    a unified training dataset. This is the single entry point trainers
    should use.

    Sources loaded (in priority order):
      1. cv_files/           — richest structured data
      2. parsed_resumes/     — deep-parsed CVs
      3. parsed_from_automated/ — bulk parsed documents (CVs + JDs)
      4. profiles/           — legacy profile records
      5. core_databases/Candidate_database_merged.json
    """
    all_records = []

    # 1. cv_files — richest data
    cv_dir = ai_data_dir / "cv_files"
    all_records.extend(load_and_adapt_directory(cv_dir, limit_per_source, min_text_length))

    # 2. parsed_resumes
    pr_dir = ai_data_dir / "parsed_resumes"
    all_records.extend(load_and_adapt_directory(pr_dir, limit_per_source, min_text_length))

    # 3. parsed_from_automated
    pa_dir = ai_data_dir / "parsed_from_automated"
    all_records.extend(load_and_adapt_directory(pa_dir, limit_per_source, min_text_length))

    # 4. profiles — with schema adaptation
    prof_dir = ai_data_dir / "profiles"
    all_records.extend(load_and_adapt_directory(prof_dir, limit_per_source, min_text_length))

    # 5. Merged database
    merged = ai_data_dir / "core_databases" / "Candidate_database_merged.json"
    all_records.extend(load_merged_database(merged, limit_per_source))

    # Deduplicate by text hash (keep first occurrence)
    import hashlib
    seen_hashes = set()
    unique = []
    for rec in all_records:
        h = hashlib.md5(rec["text"][:200].encode("utf-8", errors="replace")).hexdigest()
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(rec)

    logger.info(
        "Total training data: %d records (%d before dedup)",
        len(unique), len(all_records),
    )
    return unique
