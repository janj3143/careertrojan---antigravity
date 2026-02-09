"""
IntelliCV Updated Sidebar Demo - Job Title Intelligence Integration
================================================================
This demo shows the enhanced sidebar with Job Title Intelligence and Venn diagram features
"""

import streamlit as st
import time
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="IntelliCV - Job Title Intelligence Demo",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced appearance
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    .demo-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .sidebar-preview {
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .new-feature {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin-left: 0.5rem;
    }
    
    .feature-highlight {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .venn-demo {
        background: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    
    .overlap-badge {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffd93d 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# Simulate authentication
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = True

if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Import and show the actual sidebar
try:
    import sys
    from pathlib import Path
    
    # Add the fragments path
    fragments_path = Path(__file__).parent / "fragments"
    if str(fragments_path) not in sys.path:
        sys.path.insert(0, str(fragments_path))
    
    from sidebar import show_sidebar
    show_sidebar()
    
    sidebar_loaded = True
except ImportError as e:
    sidebar_loaded = False
    st.error(f"Could not load sidebar: {e}")

# Main content
st.markdown("""
<div class="main-header">
    <h1>🎯 Job Title Intelligence Demo</h1>
    <p>AI-Powered Semantic Analysis & Interactive Venn Diagrams</p>
    <p><strong>New Feature:</strong> Job overlap visualization with concentric circles & AI chat integration</p>
    <p><strong>Demo Port:</strong> 8504 | <strong>Updated:</strong> October 2, 2025</p>
</div>
""", unsafe_allow_html=True)

# Updated Sidebar Structure
st.markdown("## 📋 Updated Navigation Structure")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""
    <div class="sidebar-preview">
        <h3>🚀 Core Tools</h3>
        <div class="feature-highlight">
            📊 Resume Analysis Hub <span class="new-feature">ENHANCED</span>
        </div>
        <p>👤 Profile</p>
        <p>📤 Resume Upload</p>
        <p>📚 Resume History</p>
        <p>🛠️ Resume Tuner</p>
        <p>🎯 Resume vs Role Match</p>
        
        <hr>
        
        <h3>💼 Career Development</h3>
        <div class="feature-highlight">
            🎤 Interview Coach <span class="new-feature">NEW</span>
        </div>
        <div class="feature-highlight">
            🎯 Job Title Intelligence <span class="new-feature">NEW</span>
        </div>
        <p>🌟 Career Coach</p>
        <p>📋 Job Tracker</p>
        <p>💰 Salary Coach</p>
        <p>🎨 Portfolio Builder</p>
        
        <hr>
        
        <h3>🤖 Resume Intelligence</h3>
        <p>🧠 Glossary Insights</p>
        <p>📄 JD Comparison</p>
        <p>💬 Fit Feedback</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 🎯 Job Title Intelligence Features")
    
    st.markdown("""
    <div class="venn-demo">
        <h4>🔍 5 Core Features Added:</h4>
        <ul>
            <li><strong>Semantic Analysis:</strong> AI-powered job title similarity detection</li>
            <li><strong>AI Chat Integration:</strong> "What is this job title?" descriptions</li>
            <li><strong>Venn Diagrams:</strong> Interactive overlap visualization</li>
            <li><strong>Concentric Circles:</strong> Skill importance levels</li>
            <li><strong>Industry Mapping:</strong> Cross-industry job title translation</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Demo Interactive Venn Diagram
st.markdown("## 🔄 Interactive Job Title Overlap Demo")

col1, col2, col3 = st.columns(3)

with col1:
    job1 = st.selectbox("Job Title 1:", ["Software Engineer", "Data Scientist", "Product Manager", "DevOps Engineer"])

with col2:
    job2 = st.selectbox("Job Title 2:", ["Data Scientist", "Software Engineer", "Technical Lead", "Full Stack Engineer"])

with col3:
    visualization_type = st.selectbox("Visualization:", ["Venn Diagram", "Concentric Circles", "Skill Matrix"])

if st.button("🎨 Generate Overlap Visualization", type="primary"):
    st.success(f"✅ Generating {visualization_type} for {job1} vs {job2}")
    
    # Create mock Venn diagram
    if visualization_type == "Venn Diagram":
        fig = go.Figure()
        
        # Add circles
        fig.add_shape(
            type="circle",
            x0=0.2, y0=0.2, x1=0.8, y1=0.8,
            fillcolor="rgba(100, 150, 200, 0.3)",
            line=dict(color="rgba(100, 150, 200, 0.8)", width=3),
            layer="below"
        )
        
        fig.add_shape(
            type="circle", 
            x0=0.4, y0=0.2, x1=1.0, y1=0.8,
            fillcolor="rgba(200, 100, 150, 0.3)",
            line=dict(color="rgba(200, 100, 150, 0.8)", width=3),
            layer="below"
        )
        
        # Add labels
        fig.add_annotation(x=0.3, y=0.5, text=job1, showarrow=False, font=dict(size=16, color="blue"))
        fig.add_annotation(x=0.7, y=0.5, text=job2, showarrow=False, font=dict(size=16, color="red"))
        fig.add_annotation(x=0.5, y=0.5, text="Shared Skills", showarrow=False, font=dict(size=14, color="purple"))
        
        fig.update_layout(
            title=f"Job Title Overlap: {job1} ∩ {job2}",
            xaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif visualization_type == "Concentric Circles":
        fig = go.Figure()
        
        # Create concentric circles
        circles = [
            dict(size=0.8, color="rgba(100, 150, 200, 0.2)", label="All Skills"),
            dict(size=0.6, color="rgba(150, 100, 200, 0.3)", label="Common Skills"),
            dict(size=0.4, color="rgba(200, 100, 150, 0.4)", label="Core Skills"),
            dict(size=0.2, color="rgba(100, 200, 150, 0.5)", label="Essential")
        ]
        
        for circle in circles:
            fig.add_shape(
                type="circle",
                x0=0.5-circle['size']/2, y0=0.5-circle['size']/2,
                x1=0.5+circle['size']/2, y1=0.5+circle['size']/2,
                fillcolor=circle['color'],
                line=dict(width=2),
                layer="below"
            )
        
        fig.update_layout(
            title=f"Skill Importance Levels: {job1} & {job2}",
            xaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(range=[0, 1], showgrid=False, zeroline=False, showticklabels=False),
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    else:  # Skill Matrix
        skills = ["Python", "Leadership", "Analytics", "Communication", "Problem Solving", "Teamwork"]
        similarity_matrix = np.random.randint(50, 100, (len(skills), len(skills)))
        
        fig = go.Figure(data=go.Heatmap(
            z=similarity_matrix,
            x=skills,
            y=skills,
            colorscale='Viridis',
            colorbar=dict(title="Overlap %")
        ))
        
        fig.update_layout(
            title=f"Skill Overlap Matrix: {job1} & {job2}",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Show overlap analysis
    st.markdown("### 🔍 AI Analysis Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Skill Overlap", "73%", delta="High Similarity")
    
    with col2:
        st.metric("Career Bridge Score", "85%", delta="Easy Transition")
    
    with col3:
        st.metric("Shared Core Skills", "12", delta="Strong Match")
    
    # Mock shared skills
    st.markdown("#### 🎯 Shared Skills")
    shared_skills = ["Programming", "Problem Solving", "Analytics", "Team Collaboration", "Project Management"]
    
    for skill in shared_skills:
        st.markdown(f'<span class="overlap-badge">{skill}</span>', unsafe_allow_html=True)

# AI Chat Integration Demo
st.markdown("## 🤖 AI Chat Integration Demo")

col1, col2 = st.columns([2, 1])

with col1:
    chat_query = st.text_input(
        "Ask AI about any job title:",
        placeholder="What does a Product Manager do?"
    )
    
    if st.button("🤖 Ask AI", type="primary") and chat_query:
        with st.spinner("🤖 AI is analyzing the job title..."):
            time.sleep(2)  # Simulate processing
            
            st.markdown("""
            <div class="venn-demo">
                <h4>🤖 AI Response:</h4>
                <p><strong>Product Manager</strong> is a strategic role that involves:</p>
                <ul>
                    <li><strong>Product Strategy:</strong> Define product vision and roadmap</li>
                    <li><strong>Market Research:</strong> Analyze user needs and competitive landscape</li>
                    <li><strong>Cross-functional Leadership:</strong> Coordinate engineering, design, and marketing teams</li>
                    <li><strong>Data-Driven Decisions:</strong> Use analytics to guide product development</li>
                </ul>
                <p><em>This description helps populate the job title overlap cloud for similar roles like Product Owner, Business Analyst, and Strategy Manager.</em></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.success("✅ AI description added to overlap cloud database!")

with col2:
    st.markdown("### 💡 Popular Queries")
    st.info("""
    **Trending Questions:**
    • "What is a DevOps Engineer?"
    • "Data Scientist vs Data Analyst"
    • "Product Manager skills needed"
    • "Software Engineer career path"
    
    **AI builds overlap cloud:**
    • Similar job titles identified
    • Skill intersections mapped
    • Career transition paths suggested
    """)

# Admin Engine Preview
st.markdown("## ⚙️ Admin Engine: Overlap Cloud Builder")

st.markdown("""
<div class="demo-section">
    <h4>🔧 How the Admin Engine Works:</h4>
    <p><strong>1. AI Chat Integration:</strong> When users ask "What is [job title]?", responses are analyzed and stored</p>
    <p><strong>2. Similarity Detection:</strong> AI identifies job titles with overlapping responsibilities and skills</p>
    <p><strong>3. Overlap Cloud Generation:</strong> Similar titles are clustered into visual overlap maps</p>
    <p><strong>4. Venn Diagram Creation:</strong> Concentric circles show skill importance and intersections</p>
    <p><strong>5. Industry Mapping:</strong> Cross-industry equivalent roles are identified and connected</p>
</div>
""", unsafe_allow_html=True)

# Statistics
st.markdown("## 📊 System Impact")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Job Titles Analyzed", "2,847", delta="127 new")

with col2:
    st.metric("AI Descriptions", "1,923", delta="234 from chat")

with col3:
    st.metric("Overlap Pairs", "45,678", delta="1,234 new")

with col4:
    st.metric("Venn Diagrams", "567", delta="89 generated")

# Implementation Status
st.markdown("## ✅ Implementation Status")

implementation_status = pd.DataFrame([
    {"Feature": "🎯 Job Title Intelligence Page", "Status": "✅ Complete", "Details": "5 tabs with full functionality"},
    {"Feature": "🤖 AI Chat Integration", "Status": "✅ Complete", "Details": "Job title descriptions with chat interface"},
    {"Feature": "📊 Venn Diagram Visualizer", "Status": "✅ Complete", "Details": "2-way, 3-way, and concentric circles"},
    {"Feature": "🏢 Industry Mapping", "Status": "✅ Complete", "Details": "Cross-industry job title translation"},
    {"Feature": "⚙️ Admin Engine", "Status": "✅ Complete", "Details": "Database management and AI training"},
    {"Feature": "🔗 Sidebar Integration", "Status": "✅ Complete", "Details": "Added to Career Development section"}
])

st.dataframe(implementation_status, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><strong>🎯 Job Title Intelligence System</strong> - Revolutionary Career Intelligence</p>
    <p>AI-powered semantic analysis with interactive Venn diagrams and overlap cloud generation</p>
    <p><em>Admin engine analyzes user queries to build comprehensive job title relationships</em></p>
</div>
""", unsafe_allow_html=True)

# Show current time for demo purposes
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Demo Time:** {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.markdown("**Status:** ✅ Job Title Intelligence Added")
st.sidebar.markdown("**New Features:** 🎯 AI Chat + Venn Diagrams")