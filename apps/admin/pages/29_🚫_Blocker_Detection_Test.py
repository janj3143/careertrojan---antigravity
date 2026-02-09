"""
🚫 Application Blocker Detection Test Page
=========================================

Quick test page to verify Application Blockers system integration.
Shows:
- Service availability status
- Live blocker detection
- Improvement suggestions
- Objection script generation

This is a TEST PAGE - can be removed after verification.
"""

import streamlit as st
import sys
from pathlib import Path

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Add shared_backend to path
shared_backend_path = Path(__file__).parent.parent.parent / "shared_backend"
if str(shared_backend_path) not in sys.path:
    sys.path.insert(0, str(shared_backend_path))

try:
    from services.blocker_connector import get_blocker_connector
    BLOCKER_AVAILABLE = True
except ImportError as e:
    BLOCKER_AVAILABLE = False
    st.error(f"❌ Blocker system not available: {e}")


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page29_blocker_test") if BackendTelemetryHelper else None

st.set_page_config(
    page_title="🚫 Blocker Detection Test",
    page_icon="🚫",
    layout="wide"
)

st.title("🚫 Application Blocker Detection Test")
st.caption("Test page to verify Application Blockers system integration")

if TELEMETRY_HELPER:
    TELEMETRY_HELPER.render_status_panel(
        title="🛰️ Backend Telemetry Monitor",
        refresh_key="page29_backend_refresh",
    )

# ========================================
# STATUS CHECK
# ========================================

st.header("📊 System Status")

if BLOCKER_AVAILABLE:
    connector = get_blocker_connector()
    status = connector.get_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if status['services_available']:
            st.success("✅ Services Available")
        else:
            st.error("❌ Services Missing")

    with col2:
        if status['detector_loaded']:
            st.success("✅ Detector Loaded")
        else:
            st.error("❌ Detector Missing")

    with col3:
        if status['service_loaded']:
            st.success("✅ Service Loaded")
        else:
            st.error("❌ Service Missing")

    with col4:
        if status['ready']:
            st.success("✅ System Ready")
        else:
            st.warning("⚠️ Not Ready")

    with st.expander("📋 Detailed Status"):
        st.json(status)
else:
    st.error("❌ Blocker connector not available")
    st.stop()

# ========================================
# LIVE DETECTION TEST
# ========================================

st.header("🔍 Live Blocker Detection")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Job Description")
    jd_text = st.text_area(
        "Enter Job Description",
        value="""Senior Machine Learning Engineer

Required Qualifications:
• 5+ years of professional ML experience
• MS/PhD in Computer Science or related field
• Expert in Python, TensorFlow, PyTorch
• AWS cloud experience (SageMaker, EC2)
• Leadership experience managing ML teams
• Published research papers preferred

Must have:
- Strong communication skills
- Agile/Scrum methodology experience
- Security clearance (or ability to obtain)""",
        height=300
    )

with col2:
    st.subheader("📋 Resume Data")

    skills_input = st.text_input(
        "Skills (comma-separated)",
        value="Python, TensorFlow, SQL, Git"
    )
    skills = [s.strip() for s in skills_input.split(',')]

    experience_years = st.number_input(
        "Years of Experience",
        min_value=0,
        max_value=50,
        value=3
    )

    certifications_input = st.text_input(
        "Certifications (comma-separated)",
        value="AWS Certified Developer"
    )
    certifications = [c.strip() for c in certifications_input.split(',') if c.strip()]

    education_level = st.selectbox(
        "Education Level",
        ["high_school", "associate", "bachelor", "master", "phd"],
        index=2  # bachelor
    )

    has_leadership = st.checkbox("Has Leadership Experience", value=False)

