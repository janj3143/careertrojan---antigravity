"""
=============================================================================
AI Model Manager - Dynamic Model Selection and Auto-Upgrade
=============================================================================

Automatically detects and uses the latest available AI models from OpenAI,
Anthropic, Google, and other providers. Ensures the system always uses
the most advanced models available (GPT-4, GPT-5, GPT-20, etc.)

Features:
- Automatic model discovery and version detection
- Fallback to previous models if latest unavailable
- Support for multiple AI providers (OpenAI, Anthropic, Google, etc.)
- Model performance tracking and optimization
- Cost optimization with model tier selection
- Real-time model availability checking
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import streamlit as st

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AIModelManager:
    """
    Dynamic AI Model Manager with automatic version detection and upgrade
    """
    
    def __init__(self):
        self.cache_dir = Path("data/ai_models_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "model_availability_cache.json"
        self.cache_duration = timedelta(hours=6)  # Refresh every 6 hours
        
        # Model preferences by use case
        self.model_preferences = {
            "chat": ["gpt-5", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "code": ["gpt-5-code", "gpt-4-turbo", "gpt-4", "code-davinci-002"],
            "analysis": ["gpt-5-analysis", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "vision": ["gpt-5-vision", "gpt-4-vision-preview", "gpt-4-turbo-vision"],
            "embedding": ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"]
        }
        
        # Provider configurations
        self.providers = {
            "openai": {
                "enabled": OPENAI_AVAILABLE,
                "api_key_env": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1"
            },
            "anthropic": {
                "enabled": ANTHROPIC_AVAILABLE,
                "api_key_env": "ANTHROPIC_API_KEY",
                "base_url": "https://api.anthropic.com/v1"
            },
            "google": {
                "enabled": False,  # Add when implemented
                "api_key_env": "GOOGLE_API_KEY",
                "base_url": "https://generativelanguage.googleapis.com/v1"
            }
        }
        
        self.available_models = self._load_or_refresh_models()
    
    def _load_or_refresh_models(self) -> Dict[str, List[str]]:
        """Load cached models or refresh from API"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < self.cache_duration:
                    return cache_data.get('models', {})
            except Exception:
                pass
        
        # Refresh models from API
        return self._refresh_available_models()
    
    def _refresh_available_models(self) -> Dict[str, List[str]]:
        """Query APIs to get latest available models"""
        all_models = {
            "openai": [],
            "anthropic": [],
            "google": []
        }
        
        # OpenAI Models
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                models_response = client.models.list()
                
                # Extract model IDs and sort by version
                model_ids = [model.id for model in models_response.data]
                
                # Filter for relevant models (GPT, embeddings, etc.)
                gpt_models = [m for m in model_ids if 'gpt' in m.lower()]
                embedding_models = [m for m in model_ids if 'embedding' in m.lower()]
                
                all_models["openai"] = sorted(gpt_models, reverse=True) + embedding_models
                
            except Exception as e:
                # Fallback to known models if API fails
                all_models["openai"] = [
                    "gpt-4-turbo-preview",
                    "gpt-4-turbo",
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "text-embedding-3-large",
                    "text-embedding-3-small"
                ]
        
        # Anthropic Models (Claude)
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            try:
                # Anthropic doesn't have a models list endpoint, use known models
                all_models["anthropic"] = [
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307",
                    "claude-2.1",
                    "claude-2.0"
                ]
            except Exception:
                all_models["anthropic"] = ["claude-3-opus-20240229"]
        
        # Cache the results
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "models": all_models
        }
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            pass
        
        return all_models
    
    def get_best_model(self, use_case: str = "chat", provider: str = "openai") -> str:
        """
        Get the best available model for a specific use case
        
        Args:
            use_case: Type of task (chat, code, analysis, vision, embedding)
            provider: AI provider (openai, anthropic, google)
        
        Returns:
            Model ID of the best available model
        """
        # Get preference list for this use case
        preferred_models = self.model_preferences.get(use_case, self.model_preferences["chat"])
        
        # Get available models from provider
        available = self.available_models.get(provider, [])
        
        # Find first preferred model that's available
        for preferred in preferred_models:
            # Check for exact match
            if preferred in available:
                return preferred
            
            # Check for partial match (e.g., "gpt-5" matches "gpt-5-turbo")
            for avail in available:
                if preferred in avail:
                    return avail
        
        # Fallback to first available model
        if available:
            return available[0]
        
        # Ultimate fallback
        return "gpt-3.5-turbo" if provider == "openai" else "claude-3-sonnet-20240229"
    
    def get_latest_model_by_family(self, family: str = "gpt", provider: str = "openai") -> str:
        """
        Get the absolute latest model from a family (GPT, Claude, etc.)
        
        This ensures we always use GPT-5, GPT-20, or whatever is newest
        """
        available = self.available_models.get(provider, [])
        
        # Filter by family
        family_models = [m for m in available if family.lower() in m.lower()]
        
        if not family_models:
            return self.get_best_model("chat", provider)
        
        # Sort by version number (extract numbers from model name)
        def extract_version(model_name):
            import re
            numbers = re.findall(r'\d+', model_name)
            return [int(n) for n in numbers] if numbers else [0]
        
        family_models.sort(key=extract_version, reverse=True)
        
        return family_models[0]
    
    def get_model_info(self, model_id: str, provider: str = "openai") -> Dict[str, Any]:
        """Get detailed information about a specific model"""
        info = {
            "model_id": model_id,
            "provider": provider,
            "available": model_id in self.available_models.get(provider, []),
            "capabilities": [],
            "context_length": 0,
            "cost_per_1k_tokens": 0.0
        }
        
        # Add known capabilities and pricing
        if "gpt-5" in model_id:
            info["capabilities"] = ["chat", "code", "analysis", "vision", "reasoning"]
            info["context_length"] = 200000  # Estimated
            info["cost_per_1k_tokens"] = 0.10  # Estimated
        elif "gpt-4-turbo" in model_id:
            info["capabilities"] = ["chat", "code", "analysis", "vision"]
            info["context_length"] = 128000
            info["cost_per_1k_tokens"] = 0.01
        elif "gpt-4" in model_id:
            info["capabilities"] = ["chat", "code", "analysis"]
            info["context_length"] = 8192
            info["cost_per_1k_tokens"] = 0.03
        elif "gpt-3.5" in model_id:
            info["capabilities"] = ["chat", "code"]
            info["context_length"] = 16385
            info["cost_per_1k_tokens"] = 0.0005
        elif "claude-3-opus" in model_id:
            info["capabilities"] = ["chat", "code", "analysis", "reasoning"]
            info["context_length"] = 200000
            info["cost_per_1k_tokens"] = 0.015
        
        return info
    
    def force_refresh_models(self):
        """Force refresh of available models from all providers"""
        self.available_models = self._refresh_available_models()
        return self.available_models
    
    def get_all_available_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """Get all available models, optionally filtered by provider"""
        if provider:
            return {provider: self.available_models.get(provider, [])}
        return self.available_models
    
    def create_client(self, provider: str = "openai", model: Optional[str] = None):
        """
        Create an AI client configured with the best available model
        
        Args:
            provider: AI provider (openai, anthropic, google)
            model: Specific model to use, or None to auto-select best
        
        Returns:
            Configured AI client
        """
        if provider == "openai" and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            client = openai.OpenAI(api_key=api_key)
            
            # Store recommended model in client for easy access
            if model is None:
                model = self.get_latest_model_by_family("gpt", "openai")
            
            client._recommended_model = model
            return client
        
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
            client = anthropic.Anthropic(api_key=api_key)
            
            if model is None:
                model = self.get_latest_model_by_family("claude", "anthropic")
            
            client._recommended_model = model
            return client
        
        else:
            raise ValueError(f"Provider {provider} not available or not supported")


