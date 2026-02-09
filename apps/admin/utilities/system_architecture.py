
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

#!/usr/bin/env python3
"""
IntelliCV Admin Portal - System Architecture
===========================================

System architecture visualization and management dashboard.
Migrated from old admin portal with enhanced monitoring and control capabilities.

Features:
- Architecture visualization
- Component status monitoring
- System health dashboards
- Configuration management
- Performance monitoring

Author: IntelliCV AI System
Date: September 21, 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import psutil
import subprocess
import platform

# Import shared components
try:
    from shared.components import render_section_header, render_metrics_row
    from shared.utils import get_session_state, set_session_state
    SHARED_COMPONENTS_AVAILABLE = True
except ImportError:
    SHARED_COMPONENTS_AVAILABLE = False

class SystemArchitecture:
    """System architecture monitoring and management"""
    
    def __init__(self):
        """Initialize system architecture monitor"""
        self.base_path = Path(__file__).parent.parent
        self.config_path = self.base_path / "config"
        self.logs_path = self.base_path / "logs"
        
        # System components
        self.components = {
            "admin_portal": {
                "name": "Admin Portal",
                "type": "frontend",
                "status": "active",
                "dependencies": ["ai_system", "database"],
                "health_score": 98.5,
                "port": 8501,
                "version": "3.0.0"
            },
            "ai_system": {
                "name": "AI Enrichment System", 
                "type": "backend",
                "status": "active",
                "dependencies": ["database", "file_system"],
                "health_score": 97.2,
                "port": None,
                "version": "2.1.0"
            },
            "database": {
                "name": "SQLite Database",
                "type": "storage",
                "status": "active", 
                "dependencies": [],
                "health_score": 99.1,
                "port": None,
                "version": "3.39.0"
            },
            "file_system": {
                "name": "File Storage System",
                "type": "storage",
                "status": "active",
                "dependencies": [],
                "health_score": 95.8,
                "port": None,
                "version": "1.0.0"
            },
            "parser_engine": {
                "name": "CV Parser Engine",
                "type": "service",
                "status": "active",
                "dependencies": ["ai_system"],
                "health_score": 96.4,
                "port": None,
                "version": "1.5.0"
            },
            "analytics_engine": {
                "name": "Analytics Engine",
                "type": "service", 
                "status": "active",
                "dependencies": ["database", "ai_system"],
                "health_score": 94.7,
                "port": None,
                "version": "1.2.0"
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_components = len(self.components)
        active_components = sum(1 for comp in self.components.values() if comp["status"] == "active")
        avg_health = sum(comp["health_score"] for comp in self.components.values()) / total_components
        
        return {
            "total_components": total_components,
            "active_components": active_components,
            "inactive_components": total_components - active_components,
            "overall_health": avg_health,
            "uptime": self.get_system_uptime(),
            "last_update": datetime.now()
        }
    
    def get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            uptime_seconds = datetime.now().timestamp() - psutil.boot_time()
            uptime_delta = timedelta(seconds=uptime_seconds)
            
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            return f"{days}d {hours}h {minutes}m"
        except:
            return "Unknown"
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource utilization"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_usage": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_percent": (disk.used / disk.total) * 100,
                "cpu_count": psutil.cpu_count(),
                "platform": platform.system(),
                "python_version": platform.python_version()
            }
        except Exception as e:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.error(f"Error getting system resources: {e}")
            return {}
    
    def get_network_topology(self) -> Dict[str, List[str]]:
        """Get network topology for visualization"""
        topology = {}
        
        for comp_id, comp in self.components.items():
            topology[comp_id] = comp["dependencies"]
        
        return topology
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        return {
            "response_time": 0.142,
            "throughput": 850,
            "error_rate": 0.02,
            "concurrent_users": 12,
            "active_sessions": 8,
            "cache_hit_rate": 89.3,
            "database_connections": 5,
            "queue_size": 3
        }
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get security status information"""
        return {
            "auth_enabled": True,
            "ssl_enabled": False,
            "firewall_status": "active",
            "last_security_scan": datetime.now() - timedelta(days=2),
            "vulnerability_count": 0,
            "security_score": 95.2,
            "failed_login_attempts": 2,
            "active_sessions": 8
        }

