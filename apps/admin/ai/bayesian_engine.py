"""Bayesian layer for job title categorisation."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from admin_portal.config import AIConfig

try:
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:  # sklearn not installed yet
    MultinomialNB = None  # type: ignore
    TfidfVectorizer = None  # type: ignore

try:
    import joblib
except ImportError:  # joblib ships with sklearn but guard anyway
    joblib = None  # type: ignore

import pickle

logger = logging.getLogger(__name__)


class BayesianJobClassifier:
    """Thin wrapper around a MultinomialNB classifier."""

    def __init__(self, config: AIConfig):
        self.config = config
        self._model = MultinomialNB() if MultinomialNB else None
        self._vectorizer = TfidfVectorizer(max_features=2000) if TfidfVectorizer else None
        self._is_fit = False

    def fit(self, titles: Sequence[str], labels: Sequence[str]) -> None:
        if not self._model or not self._vectorizer:
            raise RuntimeError("scikit-learn not available; install scikit-learn to train Bayes model")

        if not titles or not labels:
            raise ValueError("Training data cannot be empty")

        matrix = self._vectorizer.fit_transform(titles)
        self._model.fit(matrix, labels)
        self._is_fit = True
        logger.info("Bayesian classifier trained on %d samples", len(labels))

    def predict_category(self, title: str) -> Tuple[str, float, Dict[str, float]]:
        if not title:
            return ("unknown", 0.0, {})

        if not self._model or not self._vectorizer or not self._is_fit:
            return ("untrained", 0.0, {})

        vector = self._vectorizer.transform([title])
        probabilities = self._model.predict_proba(vector)[0]
        labels = list(self._model.classes_)
        distribution = dict(zip(labels, probabilities.tolist()))
        best_idx = max(range(len(probabilities)), key=lambda idx: probabilities[idx])
        return (labels[best_idx], float(probabilities[best_idx]), distribution)

    def save(self, path: Optional[Path] = None) -> Path:
        target = Path(path or self.config.bayes_model_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'model': self._model,
            'vectorizer': self._vectorizer,
            'is_fit': self._is_fit
        }

        if joblib:
            joblib.dump(payload, target)
        else:
            with open(target, 'wb') as handle:
                pickle.dump(payload, handle)

        return target

    def load(self, path: Optional[Path] = None) -> None:
        source = Path(path or self.config.bayes_model_path)
        if not source.exists():
            raise FileNotFoundError(source)

        if joblib:
            payload = joblib.load(source)
        else:
            with open(source, 'rb') as handle:
                payload = pickle.load(handle)

        self._model = payload.get('model')
        self._vectorizer = payload.get('vectorizer')
        self._is_fit = bool(payload.get('is_fit'))
        logger.info("Loaded Bayesian classifier from %s", source)
