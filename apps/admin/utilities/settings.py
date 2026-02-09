
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
IntelliCV Admin Portal - System Settings
========================================

Comprehensive system configuration and settings management.
Migrated from old admin portal with enhanced security and validation.

Features:
- General system configuration
- Security settings
- Performance tuning
- Advanced configuration
- Environment management
- Configuration backup/restore

Author: IntelliCV AI System
Date: September 21, 2025
"""

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# Import shared components
try:
    from shared.components import render_section_header, render_metrics_row
    from shared.utils import get_session_state, set_session_state
    SHARED_AVAILABLE = True
except ImportError:
    SHARED_AVAILABLE = False

class SettingsManager:
    """Comprehensive settings management system"""
    
    def __init__(self):
        """Initialize settings manager"""
        self.base_path = Path(__file__).parent.parent
        self.config_path = self.base_path / "config"
        self.config_file = self.config_path / "admin_settings.json"
        self.backup_path = self.config_path / "backups"
        
        # Ensure directories exist
        self.config_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        
        # Default settings
        self.default_settings = {
            "general": {
                "system_name": "IntelliCV-AI",
                "admin_email": "admin@intellicv.com",
                "log_level": "INFO",
                "session_timeout": 30,
                "default_language": "English",
                "timezone": "UTC",
                "theme": "Light",
                "notifications_enabled": True
            },
            "security": {
                "enable_2fa": False,
                "require_strong_passwords": True,
                "max_login_attempts": 3,
                "password_min_length": 8,
                "allowed_ip_range": "0.0.0.0/0",
                "encryption_level": "AES-256",
                "audit_logging": True,
                "force_https": False,
                "session_encryption": True,
                "password_expiry_days": 90
            },
            "performance": {
                "max_concurrent_users": 100,
                "request_timeout": 30,
                "max_file_size_mb": 50,
                "cache_strategy": "Memory",
                "database_pool_size": 20,
                "enable_compression": True,
                "enable_cdn": False,
                "cleanup_interval_hours": 24,
                "batch_processing_size": 100,
                "concurrent_parsers": 4
            },
            "ai_system": {
                "enable_ai_processing": True,
                "ai_confidence_threshold": 0.8,
                "enable_career_analysis": True,
                "ai_model_version": "v2.1",
                "batch_ai_processing": True,
                "ai_learning_enabled": True,
                "ai_cache_results": True,
                "ai_timeout_seconds": 60
            },
            "advanced": {
                "debug_mode": False,
                "maintenance_mode": False,
                "api_rate_limit": "100/hour",
                "enable_metrics": True,
                "enable_profiling": False,
                "custom_css": "/* Custom styles */",
                "custom_javascript": "// Custom scripts",
                "external_api_key": "",
                "webhook_url": "",
                "backup_retention_days": 30
            }
        }
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file or return defaults"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_settings = {}
                for category, defaults in self.default_settings.items():
                    merged_settings[category] = {**defaults, **settings.get(category, {})}
                
                return merged_settings
            
        except Exception as e:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.error(f"Error loading settings: {e}")
        
        return self.default_settings.copy()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            # Create backup first
            self.create_backup()
            
            # Save new settings
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving settings: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create backup of current settings"""
        try:
            if self.config_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"admin_settings_backup_{timestamp}.json"
                backup_filepath = self.backup_path / backup_filename
                
                with open(self.config_file, 'r') as src, open(backup_filepath, 'w') as dst:
                    dst.write(src.read())
                
                return True
                
        except Exception as e:
            st.error(f"Error creating backup: {e}")
            
        return False
    
    def get_backups(self) -> List[Path]:
        """Get list of available backups"""
        try:
            backups = list(self.backup_path.glob("admin_settings_backup_*.json"))
            return sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True)
        except Exception:
            return []
    
    def restore_from_backup(self, backup_file: Path) -> bool:
        """Restore settings from backup"""
        try:
            with open(backup_file, 'r') as src, open(self.config_file, 'w') as dst:
                dst.write(src.read())
            return True
        except Exception as e:
            st.error(f"Error restoring backup: {e}")
            return False
    
    def validate_settings(self, settings: Dict[str, Any]) -> List[str]:
        """Validate settings and return list of errors"""
        errors = []
        
        try:
            # General settings validation
            general = settings.get("general", {})
            if not general.get("system_name", "").strip():
                errors.append("System name cannot be empty")
            
            if not general.get("admin_email", "").strip():
                errors.append("Admin email cannot be empty")
            
            # Security settings validation
            security = settings.get("security", {})
            password_length = security.get("password_min_length", 8)
            if password_length < 6 or password_length > 32:
                errors.append("Password minimum length must be between 6 and 32")
            
            max_attempts = security.get("max_login_attempts", 3)
            if max_attempts < 1 or max_attempts > 10:
                errors.append("Max login attempts must be between 1 and 10")
            
            # Performance settings validation
            performance = settings.get("performance", {})
            max_users = performance.get("max_concurrent_users", 100)
            if max_users < 1 or max_users > 10000:
                errors.append("Max concurrent users must be between 1 and 10000")
            
            timeout = performance.get("request_timeout", 30)
            if timeout < 5 or timeout > 600:
                errors.append("Request timeout must be between 5 and 600 seconds")
            
            # AI settings validation
            ai = settings.get("ai_system", {})
            confidence = ai.get("ai_confidence_threshold", 0.8)
            if confidence < 0.1 or confidence > 1.0:
                errors.append("AI confidence threshold must be between 0.1 and 1.0")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors

