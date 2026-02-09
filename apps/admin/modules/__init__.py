"""
IntelliCV-AI Admin Portal Modules
==================================

Modular architecture for the IntelliCV-AI Admin Portal.
This package contains all core components organized by functionality.
"""

# Import main modules for easy access
try:
    from .parsers.parsers_integration import *
except ImportError:
    pass

try:
    from .visualization.dashboard_visualizer import dashboard_visualizer, render_visualization_section
except ImportError:
    pass

__version__ = "1.0.0"
__author__ = "IntelliCV-AI Team"

# Module organization:
# - core/: Configuration, session management, utilities
# - intelligence/: AI engines, market analysis, company intelligence
# - ui/: Streamlit UI components and page renderers
# - integrations/: External system integrations