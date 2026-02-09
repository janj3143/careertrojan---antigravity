"""
Enhanced UI Components System - Phase 2 User Experience Improvements
=================================================================

Comprehensive shared UI components that dramatically improve user experience
across all IntelliCV portals through consistent, modern, and interactive elements.

Features:
- Consistent visual language across all portals
- Enhanced user interaction patterns
- Responsive design components
- Professional styling and animations
- Improved accessibility and usability
- Reduced cognitive load through familiar patterns

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
# ENHANCED CSS SYSTEM FOR PROFESSIONAL UI
# =============================================================================

def inject_enhanced_ui_css():
    """Inject comprehensive CSS for professional, consistent UI across all portals"""
    st.markdown("""
    <style>
    /* Global Enhanced UI Styles */
    .intellicv-main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
        color: white;
    }

    .intellicv-main-header::before {
        content: '⬢⬡⬢⬡⬢\\A⬡⬢⬡⬢⬡\\A⬢⬡⬢⬡⬢';
        white-space: pre;
        position: absolute;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
        opacity: 0.15;
        z-index: 1;
        font-size: 60px;
        line-height: 0.8;
        color: white;
    }

    .intellicv-section-header {
        background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        border-left: 5px solid #2196f3;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    .intellicv-section-header h2 {
        margin: 0;
        color: #1565c0;
        font-size: 1.8rem;
    }

    .intellicv-section-header p {
        margin: 0.5rem 0 0 0;
        color: #666;
        font-size: 1rem;
    }

    .intellicv-metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .intellicv-metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }

    .intellicv-metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1565c0;
        margin: 0;
    }

    .intellicv-metric-label {
        font-size: 1rem;
        color: #666;
        margin: 0.5rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .intellicv-status-active {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #4caf50;
        color: white;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .intellicv-status-warning {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #ff9800;
        color: white;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .intellicv-status-error {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #f44336;
        color: white;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .intellicv-status-inactive {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        background: #9e9e9e;
        color: white;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .intellicv-action-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .intellicv-action-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .intellicv-data-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }

    .intellicv-data-table th {
        background: #f8f9fa;
        padding: 1rem;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #dee2e6;
    }

    .intellicv-data-table td {
        padding: 1rem;
        border-bottom: 1px solid #dee2e6;
    }

    .intellicv-progress-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .intellicv-alert-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #155724;
    }

    .intellicv-alert-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }

    .intellicv-alert-error {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
    }

    .intellicv-alert-info {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }

    .intellicv-tab-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        overflow: hidden;
        margin: 2rem 0;
    }

    .intellicv-upload-zone {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 3rem;
        text-align: center;
        background: #f8f9ff;
        margin: 2rem 0;
        transition: all 0.2s ease;
    }

    .intellicv-upload-zone:hover {
        border-color: #764ba2;
        background: #f0f4ff;
    }

    .intellicv-sidebar-enhanced {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }

    /* Animation classes */
    .intellicv-fade-in {
        animation: intellicvFadeIn 0.5s ease-in;
    }

    @keyframes intellicvFadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .intellicv-pulse {
        animation: intellicvPulse 2s infinite;
    }

    @keyframes intellicvPulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# ENHANCED HEADER COMPONENTS
# =============================================================================

def render_main_header(title: str, subtitle: str = "", portal_type: str = "admin"):
    """Render enhanced main header with professional styling"""
    inject_enhanced_ui_css()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    portal_icons = {
        "admin": "🛡️",
        "user": "👤", 
        "backend": "⚙️"
    }
    
    icon = portal_icons.get(portal_type, "🏠")
    
    st.markdown(f"""
    <div class="intellicv-main-header intellicv-fade-in">
        <h1 style="margin: 0; font-size: 2.5rem; position: relative; z-index: 2;">
            {icon} {title}
        </h1>
        {f'<p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.2rem; position: relative; z-index: 2;">{subtitle}</p>' if subtitle else ''}
        <p style="margin: 0.5rem 0 0 0; opacity: 0.7; font-size: 1rem; position: relative; z-index: 2;">
            Welcome back • Last updated: {current_time}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_section_header(title: str, description: str = "", icon: str = "📊"):
    """Render enhanced section header with consistent styling"""
    inject_enhanced_ui_css()
    
    st.markdown(f"""
    <div class="intellicv-section-header intellicv-fade-in">
        <h2>{icon} {title}</h2>
        {f'<p>{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# METRICS AND DASHBOARD COMPONENTS
# =============================================================================

def render_metrics_row(metrics: List[Dict[str, Union[str, int, float]]]):
    """Render enhanced metrics row with professional cards"""
    inject_enhanced_ui_css()
    
    if not metrics:
        return
    
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            value = metric.get('value', '0')
            label = metric.get('label', 'Metric')
            delta = metric.get('delta', '')
            delta_color = metric.get('delta_color', 'normal')
            
            # Create enhanced metric card
            st.markdown(f"""
            <div class="intellicv-metric-card intellicv-fade-in">
                <div class="intellicv-metric-value">{value}</div>
                <div class="intellicv-metric-label">{label}</div>
                {f'<div style="color: {"green" if delta_color == "normal" else delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>' if delta else ''}
            </div>
            """, unsafe_allow_html=True)

def render_status_indicator(status: str, label: str = ""):
    """Render enhanced status indicator with consistent styling"""
    inject_enhanced_ui_css()
    
    status_classes = {
        'active': 'intellicv-status-active',
        'running': 'intellicv-status-active',
        'online': 'intellicv-status-active',
        'success': 'intellicv-status-active',
        'warning': 'intellicv-status-warning',
        'pending': 'intellicv-status-warning',
        'error': 'intellicv-status-error',
        'failed': 'intellicv-status-error',
        'offline': 'intellicv-status-error',
        'inactive': 'intellicv-status-inactive',
        'disabled': 'intellicv-status-inactive'
    }
    
    status_lower = status.lower()
    css_class = status_classes.get(status_lower, 'intellicv-status-inactive')
    
    status_html = f'<span class="{css_class}">{status}</span>'
    
    if label:
        st.markdown(f"**{label}:** {status_html}", unsafe_allow_html=True)
    else:
        st.markdown(status_html, unsafe_allow_html=True)

# =============================================================================
# INTERACTIVE COMPONENTS
# =============================================================================

def render_action_buttons(actions: List[Dict[str, Any]]) -> Dict[str, bool]:
    """Render enhanced action buttons with improved UX"""
    inject_enhanced_ui_css()
    
    if not actions:
        return {}
    
    results = {}
    cols = st.columns(len(actions))
    
    for i, action in enumerate(actions):
        with cols[i]:
            label = action.get('label', f'Action {i+1}')
            key = action.get('key', f'action_{i}')
            icon = action.get('icon', '🔧')
            disabled = action.get('disabled', False)
            help_text = action.get('help', '')
            
            # Use Streamlit button with enhanced styling
            if st.button(
                f"{icon} {label}",
                key=key,
                disabled=disabled,
                help=help_text,
                use_container_width=True
            ):
                results[key] = True
            else:
                results[key] = False
    
    return results

def render_enhanced_file_uploader(
    label: str,
    accepted_types: List[str] = None,
    max_size_mb: int = 10,
    multiple: bool = False,
    help_text: str = ""
):
    """Render enhanced file uploader with professional styling"""
    inject_enhanced_ui_css()
    
    if accepted_types is None:
        accepted_types = ["pdf", "docx", "txt"]
    
    st.markdown(f"""
    <div class="intellicv-upload-zone">
        <h3 style="margin: 0 0 1rem 0; color: #667eea;">📁 {label}</h3>
        <p style="color: #666; margin: 0;">
            Drag and drop files here, or click to browse<br>
            Supported formats: {', '.join(accepted_types)}<br>
            Maximum size: {max_size_mb}MB
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        label,
        type=accepted_types,
        accept_multiple_files=multiple,
        help=help_text,
        label_visibility="collapsed"
    )
    
    return uploaded_file

# =============================================================================
# DATA VISUALIZATION COMPONENTS
# =============================================================================

def render_enhanced_data_table(
    data: List[Dict[str, Any]], 
    columns: List[str] = None,
    searchable: bool = True,
    sortable: bool = True,
    max_height: int = 400
):
    """Render enhanced data table with improved functionality"""
    inject_enhanced_ui_css()
    
    if not data:
        st.info("No data available to display.")
        return
    
    df = pd.DataFrame(data)
    
    if columns:
        # Filter to specified columns if they exist
        available_columns = [col for col in columns if col in df.columns]
        if available_columns:
            df = df[available_columns]
    
    # Add search functionality
    if searchable and not df.empty:
        search_term = st.text_input("🔍 Search table data", key=f"search_{id(data)}")
        if search_term:
            # Search across all string columns
            mask = df.astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            df = df[mask]
    
    # Display table with enhanced styling
    if not df.empty:
        st.markdown('<div class="intellicv-data-table">', unsafe_allow_html=True)
        st.dataframe(
            df, 
            use_container_width=True,
            height=max_height
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add row count info
        st.caption(f"Displaying {len(df)} rows")
    else:
        st.info("No data matches your search criteria.")

def render_enhanced_chart(
    chart_type: str,
    data: pd.DataFrame,
    title: str = "",
    x_column: str = None,
    y_column: str = None,
    **kwargs
):
    """Render enhanced charts with professional styling"""
    inject_enhanced_ui_css()
    
    if data.empty:
        st.warning("No data available for chart visualization.")
        return
    
    # Chart container with professional styling
    st.markdown(f"""
    <div class="intellicv-tab-container">
        <div style="padding: 1rem;">
            <h3 style="margin: 0 0 1rem 0; color: #1565c0;">📈 {title}</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        if chart_type.lower() == 'line':
            fig = px.line(data, x=x_column, y=y_column, title=title, **kwargs)
        elif chart_type.lower() == 'bar':
            fig = px.bar(data, x=x_column, y=y_column, title=title, **kwargs)
        elif chart_type.lower() == 'scatter':
            fig = px.scatter(data, x=x_column, y=y_column, title=title, **kwargs)
        elif chart_type.lower() == 'pie':
            fig = px.pie(data, names=x_column, values=y_column, title=title, **kwargs)
        else:
            st.error(f"Unsupported chart type: {chart_type}")
            return
        
        # Apply professional styling
        fig.update_layout(
            font_family="Arial, sans-serif",
            title_font_size=16,
            title_font_color="#1565c0",
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error rendering chart: {str(e)}")

# =============================================================================
# ALERT AND FEEDBACK COMPONENTS
# =============================================================================

def render_enhanced_alert(message: str, alert_type: str = "info", dismissible: bool = False):
    """Render enhanced alert with professional styling"""
    inject_enhanced_ui_css()
    
    alert_classes = {
        'success': 'intellicv-alert-success',
        'warning': 'intellicv-alert-warning',
        'error': 'intellicv-alert-error',
        'info': 'intellicv-alert-info'
    }
    
    alert_icons = {
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'info': 'ℹ️'
    }
    
    css_class = alert_classes.get(alert_type, 'intellicv-alert-info')
    icon = alert_icons.get(alert_type, 'ℹ️')
    
    st.markdown(f"""
    <div class="{css_class} intellicv-fade-in">
        <strong>{icon} {alert_type.title()}:</strong> {message}
    </div>
    """, unsafe_allow_html=True)

def render_progress_indicator(progress: float, label: str = "", show_percentage: bool = True):
    """Render enhanced progress indicator"""
    inject_enhanced_ui_css()
    
    progress = max(0, min(100, progress))  # Clamp between 0 and 100
    
    st.markdown(f"""
    <div class="intellicv-progress-container intellicv-fade-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #495057;">{label}</span>
            {f'<span style="color: #667eea; font-weight: 600;">{progress:.1f}%</span>' if show_percentage else ''}
        </div>
        <div style="background: #e9ecef; border-radius: 10px; height: 8px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {progress}%; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# LAYOUT AND NAVIGATION COMPONENTS
# =============================================================================

def render_enhanced_tabs(tabs: List[Dict[str, Any]], default_tab: int = 0):
    """Render enhanced tabs with improved styling"""
    inject_enhanced_ui_css()
    
    if not tabs:
        return None
    
    tab_labels = [tab.get('label', f'Tab {i+1}') for i, tab in enumerate(tabs)]
    
    # Create Streamlit tabs
    tab_objects = st.tabs(tab_labels)
    
    # Render content for each tab
    for i, (tab_obj, tab_config) in enumerate(zip(tab_objects, tabs)):
        with tab_obj:
            content_func = tab_config.get('content')
            if callable(content_func):
                content_func()
            elif isinstance(content_func, str):
                st.markdown(content_func)
            else:
                st.info(f"Content for {tab_labels[i]} tab")

def render_enhanced_sidebar_content(title: str = "Navigation", sections: List[Dict[str, Any]] = None):
    """Render enhanced sidebar content with professional styling"""
    inject_enhanced_ui_css()
    
    st.sidebar.markdown(f"""
    <div class="intellicv-sidebar-enhanced">
        <h2 style="margin: 0 0 1rem 0; color: #1565c0;">🧭 {title}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if sections:
        for section in sections:
            section_title = section.get('title', 'Section')
            section_items = section.get('items', [])
            
            st.sidebar.markdown(f"**{section_title}**")
            
            for item in section_items:
                label = item.get('label', 'Item')
                page = item.get('page', '')
                icon = item.get('icon', '📄')
                
                if page and st.sidebar.button(f"{icon} {label}", key=f"nav_{page}"):
                    st.switch_page(page)
            
            st.sidebar.markdown("---")

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_component_theme_colors():
    """Get consistent theme colors for components"""
    return {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#4caf50',
        'warning': '#ff9800',
        'error': '#f44336',
        'info': '#2196f3',
        'light': '#f8f9fa',
        'dark': '#495057'
    }

def format_display_value(value: Any, format_type: str = "auto") -> str:
    """Format values for consistent display across components"""
    if value is None:
        return "N/A"
    
    if format_type == "number" and isinstance(value, (int, float)):
        return f"{value:,}"
    elif format_type == "percentage" and isinstance(value, (int, float)):
        return f"{value:.1f}%"
    elif format_type == "currency" and isinstance(value, (int, float)):
        return f"${value:,.2f}"
    elif format_type == "datetime" and isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    else:
        return str(value)

# =============================================================================
# EXPORT ALL FUNCTIONS
# =============================================================================

__all__ = [
    'inject_enhanced_ui_css',
    'render_main_header',
    'render_section_header',
    'render_metrics_row',
    'render_status_indicator',
    'render_action_buttons',
    'render_enhanced_file_uploader',
    'render_enhanced_data_table',
    'render_enhanced_chart',
    'render_enhanced_alert',
    'render_progress_indicator',
    'render_enhanced_tabs',
    'render_enhanced_sidebar_content',
    'get_component_theme_colors',
    'format_display_value'
]