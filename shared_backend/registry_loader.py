import os
import yaml
from loguru import logger

DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final")
REGISTRY_PATH = os.path.join(DATA_ROOT, "config", "registry.yaml")

class CapabilityRegistry:
    def __init__(self):
        self.config = {}
        self.load_registry()

    def load_registry(self):
        """
        Loads the capability registry from ai_data_final.
        """
        if os.path.exists(REGISTRY_PATH):
            try:
                with open(REGISTRY_PATH, "r") as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Capability Registry loaded from {REGISTRY_PATH}")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self.config = {"version": "fallback", "capabilities": {}}
        else:
            logger.warning(f"Registry not found at {REGISTRY_PATH}. Using empty defaults.")
            self.config = {"version": "default", "capabilities": {}}

    def is_feature_enabled(self, portal, feature):
        """
        Checks if a specific feature is enabled for a portal.
        """
        portals_config = self.config.get("capabilities", {}).get("portals", {})
        portal_features = portals_config.get(portal, {}).get("features", [])
        return feature in portal_features

# Global registry instance
registry = CapabilityRegistry()
