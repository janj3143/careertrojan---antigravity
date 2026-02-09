





































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































#!/usr/bin/env python3
"""
🧪 Sandbox Configuration Module for IntelliCV-AI User Portal Final
Comprehensive configuration management for testing and development

Features:
- Environment-specific settings
- Feature flag management
- Database configurations
- API endpoints and keys
- Performance tuning parameters
- Security settings
- Integration configurations

Date: September 29, 2025
Version: Sandbox Config v1.0
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import streamlit as st

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    name: str = "intellicv_sandbox"
    user: str = "sandbox_user"
    password: str = "sandbox_pass"
    ssl_mode: str = "prefer"
    pool_size: int = 10
    max_overflow: int = 20

@dataclass 
class RedisConfig:
    """Redis configuration for caching and sessions"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 30

@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret: str = "sandbox_jwt_secret_key_2025"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    two_factor_issuer: str = "IntelliCV-AI Sandbox"
    session_timeout_minutes: int = 60

@dataclass
class APIConfig:
    """External API configuration"""
    openai_api_key: str = "sandbox_openai_key"
    anthropic_api_key: str = "sandbox_anthropic_key"
    linkedin_api_key: str = "sandbox_linkedin_key"
    indeed_api_key: str = "sandbox_indeed_key"
    glassdoor_api_key: str = "sandbox_glassdoor_key"
    rate_limit_requests_per_minute: int = 100

@dataclass
class FeatureFlags:
    """Feature flag configuration"""
    enhanced_auth: bool = True
    admin_integration: bool = True
    analytics_dashboard: bool = True
    ai_processing: bool = True
    job_matching: bool = True
    resume_optimization: bool = True
    interview_prep: bool = True
    market_intelligence: bool = True
    email_notifications: bool = False  # Disabled in sandbox
    sms_notifications: bool = False   # Disabled in sandbox
    payment_processing: bool = False  # Disabled in sandbox
    third_party_integrations: bool = True
    beta_features: bool = True
    debug_mode: bool = True
    performance_monitoring: bool = True
    security_logging: bool = True

