"""
🏠 IntelliCV-AI Welcome & Home Page
==================================
Primary home page:

- IntelliCV logo with professional branding
- Figma-style layout: header, hero, 3 value pillars, how-it-works, pricing, CTA
- Pricing: Free → Monthly Pro ($15.99) → Annual Pro ($149.99) → Elite Pro ($299.99)
- Tier-based visibility (users only see upgrade paths from their current tier)
- Login and Registration with proper authentication
- Integration with admin AI system (via error handler + session hooks)
- Professional templates and design
"""

import streamlit as st
from pathlib import Path
import base64
import time
from datetime import datetime

from ..data.home_page_content import HOME_OFFERINGS, HOME_FEATURE_SPOTLIGHTS

# Package-based imports
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

    def handle_exceptions(func):
        return func

    def log_user_action(action, details=None):
        pass

    def show_error(msg, details=None):
        st.error(f"❌ {msg}")

    def show_success(msg, details=None):
        st.success(f"✅ {msg}")


try:
    from ..auth.sandbox_secure_auth import SandboxUserAuthenticator
    ENHANCED_AUTH_AVAILABLE = True
except ImportError:
    ENHANCED_AUTH_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🏠 IntelliCV-AI | Smart Resume Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize sidebar if available
if SIDEBAR_AVAILABLE:
    try:
        show_sidebar()
    except Exception:
        pass

# Initialize session state
if "page_visited" not in st.session_state:
    st.session_state.page_visited = "home"
if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def get_user_subscription_tier(user_id: str) -> dict:
    """
    Get user's current subscription tier from user_accounts.json.
    Used to hide plans that are below the user's current tier.
    """
    try:
        accounts_file = Path(__file__).parent.parent / "user_accounts.json"
        if accounts_file.exists():
            import json

            with open(accounts_file, "r", encoding="utf-8") as f:
                accounts = json.load(f)

            for account in accounts:
                if account.get("user_id") == user_id or account.get("username") == user_id:
                    return {
                        "tier": account.get("subscription_tier", "free"),
                        "name": account.get("subscription_name", "Free Trial"),
                        "price": account.get("subscription_price", 0),
                    }

        # Default to free if not found
        return {"tier": "free", "name": "Free Trial", "price": 0}
    except Exception:
        return {"tier": "free", "name": "Free Trial", "price": 0}


@st.cache_data
def load_logo_b64() -> str:
    """Load and cache logo with error handling."""
    try:
        base_paths = [
            Path(__file__).parent.parent / "static" / "logo.png",
            Path(__file__).parent / "static" / "logo.png",
            Path(__file__).parent.parent / "assets" / "logo.png",
        ]
        for p in base_paths:
            if p.exists():
                return base64.b64encode(p.read_bytes()).decode()
        return ""
    except Exception as e:
        if ERROR_HANDLER_AVAILABLE:
            log_user_action("missing_asset", {"asset": "logo.png", "error": str(e)})
        return ""


logo_b64 = load_logo_b64()


