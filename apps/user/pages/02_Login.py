"""
🔑 IntelliCV-AI Login Page
==========================

Secure login page aligned with Figma styling and the new Home/Dashboard:

- No demo/mock users or fake metrics.
- Reads real accounts from user_accounts.json (if available).
- Admin override: username=admin, password=admin123.
- On success: sets session_state and redirects to Dashboard.
"""

import streamlit as st
from pathlib import Path
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

# ──────────────────────────────────────────────
# Basic setup
# ──────────────────────────────────────────────
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Shared session helper (new integration)
try:
    from session import set_user_session  # centralised session model
    SHARED_SESSION_AVAILABLE = True
except ImportError:
    SHARED_SESSION_AVAILABLE = False

# Error handler (optional)
try:
    from utils.error_handler import (
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


# ──────────────────────────────────────────────
# Config & constants
# ──────────────────────────────────────────────
PAGE_ROUTES: Dict[str, str] = {
    "home": "pages/00_Home.py",
    "dashboard": "pages/04_Dashboard.py",
    "registration": "pages/03_Registration.py",  # adjust if your filename differs
}

USER_ACCOUNTS_FILE = current_dir / "user_accounts.json"

# Token limits by subscription tier – configuration, not “demo data”
TIER_TOKENS: Dict[str, Dict[str, int]] = {
    "free": {"limit": 10},
    "monthly": {"limit": 250},
    "annual": {"limit": 500},
    "elitepro": {"limit": -1},      # unlimited
    "enterprise": {"limit": -1},    # alias for elite-style
}


# ──────────────────────────────────────────────
# Styling (aligned with Home / Dashboard)
# ──────────────────────────────────────────────
def load_css() -> None:
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
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        backdrop-filter: blur(10px);
    }

    .login-hero {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 22px 26px;
        border-radius: 16px;
        margin-bottom: 24px;
        color: #ffffff;
    }

    .login-hero h1 {
        margin: 0 0 6px 0;
        font-size: 1.9rem;
    }

    .login-hero p {
        margin: 0;
        font-size: 1rem;
        opacity: 0.95;
    }

    .login-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 14px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        border: 1px solid #e5e7eb;
    }

    .login-side {
        padding-left: 1rem;
    }

    .login-side h3 {
        margin-top: 0;
        font-size: 1.1rem;
    }

    .login-side p {
        font-size: 0.9rem;
        color: #4b5563;
    }

    .login-side li {
        font-size: 0.9rem;
        color: #4b5563;
        margin-bottom: 0.35rem;
    }

    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102,126,234,0.25);
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 999px;
        padding: 0.7rem 1.6rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.22);
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    @media (max-width: 768px) {
        .login-card {
            padding: 1.5rem;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def go_to(route_key: str) -> None:
    """Navigate using st.switch_page based on PAGE_ROUTES."""
    target = PAGE_ROUTES.get(route_key)
    if not target:
        st.warning(f"Route '{route_key}' is not configured.")
        return
    try:
        st.switch_page(target)
    except Exception:
        # Fallback: just show message; do not fabricate anything
        show_error(f"Unable to open {route_key}. Please check PAGE_ROUTES.")


def load_accounts() -> List[Dict[str, Any]]:
    """Load user accounts from JSON; returns empty list if not present/invalid."""
    if not USER_ACCOUNTS_FILE.exists():
        return []
    try:
        with USER_ACCOUNTS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        if ERROR_HANDLER_AVAILABLE:
            log_user_action("accounts_load_error", {"error": str(e)})
        return []


def find_account(identifier: str, accounts: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Find account by username or email (case-insensitive)."""
    ident_lower = identifier.strip().lower()
    for acc in accounts:
        username = str(acc.get("username", "")).lower()
        email = str(acc.get("email", "")).lower()
        if ident_lower == username or ident_lower == email:
            return acc
    return None


def set_session_for_user(account: Dict[str, Any]) -> None:
    """Populate session_state for a successfully authenticated user."""
    username = account.get("username") or account.get("email") or "user"
    user_id = account.get("user_id") or username
    email = account.get("email", "")
    role = account.get("role", "user")

    # NEW: populate shared session model (for admin/mentor portals etc.)
    if SHARED_SESSION_AVAILABLE:
        set_user_session(
            user_id=str(user_id),
            email=email,
            role=str(role),
            name=username,
        )

    # Existing keys used throughout the current app
    st.session_state["authenticated_user"] = username
    st.session_state["user_role"] = role
    st.session_state["user_id"] = user_id
    st.session_state["user_email"] = email

    # Subscription tier/name/price from account (no mock values)
    tier = (account.get("subscription_tier") or "free").lower()
    name = account.get("subscription_name", "Free Plan")
    price = account.get("subscription_price", 0)

    st.session_state["subscription_tier"] = tier
    st.session_state["subscription_name"] = name
    st.session_state["subscription_price"] = price

    # Tokens: use stored usage if present; limit from config
    used = account.get("tokens_used", 0)
    tier_cfg = TIER_TOKENS.get(tier, TIER_TOKENS["free"])
    limit = tier_cfg["limit"]

    st.session_state["tokens_used"] = used
    st.session_state["tokens_monthly_limit"] = limit
    st.session_state["session_token"] = f"token_{int(time.time())}"
    st.session_state["is_new_user"] = False


def set_session_for_admin() -> None:
    """Admin override login (no backing JSON record)."""
    username = "admin"
    user_id = "admin"
    email = ""
    role = "admin"

    # NEW: shared session model for admin
    if SHARED_SESSION_AVAILABLE:
        set_user_session(
            user_id=user_id,
            email=email,
            role=role,
            name=username,
        )

    # Existing keys relied upon by current code
    st.session_state["authenticated_user"] = username
    st.session_state["user_role"] = role
    st.session_state["user_id"] = user_id
    st.session_state["user_email"] = email
    st.session_state["subscription_tier"] = "elitepro"
    st.session_state["subscription_name"] = "Admin (ElitePro)"
    st.session_state["subscription_price"] = 0
    st.session_state["tokens_used"] = 0
    st.session_state["tokens_monthly_limit"] = -1
    st.session_state["session_token"] = f"token_{int(time.time())}"
    st.session_state["is_new_user"] = False


# ──────────────────────────────────────────────
# Main page
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="🔑 Login | IntelliCV-AI",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()

# Log page view
if ERROR_HANDLER_AVAILABLE:
    log_user_action("page_view", {"page": "login", "timestamp": datetime.now().isoformat()})

# Hero header
st.markdown(
    """
    <div class="login-hero">
        <h1>🔑 Login to IntelliCV-AI</h1>
        <p>Secure access to your personalised career intelligence dashboard.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_form, col_side = st.columns([1.3, 1], gap="large")

# ──────────────────────────────────────────────
# Login form
# ──────────────────────────────────────────────
with col_form:
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("### 👤 Account Login")

    with st.form("login_form"):
        identifier = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        col_l_btn, col_l_extra = st.columns([1, 1])
        with col_l_btn:
            submit = st.form_submit_button("🔑 Login", use_container_width=True)
        with col_l_extra:
            st.write("")  # spacing
            st.caption("Forgotten password? Password reset will be handled by support.")

        if submit:
            if not identifier or not password:
                show_error("Please enter both your username/email and password.")
            else:
                # Admin override
                if identifier == "admin" and password == "admin123":
                    set_session_for_admin()
                    show_success("Admin login successful. Redirecting...")
                    if ERROR_HANDLER_AVAILABLE:
                        log_user_action("admin_login", {"username": "admin"})
                    time.sleep(1)
                    go_to("dashboard")
                    st.stop()

                accounts = load_accounts()
                if not accounts:
                    show_error(
                        "No registered accounts found. Please register first "
                        "or contact support if you believe this is an error."
                    )
                else:
                    account = find_account(identifier, accounts)
                    if not account:
                        show_error("No account found for that username or email.")
                    else:
                        stored_password = account.get("password")
                        if stored_password is None:
                            show_error(
                                "This account does not have a password set. "
                                "Please contact support or re-register."
                            )
                        elif stored_password != password:
                            show_error("Incorrect password. Please try again.")
                        else:
                            # Successful login
                            set_session_for_user(account)
                            show_success("Login successful. Redirecting to your dashboard...")
                            if ERROR_HANDLER_AVAILABLE:
                                log_user_action(
                                    "user_login",
                                    {
                                        "username": account.get("username"),
                                        "user_id": account.get("user_id"),
                                        "tier": account.get("subscription_tier"),
                                    },
                                )
                            time.sleep(1)
                            go_to("dashboard")
                            st.stop()

    st.markdown("</div>", unsafe_allow_html=True)

    # Link to registration
    st.markdown("#### 🆕 New to IntelliCV-AI?")
    reg_col1, reg_col2 = st.columns([1, 2])
    with reg_col1:
        if st.button("🆕 Create Account", use_container_width=True):
            go_to("registration")
    with reg_col2:
        st.write(
            "Create a free account or choose a subscription to unlock IntelliCV-AI’s full capabilities."
        )

# ──────────────────────────────────────────────
# Right-hand info column
# ──────────────────────────────────────────────
with col_side:
    st.markdown('<div class="login-side">', unsafe_allow_html=True)
    st.markdown("### 🌟 What you’ll access")
    st.markdown(
        """
        - Your personalised **UMarketU & skills position** dashboard
        - **Resume Intelligence** and tailored job-matching
        - AI-supported **interview preparation** tools
        - A growing suite of **advanced career analytics**
        """
    )

    st.markdown("### 🔒 Security & privacy")
    st.markdown(
        """
        - Your data is stored securely and used only to enhance your experience.
        - You stay in control of what is shared and exported.
        - We do not create or use demo accounts on your behalf.
        """
    )

    st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 0.5rem 0 1rem 0;">
        <p><strong>IntelliCV-AI</strong> | Secure Login</p>
        <p>🔒 Privacy-first • 🌍 Available worldwide • 📞 Support on request</p>
    </div>
    """,
    unsafe_allow_html=True,
)
