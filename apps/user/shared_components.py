"""
Shared Components for User Portal
==================================

Common UI components used across all pages:
- Professional styling (CSS)
- Logo watermark display
- Session state management
- Static file handling
"""

import streamlit as st
from pathlib import Path
import base64


def get_image_base64(image_path: Path) -> str:
    """
    Convert image file to base64 string for embedding in HTML/CSS.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"⚠️ Could not load image {image_path}: {e}")
        return ""


def apply_professional_styling():
    """
    Apply consistent professional CSS styling across all pages.
    """
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Professional color scheme */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #fbbf24;
        --text-dark: #1f2937;
        --text-light: #6b7280;
        --bg-light: #f9fafb;
    }

    /* Main container styling */
    .main {
        padding: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }

    /* Card styling */
    .stCard, .element-container {
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--primary-color);
    }

    /* Success/Warning/Error boxes */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 8px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)


def show_logo_watermark():
    """
    Display IntelliCV logo watermark in the top right corner.
    """
    static_dir = Path(__file__).parent / "static"
    logo_path = static_dir / "logo.png"

    if not logo_path.exists():
        # Fallback to logo1.png
        logo_path = static_dir / "logo1.png"

    if logo_path.exists():
        logo_base64 = get_image_base64(logo_path)

        if logo_base64:
            st.markdown(f"""
            <style>
            .logo-watermark {{
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 999;
                opacity: 0.9;
                transition: opacity 0.3s ease;
            }}

            .logo-watermark:hover {{
                opacity: 1;
            }}

            .logo-watermark img {{
                height: 50px;
                width: auto;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            </style>

            <div class="logo-watermark">
                <img src="data:image/png;base64,{logo_base64}" alt="IntelliCV-AI">
            </div>
            """, unsafe_allow_html=True)
    else:
        # Text fallback if no logo image
        st.markdown("""
        <style>
        .logo-text-watermark {
            position: fixed;
            top: 15px;
            right: 15px;
            z-index: 999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.9rem;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        </style>

        <div class="logo-text-watermark">
            IntelliCV-AI
        </div>
        """, unsafe_allow_html=True)


def initialize_session_manager():
    """
    Initialize critical session state variables if not already set.
    """
    defaults = {
        'authenticated_user': False,
        'user_id': None,
        'user_email': None,
        'user_name': None,
        'user_tier': 'free',
        'profile_completeness': 0,
        'user_tokens': 40,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def load_custom_css(css_file: str):
    """
    Load custom CSS file from static directory.

    Args:
        css_file: Name of the CSS file (e.g., 'watermark.css')
    """
    static_dir = Path(__file__).parent / "static"
    css_path = static_dir / css_file

    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        print(f"⚠️ CSS file not found: {css_path}")


def get_static_file_path(filename: str) -> Path:
    """
    Get full path to a static file.

    Args:
        filename: Name of the file in static directory

    Returns:
        Path object to the static file
    """
    static_dir = Path(__file__).parent / "static"
    return static_dir / filename


def display_feature_badge(tier: str, feature_name: str):
    """
    Display a tier badge for premium features.

    Args:
        tier: Tier level (free, monthly_pro, annual_pro, enterprise_pro)
        feature_name: Name of the feature
    """
    tier_colors = {
        'free': '#10b981',
        'monthly_pro': '#fbbf24',
        'annual_pro': '#f59e0b',
        'enterprise_pro': '#8b5cf6'
    }

    tier_labels = {
        'free': '🆓 FREE',
        'monthly_pro': '⭐ MONTHLY PRO',
        'annual_pro': '🌟 ANNUAL PRO',
        'enterprise_pro': '✨ ENTERPRISE'
    }

    color = tier_colors.get(tier, '#6b7280')
    label = tier_labels.get(tier, tier.upper())

    st.markdown(f"""
    <div style="display: inline-block; background: {color}; color: white;
                padding: 0.3rem 0.8rem; border-radius: 20px;
                font-weight: bold; font-size: 0.85rem; margin-left: 0.5rem;">
        {label}
    </div>
    """, unsafe_allow_html=True)


def create_gradient_header(title: str, subtitle: str = ""):
    """
    Create a professional gradient header for pages.

    Args:
        title: Main page title
        subtitle: Optional subtitle
    """
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">{title}</h1>
        {f'<p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.2rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
