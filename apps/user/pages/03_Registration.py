"""
🆕 IntelliCV-AI Registration Page
================================
Step 1: Account Creation + Plan Selection

Plans (keys + prices):
- free      → Free Trial ($0)
- monthly   → Monthly Pro ($15.99 / month)
- annual    → Annual Pro ($149.99 / year)
- elitepro  → Elite Pro ($299.99 / year)

Notes:
- No demo or mock users are created here.
- This page only collects details + plan and stores them in session_state.
- Actual account creation / payment is handled by downstream pages.
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
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="🆕 IntelliCV-AI | Registration",
    page_icon="🆕",
    layout="wide",
    initial_sidebar_state="expanded",
)

if SIDEBAR_AVAILABLE:
    try:
        show_sidebar()
    except Exception:
        # Sidebar is nice-to-have; don't break page if it fails
        pass


# ──────────────────────────────────────────────
# Routes (easy to change later if files are renumbered)
# ──────────────────────────────────────────────
PAGE_ROUTES = {
    "payment": "pages/05_Payment.py",   # Step 2 – Payment
    "login": "pages/02_Login.py",       # Existing users
    "home": "pages/01_Home.py",         # Landing / home
}


def go_to(route_key: str):
    """Wrapper around st.switch_page using PAGE_ROUTES."""
    target = PAGE_ROUTES.get(route_key)
    if not target:
        st.warning(f"Route '{route_key}' is not configured.")
        return
    try:
        st.switch_page(target)
    except Exception:
        show_error(f"Unable to open {route_key}. Please check PAGE_ROUTES mapping.")


# ──────────────────────────────────────────────
# CSS – Figma-style layout (matches Login / Payment)
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
    .registration-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 22px rgba(0,0,0,0.2);
    }
    .registration-header h1 {
        margin: 0 0 0.3rem 0;
        font-size: 1.8rem;
    }
    .registration-header p {
        margin: 0;
        font-size: 0.95rem;
        opacity: 0.95;
    }
    .steps {
        display: flex;
        gap: 0.75rem;
        margin-top: 0.75rem;
        font-size: 0.85rem;
    }
    .step-pill {
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
    }
    .step-pill.active {
        background: #ffffff;
        color: #4b2ea8;
    }
    .registration-card {
        background: white;
        padding: 1.75rem;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .pricing-card {
        background: white;
        padding: 1.3rem;
        border-radius: 12px;
        text-align: left;
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        border: 2px solid #e0e0e0;
        transition: all 0.25s ease;
        position: relative;
        min-height: 220px;
    }
    .pricing-card.selected {
        border-color: #667eea;
        box-shadow: 0 8px 22px rgba(0,0,0,0.18);
    }
    .pricing-card.featured::before {
        content: "MOST POPULAR";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        background: linear-gradient(135deg,#667eea 0%,#00bcd4 100%);
        color: white;
        padding: 0.4rem;
        font-size: 0.75rem;
        text-align: center;
        font-weight: 600;
    }
    .pricing-title {
        font-weight: 600;
        margin-top: 0.6rem;
    }
    .pricing-price {
        font-size: 1.6rem;
        font-weight: 700;
        color: #667eea;
    }
    .pricing-billing {
        font-size: 0.85rem;
        color: #666;
    }
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
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
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


load_css()

# Log page access (no mock values – just event logging)
if ERROR_HANDLER_AVAILABLE:
    log_user_action(
        "page_view",
        {"page": "registration", "timestamp": datetime.now().isoformat()},
    )


# ──────────────────────────────────────────────
# Plan configuration – NEW pricing, elitepro only
# ──────────────────────────────────────────────
PLANS = {
    "free": {
        "name": "Free Trial",
        "price": 0.00,
        "billing": "No card required",
        "tagline": "Test IntelliCV-AI with core features.",
    },
    "monthly": {
        "name": "Monthly Pro",
        "price": 15.99,
        "billing": "Billed monthly",
        "tagline": "Ideal for active job seekers.",
    },
    "annual": {
        "name": "Annual Pro",
        "price": 149.99,
        "billing": "Billed annually",
        "tagline": "Best value – save vs monthly.",
    },
    "elitepro": {
        "name": "Elite Pro",
        "price": 299.99,
        "billing": "Billed annually",
        "tagline": "Ultimate, full-featured access.",
    },
}


def format_plan_option(key: str) -> str:
    plan = PLANS[key]
    if plan["price"] == 0:
        return f"{plan['name']} – ${plan['price']:.2f} ({plan['billing']})"
    period = "/month" if key == "monthly" else "/year"
    return f"{plan['name']} – ${plan['price']:.2f}{period}"


# ──────────────────────────────────────────────
# Header + steps
# ──────────────────────────────────────────────
st.markdown(
    """
