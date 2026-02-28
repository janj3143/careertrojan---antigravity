"""
CareerTrojan — Confidence Calibration
======================================

Calibrates model confidence scores to match actual outcome probabilities.

Problem:
    - ML models often produce overconfident or underconfident predictions
    - A model saying "90% confident" should be right 90% of the time
    - Without calibration, confidence scores are unreliable

Solution:
    - Platt Scaling: Logistic regression on validation set
    - Isotonic Regression: Non-parametric monotonic calibration
    - Temperature Scaling: Simple division by temperature parameter

Usage:
    from services.ai_engine.control_plane import get_calibrator
    
    calibrator = get_calibrator()
    
    # Calibrate a raw confidence score
    calibrated = calibrator.calibrate(0.85, task_type="score")
    
    # Train calibration model on historical data
    calibrator.train("score", ground_truth_data)
    
    # Get calibration metrics
    metrics = calibrator.get_calibration_metrics("score")

Author: CareerTrojan System
Date:   February 2026
"""

import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("ConfidenceCalibrator")


@dataclass
class CalibrationMetrics:
    """Calibration quality metrics."""
    ece: float  # Expected Calibration Error
    mce: float  # Maximum Calibration Error
    brier: float  # Brier Score
    reliability_diagram: Dict[str, List[float]] = field(default_factory=dict)
    sample_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ece": round(self.ece, 4),
            "mce": round(self.mce, 4),
            "brier": round(self.brier, 4),
            "sample_count": self.sample_count,
            "bins": self.reliability_diagram,
        }


