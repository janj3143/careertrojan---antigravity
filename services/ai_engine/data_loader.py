"""
CareerTrojan — Data Loader (schema-aware)
==========================================
Loads profiles from ai_data_final/ using the SchemaAdapter so that
profiles (Qualifications / Career Summary / Personal Details) are
correctly normalised into the skills / role / experience_years format
the rest of the platform expects.
"""

import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any

# Central config for data paths
try:
    from services.ai_engine.config import AI_DATA_DIR, PROFILES_DIR
except ImportError:
    import os
    _dr = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
    AI_DATA_DIR = _dr / "ai_data_final"
    PROFILES_DIR = AI_DATA_DIR / "profiles"

# Schema adapter — handles the real data schemas
try:
    from services.ai_engine.schema_adapter import adapt_any, load_and_adapt_directory
except ImportError:
    adapt_any = None  # fallback below
    load_and_adapt_directory = None

logger = logging.getLogger("AI_DataLoader")

# ── Seniority heuristic ──────────────────────────────────────────────────

_SENIORITY_KEYWORDS = {
    "Director": ["director", "vp", "vice president", "chief", "ceo", "cto", "cfo", "head of"],
    "Senior": ["senior", "sr", "lead", "principal", "staff"],
    "Mid": ["engineer", "analyst", "consultant", "specialist", "coordinator"],
    "Junior": ["junior", "jr", "graduate", "trainee", "intern", "assistant", "entry"],
}


def _infer_seniority(job_title: str, experience_years: int) -> str:
    title_lower = job_title.lower()
    for level, keywords in _SENIORITY_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return level
    # Fall back to experience years
    if experience_years >= 10:
        return "Senior"
    if experience_years >= 4:
        return "Mid"
    if experience_years > 0:
        return "Junior"
    return "Mid"


class DataLoader:
    _instance = None
    _profiles_cache: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = DataLoader()
        return cls._instance

    def __init__(self):
        self.load_sample_profiles()

    def load_sample_profiles(self, limit=500):
        """
        Loads a sample of profiles into memory for the visualisation layer.

        Uses SchemaAdapter.adapt_any() so profiles with the real schema
        (Qualifications, Career Summary, Personal Details) are properly
        normalised into skills, experience_years, industry, etc.
        """
        # Try multiple data sources for best coverage
        sources = [
            ("cv_files", AI_DATA_DIR / "cv_files"),
            ("parsed_resumes", AI_DATA_DIR / "parsed_resumes"),
            ("profiles", PROFILES_DIR),
        ]

        loaded: List[Dict[str, Any]] = []

        for source_name, source_dir in sources:
            if not source_dir.exists():
                logger.debug("Source dir not found: %s", source_dir)
                continue

            files = list(source_dir.glob("*.json"))
            random.shuffle(files)

            remaining = limit - len(loaded)
            if remaining <= 0:
                break

            for f in files[:remaining]:
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)

                    # Use schema adapter if available
                    if adapt_any is not None:
                        rec = adapt_any(data, f.stem)
                    else:
                        # Minimal fallback (pre-adapter)
                        rec = {
                            "id": f.stem,
                            "text": data.get("raw_text", data.get("Career Summary", "")),
                            "job_title": data.get("job_title", data.get("Job Title", "")),
                            "skills": data.get("skills", []),
                            "experience_years": data.get("experience_years", 0),
                            "education": data.get("education", "Unknown"),
                            "industry": data.get("industry", "Unknown"),
                        }

                    # Build the visualisation-friendly profile
                    profile = {
                        "id": rec.get("id", f.stem),
                        "role": rec.get("job_title", "Unknown") or "Unknown",
                        "seniority": _infer_seniority(
                            rec.get("job_title", ""),
                            rec.get("experience_years", 0),
                        ),
                        "skills": rec.get("skills", []),
                        "experience_years": rec.get("experience_years", 0),
                        "match_score": random.random() * 100,
                        "industry": rec.get("industry", "Unknown"),
                        "touchpoints": [],  # populated at runtime
                        "source": source_name,
                    }

                    # Only include profiles with meaningful data
                    if profile["skills"] or profile["role"] != "Unknown":
                        loaded.append(profile)

                except Exception as e:
                    logger.debug("Failed to load %s: %s", f, e)

        self._profiles_cache = loaded
        logger.info(
            "Loaded %d profiles into memory cache from %s",
            len(self._profiles_cache),
            ", ".join(s[0] for s in sources if s[1].exists()),
        )

    def get_profiles(self) -> List[Dict[str, Any]]:
        return self._profiles_cache

    def get_terms(self) -> Dict[str, int]:
        """Extracts term frequency from skills for WordCloud."""
        freq: Dict[str, int] = {}
        for p in self._profiles_cache:
            for s in p.get("skills", []):
                s = s.lower().strip()
                if s:
                    freq[s] = freq.get(s, 0) + 1
        return freq
