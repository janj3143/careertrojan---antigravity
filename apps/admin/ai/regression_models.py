"""Regression layer for match scoring."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from admin_portal.config import AIConfig

try:
    from sklearn.linear_model import LogisticRegression
except ImportError:  # sklearn not installed yet
    LogisticRegression = None  # type: ignore

try:
    import joblib
except ImportError:
    joblib = None  # type: ignore

import pickle

logger = logging.getLogger(__name__)


class MatchScoreRegressor:
    """Thin logistic regression wrapper with persistence helpers."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._model = LogisticRegression(max_iter=1000) if LogisticRegression else None
        self._is_fit = False

    def fit(self, X, y) -> None:
        if not self._model:
            raise RuntimeError("scikit-learn not available; cannot train regression model")

        self._model.fit(X, y)
        self._is_fit = True
        logger.info("Regression model trained on %d rows", len(y))

    def predict_proba(self, X) -> List[float]:
        if not self._model or not self._is_fit:
            row_count = len(X) if isinstance(X, Sequence) else 1
            return [0.5] * row_count

        probabilities = self._model.predict_proba(X)
        return probabilities[:, 1].tolist()

    def predict_single(self, features: Sequence[float]) -> float:
        if not features:
            return 0.5

        if not self._model or not self._is_fit:
            return min(max(sum(features) / (len(features) * 100.0), 0.0), 1.0)

        probability = self._model.predict_proba([features])[0][1]
        return float(probability)

    def save(self, path: Optional[Path] = None) -> Path:
        target = Path(path or self.config.regression_model_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        if joblib and self._model:
            joblib.dump({'model': self._model, 'is_fit': self._is_fit}, target)
        else:
            with open(target, 'wb') as handle:
                pickle.dump({'model': self._model, 'is_fit': self._is_fit}, handle)

        return target

    def load(self, path: Optional[Path] = None) -> None:
        source = Path(path or self.config.regression_model_path)
        if not source.exists():
            raise FileNotFoundError(source)

        if joblib:
            payload = joblib.load(source)
        else:
            with open(source, 'rb') as handle:
                payload = pickle.load(handle)

        self._model = payload.get('model')
        self._is_fit = bool(payload.get('is_fit'))
        logger.info("Loaded regression model from %s", source)
