"""Evaluation helpers for the hybrid AI stack."""
from __future__ import annotations

import logging
from typing import Any, Dict, Sequence, Tuple

try:
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split
except ImportError:  # sklearn optional
    accuracy_score = f1_score = roc_auc_score = None  # type: ignore
    train_test_split = None  # type: ignore

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Lightweight evaluation harness that degrades gracefully without sklearn."""

    def split(self, X, y, test_size: float = 0.2, random_state: int = 42):
        if train_test_split:
            return train_test_split(X, y, test_size=test_size, random_state=random_state)

        midpoint = int(len(X) * (1 - test_size)) or 1
        return X[:midpoint], X[midpoint:], y[:midpoint], y[midpoint:]

    def evaluate(self, y_true: Sequence[int], regression_scores: Sequence[float],
                 neural_scores: Sequence[float]) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {
            'regression': self._metric_bundle(y_true, regression_scores),
            'neural': self._metric_bundle(y_true, neural_scores)
        }
        hybrid = [(r + n) / 2.0 for r, n in zip(regression_scores, neural_scores)]
        metrics['hybrid'] = self._metric_bundle(y_true, hybrid)
        return metrics

    def _metric_bundle(self, y_true: Sequence[int], scores: Sequence[float]) -> Dict[str, float]:
        if not y_true or not scores:
            return {'accuracy': 0.0, 'f1': 0.0, 'roc_auc': 0.0}

        try:
            preds = [1 if score >= 0.5 else 0 for score in scores]
            accuracy = accuracy_score(y_true, preds) if accuracy_score else self._simple_accuracy(y_true, preds)
            f1 = f1_score(y_true, preds) if f1_score else self._simple_f1(y_true, preds)
            roc_auc = roc_auc_score(y_true, scores) if roc_auc_score else self._simple_auc(y_true, scores)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Metric computation failed: %s", exc)
            return {'accuracy': 0.0, 'f1': 0.0, 'roc_auc': 0.0}

        return {'accuracy': float(accuracy), 'f1': float(f1), 'roc_auc': float(roc_auc)}

    @staticmethod
    def _simple_accuracy(y_true: Sequence[int], preds: Sequence[int]) -> float:
        matches = sum(1 for truth, pred in zip(y_true, preds) if truth == pred)
        return matches / len(y_true)

    @staticmethod
    def _simple_f1(y_true: Sequence[int], preds: Sequence[int]) -> float:
        tp = sum(1 for truth, pred in zip(y_true, preds) if truth == pred == 1)
        fp = sum(1 for truth, pred in zip(y_true, preds) if pred == 1 and truth == 0)
        fn = sum(1 for truth, pred in zip(y_true, preds) if pred == 0 and truth == 1)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def _simple_auc(y_true: Sequence[int], scores: Sequence[float]) -> float:
        paired = sorted(zip(scores, y_true), key=lambda item: item[0])
        positives = sum(y_true)
        negatives = len(y_true) - positives
        if positives == 0 or negatives == 0:
            return 0.0
        rank_sum = 0.0
        for idx, (_, truth) in enumerate(paired, start=1):
            if truth == 1:
                rank_sum += idx
        u_stat = rank_sum - (positives * (positives + 1)) / 2
        return u_stat / (positives * negatives)
