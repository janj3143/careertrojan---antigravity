"""
Configuration management for User Portal.
Provides centralized configuration handling and environment setup.
"""

import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json
import streamlit as st
from .common import get_env_variable, safe_json_loads

@dataclass
class StreamlitConfig:
    """Streamlit application configuration."""
    page_title: str = "IntelliCV User Portal"
    page_icon: str = "📄"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    menu_items: Dict[str, Any] = field(default_factory=dict)
    theme: Dict[str, str] = field(default_factory=lambda: {
        "primaryColor": "#FF6B6B",
        "backgroundColor": "#FFFFFF",
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#262730"
    })

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "intellicv_user"
    user: str = "postgres"
    password: str = ""
    ssl_mode: str = "prefer"
    pool_size: int = 5
    max_overflow: int = 10

@dataclass
class RedisConfig:
    """Redis configuration for caching and sessions."""
    host: str = "localhost"
    port: int = 6379
    database: int = 1  # User portal uses database 1
    password: Optional[str] = None
    ssl: bool = False
    socket_timeout: int = 30
    decode_responses: bool = True

@dataclass
class SecurityConfig:
    """Security-related configuration."""
    secret_key: str = ""
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 8
    require_password_complexity: bool = True
    enable_two_factor: bool = False
    allowed_file_types: List[str] = field(default_factory=lambda: [
        'pdf', 'doc', 'docx', 'txt', 'rtf'
    ])
    max_file_size_mb: float = 10.0

@dataclass
class AIConfig:
    """AI service configuration."""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    default_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    enable_ai_features: bool = True
    ai_timeout_seconds: int = 30

@dataclass
class UIConfig:
    """User interface configuration."""
    show_debug_info: bool = False
    enable_dark_mode: bool = False
    default_language: str = "en"
    items_per_page: int = 10
    enable_animations: bool = True
    sidebar_width: int = 300
    custom_css_file: Optional[str] = None

@dataclass
class EmailConfig:
    """Email service configuration."""
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    use_tls: bool = True
    from_email: str = ""
    admin_email: str = ""

