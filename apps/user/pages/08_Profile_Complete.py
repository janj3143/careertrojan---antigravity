"""
🎯 IntelliCV-AI Profile Setup / Completion
==========================================
Step 3: Profile & Onboarding Complete

- Confirms core account + subscription from session
- Captures a few key profile fields
- Marks profile as complete and routes user to the dashboard
- Now also wires in shared industry taxonomy + job-title context
"""

import streamlit as st
from datetime import datetime
import time

# ──────────────────────────────────────────────
# Optional imports (sidebar, error handler)
# ──────────────────────────────────────────────
try:
    from ..fragments.sidebar import show_sidebar
    SIDEBAR_AVAILABLE = True
except ImportError:
    SIDEBAR_AVAILABLE = False

try:
    from ..utils.error_handler import (
        handle_exceptions,
        log_user_action,
        show_error,
        show_success,
    )
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False

    def handle_exceptions(fn):
        return fn

    def log_user_action(*_, **__):
        pass

    def show_error(msg, details=None):
        st.error(f"❌ {msg}")

    def show_success(msg, details=None):
        st.success(f"✅ {msg}")


# ──────────────────────────────────────────────
# Shared taxonomy imports (industry + jobs)
# ──────────────────────────────────────────────
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]  # up from pages/ to user portal root
SHARED_BACKEND = ROOT / "shared_backend"
if str(SHARED_BACKEND) not in sys.path:
    sys.path.insert(0, str(SHARED_BACKEND))

try:
    from services.industry_taxonomy_service import (  # type: ignore
        list_high_level_industries,
        list_subindustries_for,
    )

    TAXONOMY_AVAILABLE = True
except Exception:
    TAXONOMY_AVAILABLE = False


# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="🎯 IntelliCV-AI | Profile",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

if SIDEBAR_AVAILABLE:
    try:
        show_sidebar()
    except Exception:
        pass


# ──────────────────────────────────────────────
# CSS – matches Login / Registration / Payment
# ──────────────────────────────────────────────
def load_css():
    css = """
    <style>
    .stApp {
        background: linear-gradient(
            135deg,
            rgba(102,126,234,0.45) 0%,
            rgba(118,75,162,0.55) 100%
        );
        background-attachment: fixed;
    }
    .main .block-container {
        background: rgba(255,255,255,0.97) !important;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
        margin-top: 1rem;
        max-width: 1100px;
        margin-left: auto;
        margin-right: auto;
        backdrop-filter: blur(10px);
    }
    .profile-header {
        background: linear-gradient(135deg,#667eea 0%,#764ba2 100%);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 22px rgba(0,0,0,0.2);
    }
    .profile-header h1 {
        margin: 0 0 0.3rem 0;
        font-size: 1.8rem;
    }
    .profile-header p {
        margin: 0;
        font-size: 0.95rem;
        opacity: 0.95;
    }
    .steps {
        display: flex;
        gap: 0.75rem;
        margin-top: 0.75rem;
        font-size: 0.85rem;
        flex-wrap: wrap;
    }
    .step-pill {
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
    }
    .step-pill.completed {
        background: #00c853;
        border-color: #00c853;
    }
    .step-pill.active {
        background: #ffffff;
        color: #4b2ea8;
    }
    .profile-card {
        background: white;
        padding: 1.75rem;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .summary-card {
        background: #f6f8fc;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dfe3ef;
        font-size: 0.95rem;
    }
    .summary-label {
        font-size: 0.85rem;
        color: #666;
    }
    .summary-value {
        font-weight: 600;
    }
    .highlight-pill {
        display: inline-block;
        padding: 0.25rem 0.8rem;
        border-radius: 999px;
        background: rgba(102,126,234,0.1);
        border: 1px solid rgba(102,126,234,0.4);
        font-size: 0.8rem;
        margin-right: 0.4rem;
        margin-bottom: 0.3rem;
    }
    #MainMenu, footer, header {
        visibility: hidden;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


load_css()

# Log page access
if ERROR_HANDLER_AVAILABLE:
    log_user_action(
        "page_view",
        {"page": "profile_complete", "timestamp": datetime.now().isoformat()},
    )


# ──────────────────────────────────────────────
# Ensure we have registration + payment context
# ──────────────────────────────────────────────
if "registration_data" not in st.session_state:
    show_error("Profile information requires a registered account. Please register first.")
    if st.button("🔙 Go to Registration"):
        try:
            st.switch_page("pages/03_Registration.py")
        except Exception:
            pass
    st.stop()

reg_data = st.session_state["registration_data"]

subscription_tier = st.session_state.get("subscription_tier", reg_data.get("subscription_tier", "free"))
subscription_name = st.session_state.get("subscription_name", reg_data.get("subscription_name", "Free Trial"))
subscription_price = st.session_state.get("subscription_price", reg_data.get("subscription_price", 0.0))


# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.markdown(
    """