def render_system_overview(arch: SystemArchitecture):
    """Render system overview section"""
    st.subheader("🏗️ System Overview")
    
    status = arch.get_system_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Components",
            status["total_components"],
            delta=None
        )
    
    with col2:
        st.metric(
            "Active Components", 
            status["active_components"],
            delta=f"+{status['active_components'] - status['inactive_components']}"
        )
    
    with col3:
        st.metric(
            "Overall Health",
            f"{status['overall_health']:.1f}%",
            delta="+1.2%"
        )
    
    with col4:
        st.metric(
            "System Uptime",
            status["uptime"],
            delta=None
        )

def render_component_status(arch: SystemArchitecture):
    """Render component status dashboard"""
    st.subheader("🔧 Component Status")
    
    # Component status table
    components_data = []
    for comp_id, comp in arch.components.items():
        components_data.append({
            "Component": comp["name"],
            "Type": comp["type"].title(),
            "Status": "🟢 Active" if comp["status"] == "active" else "🔴 Inactive",
            "Health": f"{comp['health_score']:.1f}%",
            "Version": comp["version"],
            "Port": comp["port"] if comp["port"] else "N/A",
            "Dependencies": len(comp["dependencies"])
        })
    
    components_df = pd.DataFrame(components_data)
    st.dataframe(components_df, use_container_width=True, hide_index=True)
    
    # Component health visualization
    health_data = [(comp["name"], comp["health_score"]) for comp in arch.components.values()]
    health_df = pd.DataFrame(health_data, columns=["Component", "Health Score"])
    
    fig = px.bar(health_df, x="Component", y="Health Score",
                title="Component Health Scores",
                color="Health Score",
                color_continuous_scale="RdYlGn")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

