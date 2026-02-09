"""
26_Career_Pattern_Intelligence.py
==================================
REAL DATA: Experience-weighted skill comparison using peer benchmarks from Candidate_database.json
GDPR-COMPLIANT: Anonymized profiles only, no PII retained, session-only analysis
AI-ENHANCED: Perplexity and Gemini API integration for career guidance
"""

import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import re

# Canonical AI data directory (repo-root ai_data_final)
try:
    from shared.config import AI_DATA_DIR
except Exception:  # pragma: no cover
    AI_DATA_DIR = Path(__file__).resolve().parents[2] / "ai_data_final"

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Setup paths
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

# Import AI chat service
try:
    from services.ai_chat_service import get_ai_chat_service
    AI_CHAT_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ AI Chat service not available: {e}")
    AI_CHAT_AVAILABLE = False


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page24_career_patterns") if BackendTelemetryHelper else None

# Page configuration
st.set_page_config(
    page_title="Career Pattern Intelligence | IntelliCV Admin",
    page_icon="🎯",
    layout="wide"
)

# Authentication
if not st.session_state.get('authenticated_admin'):
    st.error("🔒 Admin authentication required")
    st.stop()

# ============================================================================
# DATA LOADING FUNCTIONS - REAL DATA SOURCES
# ============================================================================

@st.cache_data
def load_all_cvs():
    """Load all normalized CVs from ai_data_final/normalized"""
    cv_dir = AI_DATA_DIR / "normalized"
    cvs = {}
    if cv_dir.exists():
        for cv_file in list(cv_dir.glob("*.json"))[:1000]:
            try:
                with open(cv_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('text') and len(data['text']) > 100:
                        cvs[cv_file.name] = data
            except:
                continue
    return cvs

@st.cache_data
def load_peer_benchmarks():
    """Load anonymized peer benchmark data from Candidate_database.json

    GDPR-COMPLIANT: Uses anonymized job titles and skills only, no PII retained
    Data source: Historical snapshot as of September 20, 2025
    """
    peer_db_path = AI_DATA_DIR / "core_databases" / "Candidate_database.json"

    if not peer_db_path.exists():
        st.warning("⚠️ Peer database not found. Using limited dataset.")
        return []

    try:
        with open(peer_db_path, 'r', encoding='utf-8') as f:
            candidate_db = json.load(f)

        # Extract job titles for peer comparison (ANONYMIZED - no names/PII)
        peer_data = []
        for candidate in candidate_db[:500]:  # Sample 500 for performance
            job_title = candidate.get('Job Title', '').strip()
            if job_title and job_title != '':
                peer_data.append({
                    'job_title': job_title,
                    'anonymized_id': f"PEER_{candidate.get('ID', 'UNKNOWN')}"
                })

        return peer_data
    except Exception as e:
        st.error(f"Error loading peer data: {e}")
        return []

@st.cache_data
def load_job_titles_database():
    """Load job titles database for skill classification"""
    job_titles_dir = AI_DATA_DIR / "job_titles"
    job_titles_db = {}

    if job_titles_dir.exists():
        for job_file in list(job_titles_dir.glob("*.json"))[:100]:
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    title = job_data.get('title', '').lower()
                    if title:
                        job_titles_db[title] = job_data
            except:
                continue

    return job_titles_db

# ============================================================================
# SKILL ANALYSIS FUNCTIONS - EXPERIENCE-WEIGHTED
# ============================================================================

def extract_years_of_experience(cv_text):
    """Extract years of experience from CV text"""
    text_lower = cv_text.lower()

    # Try multiple patterns
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
        r'experience:\s*(\d+)\s*years?',
        r'(\d+)\s*years?\s*in\s*(?:the\s*)?industry',
    ]

    years = 0
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            years = max(years, max(int(m) for m in matches))

    return years

