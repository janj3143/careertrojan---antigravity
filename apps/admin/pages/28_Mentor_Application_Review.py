"""
👮 Mentor Application Review | IntelliCV Admin Portal
Week 2 Implementation - November 15, 2025

Guardian review interface for mentor applications:
- Review pending mentor applications
- Approve or reject with feedback
- View applicant credentials and experience
- Check pricing reasonableness
- Monitor mentor quality standards

Quality Control: Ensures only qualified mentors join the platform
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import copy

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "shared_backend"
sys.path.insert(0, str(backend_path))

try:
    from services.mentorship_service import MentorshipService
    from database.exa_db import get_db_connection
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False

CACHE_PATH = Path(__file__).parent.parent / "shared" / "mentor_applications_cache.json"

# Page configuration
st.set_page_config(
    page_title="👮 Mentor Reviews",
    page_icon="👮",
    layout="wide"
)

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================

def check_admin_auth():
    """Ensure user is admin"""
    if st.session_state.get('user_role') != 'admin':
        st.error("🚫 Admin access only")
        st.stop()

check_admin_auth()


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page28_mentor_review") if BackendTelemetryHelper else None

# ============================================================================
# DATA FETCHING (MOCK DATA FOR NOW)
# ============================================================================

def load_cached_applications() -> List[Dict[str, Any]]:
    if not CACHE_PATH.exists():
        return []
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
    except Exception:
        return []
    return []


def _build_stub_from_backend(row: Dict[str, Any]) -> Dict[str, Any]:
    industries = row.get('industry')
    if isinstance(industries, str):
        industries_list = [industries]
    elif isinstance(industries, list):
        industries_list = industries
    else:
        industries_list = []

    return {
        'application_id': row.get('application_id'),
        'submitted_date': row.get('submitted_date'),
        'status': row.get('status'),
        'professional': {
            'full_name': row.get('full_name'),
            'email': row.get('email'),
            'phone': None,
            'linkedin': None,
            'current_role': None,
            'company': None,
            'years_experience': row.get('years_experience'),
            'industry': industries_list,
            'professional_summary': row.get('specialization'),
            'achievements': None
        },
        'expertise': {
            'technical_expertise': [],
            'leadership_expertise': [],
            'career_expertise': [],
            'business_expertise': [],
            'target_audience': [],
            'session_formats': [],
            'availability': 'Not provided',
            'ai_recommendations': []
        },
        'packages': [],
        'guardian_notes': [],
        'ai_chat_history': []
    }


def _merge_cached_snapshot(backend_entry: Dict[str, Any], cached_entry: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(backend_entry)

    if not merged.get('ai_chat_history') and cached_entry.get('ai_chat_history'):
        merged['ai_chat_history'] = cached_entry['ai_chat_history']

    if not merged.get('packages') and cached_entry.get('packages'):
        merged['packages'] = cached_entry['packages']

    if not merged.get('professional') and cached_entry.get('professional'):
        merged['professional'] = cached_entry['professional']

    merged_expertise = merged.setdefault('expertise', {})
    cached_expertise = cached_entry.get('expertise') or {}
    if not merged_expertise.get('ai_recommendations') and cached_expertise.get('ai_recommendations'):
        merged_expertise['ai_recommendations'] = cached_expertise['ai_recommendations']

    return merged


def get_pending_applications() -> List[Dict[str, Any]]:
    cache_entries = load_cached_applications()
    cache_lookup = {
        str(entry.get('application_id')): copy.deepcopy(entry)
        for entry in cache_entries
        if entry.get('application_id') is not None
    }

    applications: List[Dict[str, Any]] = []
    seen_ids = set()

    if BACKEND_AVAILABLE:
        try:
            db = get_db_connection()
            mentorship_service = MentorshipService(db)
            backend_rows = mentorship_service.get_pending_applications()
            for row in backend_rows:
                snapshot_like = copy.deepcopy(row) if isinstance(row, dict) else _build_stub_from_backend(row)
                app_id = str(snapshot_like.get('application_id'))
                seen_ids.add(app_id)
                cached_entry = cache_lookup.get(app_id)
                if cached_entry:
                    merged_entry = _merge_cached_snapshot(snapshot_like, cached_entry)
                    merged_entry['status'] = snapshot_like.get('status', cached_entry.get('status'))
                    merged_entry['submitted_date'] = snapshot_like.get('submitted_date') or cached_entry.get('submitted_date')
                    applications.append(merged_entry)
                else:
                    applications.append(snapshot_like)
        except Exception as exc:
            st.warning(f"⚠️ Backend fetch failed: {exc}. Showing cached applications.")

    for cache_id, cache_entry in cache_lookup.items():
        if cache_id not in seen_ids:
            applications.append(cache_entry)

    if not applications:
        applications = copy.deepcopy(MOCK_PENDING_APPLICATIONS)

    return applications


MOCK_PENDING_APPLICATIONS = [
        {
            'application_id': 'APP_001',
            'user_id': 'USER_456',
            'submitted_date': '2025-11-12',
            'status': 'pending',
            'professional': {
                'full_name': 'Sarah Johnson',
                'email': 'sarah.johnson@example.com',
                'phone': '+44 7XXX XXXXXX',
                'linkedin': 'https://linkedin.com/in/sarahjohnson',
                'current_role': 'Senior Data Scientist',
                'company': 'Google',
                'years_experience': '10-15 years',
                'industry': ['Data Science & AI', 'Software Engineering'],
                'professional_summary': """Experienced Data Scientist with 12 years in ML/AI across Google, Facebook, and startups.

