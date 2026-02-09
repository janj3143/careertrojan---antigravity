"""Hybrid AI orchestrator that ties all engines together."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from admin_portal.config import AIConfig
from admin_portal.ai.nlp_engine import NLPEngine
from admin_portal.ai.embeddings_engine import EmbeddingEngine
from admin_portal.ai.bayesian_engine import BayesianJobClassifier
from admin_portal.ai.regression_models import MatchScoreRegressor
from admin_portal.ai.neural_matcher import NeuralMatchModelWrapper
from admin_portal.ai.expert_rules import ExpertRuleEngine
from admin_portal.ai.llm_client import LLMClient
from shared.io_layer import get_io_layer

logger = logging.getLogger(__name__)


class UnifiedAIEngine:
    """Single entry point consumed by portals and services."""

    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.io = get_io_layer()
        self.nlp = NLPEngine(self.config)
        self.embedding_engine = EmbeddingEngine(self.config)
        self.bayesian = BayesianJobClassifier(self.config)
        self.regressor = MatchScoreRegressor(self.config)
        self.neural = NeuralMatchModelWrapper(self.config)
        self.rules = ExpertRuleEngine(self.config)
        self.llm = LLMClient(self.config)

    def score_candidate_for_job(self, candidate_id: str, job_identifier: str) -> Dict[str, Any]:
        candidate_profile = self._load_candidate_profile(candidate_id)
        job_profile = self._load_job_profile(job_identifier)

        features = self._build_features(candidate_profile, job_profile)
        feature_vector = list(features.values()) or [0.0]

        regression_score = self.regressor.predict_single(feature_vector)
        neural_score = self.neural.predict(feature_vector)

        bayes_input = job_profile.get('position') or job_profile.get('job_title') or job_identifier
        bayes_category, bayes_prob, bayes_distribution = self.bayesian.predict_category(str(bayes_input))

        blended_score = (regression_score + neural_score) / 2.0
        rule_result = self.rules.adjust_score(blended_score, candidate_profile, job_profile)

        return {
            'candidate_id': candidate_id,
            'job_identifier': job_identifier,
            'features': features,
            'scores': {
                'regression': regression_score,
                'neural': neural_score,
                'bayesian': {
                    'category': bayes_category,
                    'confidence': bayes_prob,
                    'distribution': bayes_distribution
                },
                'rules': rule_result
            }
        }

    def explain_match(self, candidate_id: str, job_identifier: str) -> Dict[str, Any]:
        payload = self.score_candidate_for_job(candidate_id, job_identifier)
        payload['explanation'] = self.llm.explain_match(payload)
        return payload

    def _load_candidate_profile(self, candidate_id: str) -> Dict[str, Any]:
        profile = self.io.get_candidate_analysis(candidate_id)
        if profile:
            return profile

        profile = self.io.get_candidate_data(candidate_id)
        if profile:
            return profile

        raise FileNotFoundError(f"Candidate profile not found: {candidate_id}")

    def _load_job_profile(self, job_identifier: str) -> Dict[str, Any]:
        job_profile = self.io.get_job_description(job_identifier)
        if job_profile:
            return job_profile

        jobs = self.io.get_jobs(limit=1)
        if jobs:
            job = jobs[0]
            job.setdefault('job_identifier', job_identifier)
            return job

        raise FileNotFoundError(f"Job profile not found: {job_identifier}")

    def _build_features(self, candidate_profile: Dict[str, Any], job_profile: Dict[str, Any]) -> Dict[str, float]:
        features: Dict[str, float] = {}

        candidate_skills = self._normalize_list(candidate_profile.get('skills'))
        if not candidate_skills:
            candidate_skills = self._normalize_list(
                candidate_profile.get('candidate_job_fit', {}).get('skills_match')
            )

        job_skills = self._normalize_list(
            job_profile.get('required_skills') or job_profile.get('key_requirements')
        )

        overlap = len(candidate_skills & job_skills)
        features['skills_overlap'] = float(overlap)
        features['skill_coverage'] = float(overlap / (len(job_skills) or 1))

        experience_years = candidate_profile.get('user_profile', {}).get('experience_years', 0.0)
        features['experience_years'] = float(experience_years or 0.0)

        candidate_text = self._extract_text(candidate_profile)
        job_text = self._extract_text(job_profile)

        token_count = len(self.nlp.tokens(candidate_text))
        features['candidate_token_count'] = float(token_count)

        embedding = self.embedding_engine.embed(candidate_text)
        features['embedding_strength'] = float(sum(embedding) / (len(embedding) or 1))

        jd_embedding = self.embedding_engine.embed(job_text)
        features['embedding_similarity'] = self._cosine_similarity(embedding, jd_embedding)

        return features

    @staticmethod
    def _normalize_list(value: Any) -> set[str]:
        if isinstance(value, list):
            return {str(item).lower() for item in value}
        return set()

    @staticmethod
    def _extract_text(payload: Dict[str, Any]) -> str:
        if 'resume_text' in payload:
            return str(payload['resume_text'])

        text_chunks: List[str] = []
        for key in ('candidate_job_fit', 'job_opportunity', 'career_insights', 'job_description'):
            chunk = payload.get(key)
            if isinstance(chunk, dict):
                text_chunks.extend(str(value) for value in chunk.values())
            elif isinstance(chunk, list):
                text_chunks.extend(str(value) for value in chunk)
        return "\n".join(text_chunks)

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0

        length = min(len(vec_a), len(vec_b))
        dot = sum(vec_a[i] * vec_b[i] for i in range(length))
        norm_a = sum(value * value for value in vec_a[:length]) ** 0.5
        norm_b = sum(value * value for value in vec_b[:length]) ** 0.5
        if not norm_a or not norm_b:
            return 0.0
        return float(dot / (norm_a * norm_b))