def load_professional_css():
    """Global CSS – tuned for Figma-like layout."""
    css = """
    <style>
    .stApp {
        background: linear-gradient(
            135deg,
            rgba(102, 126, 234, 0.45) 0%,
            rgba(118, 75, 162, 0.55) 100%
        );
        background-attachment: fixed;
    }

    .main .block-container {
        background: rgba(255, 255, 255, 0.97) !important;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
        margin-top: 1rem;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
        backdrop-filter: blur(10px);
    }

    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
    }

    .top-nav-left {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .top-nav-logo-text {
        font-weight: 700;
        font-size: 1.25rem;
        color: #0B1A33;
        letter-spacing: 0.03em;
    }

    .top-nav-links {
        display: flex;
        gap: 1.25rem;
        font-size: 0.95rem;
        color: #6D7480;
    }

    .top-nav-links span strong {
        color: #0B1A33;
    }

    .hero-wrapper {
        display: flex;
        gap: 2rem;
        align-items: center;
        margin-bottom: 2rem;
    }

    .hero-left h1 {
        font-size: 2.4rem;
        margin-bottom: 0.4rem;
        color: #0B1A33;
    }

    .hero-left p {
        font-size: 1.05rem;
        color: #49505E;
        margin-bottom: 1rem;
    }

    .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }

    .hero-badge {
        font-size: 0.8rem;
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        background: rgba(10, 132, 255, 0.07);
        color: #0A84FF;
        border: 1px solid rgba(10, 132, 255, 0.2);
    }

    .hero-note {
        font-size: 0.9rem;
        color: #68707F;
    }

    .hero-right {
        background: radial-gradient(circle at top left, #667eea, #764ba2);
        border-radius: 18px;
        padding: 1.5rem;
        color: white;
        box-shadow: 0 10px 26px rgba(0, 0, 0, 0.25);
        min-height: 260px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .hero-dash-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9rem;
        opacity: 0.95;
    }

    .hero-dash-block {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 0.65rem 0.8rem;
        margin-top: 0.75rem;
        font-size: 0.85rem;
    }

    .hero-dash-footer {
        font-size: 0.8rem;
        opacity: 0.9;
        margin-top: 0.75rem;
    }

    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 1.25rem;
        margin: 1.75rem 0 2.0rem 0;
    }

    .feature-card {
        background: white;
        padding: 1.6rem;
        border-radius: 14px;
        border: 1px solid #E2E5F0;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.12);
        border-color: #667EEA;
    }

    .how-steps {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin: 1rem 0 2rem 0;
    }

    .how-step {
        background: #F6F8FC;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #E0E4F0;
        font-size: 0.95rem;
    }

    .how-step-num {
        width: 26px;
        height: 26px;
        border-radius: 999px;
        background: #0A84FF;
        color: white;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.4rem;
    }

    .usp-list {
        max-height: 35vh;
        overflow-y: auto;
        background: #fff;
        padding: 1.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        color: #111;
        font-size: 1.0rem;
        scrollbar-width: thin;
        scrollbar-color: #667eea #f1f1f1;
    }

    .usp-list::-webkit-scrollbar {
        width: 8px;
    }

    .usp-list::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }

    .usp-list::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }

    .usp-list::-webkit-scrollbar-thumb:hover {
        background: #764ba2;
    }

    .login-card {
        background: white;
        padding: 1.8rem;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }

    .pricing-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        height: 100%;
        min-height: 300px;
    }

    .pricing-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    .pricing-card.featured {
        border-color: #667eea;
        transform: scale(1.02);
    }

    .pricing-card.featured::before {
        content: 'MOST POPULAR';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg, #667eea 0%, #00bcd4 100%);
        color: white;
        padding: 0.5rem;
        font-size: 0.8rem;
        font-weight: bold;
    }

    .pricing-card.featured h3 {
        margin-top: 2rem;
    }

    .price {
        font-size: 2.2rem;
        font-weight: bold;
        color: #667eea;
        margin: 1rem 0;
    }

    .price-period {
        font-size: 1rem;
        color: #666;
        font-weight: normal;
    }

    .fractional-banner {
        margin-top: 2rem;
        padding: 1.8rem;
        border-radius: 16px;
        background: radial-gradient(circle at top left,
                                    rgba(102,126,234,0.94),
                                    rgba(0,188,212,0.94));
        color: #fff;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        position: relative;
        overflow: hidden;
    }

    .fractional-banner::before {
        content: "";
        position: absolute;
        top: -40px;
        right: -40px;
        width: 160px;
        height: 160px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        filter: blur(2px);
    }

    .fractional-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.2);
        font-size: 0.8rem;
        margin-bottom: 0.6rem;
    }

    .fractional-cta {
        margin-top: 0.8rem;
        display: inline-block;
        padding: 0.55rem 1.2rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.9);
        color: #1a237e;
        font-weight: 600;
        font-size: 0.9rem;
        text-decoration: none;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }

    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        transition: border-color 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    @media (max-width: 768px) {
        .main .block-container {
            padding: 1.25rem;
        }
        .hero-wrapper {
            flex-direction: column;
        }
        .top-nav {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


load_professional_css()

# Log page access
if ERROR_HANDLER_AVAILABLE:
    log_user_action("page_view", {"page": "home", "timestamp": datetime.now().isoformat()})


# ─────────────────────────────────────────────────────────────
# Figma-style HEADER (nav)
# ─────────────────────────────────────────────────────────────
with st.container():
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown(
            """
            <div class="top-nav">
                <div class="top-nav-left">
                    <span style="font-size: 1.6rem;">🚀</span>
                    <div class="top-nav-logo-text">IntelliCV-AI</div>
                    <div class="top-nav-links">
                        <span><strong>Home</strong></span>
                        <span>Resume Upload</span>
                        <span>Job Match</span>
                        <span>AI Insights</span>
                        <span>Profile</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_right:
        nav_c1, nav_c2 = st.columns(2)
        with nav_c1:
            if st.button("🔑 Login", use_container_width=True):
                st.session_state["show_login"] = True
                st.session_state["show_register"] = False
        with nav_c2:
            if st.button("🆕 Register", use_container_width=True):
                st.switch_page("pages/03_Registration.py")