class ConfigManager:
    """Manages application configuration from multiple sources."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Optional path to JSON config file
        """
        self.config_file = config_file
        self._config_cache = {}
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from environment and config file."""
        # Load from config file if provided
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                self._config_cache.update(file_config)
            except Exception as e:
                st.warning(f"Could not load config file {self.config_file}: {str(e)}")
        
        # Override with environment variables
        self._load_env_config()
        
        # Create configuration objects
        self.streamlit = self._create_streamlit_config()
        self.database = self._create_database_config()
        self.redis = self._create_redis_config()
        self.security = self._create_security_config()
        self.ai = self._create_ai_config()
        self.ui = self._create_ui_config()
        self.email = self._create_email_config()
    
    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            # Database
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.database',
            'DB_USER': 'database.user',
            'DB_PASSWORD': 'database.password',
            
            # Redis
            'REDIS_HOST': 'redis.host',
            'REDIS_PORT': 'redis.port',
            'REDIS_DB': 'redis.database',
            'REDIS_PASSWORD': 'redis.password',
            
            # Security
            'SECRET_KEY': 'security.secret_key',
            'SESSION_TIMEOUT': 'security.session_timeout_minutes',
            'MAX_LOGIN_ATTEMPTS': 'security.max_login_attempts',
            
            # AI
            'OPENAI_API_KEY': 'ai.openai_api_key',
            'ANTHROPIC_API_KEY': 'ai.anthropic_api_key',
            'GOOGLE_API_KEY': 'ai.google_api_key',
            'DEFAULT_AI_MODEL': 'ai.default_model',
            
            # Email
            'SMTP_SERVER': 'email.smtp_server',
            'SMTP_PORT': 'email.smtp_port',
            'SMTP_USERNAME': 'email.smtp_username',
            'SMTP_PASSWORD': 'email.smtp_password',
            'FROM_EMAIL': 'email.from_email',
            'ADMIN_EMAIL': 'email.admin_email',
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        keys = path.split('.')
        current = self._config_cache
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        if isinstance(value, str):
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
        
        current[keys[-1]] = value
    
    def _create_streamlit_config(self) -> StreamlitConfig:
        """Create Streamlit configuration."""
        config_data = self._config_cache.get('streamlit', {})
        return StreamlitConfig(**config_data)
    
    def _create_database_config(self) -> DatabaseConfig:
        """Create database configuration."""
        config_data = self._config_cache.get('database', {})
        
        # Set defaults from environment
        config_data.setdefault('host', get_env_variable('DB_HOST', 'localhost'))
        config_data.setdefault('port', int(get_env_variable('DB_PORT', 5432)))
        config_data.setdefault('database', get_env_variable('DB_NAME', 'intellicv_user'))
        config_data.setdefault('user', get_env_variable('DB_USER', 'postgres'))
        config_data.setdefault('password', get_env_variable('DB_PASSWORD', ''))
        
        return DatabaseConfig(**config_data)
    
    def _create_redis_config(self) -> RedisConfig:
        """Create Redis configuration."""
        config_data = self._config_cache.get('redis', {})
        
        # Set defaults from environment
        config_data.setdefault('host', get_env_variable('REDIS_HOST', 'localhost'))
        config_data.setdefault('port', int(get_env_variable('REDIS_PORT', 6379)))
        config_data.setdefault('database', int(get_env_variable('REDIS_DB', 1)))
        config_data.setdefault('password', get_env_variable('REDIS_PASSWORD'))
        
        return RedisConfig(**config_data)
    
    def _create_security_config(self) -> SecurityConfig:
        """Create security configuration."""
        config_data = self._config_cache.get('security', {})
        
        # Generate secret key if not provided
        if not config_data.get('secret_key'):
            import secrets
            config_data['secret_key'] = secrets.token_hex(32)
        
        return SecurityConfig(**config_data)
    
    def _create_ai_config(self) -> AIConfig:
        """Create AI configuration."""
        config_data = self._config_cache.get('ai', {})
        
        # Set API keys from environment
        config_data.setdefault('openai_api_key', get_env_variable('OPENAI_API_KEY', ''))
        config_data.setdefault('anthropic_api_key', get_env_variable('ANTHROPIC_API_KEY', ''))
        config_data.setdefault('google_api_key', get_env_variable('GOOGLE_API_KEY', ''))
        
        return AIConfig(**config_data)
    
    def _create_ui_config(self) -> UIConfig:
        """Create UI configuration."""
        config_data = self._config_cache.get('ui', {})
        return UIConfig(**config_data)
    
    def _create_email_config(self) -> EmailConfig:
        """Create email configuration."""
        config_data = self._config_cache.get('email', {})
        return EmailConfig(**config_data)
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            path: Configuration path (e.g., 'database.host')
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        current = self._config_cache
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def update_config(self, path: str, value: Any) -> None:
        """
        Update configuration value.
        
        Args:
            path: Configuration path
            value: New value
        """
        self._set_nested_config(path, value)
        
        # Reload configuration objects
        self._load_configuration()
    
    def save_config(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: File path to save to (uses default if not provided)
        """
        save_path = file_path or self.config_file or "config/user_portal_config.json"
        
        try:
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(self._config_cache, f, indent=2)
            
            st.success(f"Configuration saved to {save_path}")
            
        except Exception as e:
            st.error(f"Could not save configuration: {str(e)}")

# Global configuration instance
_config_manager = None

def get_config() -> ConfigManager:
    """
    Get global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    global _config_manager
    
    if _config_manager is None:
        # Look for config file in common locations
        config_paths = [
            "config/user_portal_config.json",
            "../config/user_portal_config.json",
            "user_portal_config.json"
        ]
        
        config_file = None
        for path in config_paths:
            if Path(path).exists():
                config_file = path
                break
        
        _config_manager = ConfigManager(config_file)
    
    return _config_manager

def apply_streamlit_config(config: StreamlitConfig) -> None:
    """
    Apply Streamlit configuration to current page.
    
    Args:
        config: Streamlit configuration
    """
    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout=config.layout,
        initial_sidebar_state=config.initial_sidebar_state,
        menu_items=config.menu_items or None
    )

def load_custom_css(css_file: Optional[str] = None) -> None:
    """
    Load custom CSS for the application.
    
    Args:
        css_file: Path to CSS file
    """
    if css_file and Path(css_file).exists():
        try:
            with open(css_file, 'r') as f:
                css_content = f.read()
            
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
            
        except Exception as e:
            st.warning(f"Could not load CSS file {css_file}: {str(e)}")
    else:
        # Default CSS
        default_css = """
        <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        .stAlert {
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        
        .user-portal-header {
            background: linear-gradient(90deg, #FF6B6B 0%, #4ECDC4 100%);
            padding: 1rem;
            border-radius: 0.5rem;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #FF6B6B;
        }
        </style>
        """
        
        st.markdown(default_css, unsafe_allow_html=True)