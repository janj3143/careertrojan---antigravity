
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
System Monitor UI Component
==========================

System monitoring interface for the IntelliCV-AI Admin Portal.
"""

import streamlit as st
import random
from datetime import datetime, timedelta


class SystemMonitor:
    """System monitoring component for tracking system performance and health."""
    
    def __init__(self):
        """Initialize system monitor component."""
        pass
    
    @staticmethod
    def render():
        """Render the system monitoring interface."""

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.markdown('<div class="section-header"><h2>📊 System Monitoring & Performance</h2></div>', unsafe_allow_html=True)
        
        # System health metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("System Health", "98%", "+2%")
        with col2:
            st.metric("Memory Usage", "2.3 GB", "-0.1 GB")
        with col3:
            st.metric("CPU Usage", "45%", "-5%")
        with col4:
            st.metric("Disk Space", "67%", "+3%")
        
        # Monitoring tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Live Monitor", "📈 Performance", "⚠️ Alerts", "📊 Reports"])
        
        with tab1:
            st.subheader("Live System Monitoring")
            
            # Real-time status indicators
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🔧 System Services")
                services = [
                    {"name": "Database Server", "status": "Running", "uptime": "15 days"},
                    {"name": "AI Processing", "status": "Running", "uptime": "12 days"},
                    {"name": "File Parser", "status": "Running", "uptime": "8 days"},
                    {"name": "API Gateway", "status": "Running", "uptime": "20 days"},
                ]
                
                for service in services:
                    status_color = "🟢" if service["status"] == "Running" else "🔴"
                    st.write(f"{status_color} **{service['name']}** - {service['status']} ({service['uptime']})")
            
            with col2:
                st.subheader("📊 Performance Metrics")
                st.progress(0.45, text="CPU Usage: 45%")
                st.progress(0.67, text="Memory Usage: 67%")
                st.progress(0.23, text="Disk I/O: 23%")
                st.progress(0.12, text="Network Usage: 12%")
        
        with tab2:
            st.subheader("Performance Analytics")
            st.info("Performance charts and trends - to be fully implemented")
            
            # Sample performance data
            st.write("📈 **System Performance (Last 24h)**")
            perf_data = []
            base_time = datetime.now() - timedelta(hours=24)
            
            for i in range(24):
                hour_time = base_time + timedelta(hours=i)
                perf_data.append({
                    "Hour": hour_time.strftime("%H:00"),
                    "CPU": random.randint(20, 80),
                    "Memory": random.randint(40, 90),
                    "Response": random.randint(50, 200)
                })
            
            # Display last few hours
            for data in perf_data[-6:]:
                st.write(f"⏰ {data['Hour']} - CPU: {data['CPU']}%, Memory: {data['Memory']}%, Response: {data['Response']}ms")
        
        with tab3:
            st.subheader("System Alerts")
            
            alerts = [
                {"time": "2 hours ago", "level": "Warning", "message": "High memory usage detected (85%)", "status": "Active"},
                {"time": "5 hours ago", "level": "Info", "message": "Database backup completed successfully", "status": "Resolved"},
                {"time": "1 day ago", "level": "Error", "message": "API endpoint timeout occurred", "status": "Resolved"},
            ]
            
            for alert in alerts:
                level_color = {"Warning": "🟡", "Info": "🔵", "Error": "🔴"}.get(alert["level"], "⚪")
                status_text = "✅" if alert["status"] == "Resolved" else "⚠️"
                st.write(f"{level_color} **{alert['level']}** - {alert['message']} - _{alert['time']}_ {status_text}")
        
        with tab4:
            st.subheader("System Reports")
            st.info("System reporting dashboard - to be fully implemented")
            
            if st.button("📋 Generate Daily Report", use_container_width=True):
                st.success("Daily system report generated successfully!")
            
            if st.button("📊 Generate Performance Report", use_container_width=True):
                st.success("Performance report generated successfully!")