class ConfidenceCalibrator:
    """
    Calibrates raw confidence scores to match true outcome probabilities.
    
    Maintains separate calibration models per task type since each
    has different characteristics.
    """
    
    # Number of bins for calibration
    N_BINS = 10
    
    # Minimum samples required to train calibration
    MIN_SAMPLES = 100
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or Path(__file__).parent.parent / "calibration_models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = Lock()
        
        # Calibration models per task type
        self._platt_models: Dict[str, Any] = {}
        self._isotonic_models: Dict[str, Any] = {}
        self._temperatures: Dict[str, float] = {}
        
        # Fallback: simple linear adjustment
        self._linear_adjustments: Dict[str, Tuple[float, float]] = {}
        
        # Load existing models
        self._load_models()
        
        logger.info("ConfidenceCalibrator initialized (%d task types)", len(self._platt_models))
    
    def _load_models(self):
        """Load calibration models from disk."""
        for pkl_file in self.models_dir.glob("*.pkl"):
            try:
                task_type = pkl_file.stem.replace("_platt", "").replace("_isotonic", "")
                
                with open(pkl_file, 'rb') as f:
                    model = pickle.load(f)
                
                if "_platt" in pkl_file.stem:
                    self._platt_models[task_type] = model
                elif "_isotonic" in pkl_file.stem:
                    self._isotonic_models[task_type] = model
                    
            except Exception as e:
                logger.warning("Failed to load %s: %s", pkl_file, e)
        
        # Load temperatures
        temp_file = self.models_dir / "temperatures.json"
        if temp_file.exists():
            try:
                with open(temp_file, 'r') as f:
                    self._temperatures = json.load(f)
            except Exception:
                pass
        
        # Load linear adjustments
        linear_file = self.models_dir / "linear_adjustments.json"
        if linear_file.exists():
            try:
                with open(linear_file, 'r') as f:
                    data = json.load(f)
                self._linear_adjustments = {k: tuple(v) for k, v in data.items()}
            except Exception:
                pass
    
    def _save_models(self):
        """Save calibration models to disk."""
        try:
            # Save Platt models
            for task_type, model in self._platt_models.items():
                path = self.models_dir / f"{task_type}_platt.pkl"
                with open(path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save Isotonic models
            for task_type, model in self._isotonic_models.items():
                path = self.models_dir / f"{task_type}_isotonic.pkl"
                with open(path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save temperatures
            temp_file = self.models_dir / "temperatures.json"
            with open(temp_file, 'w') as f:
                json.dump(self._temperatures, f, indent=2)
            
            # Save linear adjustments
            linear_file = self.models_dir / "linear_adjustments.json"
            with open(linear_file, 'w') as f:
                json.dump({k: list(v) for k, v in self._linear_adjustments.items()}, f, indent=2)
                
        except Exception as e:
            logger.warning("Failed to save models: %s", e)
    
    def calibrate(
        self,
        raw_confidence: float,
        task_type: str,
        method: str = "auto",
    ) -> float:
        """
        Calibrate a raw confidence score.
        
        Args:
            raw_confidence: The uncalibrated confidence (0-1)
            task_type: Task type to use appropriate calibration model
            method: "platt", "isotonic", "temperature", "linear", or "auto"
        
        Returns:
            Calibrated confidence (0-1)
        """
        # Clamp input
        raw_confidence = max(0.0, min(1.0, raw_confidence))
        
        if method == "auto":
            # Try isotonic first (most flexible), then platt, then temperature
            if task_type in self._isotonic_models:
                method = "isotonic"
            elif task_type in self._platt_models:
                method = "platt"
            elif task_type in self._temperatures:
                method = "temperature"
            elif task_type in self._linear_adjustments:
                method = "linear"
            else:
                # No calibration available - return as-is with slight dampening
                return self._default_calibration(raw_confidence)
        
        try:
            if method == "isotonic":
                model = self._isotonic_models.get(task_type)
                if model:
                    return float(model.predict([[raw_confidence]])[0])
            
            elif method == "platt":
                model = self._platt_models.get(task_type)
                if model:
                    # Platt scaling uses logistic regression
                    return float(model.predict_proba([[raw_confidence]])[0, 1])
            
            elif method == "temperature":
                temp = self._temperatures.get(task_type, 1.0)
                # Apply temperature scaling (softmax with temperature)
                # For single confidence: sigmoid(logit / T)
                if raw_confidence <= 0 or raw_confidence >= 1:
                    return raw_confidence
                logit = np.log(raw_confidence / (1 - raw_confidence))
                scaled_logit = logit / temp
                return float(1 / (1 + np.exp(-scaled_logit)))
            
            elif method == "linear":
                slope, intercept = self._linear_adjustments.get(task_type, (1.0, 0.0))
                return float(max(0.0, min(1.0, slope * raw_confidence + intercept)))
        
        except Exception as e:
            logger.debug("Calibration failed for %s/%s: %s", task_type, method, e)
        
        return self._default_calibration(raw_confidence)
    
    def _default_calibration(self, raw: float) -> float:
        """Default calibration when no model is available.
        
        Applies slight dampening to reduce overconfidence.
        """
        # Push towards 0.5 by 10%
        return 0.9 * raw + 0.1 * 0.5
    
    def train(
        self,
        task_type: str,
        data: List[Tuple[float, bool]],
        method: str = "isotonic",
    ) -> bool:
        """
        Train a calibration model on historical data.
        
        Args:
            task_type: Task type to train calibration for
            data: List of (confidence, outcome) pairs
            method: "platt", "isotonic", or "temperature"
        
        Returns:
            True if training succeeded
        """
        if len(data) < self.MIN_SAMPLES:
            logger.warning("Insufficient data for calibration: %d < %d", len(data), self.MIN_SAMPLES)
            return False
        
        try:
            confidences = np.array([d[0] for d in data]).reshape(-1, 1)
            outcomes = np.array([1 if d[1] else 0 for d in data])
            
            if method == "isotonic":
                from sklearn.isotonic import IsotonicRegression
                model = IsotonicRegression(out_of_bounds='clip')
                model.fit(confidences.ravel(), outcomes)
                
                with self._lock:
                    self._isotonic_models[task_type] = model
                
            elif method == "platt":
                from sklearn.linear_model import LogisticRegression
                model = LogisticRegression()
                model.fit(confidences, outcomes)
                
                with self._lock:
                    self._platt_models[task_type] = model
                
            elif method == "temperature":
                # Find optimal temperature via grid search
                best_temp = 1.0
                best_ece = float('inf')
                
                for temp in np.linspace(0.5, 3.0, 50):
                    calibrated = []
                    for conf in confidences.ravel():
                        if conf <= 0 or conf >= 1:
                            calibrated.append(conf)
                        else:
                            logit = np.log(conf / (1 - conf))
                            calibrated.append(1 / (1 + np.exp(-logit / temp)))
                    
                    ece = self._compute_ece(np.array(calibrated), outcomes)
                    if ece < best_ece:
                        best_ece = ece
                        best_temp = temp
                
                with self._lock:
                    self._temperatures[task_type] = float(best_temp)
            
            else:
                # Linear adjustment
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(confidences, outcomes)
                
                with self._lock:
                    self._linear_adjustments[task_type] = (float(model.coef_[0]), float(model.intercept_))
            
            self._save_models()
            logger.info("Trained %s calibration for %s on %d samples", method, task_type, len(data))
            return True
            
        except Exception as e:
            logger.exception("Calibration training failed: %s", e)
            return False
    
    def _compute_ece(
        self,
        confidences: np.ndarray,
        outcomes: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """Compute Expected Calibration Error."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        
        for i in range(n_bins):
            in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                avg_confidence = confidences[in_bin].mean()
                avg_accuracy = outcomes[in_bin].mean()
                ece += prop_in_bin * abs(avg_confidence - avg_accuracy)
        
        return float(ece)
    
    def get_calibration_metrics(
        self,
        task_type: str,
        data: Optional[List[Tuple[float, bool]]] = None,
    ) -> CalibrationMetrics:
        """
        Compute calibration metrics for a task type.
        
        If data is not provided, uses cached historical data.
        """
        if data is None:
            # Try to load from outcome tracker
            try:
                from services.ai_engine.control_plane.ground_truth import get_outcome_tracker
                tracker = get_outcome_tracker()
                
                # Get appropriate outcome type for task
                outcome_map = {
                    "score": "recommendation_accepted",
                    "extract": "recommendation_accepted",
                    "match": "match_applied",
                    "rewrite": "rewrite_adopted",
                    "qa": "question_helpful",
                }
                outcome_type = outcome_map.get(task_type, "recommendation_accepted")
                
                data = tracker.get_calibration_data(task_type, outcome_type)
            except Exception as e:
                logger.debug("Could not load ground-truth data: %s", e)
                data = []
        
        if not data:
            return CalibrationMetrics(
                ece=0.0,
                mce=0.0,
                brier=0.0,
                sample_count=0,
            )
        
        confidences = np.array([d[0] for d in data])
        outcomes = np.array([1 if d[1] else 0 for d in data])
        
        # Compute metrics
        ece = self._compute_ece(confidences, outcomes)
        
        # Maximum Calibration Error
        bin_boundaries = np.linspace(0, 1, self.N_BINS + 1)
        max_gap = 0.0
        bin_data = {"boundaries": bin_boundaries.tolist(), "accuracy": [], "confidence": [], "count": []}
        
        for i in range(self.N_BINS):
            in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
            if in_bin.sum() > 0:
                avg_conf = float(confidences[in_bin].mean())
                avg_acc = float(outcomes[in_bin].mean())
                gap = abs(avg_conf - avg_acc)
                max_gap = max(max_gap, gap)
                
                bin_data["accuracy"].append(avg_acc)
                bin_data["confidence"].append(avg_conf)
                bin_data["count"].append(int(in_bin.sum()))
            else:
                bin_data["accuracy"].append(None)
                bin_data["confidence"].append(None)
                bin_data["count"].append(0)
        
        # Brier Score
        brier = float(np.mean((confidences - outcomes) ** 2))
        
        return CalibrationMetrics(
            ece=ece,
            mce=max_gap,
            brier=brier,
            reliability_diagram=bin_data,
            sample_count=len(data),
        )
    
    def auto_calibrate(self, task_type: str) -> bool:
        """
        Automatically train calibration from ground-truth data.
        
        Fetches data from OutcomeTracker and trains best-fit model.
        """
        try:
            from services.ai_engine.control_plane.ground_truth import get_outcome_tracker
            tracker = get_outcome_tracker()
            
            # Map task types to outcome types
            outcome_map = {
                "score": "recommendation_accepted",
                "extract": "recommendation_accepted",
                "match": "match_applied",
                "rewrite": "rewrite_adopted",
                "qa": "question_helpful",
            }
            
            outcome_type = outcome_map.get(task_type, "recommendation_accepted")
            data = tracker.get_calibration_data(task_type, outcome_type, days=90)
            
            if len(data) < self.MIN_SAMPLES:
                logger.info("Insufficient data for auto-calibration of %s: %d samples", task_type, len(data))
                return False
            
            # Try different methods and pick best ECE
            best_method = None
            best_ece = float('inf')
            
            for method in ["isotonic", "platt", "temperature"]:
                success = self.train(task_type, data, method)
                if success:
                    metrics = self.get_calibration_metrics(task_type, data)
                    if metrics.ece < best_ece:
                        best_ece = metrics.ece
                        best_method = method
            
            logger.info("Auto-calibrated %s using %s (ECE=%.4f)", task_type, best_method, best_ece)
            return True
            
        except Exception as e:
            logger.exception("Auto-calibration failed: %s", e)
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get calibrator statistics."""
        return {
            "platt_models": list(self._platt_models.keys()),
            "isotonic_models": list(self._isotonic_models.keys()),
            "temperatures": {k: round(v, 3) for k, v in self._temperatures.items()},
            "linear_adjustments": {k: (round(v[0], 3), round(v[1], 3)) for k, v in self._linear_adjustments.items()},
            "models_dir": str(self.models_dir),
        }


# ── Module-level Singleton ───────────────────────────────────────────────

_calibrator_instance: Optional[ConfidenceCalibrator] = None
_calibrator_lock = Lock()


def get_calibrator() -> ConfidenceCalibrator:
    """Get the module-level ConfidenceCalibrator singleton."""
    global _calibrator_instance
    
    with _calibrator_lock:
        if _calibrator_instance is None:
            _calibrator_instance = ConfidenceCalibrator()
        return _calibrator_instance
