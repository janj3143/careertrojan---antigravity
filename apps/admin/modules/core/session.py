
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

"""
Session Management for IntelliCV-AI Admin Portal
============================================

This module handles all session state management, 
user authentication, and state persistence.
"""

import streamlit as st
from typing import Any, Dict, Optional


class SessionManager:
    """Centralized session state management."""
    
    @staticmethod
    def initialize_session():
        """Initialize all session state variables."""
        defaults = {
            "current_section": "dashboard",
            "is_admin": False,
            "authenticated_user": None,
            "intelligence_engine": None,
            "market_data_cache": {},
            "user_preferences": {},
            "last_activity": None,
            "notification_count": 0
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

                st.session_state[key] = default_value
    
    @staticmethod
    def get_session_value(key: str, default: Any = None) -> Any:
        """Get a value from session state with optional default."""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set_session_value(key: str, value: Any) -> None:
        """Set a value in session state."""
        st.session_state[key] = value
    
    @staticmethod
    def update_session_values(updates: Dict[str, Any]) -> None:
        """Update multiple session state values at once."""
        for key, value in updates.items():
            st.session_state[key] = value
    
    @staticmethod
    def clear_session(keep_auth: bool = False) -> None:
        """Clear session state, optionally keeping authentication."""
        auth_keys = ["is_admin", "authenticated_user"] if keep_auth else []
        
        keys_to_keep = set(auth_keys)
        keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_keep]
        
        for key in keys_to_remove:
            del st.session_state[key]
        
        # Reinitialize
        SessionManager.initialize_session()
    
    @staticmethod
    def is_admin() -> bool:
        """Check if current user is authenticated as admin."""
        return st.session_state.get("is_admin", False)
    
    @staticmethod
    def get_current_user() -> Optional[str]:
        """Get current authenticated user."""
        return st.session_state.get("authenticated_user")
    
    @staticmethod
    def login_user(username: str) -> None:
        """Login a user and set admin privileges."""
        st.session_state.is_admin = True
        st.session_state.authenticated_user = username
    
    @staticmethod
    def logout_user() -> None:
        """Logout current user."""
        st.session_state.is_admin = False
        st.session_state.authenticated_user = None
    
    @staticmethod
    def get_navigation_section() -> str:
        """Get current navigation section."""
        return st.session_state.get("current_section", "dashboard")
    
    @staticmethod
    def set_navigation_section(section: str) -> None:
        """Set current navigation section."""
        st.session_state.current_section = section


# Global session manager instance
session_manager = SessionManager()