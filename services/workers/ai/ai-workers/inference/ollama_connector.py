"""
Ollama Connector for CareerTrojan
=================================

Provides a unified interface to local LLM models via Ollama.
Supports:
- Text Generation (Llama 2, Llama 3, Mistral)
- Embeddings (nomic-embed-text)
- Health Checks & Model Pulling

Usage:
    from services.ai_workers.inference.ollama_connector import OllamaConnector
    client = OllamaConnector()
    response = client.generate("Summarize this CV", model="llama3")
"""

import requests
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def _get_ollama_defaults() -> Dict[str, str]:
    """Read Ollama model defaults from config/models.yaml."""
    try:
        from config.model_config import model_config
        cfg = model_config.get_llm_config("ollama")
        return {
            "default_model": cfg.get("default_model", "llama3"),
            "embedding_model": cfg.get("embedding_model", "nomic-embed-text"),
            "base_url": cfg.get("base_url", "http://localhost:11434"),
        }
    except Exception:
        return {"default_model": "llama3", "embedding_model": "nomic-embed-text", "base_url": "http://localhost:11434"}

class OllamaConnector:
    def __init__(self, base_url: Optional[str] = None):
        defaults = _get_ollama_defaults()
        self.base_url = base_url or defaults["base_url"]
        self._default_model = defaults["default_model"]
        self._default_embed_model = defaults["embedding_model"]
        self.headers = {"Content-Type": "application/json"}
        
    def is_alive(self) -> bool:
        """Check if Ollama service is running"""
        try:
            res = requests.get(f"{self.base_url}/", timeout=2)
            return res.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """List available local models"""
        try:
            res = requests.get(f"{self.base_url}/api/tags")
            if res.status_code == 200:
                models = res.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def generate(self, prompt: str, model: Optional[str] = None, system: str = "") -> str:
        """Generate text completion — model from config/models.yaml"""
        model = model or self._default_model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system

        try:
            res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
            if res.status_code == 200:
                return res.json().get("response", "")
            else:
                logger.error(f"Ollama Error {res.status_code}: {res.text}")
                return ""
        except Exception as e:
            logger.error(f"Ollama generation exception: {e}")
            return ""

    def get_embeddings(self, text: str, model: Optional[str] = None) -> List[float]:
        """Generate embeddings — model from config/models.yaml"""
        model = model or self._default_embed_model
        payload = {
            "model": model,
            "prompt": text
        }
        try:
            res = requests.post(f"{self.base_url}/api/embeddings", json=payload, timeout=10)
            if res.status_code == 200:
                return res.json().get("embedding", [])
            return []
        except Exception as e:
            logger.error(f"Ollama embedding exception: {e}")
            return []

    def pull_model(self, model: str):
        """Pull a model if missing"""
        payload = {"name": model}
        try:
            logger.info(f"Pulling model {model}...")
            # Note: stream=True recommended for real usage, blocking here for simplicity
            requests.post(f"{self.base_url}/api/pull", json=payload, timeout=300)
            logger.info(f"Model {model} pull initiated/complete.")
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