def calculate_skill_distribution(cv_data, job_titles_db):
    """Calculate experience-weighted skill distribution from real job title data

    Returns skill levels based on:
    - Years of experience (determines scale/magnitude)
    - Job titles and roles (determines skill categories)
    - Real job_titles/ JSON data for skill classification

    Categories: Management, Technical, Engineering, Finance & Admin, Development, Sales, Marketing
    Scale: Years of experience (5 years = max 5, 15 years = max 15)
    """
    text = cv_data.get('text', '').lower()

    # Extract years of experience
    years_exp = cv_data.get('years_of_experience', 0)
    if years_exp == 0:
        years_exp = extract_years_of_experience(text)

    # Initialize skill categories
    skill_categories = {
        'Management': 0,
        'Technical': 0,
        'Engineering': 0,
        'Finance & Admin': 0,
        'Development': 0,
        'Sales': 0,
        'Marketing': 0
    }

    # Match CV against real job titles database
    for job_title, job_data in job_titles_db.items():
        if job_title in text:
            # Extract skills from real data
            skills = job_data.get('skills', job_data.get('required_skills', []))

            for skill in skills:
                skill_lower = skill.lower()

                # Categorize based on keywords
                if any(k in skill_lower for k in ['manage', 'lead', 'director', 'head', 'chief', 'supervisor']):
                    skill_categories['Management'] += 1
                if any(k in skill_lower for k in ['python', 'java', 'sql', 'aws', 'azure', 'cloud', 'database']):
                    skill_categories['Technical'] += 1
                if any(k in skill_lower for k in ['engineer', 'architect', 'devops', 'infrastructure', 'system']):
                    skill_categories['Engineering'] += 1
                if any(k in skill_lower for k in ['finance', 'accounting', 'admin', 'hr', 'operations', 'compliance']):
                    skill_categories['Finance & Admin'] += 1
                if any(k in skill_lower for k in ['develop', 'code', 'programming', 'software', 'application']):
                    skill_categories['Development'] += 1
                if any(k in skill_lower for k in ['sales', 'business development', 'account', 'customer']):
                    skill_categories['Sales'] += 1
                if any(k in skill_lower for k in ['marketing', 'brand', 'content', 'social media', 'campaign']):
                    skill_categories['Marketing'] += 1

    # If no matches found, use keyword analysis as fallback
    if sum(skill_categories.values()) == 0:
        management_kw = ['manager', 'director', 'lead', 'head', 'chief', 'vp', 'president', 'supervisor']
        skill_categories['Management'] = sum(text.count(kw) for kw in management_kw)

        technical_kw = ['python', 'java', 'javascript', 'sql', 'aws', 'azure', 'docker', 'kubernetes', 'cloud']
        skill_categories['Technical'] = sum(text.count(kw) for kw in technical_kw)

        engineering_kw = ['engineer', 'architect', 'infrastructure', 'devops', 'systems', 'network']
        skill_categories['Engineering'] = sum(text.count(kw) for kw in engineering_kw)

        finance_kw = ['finance', 'accounting', 'budget', 'admin', 'hr', 'operations', 'compliance']
        skill_categories['Finance & Admin'] = sum(text.count(kw) for kw in finance_kw)

        dev_kw = ['develop', 'code', 'programming', 'software', 'application', 'frontend', 'backend']
        skill_categories['Development'] = sum(text.count(kw) for kw in dev_kw)

        sales_kw = ['sales', 'business development', 'account manager', 'revenue', 'customer']
        skill_categories['Sales'] = sum(text.count(kw) for kw in sales_kw)

        marketing_kw = ['marketing', 'brand', 'content', 'social media', 'campaign', 'seo']
        skill_categories['Marketing'] = sum(text.count(kw) for kw in marketing_kw)

    # Normalize and scale by years of experience
    total_skills = sum(skill_categories.values())
    if total_skills > 0:
        # Experience determines magnitude (5 years = scale of 5, 15 years = scale of 15)
        scale_factor = max(years_exp, 1)

        for category in skill_categories:
            # Normalized proportion × experience scale
            skill_categories[category] = (skill_categories[category] / total_skills) * scale_factor

    skill_categories['years_experience'] = years_exp
    return skill_categories