def render_general_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Render general settings tab"""
    st.subheader("🌐 General System Configuration")
    
    general = settings.get("general", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        system_name = st.text_input("System Name", value=general.get("system_name", "IntelliCV-AI"))
        admin_email = st.text_input("Admin Email", value=general.get("admin_email", "admin@intellicv.com"))
        log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"], 
                                index=["DEBUG", "INFO", "WARNING", "ERROR"].index(general.get("log_level", "INFO")))
        session_timeout = st.number_input("Session Timeout (minutes)", 
                                        min_value=5, max_value=1440, 
                                        value=general.get("session_timeout", 30))
    
    with col2:
        default_language = st.text_input("Default Language", value=general.get("default_language", "English"))
        timezone = st.text_input("Timezone", value=general.get("timezone", "UTC"))
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"], 
                           index=["Light", "Dark", "Auto"].index(general.get("theme", "Light")))
        notifications_enabled = st.checkbox("Enable Notifications", 
                                          value=general.get("notifications_enabled", True))
    
    return {
        "system_name": system_name,
        "admin_email": admin_email,
        "log_level": log_level,
        "session_timeout": session_timeout,
        "default_language": default_language,
        "timezone": timezone,
        "theme": theme,
        "notifications_enabled": notifications_enabled
    }

def render_security_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Render security settings tab"""
    st.subheader("🔐 Security Configuration")
    
    security = settings.get("security", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_2fa = st.checkbox("Enable 2FA", value=security.get("enable_2fa", False))
        require_strong_passwords = st.checkbox("Require Strong Passwords", 
                                             value=security.get("require_strong_passwords", True))
        max_login_attempts = st.number_input("Max Login Attempts", 
                                           min_value=1, max_value=10, 
                                           value=security.get("max_login_attempts", 3))
        password_min_length = st.number_input("Password Min Length", 
                                            min_value=6, max_value=32, 
                                            value=security.get("password_min_length", 8))
        password_expiry_days = st.number_input("Password Expiry (days)", 
                                             min_value=30, max_value=365, 
                                             value=security.get("password_expiry_days", 90))
    
    with col2:
        allowed_ip_range = st.text_input("Allowed IP Range", 
                                       value=security.get("allowed_ip_range", "0.0.0.0/0"))
        encryption_level = st.selectbox("Encryption Level", ["AES-128", "AES-256"], 
                                      index=["AES-128", "AES-256"].index(security.get("encryption_level", "AES-256")))
        audit_logging = st.checkbox("Enable Audit Logging", 
                                  value=security.get("audit_logging", True))
        force_https = st.checkbox("Force HTTPS", value=security.get("force_https", False))
        session_encryption = st.checkbox("Session Encryption", 
                                        value=security.get("session_encryption", True))
    
    return {
        "enable_2fa": enable_2fa,
        "require_strong_passwords": require_strong_passwords,
        "max_login_attempts": max_login_attempts,
        "password_min_length": password_min_length,
        "password_expiry_days": password_expiry_days,
        "allowed_ip_range": allowed_ip_range,
        "encryption_level": encryption_level,
        "audit_logging": audit_logging,
        "force_https": force_https,
        "session_encryption": session_encryption
    }

def render_performance_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Render performance settings tab"""
    st.subheader("⚡ Performance Settings")
    
    performance = settings.get("performance", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_concurrent_users = st.number_input("Max Concurrent Users", 
                                             min_value=1, max_value=10000, 
                                             value=performance.get("max_concurrent_users", 100))
        request_timeout = st.number_input("Request Timeout (seconds)", 
                                        min_value=5, max_value=600, 
                                        value=performance.get("request_timeout", 30))
        max_file_size_mb = st.number_input("Max File Size (MB)", 
                                         min_value=1, max_value=1000, 
                                         value=performance.get("max_file_size_mb", 50))
        cache_strategy = st.selectbox("Cache Strategy", ["Memory", "Redis", "File"], 
                                    index=["Memory", "Redis", "File"].index(performance.get("cache_strategy", "Memory")))
        batch_processing_size = st.number_input("Batch Processing Size", 
                                              min_value=10, max_value=1000, 
                                              value=performance.get("batch_processing_size", 100))
    
    with col2:
        database_pool_size = st.number_input("Database Pool Size", 
                                           min_value=5, max_value=100, 
                                           value=performance.get("database_pool_size", 20))
        enable_compression = st.checkbox("Enable Compression", 
                                       value=performance.get("enable_compression", True))
        enable_cdn = st.checkbox("Enable CDN", value=performance.get("enable_cdn", False))
        cleanup_interval_hours = st.number_input("Cleanup Interval (hours)", 
                                               min_value=1, max_value=168, 
                                               value=performance.get("cleanup_interval_hours", 24))
        concurrent_parsers = st.number_input("Concurrent Parsers", 
                                           min_value=1, max_value=16, 
                                           value=performance.get("concurrent_parsers", 4))
    
    return {
        "max_concurrent_users": max_concurrent_users,
        "request_timeout": request_timeout,
        "max_file_size_mb": max_file_size_mb,
        "cache_strategy": cache_strategy,
        "batch_processing_size": batch_processing_size,
        "database_pool_size": database_pool_size,
        "enable_compression": enable_compression,
        "enable_cdn": enable_cdn,
        "cleanup_interval_hours": cleanup_interval_hours,
        "concurrent_parsers": concurrent_parsers
    }

def render_ai_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Render AI system settings tab"""
    st.subheader("🤖 AI System Configuration")
    
    ai = settings.get("ai_system", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_ai_processing = st.checkbox("Enable AI Processing", 
                                         value=ai.get("enable_ai_processing", True))
        ai_confidence_threshold = st.slider("AI Confidence Threshold", 
                                          min_value=0.1, max_value=1.0, 
                                          value=ai.get("ai_confidence_threshold", 0.8),
                                          step=0.05)
        enable_career_analysis = st.checkbox("Enable Career Analysis", 
                                           value=ai.get("enable_career_analysis", True))
        batch_ai_processing = st.checkbox("Batch AI Processing", 
                                        value=ai.get("batch_ai_processing", True))
    
    with col2:
        ai_model_version = st.selectbox("AI Model Version", ["v1.0", "v2.0", "v2.1"], 
                                      index=["v1.0", "v2.0", "v2.1"].index(ai.get("ai_model_version", "v2.1")))
        ai_learning_enabled = st.checkbox("AI Learning Enabled", 
                                        value=ai.get("ai_learning_enabled", True))
        ai_cache_results = st.checkbox("Cache AI Results", 
                                     value=ai.get("ai_cache_results", True))
        ai_timeout_seconds = st.number_input("AI Timeout (seconds)", 
                                           min_value=10, max_value=300, 
                                           value=ai.get("ai_timeout_seconds", 60))
    
    return {
        "enable_ai_processing": enable_ai_processing,
        "ai_confidence_threshold": ai_confidence_threshold,
        "enable_career_analysis": enable_career_analysis,
        "batch_ai_processing": batch_ai_processing,
        "ai_model_version": ai_model_version,
        "ai_learning_enabled": ai_learning_enabled,
        "ai_cache_results": ai_cache_results,
        "ai_timeout_seconds": ai_timeout_seconds
    }

def render_advanced_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Render advanced settings tab"""
    st.subheader("🔧 Advanced Configuration")
    
    advanced = settings.get("advanced", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        debug_mode = st.checkbox("Debug Mode", value=advanced.get("debug_mode", False))
        maintenance_mode = st.checkbox("Maintenance Mode", value=advanced.get("maintenance_mode", False))
        api_rate_limit = st.text_input("API Rate Limit", value=advanced.get("api_rate_limit", "100/hour"))
        enable_metrics = st.checkbox("Enable Metrics", value=advanced.get("enable_metrics", True))
        enable_profiling = st.checkbox("Enable Profiling", value=advanced.get("enable_profiling", False))
    
    with col2:
        external_api_key = st.text_input("External API Key", 
                                       value=advanced.get("external_api_key", ""), 
                                       type="password")
        webhook_url = st.text_input("Webhook URL", value=advanced.get("webhook_url", ""))
        backup_retention_days = st.number_input("Backup Retention (days)", 
                                              min_value=7, max_value=365, 
                                              value=advanced.get("backup_retention_days", 30))
    
    custom_css = st.text_area("Custom CSS", 
                            value=advanced.get("custom_css", "/* Custom styles */"), 
                            height=100)
    custom_javascript = st.text_area("Custom JavaScript", 
                                   value=advanced.get("custom_javascript", "// Custom scripts"), 
                                   height=100)
    
    return {
        "debug_mode": debug_mode,
        "maintenance_mode": maintenance_mode,
        "api_rate_limit": api_rate_limit,
        "enable_metrics": enable_metrics,
        "enable_profiling": enable_profiling,
        "external_api_key": external_api_key,
        "webhook_url": webhook_url,
        "backup_retention_days": backup_retention_days,
        "custom_css": custom_css,
        "custom_javascript": custom_javascript
    }

def main():
    """Main function for system settings"""
    if SHARED_AVAILABLE:
        render_section_header(
            "⚙️ System Settings",
            "Comprehensive system configuration and settings management"
        )
    else:
        st.title("⚙️ System Settings")
        st.markdown("Comprehensive system configuration and settings management")
    
    # Initialize settings manager
    settings_manager = SettingsManager()
    
    # Load current settings
    current_settings = settings_manager.load_settings()
    
    # Settings tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🌐 General", 
        "🔐 Security", 
        "⚡ Performance", 
        "🤖 AI System",
        "🔧 Advanced",
        "💾 Backup & Restore"
    ])
    
    # Store updated settings
    updated_settings = current_settings.copy()
    
    with tab1:
        updated_settings["general"] = render_general_settings(current_settings)
    
    with tab2:
        updated_settings["security"] = render_security_settings(current_settings)
    
    with tab3:
        updated_settings["performance"] = render_performance_settings(current_settings)
    
    with tab4:
        updated_settings["ai_system"] = render_ai_settings(current_settings)
    
    with tab5:
        updated_settings["advanced"] = render_advanced_settings(current_settings)
    
    with tab6:
        st.subheader("💾 Configuration Management")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save Settings", type="primary"):
                # Validate settings
                errors = settings_manager.validate_settings(updated_settings)
                
                if errors:
                    st.error("❌ Settings validation failed:")
                    for error in errors:
                        st.error(f"• {error}")
                else:
                    if settings_manager.save_settings(updated_settings):
                        st.success("✅ Settings saved successfully!")
                        set_session_state("settings_saved", True)
                    else:
                        st.error("❌ Failed to save settings")
        
        with col2:
            if st.button("🔄 Reset to Defaults"):
                if st.button("⚠️ Confirm Reset", type="secondary"):
                    if settings_manager.save_settings(settings_manager.default_settings):
                        st.success("✅ Settings reset to defaults!")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Failed to reset settings")
        
        with col3:
            if st.button("📁 Create Backup"):
                if settings_manager.create_backup():
                    st.success("✅ Backup created successfully!")
                else:
                    st.error("❌ Failed to create backup")
        
        # Backup management
        st.subheader("📂 Backup Management")
        
        backups = settings_manager.get_backups()
        
        if backups:
            selected_backup = st.selectbox("Available Backups", 
                                         [b.name for b in backups])
            
            if selected_backup:
                backup_path = next(b for b in backups if b.name == selected_backup)
                backup_date = datetime.fromtimestamp(backup_path.stat().st_mtime)
                
                st.info(f"Backup created: {backup_date.strftime('%Y-%m-%d %H:%M:%S')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Restore from Backup"):
                        if settings_manager.restore_from_backup(backup_path):
                            st.success("✅ Settings restored from backup!")
                            st.experimental_rerun()
                        else:
                            st.error("❌ Failed to restore from backup")
                
                with col2:
                    if st.button("🗑️ Delete Backup"):
                        try:
                            backup_path.unlink()
                            st.success("✅ Backup deleted!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete backup: {e}")
        else:
            st.info("No backups available.")
    
    # Settings preview
    with st.expander("👁️ Settings Preview"):
        st.json(updated_settings)

if __name__ == "__main__":
    main()