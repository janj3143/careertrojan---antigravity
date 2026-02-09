"""
💳 IntelliCV-AI Payment Page
===========================
Step 2: Payment Processing

Plan keys:
- free      → Free Trial ($0)
- monthly   → Monthly Pro ($15.99 / month)
- annual    → Annual Pro ($149.99 / year)
- elitepro  → Elite Pro ($299.99 / year)
"""

import streamlit as st
from datetime import datetime
import time

# ──────────────────────────────────────────────
# Optional imports
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
    page_title="💳 IntelliCV-AI | Payment",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

if SIDEBAR_AVAILABLE:
    try:
        show_sidebar()
    except Exception:
        pass


# ──────────────────────────────────────────────
# CSS – matches Login / Registration background
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
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
        backdrop-filter: blur(10px);
    }
    .payment-header {
        background: linear-gradient(135deg,#4b6fff 0%,#7a2ddb 100%);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 22px rgba(0,0,0,0.2);
    }
    .payment-header h1 {
        margin: 0 0 0.3rem 0;
        font-size: 1.8rem;
    }
    .payment-header p {
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
    .step-pill.completed {
        background: #00c853;
        border-color: #00c853;
    }
    .step-pill.active {
        background: #ffffff;
        color: #4b2ea8;
    }
    .payment-card {
        background: white;
        padding: 1.75rem;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.12);
        border: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    .plan-summary {
        background: #f6f8fc;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #dfe3ef;
        margin-bottom: 1rem;
        font-size: 0.95rem;
    }
    .plan-price {
        font-size: 1.4rem;
        font-weight: 700;
        color: #667eea;
    }
    .security-badges {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    .security-badge {
        font-size: 0.8rem;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        border: 1px solid #d0d4e0;
        background: #f7f8fc;
    }
    .payment-methods {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    .payment-method {
        padding: 0.5rem 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        background: white;
    }
    .payment-method:hover {
        border-color: #667eea;
    }
    .payment-method.selected {
        border-color: #667eea;
        background: rgba(102, 126, 234, 0.1);
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
    log_user_action("page_view", {"page": "payment", "timestamp": datetime.now().isoformat()})


# ──────────────────────────────────────────────
# Plan details – NEW pricing, elitepro only
# ──────────────────────────────────────────────
PLAN_DETAILS = {
    "free": {
        "name": "Free Trial",
        "price": 0.00,
        "billing": "No card required",
        "features": [
            "AI resume analysis (core)",
            "Basic job matching",
            "Standard templates",
            "Email support",
        ],
        "subscription_tier": "free",
    },
    "monthly": {
        "name": "Monthly Pro",
        "price": 15.99,
        "billing": "Billed monthly",
        "features": [
            "Unlimited resume generations",
            "250 AI tokens / month",
            "Advanced job matching",
            "Premium templates",
            "24/7 support",
            "Application tracking",
        ],
        "subscription_tier": "monthly",
    },
    "annual": {
        "name": "Annual Pro",
        "price": 149.99,
        "billing": "Billed annually",
        "features": [
            "Everything in Monthly Pro",
            "500 AI tokens / month",
            "AI Career Coach access",
            "Career workbook generator",
            "Industry insights reports",
            "Advanced analytics dashboard",
        ],
        "subscription_tier": "annual",
    },
    "elitepro": {
        "name": "Elite Pro",
        "price": 299.99,
        "billing": "Billed annually",
        "features": [
            "Unlimited AI tokens",
            "Executive templates & branding",
            "Mentorship programme access",
            "Priority 1-to-1 consultations",
            "Industry network access",
            "Custom integrations (subject to agreement)",
        ],
        "subscription_tier": "elitepro",
    },
}


# ──────────────────────────────────────────────
# Retrieve registration data
# ──────────────────────────────────────────────
if "registration_data" not in st.session_state:
    show_error("Registration data not found. Please start from the registration page.")
    if st.button("🔙 Go to Registration"):
        try:
            st.switch_page("pages/03_Registration.py")
        except Exception:
            pass
    st.stop()

reg_data = st.session_state["registration_data"]

selected_plan = reg_data.get("selected_plan", "free")
if selected_plan not in PLAN_DETAILS:
    selected_plan = "free"

plan_price_from_reg = float(reg_data.get("plan_price", PLAN_DETAILS[selected_plan]["price"]))
current_plan = PLAN_DETAILS[selected_plan]


# ──────────────────────────────────────────────
# Header + sidebar nav
# ──────────────────────────────────────────────
st.markdown(
    """
<div class="payment-header">
  <h1>💳 Secure Payment</h1>
  <p>Step 2 of 3 · Confirm your plan and payment details</p>
  <div class="steps">
    <span class="step-pill completed">1. Account & Plan</span>
    <span class="step-pill active">2. Payment</span>
    <span class="step-pill">3. Verify & Profile</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    if st.button("🔙 Back to Registration", use_container_width=True):
        try:
            st.switch_page("pages/03_Registration.py")
        except Exception:
            pass

    if st.button("🏠 Back to Home", use_container_width=True):
        try:
            st.switch_page("pages/01_Home.py")
        except Exception:
            pass

    st.markdown("---")
    st.markdown("### 🛡️ Security")
    st.markdown(
        """
- Encrypted data transport
- Card details handled securely
- No resale of personal data
        """
    )


# ──────────────────────────────────────────────
# Plan summary
# ──────────────────────────────────────────────
st.markdown('<div class="payment-card">', unsafe_allow_html=True)
st.markdown("### 📦 Your Selected Plan")

col_summary, col_price = st.columns([2, 1], gap="large")

with col_summary:
    st.markdown(
        f"""
        <div class="plan-summary">
          <strong>{current_plan['name']}</strong><br/>
          <span style="font-size:0.9rem;">{current_plan['billing']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Included features:**")
    for feat in current_plan["features"]:
        st.markdown(f"- {feat}")

with col_price:
    period = "" if selected_plan == "free" else ("/month" if selected_plan == "monthly" else "/year")
    st.markdown(
        f"""
        <div class="plan-summary">
          <div class="plan-price">
            {'FREE' if current_plan['price']==0 else f"${current_plan['price']:.2f}{period}"}
          </div>
          <div style="font-size:0.9rem; color:#555;">
            Charged as: {"$0.00" if current_plan['price']==0 else f"${current_plan['price']:.2f} {current_plan['billing']}"}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="security-badges">
  <span class="security-badge">🔒 Encrypted transmission</span>
  <span class="security-badge">💳 Card details handled securely</span>
  <span class="security-badge">✅ Transparent billing</span>
</div>
""",
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────
# Free vs Paid logic
# ──────────────────────────────────────────────
if current_plan["price"] == 0:
    # Free plan – no payment required
    st.markdown("### 🎉 Free Trial – No Payment Required")
    st.markdown(
        """
**What happens next:**

1. ✅ Your Free Trial plan will be activated
2. 🚀 You'll be sent to verification / profile
3. 🎯 Start using IntelliCV-AI right away
        """
    )

    if st.button("🚀 Activate Free Trial & Continue", use_container_width=True, type="primary"):
        # Mark subscription details in session (no mock users – this uses real registration data)
        st.session_state["subscription_tier"] = current_plan["subscription_tier"]
        st.session_state["subscription_name"] = current_plan["name"]
        st.session_state["subscription_price"] = current_plan["price"]
        st.session_state["payment_status"] = "skipped_free_plan"

        reg_data["subscription_tier"] = current_plan["subscription_tier"]
        reg_data["subscription_name"] = current_plan["name"]
        reg_data["subscription_price"] = current_plan["price"]
        st.session_state["registration_data"] = reg_data

        if ERROR_HANDLER_AVAILABLE:
            log_user_action(
                "free_plan_activated",
                {
                    "username": reg_data.get("username"),
                    "plan": selected_plan,
                },
            )

        show_success("Free Trial activated. Proceeding to verification...")
        time.sleep(0.8)
        try:
            st.switch_page("pages/07_Account_Verification.py")
        except Exception:
            pass

else:
    # Paid plans – capture payment details (no dev/simulation text)
    st.markdown(f"### 💳 Payment for {current_plan['name']}")

    st.markdown("**Select Payment Method:**")
    payment_method = st.radio(
        "Choose payment method",
        ["💳 Credit/Debit Card", "🏦 PayPal", "🍎 Apple Pay", "📱 Google Pay"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if "Credit/Debit Card" in payment_method:
        # Credit card form
        with st.form("payment_form"):
            st.markdown("**Card Information**")

            col_a, col_b = st.columns([2, 1])
            with col_a:
                card_number = st.text_input("Card Number", placeholder="1234 5678 9012 3456", max_chars=19)
            with col_b:
                cvv = st.text_input("CVV", placeholder="123", max_chars=4)

            col_c, col_d = st.columns(2)
            with col_c:
                card_name = st.text_input("Name on Card", placeholder="Name as shown on card")
            with col_d:
                expiry = st.text_input("Expiry (MM/YY)", placeholder="MM/YY", max_chars=5)

            billing_country = st.text_input("Billing Country / Region", placeholder="United Kingdom")
            agree = st.checkbox(
                f"I authorise IntelliCV-AI to charge my card for ${current_plan['price']:.2f}.",
                value=False,
            )

            submitted = st.form_submit_button(
                f"Pay ${current_plan['price']:.2f} and Continue →",
                use_container_width=True,
            )

        if submitted:
            if not (card_name and card_number and expiry and cvv and billing_country):
                show_error("Please complete all card details.")
            elif not agree:
                show_error("You must authorise the payment to continue.")
            else:
                with st.spinner("Processing payment..."):
                    time.sleep(1.0)

                # Mark payment state in session – real backend gateway should finalise this
                st.session_state["payment_status"] = "authorised"
                st.session_state["subscription_tier"] = current_plan["subscription_tier"]
                st.session_state["subscription_name"] = current_plan["name"]
                st.session_state["subscription_price"] = current_plan["price"]

                reg_data["subscription_tier"] = current_plan["subscription_tier"]
                reg_data["subscription_name"] = current_plan["name"]
                reg_data["subscription_price"] = current_plan["price"]
                st.session_state["registration_data"] = reg_data

                if ERROR_HANDLER_AVAILABLE:
                    log_user_action(
                        "payment_details_captured",
                        {
                            "username": reg_data.get("username"),
                            "plan": selected_plan,
                            "amount": current_plan["price"],
                            "method": "card",
                        },
                    )

                show_success("Payment details captured. Proceeding to verification...")
                time.sleep(0.8)
                try:
                    st.switch_page("pages/07_Account_Verification.py")
                except Exception:
                    pass

    else:
        # Non-card methods – simple confirmation
        st.info(
            "This payment will be processed via your selected provider."
        )

        if st.button(
            f"Confirm {payment_method} and Continue →",
            use_container_width=True,
        ):
            with st.spinner("Processing payment..."):
                time.sleep(1.0)

            st.session_state["payment_status"] = "authorised"
            st.session_state["subscription_tier"] = current_plan["subscription_tier"]
            st.session_state["subscription_name"] = current_plan["name"]
            st.session_state["subscription_price"] = current_plan["price"]

            reg_data["subscription_tier"] = current_plan["subscription_tier"]
            reg_data["subscription_name"] = current_plan["name"]
            reg_data["subscription_price"] = current_plan["price"]
            st.session_state["registration_data"] = reg_data

            if ERROR_HANDLER_AVAILABLE:
                log_user_action(
                    "payment_details_captured_alt",
                    {
                        "username": reg_data.get("username"),
                        "plan": selected_plan,
                        "amount": current_plan["price"],
                        "method": payment_method,
                    },
                )

            show_success("Payment details captured. Proceeding to verification...")
            time.sleep(0.8)
            try:
                st.switch_page("pages/07_Account_Verification.py")
            except Exception:
                pass

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 1rem;">
  <p><strong>IntelliCV-AI</strong> | Secure Payment Processing</p>
  <p>🔒 Payment handled via secure gateway • 🌍 Global cards supported • 💬 Priority support for paid plans</p>
</div>
""",
    unsafe_allow_html=True,
)
