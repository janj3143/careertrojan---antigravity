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

class OllamaConnector:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
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

    def generate(self, prompt: str, model: str = "llama3", system: str = "") -> str:
        """Generate text completion"""
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

    def get_embeddings(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Generate embeddings for text"""
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
