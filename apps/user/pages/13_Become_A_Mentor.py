"""
🎓 Become a Mentor | IntelliCV Platform
Week 1 Implementation - November 15, 2025

Multi-step mentor application and onboarding process:
- Step 1: Professional Background
- Step 2: Mentorship Expertise
- Step 3: Package Design
- Step 4: Guardian Review (auto-submitted)
- Step 5: Application Complete (confirmation)

Privacy-Protected Mentor-User Linking System
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, List, Tuple, Optional
from uuid import uuid4

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "shared_backend"
sys.path.insert(0, str(backend_path))

try:
    from services.mentorship_service import MentorshipService
    from database.exa_db import get_db_connection
except ImportError as e:
    st.error(f"⚠️ Backend services not available: {e}")

try:
    from shared_backend.services.portal_bridge import ChatService
    mentor_intake_chat = ChatService()
    MENTOR_CHAT_AVAILABLE = True
except Exception:
    mentor_intake_chat = None
    MENTOR_CHAT_AVAILABLE = False

try:
    from utils.mentor_application_snapshot import build_application_snapshot
except ImportError as snapshot_import_error:
    build_application_snapshot = None

# Page configuration
st.set_page_config(
    page_title="🎓 Become a Mentor",
    page_icon="🎓",
    layout="wide"
)

# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================

def check_authentication():
    """Ensure user is logged in"""
    if not st.session_state.get('authenticated_user'):
        st.error("🔒 Please log in to apply as a mentor")
        st.info("👉 Go to Home page to log in")
        st.stop()

    # Check if user already has mentor status
    if st.session_state.get('user_role') == 'mentor':
        st.success("✅ You already have mentor access!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Go to Mentor Portal", use_container_width=True):
                st.switch_page("mentor_portal/main.py")
        with col2:
            if st.button("📊 View My Earnings", use_container_width=True):
                st.switch_page("mentor_portal/pages/05_Earnings_Payouts.py")
        st.stop()

check_authentication()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'mentor_app_step' not in st.session_state:
    st.session_state.mentor_app_step = 0

if 'mentor_app_data' not in st.session_state:
    st.session_state.mentor_app_data = {
        'step1': {},
        'step2': {},
        'step3': {}
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def next_step():
    """Advance to next step"""
    st.session_state.mentor_app_step += 1

def previous_step():
    """Go back to previous step"""
    if st.session_state.mentor_app_step > 0:
        st.session_state.mentor_app_step -= 1

def save_step_data(step_num: int, data: Dict[str, Any]):
    """Save data for current step"""
    st.session_state.mentor_app_data[f'step{step_num}'] = data


MENTOR_ADMIN_SERVICE_LINKS: List[Tuple[str, str]] = [
    ("MentorshipService · approvals", "admin_portal/services/mentorship_service.py"),
    ("UserDataService · peer graph", "admin_portal/services/user_data_service.py"),
    ("Career Coach AI", "admin_portal/services/career/career_coach.py"),
    ("Intelligence Hub Connector", "admin_portal/services/intelligence_hub_connector.py"),
]


MENTOR_EXPERTISE_OPTIONS: List[str] = [
    "Career Transitions",
    "Leadership Development",
    "Technical Skills (Programming)",
    "Interview Preparation",
    "Resume & LinkedIn Optimization",
    "Salary Negotiation",
    "Work-Life Balance",
    "Startup Advice",
    "Product Management",
    "Data Science & Analytics",
    "Cloud & DevOps",
    "Marketing & Growth",
    "Sales & Business Development",
    "Other"
]


def _mentor_application_cache_path() -> Path:
    return Path(__file__).parent.parent / "shared" / "mentor_applications_cache.json"


def _load_application_cache() -> List[Dict[str, Any]]:
    cache_path = _mentor_application_cache_path()
    if not cache_path.exists():
        return []
    try:
        with open(cache_path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
    except Exception:
        return []
    return []


def _persist_application_snapshot(snapshot: Dict[str, Any]) -> None:
    cache = _load_application_cache()
    cache = [entry for entry in cache if entry.get('application_id') != snapshot.get('application_id')]
    cache.append(snapshot)

    cache_path = _mentor_application_cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as handle:
        json.dump(cache, handle, indent=2)



def render_admin_service_links() -> None:
    """Display admin service modules listening to the intake."""
    chips = ''.join([
        (
            "<span style=\"background:#eef6ff;border:1px solid #cfe0ff;padding:0.2rem 0.6rem;"
            "border-radius:999px;font-size:0.75rem;margin:0.15rem 0.25rem 0.15rem 0;display:inline-block;\">"
            + f"{label} · {path}" + "</span>"
        )
        for label, path in MENTOR_ADMIN_SERVICE_LINKS
    ])
    st.caption("Always-on admin services wired into this chat:")
    st.markdown(f"<div style='margin-bottom:0.5rem;'>{chips}</div>", unsafe_allow_html=True)


def extract_ai_focus_tags(ai_text: str, reference_options: List[str]) -> List[str]:
    """Map AI free-form responses to known expertise options."""
    if not ai_text:
        return []
    normalized: List[str] = []
    lower_text = ai_text.lower()
    for option in reference_options:
        if option.lower() in lower_text and option not in normalized:
            normalized.append(option)
    # also capture bullet-style custom tags
    for line in ai_text.splitlines():
        cleaned = line.strip("-• •\t ")
        if cleaned and len(cleaned) <= 60 and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized[:8]


def run_mentor_intake_assistant(expertise_options: List[str]) -> None:
    """Interactive AI chat to capture mentor expertise."""
    st.markdown("#### 🤖 Mentor Scope Builder (Live Admin AI)")
    st.caption("Feeds Mentor Management, Intelligence Hub, and user data services so reviewers see the same context.")
    render_admin_service_links()

    history_key = 'mentor_ai_chat_history'
    if history_key not in st.session_state:
        st.session_state[history_key] = [
            {
                "role": "assistant",
                "content": (
                    "I'm synced with the admin Mentor Management stack. Describe your signature wins, industries, "
                    "and transformations so I can tag your expertise areas."
                )
            }
        ]

    for message in st.session_state[history_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Describe standout projects, industries served, and mentee outcomes",
        key="mentor_ai_chat_input"
    )

    if prompt:
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response_text: str
        if MENTOR_CHAT_AVAILABLE and mentor_intake_chat:
            try:
                context = {
                    "flow": "mentor_application_step2",
                    "step1": st.session_state.mentor_app_data.get('step1', {}),
                    "existing_focus": st.session_state.mentor_app_data.get('step2', {}).get('expertise_areas', []),
                    "admin_services": [label for label, _ in MENTOR_ADMIN_SERVICE_LINKS]
                }
                ai_payload = mentor_intake_chat.ask(
                    question=prompt,
                    context=context,
                    user_id=st.session_state.get('user_id')
                )
                if isinstance(ai_payload, dict):
                    response_text = (
                        ai_payload.get('content')
                        or ai_payload.get('answer')
                        or ai_payload.get('message')
                        or "Admin AI captured your profile."
                    )
                else:
                    response_text = str(ai_payload)
            except Exception as exc:
                response_text = (
                    "Admin chat bridge hiccuped; retry in a moment. Meanwhile list 3-4 focus areas so I can tag them manually. "
                    f"(details: {exc})"
                )
        else:
            response_text = (
                "Admin AI bridge is offline in this environment. Summarize your standout engagements and I'll still stash them for the reviewer."
            )

        with st.chat_message("assistant"):
            st.markdown(response_text)

        st.session_state[history_key].append({"role": "assistant", "content": response_text})

        suggestions = extract_ai_focus_tags(response_text, expertise_options)
        if suggestions:
            step2_state = st.session_state.mentor_app_data.setdefault('step2', {})
            existing = step2_state.get('ai_recommendations', [])
            merged = existing + [item for item in suggestions if item not in existing]
            step2_state['ai_recommendations'] = merged[:10]
            st.toast("AI tagged fresh expertise suggestions from your story.")

# ============================================================================
# LANDING PAGE (Step 0)
# ============================================================================

def show_landing_page():
    """Welcome page explaining mentor program"""

    st.title("🎓 Become a Mentor - Share Your Expertise, Earn Revenue")

    st.markdown("""
    ### 💡 Why Become a Mentor on IntelliCV?

    **Earn While Helping Others Grow**
    - Set your own rates (typically £100-£200/session)
    - **80% goes to you**, 20% platform fee
    - Flexible scheduling - work when you want
    - Platform handles payments and administration

    **Build Your Professional Brand**
    - Showcase your expertise to thousands of users
    - Expand your professional network
    - Gain leadership and coaching experience
    - Access to mentor community and resources

    **We Provide the Tools**
    - 🤖 **AI Assistant** - Helps you extract better requirements from clients
    - 📝 **Document Generator** - Creates professional mentorship agreements
    - 💰 **Payment System** - Secure, transparent invoicing and payouts
    - 👥 **Peer Community** - Learn from experienced mentors
    """)

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.metric("Average Mentor Earnings", "£120/session", "80% of payment")

    with col2:
        st.metric("Session Duration", "45-90 min", "You choose")

    with col3:
        st.metric("Active Mentors", "Growing", "Join early")

    st.divider()

    st.markdown("""
    ### 📋 What You'll Need

    - ✅ **3+ years professional experience** in your field
    - ✅ **LinkedIn profile** (for verification)
    - ✅ **4-6 hours/week** availability (minimum)
    - ✅ **Passion for helping others** succeed

    ### 🚀 Application Process

    1. **Professional Background** - Tell us about your experience
    2. **Mentorship Expertise** - What can you mentor in?
    3. **Package Design** - Create your initial offerings
    4. **Guardian Review** - We review and approve (24-48 hours)
    5. **Activation** - Start mentoring!

    """)

    st.info("⏱️ **Application takes 10-15 minutes to complete**")

    if st.button("🚀 Start Application", type="primary", use_container_width=True):
        next_step()
        st.rerun()

# ============================================================================
# STEP 1: PROFESSIONAL BACKGROUND
# ============================================================================

def show_professional_background_form():
    """Step 1: Collect professional background"""

    st.title("📋 Step 1: Professional Background")
    st.progress(0.2)

    st.markdown("**Tell us about your professional experience**")

    with st.form("professional_background"):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input(
                "Full Name *",
                value=st.session_state.mentor_app_data['step1'].get('full_name', '')
            )

            email = st.text_input(
                "Email *",
                value=st.session_state.mentor_app_data['step1'].get('email', st.session_state.get('user_email', ''))
            )

            phone = st.text_input(
                "Phone",
                value=st.session_state.mentor_app_data['step1'].get('phone', '')
            )

        with col2:
            linkedin_url = st.text_input(
                "LinkedIn Profile URL *",
                value=st.session_state.mentor_app_data['step1'].get('linkedin_url', '')
            )

            industry = st.selectbox(
                "Industry *",
                options=[
                    "",
                    "Software Engineering",
                    "Data Science",
                    "Product Management",
                    "Marketing",
                    "Finance",
                    "Healthcare",
                    "Education",
                    "Consulting",
                    "Other"
                ],
                index=0 if not st.session_state.mentor_app_data['step1'].get('industry') else
                      ["", "Software Engineering", "Data Science", "Product Management", "Marketing", "Finance", "Healthcare", "Education", "Consulting", "Other"].index(st.session_state.mentor_app_data['step1'].get('industry'))
            )

            years_experience = st.number_input(
                "Years of Professional Experience *",
                min_value=0,
                max_value=50,
                value=st.session_state.mentor_app_data['step1'].get('years_experience', 0),
                step=1
            )

        st.divider()

        specialization = st.text_area(
            "Your Specialization *",
            value=st.session_state.mentor_app_data['step1'].get('specialization', ''),
            help="What specific area(s) are you expert in?"
        )

        col1, col2 = st.columns(2)

        with col1:
            current_role = st.text_input(
                "Current Role *",
                value=st.session_state.mentor_app_data['step1'].get('current_role', '')
            )

        with col2:
            current_company = st.text_input(
                "Current Company",
                value=st.session_state.mentor_app_data['step1'].get('current_company', '')
            )

        st.divider()

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.form_submit_button("⬅️ Back", use_container_width=True):
                previous_step()
                st.rerun()

        with col2:
            submitted = st.form_submit_button("Next ➡️", type="primary", use_container_width=True)

            if submitted:
                # Validation
                if not all([full_name, email, linkedin_url, industry, specialization, current_role]):
                    st.error("❌ Please fill in all required fields (*)")
                elif years_experience < 3:
                    st.error("❌ Minimum 3 years professional experience required")
                elif not linkedin_url.startswith("http"):
                    st.error("❌ Please enter a valid LinkedIn URL")
                else:
                    # Save data
                    save_step_data(1, {
                        'full_name': full_name,
                        'email': email,
                        'phone': phone,
                        'linkedin_url': linkedin_url,
                        'industry': industry,
                        'years_experience': years_experience,
                        'specialization': specialization,
                        'current_role': current_role,
                        'current_company': current_company
                    })
                    next_step()
                    st.rerun()

# ============================================================================
# STEP 2: MENTORSHIP EXPERTISE
# ============================================================================

def show_mentorship_expertise_form():
    """Step 2: What can you mentor in?"""

    st.title("🎯 Step 2: Mentorship Expertise")
    st.progress(0.4)

    st.markdown("**What will you mentor in? Who will you help?**")

    step2_state = st.session_state.mentor_app_data.setdefault('step2', {})

    run_mentor_intake_assistant(MENTOR_EXPERTISE_OPTIONS)

    ai_recommendations = step2_state.get('ai_recommendations', [])
    if ai_recommendations:
        st.info(
            "AI spotted focus areas based on your chat: "
            + ", ".join(ai_recommendations[:6])
        )
        if st.button("Apply AI suggestions to selectors", key="apply_ai_expertise"):
            existing = set(step2_state.get('expertise_areas', []))
            existing.update(ai_recommendations)
            step2_state['expertise_areas'] = list(existing)
            st.session_state.mentor_app_data['step2'] = step2_state
            st.success("Applied AI suggestions to your expertise list.")
            st.rerun()

    st.divider()

    with st.form("mentorship_expertise"):

        # Expertise areas
        st.subheader("Areas of Expertise")
        expertise_areas = st.multiselect(
            "Select all that apply *",
            options=MENTOR_EXPERTISE_OPTIONS,
            default=step2_state.get('expertise_areas', [])
        )

        if "Other" in expertise_areas:
            expertise_other = st.text_input(
                "Please specify other areas",
                value=step2_state.get('expertise_other', '')
            )
        else:
            expertise_other = ""

        st.divider()

        # Target audience
        st.subheader("Target Audience")
        target_audience = st.multiselect(
            "Who will you mentor? *",
            options=["Junior (0-3 years)", "Mid-level (3-7 years)", "Senior (7-12 years)", "Executive (12+ years)", "Career Changers", "Students"],
            default=step2_state.get('target_audience', [])
        )

        st.divider()

        # Session preferences
        st.subheader("Session Preferences")

        col1, col2 = st.columns(2)

        with col1:
            session_formats = st.multiselect(
                "Session Formats *",
                options=["1-on-1 Sessions", "Group Sessions (2-5 people)", "Workshops (6+ people)"],
                default=step2_state.get('session_formats', [])
            )

        with col2:
            hours_per_week = st.number_input(
                "Hours Available Per Week *",
                min_value=0,
                max_value=40,
                value=step2_state.get('hours_per_week', 4),
                step=1,
                help="Work with each mentee to set the cadence; most programs co-create ~1 hour/week of availability."
            )

        st.divider()

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.form_submit_button("⬅️ Back", use_container_width=True):
                previous_step()
                st.rerun()

        with col2:
            submitted = st.form_submit_button("Next ➡️", type="primary", use_container_width=True)

            if submitted:
                # Validation
                if not expertise_areas:
                    st.error("❌ Please select at least one area of expertise")
                elif not target_audience:
                    st.error("❌ Please select at least one target audience")
                elif not session_formats:
                    st.error("❌ Please select at least one session format")
                elif hours_per_week < 4:
                    st.error("❌ Minimum 4 hours/week required")
                else:
                    # Save data
                    save_step_data(2, {
                        'expertise_areas': expertise_areas,
                        'expertise_other': expertise_other,
                        'target_audience': target_audience,
                        'session_formats': session_formats,
                        'hours_per_week': hours_per_week
                    })
                    next_step()
                    st.rerun()

# ============================================================================
# STEP 3: PACKAGE DESIGN
# ============================================================================

def show_package_design_form():
    """Step 3: Create initial mentorship packages"""

    st.title("💰 Step 3: Package Design")
    st.progress(0.6)

    st.markdown("""
    **Create your initial mentorship packages**

    💡 **Pricing Guidance:**
    - Entry-level mentors (3-5 years): £75-£125/session
    - Mid-level mentors (5-10 years): £100-£175/session
    - Senior mentors (10+ years): £150-£250/session
    - Executive mentors (15+ years): £200-£350/session

    *Remember: You receive 80%, platform takes 20%*
    """)

    st.divider()

    # Initialize packages if not exists
    if 'packages' not in st.session_state.mentor_app_data['step3']:
        st.session_state.mentor_app_data['step3']['packages'] = [
            {'name': '', 'description': '', 'duration': 60, 'price': 0, 'sessions': 1}
        ]

    packages = st.session_state.mentor_app_data['step3']['packages']

    st.subheader("📦 Your Packages")

    # Allow up to 3 packages
    for idx, package in enumerate(packages[:3]):
        with st.expander(f"Package {idx + 1}" + (" *" if idx == 0 else ""), expanded=(idx == 0)):
            col1, col2 = st.columns([2, 1])

            with col1:
                package['name'] = st.text_input(
                    "Package Name" + (" *" if idx == 0 else ""),
                    value=package.get('name', ''),
                    key=f"pkg_name_{idx}"
                )

                package['description'] = st.text_area(
                    "Description" + (" *" if idx == 0 else ""),
                    value=package.get('description', ''),
                    key=f"pkg_desc_{idx}",
                    height=100
                )

            with col2:
                package['duration'] = st.selectbox(
                    "Session Duration" + (" *" if idx == 0 else ""),
                    options=[30, 45, 60, 90, 120],
                    index=[30, 45, 60, 90, 120].index(package.get('duration', 60)),
                    key=f"pkg_dur_{idx}",
                    help="Minutes per session"
                )

                package['sessions'] = st.number_input(
                    "Number of Sessions" + (" *" if idx == 0 else ""),
                    min_value=1,
                    max_value=24,
                    value=package.get('sessions', 1),
                    key=f"pkg_sess_{idx}",
                    help="1 = single session, 6 = package of 6"
                )

                package['price'] = st.number_input(
                    "Price per Session (£)" + (" *" if idx == 0 else ""),
                    min_value=0,
                    max_value=500,
                    value=package.get('price', 0),
                    step=5,
                    key=f"pkg_price_{idx}"
                )

            # Show earnings
            if package['price'] > 0:
                mentor_portion = package['price'] * 0.8
                platform_fee = package['price'] * 0.2
                total_package_value = package['price'] * package.get('sessions', 1)
                mentor_earns = total_package_value * 0.8

                st.success(f"💰 You earn: **£{mentor_portion:.2f}/session** (£{platform_fee:.2f} platform fee) | Package total: **£{mentor_earns:.2f}** (£{total_package_value:.2f} package)")

    st.divider()

    # Add package button
    if len(packages) < 3:
        if st.button("➕ Add Another Package (Optional)"):
            packages.append({'name': '', 'description': '', 'duration': 60, 'price': 0, 'sessions': 1})
            st.session_state.mentor_app_data['step3']['packages'] = packages
            st.rerun()

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("⬅️ Back", use_container_width=True):
            previous_step()
            st.rerun()

    with col2:
        if st.button("Submit Application 🚀", type="primary", use_container_width=True):
            # Validation - at least one package required
            first_package = packages[0]

            if not all([first_package.get('name'), first_package.get('description')]):
                st.error("❌ Please complete at least one package (Package 1)")
            elif first_package.get('price', 0) < 50:
                st.error("❌ Minimum price is £50/session")
            else:
                # Filter out empty packages
                valid_packages = [
                    p for p in packages
                    if p.get('name') and p.get('description') and p.get('price', 0) >= 50
                ]

                # Save data
                save_step_data(3, {'packages': valid_packages})

                # Submit application
                submit_application()
                next_step()
                st.rerun()

# ============================================================================
# APPLICATION SUBMISSION
# ============================================================================

def submit_application():
    """Submit application to database"""

    try:
        # Get database connection
        db = get_db_connection()
        mentorship_service = MentorshipService(db)

        # Combine all form data
        step1 = st.session_state.mentor_app_data['step1']
        step2 = st.session_state.mentor_app_data['step2']
        step3 = st.session_state.mentor_app_data['step3']
        chat_history = st.session_state.get('mentor_ai_chat_history', [])

        application_data = {
            'phone': step1.get('phone'),
            'linkedin_url': step1.get('linkedin_url'),
            'industry': step1.get('industry'),
            'specialization': step1.get('specialization'),
            'years_experience': step1.get('years_experience'),
            'current_role': step1.get('current_role'),
            'current_company': step1.get('current_company'),
            'expertise_areas': step2.get('expertise_areas'),
            'target_audience': step2.get('target_audience'),
            'session_formats': step2.get('session_formats'),
            'hours_per_week': step2.get('hours_per_week'),
            'initial_packages': step3.get('packages'),
            'expertise_other': step2.get('expertise_other'),
            'ai_recommendations': step2.get('ai_recommendations', []),
            'ai_chat_history': chat_history,
            'step1': step1,
            'step2': step2,
            'step3': step3
        }

        # Submit
        result = mentorship_service.submit_mentor_application(
            applicant_user_id=st.session_state.get('user_id', st.session_state.get('authenticated_user')),
            email=step1.get('email'),
            full_name=step1.get('full_name'),
            application_data=application_data
        )

        st.session_state.mentor_app_id = result['application_id']
        st.session_state.mentor_app_status = result['status']

        if build_application_snapshot:
            snapshot = build_application_snapshot(
                application_id=str(result['application_id']),
                status=result.get('status', 'submitted'),
                submitted_date=result.get('submitted_date'),
                step1=step1,
                step2=step2,
                step3=step3,
                ai_chat_history=chat_history
            )
            _persist_application_snapshot(snapshot)
        else:
            st.warning("Snapshot helper unavailable; cached admin preview skipped.")

    except Exception as e:
        st.error(f"❌ Error submitting application: {e}")
        st.stop()

# ============================================================================
# STEP 4: APPLICATION COMPLETE
# ============================================================================

def show_application_complete():
    """Confirmation page"""

    st.title("✅ Application Submitted!")
    st.progress(1.0)

    st.balloons()

    st.success("""
    ### 🎉 Thank you for applying to become a mentor!

    Your application has been submitted and is now under review by our Guardian team.
    """)

    st.info(f"""
    **Application ID:** {st.session_state.get('mentor_app_id', 'N/A')}

    **What happens next?**

    1. **Guardian Review** (24-48 hours)
       - We'll verify your credentials and experience
       - Review your proposed packages and pricing
       - Check your LinkedIn profile

    2. **Email Notification**
       - You'll receive an email when your application is reviewed
       - If approved, you'll get your Mentor Portal credentials
       - If more information is needed, we'll reach out

    3. **Activation** (Upon Approval)
       - Access to Mentor Portal granted
       - Your packages go live in the Mentorship Marketplace
       - Start receiving mentorship requests!
    """)

    st.divider()

    st.subheader("📊 Your Application Summary")

    step1 = st.session_state.mentor_app_data['step1']
    step2 = st.session_state.mentor_app_data['step2']
    step3 = st.session_state.mentor_app_data['step3']

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Professional Background**")
        st.write(f"- **Name:** {step1.get('full_name')}")
        st.write(f"- **Industry:** {step1.get('industry')}")
        st.write(f"- **Experience:** {step1.get('years_experience')} years")
        st.write(f"- **Role:** {step1.get('current_role')}")

    with col2:
        st.markdown("**Mentorship Focus**")
        st.write(f"- **Expertise:** {', '.join(step2.get('expertise_areas', []))}")
        st.write(f"- **Target Audience:** {', '.join(step2.get('target_audience', []))}")
        st.write(f"- **Availability:** {step2.get('hours_per_week')} hours/week")

    st.divider()

    st.markdown("**Your Packages:**")
    for idx, package in enumerate(step3.get('packages', []), 1):
        with st.expander(f"Package {idx}: {package['name']}"):
            st.write(f"**Description:** {package['description']}")
            st.write(f"**Duration:** {package['duration']} minutes")
            st.write(f"**Sessions:** {package['sessions']}")
            st.write(f"**Price:** £{package['price']}/session")
            st.write(f"**Your Earnings:** £{package['price'] * 0.8:.2f}/session (80%)")

    st.divider()

    if st.button("🏠 Return to Dashboard", use_container_width=True, type="primary"):
        # Reset application state
        st.session_state.mentor_app_step = 0
        st.session_state.mentor_app_data = {'step1': {}, 'step2': {}, 'step3': {}}
        st.switch_page("user_portal_final/pages/04_Dashboard.py")

# ============================================================================
# MAIN APP ROUTING
# ============================================================================

def main():
    """Main application router"""

    step = st.session_state.mentor_app_step

    if step == 0:
        show_landing_page()
    elif step == 1:
        show_professional_background_form()
    elif step == 2:
        show_mentorship_expertise_form()
    elif step == 3:
        show_package_design_form()
    elif step == 4:
        show_application_complete()
    else:
        st.error("Invalid step")
        st.session_state.mentor_app_step = 0
        st.rerun()

if __name__ == "__main__":
    main()
