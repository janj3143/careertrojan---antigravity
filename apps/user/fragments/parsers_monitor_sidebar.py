
import os
from datetime import datetime
import streamlit as st
from utils.utils_parsers import ensure_dirs, read_json, LOCK_DIR

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


def render_parsers_monitor():
    with st.sidebar:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.markdown("### Parsers Monitor")
        ensure_dirs()
        running = []
        try:
            for f in os.listdir(LOCK_DIR):
                if f.endswith(".lock"):
                    lk = read_json(os.path.join(LOCK_DIR, f))
                    if not lk:
                        continue
                    started = datetime.fromisoformat(lk["started_at"].replace("Z",""))
                    elapsed = int((datetime.utcnow() - started).total_seconds())
                    running.append((lk.get("task", "?"), elapsed))
        except FileNotFoundError:
            pass

        if running:
            for t, e in running:
                st.write(f"• {t}: **{e}s**")
            st.caption("This panel updates on refresh.")
        else:
            st.write("No parsers running.")
