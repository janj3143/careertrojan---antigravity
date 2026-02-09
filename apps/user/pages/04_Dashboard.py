"""
🏠 IntelliCV User Portal - Enhanced Landing Dashboard
===================================================

Main dashboard showcasing the comprehensive career intelligence platform with:
- Career quadrant positioning visualization
- Daily engagement touchpoints
- Progress tracking and analytics
- Quick access to all platform features
- Personalized recommendations

This serves as the main entry point after authentication.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
import sys
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Use Shared IO Layer for data access
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from shared.io_layer import get_io_layer
    io_layer = get_io_layer()
    SHARED_IO_AVAILABLE = True
except ImportError:
    SHARED_IO_AVAILABLE = False
    io_layer = None

# Page configuration
st.set_page_config(
    page_title="IntelliCV Dashboard | Your Career Intelligence Hub",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DashboardEngine:
    """Main dashboard data and analytics engine"""

    def __init__(self):
        self.user_data = self._load_user_data()
        self.platform_stats = self._load_platform_stats()
        self.recommendations = self._generate_recommendations()

    def _load_user_data(self) -> Dict[str, Any]:
        """Load user profile and progress data via Shared IO Layer"""

        # Get user_id from session
        user_id = st.session_state.get('user_id')

        # Try to get real user data from Shared IO Layer
        if SHARED_IO_AVAILABLE and io_layer and user_id:
            try:
                # Get real candidate profile
                candidate_data = io_layer.get_candidate_data(user_id)
                if candidate_data:
                    profile = candidate_data.get('profile', {})
                    skills_list = profile.get('skills', [])[:6]
                    sample_title = profile.get('current_role', 'Professional')
                else:
                    skills_list = []
                    sample_title = "Professional"

            except Exception as e:
                logger.warning(f"Could not load user data: {e}")
                skills_list = []
                sample_title = "Professional"
        else:
            skills_list = []
            sample_title = "Professional"

        user_name = st.session_state.get('user_name') or st.session_state.get('authenticated_user') or ""

        # Real data only: do not invent scores/tiers/locations.
        return {
            "profile": {
                "name": user_name or "User",
                "title": st.session_state.get('user_title') or sample_title or "",
                "experience_years": st.session_state.get('experience_years'),
                "target_role": st.session_state.get('target_role') or "",
                "location": st.session_state.get('location') or "",
                "skills": st.session_state.get('user_skills', skills_list) if st.session_state.get('user_skills') else skills_list
            },
            "career_position": {
                "skills_score": st.session_state.get('skills_score'),
                "market_demand": st.session_state.get('market_demand'),
                "quadrant": st.session_state.get('quadrant') or "",
                "peer_percentile": st.session_state.get('peer_percentile')
            },
            "engagement": {
                "level": st.session_state.get('engagement_level') or "",
                "points": st.session_state.get('user_points', 0),
                "streak_days": st.session_state.get('streak_days', 0),
                "completed_modules": st.session_state.get('completed_modules', 0),
                "total_modules": st.session_state.get('total_modules')
            },
            "recent_activity": st.session_state.get('recent_activity', [])
        }

    def _load_platform_stats(self) -> Dict[str, Any]:
        """Platform-wide statistics are backend-owned; do not fabricate."""
        return {}

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Recommendations must be backend/AI-sourced; do not fabricate."""
        return []