class SandboxConfiguration:
    """
    Comprehensive sandbox configuration manager
    Handles all settings for testing and development environment
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent
        self.config_file = self.config_dir / "sandbox_config.json"
        self.secrets_file = self.config_dir / "sandbox_secrets.json"
        
        # Configuration components
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.auth = AuthConfig()
        self.api = APIConfig()
        self.features = FeatureFlags()
        
        # Environment settings
        self.environment = "sandbox"
        self.debug = True
        self.testing = True
        
        # Load configurations
        self.load_configuration()
    
    def load_configuration(self):
        """Load configuration from files and environment variables"""
        # Load from JSON configuration file
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self._apply_config_data(config_data)
            except Exception as e:
                print(f"Warning: Failed to load configuration file: {e}")
        
        # Override with environment variables
        self._load_environment_variables()
        
        # Load secrets separately
        self._load_secrets()
    
    def _apply_config_data(self, config_data: Dict):
        """Apply configuration data to dataclass instances"""
        if "database" in config_data:
            for key, value in config_data["database"].items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)
        
        if "redis" in config_data:
            for key, value in config_data["redis"].items():
                if hasattr(self.redis, key):
                    setattr(self.redis, key, value)
        
        if "auth" in config_data:
            for key, value in config_data["auth"].items():
                if hasattr(self.auth, key):
                    setattr(self.auth, key, value)
        
        if "features" in config_data:
            for key, value in config_data["features"].items():
                if hasattr(self.features, key):
                    setattr(self.features, key, value)
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        # Database
        self.database.host = os.getenv("SANDBOX_DB_HOST", self.database.host)
        self.database.port = int(os.getenv("SANDBOX_DB_PORT", str(self.database.port)))
        self.database.name = os.getenv("SANDBOX_DB_NAME", self.database.name)
        self.database.user = os.getenv("SANDBOX_DB_USER", self.database.user)
        self.database.password = os.getenv("SANDBOX_DB_PASSWORD", self.database.password)
        
        # Redis
        self.redis.host = os.getenv("SANDBOX_REDIS_HOST", self.redis.host)
        self.redis.port = int(os.getenv("SANDBOX_REDIS_PORT", str(self.redis.port)))
        self.redis.password = os.getenv("SANDBOX_REDIS_PASSWORD", self.redis.password)
        
        # Authentication
        self.auth.jwt_secret = os.getenv("SANDBOX_JWT_SECRET", self.auth.jwt_secret)
        
        # APIs
        self.api.openai_api_key = os.getenv("SANDBOX_OPENAI_API_KEY", self.api.openai_api_key)
        self.api.anthropic_api_key = os.getenv("SANDBOX_ANTHROPIC_API_KEY", self.api.anthropic_api_key)
    
    def _load_secrets(self):
        """Load sensitive configuration from secrets file"""
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'r') as f:
                    secrets_data = json.load(f)
                
                # Apply secrets to API configuration
                if "api_keys" in secrets_data:
                    for key, value in secrets_data["api_keys"].items():
                        if hasattr(self.api, key):
                            setattr(self.api, key, value)
                
                # Apply secrets to auth configuration
                if "auth_secrets" in secrets_data:
                    for key, value in secrets_data["auth_secrets"].items():
                        if hasattr(self.auth, key):
                            setattr(self.auth, key, value)
                            
            except Exception as e:
                print(f"Warning: Failed to load secrets file: {e}")
    
    def save_configuration(self):
        """Save current configuration to file"""
        config_data = {
            "environment": self.environment,
            "debug": self.debug,
            "testing": self.testing,
            "last_updated": datetime.now().isoformat(),
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "name": self.database.name,
                "user": self.database.user,
                "ssl_mode": self.database.ssl_mode,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db,
                "max_connections": self.redis.max_connections,
                "socket_timeout": self.redis.socket_timeout
            },
            "auth": {
                "jwt_algorithm": self.auth.jwt_algorithm,
                "jwt_expiration_hours": self.auth.jwt_expiration_hours,
                "password_min_length": self.auth.password_min_length,
                "max_login_attempts": self.auth.max_login_attempts,
                "lockout_duration_minutes": self.auth.lockout_duration_minutes,
                "two_factor_issuer": self.auth.two_factor_issuer,
                "session_timeout_minutes": self.auth.session_timeout_minutes
            },
            "features": {
                "enhanced_auth": self.features.enhanced_auth,
                "admin_integration": self.features.admin_integration,
                "analytics_dashboard": self.features.analytics_dashboard,
                "ai_processing": self.features.ai_processing,
                "job_matching": self.features.job_matching,
                "resume_optimization": self.features.resume_optimization,
                "interview_prep": self.features.interview_prep,
                "market_intelligence": self.features.market_intelligence,
                "email_notifications": self.features.email_notifications,
                "sms_notifications": self.features.sms_notifications,
                "payment_processing": self.features.payment_processing,
                "third_party_integrations": self.features.third_party_integrations,
                "beta_features": self.features.beta_features,
                "debug_mode": self.features.debug_mode,
                "performance_monitoring": self.features.performance_monitoring,
                "security_logging": self.features.security_logging
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return (f"postgresql://{self.database.user}:{self.database.password}"
                f"@{self.database.host}:{self.database.port}/{self.database.name}")
    
    def get_redis_url(self) -> str:
        """Get formatted Redis URL"""
        if self.redis.password:
            return f"redis://:{self.redis.password}@{self.redis.host}:{self.redis.port}/{self.redis.db}"
        return f"redis://{self.redis.host}:{self.redis.port}/{self.redis.db}"
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return getattr(self.features, feature_name, False)
    
    def toggle_feature(self, feature_name: str) -> bool:
        """Toggle a feature flag and return new state"""
        if hasattr(self.features, feature_name):
            current_value = getattr(self.features, feature_name)
            new_value = not current_value
            setattr(self.features, feature_name, new_value)
            self.save_configuration()
            return new_value
        return False
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """Get Streamlit-specific configuration"""
        return {
            "page_title": "IntelliCV-AI Sandbox",
            "page_icon": "🧪",
            "layout": "wide",
            "initial_sidebar_state": "expanded",
            "menu_items": {
                'Get Help': 'https://docs.intellicv.ai/sandbox',
                'Report a bug': 'https://github.com/intellicv/issues',
                'About': '# IntelliCV-AI Sandbox\nDevelopment and testing environment'
            }
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG" if self.debug else "INFO",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "sandbox.log",
                    "mode": "a"
                }
            },
            "loggers": {
                "sandbox": {
                    "level": "DEBUG",
                    "handlers": ["console", "file"],
                    "propagate": False
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"]
            }
        }
    
    def render_config_dashboard(self):
        """Render configuration dashboard in Streamlit"""
        st.title("🔧 Sandbox Configuration")
        
        # Environment info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Environment", self.environment.title())
        with col2:
            st.metric("Debug Mode", "ON" if self.debug else "OFF")
        with col3:
            st.metric("Testing Mode", "ON" if self.testing else "OFF")
        
        # Feature flags section
        st.subheader("🎛️ Feature Flags")
        
        feature_cols = st.columns(3)
        feature_names = [
            ("enhanced_auth", "🔐 Enhanced Auth"),
            ("admin_integration", "👑 Admin Integration"),
            ("analytics_dashboard", "📊 Analytics"),
            ("ai_processing", "🤖 AI Processing"),
            ("job_matching", "🎯 Job Matching"),
            ("resume_optimization", "📄 Resume Optimization"),
            ("interview_prep", "🗣️ Interview Prep"),
            ("market_intelligence", "📈 Market Intelligence"),
            ("debug_mode", "🐛 Debug Mode"),
            ("performance_monitoring", "📊 Performance Monitoring"),
            ("security_logging", "🔒 Security Logging"),
            ("beta_features", "🧪 Beta Features")
        ]
        
        for i, (feature_key, feature_label) in enumerate(feature_names):
            with feature_cols[i % 3]:
                current_value = getattr(self.features, feature_key)
                new_value = st.checkbox(
                    feature_label, 
                    value=current_value,
                    key=f"config_{feature_key}"
                )
                
                if new_value != current_value:
                    setattr(self.features, feature_key, new_value)
                    self.save_configuration()
                    st.success(f"{'Enabled' if new_value else 'Disabled'} {feature_label}")
        
        # Database configuration
        st.subheader("🗄️ Database Configuration")
        with st.expander("Database Settings"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Host", value=self.database.host, disabled=True)
                st.number_input("Port", value=self.database.port, disabled=True)
                st.text_input("Database Name", value=self.database.name, disabled=True)
            with col2:
                st.text_input("User", value=self.database.user, disabled=True)
                st.text_input("SSL Mode", value=self.database.ssl_mode, disabled=True)
                st.number_input("Pool Size", value=self.database.pool_size, disabled=True)
        
        # Redis configuration
        st.subheader("📦 Redis Configuration")
        with st.expander("Redis Settings"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Redis Host", value=self.redis.host, disabled=True)
                st.number_input("Redis Port", value=self.redis.port, disabled=True)
            with col2:
                st.number_input("Database", value=self.redis.db, disabled=True)
                st.number_input("Max Connections", value=self.redis.max_connections, disabled=True)
        
        # Save configuration
        if st.button("💾 Save Configuration"):
            if self.save_configuration():
                st.success("✅ Configuration saved successfully!")
            else:
                st.error("❌ Failed to save configuration")


# Global configuration instance
sandbox_config = SandboxConfiguration()

def get_config() -> SandboxConfiguration:
    """Get the global sandbox configuration instance"""
    return sandbox_config

if __name__ == "__main__":
    # Test configuration
    config = SandboxConfiguration()
    print("✅ Sandbox configuration loaded successfully")
    print(f"Database URL: {config.get_database_url()}")
    print(f"Redis URL: {config.get_redis_url()}")
    print(f"Features enabled: {sum(1 for attr in dir(config.features) if not attr.startswith('_') and getattr(config.features, attr))}")