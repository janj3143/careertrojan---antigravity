
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

"""
Dashboard UI Component
=====================

Main dashboard interface for the IntelliCV-AI Admin Portal.
"""

import streamlit as st
from datetime import datetime


class Dashboard:
    """Main dashboard component with overview metrics and quick actions."""
    
    def __init__(self):
        """Initialize dashboard component."""
        pass
    
    def render(self):
        """Render the main dashboard interface."""

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.markdown('<div class="section-header"><h2>🏠 Admin Dashboard Overview</h2></div>', unsafe_allow_html=True)
        
        # Key metrics
        self._render_metrics()
        
        # Quick actions
        self._render_quick_actions()
        
        # Recent activity
        self._render_recent_activity()
        
        # System health
        self._render_system_health()
    
    def _render_metrics(self):
        """Render key metrics cards."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Users", "142", "+8 today")
        with col2:
            st.metric("📊 Jobs Processed", "1,234", "+15 today")
        with col3:
            st.metric("🤖 AI Enrichments", "89", "+12 today")
        with col4:
            st.metric("⚡ System Health", "98%", "+2%")
    
    def _render_quick_actions(self):
        """Render quick action buttons."""
        st.subheader("🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🤖 Run AI Analysis", use_container_width=True):
                st.success("AI analysis initiated successfully!")
        
        with col2:
            if st.button("📊 Generate Report", use_container_width=True):
                st.success("Report generation started!")
        
        with col3:
            if st.button("🔄 Sync User Portal", use_container_width=True):
                st.success("User portal sync completed!")
    
    def _render_recent_activity(self):
        """Render recent activity feed."""
        st.subheader("📈 Recent Activity")
        
        activity_data = [
            {"Time": "2 min ago", "Activity": "User registered", "Details": "jane.doe@company.com", "Status": "✅"},
            {"Time": "5 min ago", "Activity": "Data parsing completed", "Details": "145 files processed", "Status": "✅"},
            {"Time": "8 min ago", "Activity": "AI enrichment", "Details": "89 profiles enriched", "Status": "✅"},
            {"Time": "12 min ago", "Activity": "System backup", "Details": "Full backup completed", "Status": "✅"},
        ]
        
        for activity in activity_data:
            st.write(f"{activity['Status']} **{activity['Activity']}** - {activity['Details']} - _{activity['Time']}_")
    
    def _render_system_health(self):
        """Render system health overview."""
        st.subheader("🔧 System Health")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.progress(0.98, text="System Performance: 98%")
            st.progress(0.85, text="Memory Usage: 85%")
        
        with col2:
            st.progress(0.92, text="Database Health: 92%")
            st.progress(0.76, text="API Response Time: 76ms")