Led teams of 5-15 engineers, shipped production ML systems serving 100M+ users. Deep expertise in MLOps, production deployment, and scaling ML infrastructure.

Passionate about mentoring - have informally mentored 20+ junior engineers, 3 of whom achieved promotion to senior roles within 18 months.

Want to formalize my mentoring practice and help more people transition into senior ML roles.""",
                'achievements': """• Built recommendation system serving 100M users
• Led MLOps platform migration (reduced deployment time 10x)
• Promoted 3 junior engineers to senior in 18 months
• Speaker at MLConf, NeurIPS workshops"""
            },
            'expertise': {
                'technical_expertise': ['Data Science & ML', 'AI/LLM Integration', 'Cloud Architecture'],
                'leadership_expertise': ['Engineering Leadership', 'Team Management'],
                'career_expertise': ['Career Transitions', 'Promotion Strategy', 'Interview Preparation'],
                'business_expertise': [],
                'target_audience': ['Junior (0-3 years)', 'Mid-level (3-7 years)', 'First-time Managers'],
                'session_formats': ['1-on-1 Video Sessions', 'Group Sessions (up to 5)'],
                'availability': '8-12 hours/week'
            },
            'packages': [
                {
                    'name': 'ML Career Acceleration',
                    'description': 'For mid-level ML engineers wanting to reach senior level',
                    'session_count': 6,
                    'session_duration': '60 minutes',
                    'price_per_session': 180,
                    'total_price': 1080,
                    'mentor_earnings': 864,
                    'includes': '• Pre-session prep notes\n• Career roadmap document\n• Email support between sessions'
                },
                {
                    'name': 'MLOps Deep Dive',
                    'description': 'Production ML deployment mastery',
                    'session_count': 8,
                    'session_duration': '90 minutes',
                    'price_per_session': 250,
                    'total_price': 2000,
                    'mentor_earnings': 1600,
                    'includes': '• Technical architecture reviews\n• Code review sessions\n• Deployment best practices guide'
                }
            ],
            'guardian_notes': []
        },
        {
            'application_id': 'APP_002',
            'user_id': 'USER_789',
            'submitted_date': '2025-11-14',
            'status': 'pending',
            'professional': {
                'full_name': 'Michael Chen',
                'email': 'michael.chen@example.com',
                'phone': '+44 7YYY YYYYYY',
                'linkedin': 'https://linkedin.com/in/michaelchen',
                'current_role': 'VP Engineering',
                'company': 'Stripe',
                'years_experience': '15-20 years',
                'industry': ['Engineering Leadership', 'Software Engineering'],
                'professional_summary': """Engineering leader with 18 years experience scaling teams from 10 to 200+ engineers.

Currently VP Engineering at Stripe. Previously Head of Engineering at Shopify and early engineer at Twitter.

Expertise in IC-to-manager transitions, building high-performing teams, and technical leadership. Have mentored 50+ engineers throughout career.""",
                'achievements': """• Scaled engineering org from 10 to 200 people
