
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

#!/usr/bin/env python3
"""
Configuration Manager Module
===========================

Centralized configuration management for the IntelliCV Admin Portal.
Handles application settings, environment variables, and configuration persistence.

Author: IntelliCV Admin Portal
Purpose: Centralized configuration management and settings
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime
import configparser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Centralized configuration manager for IntelliCV Admin Portal"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "admin_portal_config.json"
        self.config_path = Path(__file__).parent / self.config_file
        self.config = {}
        self.env_prefix = "INTELLICV_"
        
        # Load default configuration
        self._load_default_config()
        
        # Load configuration from file if exists
        self._load_config_file()
        
        # Override with environment variables
        self._load_env_config()
        
    def _load_default_config(self):
        """Load default configuration settings"""
        self.config = {
            "app": {
                "name": "IntelliCV Admin Portal",
                "version": "1.0.0",
                "debug": False,
                "environment": "development"
            },
            "database": {
                "type": "sqlite",
                "path": "admin_portal.db",
                "connection_timeout": 30
            },
            "ai": {
                "default_model": "gpt-3.5-turbo",
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 60
            },
            "parsing": {
                "max_file_size": 50 * 1024 * 1024,  # 50MB
                "supported_formats": ["pdf", "docx", "doc", "txt"],
                "batch_size": 10,
                "timeout": 300
            },
            "security": {
                "session_timeout": 3600,  # 1 hour
                "max_login_attempts": 5,
                "password_min_length": 8,
                "require_2fa": False
            },
            "logging": {
                "level": "INFO",
                "file": "admin_portal.log",
                "max_size": 10 * 1024 * 1024,  # 10MB
                "backup_count": 5
            },
            "email": {
                "enabled": True,
                "smtp_server": "",
                "smtp_port": 587,
                "use_tls": True,
                "timeout": 30
            },
            "cloud_mining": {
                "enabled": True,
                "providers": ["gmail", "outlook", "google_drive", "onedrive"],
                "batch_size": 50,
                "timeout": 300
            },
            "dashboard": {
                "refresh_interval": 30,
                "max_chart_points": 1000,
                "theme": "light",
                "page_size": 25
            }
        }
    
    def _load_config_file(self):
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info(f"Config file {self.config_path} not found, using defaults")
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    def _load_env_config(self):
        """Load configuration from environment variables"""
        try:
            # Check for environment variables with INTELLICV_ prefix
            for key, value in os.environ.items():
                if key.startswith(self.env_prefix):
                    config_key = key[len(self.env_prefix):].lower()
                    self._set_nested_config(config_key, value)
            logger.info("Environment configuration loaded")
        except Exception as e:
            logger.warning(f"Failed to load environment config: {e}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Recursively merge new configuration with existing"""
        def merge_dict(base: dict, update: dict):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self.config, new_config)
    
    def _set_nested_config(self, key_path: str, value: str):
        """Set nested configuration value from dot-separated key"""
        try:
            keys = key_path.split('_')
            config_ref = self.config
            
            # Navigate to the nested dictionary
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            # Convert string value to appropriate type
            final_key = keys[-1]
            config_ref[final_key] = self._convert_value(value)
            
        except Exception as e:
            logger.warning(f"Failed to set nested config {key_path}: {e}")
    
    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string value to appropriate Python type"""
        # Convert boolean values
        if value.lower() in ('true', 'yes', '1'):
            return True
        elif value.lower() in ('false', 'no', '0'):
            return False
        
        # Try to convert to number
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            # Return as string if conversion fails
            return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'app.name' or 'database.timeout')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.warning(f"Failed to get config key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'app.debug')
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key.split('.')
            config_ref = self.config
            
            # Navigate to the nested dictionary
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            
            # Set the value
            config_ref[keys[-1]] = value
            return True
            
        except Exception as e:
            logger.error(f"Failed to set config key '{key}': {e}")
            return False
    
    def save(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            save_config = self.config.copy()
            save_config['__metadata__'] = {
                'saved_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            # Save to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def reload(self) -> bool:
        """
        Reload configuration from all sources.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Reloading configuration...")
            
            # Reset and reload
            self._load_default_config()
            self._load_config_file()
            self._load_env_config()
            
            logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration as dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return self.config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get configuration section.
        
        Args:
            section: Section name (e.g., 'app', 'database')
            
        Returns:
            Section configuration dictionary
        """
        return self.config.get(section, {}).copy()
    
    def validate(self) -> Dict[str, Any]:
        """
        Validate current configuration.
        
        Returns:
            Validation results with status and issues
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            # Check required sections
            required_sections = ["app", "database", "ai", "parsing"]
            for section in required_sections:
                if section not in self.config:
                    validation_result["issues"].append(f"Missing required section: {section}")
                    validation_result["valid"] = False
            
            # Check file size limits
            max_file_size = self.get("parsing.max_file_size", 0)
            if max_file_size <= 0:
                validation_result["warnings"].append("Invalid parsing.max_file_size")
            
            # Check AI timeout
            ai_timeout = self.get("ai.timeout", 0)
            if ai_timeout <= 0:
                validation_result["warnings"].append("Invalid ai.timeout")
            
            # Check session timeout
            session_timeout = self.get("security.session_timeout", 0)
            if session_timeout <= 0:
                validation_result["warnings"].append("Invalid security.session_timeout")
            
        except Exception as e:
            validation_result["issues"].append(f"Validation error: {e}")
            validation_result["valid"] = False
        
        return validation_result

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager instance"""
    return config_manager

def initialize_config(config_file: Optional[str] = None) -> bool:
    """
    Initialize configuration manager with optional config file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        global config_manager
        config_manager = ConfigManager(config_file)
        
        # Validate configuration
        validation = config_manager.validate()
        if not validation["valid"]:
            logger.warning(f"Configuration validation issues: {validation['issues']}")
        
        if validation["warnings"]:
            logger.warning(f"Configuration warnings: {validation['warnings']}")
        
        logger.info("Configuration manager initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize configuration manager: {e}")
        return False

# Module test function
def test_config_manager():
    """Test configuration manager functionality"""
    print("Testing Configuration Manager...")
    
    print(f"App name: {config_manager.get('app.name')}")
    print(f"Debug mode: {config_manager.get('app.debug')}")
    print(f"Database type: {config_manager.get('database.type')}")
    
    # Test setting and getting
    config_manager.set('test.value', 'hello')
    print(f"Test value: {config_manager.get('test.value')}")
    
    # Test validation
    validation = config_manager.validate()
    print(f"Configuration valid: {validation['valid']}")
    
    print("Configuration Manager test completed.")

if __name__ == "__main__":
    test_config_manager()