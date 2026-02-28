"""
CareerTrojan — Schema Adapter
==============================
Normalizes heterogeneous record schemas from ai_data_final into a unified
training format consumed by model trainers.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("SchemaAdapter")


_INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "technology": ["software", "developer", "engineering", "cloud", "devops", "data"],
    "finance": ["finance", "bank", "trading", "accounting", "audit", "risk"],
    "healthcare": ["health", "medical", "nurse", "hospital", "clinical"],
    "education": ["education", "teacher", "lecturer", "training", "university"],
    "sales": ["sales", "account executive", "business development", "revenue"],
    "operations": ["operations", "logistics", "supply chain", "procurement"],
    "marketing": ["marketing", "seo", "campaign", "brand", "growth"],
}

_EXPERIENCE_PATTERNS = [
    re.compile(r"(\d{1,2})\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", re.I),
    re.compile(r"experience\s*[:\-]?\s*(\d{1,2})", re.I),
]

_EDUCATION_LEVEL_MAP = {
    "phd": "PhD",
    "doctorate": "PhD",
    "master": "Master",
    "msc": "Master",
    "mba": "Master",
    "bachelor": "Bachelor",
    "bsc": "Bachelor",
    "ba": "Bachelor",
    "hnd": "HND",
    "hnc": "HNC",
    "diploma": "Diploma",
    "associate": "Associate",
    "a-level": "A-Level",
    "gcse": "GCSE",
}


def _extract_experience_years(text: str) -> int:
    if not text:
        return 0
    for pattern in _EXPERIENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                return max(0, min(50, int(match.group(1))))
            except Exception:
                continue
    return 0


def _extract_education_level(text: str) -> str:
    haystack = (text or "").lower()
    for key, label in _EDUCATION_LEVEL_MAP.items():
        if key in haystack:
            return label
    return "Unknown"


def _infer_industry(text: str) -> str:
    haystack = (text or "").lower()
    if not haystack:
        return "unknown"
    scores: Dict[str, int] = {}
    for industry, keys in _INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for key in keys if key in haystack)
    top = max(scores, key=scores.get)
    return top if scores[top] > 0 else "unknown"


def _extract_skills_from_text(text: str) -> List[str]:
    if not text:
        return []
    common = {
        "python", "java", "javascript", "typescript", "sql", "postgresql",
        "aws", "azure", "docker", "kubernetes", "fastapi", "react",
        "tensorflow", "pytorch", "power bi", "excel", "salesforce",
        "leadership", "communication", "project management",
    }
    lower = text.lower()
    found = [skill for skill in common if skill in lower]
    return sorted(set(found))


def _extract_job_titles_from_career_summary(text: str) -> List[str]:
    if not text:
        return []
    candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", text)
    blocked = {"Curriculum Vitae", "United Kingdom", "Personal Statement"}
    titles = [c for c in candidates if c not in blocked and len(c.split()) <= 4]
    return titles[:5]


def _safe_text(*parts: Any) -> str:
    values: List[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, str):
            values.append(part)
        elif isinstance(part, (list, tuple)):
            values.extend(str(x) for x in part if x)
        elif isinstance(part, dict):
            values.extend(str(v) for v in part.values() if v)
        else:
            values.append(str(part))
    return "\n".join(v for v in values if v).strip()


def adapt_profile(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    summary = _safe_text(
        data.get("summary"),
        data.get("profile"),
        data.get("headline"),
        data.get("bio"),
        data.get("work_experience"),
    )
    skills = data.get("skills") or _extract_skills_from_text(summary)
    if isinstance(skills, str):
        skills = [skills]
    text = _safe_text(summary, data.get("education"), data.get("certifications"))
    exp_years = data.get("experience_years") or _extract_experience_years(text)
    education = data.get("education_level") or _extract_education_level(text)
    industry = data.get("industry") or _infer_industry(text)
    job_title = data.get("job_title") or data.get("title") or (file_stem.replace("_", " ") if file_stem else "")

    return {
        "source_type": "profile",
        "source_id": data.get("id") or file_stem,
        "text": text,
        "job_title": job_title,
        "skills": [str(s).strip().lower() for s in skills if str(s).strip()],
        "experience_years": int(exp_years) if str(exp_years).isdigit() else 0,
        "education": education,
        "industry": industry,
        "salary": data.get("salary_expectation") or data.get("salary") or None,
    }


def adapt_cv_file(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    raw_text = _safe_text(
        data.get("text"),
        data.get("content"),
        data.get("raw_text"),
        data.get("profile"),
        data.get("career_summary"),
    )
    titles = _extract_job_titles_from_career_summary(raw_text)
    job_title = data.get("job_title") or (titles[0] if titles else file_stem.replace("_", " "))
    skills = data.get("skills") or _extract_skills_from_text(raw_text)

    return {
        "source_type": "cv_file",
        "source_id": data.get("id") or file_stem,
        "text": raw_text,
        "job_title": job_title,
        "skills": [str(s).strip().lower() for s in skills if str(s).strip()],
        "experience_years": _extract_experience_years(raw_text),
        "education": _extract_education_level(raw_text),
        "industry": _infer_industry(raw_text),
        "salary": data.get("salary_expectation") or None,
    }


def adapt_parsed_resume(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    resume_text = _safe_text(
        data.get("resume_text"),
        data.get("parsed_text"),
        data.get("summary"),
        data.get("work_history"),
    )
    skills = data.get("skills") or _extract_skills_from_text(resume_text)
    title = data.get("target_role") or data.get("job_title") or file_stem.replace("_", " ")

    return {
        "source_type": "parsed_resume",
        "source_id": data.get("id") or file_stem,
        "text": resume_text,
        "job_title": title,
        "skills": [str(s).strip().lower() for s in skills if str(s).strip()],
        "experience_years": data.get("experience_years") or _extract_experience_years(resume_text),
        "education": data.get("education_level") or _extract_education_level(resume_text),
        "industry": data.get("industry") or _infer_industry(resume_text),
        "salary": data.get("salary") or data.get("salary_expectation"),
    }


def adapt_merged_candidate(data: Dict[str, Any]) -> Dict[str, Any]:
    text = _safe_text(
        data.get("text"),
        data.get("summary"),
        data.get("notes"),
        data.get("experience"),
        data.get("education"),
    )
    skills = data.get("skills") or _extract_skills_from_text(text)
    title = data.get("job_title") or data.get("current_title") or ""

    return {
        "source_type": "merged_candidate",
        "source_id": str(data.get("id") or data.get("candidate_id") or ""),
        "text": text,
        "job_title": title,
        "skills": [str(s).strip().lower() for s in skills if str(s).strip()],
        "experience_years": int(data.get("experience_years") or _extract_experience_years(text) or 0),
        "education": data.get("education_level") or _extract_education_level(text),
        "industry": data.get("industry") or _infer_industry(text),
        "salary": data.get("salary") or data.get("salary_expectation"),
    }


def adapt_any(data: Dict[str, Any], file_stem: str = "") -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {
            "source_type": "unknown",
            "source_id": file_stem,
            "text": str(data),
            "job_title": "",
            "skills": [],
            "experience_years": 0,
            "education": "Unknown",
            "industry": "unknown",
            "salary": None,
        }

    keys = set(k.lower() for k in data.keys())
    if {"work_experience", "skills"} & keys:
        return adapt_profile(data, file_stem=file_stem)
    if {"resume_text", "parsed_text", "work_history"} & keys:
        return adapt_parsed_resume(data, file_stem=file_stem)
    if {"content", "raw_text", "career_summary"} & keys:
        return adapt_cv_file(data, file_stem=file_stem)
    return adapt_merged_candidate(data)


def load_and_adapt_directory(
    directory: Path,
    limit: int = 50000,
    min_text_length: int = 50,
) -> List[Dict[str, Any]]:
    directory = Path(directory)
    if not directory.exists():
        logger.warning("Directory not found: %s", directory)
        return []

    records: List[Dict[str, Any]] = []
    json_files = list(directory.glob("*.json"))
    for file_path in json_files[:limit]:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            adapted = adapt_any(payload, file_stem=file_path.stem)
            if len((adapted.get("text") or "").strip()) >= min_text_length:
                records.append(adapted)
        except Exception as exc:
            logger.debug("Failed to adapt %s: %s", file_path, exc)
    return records


def load_merged_database(db_path: Path, limit: int = 50000) -> List[Dict[str, Any]]:
    db_path = Path(db_path)
    if not db_path.exists():
        logger.warning("Merged DB path not found: %s", db_path)
        return []

    records: List[Dict[str, Any]] = []
    try:
        data = json.loads(db_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for item in data[:limit]:
                records.append(adapt_merged_candidate(item if isinstance(item, dict) else {"text": str(item)}))
        elif isinstance(data, dict):
            rows = data.get("candidates") if isinstance(data.get("candidates"), list) else [data]
            for item in rows[:limit]:
                records.append(adapt_merged_candidate(item if isinstance(item, dict) else {"text": str(item)}))
    except Exception as exc:
        logger.warning("Failed loading merged database from %s: %s", db_path, exc)
    return records


def load_all_training_data(
    ai_data_path: Optional[Path] = None,
    limit_per_dir: int = 50000,
    min_text_length: int = 50,
) -> List[Dict[str, Any]]:
    base = Path(ai_data_path) if ai_data_path else Path.cwd() / "ai_data_final"

    candidate_dirs = [
        base / "profiles",
        base / "cv_files",
        base / "parsed_resumes",
        base / "parsed_cv_files",
        base / "parsed_from_automated",
    ]

    merged_paths = [
        base / "merged_candidates.json",
        base / "merged_database.json",
    ]

    records: List[Dict[str, Any]] = []
    for directory in candidate_dirs:
        records.extend(
            load_and_adapt_directory(
                directory=directory,
                limit=limit_per_dir,
                min_text_length=min_text_length,
            )
        )

    for merged_path in merged_paths:
        records.extend(load_merged_database(merged_path, limit=limit_per_dir))

    logger.info("Schema adapter loaded %d normalized records", len(records))
    return records
