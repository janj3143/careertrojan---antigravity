"""
IntelliCV-AI Branding and Styling Module
========================================

Provides consistent branding and styling across all admin portal pages.
Includes the hexagon motif and IntelliCV-AI branding.
"""

import streamlit as st
from datetime import datetime

def inject_intellicv_branding():
    """Inject IntelliCV-AI branding and hexagon motif CSS"""
    st.markdown("""
    <style>
    /* IntelliCV-AI Main Header Styling */
    .intellicv-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }

    .intellicv-header::before {
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

    .intellicv-header > * {
        position: relative;
        z-index: 2;
    }

    /* Page-specific hexagon motif (smaller, right-aligned) */
    .page-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }

    .page-header::after {
        content: '⬢⬡⬢';
        position: absolute;
        top: 50%;
        right: 15px;
        transform: translateY(-50%);
        opacity: 0.2;
        z-index: 1;
        font-size: 40px;
        color: white;
    }

    .page-header > * {
        position: relative;
        z-index: 2;
    }

    /* Enhanced metric cards */
    .intellicv-metric-card {
        background: #fff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        position: relative;
    }

    .intellicv-metric-card::before {
        content: '⬡';
        position: absolute;
        top: 10px;
        right: 10px;
        opacity: 0.1;
        font-size: 24px;
        color: #667eea;
    }

    /* Section headers with subtle hexagon */
    .intellicv-section-header {
        background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        border-left: 4px solid #2196f3;
        position: relative;
    }

    .intellicv-section-header::after {
        content: '⬢';
        position: absolute;
        top: 50%;
        right: 15px;
        transform: translateY(-50%);
        opacity: 0.15;
        font-size: 20px;
        color: #2196f3;
    }

    /* Subtle animation for interactive elements */
    .intellicv-metric-card:hover, .intellicv-section-header:hover {
        transform: translateY(-2px);
        transition: all 0.3s ease;
    }
    </style>
    """, unsafe_allow_html=True)

def render_intellicv_main_header():
    """Render the main IntelliCV-AI header for Home page"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(f"""
    <div class="intellicv-header">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">🏠 IntelliCV-AI Admin Portal</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.2rem;">
            Complete Administrative Control Center • AI-Powered • Real-Time Monitoring
        </p>
        <p style="color: white; margin: 0.5rem 0 0 0; opacity: 0.7; font-size: 1rem;">
            Welcome back, Administrator • Last login: {current_time}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_intellicv_page_header(page_title, page_icon="", description=""):
    """Render a consistent page header for all admin pages"""
    st.markdown(f"""
    <div class="page-header">
        <h1 style="color: white; margin: 0; font-size: 2rem;">{page_icon} {page_title}</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem;">
            IntelliCV-AI • {description}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_intellicv_section_header(title, icon=""):
    """Render a section header with IntelliCV styling"""
    st.markdown(f"""
    <div class="intellicv-section-header">
        <h2 style="margin: 0; color: #1976d2;">{icon} {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def apply_intellicv_styling():
    """Apply IntelliCV-AI styling to the entire page"""
    inject_intellicv_branding()
    
    # Set page config if not already set
    try:
        st.set_page_config(
            page_title="IntelliCV-AI Admin Portal",
            page_icon="⬢",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except:
        pass  # Page config already set