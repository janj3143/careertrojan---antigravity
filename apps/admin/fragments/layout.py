"""
Admin Portal Layout Helper

Use this to give every admin portal page:
- Consistent page_config (title, icon, wide layout)
- The standard admin sidebar
- A header strip with title + admin name
- A safety check that only admin users can access the page
"""

import streamlit as st

from session import get_current_user, require_role
from admin_fragments.sidebar_admin import show_admin_sidebar  # adjust path if needed


def render_admin_layout(page_title: str, icon: str = "🛡️") -> None:
    """
    Initialise the standard admin portal layout.

    Call this at the start of each admin page's main() function:

        from admin_fragments.layout import render_admin_layout

        def main():
            render_admin_layout("Service Status Monitor", icon="📡")
            # ... rest of page body ...

    Args:
        page_title: Title to show in the browser tab and page header.
        icon: Emoji/icon for the browser tab.
    """
    # Enforce admin access first
    admin_user = require_role(("admin",))

    # Page config
    st.set_page_config(
        page_title=f"Admin | {page_title}",
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Render admin sidebar
    show_admin_sidebar()

    # Top-of-page header
    user = get_current_user() or admin_user
    col_title, col_user = st.columns([3, 2])

    with col_title:
        st.markdown(f"## {page_title}")

    with col_user:
        if user:
            st.markdown(
                f"<div style='text-align: right; color: #4b5563;'>"
                f"Admin: <strong>{user.display_name}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='text-align: right; color: #9ca3af;'>"
                "Admin not identified</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
