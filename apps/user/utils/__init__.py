"""
User Portal utilities package initialization.
Provides organized imports for all utility modules.
"""

from .common import (
    setup_logging,
    get_env_variable,
    handle_error,
    validate_streamlit_input,
    safe_json_loads,
    format_datetime,
    calculate_file_hash,
    performance_monitor,
    retry_with_backoff,
    init_session_state,
    clear_session_state,
    show_success_message,
    show_loading_spinner,
    validate_file_upload,
    create_download_link
)

from .auth import (
    UserSession,
    UserAuthenticationManager,
    require_authentication,
    require_role,
    check_password_strength,
    create_login_form
)

from .config import (
    StreamlitConfig,
    DatabaseConfig,
    RedisConfig,
    SecurityConfig,
    AIConfig,
    UIConfig,
    EmailConfig,
    ConfigManager,
    get_config,
    apply_streamlit_config,
    load_custom_css
)

__all__ = [
    # Common utilities
    'setup_logging',
    'get_env_variable',
    'handle_error',
    'validate_streamlit_input',
    'safe_json_loads',
    'format_datetime',
    'calculate_file_hash',
    'performance_monitor',
    'retry_with_backoff',
    'init_session_state',
    'clear_session_state',
    'show_success_message',
    'show_loading_spinner',
    'validate_file_upload',
    'create_download_link',
    
    # Authentication utilities
    'UserSession',
    'UserAuthenticationManager',
    'require_authentication',
    'require_role',
    'check_password_strength',
    'create_login_form',
    
    # Configuration utilities
    'StreamlitConfig',
    'DatabaseConfig',
    'RedisConfig',
    'SecurityConfig',
    'AIConfig',
    'UIConfig',
    'EmailConfig',
    'ConfigManager',
    'get_config',
    'apply_streamlit_config',
    'load_custom_css'
]

# Module metadata
__version__ = "1.0.0"
__author__ = "IntelliCV Development Team"
__description__ = "User Portal utilities for IntelliCV Streamlit application"

# Setup package logging
import logging

logger = logging.getLogger("user_portal.utils")
logger.setLevel(logging.INFO)

# Package initialization message
logger.info("User Portal utilities package initialized")

# Convenience functions for common patterns
def initialize_page(
    page_title: str,
    page_icon: str = "📄",
    layout: str = "wide",
    require_auth: bool = True
) -> None:
    """
    Initialize Streamlit page with common setup.
    
    Args:
        page_title: Page title
        page_icon: Page icon
        layout: Page layout
        require_auth: Whether authentication is required
    """
    import streamlit as st
    
    # Set page config
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
    # Check authentication if required
    if require_auth:
        auth_manager = UserAuthenticationManager()
        if not auth_manager.is_authenticated():
            st.warning("🔒 Please log in to access this page.")
            
            # Show login form
            login_data = create_login_form()
            if login_data:
                # This would typically connect to your authentication backend
                st.info("Please implement authentication backend connection.")
            
            st.stop()

def setup_sidebar_navigation() -> None:
    """Setup standard sidebar navigation for user portal."""
    import streamlit as st
    
    with st.sidebar:
        st.markdown("### 🏠 Navigation")
        
        # Get current user info
        auth_manager = UserAuthenticationManager()
        current_user = auth_manager.get_current_user()
        
        if current_user:
            st.markdown(f"**Welcome, {current_user.username}!**")
            st.markdown(f"Role: {current_user.role.title()}")
            
            if st.button("🚪 Logout", type="secondary"):
                auth_manager.logout_user()
        
        st.markdown("---")
        
        # Navigation links (customize based on your pages)
        nav_items = [
            ("🏠 Home", "Home"),
            ("📄 Upload CV", "Upload_CV"),
            ("🔍 Analysis", "Analysis"),
            ("📊 Dashboard", "Dashboard"),
            ("👤 Profile", "Profile"),
            ("⚙️ Settings", "Settings")
        ]
        
        for label, page in nav_items:
            if st.button(label, key=f"nav_{page}"):
                st.switch_page(f"pages/{page}.py")

def create_header_section(title: str, subtitle: str = "") -> None:
    """
    Create standardized header section.
    
    Args:
        title: Main title
        subtitle: Optional subtitle
    """
    import streamlit as st
    
    header_html = f"""
    <div class="user-portal-header">
        <h1 style="margin: 0; font-size: 2.5rem;">{title}</h1>
        {f'<p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)

def display_metric_cards(metrics: list) -> None:
    """
    Display metrics in card format.
    
    Args:
        metrics: List of metric dictionaries with keys: label, value, delta (optional)
    """
    import streamlit as st
    
    cols = st.columns(len(metrics))
    
    for i, metric in enumerate(metrics):
        with cols[i]:
            st.metric(
                label=metric.get('label', ''),
                value=metric.get('value', ''),
                delta=metric.get('delta')
            )

def show_error_page(error_title: str, error_message: str, show_contact: bool = True) -> None:
    """
    Display standardized error page.
    
    Args:
        error_title: Error title
        error_message: Error message
        show_contact: Whether to show contact information
    """
    import streamlit as st
    
    st.error(f"**{error_title}**")
    st.write(error_message)
    
    if show_contact:
        st.info("If this problem persists, please contact support at support@intellicv.com")
    
    if st.button("🔄 Try Again"):
        st.rerun()