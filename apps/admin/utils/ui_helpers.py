
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
Admin portal-only Streamlit metric and widget helpers with tooltips.
"""
import streamlit as st

def metric_with_help(label, value, help_text):

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.metric(label, value, help=help_text)

def button_with_help(label, help_text, **kwargs):
    return st.button(label, help=help_text, **kwargs)

def selectbox_with_help(label, options, help_text, **kwargs):
    return st.selectbox(label, options, help=help_text, **kwargs)
