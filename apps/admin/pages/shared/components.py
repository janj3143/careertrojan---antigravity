"""
Shared UI Components for IntelliCV Admin Portal
=============================================

Reusable UI components used across multiple admin modules.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

def render_section_header(title: str, description: str = "", icon: str = "🛡️", show_logo: bool = False) -> None:
    """Render a consistent section header across all admin modules"""
    if show_logo:
        # Create header with logo on the right
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(
                f'<div class="section-header"><h2>{icon} {title}</h2></div>', 
                unsafe_allow_html=True
            )
            if description:
                st.markdown(f'<p style="color: #666; font-size: 1.1rem; margin-top: -10px;">{description}</p>', unsafe_allow_html=True)
        
        with col2:
            # IntelliCV-AI logo on the right
            # Note: Easy to change "IntelliCV-AI" to "IntelliC-CV-AI" or other variations
            logo_text = "IntelliCV-AI"  # Change this line to experiment with different variations
            st.markdown(f"""
            <div style="text-align: right; padding: 10px 0;">
                <div class="intellicv-logo">
                    <div class="intellicv-logo-text">
                        🤖 {logo_text}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Original simple header
        st.markdown(
            f'<div class="section-header"><h2>{icon} {title}</h2></div>', 
            unsafe_allow_html=True
        )
        if description:
            st.markdown(f'<p style="color: #666; font-size: 1.1rem; margin-top: -10px;">{description}</p>', unsafe_allow_html=True)

def render_metrics_row(metrics: List[Tuple[str, str, str]]) -> None:
    """Render a row of metrics with consistent formatting
    
    Args:
        metrics: List of tuples (label, value, delta)
    """
    cols = st.columns(len(metrics))
    for i, (label, value, delta) in enumerate(metrics):
        with cols[i]:
            st.metric(label, value, delta)

def render_status_indicator(status: str, label: str = "") -> str:
    """Render a consistent status indicator"""
    status_colors = {
        "operational": "🟢",
        "warning": "🟡", 
        "error": "🔴",
        "info": "🔵",
        "success": "✅",
        "failed": "❌",
        "pending": "⏳"
    }
    
    indicator = status_colors.get(status.lower(), "⚪")
    return f"{indicator} {label}" if label else indicator

def render_action_buttons(actions: List[Tuple[str, str, bool]]) -> Dict[str, bool]:
    """Render a set of action buttons
    
    Args:
        actions: List of tuples (label, key, is_primary)
        
    Returns:
        Dict mapping action keys to whether they were clicked
    """
    results = {}
    cols = st.columns(len(actions))
    
    for i, (label, key, is_primary) in enumerate(actions):
        with cols[i]:
            button_type = "primary" if is_primary else "secondary"
            results[key] = st.button(label, key=key, type=button_type)
    
    return results

def render_data_table(data: List[Dict[str, Any]], columns: List[str], 
                     actions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Render a data table with optional actions
    
    Args:
        data: List of dictionaries containing row data
        columns: List of column names to display
        actions: Optional list of action button labels
        
    Returns:
        Dict containing any action results
    """
    if not data:
        st.info("No data available")
        return {}
    
    results = {}
    
    for i, row in enumerate(data):
        cols = st.columns(len(columns) + (len(actions) if actions else 0))
        
        # Render data columns
        for j, col in enumerate(columns):
            with cols[j]:
                st.write(row.get(col, ""))
        
        # Render action buttons
        if actions:
            for k, action in enumerate(actions):
                with cols[len(columns) + k]:
                    key = f"{action}_{i}"
                    if st.button(action, key=key):
                        results[key] = {"action": action, "row": i, "data": row}
    
    return results

def render_progress_bar(progress: float, label: str = "") -> None:
    """Render a progress bar with optional label"""
    if label:
        st.write(f"**{label}**")
    st.progress(progress)

def render_chart_container(chart_type: str, data: pd.DataFrame, 
                          title: str = "", **kwargs) -> None:
    """Render a chart in a consistent container
    
    Args:
        chart_type: Type of chart ('line', 'bar', 'area')
        data: DataFrame with chart data
        title: Optional chart title
        **kwargs: Additional chart parameters
    """
    if title:
        st.subheader(title)
    
    chart_functions = {
        'line': st.line_chart,
        'bar': st.bar_chart,
        'area': st.area_chart
    }
    
    chart_func = chart_functions.get(chart_type, st.line_chart)
    chart_func(data, **kwargs)

def render_collapsible_section(title: str, content_func, default_expanded: bool = False):
    """Render a collapsible section with consistent styling"""
    with st.expander(title, expanded=default_expanded):
        content_func()

def render_alert(message: str, alert_type: str = "info") -> None:
    """Render an alert message with consistent styling
    
    Args:
        message: Alert message
        alert_type: Type of alert ('info', 'success', 'warning', 'error')
    """
    alert_functions = {
        'info': st.info,
        'success': st.success,
        'warning': st.warning,
        'error': st.error
    }
    
    alert_func = alert_functions.get(alert_type, st.info)
    alert_func(message)

def render_key_value_pairs(data: Dict[str, Any], columns: int = 2) -> None:
    """Render key-value pairs in columns"""
    items = list(data.items())
    cols = st.columns(columns)
    
    for i, (key, value) in enumerate(items):
        with cols[i % columns]:
            st.write(f"**{key}**: {value}")

# CSS for consistent styling across modules
ADMIN_CSS = """
<style>
.section-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    color: white;
    text-align: center;
}

.section-header h2 {
    margin: 0;
    color: white;
}

.metric-container {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #667eea;
}

.status-good { color: #28a745; }
.status-warning { color: #ffc107; }
.status-error { color: #dc3545; }
.status-info { color: #17a2b8; }
</style>
"""

def inject_admin_css() -> None:
    """Inject consistent CSS styling for admin modules"""
    st.markdown(ADMIN_CSS, unsafe_allow_html=True)