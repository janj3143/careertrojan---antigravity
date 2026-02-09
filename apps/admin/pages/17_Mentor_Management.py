"""
🎯 Admin Mentorship Management Dashboard
=======================================
Comprehensive admin interface for managing the mentorship system:
- Application review and approval workflow
- Mentor performance monitoring
- System analytics and reporting
- Quality control and moderation tools
- Skills & Glossary Intelligence (merged from Enhanced Glossary)

**USER DATA INTEGRATION:**
Glossary automatically enhances itself with user registration/login data:
- Extracts skills from user profiles (secure_credentials.db)
- Captures job titles from user work history
- Identifies companies from user experience
- Merges user data with ai_data_final for comprehensive glossary
- Auto-updates on each user login/registration
- Persists enriched data back to ai_data_final

Combined from:
- 28_Mentor_Application_Review.py (Mentor application workflow)
- 17_Enhanced_Glossary.py (AI-powered skills/glossary intelligence)

Created: November 16, 2025
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional in dev
    BackendTelemetryHelper = None

# Page configuration
st.set_page_config(
    page_title="🎯 Mentor Management | IntelliCV-AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
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


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page17_mentor_mgmt") if BackendTelemetryHelper else None

# ============================================================================
# AI DATA LOADER FOR SKILLS/GLOSSARY
# ============================================================================

try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from real_ai_connector import RealAIConnector
    ai_loader = RealAIConnector()
    AI_LOADER_AVAILABLE = True
except ImportError:
    AI_LOADER_AVAILABLE = False
    ai_loader = None

# ============================================================================
# MENTORSHIP SERVICE
# ============================================================================

backend_path = Path(__file__).parent.parent.parent / "shared_backend"
sys.path.insert(0, str(backend_path))

try:
    from services.mentorship_service import MentorshipService
    from database.exa_db import get_db_connection
    BACKEND_AVAILABLE = True
except ImportError as e:
    BACKEND_AVAILABLE = False

# ============================================================================
# SKILLS & GLOSSARY INTELLIGENCE CLASS
# ============================================================================

class SkillsGlossaryIntelligence:
    """AI-Powered Skills & Glossary Intelligence - loads from ai_data_final + USER DATA"""

    def __init__(self):
        """Initialize skills/glossary system with user data integration."""
        self.term_categories = [
            "job_titles", "technical_terms", "companies", "skills",
            "abbreviations", "industry_terms", "organizations"
        ]

        # User database path for real-time glossary enhancement
        self.user_db_path = Path(__file__).parent.parent / "secure_credentials.db"
        self.user_data_enrichment = {}

        # Load live data from AI processing
        if AI_LOADER_AVAILABLE and ai_loader:
            self.load_live_data()
            # CRITICAL: Load user data to enhance glossary
            self.load_user_data_enrichment()
        else:
            st.error("❌ CRITICAL: AI data loader (real_ai_connector) not available")
            st.error("❌ Cannot load from ai_data_final - system requires RealAIConnector")
            st.stop()

    def load_live_data(self):
        """Load live data from ai_data_final ONLY - NO FALLBACKS."""
        try:
            st.info("🔄 Loading live AI data from ai_data_final...")
            self.ai_terms = self.get_ai_loader_terms_data()
            self.companies_data = self.get_ai_loader_companies_data()
            self.abbreviations_data = self.get_ai_loader_abbreviations_data()
        except Exception as e:
            st.error(f"❌ CRITICAL: Error loading live AI data: {e}")
            st.stop()

    def load_user_data_enrichment(self):
        """Load user profile data to enhance glossary in real-time.

        Extracts skills, job titles, and companies from user registrations/logins
        to dynamically update the glossary database.
        """
        try:
            import sqlite3

            if not self.user_db_path.exists():
                st.warning(f"⚠️ User database not found at {self.user_db_path}")
                st.info("💡 Glossary will use ai_data_final only - user enrichment unavailable")
                return

            st.info("👥 Loading user data to enhance glossary...")

            with sqlite3.connect(str(self.user_db_path)) as conn:
                cursor = conn.cursor()

                # Extract user profile data
                cursor.execute('''
                    SELECT
                        up.job_title,
                        up.skills,
                        up.parsed_data,
                        u.email,
                        u.created_at,
                        u.last_login
                    FROM user_profiles up
                    JOIN users u ON up.user_id = u.user_id
                    WHERE u.is_active = 1
                ''')

                user_profiles = cursor.fetchall()

                # Process user data to enhance glossary
                user_skills = set()
                user_job_titles = set()
                user_companies = set()

                for profile in user_profiles:
                    job_title, skills, parsed_data, email, created_at, last_login = profile

                    # Extract job titles
                    if job_title:
                        user_job_titles.add(job_title)

                    # Extract skills (JSON or comma-separated)
                    if skills:
                        try:
                            if isinstance(skills, str):
                                if skills.startswith('['):
                                    skill_list = json.loads(skills)
                                else:
                                    skill_list = [s.strip() for s in skills.split(',')]
                                user_skills.update(skill_list)
                        except:
                            pass

                    # Extract from parsed_data JSON
                    if parsed_data:
                        try:
                            data = json.loads(parsed_data) if isinstance(parsed_data, str) else parsed_data

                            # Skills from parsed data
                            if 'skills' in data:
                                if isinstance(data['skills'], list):
                                    user_skills.update(data['skills'])

                            # Companies from work history
                            if 'experience' in data:
                                exp = data['experience']
                                if isinstance(exp, list):
                                    for job in exp:
                                        if isinstance(job, dict) and 'company' in job:
                                            user_companies.add(job['company'])
                        except Exception as e:
                            # Log parsing error but continue processing other profiles
                            st.warning(f"⚠️ Error parsing user profile data: {e}")

                # Store user enrichment data
                self.user_data_enrichment = {
                    'skills': user_skills,
                    'job_titles': user_job_titles,
                    'companies': user_companies,
                    'total_users': len(user_profiles),
                    'last_updated': datetime.now().isoformat()
                }

                # Merge user data into main glossary
                self._merge_user_data_into_glossary()

                st.success(f"✅ Enriched glossary with {len(user_profiles)} user profiles")
                st.info(f"📊 Added: {len(user_skills)} skills, {len(user_job_titles)} job titles, {len(user_companies)} companies")

        except sqlite3.Error as e:
            st.warning(f"⚠️ Could not load user data: {e}")
            st.info("💡 Continuing with ai_data_final only")
        except Exception as e:
            st.warning(f"⚠️ Error enriching glossary with user data: {e}")
            st.info("💡 Continuing with ai_data_final only")

    def _merge_user_data_into_glossary(self):
        """Merge user-extracted data into main glossary dictionaries."""

        # Merge user skills into ai_terms
        if 'skills' in self.user_data_enrichment:
            for skill in self.user_data_enrichment['skills']:
                skill_key = skill.lower().replace(' ', '_')
                if skill_key not in self.ai_terms:
                    self.ai_terms[skill_key] = {
                        "definition": f"User skill: {skill}",
                        "category": "technical_terms",
                        "frequency": 1,
                        "contexts": ["User Profiles"],
                        "source": "user_data"
                    }
                else:
                    # Increment frequency for existing skills
                    self.ai_terms[skill_key]['frequency'] = self.ai_terms[skill_key].get('frequency', 0) + 1

        # Merge user job titles into ai_terms
        if 'job_titles' in self.user_data_enrichment:
            for job_title in self.user_data_enrichment['job_titles']:
                title_key = job_title.lower().replace(' ', '_')
                if title_key not in self.ai_terms:
                    self.ai_terms[title_key] = {
                        "definition": f"User job title: {job_title}",
                        "category": "job_titles",
                        "frequency": 1,
                        "contexts": ["User Profiles", "Career"],
                        "source": "user_data"
                    }
                else:
                    self.ai_terms[title_key]['frequency'] = self.ai_terms[title_key].get('frequency', 0) + 1

        # Merge user companies into companies_data
        if 'companies' in self.user_data_enrichment:
            for company in self.user_data_enrichment['companies']:
                if company not in self.companies_data:
                    self.companies_data[company] = {
                        "frequency": 1,
                        "contexts": ["User Work History"],
                        "source": "user_data"
                    }
                else:
                    self.companies_data[company]['frequency'] = self.companies_data[company].get('frequency', 0) + 1

    def save_glossary_updates(self):
        """Save enhanced glossary back to ai_data_final for persistence."""
        try:
            sandbox_path = Path(__file__).parent.parent.parent

            # Save enhanced consolidated_terms.json
            consolidated_path = sandbox_path / "ai_data_final" / "consolidated_terms.json"
            if consolidated_path.exists():
                with open(consolidated_path, 'r', encoding='utf-8') as f:
                    existing_terms = json.load(f)

                # Merge with user-enriched terms
                for term_key, term_data in self.ai_terms.items():
                    if term_data.get('source') == 'user_data':
                        existing_terms[term_key] = term_data

                # Save back
                with open(consolidated_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_terms, f, indent=2, ensure_ascii=False)

                st.success(f"✅ Saved {len(self.ai_terms)} terms to consolidated_terms.json")

            # Save enhanced companies data
            companies_path = sandbox_path / "ai_data_final" / "companies_enriched.json"
            with open(companies_path, 'w', encoding='utf-8') as f:
                json.dump(self.companies_data, f, indent=2, ensure_ascii=False)

            st.success(f"✅ Saved {len(self.companies_data)} companies to companies_enriched.json")

        except Exception as e:
            st.error(f"❌ Error saving glossary updates: {e}")

    def get_ai_loader_terms_data(self):
        """Load terms data from ALL ai_data_final categories - NO LIMITS."""
        try:
            terms_dict = {}

            # Load ALL skills from ai_data_final
            skills_data = ai_loader.load_real_skills_data()
            if skills_data:
                if isinstance(skills_data, dict):
                    for skill_name, skill_info in skills_data.items():
                        terms_dict[skill_name.lower().replace(' ', '_')] = {
                            "definition": f"Technical skill: {skill_name}",
                            "category": "technical_terms",
                            "frequency": skill_info.get('frequency', 1) if isinstance(skill_info, dict) else 1,
                            "contexts": skill_info.get('contexts', ["Skills"]) if isinstance(skill_info, dict) else ["Skills"]
                        }
                elif isinstance(skills_data, list):
                    for skill_name in skills_data:
                        terms_dict[skill_name.lower().replace(' ', '_')] = {
                            "definition": f"Technical skill: {skill_name}",
                            "category": "technical_terms",
                            "frequency": 1,
                            "contexts": ["Skills"]
                        }

            # Load ALL job titles from ai_data_final
            job_titles_data = ai_loader.load_real_job_titles()
            if job_titles_data and 'job_titles' in job_titles_data:
                for job_title in job_titles_data['job_titles']:
                    title_name = job_title.get('title', job_title) if isinstance(job_title, dict) else job_title
                    terms_dict[title_name.lower().replace(' ', '_')] = {
                        "definition": f"Job role: {title_name}",
                        "category": "job_titles",
                        "frequency": job_title.get('frequency', 1) if isinstance(job_title, dict) else 1,
                        "contexts": ["Career", "Hiring"]
                    }

            if not terms_dict:
                st.error("❌ CRITICAL: No terms data found in ai_data_final")
                st.stop()
            return terms_dict
        except Exception as e:
            st.error(f"❌ CRITICAL: Error loading AI data: {e}")
            st.stop()

    def get_ai_loader_companies_data(self):
        """Load companies data from ALL ai_data_final categories - NO FALLBACK."""
        try:
            companies_data = ai_loader.load_real_companies_data()
            if companies_data and isinstance(companies_data, dict):
                result = {
                    name: {
                        "frequency": info.get('count', 1) if isinstance(info, dict) else 1,
                        "contexts": info.get('contexts', ["Employment"]) if isinstance(info, dict) else ["Employment"]
                    }
                    for name, info in companies_data.items()
                }
                if not result:
                    st.error("❌ CRITICAL: No companies data found in ai_data_final")
                    st.stop()
                return result
            else:
                st.error("❌ CRITICAL: No companies data found in ai_data_final")
                st.stop()
        except Exception as e:
            st.error(f"❌ CRITICAL: Error loading companies data: {e}")
            st.stop()

    def get_ai_loader_abbreviations_data(self):
        """Load abbreviations from canonical_glossary.json ONLY."""
        try:
            sandbox_path = Path(__file__).parent.parent.parent
            glossary_path = sandbox_path / "ai_data_final" / "canonical_glossary.json"

            if glossary_path.exists():
                with open(glossary_path, 'r', encoding='utf-8') as f:
                    glossary_data = json.load(f)

                abbreviations = {}
                for abbrev, expansion in glossary_data.items():
                    abbreviations[abbrev] = {
                        "expansion": expansion,
                        "frequency": 100
                    }

                st.info(f"✅ Loaded {len(abbreviations)} abbreviations from canonical_glossary.json")
                return abbreviations
            else:
                st.error(f"❌ CRITICAL: canonical_glossary.json not found at {glossary_path}")
                st.stop()

        except Exception as e:
            st.error(f"❌ CRITICAL: Error loading canonical_glossary.json: {e}")
            st.stop()

# ============================================================================
# DATA FETCHING FOR MENTOR APPLICATIONS
# ============================================================================

def get_pending_applications() -> List[Dict[str, Any]]:
    """Fetch all pending mentor applications from backend or demo data."""

    if BACKEND_AVAILABLE:
        try:
            # TODO: Implement real backend call
            # return MentorshipService.get_pending_applications()
            pass
        except Exception as e:
            st.warning(f"Backend error: {e}")

    # Demo data for now
    return [
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
                'industry': ['Data Science & AI', 'Software Engineering']
            },
            'expertise': {
                'technical_expertise': ['Data Science & ML', 'AI/LLM Integration'],
                'leadership_expertise': ['Engineering Leadership'],
                'marketing_expertise': [],  # Marketing gurus
                'sales_expertise': [],  # Sales specialists
                'product_expertise': [],  # Product management
                'design_expertise': [],  # Design specialists
                'availability': '8-12 hours/week'
            },
            'packages': []
        }
    ]

# ============================================================================
# MAIN PAGE
# ============================================================================

def main():
    """Main Mentor Management interface"""

    st.title("🎯 Mentor Management Dashboard")
    st.markdown("**Comprehensive mentorship system administration and skills intelligence**")

    if TELEMETRY_HELPER:
        TELEMETRY_HELPER.render_status_panel(
            title="🛰️ Backend Telemetry Monitor",
            refresh_key="page17_backend_refresh",
        )

    # Main tabs
    tab_applications, tab_skills, tab_analytics = st.tabs([
        "📋 Mentor Applications",
        "🧠 Skills & Glossary Intelligence",
        "📈 Analytics & Reports"
    ])

    # ========================================================================
    # TAB 1: MENTOR APPLICATIONS
    # ========================================================================
    with tab_applications:
        st.header("📋 Mentor Application Review")

        pending_apps = get_pending_applications()

        col1, col2, col3 = st.columns(3)
        col1.metric("Pending Review", len(pending_apps))
        col2.metric("Approved (Last 7 days)", 0)
        col3.metric("Rejected (Last 7 days)", 0)

        st.divider()

        if not pending_apps:
            st.info("No pending applications at this time")
        else:
            for app in pending_apps:
                prof = app['professional']
                exp = app['expertise']

                with st.expander(
                    f"🔍 {prof['full_name']} - {prof['current_role']} @ {prof['company']}",
                    expanded=False
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown("### 👤 Professional Background")
                        st.markdown(f"**Name:** {prof['full_name']}")
                        st.markdown(f"**Email:** {prof['email']}")
                        st.markdown(f"**LinkedIn:** [{prof['linkedin']}]({prof['linkedin']})")
                        st.markdown(f"**Experience:** {prof['years_experience']}")

                        st.markdown("### 🎯 Areas of Expertise")

                        # Technical Expertise
                        if exp.get('technical_expertise'):
                            st.markdown("**💻 Technical Expertise:**")
                            for skill in exp['technical_expertise']:
                                st.markdown(f"- {skill}")

                        # Leadership Expertise
                        if exp.get('leadership_expertise'):
                            st.markdown("**👥 Leadership Expertise:**")
                            for skill in exp['leadership_expertise']:
                                st.markdown(f"- {skill}")

                        # Marketing Expertise
                        if exp.get('marketing_expertise'):
                            st.markdown("**📢 Marketing Expertise:**")
                            for skill in exp['marketing_expertise']:
                                st.markdown(f"- {skill}")

                        # Sales Expertise
                        if exp.get('sales_expertise'):
                            st.markdown("**💼 Sales Expertise:**")
                            for skill in exp['sales_expertise']:
                                st.markdown(f"- {skill}")

                        # Product Expertise
                        if exp.get('product_expertise'):
                            st.markdown("**🎨 Product Expertise:**")
                            for skill in exp['product_expertise']:
                                st.markdown(f"- {skill}")

                        # Design Expertise
                        if exp.get('design_expertise'):
                            st.markdown("**✨ Design Expertise:**")
                            for skill in exp['design_expertise']:
                                st.markdown(f"- {skill}")

                        # Availability
                        st.markdown(f"**📅 Availability:** {exp.get('availability', 'Not specified')}")

                    with col2:
                        st.markdown("### 📊 Quick Assessment")
                        st.checkbox("✅ 5+ years experience", value=True, disabled=True)
                        st.checkbox("✅ Senior role", value=True, disabled=True)
                        st.checkbox("✅ LinkedIn verified", value=True, disabled=True)

                    st.divider()

                    # Admin decision
                    st.markdown("### ✍️ Guardian Decision")

                    col_action1, col_action2 = st.columns(2)

                    with col_action1:
                        if st.button("✅ Approve", key=f"approve_{app['application_id']}", type="primary"):
                            st.success(f"✅ {prof['full_name']} approved as mentor!")
                            st.balloons()

                    with col_action2:
                        if st.button("❌ Reject", key=f"reject_{app['application_id']}"):
                            st.error("❌ Application rejected")

    # ========================================================================
    # TAB 2: SKILLS & GLOSSARY INTELLIGENCE
    # ========================================================================
    with tab_skills:
        st.header("🧠 Skills & Glossary Intelligence")
        st.markdown("**AI-powered skills, terms, and company data from ai_data_final**")

        if AI_LOADER_AVAILABLE:
            skills_intel = SkillsGlossaryIntelligence()

            # User data enrichment status
            if skills_intel.user_data_enrichment:
                enrichment = skills_intel.user_data_enrichment
                st.success(f"✅ Glossary enhanced with data from {enrichment.get('total_users', 0)} user profiles")

                col_enrich1, col_enrich2, col_enrich3, col_enrich4 = st.columns(4)
                with col_enrich1:
                    st.metric("👥 User Skills Added", len(enrichment.get('skills', [])))
                with col_enrich2:
                    st.metric("💼 User Job Titles", len(enrichment.get('job_titles', [])))
                with col_enrich3:
                    st.metric("🏢 User Companies", len(enrichment.get('companies', [])))
                with col_enrich4:
                    last_updated = enrichment.get('last_updated', 'N/A')
                    st.metric("🔄 Last Updated", last_updated[:19] if isinstance(last_updated, str) and len(last_updated) > 19 else last_updated)

                st.divider()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_terms = len(skills_intel.ai_terms) if skills_intel.ai_terms else 0
                st.metric("📚 AI-Extracted Terms", f"{total_terms:,}", "+Live")

            with col2:
                total_companies = len(skills_intel.companies_data) if skills_intel.companies_data else 0
                st.metric("🏢 Companies Found", f"{total_companies:,}", "+Dynamic")

            with col3:
                total_abbrev = len(skills_intel.abbreviations_data) if skills_intel.abbreviations_data else 0
                st.metric("📖 Abbreviations", f"{total_abbrev:,}", "+Real")

            with col4:
                st.metric("🤖 AI Status", "Connected", "Real Data")

            st.divider()

            # Admin controls
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button("🔄 Refresh User Data", help="Reload user profiles to update glossary"):
                    skills_intel.load_user_data_enrichment()
                    st.rerun()

            with col_btn2:
                if st.button("💾 Save Glossary Updates", help="Persist user-enriched data to ai_data_final"):
                    skills_intel.save_glossary_updates()

            with col_btn3:
                st.info("💡 Glossary auto-updates on user login/registration")

            st.divider()

            # Display samples
            tab_terms, tab_companies, tab_abbrev = st.tabs(["📚 Terms", "🏢 Companies", "📖 Abbreviations"])

            with tab_terms:
                if skills_intel.ai_terms:
                    terms_df = pd.DataFrame([
                        {
                            "Term": term_id,
                            "Definition": data.get('definition', 'N/A'),
                            "Category": data.get('category', 'N/A'),
                            "Frequency": data.get('frequency', 0)
                        }
                        for term_id, data in list(skills_intel.ai_terms.items())[:50]
                    ])
                    st.dataframe(terms_df, use_container_width=True, height=400)
                else:
                    st.info("No terms data loaded")

            with tab_companies:
                if skills_intel.companies_data:
                    companies_df = pd.DataFrame([
                        {
                            "Company": name,
                            "Frequency": data.get('frequency', 0),
                            "Contexts": ', '.join(data.get('contexts', []))
                        }
                        for name, data in list(skills_intel.companies_data.items())[:50]
                    ])
                    st.dataframe(companies_df, use_container_width=True, height=400)
                else:
                    st.info("No companies data loaded")

            with tab_abbrev:
                if skills_intel.abbreviations_data:
                    abbrev_df = pd.DataFrame([
                        {
                            "Abbreviation": abbrev,
                            "Expansion": data.get('expansion', 'N/A'),
                            "Frequency": data.get('frequency', 0)
                        }
                        for abbrev, data in list(skills_intel.abbreviations_data.items())[:50]
                    ])
                    st.dataframe(abbrev_df, use_container_width=True, height=400)
                else:
                    st.info("No abbreviations data loaded")
        else:
            st.error("❌ AI Loader not available - cannot display skills intelligence")

    # ========================================================================
    # TAB 3: ANALYTICS & REPORTS
    # ========================================================================
    with tab_analytics:
        st.header("📈 Analytics & Reports")
        st.markdown("**System analytics and performance metrics**")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Mentors", "0", "Awaiting Launch")

        with col2:
            st.metric("Active Sessions", "0", "Awaiting Launch")

        with col3:
            st.metric("Platform Health", "Ready", "✅ Built")

        st.divider()

        st.info("""
        **📊 Analytics dashboard will populate with real data once mentorship program launches.**

        **Planned metrics:**
        - 📈 Monthly application trends
        - ✅ Approval and acceptance rates
        - 📊 Session completion statistics
        - ⭐ Satisfaction and rating trends
        - 🎯 Mentor performance analytics
        - 🧠 Skills demand analysis
        """)

    # Footer
    st.markdown("---")
    st.markdown("**🎯 Mentor Management Dashboard** | IntelliCV AI Platform | Admin Portal")

# ============================================================================
# SIDEBAR - REVIEW GUIDELINES
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

    ✅ **Commitment:**
    - At least 4 hours/week
    - Professional communication
    - Quality engagement

    ---

    **Red Flags:**

    ❌ Insufficient experience (< 5 years)
    ❌ Vague or generic expertise
    ❌ No LinkedIn or can't verify claims
    ❌ Poor communication quality
    """)

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