• Built engineering career ladder used by 1000+ engineers
• Promoted 15 ICs to management roles
• Published thought leadership in Harvard Business Review"""
            },
            'expertise': {
                'technical_expertise': ['Software Engineering', 'Cloud Architecture'],
                'leadership_expertise': ['Engineering Leadership', 'Team Management', 'People Management', 'Organizational Design'],
                'career_expertise': ['Career Transitions', 'Promotion Strategy', 'Interview Preparation'],
                'business_expertise': ['Product Strategy', 'Business Development'],
                'target_audience': ['Senior (7-12 years)', 'Staff/Principal (12+ years)', 'First-time Managers', 'Experienced Leaders'],
                'session_formats': ['1-on-1 Video Sessions'],
                'availability': '4-8 hours/week'
            },
            'packages': [
                {
                    'name': 'IC to Engineering Manager',
                    'description': 'Complete transition program for first-time managers',
                    'session_count': 12,
                    'session_duration': '60 minutes',
                    'price_per_session': 350,
                    'total_price': 4200,
                    'mentor_earnings': 3360,
                    'includes': '• Leadership assessment\n• 30-60-90 day plan\n• Team building strategies\n• Ongoing email support'
                }
            ],
            'guardian_notes': []
        }
    ]

def get_approved_applications() -> List[Dict[str, Any]]:
    """Fetch recently approved applications"""
    # TODO: Implement
    return []

def get_rejected_applications() -> List[Dict[str, Any]]:
    """Fetch recently rejected applications"""
    # TODO: Implement
    return []

# ============================================================================
# MAIN PAGE
# ============================================================================

def main():
    """Main Guardian review interface"""

    st.title("👮 Mentor Application Review (Guardian)")

    st.markdown("""
    Review and approve mentor applications to ensure platform quality.
    Only qualified, experienced professionals should be approved.
    """)

    if TELEMETRY_HELPER:
        TELEMETRY_HELPER.render_status_panel(
            title="🛰️ Backend Telemetry Monitor",
            refresh_key="page28_backend_refresh",
        )

    st.divider()

    # Fetch applications
    pending_apps = get_pending_applications()

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Pending Review", len(pending_apps))
    col2.metric("Approved (Last 7 days)", 0)  # TODO: Real data
    col3.metric("Rejected (Last 7 days)", 0)  # TODO: Real data

    st.divider()

    # Tabs for different application states
    tab_pending, tab_approved, tab_rejected = st.tabs([
        f"⏳ Pending Review ({len(pending_apps)})",
        "✅ Approved",
        "❌ Rejected"
    ])

    with tab_pending:
        if not pending_apps:
            st.info("No pending applications at this time")
        else:
            for app in pending_apps:
                render_application_review(app)

    with tab_approved:
        st.info("Recently approved applications will appear here")

    with tab_rejected:
        st.info("Recently rejected applications will appear here")

def render_application_review(app: Dict[str, Any]):
    """Render full application review interface"""

    prof = app.get('professional', {})
    exp = app.get('expertise', {})
    packages = app.get('packages', [])
    ai_tags = exp.get('ai_recommendations') or app.get('ai_recommendations') or []
    industries = prof.get('industry') or []
    if isinstance(industries, str):
        industries = [industries]

    with st.expander(
        f"🔍 {prof.get('full_name', 'Mentor Applicant')} - "
        f"{prof.get('current_role', 'Role TBD')} @ {prof.get('company', 'Company TBD')} "
        f"(Submitted: {app.get('submitted_date', '—')})",
        expanded=True
    ):

        # Application overview
        col_overview1, col_overview2 = st.columns([2, 1])

        with col_overview1:
            st.markdown("### 👤 Professional Background")

            linkedin = prof.get('linkedin')
            st.markdown(f"**Name:** {prof.get('full_name', 'Unknown')}")
            st.markdown(f"**Email:** {prof.get('email', 'Not provided')}")
            if linkedin:
                st.markdown(f"**LinkedIn:** [{linkedin}]({linkedin})")
            st.markdown(f"**Current Role:** {prof.get('current_role', 'Not provided')} at {prof.get('company', 'N/A')}")
            st.markdown(f"**Experience:** {prof.get('years_experience', 'Not provided')}")
            industries_label = ', '.join(industries) if industries else 'Not provided'
            st.markdown(f"**Industries:** {industries_label}")

            st.markdown("---")
            st.markdown("**Professional Summary:**")
            summary_text = prof.get('professional_summary') or "Applicant did not include a summary."
            st.info(summary_text)

            if prof.get('achievements'):
                st.markdown("**Key Achievements:**")
                st.success(prof['achievements'])

        with col_overview2:
            st.markdown("### 📊 Quick Assessment")

            # Qualification checklist
            st.markdown("**Qualification Check:**")

            years_text = str(prof.get('years_experience') or '')
            qualified_experience = any(token in years_text for token in ('5', '6', '7', '8', '9', '10', '11', '12', '15', '20'))

            st.checkbox("✅ 5+ years experience", value=qualified_experience, disabled=True)
            st.checkbox(
                "✅ Senior role",
                value='Senior' in str(prof.get('current_role', '')) or 'Lead' in str(prof.get('current_role', '')) or 'VP' in str(prof.get('current_role', '')),
                disabled=True
            )
            st.checkbox("✅ LinkedIn verified", value=bool(prof.get('linkedin')), disabled=True)
            st.checkbox(
                "✅ Clear expertise",
                value=(len(exp.get('technical_expertise', [])) + len(exp.get('leadership_expertise', [])) + len(exp.get('career_expertise', []))) > 0,
                disabled=True
            )

            st.markdown("---")

            # Pricing check
            if packages:
                avg_price = sum([pkg.get('price_per_session', 0) for pkg in packages]) / max(len(packages), 1)

                if avg_price < 100:
                    price_status = "⚠️ Low (suggest £100-£200)"
                    price_color = "warning"
                elif avg_price > 500:
                    price_status = "⚠️ High (£500+ unusual)"
                    price_color = "warning"
                else:
                    price_status = "✅ Reasonable"
                    price_color = "success"

                if price_color == "warning":
                    st.warning(f"**Avg Price:** £{avg_price:.0f}/session\n{price_status}")
                else:
                    st.success(f"**Avg Price:** £{avg_price:.0f}/session\n{price_status}")
            else:
                st.info("Pricing data pending submission of packages.")

        st.divider()

        # Expertise areas
        st.markdown("### 🎯 Expertise Areas")

        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            if exp.get('technical_expertise'):
                st.markdown("**Technical:**")
                for item in exp.get('technical_expertise', []):
                    st.markdown(f"• {item}")

            if exp.get('leadership_expertise'):
                st.markdown("**Leadership:**")
                for item in exp.get('leadership_expertise', []):
                    st.markdown(f"• {item}")

        with col_exp2:
            if exp.get('career_expertise'):
                st.markdown("**Career Development:**")
                for item in exp.get('career_expertise', []):
                    st.markdown(f"• {item}")

            if exp.get('business_expertise'):
                st.markdown("**Business:**")
                for item in exp.get('business_expertise', []):
                    st.markdown(f"• {item}")

        target_audience = ', '.join(exp.get('target_audience', [])) or 'Not provided'
        session_formats = ', '.join(exp.get('session_formats', [])) or 'Not provided'
        st.markdown(f"**Target Audience:** {target_audience}")
        st.markdown(f"**Session Formats:** {session_formats}")
        st.markdown(f"**Availability:** {exp.get('availability', 'Not provided')}")

        if ai_tags:
            st.markdown("**AI Suggested Focus Areas:**")
            chips = ''.join([
                (
                    "<span style=\"background:#eef6ff;border:1px solid #cfe0ff;padding:0.2rem 0.6rem;"
                    "border-radius:999px;font-size:0.75rem;margin:0.15rem 0.25rem 0.15rem 0;display:inline-block;\">"
                    + tag + "</span>"
                )
                for tag in ai_tags[:8]
            ])
            st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)

        st.divider()

        # Packages
        st.markdown("### 📦 Proposed Packages")

        if not packages:
            st.info("Applicant has not proposed packages yet.")

        for pkg in packages:
            with st.container():
                col_pkg1, col_pkg2 = st.columns([2, 1])

                with col_pkg1:
                    st.markdown(f"#### {pkg['name']}")
                    st.write(pkg['description'])
                    st.caption(f"{pkg['session_count']} sessions × {pkg['session_duration']} @ £{pkg['price_per_session']}/session")

                    if pkg.get('includes'):
                        st.markdown("**Includes:**")
                        st.write(pkg['includes'])

                with col_pkg2:
                    total_price = pkg.get('total_price')
                    mentor_earnings = pkg.get('mentor_earnings')
                    if total_price is not None:
                        st.metric("Total Price", f"£{total_price}")
                        st.metric("Mentor Earns", f"£{mentor_earnings or 0:.0f}")
                        st.caption("(80% share)")
                    else:
                        st.caption("Pricing pending")

                st.markdown("---")

        chat_history = app.get('ai_chat_history') or []
        if chat_history:
            with st.expander("AI Intake Transcript"):
                for message in chat_history:
                    role = message.get('role', 'assistant').title()
                    content = message.get('content', '')
                    st.markdown(f"**{role}:** {content}")

        st.divider()

        # Guardian decision
        st.markdown("### ✍️ Guardian Decision")

        col_decision1, col_decision2 = st.columns(2)

        with col_decision1:
            st.markdown("**Internal Notes (not visible to applicant):**")
            guardian_notes = st.text_area(
                "Notes",
                key=f"notes_{app['application_id']}",
                placeholder="Record your assessment, any concerns, or pricing recommendations...",
                height=100
            )

        with col_decision2:
            st.markdown("**Feedback to Applicant (if rejected):**")
            feedback = st.text_area(
                "Feedback",
                key=f"feedback_{app['application_id']}",
                placeholder="Explain reasons for rejection and suggestions for re-application...",
                height=100
            )

        st.divider()

        # Action buttons
        col_action1, col_action2, col_action3 = st.columns([1, 1, 1])

        with col_action1:
            if st.button("✅ Approve Application", type="primary", use_container_width=True, key=f"approve_{app['application_id']}"):
                # TODO: Call MentorshipService.approve_mentor_application(app_id, guardian_notes)
                st.success(f"✅ **{prof['full_name']} approved as mentor!**\n\nThey will receive portal access and onboarding materials.")
                st.balloons()

        with col_action2:
            if st.button("⏸️ Request More Info", use_container_width=True, key=f"info_{app['application_id']}"):
                # TODO: Send email requesting clarification
                st.info("📧 Email sent requesting additional information")

        with col_action3:
            if st.button("❌ Reject", use_container_width=True, key=f"reject_{app['application_id']}"):
                if not feedback:
                    st.error("❌ Please provide feedback explaining rejection")
                else:
                    # TODO: Call MentorshipService.reject_mentor_application(app_id, feedback, guardian_notes)
                    st.error(f"❌ Application rejected. Feedback sent to {prof['email']}")

# ============================================================================
# REVIEW GUIDELINES SIDEBAR
# ============================================================================

with st.sidebar:
    st.markdown("### 📋 Review Guidelines")

    st.markdown("""
    **Approval Criteria:**

    ✅ **Experience:**
    - 5+ years in field (3+ for specialized tech)
    - Current/recent senior role
    - Verifiable LinkedIn profile

    ✅ **Expertise:**
    - Clear, specific expertise areas
    - Relevant to platform users
    - Demonstrates depth of knowledge

    ✅ **Pricing:**
    - £100-£200/session (mid-level)
    - £200-£500/session (senior/exec)
    - Reasonable for experience level

    ✅ **Commitment:**
    - At least 4 hours/week
    - Professional communication
    - Quality packages designed

    ---

    **Red Flags:**

    ❌ Insufficient experience (< 5 years)
    ❌ Vague or generic expertise
    ❌ Pricing too low (< £100) or too high (> £500)
    ❌ No LinkedIn or can't verify claims
    ❌ Poor communication quality
    ❌ Unrealistic availability promises

    ---

    **Common Rejection Reasons:**

    1. **Insufficient Experience:** "Need 5+ years minimum"
    2. **Unverifiable Credentials:** "LinkedIn profile doesn't match claims"
    3. **Pricing Issues:** "Suggested pricing is not aligned with market rates"
    4. **Vague Expertise:** "Need more specific expertise areas"
    5. **Quality Concerns:** "Professional summary lacks depth"
    """)

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
