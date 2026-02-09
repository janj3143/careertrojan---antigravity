
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
Watermark Utility - Optimized for Admin Portal
"""
import streamlit as st

def show_watermark():

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.markdown(
        """
        <div style='position: fixed; bottom: 10px; right: 10px; opacity: 0.2; font-size: 18px;'>
            IntelliCV Admin Portal
        </div>
        """,
        unsafe_allow_html=True
    )
