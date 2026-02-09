"""
User Portal Enhanced Components - Phase 2 UX Focused
==================================================

User-facing UI components focused on enhancing the end-user experience
without administrative monitoring features. These components are designed
for job seekers, CV uploaders, and regular users.

Features:
- User-friendly interface elements
- CV/Resume processing workflows
- Job matching interactions
- Personal dashboard components
- Profile management elements
- Application tracking components

Author: IntelliCV Enhancement Team
Python Environment: IntelliCV/env310
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
import json
import base64
from pathlib import Path

# =============================================================================
# USER-FOCUSED CSS SYSTEM
# =============================================================================

def inject_user_portal_css():
    """Inject user-friendly CSS focused on end-user experience"""
    st.markdown("""
    <style>
    /* User Portal Specific Styles */
    .user-main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
        color: white;
    }
    
    .user-welcome-card {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        border-left: 4px solid #6366f1;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .cv-upload-area {
        background: linear-gradient(135deg, #fef7ff 0%, #f3e8ff 100%);
        border: 2px dashed #8b5cf6;
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        margin: 2rem 0;
        transition: all 0.3s ease;
    }
    
    .cv-upload-area:hover {
        border-color: #6366f1;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    }
    
    .job-match-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #10b981;
        transition: transform 0.2s ease;
    }
    
    .job-match-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .user-progress-section {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid #bbf7d0;
    }
    
    .user-stat-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 3px solid #6366f1;
        transition: all 0.2s ease;
    }
    
    .user-stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
    }
    
    .user-action-button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100%;
        margin: 0.5rem 0;
    }
    
    .user-action-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    
    .user-profile-section {
        background: linear-gradient(135deg, #fefce8 0%, #fef3c7 100%);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid #fde047;
    }
    
    .application-status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .status-applied {
        background-color: #dbeafe;
        color: #1e40af;
    }
    
    .status-interview {
        background-color: #fef3c7;
        color: #92400e;
    }
    
    .status-offer {
        background-color: #dcfce7;
        color: #166534;
    }
    
    .status-rejected {
        background-color: #fee2e2;
        color: #991b1b;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# USER-FOCUSED COMPONENTS
# =============================================================================

def render_user_welcome_header(user_name: str = "User", recent_activity: str = ""):
    """Render a welcoming header for users"""
    current_time = datetime.now().strftime("%B %d, %Y")
    
    st.markdown(f"""
    <div class="user-main-header">
        <h1>👋 Welcome back, {user_name}!</h1>
        <p>Today is {current_time}</p>
        {f'<p style="font-size: 0.9rem; opacity: 0.9;">{recent_activity}</p>' if recent_activity else ''}
    </div>
    """, unsafe_allow_html=True)

def render_cv_upload_area(key_suffix: str = ""):
    """Render an enhanced CV upload area"""
    st.markdown("""
    <div class="cv-upload-area">
        <h3>📄 Upload Your CV/Resume</h3>
        <p>Drag and drop your CV here or click to browse</p>
        <p style="font-size: 0.9rem; opacity: 0.7;">Supported formats: PDF, DOC, DOCX</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose your CV/Resume file",
        type=['pdf', 'doc', 'docx'],
        key=f"cv_upload_{key_suffix}",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 Parse CV", key=f"parse_{key_suffix}"):
                st.info("CV parsing started...")
        with col2:
            if st.button("🎯 Find Jobs", key=f"jobs_{key_suffix}"):
                st.info("Job matching initiated...")
        with col3:
            if st.button("📊 Analysis", key=f"analysis_{key_suffix}"):
                st.info("CV analysis in progress...")
    
    return uploaded_file

def render_user_stats_dashboard(stats: Dict[str, Any]):
    """Render user statistics dashboard"""
    cols = st.columns(len(stats))
    
    for i, (stat_name, stat_value) in enumerate(stats.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="user-stat-card">
                <h3 style="color: #6366f1; margin: 0;">{stat_value}</h3>
                <p style="margin: 0.5rem 0 0 0; color: #64748b;">{stat_name}</p>
            </div>
            """, unsafe_allow_html=True)

def render_job_matches(matches: List[Dict[str, Any]]):
    """Render job match cards for users"""
    st.markdown("### 🎯 Recommended Job Matches")
    
    for match in matches:
        match_score = match.get('score', 85)
        company = match.get('company', 'Unknown Company')
        title = match.get('title', 'Job Title')
        location = match.get('location', 'Location')
        
        st.markdown(f"""
        <div class="job-match-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: #1f2937;">{title}</h4>
                    <p style="margin: 0.5rem 0; color: #6b7280;"><strong>{company}</strong> • {location}</p>
                </div>
                <div style="text-align: right;">
                    <div style="background: #10b981; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: 600;">
                        {match_score}% Match
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 View Details", key=f"view_{company}_{title}"):
                st.info(f"Viewing details for {title} at {company}")
        with col2:
            if st.button("📧 Apply Now", key=f"apply_{company}_{title}"):
                st.success(f"Application started for {title}")
        with col3:
            if st.button("💾 Save Job", key=f"save_{company}_{title}"):
                st.info(f"Job saved: {title}")

def render_application_tracker(applications: List[Dict[str, Any]]):
    """Render application tracking dashboard"""
    st.markdown("### 📋 Your Applications")
    
    if not applications:
        st.info("🚀 No applications yet. Start applying to jobs that match your profile!")
        return
    
    for app in applications:
        company = app.get('company', 'Unknown Company')
        title = app.get('title', 'Job Title')
        status = app.get('status', 'applied')
        date_applied = app.get('date_applied', 'Unknown Date')
        
        status_class = f"status-{status}"
        status_emoji = {
            'applied': '📧',
            'interview': '🗣️',
            'offer': '🎉',
            'rejected': '❌'
        }.get(status, '📧')
        
        st.markdown(f"""
        <div style="background: white; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h5 style="margin: 0;">{title}</h5>
                    <p style="margin: 0.25rem 0; color: #6b7280;">{company} • Applied: {date_applied}</p>
                </div>
                <div class="application-status-indicator {status_class}">
                    {status_emoji} {status.title()}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_user_profile_section(profile_data: Dict[str, Any]):
    """Render user profile management section"""
    st.markdown("""
    <div class="user-profile-section">
        <h3>👤 Your Profile</h3>
        <p>Keep your profile updated to get better job matches</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Full Name", value=profile_data.get('name', ''), key="profile_name")
        st.text_input("Email", value=profile_data.get('email', ''), key="profile_email")
        st.selectbox("Experience Level", 
                    options=["Entry Level", "Mid Level", "Senior Level", "Executive"],
                    index=0, key="profile_experience")
    
    with col2:
        st.text_input("Phone", value=profile_data.get('phone', ''), key="profile_phone")
        st.text_input("Location", value=profile_data.get('location', ''), key="profile_location")
        st.multiselect("Skills", 
                      options=["Python", "JavaScript", "React", "SQL", "Machine Learning", "Project Management"],
                      default=profile_data.get('skills', []), key="profile_skills")
    
    if st.button("💾 Update Profile", key="update_profile"):
        st.success("✅ Profile updated successfully!")

def render_user_progress_section(progress_data: Dict[str, Any]):
    """Render user progress and achievements"""
    st.markdown("""
    <div class="user-progress-section">
        <h3>🚀 Your Progress</h3>
        <p>Track your job search journey and achievements</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("Profile Completeness", progress_data.get('profile_complete', 75), "%"),
        ("CVs Uploaded", progress_data.get('cvs_uploaded', 3), ""),
        ("Jobs Applied", progress_data.get('jobs_applied', 12), ""),
        ("Interviews", progress_data.get('interviews', 2), "")
    ]
    
    for i, (label, value, unit) in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            st.metric(label, f"{value}{unit}")

def render_user_quick_actions():
    """Render quick action buttons for users"""
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📤 Upload New CV", key="quick_upload"):
            st.info("Redirecting to CV upload...")
    
    with col2:
        if st.button("🔍 Search Jobs", key="quick_search"):
            st.info("Opening job search...")
    
    with col3:
        if st.button("👤 Edit Profile", key="quick_profile"):
            st.info("Opening profile editor...")
    
    with col4:
        if st.button("📊 View Analytics", key="quick_analytics"):
            st.info("Loading your analytics...")

# =============================================================================
# USER EXPERIENCE HELPERS
# =============================================================================

def render_user_tips_sidebar():
    """Render helpful tips in sidebar for users"""
    with st.sidebar:
        st.markdown("### 💡 Tips for Success")
        
        tips = [
            "📄 Keep your CV updated and tailored",
            "🎯 Apply to jobs that match your skills",
            "📧 Follow up on applications",
            "💼 Build a strong LinkedIn profile",
            "🌟 Highlight your achievements"
        ]
        
        for tip in tips:
            st.markdown(f"• {tip}")
        
        st.markdown("---")
        st.markdown("### 📞 Need Help?")
        st.markdown("Contact our support team for assistance with your job search.")

def create_user_dashboard_layout():
    """Create a standard user dashboard layout"""
    # Welcome section
    render_user_welcome_header()
    
    # Quick stats
    sample_stats = {
        "Profile Score": "85%",
        "Job Matches": "23",
        "Applications": "12",
        "Responses": "4"
    }
    render_user_stats_dashboard(sample_stats)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Job Matches",
        "📋 Applications", 
        "👤 Profile",
        "📊 Progress"
    ])
    
    return tab1, tab2, tab3, tab4

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

__all__ = [
    'inject_user_portal_css',
    'render_user_welcome_header',
    'render_cv_upload_area',
    'render_user_stats_dashboard',
    'render_job_matches',
    'render_application_tracker',
    'render_user_profile_section',
    'render_user_progress_section',
    'render_user_quick_actions',
    'render_user_tips_sidebar',
    'create_user_dashboard_layout'
]