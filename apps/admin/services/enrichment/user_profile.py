
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    """
    Standardized schema for user profile enrichment input/output.
    This dataclass is designed for maximum compatibility and easy translation to C# POCOs.
    Includes enrichment and integration hooks for user growth, benchmarking, and analytics.
    """
    personal_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[str]
    achievements: List[str]
    preferences: Dict[str, Any]
    # Enrichment output fields (optional)
    smart_analysis: Optional[Dict[str, Any]] = field(default=None)
    ats_score: Optional[float] = field(default=None)
    enriched_at: Optional[str] = field(default=None)
    categorized_skills: Optional[Dict[str, List[str]]] = field(default=None)
    impact_achievements: Optional[List[str]] = field(default=None)
    total_years_experience: Optional[float] = field(default=None)
    primary_language: Optional[str] = field(default=None)
    job_title_languages: Optional[Dict[str, str]] = field(default=None)
    soft_skills: Optional[List[str]] = field(default=None)
    employment_gaps: Optional[List[Dict[str, Any]]] = field(default=None)
    recommendations: Optional[List[str]] = field(default=None)
    # User growth, benchmarking, and analytics hooks
    growth_metrics: Optional[Dict[str, Any]] = field(default_factory=dict)
    benchmarks: Optional[Dict[str, Any]] = field(default_factory=dict)
    session_logs: Optional[List[Dict[str, Any]]] = field(default_factory=list)

    def update_growth_metrics(self, metrics: Dict[str, Any]):
        self.growth_metrics.update(metrics)

    def update_benchmarks(self, benchmarks: Dict[str, Any]):
        self.benchmarks.update(benchmarks)

    def log_session(self, session_data: Dict[str, Any]):
        self.session_logs.append(session_data)

    def get_profile(self) -> Dict[str, Any]:
        return {
            "personal_info": self.personal_info,
            "experience": self.experience,
            "education": self.education,
            "skills": self.skills,
            "achievements": self.achievements,
            "preferences": self.preferences,
            "smart_analysis": self.smart_analysis,
            "ats_score": self.ats_score,
            "enriched_at": self.enriched_at,
            "categorized_skills": self.categorized_skills,
            "impact_achievements": self.impact_achievements,
            "total_years_experience": self.total_years_experience,
            "primary_language": self.primary_language,
            "job_title_languages": self.job_title_languages,
            "soft_skills": self.soft_skills,
            "employment_gaps": self.employment_gaps,
            "recommendations": self.recommendations,
            "growth_metrics": self.growth_metrics,
            "benchmarks": self.benchmarks,
            "session_logs": self.session_logs
        }
    # TODO: Add hooks for integration with user growth, benchmarking, and analytics modules
