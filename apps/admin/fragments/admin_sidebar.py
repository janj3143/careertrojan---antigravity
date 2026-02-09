import streamlit as st

from session import get_current_user, require_role


def show_admin_sidebar() -> None:
    """
    IntelliCV – Admin Portal Sidebar

    Sections:
      - 🏠 Core Admin
      - 🧬 Data & Pipelines
      - 🧭 Intelligence Hubs
      - ⚙️ Models & Config
      - 🧑‍🏫 People & Mentoring
      - 🧪 Monitoring & Debug

    Behaviour:
      - Admin-only (require_role(("admin",))) – stops the page if not admin
      - Sets st.session_state["is_admin"] = True so older code paths still work
      - Uses page_link() to navigate to admin pages from admin_pages.zip
    """
    # Enforce admin role; this will st.stop() if not authorised
    user = require_role(("admin",))

    # Maintain compatibility with any existing checks
    st.session_state["is_admin"] = True

    st.sidebar.title("🛡️ IntelliCV Admin Portal")
    st.sidebar.markdown(f"**Admin:** {user.display_name}")
    st.sidebar.markdown("---")

    def section(label: str) -> None:
        st.sidebar.markdown(f"### {label}")

    def divider() -> None:
        st.sidebar.markdown("---")

    # ──────────────────────────────────────────────
    # 🏠 Core Admin
    # ──────────────────────────────────────────────
    section("🏠 Core Admin")

    st.sidebar.page_link("pages/00_Home.py", label="🏠 Admin Home")
    st.sidebar.page_link("pages/01_Service_Status_Monitor.py", label="📡 Service Status Monitor")
    st.sidebar.page_link("pages/02_Analytics.py", label="📊 Analytics")
    st.sidebar.page_link("pages/03_User_Management.py", label="👥 User Management")
    st.sidebar.page_link("pages/04_Compliance_Audit.py", label="⚖️ Compliance Audit")
    st.sidebar.page_link("pages/05_Email_Integration.py", label="📧 Email Integration")

    divider()

    # ──────────────────────────────────────────────
    # 🧬 Data & Pipelines
    # ──────────────────────────────────────────────
    section("🧬 Data & Pipelines")

    st.sidebar.page_link("pages/06_Complete_Data_Parser.py", label="🧬 Complete Data Parser")
    st.sidebar.page_link("pages/07_Batch_Processing.py", label="📦 Batch Processing (Test)")
    st.sidebar.page_link("pages/07_Batch_Processing_REAL_DATA.py", label="📦 Batch Processing – Real Data")
    st.sidebar.page_link("pages/08_AI_Enrichment.py", label="🧠 AI Enrichment Pipeline")
    st.sidebar.page_link("pages/09_AI_Content_Generator.py", label="✍️ AI Content Generator")

    divider()

    # ──────────────────────────────────────────────
    # 🧭 Intelligence Hubs
    # ──────────────────────────────────────────────
    section("🧭 Intelligence Hubs")

    st.sidebar.page_link("pages/10_Market_Intelligence_Center.py", label="📈 Market Intelligence Center")
    st.sidebar.page_link("pages/11_Competitive_Intelligence.py", label="🏁 Competitive Intelligence")
    st.sidebar.page_link("pages/12_Web_Company_Intelligence.py", label="🌐 Web Company Intelligence")
    st.sidebar.page_link("pages/23_Intelligence_Hub.py", label="🗺️ Intelligence Hub")
    st.sidebar.page_link("pages/24_Career_Pattern_Intelligence.py", label="📌 Career Pattern Intelligence")
    st.sidebar.page_link("pages/25_Exa_Web_Intelligence.py", label="🌐 Exa Web Intelligence")

    divider()

    # ──────────────────────────────────────────────
    # ⚙️ Models & Config
    # ──────────────────────────────────────────────
    section("⚙️ Models & Config")

    st.sidebar.page_link("pages/13_API_Integration.py", label="🔗 API Integration")
    st.sidebar.page_link("pages/14_Contact_Communication.py", label="✉️ Contact & Communication")
    st.sidebar.page_link("pages/15_Advanced_Settings.py", label="⚙️ Advanced Settings")
    st.sidebar.page_link("pages/18_Job_Title_AI_Integration.py", label="🧩 Job Title AI Integration")
    st.sidebar.page_link("pages/19_Job_Title_Overlap_Cloud.py", label="☁️ Job Title Overlap Cloud")
    st.sidebar.page_link("pages/20_Software_Requirements_Management.py", label="📋 Software Requirements Management")
    st.sidebar.page_link("pages/21_AI_Model_Training_Review.py", label="🧠 AI Model Training Review")
    st.sidebar.page_link("pages/10_Token_Management.py", label="🧮 Token Management")

    divider()

    # ──────────────────────────────────────────────
    # 🧑‍🏫 People & Mentoring
    # ──────────────────────────────────────────────
    section("🧑‍🏫 People & Mentoring")

    st.sidebar.page_link("pages/17_Mentor_Management.py", label="🧑‍🏫 Mentor Management")
    st.sidebar.page_link("pages/28_Mentor_Application_Review.py", label="📨 Mentor Application Review")

    divider()

    # ──────────────────────────────────────────────
    # 🧪 Monitoring & Debug
    # ──────────────────────────────────────────────
    section("🧪 Monitoring & Debug")

    st.sidebar.page_link(
        "pages/16_Logging_Error_Screen_Snapshot_and_Fixes.py",
        label="🐞 Logging & Error Snapshot",
    )
    st.sidebar.page_link(
        "pages/26_Unified_Analytics_Dashboard.py",
        label="📊 Unified Analytics Dashboard",
    )
    st.sidebar.page_link(
        "pages/27_System_Connectivity_Audit.py",
        label="🔌 System Connectivity Audit",
    )

    divider()
    st.sidebar.caption("🛡️ Admin Tools © IntelliCV 2025")