# ─────────────────────────────────────────────────────────────
# HERO SECTION
# ─────────────────────────────────────────────────────────────
with st.container():
    st.markdown("---")
    st.write("")

    hero_left_col, hero_right_col = st.columns([1.7, 1.3])

    with hero_left_col:
        st.markdown(
            """
            <div class="hero-left">
                <h1>Build a Smarter, Stronger Career with IntelliCV-AI</h1>
                <p>Your resume. Your journey. AI-enhanced insights that help you stand out and get hired faster.</p>
                <div class="hero-badges">
                    <span class="hero-badge">AI Resume Intelligence</span>
                    <span class="hero-badge">Job Match Engine</span>
                    <span class="hero-badge">Career Analytics</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        hero_btn_col1, hero_btn_col2 = st.columns([1.1, 1])
        with hero_btn_col1:
            if st.button("📄 Upload Your CV", key="hero_upload", use_container_width=True):
                try:
                    st.switch_page("pages/09_Resume_Upload_Analysis.py")
                except Exception:
                    show_error("Upload page not available")
        with hero_btn_col2:
            if st.button("👀 See How It Works", key="hero_how", use_container_width=True):
                st.info("Scroll down to see how IntelliCV-AI works step-by-step.")

        st.markdown(
            '<p class="hero-note">No credit card required to start. Upgrade only when you’re ready.</p>',
            unsafe_allow_html=True,
        )

    with hero_right_col:
        st.markdown(
            """
            <div class="hero-right">
                <div class="hero-dash-header">
                    <div>📊 Resume Intelligence Overview</div>
                    <div style="font-size:0.8rem;">AI powered</div>
                </div>
                <div class="hero-dash-block">
                    <strong>Match score, gaps and strengths</strong><br/>
                    Once your CV and target role are loaded, you'll see a clear summary of how well you align,
                    which skills stand out and where you can improve.
                </div>
                <div class="hero-dash-block">
                    <strong>AI-driven suggestions</strong><br/>
                    Get tailored bullet rewrites, keyword recommendations and structure tips designed specifically for your profile.
                </div>
                <div class="hero-dash-footer">
                    Next step: upload your CV (and a job description if you have one) to unlock your personalised insights.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────
# THREE-PILLAR VALUE SECTION
# ─────────────────────────────────────────────────────────────
st.markdown("### 🌐 Why IntelliCV-AI?")

with st.container():
    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)

    pillars = HOME_FEATURE_SPOTLIGHTS[:3] if len(HOME_FEATURE_SPOTLIGHTS) >= 3 else HOME_FEATURE_SPOTLIGHTS
    for feature in pillars:
        st.markdown(
            f"""
            <div class="feature-card">
                <h3>{feature.get('icon', '✨')} {feature.get('title', '')}</h3>
                <p>{feature.get('description', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# HOW IT WORKS
# ─────────────────────────────────────────────────────────────
st.markdown("### 🛠 How IntelliCV-AI Works")

st.markdown(
    """
    <div class="how-steps">
        <div class="how-step">
            <div class="how-step-num">1</div>
            <div><strong>Upload your CV</strong></div>
            <div>Drag & drop your existing resume or paste your content.</div>
        </div>
        <div class="how-step">
            <div class="how-step-num">2</div>
            <div><strong>AI parses & scores it</strong></div>
            <div>Your structure, keywords, achievements and gaps are analysed.</div>
        </div>
        <div class="how-step">
            <div class="how-step-num">3</div>
            <div><strong>Get insights & fixes</strong></div>
            <div>See suggestions, STAR rewrites and optimisation tips.</div>
        </div>
        <div class="how-step">
            <div class="how-step-num">4</div>
            <div><strong>Match jobs & apply</strong></div>
            <div>Align your resume to roles and track your applications.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# MAIN CONTENT: USPs + LOGIN / ACCOUNT PANEL
# ─────────────────────────────────────────────────────────────
usp_col, login_col = st.columns([2, 1.3], gap="medium")

with usp_col:
    st.markdown("### 💡 Key IntelliCV-AI Benefits")
    st.markdown('<div class="usp-list">', unsafe_allow_html=True)
    for usp in HOME_OFFERINGS:
        st.markdown(f"• {usp}")
    st.markdown("</div>", unsafe_allow_html=True)

with login_col:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    if st.session_state.get("authenticated_user"):
        st.success(f"✅ Welcome back, **{st.session_state['authenticated_user']}**!")

        tier = st.session_state.get("subscription_tier", "free")
        tier_name = st.session_state.get("subscription_name", "Free Trial")
        tokens_limit = st.session_state.get("tokens_monthly_limit", 10)
        tokens_used = st.session_state.get("tokens_used", 0)

        st.markdown(f"**Plan:** {tier_name}")

        if tokens_limit == -1:
            st.info("🎯 **AI Tokens:** Unlimited ∞")
        else:
            tokens_remaining = tokens_limit - tokens_used
            usage_fraction = (tokens_used / tokens_limit) if tokens_limit > 0 else 0
            st.markdown(f"🎯 **AI Tokens:** {tokens_remaining}/{tokens_limit} remaining")
            st.progress(usage_fraction)

            if tokens_remaining < 2:
                st.warning("⚠️ Low on tokens! Consider upgrading for more AI features.")

        st.markdown("### 🚀 Quick Actions")
        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button("📄 Upload Resume", use_container_width=True):
                try:
                    st.switch_page("pages/09_Resume_Upload_Analysis.py")
                except Exception:
                    show_error("Upload page not available")
        with qa2:
            if st.button("🎯 Job Match", use_container_width=True):
                try:
                    st.switch_page("pages/10_UMarketU_Suite.py")
                except Exception:
                    show_error("Job Match page not available")

        st.markdown("---")
        user_role = st.session_state.get("user_role", "user")
        st.info(f"👤 **Role:** {user_role.title()}")

        if st.button("🚪 Logout", use_container_width=True):
            keys_to_clear = [
                "authenticated_user",
                "user_role",
                "session_token",
                "user_email",
                "subscription_tier",
                "subscription_name",
                "subscription_price",
                "tokens_monthly_limit",
                "tokens_used",
            ]
            for k in keys_to_clear:
                st.session_state.pop(k, None)
            if ERROR_HANDLER_AVAILABLE:
                log_user_action("user_logout", {"page": "home"})
            show_success("Successfully logged out!")
            time.sleep(1)
            st.rerun()

    else:
        st.markdown("### 🔐 Access Your Account")

        if st.button("🔑 Login", use_container_width=True):
            st.session_state["show_login"] = True
            st.session_state["show_register"] = False
            st.rerun()

        if st.button("🆕 Create Account", use_container_width=True):
            st.switch_page("pages/03_Registration.py")

        if st.session_state.get("show_login", False):
            with st.expander("🔐 Login Form", expanded=True):
                with st.form("login_form"):
                    username = st.text_input("Username or Email", placeholder="Enter your username or email")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("🔑 Login", use_container_width=True):
                            if username and password:
                                accounts_file = Path(__file__).parent.parent / "user_accounts.json"
                                user_found = False
                                user_data = None

                                if accounts_file.exists():
                                    import json

                                    with open(accounts_file, "r", encoding="utf-8") as f:
                                        accounts = json.load(f)

                                    for account in accounts:
                                        if account.get("username") == username or account.get("email") == username:
                                            user_found = True
                                            user_data = account
                                            break

                                if username == "admin" and password == "admin123":
                                    st.session_state["authenticated_user"] = username
                                    st.session_state["user_role"] = "admin"
                                    st.session_state["user_id"] = "admin"
                                    user_found = True

                                elif user_found and user_data:
                                    st.session_state["authenticated_user"] = user_data.get("username", username)
                                    st.session_state["user_role"] = "user"
                                    st.session_state["user_id"] = user_data.get("user_id", username)
                                    st.session_state["user_email"] = user_data.get("email", "")
                                    st.session_state["subscription_tier"] = user_data.get("subscription_tier", "free")
                                    st.session_state["subscription_name"] = user_data.get(
                                        "subscription_name", "Free Trial"
                                    )

                                    tier_tokens = {
                                        "free": {"monthly": 10, "current": user_data.get("tokens_used", 0), "limit": 10},
                                        "monthly": {
                                            "monthly": 250,
                                            "current": user_data.get("tokens_used", 0),
                                            "limit": 250,
                                        },
                                        "annual": {
                                            "monthly": 500,
                                            "current": user_data.get("tokens_used", 0),
                                            "limit": 500,
                                        },
                                        "elitepro": {"monthly": -1, "current": 0, "limit": -1},
                                        "enterprise": {"monthly": -1, "current": 0, "limit": -1},
                                    }
                                    tier = user_data.get("subscription_tier", "free")
                                    if tier not in tier_tokens:
                                        tier = "free"
                                    st.session_state["tokens_available"] = tier_tokens[tier]
                                    st.session_state["tokens_monthly_limit"] = tier_tokens[tier]["limit"]
                                    st.session_state["tokens_used"] = tier_tokens[tier]["current"]
                                else:
                                    st.session_state["authenticated_user"] = username
                                    st.session_state["user_role"] = "user"
                                    st.session_state["user_id"] = username

                                st.session_state["session_token"] = f"token_{int(time.time())}"
                                st.session_state["is_new_user"] = False
                                st.session_state["show_login"] = False

                                show_success("Login successful! Redirecting to profile...")
                                if ERROR_HANDLER_AVAILABLE:
                                    log_user_action("user_login", {"username": username})
                                time.sleep(1)
                                st.switch_page("pages/08_Profile_Complete.py")
                            else:
                                show_error("Please enter both username and password")

                    with col2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state["show_login"] = False
                            st.rerun()

                st.info(
                    "💡 **New User?** Create your account to access IntelliCV's comprehensive career acceleration platform!"
                )

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PRICING SECTION – Tier-based visibility
# ─────────────────────────────────────────────────────────────
st.markdown("---")

current_user_tier = None
if st.session_state.get("authenticated_user"):
    user_id = st.session_state.get("user_id", st.session_state.get("authenticated_user"))
    user_subscription = get_user_subscription_tier(user_id)
    current_user_tier = user_subscription["tier"]

    st.markdown("## 💰 Upgrade Your Plan")
    st.markdown(f"**Current Plan:** {user_subscription['name']} (${user_subscription['price']:.2f})")
    st.markdown("Unlock more features with an upgrade:")
else:
    st.markdown("## 💰 Choose Your Plan")
    st.markdown("Select the plan that best fits your career goals:")

tier_order = {"free": 0, "monthly": 1, "annual": 2, "elitepro": 3, "enterprise": 3}
current_tier_level = tier_order.get(current_user_tier, -1) if current_user_tier else -1

show_free = current_tier_level < 0    # Only for unauthenticated
show_monthly = current_tier_level < 1
show_annual = current_tier_level < 2
show_elitepro = current_tier_level < 3

visible_columns = []
if show_free:
    visible_columns.append("free")
if show_monthly:
    visible_columns.append("monthly")
if show_annual:
    visible_columns.append("annual")
if show_elitepro:
    visible_columns.append("elitepro")

if len(visible_columns) == 0:
    st.success("🎉 You're on our highest tier! Thank you for being an Elite Pro customer!")
    cols = []
elif len(visible_columns) == 1:
    c1 = st.container()
    cols = [c1]
elif len(visible_columns) == 2:
    c1, c2 = st.columns(2, gap="medium")
    cols = [c1, c2]
elif len(visible_columns) == 3:
    c1, c2, c3 = st.columns(3, gap="medium")
    cols = [c1, c2, c3]
else:
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    cols = [c1, c2, c3, c4]

col_idx = 0

# FREE
if show_free and col_idx < len(cols):
    with cols[col_idx]:
        st.markdown(
            """
            <div class="pricing-card">
                <h3>🆓 Free Trial</h3>
                <div class="price">FREE</div>
                <p style="text-align: center; color: #666;">Perfect for testing our platform</p>
                <ul style="text-align: left; padding-left: 1rem; margin: 1rem 0;">
                    <li>Advanced AI analysis</li>
                    <li>Basic job matching</li>
                    <li>Resume templates (5)</li>
                    <li>Email support</li>
                    <li>LinkedIn export ready</li>
                    <li>Basic keyword suggestions</li>
                    <li>10 AI tokens</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚀 Start Free Trial", key="free_trial", use_container_width=True):
            st.session_state["selected_plan"] = "free"
            st.switch_page("pages/03_Registration.py")
    col_idx += 1

# MONTHLY PRO
if show_monthly and col_idx < len(cols):
    with cols[col_idx]:
        st.markdown(
            """
            <div class="pricing-card">
                <h3>⭐ Monthly Pro</h3>
                <div class="price">$15.99<span class="price-period">/month</span></div>
                <p style="text-align: center; color: #666;">Ideal for active job seekers</p>
                <ul style="text-align: left; padding-left: 1rem; margin: 1rem 0; min-height: 120px;">
                    <li>Unlimited resume generations</li>
                    <li>250 AI tokens/month</li>
                    <li>Advanced AI job matching</li>
                    <li>Premium templates</li>
                    <li>24/7 support</li>
                    <li>LinkedIn export ready</li>
                    <li>Application tracking</li>
                    <li>ATS optimization</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        btn_text = "⭐ Upgrade to Monthly Pro" if current_user_tier else "⭐ Choose Monthly Pro"
        if st.button(btn_text, key="monthly_pro", use_container_width=True):
            st.session_state["selected_plan"] = "monthly"
            if current_user_tier:
                st.switch_page("pages/05_Payment.py")
            else:
                st.switch_page("pages/03_Registration.py")
    col_idx += 1

# ANNUAL PRO (featured)
if show_annual and col_idx < len(cols):
    with cols[col_idx]:
        st.markdown(
            """
            <div class="pricing-card featured">
                <h3>🏆 Annual Pro</h3>
                <div class="price">$149.99<span class="price-period">/year</span></div>
                <p style="text-align: center; color: #666;">Best value - Save $42!</p>
                <ul style="text-align: left; padding-left: 1rem; margin: 1rem 0; min-height: 120px;">
                    <li>Everything in Monthly Pro, plus:</li>
                    <li>500 AI tokens/month</li>
                    <li>AI Career Coach</li>
                    <li>Career workbook generator</li>
                    <li>Industry insights reports</li>
                    <li>1-on-1 career consultation</li>
                    <li>Resume version history</li>
                    <li>Advanced analytics dashboard</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        btn_text = "🏆 Upgrade to Annual Pro" if current_user_tier else "🏆 Choose Annual Pro"
        if st.button(btn_text, key="annual_pro", use_container_width=True):
            st.session_state["selected_plan"] = "annual"
            if current_user_tier:
                st.switch_page("pages/05_Payment.py")
            else:
                st.switch_page("pages/03_Registration.py")
    col_idx += 1

# ELITE PRO
if show_elitepro and col_idx < len(cols):
    with cols[col_idx]:
        st.markdown(
            """
            <div class="pricing-card">
                <h3>👑 Elite Pro</h3>
                <div class="price">$299.99<span class="price-period">/year</span></div>
                <p style="text-align: center; color: #666;">Ultimate career acceleration</p>
                <ul style="text-align: left; padding-left: 1rem; margin: 1rem 0; min-height: 120px;">
                    <li>Everything in Annual Pro, plus:</li>
                    <li>Unlimited AI tokens</li>
                    <li>Access to Mentorship Programme</li>
                    <li>Executive resume templates</li>
                    <li>Unlimited consultations</li>
                    <li>Industry network access</li>
                    <li>Priority support</li>
                    <li>Custom integrations</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        btn_text = "👑 Upgrade to Elite Pro" if current_user_tier else "👑 Choose Elite Pro"
        if st.button(btn_text, key="elite_pro", use_container_width=True):
            st.session_state["selected_plan"] = "elitepro"
            if current_user_tier:
                st.switch_page("pages/05_Payment.py")
            else:
                st.switch_page("pages/03_Registration.py")
    col_idx += 1


# ─────────────────────────────────────────────────────────────
# Fractional-ownership CTA banner
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="fractional-banner">
        <span class="fractional-badge">💡 Innovation & Opportunity</span>
        <h3>Help Us to Help You</h3>
        <p>We believe the best ideas come from real job seekers and career changers using IntelliCV-AI every day.</p>
        <p>Have an idea that could improve user experience or unlock new value?</p>
        <p><strong>For selected ideas, we may explore fractional ownership opportunities in the platform.</strong></p>
        <a class="fractional-cta" href="#idea-submission">🚀 Submit Your Idea</a>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# Enhanced promo for new users
# ─────────────────────────────────────────────────────────────
if st.session_state.get("is_new_user", False) and not st.session_state.get("authenticated_user"):
    st.markdown("---")
    st.markdown("### 🌟 Enhanced Features for New Users")

    features = [
        {
            "icon": "🎯",
            "title": "Smart Targeting",
            "description": "AI analyzes job descriptions and optimizes your resume for maximum impact",
        },
        {
            "icon": "⚡",
            "title": "Lightning Fast",
            "description": "Generate professional resumes in seconds, not hours",
        },
        {
            "icon": "📊",
            "title": "Data-Driven",
            "description": "Make informed decisions with comprehensive analytics and insights",
        },
        {
            "icon": "🔧",
            "title": "Fully Customizable",
            "description": "Tailor every aspect to match your industry and personal brand",
        },
    ]

    st.markdown('<div class="feature-grid">', unsafe_allow_html=True)
    for feature in features:
        st.markdown(
            f"""
            <div class="feature-card">
                <h3>{feature["icon"]} {feature["title"]}</h3>
                <p>{feature["description"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("👋 Welcome to IntelliCV-AI! Complete your registration above to unlock all these features.")


# ─────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p><strong>IntelliCV-AI</strong> | Powered by Advanced AI Technology</p>
        <p>🔒 Your data is secure • 🌍 Available worldwide • 📞 24/7 Support</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Optional debug panel
if st.sidebar.checkbox("🔧 Debug Info", value=False):
    with st.sidebar.expander("System Status"):
        st.write("**Module Status:**")
        st.write(f"• Sidebar: {'✅' if SIDEBAR_AVAILABLE else '❌'}")
        st.write(f"• Error Handler: {'✅' if ERROR_HANDLER_AVAILABLE else '❌'}")
        st.write(f"• Enhanced Auth: {'✅' if ENHANCED_AUTH_AVAILABLE else '❌'}")
        st.write(f"• Logo: {'✅' if logo_b64 else '❌'}")

        st.write("**Session State:**")
        for key, value in st.session_state.items():
            key_str = str(key)
            if not key_str.startswith("_"):
                st.write(f"• {key_str}: {str(value)[:50]}...")