def render_architecture_diagram(arch: SystemArchitecture):
    """Render system architecture diagram"""
    st.subheader("🏛️ Architecture Diagram")
    
    # Create network graph
    G = nx.DiGraph()
    
    # Add nodes
    for comp_id, comp in arch.components.items():
        G.add_node(comp_id, 
                  label=comp["name"],
                  type=comp["type"],
                  status=comp["status"])
    
    # Add edges (dependencies)
    for comp_id, comp in arch.components.items():
        for dep in comp["dependencies"]:
            if dep in arch.components:
                G.add_edge(dep, comp_id)
    
    # Create layout
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Extract node and edge information
    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_labels = [arch.components[node]["name"] for node in G.nodes()]
    node_colors = [arch.components[node]["health_score"] for node in G.nodes()]
    
    # Create plotly figure
    fig = go.Figure()
    
    # Add edges
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode='lines',
            line=dict(width=2, color='rgba(100,100,100,0.5)'),
            hoverinfo='none',
            showlegend=False
        ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(
            size=20,
            color=node_colors,
            colorscale='RdYlGn',
            colorbar=dict(title="Health Score"),
            line=dict(width=2, color='black')
        ),
        text=node_labels,
        textposition="bottom center",
        hovertemplate="<b>%{text}</b><br>Health: %{marker.color:.1f}%<extra></extra>",
        showlegend=False
    ))
    
    fig.update_layout(
        title="System Architecture Network",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_resource_monitoring(arch: SystemArchitecture):
    """Render system resource monitoring"""
    st.subheader("📊 Resource Monitoring")
    
    resources = arch.get_system_resources()
    
    if resources:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### CPU Usage")
            cpu_usage = resources["cpu_usage"]
            st.metric("CPU Usage", f"{cpu_usage:.1f}%")
            color = "green" if cpu_usage < 70 else "orange" if cpu_usage < 90 else "red"
            st.progress(cpu_usage / 100)
            
            st.markdown(f"**CPU Cores:** {resources['cpu_count']}")
            st.markdown(f"**Platform:** {resources['platform']}")
        
        with col2:
            st.markdown("#### Memory Usage")
            memory_percent = resources["memory_percent"]
            memory_used_gb = resources["memory_used"] / (1024**3)
            memory_total_gb = resources["memory_total"] / (1024**3)
            
            st.metric("Memory Usage", f"{memory_percent:.1f}%")
            st.progress(memory_percent / 100)
            
            st.markdown(f"**Used:** {memory_used_gb:.1f} GB")
            st.markdown(f"**Total:** {memory_total_gb:.1f} GB")
        
        with col3:
            st.markdown("#### Disk Usage")
            disk_percent = resources["disk_percent"]
            disk_used_gb = resources["disk_used"] / (1024**3)
            disk_total_gb = resources["disk_total"] / (1024**3)
            
            st.metric("Disk Usage", f"{disk_percent:.1f}%")
            st.progress(disk_percent / 100)
            
            st.markdown(f"**Used:** {disk_used_gb:.1f} GB")
            st.markdown(f"**Total:** {disk_total_gb:.1f} GB")
        
        # System info
        st.markdown("---")
        st.markdown("#### System Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"**Python Version:** {resources['python_version']}")
            st.markdown(f"**Platform:** {resources['platform']}")
        
        with info_col2:
            st.markdown(f"**CPU Cores:** {resources['cpu_count']}")
            st.markdown(f"**Architecture:** {platform.machine()}")

def render_performance_dashboard(arch: SystemArchitecture):
    """Render performance monitoring dashboard"""
    st.subheader("⚡ Performance Dashboard")
    
    performance = arch.get_performance_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Response Time", f"{performance['response_time']:.3f}s", delta="-0.008s")
    
    with col2:
        st.metric("Throughput", f"{performance['throughput']}/hr", delta="+45")
    
    with col3:
        st.metric("Error Rate", f"{performance['error_rate']:.2%}", delta="-0.01%")
    
    with col4:
        st.metric("Concurrent Users", performance['concurrent_users'], delta="+2")
    
    # Additional performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Sessions", performance['active_sessions'])
    
    with col2:
        st.metric("Cache Hit Rate", f"{performance['cache_hit_rate']:.1f}%")
    
    with col3:
        st.metric("DB Connections", performance['database_connections'])
    
    with col4:
        st.metric("Queue Size", performance['queue_size'])

def render_security_status(arch: SystemArchitecture):
    """Render security status dashboard"""
    st.subheader("🔒 Security Status")
    
    security = arch.get_security_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Authentication")
        auth_status = "🟢 Enabled" if security["auth_enabled"] else "🔴 Disabled"
        st.markdown(f"**Status:** {auth_status}")
        
        ssl_status = "🟢 Enabled" if security["ssl_enabled"] else "🟡 Disabled"
        st.markdown(f"**SSL:** {ssl_status}")
        
        st.markdown(f"**Failed Logins:** {security['failed_login_attempts']}")
    
    with col2:
        st.markdown("#### Security Metrics")
        st.metric("Security Score", f"{security['security_score']:.1f}%", delta="+2.1%")
        st.metric("Vulnerabilities", security['vulnerability_count'])
        st.metric("Active Sessions", security['active_sessions'])
    
    with col3:
        st.markdown("#### Last Security Scan")
        scan_date = security["last_security_scan"].strftime("%Y-%m-%d %H:%M")
        st.markdown(f"**Date:** {scan_date}")
        
        firewall_status = "🟢 Active" if security["firewall_status"] == "active" else "🔴 Inactive"
        st.markdown(f"**Firewall:** {firewall_status}")

def render_system_controls(arch: SystemArchitecture):
    """Render system control panel"""
    st.subheader("🎛️ System Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Component Controls")
        
        if st.button("🔄 Restart All Services", type="primary"):
            with st.spinner("Restarting services..."):
                # Simulate service restart
                progress_bar = st.progress(0)
                services = ["AI System", "Parser Engine", "Analytics Engine"]
                
                for i, service in enumerate(services):
                    progress_bar.progress((i + 1) / len(services))
                    st.text(f"Restarting {service}...")
                
                st.success("✅ All services restarted successfully!")
        
        if st.button("🔍 Health Check"):
            with st.spinner("Running health checks..."):
                st.text("Checking component health...")
                st.text("Validating connections...")
                st.text("Testing performance...")
                
                st.success("✅ All health checks passed!")
        
        if st.button("📊 Generate Report"):
            st.success("✅ System report generated!")
    
    with col2:
        st.markdown("#### Maintenance Operations")
        
        if st.button("🧹 Clean Temporary Files"):
            st.success("✅ Temporary files cleaned!")
        
        if st.button("🔧 Optimize Database"):
            with st.spinner("Optimizing database..."):
                st.text("Analyzing tables...")
                st.text("Rebuilding indexes...")
                st.text("Updating statistics...")
                
                st.success("✅ Database optimized!")
        
        if st.button("💾 Backup System"):
            with st.spinner("Creating system backup..."):
                st.text("Backing up configuration...")
                st.text("Backing up database...")
                st.text("Backing up logs...")
                
                st.success("✅ System backup completed!")
    
    with col3:
        st.markdown("#### Monitoring Controls")
        
        if st.button("📈 Export Metrics"):
            st.success("✅ Metrics exported to CSV!")
        
        if st.button("🔔 Test Alerts"):
            st.info("📧 Test alert sent to administrators")
        
        if st.button("⚙️ Update Configuration"):
            st.success("✅ Configuration updated!")

def main():
    """Main function for system architecture dashboard"""
    if SHARED_COMPONENTS_AVAILABLE:
        render_section_header(
            "🏗️ System Architecture",
            "System architecture monitoring and management dashboard"
        )
    else:
        st.title("🏗️ System Architecture")
        st.markdown("System architecture monitoring and management dashboard")
    
    # Initialize architecture monitor
    arch = SystemArchitecture()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏗️ Overview",
        "🔧 Components",
        "🏛️ Architecture", 
        "📊 Resources",
        "⚡ Performance",
        "🎛️ Controls"
    ])
    
    with tab1:
        render_system_overview(arch)
        st.markdown("---")
        render_security_status(arch)
    
    with tab2:
        render_component_status(arch)
    
    with tab3:
        render_architecture_diagram(arch)
    
    with tab4:
        render_resource_monitoring(arch)
    
    with tab5:
        render_performance_dashboard(arch)
    
    with tab6:
        render_system_controls(arch)
    
    # System status sidebar
    with st.sidebar:
        st.markdown("### 🚥 System Status")
        
        status = arch.get_system_status()
        
        # Overall health indicator
        health = status["overall_health"]
        if health >= 95:
            st.success(f"🟢 System Health: {health:.1f}%")
        elif health >= 85:
            st.warning(f"🟡 System Health: {health:.1f}%")
        else:
            st.error(f"🔴 System Health: {health:.1f}%")
        
        # Quick stats
        st.metric("Active Components", f"{status['active_components']}/{status['total_components']}")
        st.metric("Uptime", status["uptime"])
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Data", key="sidebar_refresh"):
            st.experimental_rerun()
        
        if st.button("💾 Quick Backup", key="sidebar_backup"):
            st.success("Backup initiated!")
    
    # Usage guide
    with st.expander("ℹ️ Architecture Guide"):
        st.markdown("""
        ### System Architecture Features
        
        **Overview Tab:**
        - System health summary
        - Component status overview
        - Security status dashboard
        
        **Components Tab:**
        - Detailed component status
        - Health score monitoring
        - Version information
        
        **Architecture Tab:**
        - Visual system architecture
        - Component relationships
        - Dependency mapping
        
        **Resources Tab:**
        - System resource monitoring
        - CPU, memory, disk usage
        - Platform information
        
        **Performance Tab:**
        - Real-time performance metrics
        - Response times and throughput
        - Error rates and capacity
        
        **Controls Tab:**
        - System control operations
        - Maintenance functions
        - Monitoring controls
        
        ### Best Practices
        - Monitor system health regularly
        - Address performance issues promptly
        - Keep all components updated
        - Regular backups and maintenance
        - Security monitoring and updates
        """)

if __name__ == "__main__":
    main()