# Global instance for easy access
_model_manager = None

def get_model_manager() -> AIModelManager:
    """Get global AI Model Manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = AIModelManager()
    return _model_manager


def get_best_ai_client(use_case: str = "chat", provider: str = "openai"):
    """
    Convenience function to get an AI client with the best model
    
    Example:
        client = get_best_ai_client("code", "openai")
        response = client.chat.completions.create(
            model=client._recommended_model,
            messages=[{"role": "user", "content": "Write a Python function"}]
        )
    """
    manager = get_model_manager()
    model = manager.get_best_model(use_case, provider)
    client = manager.create_client(provider, model)
    return client


def get_latest_gpt_model() -> str:
    """Get the absolute latest GPT model (GPT-5, GPT-20, etc.)"""
    manager = get_model_manager()
    return manager.get_latest_model_by_family("gpt", "openai")


def get_latest_claude_model() -> str:
    """Get the absolute latest Claude model"""
    manager = get_model_manager()
    return manager.get_latest_model_by_family("claude", "anthropic")


# Streamlit UI Component for Model Selection
def render_model_selector(use_case: str = "chat") -> str:
    """
    Render a Streamlit UI component for model selection
    
    Returns the selected model ID
    """
    manager = get_model_manager()
    
    st.markdown("### 🤖 AI Model Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        provider = st.selectbox(
            "AI Provider",
            options=["openai", "anthropic", "google"],
            help="Select the AI provider"
        )
    
    with col2:
        auto_select = st.checkbox(
            "Auto-select latest model",
            value=True,
            help="Automatically use the newest available model (GPT-5, GPT-20, etc.)"
        )
    
    if auto_select:
        model = manager.get_latest_model_by_family("gpt" if provider == "openai" else "claude", provider)
        st.success(f"✅ Using latest model: **{model}**")
    else:
        available = manager.get_all_available_models(provider)[provider]
        model = st.selectbox(
            "Model Version",
            options=available,
            help="Select specific model version"
        )
    
    # Show model info
    model_info = manager.get_model_info(model, provider)
    
    with st.expander("📊 Model Information"):
        st.write(f"**Model ID:** {model_info['model_id']}")
        st.write(f"**Provider:** {model_info['provider']}")
        st.write(f"**Available:** {'✅ Yes' if model_info['available'] else '❌ No'}")
        st.write(f"**Capabilities:** {', '.join(model_info['capabilities'])}")
        st.write(f"**Context Length:** {model_info['context_length']:,} tokens")
        st.write(f"**Cost:** ${model_info['cost_per_1k_tokens']:.4f} per 1K tokens")
    
    # Refresh button
    if st.button("🔄 Refresh Available Models"):
        with st.spinner("Checking for new models..."):
            manager.force_refresh_models()
            st.success("Models refreshed!")
            st.rerun()
    
    return model
