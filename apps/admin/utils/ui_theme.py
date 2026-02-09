
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
UI Theme Utility - Optimized for Admin Portal
"""
import streamlit as st

def apply_theme():

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.markdown(
        """
        <style>
        .main {background-color: #f5f7fa;}
        .sidebar .sidebar-content {background-color: #e3eaf2;}
        </style>
        """,
        unsafe_allow_html=True
    )