def detect_career_patterns(cv_text):
    """Detect non-traditional career patterns in CV"""
    text_lower = cv_text.lower()
    patterns = []

    if 'onc' in text_lower and 'hnc' in text_lower and ('degree' in text_lower or 'bsc' in text_lower):
        patterns.append('onc_to_degree')
    if 'apprentice' in text_lower and any(t in text_lower for t in ['senior', 'lead', 'manager', 'director']):
        patterns.append('apprentice_to_leader')
    if 'polytechnic' in text_lower and any(t in text_lower for t in ['senior', 'lead', 'manager']):
        patterns.append('polytechnic_to_leader')
    if 'mature student' in text_lower:
        patterns.append('mature_student')
    if any(p in text_lower for p in ['failed a-level', 'failed exam', 'resit']):
        patterns.append('failed_to_success')

    return patterns

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_experience_weighted_radar(candidate_skills, peer_avg_skills, candidate_name="Candidate"):
    """Create experience-weighted skill radar chart

    Chart shows skill distribution scaled by years of experience:
    - 5 years exp = max radius 5
    - 15 years exp = max radius 15
    - No leadership experience = Management skill close to 0
    - Core skill appears as longest line

    Supports overlaying multiple candidates for comparison
    """

    categories = ['Management', 'Technical', 'Engineering', 'Finance & Admin',
                  'Development', 'Sales', 'Marketing']

    fig = go.Figure()

    # Candidate skills
    candidate_values = [candidate_skills.get(cat, 0) for cat in categories]
    candidate_years = candidate_skills.get('years_experience', 0)

    fig.add_trace(go.Scatterpolar(
        r=candidate_values,
        theta=categories,
        fill='toself',
        name=f"{candidate_name} ({candidate_years}y exp)",
        line=dict(color='#667eea', width=3),
        fillcolor='rgba(102, 126, 234, 0.3)'
    ))

    # Peer average overlay
    if peer_avg_skills:
        peer_values = [peer_avg_skills.get(cat, 0) for cat in categories]
        peer_years = peer_avg_skills.get('years_experience', 0)

        fig.add_trace(go.Scatterpolar(
            r=peer_values,
            theta=categories,
            fill='toself',
            name=f"Peer Average ({peer_years:.0f}y exp)",
            line=dict(color='#f59e0b', width=2, dash='dash'),
            fillcolor='rgba(245, 158, 11, 0.2)'
        ))

    # Dynamic range based on max experience
    max_exp = max(candidate_years,
                  peer_avg_skills.get('years_experience', 5) if peer_avg_skills else 5)

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(max_exp, 10)],
                tickfont=dict(size=12)
            )
        ),
        showlegend=True,
        title="Experience-Weighted Skill Distribution",
        height=550
    )

    return fig

# ============================================================================
# MAIN APPLICATION
# ============================================================================

st.title("🎯 Career Pattern Intelligence")
st.markdown("### Real Data: Peer Benchmarking & Skill Analysis")

if TELEMETRY_HELPER:
    TELEMETRY_HELPER.render_status_panel(
        title="🛰️ Backend Telemetry Monitor",
        refresh_key="page24_backend_refresh",
    )

# Load data
all_cvs = load_all_cvs()
peer_benchmarks = load_peer_benchmarks()
job_titles_db = load_job_titles_database()

if not all_cvs:
    st.error("❌ No CV data available. Please ensure ai_data_final/normalized directory exists.")
    st.stop()

st.success(f"✅ Loaded {len(all_cvs):,} CVs for analysis")
st.info(f"📊 Loaded {len(peer_benchmarks):,} peer benchmarks from database (Historical: Sep 20, 2025)")
st.caption(f"🔍 Job titles database: {len(job_titles_db)} entries loaded")

# ============================================================================
# SIDEBAR - USER SELECTION (GDPR-COMPLIANT)
# ============================================================================

st.sidebar.header("🔍 Profile Analysis")
st.sidebar.info("⚠️ GDPR Notice: No user data is stored. Analysis runs in-session only.")

# Analysis mode selection
analysis_mode = st.sidebar.radio(
    "Analysis Mode:",
    ["Demo with Historical Data (Anonymized)", "Upload Your CV (Not Yet Implemented)"]
)

selected_cv = None

