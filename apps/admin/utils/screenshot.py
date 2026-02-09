
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
Screenshot Utility - Optimized for Admin Portal
"""
import os
import datetime
import streamlit as st

def capture_screenshot(page_label=None, save_dir="admin_screenshots"):
    raise RuntimeError(
        "Screenshot capture is not integrated. Refusing to write simulated screenshot data."
    )

def sidebar_capture_button(page_label):
    if st.sidebar.button("📸 Capture Screenshot", key="sidebar_capture"):
        try:
            path = capture_screenshot(page_label)
            st.sidebar.success(f"Screenshot saved: {os.path.basename(path)}")
        except Exception as e:
            st.sidebar.error(str(e))

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

