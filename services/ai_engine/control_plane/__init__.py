"""
CareerTrojan — AI Control Plane
================================

The measurement + control layer that sits between all frontends and AI engines.

Modules:
    - gateway:       Unified entry point for all AI calls
    - ground_truth:  Outcome tracking (interview rate, user acceptance, etc.)
    - evaluation:    Golden test harness, regression tests, metrics
    - routing:       Policy engine for model/engine selection
    - calibration:   Confidence score calibration (Platt/Isotonic)
    - drift:         Distribution shift & performance degradation detection

Author: CareerTrojan System
Date:   February 2026
"""

from .gateway import AIGateway, get_gateway
from .ground_truth import OutcomeTracker, get_outcome_tracker
from .evaluation import EvaluationHarness, get_evaluator
from .routing import RoutingPolicy, get_router
from .calibration import ConfidenceCalibrator, get_calibrator
from .drift import DriftDetector, get_drift_detector

__all__ = [
    "AIGateway", "get_gateway",
    "OutcomeTracker", "get_outcome_tracker",
    "EvaluationHarness", "get_evaluator",
    "RoutingPolicy", "get_router",
    "ConfidenceCalibrator", "get_calibrator",
    "DriftDetector", "get_drift_detector",
]