<div class="registration-header">
  <h1>🆕 Create Your IntelliCV-AI Account</h1>
  <p>Step 1 of 3 · Account details & plan selection</p>
  <div class="steps">
    <span class="step-pill active">1. Account & Plan</span>
    <span class="step-pill">2. Payment</span>
    <span class="step-pill">3. Verify & Profile</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Optional: Back to home / login in sidebar
with st.sidebar:
    if st.button("🏠 Back to Home", use_container_width=True):
        go_to("home")
    if st.button("🔑 Already registered? Login", use_container_width=True):
        go_to("login")


form_col, plan_col = st.columns([1.3, 1.2], gap="large")

preselected_plan = st.session_state.get("selected_plan", "free")
if preselected_plan not in PLANS:
    preselected_plan = "free"


# ──────────────────────────────────────────────
# LEFT: Account details
# ──────────────────────────────────────────────
with form_col:
    st.markdown('<div class="registration-card">', unsafe_allow_html=True)
    st.markdown("### 👤 Account Details")

    with st.form("registration_form", clear_on_submit=False):
        full_name = st.text_input("Full Name", placeholder="Your full name")
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email", placeholder="your.email@domain.com")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        st.markdown("#### 🔐 Security & Consent")
        accept_terms = st.checkbox(
            "I agree to the Terms of Use and Privacy Policy.",
            value=False,
        )

        submitted = st.form_submit_button("Continue to Payment →")

    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# RIGHT: Plan selection
# ──────────────────────────────────────────────
with plan_col:
    st.markdown('<div class="registration-card">', unsafe_allow_html=True)
    st.markdown("### 💰 Choose Your Plan")

    # Radio selects the active plan; cards are visual only
    selected_plan_key = st.radio(
        "Plan",
        options=list(PLANS.keys()),
        index=list(PLANS.keys()).index(preselected_plan),
        format_func=format_plan_option,
        label_visibility="collapsed",
    )

    c1, c2 = st.columns(2)

    with c1:
        for key in ["free", "monthly"]:
            plan = PLANS[key]
            selected_class = "selected" if key == selected_plan_key else ""
            period = "" if key == "free" else "/month"
            price_text = "FREE" if plan["price"] == 0 else f"${plan['price']:.2f}{period}"

            st.markdown(
                f"""
                <div class="pricing-card {selected_class}">
                  <div class="pricing-title">{plan['name']}</div>
                  <div class="pricing-price">
                    {price_text}
                  </div>
                  <div class="pricing-billing">{plan['billing']}</div>
                  <p style="font-size:0.85rem; margin-top:0.4rem;">{plan['tagline']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with c2:
        for key in ["annual", "elitepro"]:
            plan = PLANS[key]
            featured = "featured" if key == "annual" else ""
            selected_class = "selected" if key == selected_plan_key else ""
            period = "/year"
            price_text = f"${plan['price']:.2f}{period}"

            st.markdown(
                f"""
                <div class="pricing-card {featured} {selected_class}">
                  <div class="pricing-title">{plan['name']}</div>
                  <div class="pricing-price">{price_text}</div>
                  <div class="pricing-billing">{plan['billing']}</div>
                  <p style="font-size:0.85rem; margin-top:0.4rem;">{plan['tagline']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Session defaults (no mock accounts – just placeholders)
# ──────────────────────────────────────────────
if "registration_data" not in st.session_state:
    st.session_state["registration_data"] = {}

if "plan_price" not in st.session_state:
    st.session_state["plan_price"] = PLANS[preselected_plan]["price"]


# ──────────────────────────────────────────────
# Handle submission
# ──────────────────────────────────────────────
if submitted:
    if not (full_name and username and email and password and confirm):
        show_error("Please fill in all required fields.")
    elif password != confirm:
        show_error("Passwords do not match.")
    elif not accept_terms:
        show_error("You must accept the Terms of Use and Privacy Policy.")
    else:
        plan = PLANS[selected_plan_key]

        # Store data only in session – no file writes, no mock accounts
        st.session_state["registration_data"] = {
            "full_name": full_name,
            "username": username,
            "email": email,
            "password": password,  # NOTE: hash in production / FastAPI backend
            "created_at": datetime.utcnow().isoformat(),
            "selected_plan": selected_plan_key,
            "plan_price": float(plan["price"]),
        }
        st.session_state["plan_price"] = float(plan["price"])
        st.session_state["selected_plan"] = selected_plan_key

        if ERROR_HANDLER_AVAILABLE:
            log_user_action(
                "registration_submitted",
                {
                    "username": username,
                    "plan": selected_plan_key,
                    "price": float(plan["price"]),
                },
            )

        show_success("Account details saved. Proceeding to secure payment...")
        time.sleep(0.7)
        go_to("payment")


# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 1rem;">
  <p><strong>IntelliCV-AI</strong> | Secure Registration Process</p>
  <p>🔒 Your data is encrypted • 💳 Payment handled securely • 📞 Support available</p>
</div>
""",
    unsafe_allow_html=True,
)