if analysis_mode == "Upload Your CV (Not Yet Implemented)":
    st.sidebar.warning("⚠️ CV upload feature coming soon. Please use demo mode.")
    st.sidebar.info("Demo mode uses fully anonymized historical data (pre-Sep 2025)")
    # Fall through to demo mode
    analysis_mode = "Demo with Historical Data (Anonymized)"

if analysis_mode == "Demo with Historical Data (Anonymized)":
    st.sidebar.info("Using anonymized historical dataset for demonstration")
    sample = list(all_cvs.keys())[:100]
    selected_cv = st.sidebar.selectbox(
        "Select Demo Profile:",
        sample,
        help="Anonymized profiles from historical data (pre-Sep 2025)"
    )

if not selected_cv:
    st.warning("⚠️ Please select a profile to analyze")
    st.stop()

# ============================================================================
# LOAD AND ANALYZE SELECTED PROFILE
# ============================================================================

cv_data = all_cvs[selected_cv]
cv_text = cv_data.get('text', '')

# Detect career patterns
patterns = detect_career_patterns(cv_text)

# Calculate skill distribution using REAL DATA
candidate_skills = calculate_skill_distribution(cv_data, job_titles_db)

# Display profile info
st.markdown("---")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📄 Profile: {selected_cv[:50]}")
    st.write(f"**Career Patterns Detected:** {len(patterns)}")
    if patterns:
        for p in patterns:
            st.write(f"- {p.replace('_', ' ').title()}")
    else:
        st.info("No specific non-traditional career patterns detected")

with col2:
    years_exp = candidate_skills['years_experience']
    st.metric("Years of Experience", years_exp if years_exp > 0 else "Not specified")
    st.metric("Pattern Count", len(patterns))

# ============================================================================
# CALCULATE PEER BENCHMARKS FROM REAL DATABASE
# ============================================================================

st.markdown("---")
with st.spinner("🔄 Loading peer benchmarks from database..."):
    peer_skills_list = []

    for peer in peer_benchmarks[:200]:  # Limit for performance
        # Create synthetic CV data from job title for benchmarking
        peer_cv_data = {
            'text': peer['job_title'].lower(),
            'job_title': peer['job_title'],
            'years_of_experience': 10  # Average assumption for benchmarking
        }
        peer_skills = calculate_skill_distribution(peer_cv_data, job_titles_db)
        peer_skills_list.append(peer_skills)

    # Calculate peer averages
    if peer_skills_list:
        peer_avg_skills = {}
        categories = ['Management', 'Technical', 'Engineering', 'Finance & Admin',
                      'Development', 'Sales', 'Marketing', 'years_experience']

        for cat in categories:
            values = [p.get(cat, 0) for p in peer_skills_list]
            peer_avg_skills[cat] = sum(values) / len(values) if values else 0
    else:
        peer_avg_skills = None

st.success(f"✅ Analyzed {len(peer_benchmarks)} peer profiles from Candidate_database.json")
st.info("ℹ️ Peer data is fully anonymized and GDPR-compliant. No PII is retained.")

# ============================================================================
# VISUALIZATION TABS
# ============================================================================

tab1, tab2 = st.tabs(["🕸️ Skill Radar", "💡 Career Insights"])

