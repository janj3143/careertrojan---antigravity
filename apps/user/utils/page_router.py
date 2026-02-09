import streamlit as st

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


def require_login(session_key="authenticated_user"):
    if session_key not in st.session_state or not st.session_state[session_key]:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.warning("You must log in to access this page.")
        st.stop()

def switch_page(page_name):
    from streamlit_extras.switch_page_button import switch_page as sp
    sp(page_name)