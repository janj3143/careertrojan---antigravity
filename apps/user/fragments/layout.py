"""
User Portal Layout Helper

Use this to give every user portal page:
- Consistent page_config (title, icon, wide layout)
- The standard user sidebar
- A header strip showing the page title and signed-in user
"""

import streamlit as st

from session import get_current_user
from fragments.sidebar import show_sidebar  # adjust path if needed


def render_user_layout(page_title: str, icon: str = "📂") -> None:
    """
    Initialise the standard user portal layout.

    Call this at the start of each user page's main() function:

        from user_fragments.layout import render_user_layout

        def main():
            render_user_layout("Resume Upload & Analysis", icon="📄")
            # ... rest of page body ...

    Args:
        page_title: Title to show in the browser tab and page header.
        icon: Emoji/icon for the browser tab.
    """
    # Page config (safe to call once per run)
    st.set_page_config(
        page_title=page_title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Render shared sidebar (no-op if not authenticated)
    show_sidebar()

    # Top-of-page header
    user = get_current_user()
    col_title, col_user = st.columns([3, 2])

    with col_title:
        st.markdown(f"## {page_title}")

    with col_user:
        if user:
            st.markdown(
                f"<div style='text-align: right; color: #4b5563;'>"
                f"Signed in as <strong>{user.display_name}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='text-align: right; color: #9ca3af;'>"
                "Not signed in</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

