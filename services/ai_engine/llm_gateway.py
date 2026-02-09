"""
CareerTrojan — Unified LLM Gateway
====================================

SINGLE entry point for ALL LLM/AI provider calls across the platform.
Replaces: LLMFactory, AIChatService (direct calls), OllamaConnector (direct calls).

All code should call:
    from services.ai_engine.llm_gateway import llm_gateway
    response = llm_gateway.generate("prompt here")
    response = llm_gateway.generate("prompt here", provider="anthropic")
    response = llm_gateway.generate("prompt here", provider="perplexity")

Features:
    - Reads all model names from config/models.yaml (zero hardcoding)
    - Provider fallback chain if primary fails
    - Unified response format across all providers
    - Health checks per provider
    - Hot-reloadable config
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ── Response Contract ────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    text: str
    provider: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    web_grounded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp,
            "web_grounded": self.web_grounded,
        }


# ── Provider Implementations ─────────────────────────────────────────────

class _OpenAIProvider:
    """OpenAI API (GPT-4, GPT-3.5, etc.)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = os.getenv(config.get("api_key_env", "OPENAI_API_KEY"))
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning("openai package not installed")

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> LLMResponse:
        if not self.client:
            return LLMResponse(text="", provider="openai", model="", success=False, error="Client not available")
        model = model or self.config.get("default_model", "gpt-4")
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=kwargs.get("messages", [{"role": "user", "content": prompt}]),
                max_tokens=kwargs.get("max_tokens", self.config.get("max_tokens", 1000)),
                temperature=kwargs.get("temperature", self.config.get("temperature", 0.7)),
            )
            return LLMResponse(
                text=response.choices[0].message.content or "",
                provider="openai",
                model=response.model,
                usage=response.usage.model_dump() if response.usage else {},
            )
        except Exception as e:
            return LLMResponse(text="", provider="openai", model=model, success=False, error=str(e))

    def is_available(self) -> bool:
        return self.client is not None and self.api_key is not None


class _AnthropicProvider:
    """Anthropic API (Claude)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = os.getenv(config.get("api_key_env", "ANTHROPIC_API_KEY"))
        self.client = None
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                logger.warning("anthropic package not installed")

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> LLMResponse:
        if not self.client:
            return LLMResponse(text="", provider="anthropic", model="", success=False, error="Client not available")
        model = model or self.config.get("default_model", "claude-sonnet-4-20250514")
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", self.config.get("max_tokens", 1000)),
                temperature=kwargs.get("temperature", self.config.get("temperature", 0.7)),
                messages=kwargs.get("messages", [{"role": "user", "content": prompt}]),
            )
            return LLMResponse(
                text=response.content[0].text if response.content else "",
                provider="anthropic",
                model=response.model,
                usage=response.usage.model_dump() if response.usage else {},
            )
        except Exception as e:
            return LLMResponse(text="", provider="anthropic", model=model, success=False, error=str(e))

    def is_available(self) -> bool:
        return self.client is not None and self.api_key is not None


class _GeminiProvider:
    """Google Gemini API"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = os.getenv(config.get("api_key_env", "GEMINI_API_KEY"))
        self.base_url = config.get("base_url", "https://generativelanguage.googleapis.com/v1beta/models")

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(text="", provider="gemini", model="", success=False, error="No API key")
        model = model or self.config.get("default_model", "gemini-pro")
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        timeout = self.config.get("timeout", 30)
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return LLMResponse(text=text, provider="gemini", model=model)
        except Exception as e:
            return LLMResponse(text="", provider="gemini", model=model, success=False, error=str(e))

    def is_available(self) -> bool:
        return bool(self.api_key)


