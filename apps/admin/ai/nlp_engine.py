"""spaCy-backed NLP utilities (backend-required; no heuristic fallbacks)."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from admin_portal.config import AIConfig

try:
    import spacy
    from spacy.language import Language
except ImportError:  # spaCy not installed yet
    spacy = None  # type: ignore
    Language = None  # type: ignore

logger = logging.getLogger(__name__)


class NLPEngine:
    """Central NLP helper so other modules never load spaCy directly."""

    def __init__(self, config: AIConfig, model_name: Optional[str] = None):
        self.config = config
        self.model_name = model_name or "en_core_web_sm"
        self._nlp = self._load_model()

    def _load_model(self) -> Optional["Language"]:
        if spacy is None:
            raise RuntimeError("spaCy is not installed; NLPEngine cannot run")

        try:
            return spacy.load(self.model_name)
        except OSError:
            raise RuntimeError(f"spaCy model '{self.model_name}' is missing; NLPEngine cannot run")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Failed to load spaCy model '{self.model_name}': {exc}")
            raise RuntimeError(f"Failed to load spaCy model '{self.model_name}'")

    def parse(self, text: str) -> Dict[str, List[str]]:
        if not text:
            return {"tokens": [], "sentences": [], "entities": []}

        if self._nlp is None:
            raise RuntimeError("NLP engine unavailable")

        doc = self._nlp(text)
        entities = [f"{ent.text}::{ent.label_}" for ent in doc.ents]
        sentences = [sent.text.strip() for sent in doc.sents]
        tokens = [token.text for token in doc]
        return {"tokens": tokens, "sentences": sentences, "entities": entities}

    def extract_entities(self, text: str) -> List[str]:
        return self.parse(text).get("entities", [])

    def sentences(self, text: str) -> List[str]:
        return self.parse(text).get("sentences", [])

    def tokens(self, text: str) -> List[str]:
        return self.parse(text).get("tokens", [])


