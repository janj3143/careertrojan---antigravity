
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
Admin portal-only Streamlit sidebar help/guide utilities.
"""
import streamlit as st
from pathlib import Path

def show_help_sidebar():
    with st.sidebar.expander("ℹ️ Help & Guides", expanded=False):

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.markdown(
            """
            - [Master Roadmap](docs/master.md)
            - [Component Guide](docs/ENHANCED_ADMIN_COMPONENT_GUIDE.md)
            - [Parsing Guide](docs/ENHANCED_PARSING_GUIDE.md)
            - [Environment Management](docs/ENVIRONMENT_MANAGEMENT_COMPLETE.md)
            - [Multi-User Guide](docs/MULTI_USER_GUIDE.md)
            - [Troubleshooting](docs/TROUBLESHOOTING.md)
            """
        )
