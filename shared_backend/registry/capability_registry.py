import os
import yaml
from loguru import logger
from threading import Lock

class CapabilityRegistry:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.config = {}
                cls._instance.data_root = os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final")
                cls._instance.config_path = os.path.join(cls._instance.data_root, "config", "registry.yaml")
                cls._instance.load_registry()
        return cls._instance

    def load_registry(self):
        """
        Loads the capability registry configuration from the L: drive.
        Safely defaults to empty if file is missing to avoid runtime crash.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Capability Registry loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load registry yaml: {e}")
                self.config = {}
        else:
            logger.warning(f"Registry config not found at {self.config_path}. Using defaults.")
            self.config = {}

    def is_feature_enabled(self, portal: str, feature: str) -> bool:
        """
        Checks if a specific feature is enabled for a given portal in the registry.
        Structure:
          capabilities:
            portals:
              user_portal:
                features: ["resume_upload", "job_match"]
        """
        capabilities = self.config.get("capabilities", {})
        portals = capabilities.get("portals", {})
        portal_config = portals.get(portal, {})
        allowed_features = portal_config.get("features", [])
        
        return feature in allowed_features

    def get_portal_theme(self, portal: str) -> dict:
        """
        Returns theme configuration if defined, otherwise empty dict.
        """
        capabilities = self.config.get("capabilities", {})
        portals = capabilities.get("portals", {})
        portal_config = portals.get(portal, {})
        return portal_config.get("theme", {})

# Global Instance
registry = CapabilityRegistry()