# Detect button
if st.button("🔍 Detect Blockers", type="primary", use_container_width=True):
    if not connector.is_available():
        st.error("❌ Blocker detection service not ready")
    else:
        resume_data = {
            'skills': skills,
            'experience_years': experience_years,
            'certifications': certifications,
            'education_level': education_level,
            'has_leadership': has_leadership
        }

        with st.spinner("Analyzing application blockers..."):
            result = connector.detect_blockers_for_user(jd_text, resume_data)

        if 'error' in result:
            st.error(f"❌ Detection failed: {result['error']}")
        else:
            # Summary metrics
            st.success(f"✅ Analysis complete - Found {result['total_blockers']} blockers")

            metric_cols = st.columns(5)
            with metric_cols[0]:
                st.metric("🔴 Critical", result.get('critical_count', 0))
            with metric_cols[1]:
                st.metric("🟠 Major", result.get('major_count', 0))
            with metric_cols[2]:
                st.metric("🟡 Moderate", result.get('moderate_count', 0))
            with metric_cols[3]:
                st.metric("🟢 Minor", result.get('minor_count', 0))
            with metric_cols[4]:
                st.metric("📊 Impact Score", f"{result['overall_impact']:.1f}/10")

            # Detailed blockers
            if result['blockers']:
                st.header("🚫 Detected Blockers")

                for idx, blocker in enumerate(result['blockers'], 1):
                    severity = blocker.get('severity', 'unknown')
                    severity_emoji = {
                        'critical': '🔴',
                        'major': '🟠',
                        'moderate': '🟡',
                        'minor': '🟢'
                    }.get(severity, '⚪')

                    with st.expander(f"{severity_emoji} #{idx}: {blocker.get('blocker_name', 'Unknown')} - {blocker.get('qualification_gap', '')}", expanded=(idx == 1)):
                        st.markdown(f"**Category:** {blocker.get('category', 'N/A')}")
                        st.markdown(f"**Impact:** {blocker.get('impact_on_success', 0)}/10")
                        st.markdown(f"**Addressable:** {'✅ Yes' if blocker.get('is_addressable') else '❌ No'}")

                        # Get improvement suggestions
                        improvements = connector.get_improvement_suggestions(blocker)
                        if improvements:
                            st.subheader("💡 Improvement Strategies")
                            for imp in improvements[:3]:  # Show top 3
                                st.info(f"**{imp.get('strategy_type', 'Strategy')}:** {imp.get('action_items', [''])[0]}")

                        # Get objection script
                        script = connector.generate_interview_script(blocker)
                        if script:
                            st.subheader("🎤 Interview Script")
                            st.markdown(f"**Opening:** {script.get('opening', 'N/A')}")
                            st.markdown(f"**Mitigation:** {script.get('mitigation', 'N/A')}")
            else:
                st.info("🎉 No blockers detected - strong match!")

# ========================================
# INTEGRATION CHECKLIST
# ========================================

st.header("✅ Integration Checklist")

checklist = {
    "Database Schema in init/": Path(__file__).parent.parent.parent / "admin_portal/db/init/04-application-blockers-schema.sql",
    "Blocker Connector Service": Path(__file__).parent.parent.parent / "shared_backend/services/blocker_connector.py",
    "User Portal Blocker Service": Path(__file__).parent.parent / "backend/services/blocker_service.py",
    "User Portal Blocker Detector": Path(__file__).parent.parent / "utilities/blocker_detector.py",
    "Mentor Blocker Integration": Path(__file__).parent.parent.parent / "mentor_portal/utilities/blocker_mentorship_integration.py"
}

for item, filepath in checklist.items():
    if filepath.exists():
        st.success(f"✅ {item}")
    else:
        st.error(f"❌ {item} - File not found: {filepath}")

# ========================================
# NEXT STEPS
# ========================================

st.header("🎯 Next Integration Steps")

st.info("""
**Remaining Integration Tasks:**

1. **Resume Upload Pages (13, 15):**
   - Add blocker detection after resume parsing
   - Show blocker summary in results

2. **UMarketU Job Matching (Page 10, 16, 24):**
   - Add blocker analysis to job comparisons
   - Show addressability scores

3. **Mentor AI Assistant (Page 08):**
   - Add 6th tab "🚫 Blocker Resolution"
   - Show mentee blocker tracking

4. **Admin Analytics:**
   - Add blocker statistics dashboard
   - Track resolution trends

5. **Database Initialization:**
   - Verify schema loads on startup
   - Test with real user data
""")

st.markdown("---")
st.caption("🧪 Test Page - Can be removed after integration verification")
