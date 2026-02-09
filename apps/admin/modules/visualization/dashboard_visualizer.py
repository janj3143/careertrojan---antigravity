
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
IntelliCV Dashboard Visualization Integration
===========================================

Comprehensive visualization module that integrates all visual components
with the admin dashboard and provides a unified interface for charts,
graphs, plots, and interactive visualizations.

Author: IntelliCV Admin Portal
Purpose: Unified visualization interface for dashboard components
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    sns = None

try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
    WordCloud = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import base64
from io import BytesIO
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Set default style
plt.style.use('default')
if SEABORN_AVAILABLE:
    sns.set_palette("husl")

class DashboardVisualizer:
    """Main visualization class for the IntelliCV dashboard"""
    
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff7f0e',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }
        
        self.plotly_theme = 'plotly_white'
        
    def render_overview_dashboard(self, data: Dict[str, Any]):
        """Render the main overview dashboard with key metrics"""
        
        # Activate Enhanced Sidebar
        if ENHANCED_SIDEBAR_AVAILABLE:
            inject_sidebar_css()
            render_enhanced_sidebar()

        st.markdown("### 📊 System Overview Dashboard")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Documents", 
                data.get('total_documents', 0),
                delta=data.get('documents_delta', 0)
            )
        
        with col2:
            st.metric(
                "Processed Today", 
                data.get('processed_today', 0),
                delta=data.get('processed_delta', 0)
            )
        
        with col3:
            st.metric(
                "Success Rate", 
                f"{data.get('success_rate', 0):.1f}%",
                delta=f"{data.get('success_delta', 0):.1f}%"
            )
        
        with col4:
            st.metric(
                "Active Users", 
                data.get('active_users', 0),
                delta=data.get('users_delta', 0)
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_processing_timeline(data.get('timeline_data', {}))
        
        with col2:
            self.render_document_types_pie(data.get('document_types', {}))
    
    def render_processing_timeline(self, timeline_data: Dict):
        """Render processing activity timeline"""
        if not timeline_data:
            # Generate sample data
            dates = pd.date_range(start='2025-09-01', end='2025-09-21', freq='D')
            timeline_data = {
                'dates': dates.strftime('%Y-%m-%d').tolist(),
                'processed': np.random.randint(10, 100, len(dates)).tolist(),
                'success': np.random.randint(8, 95, len(dates)).tolist()
            }
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=timeline_data['dates'],
            y=timeline_data['processed'],
            mode='lines+markers',
            name='Documents Processed',
            line=dict(color=self.colors['primary'], width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=timeline_data['dates'],
            y=timeline_data['success'],
            mode='lines+markers',
            name='Successfully Processed',
            line=dict(color=self.colors['success'], width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="📈 Processing Activity Timeline",
            xaxis_title="Date",
            yaxis_title="Number of Documents",
            template=self.plotly_theme,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_document_types_pie(self, document_types: Dict):
        """Render document types distribution pie chart"""
        if not document_types:
            # Generate sample data
            document_types = {
                'PDF': 45,
                'DOCX': 30,
                'DOC': 15,
                'TXT': 8,
                'Others': 2
            }
        
        fig = go.Figure(data=[go.Pie(
            labels=list(document_types.keys()),
            values=list(document_types.values()),
            hole=0.4,
            textinfo='label+percent',
            textposition='outside',
            marker=dict(colors=px.colors.qualitative.Set3)
        )])
        
        fig.update_layout(
            title="📄 Document Types Distribution",
            template=self.plotly_theme,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_analytics_dashboard(self, analytics_data: Dict[str, Any]):
        """Render comprehensive analytics dashboard"""
        st.markdown("### 📊 Analytics & Insights Dashboard")
        
        # Create tabs for different analytics views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Performance", "🎯 Success Metrics", "🔍 Data Quality", "🌐 Network Analysis"
        ])
        
        with tab1:
            self.render_performance_analytics(analytics_data.get('performance', {}))
        
        with tab2:
            self.render_success_metrics(analytics_data.get('success_metrics', {}))
        
        with tab3:
            self.render_data_quality_dashboard(analytics_data.get('data_quality', {}))
        
        with tab4:
            self.render_network_analysis(analytics_data.get('network_data', {}))
    
    def render_performance_analytics(self, performance_data: Dict):
        """Render performance analytics charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Processing speed over time
            if not performance_data.get('speed_data'):
                # Generate sample data
                dates = pd.date_range(start='2025-09-01', end='2025-09-21', freq='D')
                speed_data = {
                    'dates': dates.strftime('%Y-%m-%d').tolist(),
                    'avg_processing_time': np.random.uniform(2.0, 8.0, len(dates)).tolist(),
                    'throughput': np.random.randint(50, 200, len(dates)).tolist()
                }
            else:
                speed_data = performance_data['speed_data']
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Average Processing Time (seconds)', 'Documents per Hour'),
                vertical_spacing=0.1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=speed_data['dates'],
                    y=speed_data['avg_processing_time'],
                    mode='lines+markers',
                    name='Avg Processing Time',
                    line=dict(color=self.colors['warning'])
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=speed_data['dates'],
                    y=speed_data['throughput'],
                    mode='lines+markers',
                    name='Throughput',
                    line=dict(color=self.colors['info'])
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                title="⚡ Performance Metrics",
                template=self.plotly_theme,
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Resource utilization
            self.render_resource_utilization(performance_data.get('resources', {}))
    
    def render_resource_utilization(self, resource_data: Dict):
        """Render resource utilization charts"""
        if not resource_data:
            resource_data = {
                'cpu': np.random.uniform(20, 80, 24).tolist(),
                'memory': np.random.uniform(30, 90, 24).tolist(),
                'disk': np.random.uniform(40, 70, 24).tolist(),
                'hours': list(range(24))
            }
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=resource_data['hours'],
            y=resource_data['cpu'],
            mode='lines',
            name='CPU %',
            line=dict(color=self.colors['danger'], width=2),
            fill='tonexty'
        ))
        
        fig.add_trace(go.Scatter(
            x=resource_data['hours'],
            y=resource_data['memory'],
            mode='lines',
            name='Memory %',
            line=dict(color=self.colors['warning'], width=2),
            fill='tonexty'
        ))
        
        fig.add_trace(go.Scatter(
            x=resource_data['hours'],
            y=resource_data['disk'],
            mode='lines',
            name='Disk %',
            line=dict(color=self.colors['info'], width=2)
        ))
        
        fig.update_layout(
            title="💻 Resource Utilization (24h)",
            xaxis_title="Hour of Day",
            yaxis_title="Utilization %",
            template=self.plotly_theme,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_success_metrics(self, success_data: Dict):
        """Render success metrics and quality indicators"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Success rate by document type
            if not success_data.get('by_type'):
                success_data['by_type'] = {
                    'PDF': 95.2,
                    'DOCX': 98.1,
                    'DOC': 87.3,
                    'TXT': 99.5,
                    'Others': 78.9
                }
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(success_data['by_type'].keys()),
                    y=list(success_data['by_type'].values()),
                    marker_color=px.colors.qualitative.Set2,
                    text=[f"{v:.1f}%" for v in success_data['by_type'].values()],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="✅ Success Rate by Document Type",
                xaxis_title="Document Type",
                yaxis_title="Success Rate (%)",
                template=self.plotly_theme,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Error analysis
            if not success_data.get('errors'):
                success_data['errors'] = {
                    'Parsing Errors': 35,
                    'Format Issues': 28,
                    'Corrupted Files': 20,
                    'Timeout': 12,
                    'Other': 5
                }
            
            fig = go.Figure(data=[go.Pie(
                labels=list(success_data['errors'].keys()),
                values=list(success_data['errors'].values()),
                textinfo='label+percent',
                marker=dict(colors=px.colors.qualitative.Pastel)
            )])
            
            fig.update_layout(
                title="❌ Error Distribution",
                template=self.plotly_theme,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def render_data_quality_dashboard(self, quality_data: Dict):
        """Render data quality metrics and indicators"""
        st.markdown("#### 🔍 Data Quality Metrics")
        
        # Quality score indicators
        col1, col2, col3, col4 = st.columns(4)
        
        quality_scores = quality_data.get('scores', {
            'completeness': 87.5,
            'accuracy': 92.3,
            'consistency': 89.1,
            'timeliness': 95.8
        })
        
        with col1:
            self.render_quality_gauge("Completeness", quality_scores['completeness'])
        
        with col2:
            self.render_quality_gauge("Accuracy", quality_scores['accuracy'])
        
        with col3:
            self.render_quality_gauge("Consistency", quality_scores['consistency'])
        
        with col4:
            self.render_quality_gauge("Timeliness", quality_scores['timeliness'])
        
        # Quality trends
        st.markdown("#### 📈 Quality Trends")
        self.render_quality_trends(quality_data.get('trends', {}))
    
    def render_quality_gauge(self, metric_name: str, value: float):
        """Render a quality gauge chart"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': metric_name},
            delta={'reference': 90},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [0, 50], 'color': self.colors['danger']},
                    {'range': [50, 80], 'color': self.colors['warning']},
                    {'range': [80, 100], 'color': self.colors['success']}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(height=250, template=self.plotly_theme)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_quality_trends(self, trends_data: Dict):
        """Render quality trends over time"""
        if not trends_data:
            # Generate sample trend data
            dates = pd.date_range(start='2025-09-01', end='2025-09-21', freq='D')
            trends_data = {
                'dates': dates.strftime('%Y-%m-%d').tolist(),
                'completeness': np.random.uniform(85, 95, len(dates)).tolist(),
                'accuracy': np.random.uniform(88, 96, len(dates)).tolist(),
                'consistency': np.random.uniform(86, 94, len(dates)).tolist()
            }
        
        fig = go.Figure()
        
        for metric, values in trends_data.items():
            if metric != 'dates':
                fig.add_trace(go.Scatter(
                    x=trends_data['dates'],
                    y=values,
                    mode='lines+markers',
                    name=metric.title(),
                    line=dict(width=3)
                ))
        
        fig.update_layout(
            title="📊 Quality Metrics Trends",
            xaxis_title="Date",
            yaxis_title="Quality Score (%)",
            template=self.plotly_theme,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_network_analysis(self, network_data: Dict):
        """Render network analysis and relationship graphs"""
        st.markdown("#### 🌐 Document Relationship Network")
        
        if not network_data:
            # Generate sample network data
            network_data = self.generate_sample_network_data()
        
        # Create network graph
        try:
            import pyvis
            from pyvis.network import Network
            
            # Create pyvis network
            net = Network(height="500px", width="100%", bgcolor="#ffffff")
            
            # Add nodes and edges
            for node in network_data.get('nodes', []):
                net.add_node(
                    node['id'], 
                    label=node['label'], 
                    title=node.get('title', ''),
                    color=node.get('color', self.colors['primary'])
                )
            
            for edge in network_data.get('edges', []):
                net.add_edge(edge['from'], edge['to'], width=edge.get('weight', 1))
            
            # Generate HTML
            net.set_options("""
            var options = {
                "nodes": {
                    "borderWidth": 2,
                    "size": 20,
                    "font": {"size": 12}
                },
                "edges": {
                    "color": {"inherit": true},
                    "smooth": false
                },
                "physics": {
                    "enabled": true,
                    "stabilization": {"iterations": 100}
                }
            }
            """)
            
            # Save and display
            html_path = "temp_network.html"
            net.save_graph(html_path)
            
            # Read and display HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.components.v1.html(html_content, height=500)
            
        except ImportError:
            st.warning("Network visualization requires pyvis. Install with: pip install pyvis")
            self.render_network_fallback(network_data)
    
    def render_network_fallback(self, network_data: Dict):
        """Fallback network visualization using plotly"""
        if not network_data.get('nodes'):
            st.info("No network data available")
            return
        
        # Create simple network plot with plotly
        node_trace = go.Scatter(
            x=[node.get('x', 0) for node in network_data['nodes']],
            y=[node.get('y', 0) for node in network_data['nodes']],
            mode='markers+text',
            text=[node['label'] for node in network_data['nodes']],
            textposition="middle center",
            marker=dict(
                size=20,
                color=self.colors['primary'],
                line=dict(width=2, color='white')
            ),
            name="Documents"
        )
        
        fig = go.Figure(data=[node_trace])
        fig.update_layout(
            title="📊 Document Network (Simplified View)",
            showlegend=False,
            template=self.plotly_theme,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def generate_sample_network_data(self) -> Dict:
        """Generate sample network data for demonstration"""
        nodes = [
            {'id': 1, 'label': 'Resume_001.pdf', 'title': 'Software Engineer Resume', 'x': 0, 'y': 0},
            {'id': 2, 'label': 'Job_Desc_A.txt', 'title': 'Senior Developer Position', 'x': 1, 'y': 1},
            {'id': 3, 'label': 'Resume_002.docx', 'title': 'Data Scientist Resume', 'x': -1, 'y': 1},
            {'id': 4, 'label': 'Company_Profile.pdf', 'title': 'TechCorp Profile', 'x': 0, 'y': 2},
            {'id': 5, 'label': 'Skills_Matrix.xlsx', 'title': 'Skills Comparison', 'x': 2, 'y': 0}
        ]
        
        edges = [
            {'from': 1, 'to': 2, 'weight': 2},
            {'from': 1, 'to': 4, 'weight': 1},
            {'from': 2, 'to': 4, 'weight': 3},
            {'from': 3, 'to': 4, 'weight': 1},
            {'from': 1, 'to': 5, 'weight': 2},
            {'from': 3, 'to': 5, 'weight': 2}
        ]
        
        return {'nodes': nodes, 'edges': edges}
    
    def render_word_cloud(self, text_data: str, title: str = "Word Cloud"):
        """Render word cloud visualization"""
        if not text_data:
            st.info("No text data available for word cloud")
            return
        
        try:
            # Generate word cloud
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='white',
                colormap='viridis',
                max_words=100
            ).generate(text_data)
            
            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(title, fontsize=16, fontweight='bold')
            
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            st.error(f"Error generating word cloud: {e}")
    
    def render_parser_analytics(self, parser_data: Dict):
        """Render parser-specific analytics"""
        st.markdown("### ⚙️ Parser Analytics Dashboard")
        
        # Parser performance metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # Parser success rates
            if not parser_data.get('success_rates'):
                parser_data['success_rates'] = {
                    'PDF Parser': 94.5,
                    'DOCX Parser': 97.8,
                    'Email Parser': 89.2,
                    'Table Parser': 91.6,
                    'NLP Parser': 87.9
                }
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(parser_data['success_rates'].keys()),
                    y=list(parser_data['success_rates'].values()),
                    marker_color=px.colors.qualitative.Plotly,
                    text=[f"{v:.1f}%" for v in parser_data['success_rates'].values()],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="🔧 Parser Success Rates",
                xaxis_title="Parser Type",
                yaxis_title="Success Rate (%)",
                template=self.plotly_theme,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Processing time by parser
            if not parser_data.get('processing_times'):
                parser_data['processing_times'] = {
                    'PDF Parser': 3.2,
                    'DOCX Parser': 1.8,
                    'Email Parser': 2.5,
                    'Table Parser': 4.1,
                    'NLP Parser': 6.7
                }
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(parser_data['processing_times'].keys()),
                    y=list(parser_data['processing_times'].values()),
                    marker_color=px.colors.qualitative.Set1,
                    text=[f"{v:.1f}s" for v in parser_data['processing_times'].values()],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title="⏱️ Average Processing Time",
                xaxis_title="Parser Type",
                yaxis_title="Time (seconds)",
                template=self.plotly_theme,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Global visualizer instance
dashboard_visualizer = DashboardVisualizer()

def render_visualization_section():
    """Main function to render visualization section in dashboard"""
    st.markdown("## 📊 IntelliCV Visualization Dashboard")
    
    # Sample data for demonstration
    sample_data = {
        'total_documents': 1247,
        'documents_delta': 23,
        'processed_today': 89,
        'processed_delta': 12,
        'success_rate': 94.2,
        'success_delta': 1.3,
        'active_users': 34,
        'users_delta': 3
    }
    
    # Render main dashboard
    dashboard_visualizer.render_overview_dashboard(sample_data)
    
    # Additional analytics
    st.markdown("---")
    analytics_data = {
        'performance': {},
        'success_metrics': {},
        'data_quality': {},
        'network_data': {}
    }
    
    dashboard_visualizer.render_analytics_dashboard(analytics_data)
    
    # Parser analytics
    st.markdown("---")
    parser_data = {}
    dashboard_visualizer.render_parser_analytics(parser_data)

if __name__ == "__main__":
    render_visualization_section()