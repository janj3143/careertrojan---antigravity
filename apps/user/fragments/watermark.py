import streamlit as st
from pathlib import Path
import base64

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


def apply_watermark():
    """Injects a faint watermark background image with opacity 0.1, always centered."""
    logo_path = Path(__file__).parent.parent / "static" / "logo.png"
    if logo_path.exists():
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.markdown(f'''
        <style>
        /* Watermark for registration page (f), profile page (u), resume upload page (l) */
        .stApp::before {{
            content: "";
            position: fixed;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 200vw; height: 200vh;
            background: url("data:image/png;base64,{logo_b64}") center center / contain no-repeat;
            opacity: 0.2;
            z-index: 0;
            pointer-events: none;
            display: block;
        }}
        .stApp > * {{ position: relative; z-index: 1; }}
        </style>
        ''', unsafe_allow_html=True)