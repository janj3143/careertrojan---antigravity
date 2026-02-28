"""
Shared training data loader for all model trainers.

Features
 - Reads both legacy profiles and parsed CV files (including cv_uploads when mounted)
 - Normalizes schemas into a single record shape
 - Extracts text, skills, education, experience, email, and phone
 - Provides helpers for feature vectors and text corpora
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

import numpy as np

from services.shared.paths import CareerTrojanPaths

logger = logging.getLogger("training_data_loader")


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}")


def _to_list(value) -> List:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text_join(parts: Iterable[str]) -> str:
    return " ".join([p for p in parts if p]).strip()


@dataclass
class TrainingRecord:
    """Canonical schema for training samples."""

    id: str
    source: str
    skills: List
    education: List
    work_experience: List
    job_title: str
    raw_text: str
    email: str
    phone: str
    years_experience: float
    industry: str
    raw: Dict

    def full_text(self) -> str:
        return _text_join([
            " ".join(map(str, self.skills)),
            " ".join(map(str, self.work_experience)),
            " ".join(map(str, self.education)),
            self.raw_text,
            self.email,
            self.phone,
        ])


class TrainingDataLoader:
    """Loads and normalizes training data for every trainer."""

    def __init__(self, limit_per_source: int | None = None):
        self.paths = CareerTrojanPaths()
        self.ai_data = self.paths.ai_data_final
        self.user_data = self.paths.user_data
        self.limit_per_source = limit_per_source or 50000

        self.sources: List[Tuple[str, Path, Callable[[Dict, str, Path], TrainingRecord]]] = [
            ("profiles", self.ai_data / "profiles", self._normalize_profile),
            ("parsed_resumes", self.ai_data / "parsed_resumes", self._normalize_resume_like),
            ("cv_files", self.ai_data / "cv_files", self._normalize_resume_like),
            ("cv_uploads", self.user_data / "cv_uploads", self._normalize_resume_like),
        ]

    def _extract_email(self, text: str) -> str:
        if not text:
            return ""
        match = EMAIL_RE.search(text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        if not text:
            return ""
        match = PHONE_RE.search(text)
        return match.group(0).strip() if match else ""

    def _normalize_profile(self, profile: Dict, source: str, path: Path) -> TrainingRecord:
        qualifications = profile.get("Qualifications") or ""
        career_summary = profile.get("Career Summary") or ""
        personal_details = profile.get("Personal Details") or ""

        skills = _to_list(profile.get("skills"))
        education = _to_list(profile.get("education"))
        work_experience = _to_list(profile.get("work_experience"))

        if qualifications:
            education.append(qualifications)
        if career_summary:
            work_experience.append(career_summary)

        text_blob = _text_join([
            personal_details,
            qualifications,
            career_summary,
            profile.get("raw_text", ""),
        ])

        email = profile.get("email") or self._extract_email(text_blob)
        phone = profile.get("phone") or self._extract_phone(text_blob)

        return TrainingRecord(
            id=path.stem,
            source=source,
            skills=skills,
            education=education,
            work_experience=work_experience,
            job_title=str(profile.get("job_title") or profile.get("Job Title") or ""),
            raw_text=text_blob,
            email=email,
            phone=phone,
            years_experience=float(profile.get("years_experience") or profile.get("experience_years") or 0),
            industry=str(profile.get("industry") or ""),
            raw=profile,
        )

    def _normalize_resume_like(self, resume: Dict, source: str, path: Path) -> TrainingRecord:
        raw_text = str(
            resume.get("raw_text")
            or resume.get("text")
            or resume.get("resume_text")
            or ""
        )

        skills = _to_list(resume.get("skills"))
        education = _to_list(resume.get("education"))
        work_experience = _to_list(resume.get("experience") or resume.get("work_experience"))

        email = resume.get("email") or self._extract_email(raw_text)
        phone = resume.get("phone") or self._extract_phone(raw_text)

        return TrainingRecord(
            id=path.stem,
            source=source,
            skills=skills,
            education=education,
            work_experience=work_experience,
            job_title=str(resume.get("job_title") or resume.get("Job Title") or ""),
            raw_text=raw_text,
            email=email,
            phone=phone,
            years_experience=float(resume.get("years_experience") or resume.get("experience_years") or 0),
            industry=str(resume.get("industry") or ""),
            raw=resume,
        )

    def _iter_records(self, source_name: str, folder: Path, normalizer: Callable[[Dict, str, Path], TrainingRecord]) -> Iterable[TrainingRecord]:
        if not folder.exists():
            logger.debug("Source folder missing: %s", folder)
            return []

        files = list(folder.glob("*.json"))[: self.limit_per_source]
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                yield normalizer(payload, source_name, file_path)
            except Exception as exc:
                logger.warning("Failed to load %s: %s", file_path, exc)

    def load_records(self) -> List[TrainingRecord]:
        records: List[TrainingRecord] = []
        for source_name, folder, normalizer in self.sources:
            records.extend(self._iter_records(source_name, folder, normalizer))
        logger.info("Loaded %s training records from shared loader", len(records))
        return records

    def build_feature_matrix(self, records: List[TrainingRecord]) -> Tuple[np.ndarray, np.ndarray]:
        features: List[List[float]] = []
        labels: List[int] = []

        for record in records:
            feature_dict = self.basic_features(record)
            features.append(list(feature_dict.values()))
            labels.append(self.infer_seniority(record))

        return np.array(features), np.array(labels)

    def basic_features(self, record: TrainingRecord) -> Dict[str, float]:
        return {
            "skills_count": float(len(record.skills)),
            "experience_years": float(len(record.work_experience) or record.years_experience),
            "education_count": float(len(record.education)),
            "has_technical_skills": float(any("tech" in str(s).lower() for s in record.skills)),
            "has_management": float(any("manag" in str(exp).lower() for exp in record.work_experience)),
            "has_degree": float(any("degree" in str(edu).lower() for edu in record.education)),
        }

    def infer_seniority(self, record: TrainingRecord) -> int:
        exp_entries = len(record.work_experience)
        years = record.years_experience or exp_entries
        if years >= 10 or exp_entries >= 10:
            return 2
        if years >= 5 or exp_entries >= 5:
            return 1
        return 0

    def build_text_corpus(self, records: List[TrainingRecord]) -> List[str]:
        return [rec.full_text() for rec in records if rec.full_text()]
