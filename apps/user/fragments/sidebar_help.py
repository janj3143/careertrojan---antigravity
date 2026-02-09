import streamlit as st

# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False


def show_help_tour():

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.sidebar.title("🆘 Help & Tour")

    query = st.sidebar.text_input("Search Help Topics", placeholder="e.g., resume feedback, job match")

    help_topics = {
        "Getting Started": "Start by uploading your resume and reviewing your profile.",
        "Resume Upload": "Upload a .pdf or .docx file. It will be parsed and enriched automatically.",
        "Resume Feedback": "Get AI-based feedback on your resume including STAR stories and keyword analysis.",
        "Job Matching": "Paste a job description and see how well your resume matches the required skills.",
        "Resume Tuner": "Use this tool to refine tone, structure, and emphasis for specific roles.",
        "Application Tracker": "Track where and when resumes were sent, and receive status updates.",
        "Profile Completion": "Fill in your key skills, past roles, and optionally link your LinkedIn.",
        "AI Insights": "Leverage industry trends, job radar, and predictive fit models for deeper insights."
    }

    if query:
        filtered = {k: v for k, v in help_topics.items() if query.lower() in k.lower() or query.lower() in v.lower()}
        if filtered:
            for title, desc in filtered.items():
                st.sidebar.markdown(f"**{title}**
- {desc}")
        else:
            st.sidebar.info("No matching help topics found.")
    else:
        # Default tour
        with st.sidebar.expander("📖 Guided Tour", expanded=False):
            for title, desc in help_topics.items():
                st.markdown(f"### {title}")
                st.markdown(desc)
                st.markdown("---")