<div class="profile-header">
  <h1>🎯 Set Up Your IntelliCV-AI Profile</h1>
  <p>Final step · Tell us a little more so we can personalise your career insights.</p>
  <div class="steps">
    <span class="step-pill completed">1. Account & Plan</span>
    <span class="step-pill completed">2. Payment / Free Activation</span>
    <span class="step-pill active">3. Profile</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### ℹ Account Snapshot")
    st.markdown(f"**User:** {reg_data.get('full_name', reg_data.get('username', 'Guest'))}")
    st.markdown(f"**Plan:** {subscription_name}")
    st.markdown(f"**Tier:** `{subscription_tier}`")
    st.markmarkdown(f"**Price:** ${float(subscription_price):.2f}")
    st.markdown("---")
    if st.button("🏠 Go to Home", use_container_width=True):
        try:
            st.switch_page("pages/01_Home.py")
        except Exception:
            pass


# ──────────────────────────────────────────────
# Layout – profile form + summary
# ──────────────────────────────────────────────
col_form, col_summary = st.columns([1.4, 1], gap="large")

# Defaults from session if we have them
existing_profile = st.session_state.get("user_profile", {}) or {}

default_headline = existing_profile.get("headline", "")
default_location = existing_profile.get("location", "")
default_role_focus = existing_profile.get("role_focus", existing_profile.get("target_job_title", ""))
default_industry = existing_profile.get("industry", existing_profile.get("primary_industry", ""))
default_search_status = existing_profile.get("search_status", "Exploring options")
default_linkedin = existing_profile.get("linkedin_url", "")

default_current_job_title = existing_profile.get("current_job_title", "")
default_primary_industry = existing_profile.get("primary_industry", default_industry)
default_subindustries = existing_profile.get("subindustries", [])
default_alt_targets = existing_profile.get("alternative_target_titles", [])


with col_form:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 👤 Core Profile Details")

    with st.form("profile_form", clear_on_submit=False):
        headline = st.text_input(
            "Professional Headline",
            placeholder="e.g. Senior Project Manager | Digital Transformation | Stakeholder Engagement",
            value=default_headline,
        )
        location = st.text_input(
            "Location (City / Region)",
            placeholder="e.g. Liverpool, UK",
            value=default_location,
        )

        # Current + target role
        current_job_title = st.text_input(
            "Current Job Title (optional)",
            placeholder="e.g. Senior Data Analyst",
            value=default_current_job_title,
        )

        role_focus = st.text_input(
            "Primary Target Role / Job Focus",
            placeholder="e.g. Data Analyst, Marketing Manager, Software Engineer",
            value=default_role_focus,
        )

        # Industry / sector – taxonomy-driven if available
        if TAXONOMY_AVAILABLE:
            high_level_industries = list_high_level_industries()
            if default_primary_industry in high_level_industries:
                idx = high_level_industries.index(default_primary_industry) + 1
            else:
                idx = 0

            primary_industry = st.selectbox(
                "Primary Industry / Sector",
                options=["(Select…)"] + high_level_industries,
                index=idx,
                help="This drives how UMarketU, Coaching Hub and Mentorship segment your market.",
            )

            # Subindustries for that selection
            subindustry_options = (
                list_subindustries_for(primary_industry)
                if primary_industry and primary_industry != "(Select…)"
                else []
            )

            subindustries = st.multiselect(
                "Key Subsectors / Verticals (optional)",
                options=subindustry_options,
                default=[s for s in default_subindustries if s in subindustry_options],
                help="Useful if you are focused on specific niches within your main industry.",
            )

            # For backwards compatibility with existing code that expects `industry`
            industry = primary_industry if primary_industry != "(Select…)" else default_industry
        else:
            primary_industry = default_primary_industry
            subindustries = default_subindustries
            industry = st.text_input(
                "Industry / Sector Focus",
                placeholder="e.g. Healthcare, FinTech, Education, Energy",
                value=default_industry,
            )

        search_status = st.selectbox(
            "Current Job Search Status",
            [
                "Actively looking",
                "Quietly exploring",
                "Not looking, open to ideas",
                "Contract / interim focus",
            ],
            index=(
                ["Actively looking", "Quietly exploring", "Not looking, open to ideas", "Contract / interim focus"]
                .index(default_search_status)
                if default_search_status in [
                    "Actively looking",
                    "Quietly exploring",
                    "Not looking, open to ideas",
                    "Contract / interim focus",
                ]
                else 1
            ),
        )

        linkedin_url = st.text_input(
            "LinkedIn Profile (optional)",
            placeholder="https://www.linkedin.com/in/your-profile",
            value=default_linkedin,
        )

        alt_targets_raw = st.text_area(
            "Alternative / Adjacent Target Roles (optional, one per line)",
            value="\n".join(default_alt_targets),
            height=80,
            help="e.g. Data Scientist, Analytics Engineer, BI Developer",
        )

        st.markdown("#### ✅ Ready to go?")
        confirm_ready = st.checkbox(
            "Yes, I'm happy with these details and ready to continue.",
            value=False,
        )

        submitted = st.form_submit_button("Save Profile & Go to Dashboard →")

    st.markdown("</div>", unsafe_allow_html=True)

