"""
CareerTrojan — Unified Model Configuration Loader
==================================================

Single source of truth for ALL model configuration.
Reads config/models.yaml and provides typed access to every model setting.

Usage:
    from config.model_config import model_config

    # Get default LLM provider settings
    provider = model_config.get_llm_provider()
    model_name = model_config.get_llm_model()

    # Get a specific ML model path
    path = model_config.get_model_path('bayesian', 'bayesian_classifier')

    # Get embedding model name
    emb = model_config.get_embedding_model()

    # Get task pipeline
    pipeline = model_config.get_task_pipeline('cv_matching')

    # Hot-reload after YAML change
    model_config.reload()
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from threading import Lock

logger = logging.getLogger(__name__)

# Resolve config path relative to this file's location
_CONFIG_DIR = Path(__file__).parent
_DEFAULT_CONFIG_PATH = _CONFIG_DIR / "models.yaml"


class ModelConfig:
    """Thread-safe, hot-reloadable model configuration singleton."""

    _instance = None
    _lock = Lock()

    def __new__(cls, config_path: Optional[str] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        if self._initialized:
            return
        self._config_path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._load()
        self._initialized = True

    def _load(self):
        """Load or reload the YAML config."""
        try:
            with open(self._config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Model config loaded from {self._config_path}")
        except FileNotFoundError:
            logger.warning(f"Model config not found at {self._config_path} — using defaults")
            self._config = {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {self._config_path}: {e}")
            self._config = {}

    def reload(self):
        """Hot-reload the config from disk."""
        with self._lock:
            self._load()

    # ── LLM Provider Access ──────────────────────────────────────────────

    def get_llm_provider(self, override: Optional[str] = None) -> str:
        """Get active LLM provider name."""
        if override:
            return override
        return self._config.get("llm", {}).get("default_provider", "openai")

    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get full config dict for a specific LLM provider."""
        provider = provider or self.get_llm_provider()
        providers = self._config.get("llm", {}).get("providers", {})
        return providers.get(provider, {})

    def get_llm_model(self, provider: Optional[str] = None) -> str:
        """Get default model name for a provider."""
        cfg = self.get_llm_config(provider)
        return cfg.get("default_model", "gpt-4")

    def get_llm_fallback_models(self, provider: Optional[str] = None) -> List[str]:
        """Get fallback model list for a provider."""
        cfg = self.get_llm_config(provider)
        return cfg.get("fallback_models", [])

    def get_llm_api_key(self, provider: Optional[str] = None) -> Optional[str]:
        """Resolve the API key from the env var named in config."""
        cfg = self.get_llm_config(provider)
        env_var = cfg.get("api_key_env", "")
        return os.getenv(env_var) if env_var else None

    def get_llm_fallback_chain(self) -> List[str]:
        """Get provider fallback order."""
        return self._config.get("llm", {}).get("fallback_chain", ["openai"])

    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a provider is enabled in config."""
        cfg = self.get_llm_config(provider)
        return cfg.get("enabled", False)

    # ── Embedding Access ─────────────────────────────────────────────────

    def get_embedding_provider(self) -> str:
        """Get active embedding provider."""
        return self._config.get("embeddings", {}).get("provider", "sentence_transformers")

    def get_embedding_model(self, provider: Optional[str] = None) -> str:
        """Get embedding model name."""
        provider = provider or self.get_embedding_provider()
        models = self._config.get("embeddings", {}).get("models", {})
        provider_cfg = models.get(provider, {})
        return provider_cfg.get("model_name", "all-MiniLM-L6-v2")

    def get_embedding_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get full embedding config for a provider."""
        provider = provider or self.get_embedding_provider()
        models = self._config.get("embeddings", {}).get("models", {})
        return models.get(provider, {})

    # ── ML Model Access ──────────────────────────────────────────────────

    def get_ml_base_dir(self) -> Path:
        """Get base directory for trained models."""
        ml = self._config.get("ml_models", {})
        env_var = ml.get("base_dir_env", "ML_MODELS_PATH")
        env_path = os.getenv(env_var)
        if env_path and Path(env_path).exists():
            return Path(env_path)
        return Path(ml.get("fallback_dir", "trained_models"))

    def get_model_path(self, family: str, model_name: str) -> Optional[Path]:
        """Get the full file path for a specific trained model."""
        family_cfg = self._config.get("ml_models", {}).get(family, {})
        models = family_cfg.get("models", [])
        for m in models:
            if m["name"] == model_name:
                return self.get_ml_base_dir() / m["file"]
        return None

    def get_family_models(self, family: str) -> List[Dict[str, Any]]:
        """Get all model definitions for a family (bayesian, neural, etc.)."""
        return self._config.get("ml_models", {}).get(family, {}).get("models", [])

    def is_family_enabled(self, family: str) -> bool:
        """Check if a model family is enabled."""
        return self._config.get("ml_models", {}).get(family, {}).get("enabled", False)

    def get_training_script(self, family: str) -> Optional[str]:
        """Get the training script path for a model family."""
        return self._config.get("ml_models", {}).get(family, {}).get("training_script")

    # ── Task Pipeline Access ─────────────────────────────────────────────

    def get_task_pipeline(self, task: str) -> List[str]:
        """Get the model pipeline for a specific inference task."""
        tasks = self._config.get("inference", {}).get("tasks", {})
        return tasks.get(task, {}).get("pipeline", [])

    def get_task_llm_provider(self, task: str) -> Optional[str]:
        """Get the LLM provider override for a specific task (or None for default)."""
        tasks = self._config.get("inference", {}).get("tasks", {})
        task_cfg = tasks.get(task, {})
        if not task_cfg.get("llm_augment", False):
            return None
        return task_cfg.get("llm_provider") or self.get_llm_provider()

    # ── Hot Reload Settings ──────────────────────────────────────────────

    def is_hot_reload_enabled(self) -> bool:
        return self._config.get("hot_reload", {}).get("enabled", False)

    def get_hot_reload_interval(self) -> int:
        return self._config.get("hot_reload", {}).get("check_interval_seconds", 60)

    # ── Raw Access ───────────────────────────────────────────────────────

    @property
    def raw(self) -> Dict[str, Any]:
        """Access the raw config dict (for edge cases)."""
        return self._config


# Module-level singleton — import this everywhere
model_config = ModelConfig()
