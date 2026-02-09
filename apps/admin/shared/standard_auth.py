"""
SANDBOX Admin Portal - Standard Authentication Check
==================================================
Standard authentication function to be used by all admin portal pages.
"""

import streamlit as st

def check_admin_authentication():
    """
    Standard authentication check for all SANDBOX admin portal pages.
    This function should be called at the beginning of every admin page.
    """
    if not st.session_state.get('admin_authenticated', False):
        st.error("🔒 **ADMIN AUTHENTICATION REQUIRED**")
        st.warning("You must login through the main admin portal to access this module.")
        
        st.markdown("""
        ### 🚫 Access Denied
        
        This admin module requires authentication. Please:
        
        1. **Return to the main admin portal** 
        2. **Login with admin credentials**
        3. **Navigate back to this page**
        
        All admin functions are protected by authentication.
        """)
        
        if st.button("🏠 Return to Main Portal", type="primary"):
            # This will redirect to the main page
            st.switch_page("main.py")
        
        st.stop()
    
    # If we reach here, user is authenticated
    with st.sidebar:
        st.success(f"✅ Authenticated: {st.session_state.get('admin_user', 'admin')}")
        
        if st.button("🚪 Logout", key="page_logout"):
            # Clear authentication
            st.session_state.admin_authenticated = False
            if 'admin_user' in st.session_state:
                del st.session_state.admin_user
            st.success("👋 Logged out successfully!")
            st.rerun()

def get_admin_user():
    """Get the current authenticated admin user"""
    return st.session_state.get('admin_user', 'admin')

def is_authenticated():
    """Check if user is authenticated (returns boolean)"""
    return st.session_state.get('admin_authenticated', False)