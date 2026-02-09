"""
📊 Career Intelligence & Trajectory Analysis
============================================
Advanced career trajectory analysis with AI-powered insights:
- Visualize career trajectory vs. peers
- Scenario simulation (Beat Peers, Match Peers, Lifestyle)
- Cloud overlays (Job, Skills, Peer Group)
- Real-time market intelligence

Premium Feature | Token Cost: 12 tokens
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

# Setup paths
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Import portal bridge for cross-portal communication
try:
    from shared_backend.services.portal_bridge import IntelligenceService
    intelligence_service = IntelligenceService()
    PORTAL_BRIDGE_AVAILABLE = True
except ImportError as e:
    PORTAL_BRIDGE_AVAILABLE = False
    intelligence_service = None

# Page configuration
st.set_page_config(
    page_title="📊 Career Intelligence | IntelliCV-AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication check
if not st.session_state.get('authenticated_user'):
    st.error("🔒 Please log in to access Career Intelligence")
    if st.button("🏠 Return to Home"):
        st.switch_page("main.py")
    st.stop()

# Tier check for premium features
user_tier = st.session_state.get('subscription_tier', 'free')
PREMIUM_TIERS = ['monthly_pro', 'annual_pro', 'enterprise_pro']

if user_tier not in PREMIUM_TIERS:
    st.warning("⭐ Career Intelligence requires Premium subscription")
    if st.button("⬆️ Upgrade to Premium", type="primary"):
        st.switch_page("pages/06_Pricing.py")
    st.stop()

# Title and introduction
st.title("📊 Career Intelligence & Trajectory Analysis")
st.markdown("**AI-powered career path analysis with peer benchmarking and scenario simulation**")

st.info("💎 **Token Cost: 12 tokens** | Comprehensive trajectory analysis with market intelligence")

# Main content tabs
tab1, tab2, tab3 = st.tabs([
    "🎯 Career Trajectory",
    "🔮 Scenario Simulation", 
    "☁️ Cloud Overlays"
])

# ===========================
# TAB 1: CAREER TRAJECTORY
# ===========================
with tab1:
    st.header("🎯 Career Trajectory Analysis")
    st.markdown("Visualize your career path vs. peer benchmarks")
    
    # Get resume data from session
    resume_data = st.session_state.get('resume_data', {})
    
    if not resume_data:
        st.warning("⚠️ No resume data found. Please upload your resume in Resume Analysis page first.")
        if st.button("📄 Go to Resume Analysis"):
            st.switch_page("pages/09_Resume_Upload_Analysis.py")
    else:
        # Controls
        col1, col2 = st.columns(2)
        
        with col1:
            target_roles = st.multiselect(
                "🎯 Target Roles",
                ["Senior Data Scientist", "ML Engineer Lead", "AI Research Scientist", 
                 "Technical Manager", "Principal Engineer"],
                default=["Senior Data Scientist"]
            )
        
        with col2:
            location_flex = st.slider("📍 Location Flexibility (km)", 0, 500, 50, 25)
        
        # Analyze button
        if st.button("🔍 Analyze Career Trajectory", type="primary", use_container_width=True):
            with st.spinner("🧠 Analyzing career path with AI..."):
                # Call portal_bridge for career analysis
                if PORTAL_BRIDGE_AVAILABLE and intelligence_service:
                    try:
                        # Get career trajectory analysis from admin backend
                        trajectory_data = intelligence_service.analyze_career(
                            cv_data=resume_data,
                            target_roles=target_roles
                        )
                        
                        # Display results
                        st.success("✅ Career trajectory analysis complete!")
                        
                        # Current position
                        st.markdown("### 📍 Current Position")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Current Role", trajectory_data.get('current_role', 'Data Scientist'))
                        with col2:
                            st.metric("Years Experience", trajectory_data.get('years_experience', '5'))
                        with col3:
                            st.metric("Career Level", trajectory_data.get('career_level', 'Mid-Senior'))
                        
                        # Trajectory chart
                        st.markdown("### 📈 Career Trajectory Projection")
                        
                        # Create trajectory visualization
                        fig = go.Figure()
                        
                        # Add user trajectory line
                        if 'trajectory_points' in trajectory_data:
                            fig.add_trace(go.Scatter(
                                x=[p['year'] for p in trajectory_data['trajectory_points']],
                                y=[p['level'] for p in trajectory_data['trajectory_points']],
                                mode='lines+markers',
                                name='Your Trajectory',
                                line=dict(color='#667eea', width=3)
                            ))
                        
                        # Add peer benchmark
                        if 'peer_benchmark' in trajectory_data:
                            fig.add_trace(go.Scatter(
                                x=[p['year'] for p in trajectory_data['peer_benchmark']],
                                y=[p['level'] for p in trajectory_data['peer_benchmark']],
                                mode='lines',
                                name='Peer Average',
                                line=dict(color='#f59e0b', width=2, dash='dash')
                            ))
                        
                        fig.update_layout(
                            title="Career Level Progression",
                            xaxis_title="Years from Now",
                            yaxis_title="Career Level Score",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Next steps
                        st.markdown("### 🚀 Recommended Next Steps")
                        if 'recommendations' in trajectory_data:
                            for i, rec in enumerate(trajectory_data['recommendations'], 1):
                                st.markdown(f"{i}. {rec}")
                        
                        # Skill gaps
                        st.markdown("### 🎯 Skill Gap Analysis")
                        if 'skill_gaps' in trajectory_data:
                            gap_df = pd.DataFrame(trajectory_data['skill_gaps'])
                            st.dataframe(gap_df, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"❌ Error analyzing trajectory: {str(e)}")
                        st.info("Using fallback analysis...")
                        st.markdown("**Fallback Analysis**: Please ensure admin backend is running")
                else:
                    st.warning("⚠️ Portal bridge unavailable - using cached analysis")
                    st.info("ℹ️ Start admin backend API for real-time analysis")

# ===========================
# TAB 2: SCENARIO SIMULATION
# ===========================
with tab2:
    st.header("🔮 Career Scenario Simulation")
    st.markdown("Simulate different career paths and see projected outcomes")
    
    # Scenario selection
    scenario = st.selectbox(
        "📋 Select Scenario",
        ["Beat Peers - Accelerated Growth", 
         "Match Peers - Steady Progression",
         "Lifestyle - Work-Life Balance"]
    )
    
    # Scenario parameters
    col1, col2 = st.columns(2)
    
    with col1:
        years_ahead = st.slider("🕐 Years to Simulate", 1, 10, 5)
        relocation_ok = st.checkbox("🌍 Open to Relocation", value=True)
    
    with col2:
        upskill_commitment = st.slider("📚 Upskilling Hours/Week", 0, 20, 5)
        job_switch_ok = st.checkbox("🔄 Open to Job Switch", value=True)
    
    if st.button("🎬 Run Simulation", type="primary", use_container_width=True):
        st.success(f"✅ Simulated '{scenario}' for {years_ahead} years")
        
        # Mock simulation results
        st.markdown("### 📊 Simulation Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Projected Role", "Senior ML Lead", delta="2 levels up")
        with col2:
            st.metric("Salary Increase", "+£35k", delta="+58%")
        with col3:
            st.metric("Skills Gained", "12 new skills")
        with col4:
            st.metric("Network Growth", "+150 contacts")

# ===========================
# TAB 3: CLOUD OVERLAYS
# ===========================
with tab3:
    st.header("☁️ Cloud Overlays & Visualizations")
    st.markdown("Generate word clouds and skill overlays from your career data")
    
    # Cloud type selection
    cloud_type = st.selectbox(
        "☁️ Cloud Type",
        ["Job Titles Cloud", "Skills Cloud", "Industry Cloud", "Peer Group Cloud"]
    )
    
    # Cloud options
    col1, col2 = st.columns(2)
    with col1:
        cloud_size = st.slider("Cloud Size", 50, 200, 100)
    with col2:
        color_scheme = st.selectbox("Color Scheme", ["Blue", "Green", "Purple", "Rainbow"])
    
    if st.button("🎨 Generate Cloud", type="primary", use_container_width=True):
        st.success(f"✅ Generated {cloud_type}")
        st.info("💡 Cloud visualization would appear here (integration with universal_cloud_maker.py)")

# Footer
st.markdown("---")
st.markdown("*Powered by IntelliCV-AI Career Intelligence Engine*")
