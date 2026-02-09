"""
LLM Service — Legacy Interface
==============================
NOTE: New code should use services.ai_engine.llm_gateway instead.
This module is retained for backward compatibility.
All model names are now read from config/models.yaml.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

def _get_model_default(provider: str, fallback: str) -> str:
    """Read default model from config/models.yaml, fallback to hardcoded."""
    try:
        from config.model_config import model_config
        return model_config.get_llm_model(provider)
    except Exception:
        return fallback

class LLMBackendType(Enum):
    OPENAI = "openai"
    VLLM = "vllm"
    ANTHROPIC = "anthropic"

class LLMRequest(ABC):
    """Abstract Request Object"""
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7

class LLMResponse(ABC):
    """Abstract Response Object"""
    text: str
    usage: Dict[str, int]
    model_name: str

class BaseLLMService(ABC):
    """Abstract Base Class for LLM Services"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

class OpenAIService(BaseLLMService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("⚠️ OpenAIService initialized without API Key. Calls will fail.")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            print("❌ 'openai' package not installed. Please run: pip install openai")
            self.client = None

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        if not self.client:
            return LLMResponse(text="Error: OpenAI client not available.", usage={}, model_name="error")
        
        try:
            response = self.client.chat.completions.create(
                model=kwargs.get("model", _get_model_default("openai", "gpt-4")),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7)
            )
            return LLMResponse(
                text=response.choices[0].message.content,
                usage=response.usage.model_dump() if response.usage else {},
                model_name=response.model
            )
        except Exception as e:
            return LLMResponse(text=f"OpenAI Error: {str(e)}", usage={}, model_name="error")

    def health_check(self) -> bool:
        return self.client is not None and self.api_key is not None

class AnthropicService(BaseLLMService):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("⚠️ AnthropicService initialized without API Key.")
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            print("❌ 'anthropic' package not installed. Please run: pip install anthropic")
            self.client = None

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        if not self.client:
            return LLMResponse(text="Error: Anthropic client not available.", usage={}, model_name="error")
        
        try:
            response = self.client.messages.create(
                model=kwargs.get("model", _get_model_default("anthropic", "claude-sonnet-4-20250514")),
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )
            return LLMResponse(
                text=response.content[0].text,
                usage=response.usage.model_dump() if response.usage else {},
                model_name=response.model
            )
        except Exception as e:
            return LLMResponse(text=f"Anthropic Error: {str(e)}", usage={}, model_name="error")

    def health_check(self) -> bool:
        return self.client is not None and self.api_key is not None

class VLLMService(BaseLLMService):
    def __init__(self, endpoint: str = "http://localhost:8000/v1"):
        self.endpoint = endpoint
        # Initialize local VLLM client

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        import requests
        try:
            # Real vLLM / OpenAI-compatible endpoint
            payload = {
                "model": _get_model_default("vllm", "llama-3-8b-instruct"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", 1000),
                "temperature": kwargs.get("temperature", 0.7)
            }
            response = requests.post(f"{self.endpoint}/chat/completions", json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model_name=data.get("model", "vllm-model")
            )
        except Exception as e:
            return LLMResponse(text=f"vLLM Error: {str(e)}", usage={}, model_name="error")
    
    def health_check(self) -> bool:
        # Ping endpoint
        return True

class LLMFactory:
    _instance = None
    _backend: LLMBackendType = LLMBackendType.OPENAI
    _service: BaseLLMService = None

    @classmethod
    def get_service(cls) -> BaseLLMService:
        if not cls._service:
            cls.initialize()
        return cls._service

    @classmethod
    def initialize(cls, backend: str = "openai", **kwargs):
        try:
            cls._backend = LLMBackendType(backend.lower())
        except ValueError:
            cls._backend = LLMBackendType.OPENAI
        
        if cls._backend == LLMBackendType.VLLM:
            cls._service = VLLMService(**kwargs)
        elif cls._backend == LLMBackendType.OPENAI:
            cls._service = OpenAIService(**kwargs)
        elif cls._backend == LLMBackendType.ANTHROPIC:
            cls._service = AnthropicService(**kwargs)
        # Add Anthropic etc.

    @classmethod
    def switch_backend(cls, backend: str):
        print(f"Switching LLM Backend to {backend}")
        cls.initialize(backend)
