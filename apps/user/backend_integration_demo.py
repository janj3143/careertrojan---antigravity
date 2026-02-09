"""
Demo: Backend Integration Placeholders
=====================================
This demonstrates what users see when accessing word cloud and job intelligence features.
"""

import streamlit as st
from job_title_backend_integration import JobTitleBackend

st.set_page_config(page_title="Backend Integration Demo", page_icon="🎨", layout="wide")

st.title("🎨 Backend Integration Placeholders Demo")
st.markdown("This shows what users see when accessing the moved backend services.")

# Initialize session state for demo
if 'user_tokens' not in st.session_state:
    st.session_state['user_tokens'] = 50  # Give user some tokens for demo
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = 'demo_user'

# Show current token balance
st.info(f"💎 **Your Token Balance**: {st.session_state.get('user_tokens', 0)} tokens")

# Initialize backend integration
backend = JobTitleBackend(st.session_state.get('user_id'))

# Show service status
backend.show_service_status()

st.markdown("---")

# Demo the different services
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎨 Word Cloud Generation")
    if st.button("Generate Word Cloud (5 tokens)", key="wordcloud"):
        # Use real job titles from AI data
        real_job_titles = backend._extract_job_titles_from_real_data()
        job_titles = real_job_titles[:4] if real_job_titles else ["Data Scientist", "ML Engineer", "AI Researcher", "Python Developer"]
        result = backend.generate_word_cloud(job_titles, "demo_page")
        if result:
            st.success(f"Word cloud generated from {len(job_titles)} real job titles!")

    st.subheader("🧠 Job Title Analysis")
    job_title = st.text_input("Enter job title to analyze:", value="Senior Data Scientist")
    if st.button("Analyze Job Title (7 tokens)", key="analyze"):
        result = backend.analyze_job_title(job_title, "5 years experience in ML")
        if result:
            st.success("Job title analysis completed!")

with col2:
    st.subheader("🛤️ Career Pathways")
    current_role = st.text_input("Your current role:", value="Data Analyst")
    if st.button("Get Career Pathways (7 tokens)", key="pathways"):
        result = backend.get_career_pathways(current_role)
        if result:
            st.success("Career pathways generated!")

    st.subheader("📊 Market Intelligence")
    job_category = st.selectbox("Select category:", ["Technology", "Finance", "Healthcare", "Marketing"])
    if st.button("Get Market Intelligence (7 tokens)", key="market"):
        result = backend.get_market_intelligence(job_category)
        if result:
            st.success("Market intelligence retrieved!")

st.markdown("---")

st.subheader("🔗 Title Relationships")
base_title = st.text_input("Job title to find relationships for:", value="Product Manager")
if st.button("Find Related Titles (5 tokens)", key="relationships"):
    result = backend.get_title_relationships(base_title)
    if result:
        st.success("Title relationships mapped!")

st.markdown("---")
st.info("💡 **Note**: This demo shows the placeholder UI that users see while the backend service is connecting. In production, these would display actual analysis results.")