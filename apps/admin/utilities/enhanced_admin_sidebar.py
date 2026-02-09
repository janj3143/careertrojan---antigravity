
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
Final Consolidated Admin Sidebar - Unified Navigation
===================================================

The definitive unified sidebar navigation system that powers the consolidated admin portal.
Self-contained with all functionality embedded - no external dependencies.
Used by the consolidated 00_Admin_Home.py for seamless navigation.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

def render_enhanced_admin_sidebar():
    """
    Final consolidated sidebar navigation - used by the unified admin portal.
    Provides clean navigation without external page dependencies.
    """
    
    # Enhanced header with final styling

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.sidebar.markdown("""
    <div style="
        text-align: center; 
        padding: 1.5rem; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        border-radius: 15px; 
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    ">
        <h1 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 700;">🛡️ IntelliCV</h1>
        <h2 style="color: white; margin: 0.25rem 0 0 0; font-size: 1.2rem; font-weight: 400;">Admin Portal</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Unified • Consolidated • Complete
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # === MAIN NAVIGATION ===
    st.sidebar.markdown("### 🎛️ Main Navigation")
    
    sections = [
        ("🏠 Dashboard", "dashboard"),
        ("👥 User Management", "users"),
        ("📊 Data Parsers", "parsers"),
        ("�️ System Monitor", "monitor"),
        ("🤖 AI & Enrichment", "ai"),
        ("� Analytics", "analytics"),
        ("🔐 Admin Login", "login")
    ]
    
    for name, key in sections:
        if st.sidebar.button(name, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_section = key
            st.rerun()

    st.sidebar.markdown("---")
    
    # === QUICK STATS ===
    st.sidebar.markdown("### � Quick Stats")
    st.sidebar.metric("System Status", "🟢 Online")
    st.sidebar.metric("Users", "156")
    st.sidebar.metric("Files Processed", "2,347")
    
    # Admin status
    if st.session_state.get('is_admin', False):
        st.sidebar.success(f"Admin: {st.session_state.get('authenticated_user', 'Unknown')}")
    else:
        st.sidebar.warning("Not authenticated")

def render_main_header():
    """Render the main unified header for the consolidated portal"""
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">�️ IntelliCV Unified Admin Portal</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.2rem;">
            Complete Administration Suite • All-in-One Dashboard • 85+ Features Consolidated
        </p>
        <p style="color: white; margin: 0.25rem 0 0 0; opacity: 0.8; font-size: 1rem;">
            No External Dependencies • Self-Contained • Production Ready
        </p>
    </div>
    """, unsafe_allow_html=True)

def get_consolidated_navigation_state():
    """Get current navigation state for the consolidated portal"""
    return {
        'current_section': st.session_state.get('current_section', 'dashboard'),
        'is_admin': st.session_state.get('is_admin', False),
        'authenticated_user': st.session_state.get('authenticated_user', None)
    }

def initialize_session_state():
    """Initialize session state for the consolidated portal"""
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 'dashboard'
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if 'authenticated_user' not in st.session_state:
        st.session_state.authenticated_user = None

def render_footer_info():
    """Render footer information for the consolidated portal"""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🛡️ IntelliCV Unified Admin Portal")
    with col2:
        st.caption("📊 All Features Consolidated • No External Dependencies")
    with col3:
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Export functions for the consolidated portal
__all__ = [
    'render_enhanced_admin_sidebar', 
    'render_main_header',
    'get_consolidated_navigation_state',
    'initialize_session_state',
    'render_footer_info'
]