def create_career_quadrant_mini(user_position: Dict) -> go.Figure:
    """Create mini career quadrant for dashboard"""

    fig = go.Figure()

    # Add quadrant background
    quadrants = [
        {"x": [0, 50], "y": [0, 50], "color": "rgba(255, 200, 200, 0.3)"},
        {"x": [50, 100], "y": [0, 50], "color": "rgba(255, 255, 200, 0.3)"},
        {"x": [0, 50], "y": [50, 100], "color": "rgba(200, 255, 200, 0.3)"},
        {"x": [50, 100], "y": [50, 100], "color": "rgba(200, 200, 255, 0.3)"}
    ]

    for quad in quadrants:
        fig.add_shape(
            type="rect",
            x0=quad["x"][0], y0=quad["y"][0],
            x1=quad["x"][1], y1=quad["y"][1],
            fillcolor=quad["color"],
            layer="below",
            line_width=0
        )

    # Add dividing lines
    fig.add_hline(y=50, line_dash="dash", line_color="gray", line_width=1)
    fig.add_vline(x=50, line_dash="dash", line_color="gray", line_width=1)

    # Add user position
    fig.add_trace(go.Scatter(
        x=[user_position["market_demand"]],
        y=[user_position["skills_score"]],
        mode='markers',
        marker=dict(
            size=20,
            color='red',
            symbol='star',
            line=dict(width=3, color='darkred')
        ),
        name='Your Position',
        hovertemplate=f'<b>Your Position</b><br>Skills: %{{y}}<br>Market Demand: %{{x}}<br>Quadrant: {user_position["quadrant"]}<extra></extra>'
    ))

    fig.update_layout(
        xaxis_title='Market Demand',
        yaxis_title='Skills Score',
        xaxis=dict(range=[0, 100], showgrid=False),
        yaxis=dict(range=[0, 100], showgrid=False),
        plot_bgcolor='white',
        width=300,
        height=250,
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False
    )

    return fig

