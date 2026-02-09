import streamlit as st

from session import get_current_user


def show_sidebar() -> None:
    """Render the IntelliCV user portal sidebar.

    Sections (based on full pages list):
    - 🚀 Core Journey
        • 01_Home.py
        • 04_Dashboard.py
        • 09_Resume_Upload_Analysis.py
        • 10_UMarketU_Suite.py
    - 👤 Account & Onboarding
        • 02_Login.py
        • 03_Registration.py
        • 05_Payment.py
        • 07_Account_Verification.py
        • 08_Profile_Complete.py
    - 🎯 Growth & Coaching
        • 11_Coaching_Hub.py
        • 12_Mentorship_Marketplace.py
        • 13_Become_A_Mentor.py
        • 14_Dual_Career_Suite.py
        • 15_User_Rewards.py

    Behaviour:
    - Uses shared session model (get_current_user)
    - Falls back to legacy session_state['authenticated_user'] / ['user_role']
    - Does NOT show any admin or debug tools
    """
    user = get_current_user()

    # Backwards-compatible fallback
    legacy_auth = st.session_state.get("authenticated_user")
    legacy_role = st.session_state.get("user_role", "user")

    if not user and not legacy_auth:
        # No authenticated user -> no sidebar
        return

    display_name = user.display_name if user else str(legacy_auth)
    role = user.role.lower() if user else str(legacy_role).lower()

    # Track admin internally if needed elsewhere, but do NOT show admin UI here
    is_admin = role == "admin"
    st.session_state["is_admin"] = is_admin

    st.sidebar.title("📂 IntelliCV")
    st.sidebar.markdown(f"**Signed in as:** {display_name}")
    st.sidebar.markdown("---")

    def section(label: str) -> None:
        st.sidebar.markdown(f"### {label}")

    def divider() -> None:
        st.sidebar.markdown("---")

    # ──────────────────────────────────────────────
    # 🚀 Core Journey – main user tools
    # ──────────────────────────────────────────────
    section("🚀 Core Journey")

    # Primary navigation
    st.sidebar.page_link("pages/01_Home.py", label="🏠 Home")
    st.sidebar.page_link("pages/04_Dashboard.py", label="📊 Dashboard")

    # Core resume & market tools
    st.sidebar.page_link(
        "pages/09_Resume_Upload_Analysis.py",
        label="📄 Resume Upload & Analysis",
    )
    st.sidebar.page_link(
        "pages/10_UMarketU_Suite.py",
        label="🧩 UMarketU Suite",
    )

    divider()

    # ──────────────────────────────────────────────
    # 👤 Account & Onboarding
    # ──────────────────────────────────────────────
    section("👤 Account & Onboarding")

    st.sidebar.page_link("pages/02_Login.py", label="🔐 Login")
    st.sidebar.page_link("pages/03_Registration.py", label="🆕 Registration")
    st.sidebar.page_link("pages/05_Payment.py", label="💳 Payment & Billing")
    st.sidebar.page_link(
        "pages/07_Account_Verification.py",
        label="✅ Account Verification",
    )
    st.sidebar.page_link(
        "pages/08_Profile_Complete.py",
        label="📋 Profile Completion",
    )

    divider()

    # ──────────────────────────────────────────────
    # 🎯 Growth & Coaching
    # ──────────────────────────────────────────────
    section("🎯 Growth & Coaching")

    st.sidebar.page_link("pages/11_Coaching_Hub.py", label="🎤 Coaching Hub")
    st.sidebar.page_link(
        "pages/12_Mentorship_Marketplace.py",
        label="🤝 Mentorship Marketplace",
    )
    st.sidebar.page_link(
        "pages/13_Become_A_Mentor.py",
        label="🧑‍🏫 Become a Mentor",
    )
    st.sidebar.page_link(
        "pages/14_Dual_Career_Suite.py",
        label="🌓 Dual Career Suite",
    )
    st.sidebar.page_link(
        "pages/15_User_Rewards.py",
        label="🏅 User Rewards",
    )

    divider()

    st.sidebar.caption("© 2025 IntelliCV | User Portal")