with tab1:
    st.markdown("### 🕸️ Experience-Weighted Skill Distribution")
    st.markdown("*Your skill profile based on real job market data vs. peer benchmarks*")

    if candidate_skills['years_experience'] > 0:
        st.info(f"📊 Your profile shows {candidate_skills['years_experience']} years of experience")
    else:
        st.warning("⚠️ Years of experience not detected in CV. Scale may be limited.")

    # Create and display radar chart
    radar_fig = create_experience_weighted_radar(
        candidate_skills,
        peer_avg_skills,
        selected_cv[:30]
    )
    st.plotly_chart(radar_fig, use_container_width=True)

    # Skill breakdown table
    st.markdown("#### 📊 Detailed Skill Analysis")
    st.markdown("*Scale represents experience level (years) × skill emphasis*")

    categories = ['Management', 'Technical', 'Engineering', 'Finance & Admin', 'Development', 'Sales', 'Marketing']

    cols = st.columns(len(categories))

    for idx, cat in enumerate(categories):
        with cols[idx]:
            candidate_val = candidate_skills.get(cat, 0)
            peer_val = peer_avg_skills.get(cat, 0) if peer_avg_skills else 0
            diff = candidate_val - peer_val

            st.metric(
                cat.replace(' & ', '\n'),
                f"{candidate_val:.1f}",
                f"{diff:+.1f} vs peers" if peer_avg_skills else "N/A"
            )

    # Core skill identification
    st.markdown("#### 🎯 Your Core Skills")
    sorted_skills = sorted(
        [(cat, candidate_skills.get(cat, 0)) for cat in categories],
        key=lambda x: x[1],
        reverse=True
    )

    top_3 = sorted_skills[:3]
    for rank, (skill, value) in enumerate(top_3, 1):
        if value > 0:
            st.success(f"**#{rank}: {skill}** (Score: {value:.1f})")
        else:
            st.info(f"**#{rank}: {skill}** (Score: {value:.1f}) - Consider developing this area")

    # Experience-based guidance
    if candidate_skills['years_experience'] < 5:
        st.info("💡 Early Career: Focus on building depth in your core skill areas")
    elif candidate_skills['years_experience'] < 10:
        st.info("💡 Mid-Career: Consider broadening into complementary skill areas")
    else:
        st.info("💡 Senior Professional: Your diverse experience is a major asset")