class _PerplexityProvider:
    """Perplexity API (web-grounded)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = os.getenv(config.get("api_key_env", "PERPLEXITY_API_KEY"))
        self.base_url = config.get("base_url", "https://api.perplexity.ai/chat/completions")

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(text="", provider="perplexity", model="", success=False, error="No API key")
        model = model or self.config.get("default_model", "llama-3.1-sonar-large-128k-online")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": kwargs.get("messages", [{"role": "user", "content": prompt}]),
        }
        timeout = self.config.get("timeout", 30)
        try:
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return LLMResponse(text=text, provider="perplexity", model=model, web_grounded=True)
        except Exception as e:
            return LLMResponse(text="", provider="perplexity", model=model, success=False, error=str(e))

    def is_available(self) -> bool:
        return bool(self.api_key)


class _OllamaProvider:
    """Ollama (local LLMs — Llama3, Mistral, etc.)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "http://localhost:11434")

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> LLMResponse:
        model = model or self.config.get("default_model", "llama3")
        payload = {"model": model, "prompt": prompt, "stream": False}
        if kwargs.get("system"):
            payload["system"] = kwargs["system"]
        try:
            resp = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.config.get("timeout", 60))
            if resp.status_code == 200:
                text = resp.json().get("response", "")
                return LLMResponse(text=text, provider="ollama", model=model)
            return LLMResponse(text="", provider="ollama", model=model, success=False, error=f"HTTP {resp.status_code}")
        except Exception as e:
            return LLMResponse(text="", provider="ollama", model=model, success=False, error=str(e))

    def get_embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        model = model or self.config.get("embedding_model", "nomic-embed-text")
        try:
            resp = requests.post(f"{self.base_url}/api/embeddings", json={"model": model, "prompt": text}, timeout=10)
            return resp.json().get("embedding", []) if resp.status_code == 200 else []
        except Exception:
            return []

    def is_available(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/", timeout=2).status_code == 200
        except Exception:
            return False


class _VLLMProvider:
    """vLLM (OpenAI-compatible self-hosted)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "http://localhost:8000/v1")

    def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> LLMResponse:
        model = model or self.config.get("default_model", "llama-3-8b-instruct")
        payload = {
            "model": model,
            "messages": kwargs.get("messages", [{"role": "user", "content": prompt}]),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, timeout=self.config.get("timeout", 30))
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return LLMResponse(text=text, provider="vllm", model=data.get("model", model), usage=data.get("usage", {}))
        except Exception as e:
            return LLMResponse(text="", provider="vllm", model=model, success=False, error=str(e))

    def is_available(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/models", timeout=2).status_code == 200
        except Exception:
            return False


# ── Provider Registry ────────────────────────────────────────────────────

_PROVIDER_CLASSES = {
    "openai": _OpenAIProvider,
    "anthropic": _AnthropicProvider,
    "gemini": _GeminiProvider,
    "perplexity": _PerplexityProvider,
    "ollama": _OllamaProvider,
    "vllm": _VLLMProvider,
}


# ── Unified Gateway ─────────────────────────────────────────────────────

class LLMGateway:
    """
    Unified gateway for ALL LLM calls.

    Usage:
        gateway = LLMGateway()            # reads config/models.yaml
        resp = gateway.generate("Hello")  # uses default provider
        resp = gateway.generate("Hello", provider="anthropic")  # specific provider
        resp = gateway.generate("Hello", provider="perplexity") # web-grounded
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            # Import here to avoid circular dependency
            try:
                from config.model_config import model_config
                config = model_config.raw.get("llm", {})
            except ImportError:
                logger.warning("Could not import model_config — using empty config")
                config = {}

        self._config = config
        self._providers: Dict[str, Any] = {}
        self._init_providers()

    def _init_providers(self):
        """Initialize all enabled providers."""
        providers_config = self._config.get("providers", {})
        for name, cfg in providers_config.items():
            if cfg.get("enabled", False) and name in _PROVIDER_CLASSES:
                try:
                    self._providers[name] = _PROVIDER_CLASSES[name](cfg)
                    logger.info(f"LLM provider initialized: {name}")
                except Exception as e:
                    logger.error(f"Failed to init provider {name}: {e}")

    def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        Generate text using the specified provider (or default with fallback chain).

        Args:
            prompt: The text prompt
            provider: Specific provider name, or None for default + fallback chain
            **kwargs: model, max_tokens, temperature, messages, system

        Returns:
            LLMResponse with text, provider used, model, etc.
        """
        if provider:
            # Direct provider call — no fallback
            return self._call_provider(provider, prompt, **kwargs)

        # Use fallback chain
        chain = self._config.get("fallback_chain", ["openai"])
        default = self._config.get("default_provider", "openai")

        # Put default first if not already
        if default in chain:
            chain = [default] + [p for p in chain if p != default]

        for prov_name in chain:
            if prov_name in self._providers:
                resp = self._call_provider(prov_name, prompt, **kwargs)
                if resp.success:
                    return resp
                logger.warning(f"Provider {prov_name} failed: {resp.error}, trying next...")

        return LLMResponse(
            text="",
            provider="none",
            model="",
            success=False,
            error="All providers in fallback chain failed or unavailable",
        )

    def _call_provider(self, name: str, prompt: str, **kwargs) -> LLMResponse:
        """Call a specific provider."""
        prov = self._providers.get(name)
        if not prov:
            return LLMResponse(text="", provider=name, model="", success=False, error=f"Provider '{name}' not initialized")
        try:
            return prov.generate(prompt, **kwargs)
        except Exception as e:
            return LLMResponse(text="", provider=name, model="", success=False, error=str(e))

    def health_check(self) -> Dict[str, bool]:
        """Check availability of all providers."""
        return {name: prov.is_available() for name, prov in self._providers.items()}

    def list_providers(self) -> List[str]:
        """List all initialized provider names."""
        return list(self._providers.keys())

    def get_provider(self, name: str):
        """Get a raw provider instance (for provider-specific features like Ollama embeddings)."""
        return self._providers.get(name)

    def reload(self):
        """Re-read config and reinitialize providers."""
        try:
            from config.model_config import model_config
            model_config.reload()
            self._config = model_config.raw.get("llm", {})
            self._providers.clear()
            self._init_providers()
            logger.info("LLM Gateway reloaded from config")
        except Exception as e:
            logger.error(f"Failed to reload LLM Gateway: {e}")


# Module-level singleton
llm_gateway = LLMGateway()
