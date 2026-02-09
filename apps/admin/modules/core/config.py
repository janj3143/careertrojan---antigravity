
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
Configuration Management for IntelliCV-AI Admin Portal
=================================================

This module contains all configuration classes, data classes, 
and environment settings for the admin portal system.
"""

import os
import streamlit as st
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class IntelligenceConfig:
    """Configuration for intelligence engine."""
    knowledge_base_path: str = "ai_data"
    enable_salary_estimation: bool = True
    enable_market_analysis: bool = True
    enable_cultural_fit: bool = True
    confidence_threshold: float = 0.7
    log_level: str = "INFO"
    batch_size: int = 100


@dataclass
class CandidateInsight:
    """Structured candidate insight data."""
    candidate_id: str
    insights: Dict[str, Any]
    confidence_score: float
    generated_at: str
    processing_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class AppConfig:
    """Global application configuration."""
    
    def __init__(self):
        """Initialize application configuration."""
        self._setup_page_config()
        self._setup_paths()
        self._setup_session_state()
    
    def _setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            page_title="IntelliCV-AI Unified Admin Portal",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def _setup_paths(self):
        """Setup project directories."""
        self.PROJECT_ROOT = Path(__file__).resolve().parents[3] if Path(__file__).name != "streamlit_app.py" else Path.cwd()
        self.ADMIN_ROOT = Path(__file__).parents[2] / "pages" if Path(__file__).name != "streamlit_app.py" else Path.cwd() / "pages"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.AI_DATA_DIR = self.PROJECT_ROOT / "ai_data"
        self.USER_DATA_DIR = self.PROJECT_ROOT / "frontend" / "data"
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        
        # Ensure directories exist
        for directory in [self.DATA_DIR, self.AI_DATA_DIR, self.USER_DATA_DIR, self.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_session_state(self):
        """Initialize Streamlit session state variables."""
        if "current_section" not in st.session_state:
            st.session_state.current_section = "dashboard"
        if "is_admin" not in st.session_state:
            st.session_state.is_admin = False
        if "authenticated_user" not in st.session_state:
            st.session_state.authenticated_user = None
    
    @property
    def paths(self):
        """Get all configured paths."""
        return {
            'project_root': self.PROJECT_ROOT,
            'admin_root': self.ADMIN_ROOT,
            'data_dir': self.DATA_DIR,
            'ai_data_dir': self.AI_DATA_DIR,
            'user_data_dir': self.USER_DATA_DIR,
            'logs_dir': self.LOGS_DIR
        }


def get_css_styles():
    """Get CSS styles for the application."""
    return """
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .category-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        transition: transform 0.2s ease;
    }
    .category-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .metric-card {
        background: #fff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online { background-color: #4caf50; }
    .status-warning { background-color: #ff9800; }
    .status-offline { background-color: #f44336; }
    .section-header {
        background: linear-gradient(90deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    </style>
    """


# Global configuration instance
app_config = AppConfig()