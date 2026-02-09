"""AI configuration objects for the admin portal engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from shared import (
    INTELLICV_ROOT,
    AI_DATA_ROOT,
    WORKING_COPY_DIR,
    ADMIN_PORTAL_DIR,
    USER_PORTAL_DIR
)


@dataclass(frozen=True)
class AIConfig:
    """Lightweight container for all hybrid-AI path and model settings."""

    ai_data_root: Path = AI_DATA_ROOT
    model_root: Path = ADMIN_PORTAL_DIR / "models"
    working_copy_root: Path = WORKING_COPY_DIR
    admin_data_root: Path = ADMIN_PORTAL_DIR / "data"
    user_data_root: Path = USER_PORTAL_DIR / "data"
    runtime_root: Path = INTELLICV_ROOT

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    default_llm: str = "openai:gpt-4.1-mini"
    local_llm: str = "ollama:phi3:mini"

    use_local_first: bool = True
    temperature: float = 0.2
    max_output_tokens: int = 900
    llm_timeout_secs: int = 60

    extra_params: Dict[str, Any] = field(default_factory=dict)

    def with_overrides(self, **overrides: Any) -> "AIConfig":
        """Return a new config with updated fields without mutating self."""

        data = self.to_dict()
        data.update(overrides)
        return AIConfig(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config values into a plain dictionary."""

        return {
            "ai_data_root": self.ai_data_root,
            "model_root": self.model_root,
            "working_copy_root": self.working_copy_root,
            "admin_data_root": self.admin_data_root,
            "user_data_root": self.user_data_root,
            "runtime_root": self.runtime_root,
            "embedding_model_name": self.embedding_model_name,
            "default_llm": self.default_llm,
            "local_llm": self.local_llm,
            "use_local_first": self.use_local_first,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "llm_timeout_secs": self.llm_timeout_secs,
            "extra_params": self.extra_params.copy(),
        }

    @property
    def bayes_model_path(self) -> Path:
        return self.model_root / "bayesian_classifier.pkl"

    @property
    def regression_model_path(self) -> Path:
        return self.model_root / "regression_match_model.pkl"

    @property
    def neural_model_path(self) -> Path:
        return self.model_root / "nn_matcher.pt"

    @classmethod
    def build(cls, overrides: Optional[Dict[str, Any]] = None) -> "AIConfig":
        """Convenience constructor that accepts optional overrides."""

        overrides = overrides or {}
        return cls(**overrides)