def create_progress_chart(recent_activity: List[Dict[str, Any]]) -> go.Figure:
    """Create progress tracking chart from real recent activity events."""

    # Build last-7-days buckets using only recorded activity.
    today = datetime.now().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    labels = [d.strftime('%a') for d in days]
    completed_map = {d: 0 for d in days}

    for ev in (recent_activity or []):
        try:
            raw = ev.get('date')
            if not raw:
                continue
            # Accept YYYY-MM-DD or ISO; ignore unparseable.
            d = datetime.fromisoformat(str(raw)).date()
        except Exception:
            try:
                d = datetime.strptime(str(raw)[:10], '%Y-%m-%d').date()
            except Exception:
                continue

        if d in completed_map:
            completed_map[d] += 1

    completed = [completed_map[d] for d in days]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=days,
        y=completed,
        name='Completed',
        marker_color='green',
        opacity=0.8
    ))

    if sum(completed) == 0:
        fig.add_annotation(
            text="No activity recorded this week.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

    fig.update_layout(
        title='This Week\'s Activity',
        xaxis_title='Day',
        yaxis_title='Activities Completed',
        height=250,
        margin=dict(l=40, r=40, t=40, b=40)
    )

    return fig

def main():
    """Main dashboard interface"""

    # Initialize dashboard engine
    dashboard = DashboardEngine()
    user_data = dashboard.user_data

    # Header with personalized greeting
    current_hour = datetime.now().hour
    greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 18 else "Good evening"

    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                padding: 30px; border-radius: 15px; margin-bottom: 30px;">
        <h1 style="color: white; margin: 0;">{greeting}, {user_data['profile']['name']}! 👋</h1>
        <p style="color: white; margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">
            Ready to accelerate your career journey? Let's make today count! 🚀
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats overview
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Career Level",
            user_data['engagement']['level'] or "–",
            delta=None
        )

    with col2:
        total_modules = user_data['engagement'].get('total_modules')
        completed_modules = user_data['engagement'].get('completed_modules', 0)
        if isinstance(total_modules, int) and total_modules > 0:
            completion_rate = (completed_modules / total_modules) * 100
            st.metric("Platform Progress", f"{completion_rate:.0f}%")
        else:
            st.metric("Platform Progress", "Unavailable")

    with col3:
        st.metric(
            "Career Quadrant",
            user_data['career_position']['quadrant'] or "Unavailable",
            delta=None
        )

    with col4:
        st.metric(
            "Engagement Points",
            f"{user_data['engagement']['points']:,}",
            delta=None
        )

    with col5:
        st.metric("Next Milestone", "Unavailable")

    # Main dashboard content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Career positioning section
        st.markdown("### 🎯 Your Career Position")

        subcol1, subcol2 = st.columns([1, 1])

        with subcol1:
            skills_score = user_data['career_position'].get('skills_score')
            market_demand = user_data['career_position'].get('market_demand')
            if isinstance(skills_score, (int, float)) and isinstance(market_demand, (int, float)):
                quadrant_chart = create_career_quadrant_mini(user_data['career_position'])
                st.plotly_chart(quadrant_chart, use_container_width=True)
            else:
                st.info("Career quadrant is unavailable until real scoring data is provided.")

        with subcol2:
            quadrant = user_data['career_position'].get('quadrant') or "Unavailable"
            skills_score = user_data['career_position'].get('skills_score')
            market_demand = user_data['career_position'].get('market_demand')
            peer_percentile = user_data['career_position'].get('peer_percentile')

            st.markdown(f"**Current Quadrant:** {quadrant}")
            st.markdown(f"**Skills Score:** {skills_score if skills_score is not None else '–'}")
            st.markdown(f"**Market Demand:** {market_demand if market_demand is not None else '–'}")
            st.markdown(f"**Peer Percentile:** {peer_percentile if peer_percentile is not None else '–'}")

            if st.button("📊 View Full Career Analytics", use_container_width=True):
                st.session_state.current_page = "Career_Intelligence"
                st.rerun()

        # Activity progress
        st.markdown("### 📈 This Week's Progress")

        progress_chart = create_progress_chart(user_data.get('recent_activity', []))
        st.plotly_chart(progress_chart, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Today's Opportunities")
        st.info("Opportunities require backend task definitions.")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🎯 Start Interview Practice", use_container_width=True):
            st.session_state.current_page = "AI_Interview_Coach"
            st.rerun()

        if st.button("🤝 Find Mentors", use_container_width=True):
            st.session_state.current_page = "Mentorship_Hub"
            st.rerun()

        if st.button("💰 Salary Analysis", use_container_width=True):
            st.session_state.current_page = "Advanced_Career_Tools"
            st.rerun()

    # Recommendations section
    st.markdown("### 🎯 Personalized Recommendations")

    recommendations = dashboard.recommendations
    if not recommendations:
        st.info("Recommendations are unavailable until provided by backend/AI services.")

    # Recent activity and community highlights
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 Recent Activity")

        recent = user_data.get('recent_activity') or []
        if not recent:
            st.info("No recent activity recorded.")
        else:
            for activity in recent[:4]:
                st.markdown(f"**{activity.get('date','')}**")
                st.caption(activity.get('activity',''))

    with col2:
        st.markdown("### 🏆 Platform Highlights")
        st.info("Platform-wide highlights are unavailable until provided by backend analytics.")

    # Feature discovery section
    st.markdown("### 🚀 Discover Platform Features")

    feature_cols = st.columns(4)

    features = [
        {
            "name": "AI Interview Coach",
            "icon": "🎯",
            "description": "Practice with AI feedback",
            "page": "AI_Interview_Coach",
            "users": ""
        },
        {
            "name": "Career Intelligence",
            "icon": "📊",
            "description": "Quadrant positioning",
            "page": "Career_Intelligence",
            "users": ""
        },
        {
            "name": "Mentorship Hub",
            "icon": "🤝",
            "description": "Connect with mentors",
            "page": "Mentorship_Hub",
            "users": ""
        },
        {
            "name": "Career Tools",
            "icon": "🛠️",
            "description": "Salary & market analysis",
            "page": "Advanced_Career_Tools",
            "users": ""
        }
    ]

    for i, feature in enumerate(features):
        with feature_cols[i]:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 10px;
                        border: 1px solid #e0e0e0; text-align: center; height: 160px;">
                <div style="font-size: 30px; margin-bottom: 10px;">{feature['icon']}</div>
                <h4 style="margin: 10px 0;">{feature['name']}</h4>
                <p style="font-size: 14px; color: #666; margin: 5px 0;">{feature['description']}</p>
                <p style="font-size: 12px; color: #999;">{feature['users']}</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Explore {feature['name']}", key=f"feature_{i}", use_container_width=True):
                st.session_state.current_page = feature['page']
                st.rerun()

if __name__ == "__main__":
    main()
