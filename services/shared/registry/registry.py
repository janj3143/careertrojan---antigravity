import yaml
import os
import logging
from typing import Dict, Any, Optional

class RegistryLoader:
    """
    Loads and manages system capabilities and feature flags.
    Allows for dynamic toggling of features without code deployment.
    """
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RegistryLoader, cls).__new__(cls)
            cls._instance._load_registry()
        return cls._instance

    def _load_registry(self):
        """Loads the registry from yaml files."""
        # Load defaults first
        default_path = os.path.join(os.path.dirname(__file__), 'defaults.yaml')
        if os.path.exists(default_path):
            with open(default_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            logging.warning(f"Default registry not found at {default_path}")
            self._config = {}

        # Load overrides from environment or extra file if needed (Future Phase)
        # self._load_overrides()

    def check_capability(self, capability: str) -> bool:
        """
        Checks if a specific capability is enabled.
        Args:
            capability: Dot-notation string (e.g. 'parsing.resume_parsing')
        """
        keys = capability.split('.')
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return bool(value)
        except (KeyError, TypeError):
            return False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Attributes accessor"""
        return self._config.get(key, default)

registry = RegistryLoader()
