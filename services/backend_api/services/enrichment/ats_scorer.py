import re
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .config import load_config
from .skill_categorizer import SkillCategorizer
from .experience_analyzer import ExperienceAnalyzer
from .achievement_analyzer import AchievementAnalyzer
from .user_profile import UserProfile

try:
    from langdetect import detect, DetectorFactory
    DetectorFactory.seed = 0
except ImportError:
    detect = None

# --- spaCy and rapidfuzz model loading at module level ---
try:
    import spacy
    from rapidfuzz import fuzz
except ImportError:
    spacy = None
    fuzz = None

NLP_MODEL = None
if spacy:
    try:
        NLP_MODEL = spacy.load('en_core_web_sm')
    except Exception as e:
        logging.warning(f"spaCy model load failed: {e}")
        NLP_MODEL = None

CONFIG = load_config()

class ATSScorer:
    """
    Main enrichment and ATS scoring engine for user profiles.
    Provides contextual scoring, soft skills extraction, and language detection.
    """
    def __init__(self, ats_keywords: List[str]) -> None:
        """
        Args:
            ats_keywords: List of keywords relevant for ATS scoring.
        """
        self.ats_keywords: List[str] = ats_keywords
        self.skill_categorizer: SkillCategorizer = SkillCategorizer(CONFIG)
        self.language_detector = detect if detect else None
        self.soft_skills_keywords: List[str] = CONFIG.get('soft_skills', [
            "communication", "teamwork", "leadership", "problem solving", "adaptability", "creativity",
            "work ethic", "time management", "collaboration", "empathy", "conflict resolution",
            "critical thinking", "decision making", "flexibility", "initiative", "motivation", "organization",
            "responsibility", "stress management", "negotiation", "presentation", "public speaking",
            "active listening", "interpersonal", "mentoring", "coaching", "delegation", "influence"
        ])
        self.soft_skills_pattern = re.compile(r"|".join([re.escape(skill) for skill in self.soft_skills_keywords]), re.I)

    def contextual_score(self, profile: Dict[str, Any], job_target: Optional[str]) -> float:
        """
        Compute a contextual ATS score for a user profile given a job target string.
        Args:
            profile: User profile dict (should match UserProfile schema).
            job_target: Job description or title string.
        Returns:
            ATS score as a float between 0.0 and 1.0.
        """
        job_keywords: List[str] = []
        try:
            if job_target:
                if NLP_MODEL:
                    doc = NLP_MODEL(job_target)
                    job_keywords = [ent.text.lower() for ent in doc.ents if ent.label_ in ('SKILL', 'ORG', 'WORK_OF_ART', 'PRODUCT')]
                else:
                    job_keywords = re.findall(r'\b\w+\b', job_target.lower())
            text: str = ' '.join(profile.get('skills', []))
            for exp in profile.get('experience', []):
                text += ' ' + exp.get('title', '') + ' ' + exp.get('description', '')
            match_count: int = 0
            for kw in job_keywords:
                if fuzz and any(fuzz.partial_ratio(kw, s.lower()) > 80 for s in text.split()):
                    match_count += 1
                elif kw in text.lower():
                    match_count += 1
            base_score: int = sum(1 for kw in self.ats_keywords if kw in text.lower())
            score: float = base_score + match_count
            return min(1.0, score / 10.0)
        except Exception as e:
            logging.error(f"[ATSScorer] Error computing contextual score: {e}")
            return 0.0


    def enrich(self, profile: Dict[str, Any], job_target: Optional[str] = None, user_profile: Optional[UserProfile] = None) -> Dict[str, Any]:
        """
        Enrich a resume/profile dict with ATS score and user analytics hooks.
        Args:
            profile: Resume/profile dict.
            job_target: Optional job description string for contextual scoring.
            user_profile: Optional UserProfile object for integration (growth, benchmarking, analytics).
        Returns:
            Enriched profile dict.
        """
        enriched = profile.copy()
        # Compute ATS/contextual score
        enriched['ats_score'] = self.contextual_score(profile, job_target)
        # User profile integration hooks (scaffold only)
        if user_profile:
            # Example: update user growth metrics, benchmarks, session logs
            user_profile.update_growth_metrics({'last_enriched': datetime.now().isoformat()})
            user_profile.update_benchmarks({'ats_score': enriched['ats_score']})
            user_profile.log_session({'event': 'enrichment', 'timestamp': datetime.now().isoformat()})
            # Attach user analytics to enriched profile (optional)
            enriched['user_growth_metrics'] = user_profile.growth_metrics
            enriched['user_benchmarks'] = user_profile.benchmarks
            enriched['user_session_logs'] = user_profile.session_logs
        # TODO: Integrate with user growth, benchmarking, and analytics modules as implemented
        return enriched
