"""
Centralized configuration loader for IntelliCV Admin Portal.
Loads config from a central location if available, else uses defaults.
"""
import os
from pathlib import Path
import json

class ConfigManager:
    def __init__(self):
        self.config = self._load_config()
        self.BASE_DIR = Path(self.config.get('base_dir', Path(__file__).parent))
        self.DATA_DIR = Path(self.config.get('data_dir', self.BASE_DIR / 'data'))
        self.LOGS_DIR = Path(self.config.get('logs_dir', self.DATA_DIR / 'logs'))
        self.UPLOAD_DIR = Path(self.config.get('upload_dir', self.DATA_DIR / 'uploads'))
        # Ensure directories exist
        for dir_path in [self.DATA_DIR, self.LOGS_DIR, self.UPLOAD_DIR]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        # Try to load from centralized config file
        config_path = os.environ.get('ADMIN_PORTAL_CONFIG', None)
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback to defaults
        return {}

    def get(self, key, default=None):
        return self.config.get(key, default)
