import streamlit as st
import os

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


def show_debug_sidebar():

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.sidebar.title("🐞 Debug Tools")

    debug_folder = "pages/99_debug"
    for filename in sorted(os.listdir(debug_folder)):
        if filename.endswith(".py") and not filename.startswith("__"):
            page_path = f"{debug_folder}/{filename}"
            label = filename.replace(".py", "").replace("_", " ").title()
            st.sidebar.page_link(page_path, label=f"🧪 {label}", help="Debug or diagnostic tool")

    st.sidebar.markdown("---")
    st.sidebar.caption("🧪 Debug Mode – Internal Use Only")
