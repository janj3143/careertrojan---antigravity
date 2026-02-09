"""
Analytics package for IntelliCV
Zero-cost statistical analysis integrated with Hybrid AI Engine
"""

from .stats_engine import ZeroCostStatsEngine
from .feature_builder import ZeroCostFeatureBuilder
from .evaluation import EvaluationEngine

__all__ = ['ZeroCostStatsEngine', 'ZeroCostFeatureBuilder', 'EvaluationEngine']
