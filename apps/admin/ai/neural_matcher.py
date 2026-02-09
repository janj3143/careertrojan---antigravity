"""Lightweight neural-network wrapper for nonlinear match scoring."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Sequence

from admin_portal.config import AIConfig

try:
    import torch
    import torch.nn as nn
except ImportError:  # PyTorch not installed in many dev setups
    torch = None  # type: ignore
    nn = None  # type: ignore

logger = logging.getLogger(__name__)


class NeuralMatchModelWrapper:
    """Wrapper that gracefully degrades when PyTorch is not installed."""

    def __init__(self, config: AIConfig, input_dim: int = 128, hidden_dim: int = 64):
        self.config = config
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.model_path = self.config.neural_model_path
        self._model = self._build_model()

    def _build_model(self):
        if torch is None or nn is None:
            logger.warning("PyTorch not installed; NeuralMatchModel will use heuristics")
            return None

        class _Net(nn.Module):  # type: ignore
            def __init__(self, in_dim: int, hid_dim: int):
                super().__init__()
                self.layers = nn.Sequential(
                    nn.Linear(in_dim, hid_dim),
                    nn.ReLU(),
                    nn.Linear(hid_dim, hid_dim // 2 or 1),
                    nn.ReLU(),
                    nn.Linear(hid_dim // 2 or 1, 1)
                )

            def forward(self, x):  # type: ignore[override]
                return self.layers(x)

        return _Net(self.input_dim, self.hidden_dim)

    def predict(self, features: Sequence[float]) -> float:
        if not features:
            return 0.5

        if self._model is None or torch is None:
            heuristic = sum(features) / (len(features) * 100.0)
            return float(min(max(heuristic, 0.0), 1.0))

        self._model.eval()
        with torch.no_grad():
            vector = self._resize_vector(features)
            tensor = torch.tensor([vector], dtype=torch.float32)
            score = torch.sigmoid(self._model(tensor)).item()
            return float(score)

    def _resize_vector(self, vector: Sequence[float]) -> List[float]:
        vector = list(vector)
        if len(vector) >= self.input_dim:
            return vector[:self.input_dim]
        padding = [0.0] * (self.input_dim - len(vector))
        return vector + padding

    def save(self, path: Optional[Path] = None) -> Optional[Path]:
        if self._model is None or torch is None:
            logger.warning("PyTorch not available; skipping neural model save")
            return None

        target = Path(path or self.model_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self._model.state_dict(), target)
        return target

    def load(self, path: Optional[Path] = None) -> None:
        if self._model is None or torch is None:
            logger.warning("PyTorch not available; cannot load neural model")
            return

        source = Path(path or self.model_path)
        if not source.exists():
            raise FileNotFoundError(source)

        state_dict = torch.load(source, map_location='cpu')
        self._model.load_state_dict(state_dict)
        logger.info("Loaded neural matcher weights from %s", source)
