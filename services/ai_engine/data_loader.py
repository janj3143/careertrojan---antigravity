
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any

# Assuming services.shared.config or similar exists, but we'll use direct imports/env for now to be safe
try:
    from services.ai_engine.config import PROFILES_DIR
except ImportError:
    # Fallback
    import os
    PROFILES_DIR = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\Codec-Antigravity Data set")) / "ai_data_final" / "profiles"

logger = logging.getLogger("AI_DataLoader")


def _derive_match_score(profile: Dict[str, Any]) -> float:
    years = float(profile.get("experience_years") or 0)
    skills = profile.get("skills") or []
    skills_count = len(skills) if isinstance(skills, list) else 0
    role = str(profile.get("role") or "").lower()

    score = 0.15
    score += min(years / 15.0, 0.45)
    score += min(skills_count / 30.0, 0.35)
    if any(token in role for token in ["senior", "lead", "principal", "manager"]):
        score += 0.08
    return round(min(max(score, 0.05), 0.99) * 100, 2)


def _load_enhanced_keywords() -> Dict[str, List[str]]:
    try:
        from services.shared.paths import CareerTrojanPaths

        paths = CareerTrojanPaths()
        target = paths.ai_data_final / "metadata" / "enhanced_keywords.json"
        if not target.exists():
            return {}
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}


_ENHANCED_KW = _load_enhanced_keywords()

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
        """Loads a sample of profiles into memory for visualization demos."""
        if not PROFILES_DIR.exists():
            logger.warning(f"Profiles dir not found: {PROFILES_DIR}")
            return

        files = list(PROFILES_DIR.glob("*.json"))
        # Shuffle to get random sample
        random.shuffle(files)
        
        loaded = []
        for f in files[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    # Normalize basic fields
                    profile = {
                        "id": f.stem,
                        "role": data.get("role", "Unknown"),
                        "seniority": data.get("seniority", "Mid"),
                        "skills": data.get("skills", []),
                        "experience_years": data.get("experience_years", 0),
                        "match_score": data.get("match_score") if data.get("match_score") is not None else _derive_match_score(data),
                        "industry": data.get("industry", "Tech"),
                        "touchpoints": data.get("touchpoints", [])
                    }
                    loaded.append(profile)
            except Exception as e:
                logger.debug(f"Failed to load {f}: {e}")
        
        self._profiles_cache = loaded
        logger.info(f"Loaded {len(self._profiles_cache)} profiles into memory cache.")

    def get_profiles(self) -> List[Dict[str, Any]]:
        return self._profiles_cache

    def get_terms(self) -> Dict[str, int]:
        """Extracts term frequency from skills for WordCloud."""
        freq = {}
        for p in self._profiles_cache:
            for s in p.get("skills", []):
                s = s.lower().strip()
                freq[s] = freq.get(s, 0) + 1

        for term in _ENHANCED_KW.get("skills", []):
            normalized = str(term).lower().strip()
            if normalized:
                freq[normalized] = freq.get(normalized, 0) + 1

        return freq