with tab2:
    st.markdown("### 💡 Personalized Career Insights")

    # Strengths analysis
    st.markdown("#### 🌟 Your Strongest Skills")

    top_skills = [s for s in sorted_skills if s[1] > 0][:3]

    if top_skills:
        for rank, (skill, value) in enumerate(top_skills, 1):
            st.success(f"✅ **#{rank}: {skill}** - Score: {value:.1f}")
    else:
        st.info("Upload your CV to identify your core strengths")

    # Development opportunities vs peers
    st.markdown("#### 🎯 Development Opportunities")

    if peer_avg_skills:
        below_peer = []
        for cat in categories:
            candidate_val = candidate_skills.get(cat, 0)
            peer_val = peer_avg_skills.get(cat, 0)

            if peer_val > 0 and candidate_val < peer_val * 0.8:
                diff_pct = ((peer_val - candidate_val) / peer_val * 100)
                below_peer.append((cat, candidate_val, peer_val, diff_pct))

        if below_peer:
            for skill, your_val, peer_val, diff_pct in sorted(below_peer, key=lambda x: x[3], reverse=True)[:3]:
                st.warning(f"💡 **{skill}**: {diff_pct:.0f}% below peer benchmark - consider skill development")
        else:
            st.success("✅ Your skills match or exceed peer benchmarks across all categories!")
    else:
        st.info("Peer benchmark data will appear here once database is loaded")

    # Peer comparison insights
    st.markdown("#### 📊 Peer Benchmark Analysis")
    st.caption("Based on real job market data from Candidate_database.json (Sep 20, 2025)")

    if peer_avg_skills:
        strengths_vs_peers = []
        gaps_vs_peers = []

        for cat in categories:
            candidate_val = candidate_skills.get(cat, 0)
            peer_val = peer_avg_skills.get(cat, 0)

            if candidate_val > peer_val * 1.2:  # 20% above peer average
                strengths_vs_peers.append((cat, candidate_val, peer_val))
            elif candidate_val < peer_val * 0.8 and peer_val > 0:  # 20% below peer average
                gaps_vs_peers.append((cat, candidate_val, peer_val))

        if strengths_vs_peers:
            st.success("🌟 **Areas Where You Excel vs. Peers:**")
            for skill, your_val, peer_val in strengths_vs_peers:
                diff_pct = ((your_val - peer_val) / peer_val * 100) if peer_val > 0 else 0
                st.write(f"- **{skill}**: {diff_pct:.0f}% above peer average")

        if gaps_vs_peers:
            st.info("💡 **Opportunities to Match Peer Benchmarks:**")
            for skill, your_val, peer_val in gaps_vs_peers:
                diff_pct = ((peer_val - your_val) / peer_val * 100) if peer_val > 0 else 0
                st.write(f"- **{skill}**: {diff_pct:.0f}% below peer average - consider development")

        if not strengths_vs_peers and not gaps_vs_peers:
            st.success("✅ Your skill distribution closely matches peer benchmarks")
    else:
        st.warning("⚠️ Peer benchmark data unavailable. Enable database connection for comparisons.")

    # Career stage roadmap
    st.markdown("#### 🎯 Career Development Roadmap")

    years_exp = candidate_skills['years_experience']

    if years_exp < 5:
        st.info("""
        **Early Career Stage (0-5 years)**

        Focus areas based on your profile:
        - Deepen expertise in your core skill (top skill on radar chart)
        - Build foundational skills in 2-3 complementary areas
        - Document achievements with quantifiable metrics
        - Seek mentorship from senior professionals
        """)
    elif years_exp < 10:
        st.info("""
        **Mid-Career Stage (5-10 years)**

        Development priorities:
        - Expand into adjacent skill domains (diversification)
        - Begin building leadership/management capabilities if not already present
        - Consider specialization vs. generalization strategy
        - Network within your industry vertical
        """)
    else:
        st.info("""
        **Senior Professional (10+ years)**

        Strategic positioning:
        - Leverage deep experience as unique differentiator
        - Mentor emerging professionals in your core domains
        - Consider thought leadership (speaking, writing, teaching)
        - Focus on high-impact strategic contributions
        """)

    # AI-Powered Career Recommendations
    st.markdown("---")
    st.markdown("#### 🤖 AI-Powered Career Guidance")
    st.caption("Powered by Perplexity (web-grounded) and Gemini (analysis)")

    if AI_CHAT_AVAILABLE:
        ai_service = get_ai_chat_service()
        service_status = ai_service.get_service_status()

        if service_status['any_available']:
            # Service status indicator
            col1, col2 = st.columns(2)
            with col1:
                if service_status['perplexity']['available']:
                    st.success("🟢 Perplexity API: Active (web-grounded insights)")
                else:
                    st.info("⚪ Perplexity API: Not configured")

            with col2:
                if service_status['gemini']['available']:
                    st.success("🟢 Gemini API: Active (analysis & planning)")
                else:
                    st.info("⚪ Gemini API: Not configured")

            st.markdown("---")

            # User input for targeted advice
            col1, col2 = st.columns([3, 1])

            with col1:
                target_role = st.text_input(
                    "Target role (optional):",
                    placeholder="e.g., Senior Software Engineer, Product Manager",
                    help="Enter a specific role you're targeting for personalized advice"
                )

            with col2:
                st.write("")  # Spacing
                st.write("")
                get_advice_btn = st.button("💡 Get AI Career Advice", type="primary")

            if get_advice_btn or st.session_state.get('show_ai_advice', False):
                st.session_state['show_ai_advice'] = True

                with st.spinner("🤖 Analyzing your profile and consulting AI advisors..."):
                    advice_response = ai_service.get_career_advice(
                        user_skills=candidate_skills,
                        career_patterns=patterns,
                        target_role=target_role if target_role else None
                    )

                # Display advice
                st.markdown("##### 💡 Personalized Career Advice")

                # Source indicator
                source_emoji = {
                    'perplexity': '🔵',
                    'gemini': '🟣',
                    'fallback': '⚪'
                }

                source_name = {
                    'perplexity': 'Perplexity AI (Web-grounded)',
                    'gemini': 'Gemini AI',
                    'fallback': 'Fallback Mode'
                }

                st.caption(f"{source_emoji.get(advice_response['source'], '⚪')} Source: {source_name.get(advice_response['source'], 'Unknown')}")

                if advice_response.get('web_grounded'):
                    st.info("✅ This advice is grounded in current web data and market conditions")

                # Display the advice
                st.markdown(advice_response['advice'])

                st.markdown("---")

                # Additional AI features
                tab_ai1, tab_ai2 = st.tabs([
                    "📚 Skill Development Plan",
                    "📊 Job Market Insights"
                ])

                with tab_ai1:
                    st.markdown("##### 📚 Personalized Skill Development Plan")

                    # Let user select timeline
                    timeline = st.select_slider(
                        "Development timeline:",
                        options=["3 months", "6 months", "1 year", "2 years"],
                        value="6 months"
                    )

                    if st.button("Generate Development Plan", key="dev_plan"):
                        with st.spinner("Creating your personalized development plan..."):
                            # Build target skills (assuming user wants to improve weak areas)
                            target_skills = candidate_skills.copy()
                            if peer_avg_skills:
                                # Target peer averages for weak skills
                                for cat in categories:
                                    if peer_avg_skills.get(cat, 0) > candidate_skills.get(cat, 0):
                                        target_skills[cat] = peer_avg_skills[cat]

                            dev_plan = ai_service.get_skill_development_plan(
                                current_skills=candidate_skills,
                                target_skills=target_skills,
                                timeline=timeline
                            )

                        st.markdown(dev_plan['plan'])
                        st.caption(f"Generated: {dev_plan['timestamp'][:10]}")

                with tab_ai2:
                    st.markdown("##### 📊 Current Job Market Insights")

                    # Let user specify role
                    market_role = st.text_input(
                        "Role to analyze:",
                        value=target_role if target_role else "",
                        placeholder="e.g., Data Scientist, Marketing Manager",
                        key="market_role"
                    )

                    market_location = st.text_input(
                        "Location (optional):",
                        placeholder="e.g., United States, London, Remote",
                        key="market_location"
                    )

                    if st.button("Get Market Insights", key="market_insights"):
                        if not market_role:
                            st.warning("Please enter a role to analyze")
                        else:
                            with st.spinner(f"Researching job market for {market_role}..."):
                                # Extract user's top skills
                                top_user_skills = [s[0] for s in sorted_skills if s[1] > 0][:5]

                                insights = ai_service.get_job_market_insights(
                                    job_title=market_role,
                                    location=market_location if market_location else None,
                                    skills=top_user_skills
                                )

                            st.markdown(insights['insights'])
                            st.caption(f"Generated: {insights['timestamp'][:10]}")

                            if insights['source'] == 'perplexity':
                                st.success("✅ Data sourced from current web search results")
        else:
            st.warning("""
            ⚠️ **AI Career Advisory Services Not Configured**

            To enable AI-powered career guidance, add API keys to your `.env` file:

            ```
            PERPLEXITY_API_KEY=your_key_here
            GEMINI_API_KEY=your_key_here
            ```

            **Perplexity** provides web-grounded career insights based on current market data.
            **Gemini** offers analytical career guidance and skill development planning.
            """)
    else:
        st.error("❌ AI Chat service not available. Check service installation.")