# Summary column
with col_summary:
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Quick Summary")

    st.markdown('<div class="summary-card">', unsafe_allow_html=True)
    st.markdown('<span class="summary-label">Name</span><br>', unsafe_allow_html=True)
    st.markdown(
        f'<span class="summary-value">{reg_data.get("full_name", reg_data.get("username", "Not set"))}</span>',
        unsafe_allow_html=True,
    )

    st.markdown('<br><span class="summary-label">Plan</span><br>', unsafe_allow_html=True)
    st.markdown(
        f'<span class="summary-value">{subscription_name} (${float(subscription_price):.2f})</span>',
        unsafe_allow_html=True,
    )

    st.markdown("<br><span class=\"summary-label\">Email</span><br>", unsafe_allow_html=True)
    st.markdown(
        f'<span class="summary-value">{reg_data.get("email", "Not set")}</span>',
        unsafe_allow_html=True,
    )

    st.markdown("<br><span class=\"summary-label\">Focus</span><br>", unsafe_allow_html=True)
    tags_html = ""
    if default_role_focus or role_focus:
        tags_html += f'<span class="highlight-pill">{role_focus or default_role_focus}</span>'
    if industry or default_industry:
        tags_html += f'<span class="highlight-pill">{industry or default_industry}</span>'
    tags_html += f'<span class="highlight-pill">{search_status}</span>'
    st.markdown(tags_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Handle submission
# ──────────────────────────────────────────────
if submitted:
    if not (headline and location and role_focus):
        show_error("Please complete your headline, location, and primary role focus.")
    elif not confirm_ready:
        show_error("Please confirm you're happy with these details before continuing.")
    else:
        alternative_target_titles = [
            line.strip()
            for line in alt_targets_raw.splitlines()
            if line.strip()
        ]

        # If taxonomy wasn't available, primary_industry may still be empty;
        # in that case, fall back to the free-text `industry`
        final_primary_industry = primary_industry
        if not final_primary_industry or final_primary_industry == "(Select…)":
            final_primary_industry = industry

        profile_payload = {
            # Existing keys (keep for backwards compatibility)
            "headline": headline,
            "location": location,
            "role_focus": role_focus,
            "industry": industry,
            "search_status": search_status,
            "linkedin_url": linkedin_url,
            "updated_at": datetime.utcnow().isoformat(),
            # New taxonomy + job-title aware keys
            "current_job_title": current_job_title,
            "target_job_title": role_focus,
            "primary_industry": final_primary_industry,
            "subindustries": subindustries,
            "alternative_target_titles": alternative_target_titles,
        }

        # Store in session – real backend would persist this to DB
        st.session_state["user_profile"] = profile_payload
        st.session_state["profile_complete"] = True

        # Mark user as authenticated if not already
        if "authenticated_user" not in st.session_state:
            st.session_state["authenticated_user"] = reg_data.get("username", "user")
        if "user_role" not in st.session_state:
            st.session_state["user_role"] = "user"

        if ERROR_HANDLER_AVAILABLE:
            log_user_action(
                "profile_completed",
                {
                    "username": reg_data.get("username"),
                    "subscription_tier": subscription_tier,
                },
            )

        show_success("Profile saved. Taking you to your IntelliCV-AI dashboard...")
        time.sleep(0.9)
        try:
            st.switch_page("pages/04_Dashboard.py")
        except Exception:
            pass


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 1rem;">
  <p><strong>IntelliCV-AI</strong> | Profile set · You’re ready to explore your career data.</p>
  <p>📄 Next: upload your CV · 🎯 Explore UMarketU · 🔍 Match roles · 🧠 Use AI insights.</p>
</div>
""",
    unsafe_allow_html=True,
)
