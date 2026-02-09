"""Hybrid AI engine package for the admin portal."""

from .nlp_engine import NLPEngine
from .embeddings_engine import EmbeddingEngine
from .bayesian_engine import BayesianJobClassifier
from .regression_models import MatchScoreRegressor
from .neural_matcher import NeuralMatchModelWrapper
from .expert_rules import ExpertRuleEngine
from .llm_client import LLMClient
from .unified_ai_engine import UnifiedAIEngine

__all__ = [
    'NLPEngine',
    'EmbeddingEngine',
    'BayesianJobClassifier',
    'MatchScoreRegressor',
    'NeuralMatchModelWrapper',
    'ExpertRuleEngine',
    'LLMClient',
    'UnifiedAIEngine'
]
