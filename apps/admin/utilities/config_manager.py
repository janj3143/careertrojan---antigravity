
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

#!/usr/bin/env python3
"""
IntelliCV Admin Portal - Configuration Manager
==============================================

Advanced configuration management system for the IntelliCV platform.
Migrated from old admin portal with enhanced security and validation.

Features:
- Configuration management
- Environment settings
- Security configuration
- API key management
- System validation

Author: IntelliCV AI System
Date: September 21, 2025
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import toml
from cryptography.fernet import Fernet
import base64
import hashlib

# Import shared components
try:
    from shared.components import render_section_header, render_metrics_row
    from shared.utils import get_session_state, set_session_state
    SHARED_COMPONENTS_AVAILABLE = True
except ImportError:
    SHARED_COMPONENTS_AVAILABLE = False

class ConfigurationManager:
    """Advanced configuration management system"""
    
    def __init__(self):
        """Initialize configuration manager"""
        self.base_path = Path(__file__).parent.parent
        self.config_path = self.base_path / "config"
        self.backup_path = self.config_path / "backups"
        
        # Ensure directories exist
        self.config_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        
        # Configuration files
        self.config_files = {
            "app_config": self.config_path / "app_config.json",
            "database_config": self.config_path / "database_config.json",
            "ai_config": self.config_path / "ai_config.json",
            "security_config": self.config_path / "security_config.json",
            "environment": self.config_path / "environment.json"
        }
        
        # Initialize default configurations
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default configuration files"""
        default_configs = {
            "app_config": {
                "app_name": "IntelliCV Admin Portal",
                "version": "3.0.0",
                "debug": False,
                "log_level": "INFO",
                "max_upload_size": 16777216,  # 16MB
                "session_timeout": 3600,  # 1 hour
                "auto_refresh": True,
                "theme": "light",
                "timezone": "UTC"
            },
            "database_config": {
                "type": "sqlite",
                "path": "data/intellicv.db",
                "backup_enabled": True,
                "backup_interval": 86400,  # 24 hours
                "max_connections": 10,
                "connection_timeout": 30,
                "query_timeout": 300
            },
            "ai_config": {
                "enabled": True,
                "model_type": "hybrid",
                "confidence_threshold": 0.8,
                "batch_size": 32,
                "max_processing_time": 300,
                "cache_enabled": True,
                "cache_ttl": 3600,
                "auto_enrichment": True,
                "quality_checks": True
            },
            "security_config": {
                "authentication_required": True,
                "session_encryption": True,
                "api_rate_limiting": True,
                "max_login_attempts": 5,
                "password_min_length": 8,
                "password_require_special": True,
                "audit_logging": True,
                "data_encryption": True
            },
            "environment": {
                "environment": "production",
                "admin_email": "admin@intellicv.com",
                "support_email": "support@intellicv.com",
                "company_name": "IntelliCV",
                "api_base_url": "https://api.intellicv.com",
                "frontend_url": "https://intellicv.com",
                "allowed_origins": ["https://intellicv.com"]
            }
        }
        
        for config_name, config_data in default_configs.items():
            config_file = self.config_files[config_name]
            if not config_file.exists():
                self.save_config(config_name, config_data)
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_file = self.config_files.get(config_name)
            if not config_file or not config_file.exists():
                return {}
            
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.error(f"Error loading config {config_name}: {e}")
            return {}
    
    def save_config(self, config_name: str, config_data: Dict[str, Any]):
        """Save configuration to file"""
        try:
            config_file = self.config_files.get(config_name)
            if not config_file:
                raise ValueError(f"Unknown config: {config_name}")
            
            # Create backup before saving
            self.create_backup(config_name)
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return True
        except Exception as e:
            st.error(f"Error saving config {config_name}: {e}")
            return False
    
    def create_backup(self, config_name: str):
        """Create backup of configuration"""
        try:
            config_file = self.config_files.get(config_name)
            if not config_file or not config_file.exists():
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_path / f"{config_name}_{timestamp}.json"
            
            # Copy current config to backup
            import shutil
            shutil.copy2(config_file, backup_file)
            
            # Keep only last 10 backups
            self._cleanup_old_backups(config_name)
            
        except Exception as e:
            st.error(f"Error creating backup for {config_name}: {e}")
    
    def _cleanup_old_backups(self, config_name: str):
        """Keep only the most recent backups"""
        try:
            backup_files = list(self.backup_path.glob(f"{config_name}_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only 10 most recent backups
            for old_backup in backup_files[10:]:
                old_backup.unlink()
        except:
            pass
    
    def validate_config(self, config_name: str, config_data: Dict[str, Any]) -> List[str]:
        """Validate configuration data"""
        errors = []
        
        if config_name == "app_config":
            if not config_data.get("app_name"):
                errors.append("App name is required")
            if not config_data.get("version"):
                errors.append("Version is required")
            if config_data.get("max_upload_size", 0) <= 0:
                errors.append("Max upload size must be positive")
        
        elif config_name == "database_config":
            if not config_data.get("type"):
                errors.append("Database type is required")
            if not config_data.get("path"):
                errors.append("Database path is required")
        
        elif config_name == "ai_config":
            threshold = config_data.get("confidence_threshold", 0)
            if not 0 <= threshold <= 1:
                errors.append("Confidence threshold must be between 0 and 1")
            if config_data.get("batch_size", 0) <= 0:
                errors.append("Batch size must be positive")
        
        elif config_name == "security_config":
            min_length = config_data.get("password_min_length", 0)
            if min_length < 6:
                errors.append("Password minimum length should be at least 6")
            max_attempts = config_data.get("max_login_attempts", 0)
            if max_attempts <= 0:
                errors.append("Max login attempts must be positive")
        
        elif config_name == "environment":
            if not config_data.get("environment"):
                errors.append("Environment is required")
            if not config_data.get("admin_email"):
                errors.append("Admin email is required")
        
        return errors
    
    def get_config_history(self, config_name: str) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        try:
            backup_files = list(self.backup_path.glob(f"{config_name}_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            history = []
            for backup_file in backup_files[:10]:  # Show last 10 changes
                timestamp = backup_file.stem.split('_', 1)[1]
                formatted_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                
                history.append({
                    "timestamp": formatted_time,
                    "file": backup_file.name,
                    "size": backup_file.stat().st_size
                })
            
            return history
        except:
            return []
    
    def restore_config(self, config_name: str, backup_file: str) -> bool:
        """Restore configuration from backup"""
        try:
            backup_path = self.backup_path / backup_file
            if not backup_path.exists():
                return False
            
            config_file = self.config_files.get(config_name)
            if not config_file:
                return False
            
            # Create backup of current config before restore
            self.create_backup(config_name)
            
            # Restore from backup
            import shutil
            shutil.copy2(backup_path, config_file)
            
            return True
        except Exception as e:
            st.error(f"Error restoring config: {e}")
            return False

def render_app_configuration(config_manager: ConfigurationManager):
    """Render application configuration section"""
    st.subheader("⚙️ Application Configuration")
    
    config = config_manager.load_config("app_config")
    
    col1, col2 = st.columns(2)
    
    with col1:
        app_name = st.text_input("App Name", value=config.get("app_name", ""))
        version = st.text_input("Version", value=config.get("version", ""))
        debug = st.checkbox("Debug Mode", value=config.get("debug", False))
        log_level = st.selectbox("Log Level", 
                                ["DEBUG", "INFO", "WARNING", "ERROR"], 
                                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(config.get("log_level", "INFO")))
    
    with col2:
        max_upload_mb = st.number_input("Max Upload Size (MB)", 
                                       value=config.get("max_upload_size", 16777216) / (1024*1024),
                                       min_value=1.0, max_value=100.0)
        session_timeout = st.number_input("Session Timeout (minutes)", 
                                         value=config.get("session_timeout", 3600) / 60,
                                         min_value=5, max_value=480)
        auto_refresh = st.checkbox("Auto Refresh", value=config.get("auto_refresh", True))
        theme = st.selectbox("Theme", ["light", "dark"], 
                           index=0 if config.get("theme", "light") == "light" else 1)
    
    if st.button("💾 Save Application Config", type="primary"):
        new_config = {
            "app_name": app_name,
            "version": version,
            "debug": debug,
            "log_level": log_level,
            "max_upload_size": int(max_upload_mb * 1024 * 1024),
            "session_timeout": int(session_timeout * 60),
            "auto_refresh": auto_refresh,
            "theme": theme,
            "timezone": config.get("timezone", "UTC")
        }
        
        errors = config_manager.validate_config("app_config", new_config)
        if errors:
            for error in errors:
                st.error(error)
        else:
            if config_manager.save_config("app_config", new_config):
                st.success("✅ Application configuration saved!")

def render_database_configuration(config_manager: ConfigurationManager):
    """Render database configuration section"""
    st.subheader("🗄️ Database Configuration")
    
    config = config_manager.load_config("database_config")
    
    col1, col2 = st.columns(2)
    
    with col1:
        db_type = st.selectbox("Database Type", ["sqlite", "postgresql", "mysql"], 
                              index=["sqlite", "postgresql", "mysql"].index(config.get("type", "sqlite")))
        db_path = st.text_input("Database Path", value=config.get("path", ""))
        backup_enabled = st.checkbox("Backup Enabled", value=config.get("backup_enabled", True))
        backup_interval = st.number_input("Backup Interval (hours)", 
                                         value=config.get("backup_interval", 86400) / 3600,
                                         min_value=1, max_value=168)
    
    with col2:
        max_connections = st.number_input("Max Connections", 
                                         value=config.get("max_connections", 10),
                                         min_value=1, max_value=100)
        connection_timeout = st.number_input("Connection Timeout (seconds)", 
                                            value=config.get("connection_timeout", 30),
                                            min_value=5, max_value=300)
        query_timeout = st.number_input("Query Timeout (seconds)", 
                                       value=config.get("query_timeout", 300),
                                       min_value=30, max_value=3600)
    
    if st.button("💾 Save Database Config", type="primary"):
        new_config = {
            "type": db_type,
            "path": db_path,
            "backup_enabled": backup_enabled,
            "backup_interval": int(backup_interval * 3600),
            "max_connections": max_connections,
            "connection_timeout": connection_timeout,
            "query_timeout": query_timeout
        }
        
        errors = config_manager.validate_config("database_config", new_config)
        if errors:
            for error in errors:
                st.error(error)
        else:
            if config_manager.save_config("database_config", new_config):
                st.success("✅ Database configuration saved!")

def render_ai_configuration(config_manager: ConfigurationManager):
    """Render AI system configuration section"""
    st.subheader("🤖 AI System Configuration")
    
    config = config_manager.load_config("ai_config")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enabled = st.checkbox("AI System Enabled", value=config.get("enabled", True))
        model_type = st.selectbox("Model Type", ["hybrid", "classification", "extraction"], 
                                 index=["hybrid", "classification", "extraction"].index(config.get("model_type", "hybrid")))
        confidence_threshold = st.slider("Confidence Threshold", 
                                        min_value=0.0, max_value=1.0, 
                                        value=config.get("confidence_threshold", 0.8),
                                        step=0.05)
        batch_size = st.number_input("Batch Size", 
                                    value=config.get("batch_size", 32),
                                    min_value=1, max_value=128)
    
    with col2:
        max_processing_time = st.number_input("Max Processing Time (seconds)", 
                                             value=config.get("max_processing_time", 300),
                                             min_value=30, max_value=3600)
        cache_enabled = st.checkbox("Cache Enabled", value=config.get("cache_enabled", True))
        cache_ttl = st.number_input("Cache TTL (seconds)", 
                                   value=config.get("cache_ttl", 3600),
                                   min_value=300, max_value=86400)
        auto_enrichment = st.checkbox("Auto Enrichment", value=config.get("auto_enrichment", True))
        quality_checks = st.checkbox("Quality Checks", value=config.get("quality_checks", True))
    
    if st.button("💾 Save AI Config", type="primary"):
        new_config = {
            "enabled": enabled,
            "model_type": model_type,
            "confidence_threshold": confidence_threshold,
            "batch_size": batch_size,
            "max_processing_time": max_processing_time,
            "cache_enabled": cache_enabled,
            "cache_ttl": cache_ttl,
            "auto_enrichment": auto_enrichment,
            "quality_checks": quality_checks
        }
        
        errors = config_manager.validate_config("ai_config", new_config)
        if errors:
            for error in errors:
                st.error(error)
        else:
            if config_manager.save_config("ai_config", new_config):
                st.success("✅ AI configuration saved!")

def render_security_configuration(config_manager: ConfigurationManager):
    """Render security configuration section"""
    st.subheader("🔒 Security Configuration")
    
    config = config_manager.load_config("security_config")
    
    col1, col2 = st.columns(2)
    
    with col1:
        auth_required = st.checkbox("Authentication Required", value=config.get("authentication_required", True))
        session_encryption = st.checkbox("Session Encryption", value=config.get("session_encryption", True))
        api_rate_limiting = st.checkbox("API Rate Limiting", value=config.get("api_rate_limiting", True))
        max_login_attempts = st.number_input("Max Login Attempts", 
                                           value=config.get("max_login_attempts", 5),
                                           min_value=1, max_value=20)
    
    with col2:
        password_min_length = st.number_input("Password Min Length", 
                                             value=config.get("password_min_length", 8),
                                             min_value=6, max_value=50)
        password_require_special = st.checkbox("Require Special Characters", 
                                              value=config.get("password_require_special", True))
        audit_logging = st.checkbox("Audit Logging", value=config.get("audit_logging", True))
        data_encryption = st.checkbox("Data Encryption", value=config.get("data_encryption", True))
    
    if st.button("💾 Save Security Config", type="primary"):
        new_config = {
            "authentication_required": auth_required,
            "session_encryption": session_encryption,
            "api_rate_limiting": api_rate_limiting,
            "max_login_attempts": max_login_attempts,
            "password_min_length": password_min_length,
            "password_require_special": password_require_special,
            "audit_logging": audit_logging,
            "data_encryption": data_encryption
        }
        
        errors = config_manager.validate_config("security_config", new_config)
        if errors:
            for error in errors:
                st.error(error)
        else:
            if config_manager.save_config("security_config", new_config):
                st.success("✅ Security configuration saved!")

def render_environment_configuration(config_manager: ConfigurationManager):
    """Render environment configuration section"""
    st.subheader("🌍 Environment Configuration")
    
    config = config_manager.load_config("environment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        environment = st.selectbox("Environment", ["development", "staging", "production"], 
                                  index=["development", "staging", "production"].index(config.get("environment", "production")))
        admin_email = st.text_input("Admin Email", value=config.get("admin_email", ""))
        support_email = st.text_input("Support Email", value=config.get("support_email", ""))
        company_name = st.text_input("Company Name", value=config.get("company_name", ""))
    
    with col2:
        api_base_url = st.text_input("API Base URL", value=config.get("api_base_url", ""))
        frontend_url = st.text_input("Frontend URL", value=config.get("frontend_url", ""))
        
        # Allowed origins
        current_origins = config.get("allowed_origins", [])
        origins_text = st.text_area("Allowed Origins (one per line)", 
                                   value="\n".join(current_origins))
    
    if st.button("💾 Save Environment Config", type="primary"):
        allowed_origins = [origin.strip() for origin in origins_text.split('\n') if origin.strip()]
        
        new_config = {
            "environment": environment,
            "admin_email": admin_email,
            "support_email": support_email,
            "company_name": company_name,
            "api_base_url": api_base_url,
            "frontend_url": frontend_url,
            "allowed_origins": allowed_origins
        }
        
        errors = config_manager.validate_config("environment", new_config)
        if errors:
            for error in errors:
                st.error(error)
        else:
            if config_manager.save_config("environment", new_config):
                st.success("✅ Environment configuration saved!")

def render_backup_management(config_manager: ConfigurationManager):
    """Render backup management section"""
    st.subheader("💾 Backup Management")
    
    # Configuration selector
    config_type = st.selectbox("Select Configuration", 
                              list(config_manager.config_files.keys()))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Available Backups")
        
        history = config_manager.get_config_history(config_type)
        
        if history:
            for backup in history:
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    st.text(backup["timestamp"].strftime("%Y-%m-%d %H:%M:%S"))
                
                with col_b:
                    st.text(f"{backup['size']} bytes")
                
                with col_c:
                    if st.button("Restore", key=f"restore_{backup['file']}"):
                        if config_manager.restore_config(config_type, backup["file"]):
                            st.success("✅ Configuration restored!")
                            st.rerun()
                        else:
                            st.error("❌ Restore failed!")
        else:
            st.info("No backups available")
    
    with col2:
        st.markdown("#### Backup Operations")
        
        if st.button("📁 Create Manual Backup", type="primary"):
            config_manager.create_backup(config_type)
            st.success("✅ Manual backup created!")
            st.rerun()
        
        if st.button("🧹 Clean Old Backups"):
            config_manager._cleanup_old_backups(config_type)
            st.success("✅ Old backups cleaned!")
            st.rerun()
        
        if st.button("📤 Export Configuration"):
            config_data = config_manager.load_config(config_type)
            if config_data:
                config_json = json.dumps(config_data, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=config_json,
                    file_name=f"{config_type}_config.json",
                    mime="application/json"
                )

def main():
    """Main function for configuration manager"""
    if SHARED_COMPONENTS_AVAILABLE:
        render_section_header(
            "⚙️ Configuration Manager",
            "Advanced configuration management and system settings"
        )
    else:
        st.title("⚙️ Configuration Manager")
        st.markdown("Advanced configuration management and system settings")
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "⚙️ Application",
        "🗄️ Database",
        "🤖 AI System",
        "🔒 Security", 
        "🌍 Environment",
        "💾 Backups"
    ])
    
    with tab1:
        render_app_configuration(config_manager)
    
    with tab2:
        render_database_configuration(config_manager)
    
    with tab3:
        render_ai_configuration(config_manager)
    
    with tab4:
        render_security_configuration(config_manager)
    
    with tab5:
        render_environment_configuration(config_manager)
    
    with tab6:
        render_backup_management(config_manager)
    
    # Configuration status sidebar
    with st.sidebar:
        st.markdown("### 📊 Configuration Status")
        
        # Load all configs and show status
        all_configs = {}
        for config_name in config_manager.config_files.keys():
            all_configs[config_name] = config_manager.load_config(config_name)
        
        for config_name, config_data in all_configs.items():
            if config_data:
                st.success(f"✅ {config_name.replace('_', ' ').title()}")
            else:
                st.error(f"❌ {config_name.replace('_', ' ').title()}")
        
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Reload All Configs"):
            st.rerun()
        
        if st.button("💾 Backup All Configs"):
            for config_name in config_manager.config_files.keys():
                config_manager.create_backup(config_name)
            st.success("All configs backed up!")
    
    # Usage guide
    with st.expander("ℹ️ Configuration Guide"):
        st.markdown("""
        ### Configuration Manager Features
        
        **Application Tab:**
        - Basic application settings
        - UI preferences and limits
        - Session and timeout settings
        
        **Database Tab:**
        - Database connection settings
        - Backup configuration
        - Performance tuning
        
        **AI System Tab:**
        - AI model configuration
        - Processing parameters
        - Cache and performance settings
        
        **Security Tab:**
        - Authentication settings
        - Password policies
        - Security features
        
        **Environment Tab:**
        - Environment-specific settings
        - Contact information
        - External service URLs
        
        **Backups Tab:**
        - Configuration backup management
        - Restore operations
        - Export functionality
        
        ### Best Practices
        - Always backup before major changes
        - Validate configurations after changes
        - Keep environment settings updated
        - Monitor security settings regularly
        - Use appropriate settings for each environment
        """)

if __name__ == "__main__":
    main()