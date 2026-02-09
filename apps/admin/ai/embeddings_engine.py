"""Centralized embedding utilities for the hybrid AI engine."""
from __future__ import annotations

import hashlib
import logging
from typing import List, Sequence

from admin_portal.config import AIConfig

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # sentence-transformers not installed yet
    SentenceTransformer = None  # type: ignore

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Provides a single interface for generating text embeddings."""

    def __init__(self, config: AIConfig, model_name: str | None = None):
        self.config = config
        self.model_name = model_name or config.embedding_model_name
        self._model = self._load_model()

    def _load_model(self):  # type: ignore[override]
        if SentenceTransformer is None:
            logger.warning("sentence-transformers not installed; using hash fallback")
            return None

        try:
            return SentenceTransformer(self.model_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to load embedding model '{self.model_name}': {exc}")
            return None

    def embed(self, text: str) -> List[float]:
        if not text:
            return [0.0]

        if self._model is not None:
            vector = self._model.encode(text)
            return vector.tolist() if hasattr(vector, "tolist") else list(vector)

        return self._hash_vector(text)

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        return [self.embed(text) for text in texts]

    @staticmethod
    def _hash_vector(text: str, dims: int = 32) -> List[float]:
        digest = hashlib.sha256(text.encode('utf-8')).digest()
        return [digest[i % len(digest)] / 255.0 for i in range(dims)]