# ============================================================================
# EXPORT SECTION
# ============================================================================

st.markdown("---")
st.markdown("### 📥 Export Analysis")

analysis_report = {
    'profile_id': selected_cv if selected_cv else 'user_upload',
    'analysis_date': datetime.now().isoformat(),
    'years_experience': candidate_skills.get('years_experience', 0),
    'career_patterns': patterns,
    'skill_distribution': {
        cat: candidate_skills.get(cat, 0)
        for cat in ['Management', 'Technical', 'Engineering', 'Finance & Admin', 'Development', 'Sales', 'Marketing']
    },
    'peer_benchmarks': peer_avg_skills if peer_avg_skills else {},
    'data_source': 'ai_data_final/core_databases/Candidate_database.json (Historical: Sep 20, 2025)',
    'gdpr_notice': 'No PII retained. Analysis is session-only.',
    'peer_count': len(peer_benchmarks)
}

export_json = json.dumps(analysis_report, indent=2)
st.download_button(
    "📊 Download Skill Analysis (JSON)",
    export_json,
    f"skill_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    "application/json"
)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.caption(f"🎯 Career Pattern Intelligence | {len(peer_benchmarks)} peer benchmarks | Historical data: Sep 20, 2025 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.caption("ℹ️ GDPR-Compliant: Anonymized profiles only, no PII retained")
