"""
🎁 User Rewards - Fractional Ownership Program
==============================================
Earn fractional ownership in IntelliCV-AI by contributing
feature suggestions, improvements, and platform enhancements.

AVAILABLE TO ALL TIERS
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime
import json

# Add parent directory to path for imports
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

st.set_page_config(
    page_title="User Rewards - IntelliCV",
    page_icon="🎁",
    layout="wide"
)

# Check authentication
if not st.session_state.get("authenticated_user"):
    st.warning("🔐 Please login to access User Rewards")
    st.stop()

# Main content
st.title("🎁 User Rewards - Fractional Ownership Program")
st.markdown("### Contribute to IntelliCV-AI and Earn Ownership")

st.success("""
🌟 **Fractional Ownership Opportunity**
At IntelliCV-AI, we believe in rewarding our community members who help us improve the platform.
Submit feature suggestions, report bugs, and contribute improvements.
""")

# How it works
st.markdown("---")
st.markdown("### 📋 How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <h3>1️⃣ Suggest</h3>
        <p>Submit feature ideas, improvements, or bug reports</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <h3>2️⃣ Review</h3>
        <p>Our team evaluates and implements your suggestion</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <h3>3️⃣ Earn</h3>
        <p>Receive ownership credits based on impact</p>
    </div>
    """, unsafe_allow_html=True)

# Reward tiers
st.markdown("---")
st.markdown("### 💎 Reward Tiers")
reward_tiers = {
    "🥉 Minor Improvement": "UI tweak, typo fix, small suggestion",
    "🥈 Moderate Feature": "New feature idea, workflow improvement, integration suggestion",
    "🥇 Major Enhancement": "Major feature, algorithm improvement, strategic partnership idea",
    "💎 Revolutionary Contribution": "Platform transformation, new business model, major technical breakthrough",
}

for tier, examples in reward_tiers.items():
    with st.expander(tier):
        st.markdown(f"**Examples:** {examples}")
        st.caption("Credits are assigned by the backend program rules; this page will not estimate values.")

# Your current rewards
st.markdown("---")
st.markdown("### 🏆 Your Ownership Portfolio")

user_email = st.session_state.get("user_email", "unknown")

submissions_log = Path("ai_data") / "user_rewards_submissions.jsonl"

def _load_user_submissions(email: str):
    rows = []
    if not submissions_log.exists():
        return rows
    try:
        for line in submissions_log.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict) and obj.get("user_email") == email:
                rows.append(obj)
    except Exception:
        return []
    return rows


user_submissions = _load_user_submissions(user_email)
total_contributions = len(user_submissions)
pending_review = sum(1 for s in user_submissions if (s.get("status") in ("pending", "under_review")))

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Ownership", "Unavailable")

with col2:
    st.metric("Total Contributions", total_contributions)

with col3:
    st.metric("Pending Review", pending_review)

with col4:
    st.metric("Estimated Value", "Unavailable")

# Contribution history
st.markdown("### 📊 Your Contribution History")
if not user_submissions:
    st.info("No submissions found yet.")
else:
    for contribution in sorted(user_submissions, key=lambda x: x.get("submitted_at", ""), reverse=True)[:20]:
        with st.container():
            col1, col2, col3 = st.columns([2, 4, 2])
            with col1:
                st.markdown(f"**{contribution.get('submitted_at','')[:10]}**")
            with col2:
                st.markdown(f"**{contribution.get('title','(no title)')}**")
                st.caption(contribution.get("type") or "")
            with col3:
                st.markdown(contribution.get("status_label") or "Pending")
            st.markdown("---")

# Submit new suggestion
st.markdown("### 💡 Submit New Suggestion")

with st.form("suggestion_form"):
    suggestion_type = st.selectbox(
        "Type of Contribution",
        ["Feature Suggestion", "UI/UX Improvement", "Bug Report", "Integration Idea", "Business Model Suggestion", "Other"]
    )

    suggestion_title = st.text_input(
        "Title (Short Description)",
        placeholder="e.g., Add real-time job alerts via email"
    )

    suggestion_details = st.text_area(
        "Detailed Description",
        placeholder="Explain your idea in detail. Include:\n- What problem does it solve?\n- How would it work?\n- What value does it add?\n- Any technical considerations?",
        height=200
    )

    suggestion_impact = st.select_slider(
        "Estimated Impact",
        options=["Minor", "Moderate", "Significant", "Major", "Revolutionary"]
    )

    files = st.file_uploader(
        "Attachments (mockups, screenshots, etc.)",
        accept_multiple_files=True,
        type=["png", "jpg", "pdf", "doc", "docx"]
    )

    submit_button = st.form_submit_button("🚀 Submit Contribution", use_container_width=True, type="primary")

    if submit_button:
        if suggestion_title and suggestion_details:
            payload = {
                "user_email": user_email,
                "type": suggestion_type,
                "title": suggestion_title,
                "details": suggestion_details,
                "impact": suggestion_impact,
                "submitted_at": datetime.now().isoformat(),
                "status": "pending",
                "status_label": "🔄 Pending Review",
            }
            try:
                submissions_log.parent.mkdir(parents=True, exist_ok=True)
                with submissions_log.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except Exception as exc:
                st.error(f"❌ Could not persist your submission: {exc}")
                st.stop()

            st.success("✅ Contribution submitted successfully!")
            st.info("""
            📧 **Next Steps:**
            1. Our team will review your submission within 5 business days
            2. You'll receive an email with the evaluation decision
            3. If implemented, ownership credits will be added to your account
            4. You'll be credited in our changelog and contributor list
            """)
        else:
            st.error("❌ Please fill in both title and detailed description")

# Terms and conditions
st.markdown("---")
st.markdown("### 📜 Program Terms")

with st.expander("View Complete Terms & Conditions"):
    st.markdown("""
    **IntelliCV-AI Fractional Ownership Rewards Program**

    This page does not publish or estimate ownership percentages, valuations, payout thresholds, or leaderboards.
    Those values must come from the official backend program policy and your account ledger.

    **Questions?** Contact rewards@intellicv.ai
    """)

# Leaderboard
st.markdown("---")
st.markdown("### 🏅 Top Contributors")

st.info("Leaderboard is unavailable until the backend provides verified rankings.")
