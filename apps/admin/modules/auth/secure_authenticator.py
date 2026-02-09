
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
Enhanced Authentication System for IntelliCV Admin Portal
Implements secure login with mandatory password changes
"""

import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import streamlit as st
from dataclasses import dataclass
import re

@dataclass
class UserCredentials:
    """User credentials data structure"""
    username: str
    password_hash: str
    salt: str
    is_default_password: bool
    last_login: Optional[str]
    failed_attempts: int
    locked_until: Optional[str]
    password_changed_at: str
    requires_password_change: bool

class SecureAuthenticator:
    """Enhanced secure authentication system"""
    
    def __init__(self, credentials_file: str = "admin_credentials.json"):
        self.credentials_file = credentials_file
        self.max_failed_attempts = 3
        self.lockout_duration = 15  # minutes
        self.min_password_length = 8
        self.session_timeout = 30  # minutes
        
        # Initialize with default admin credentials if file doesn't exist
        self._initialize_default_credentials()
    
    def _initialize_default_credentials(self):
        """Initialize with default admin/admin credentials"""
        if not os.path.exists(self.credentials_file):
            # Create default admin user with admin/admin
            salt = secrets.token_hex(32)
            password_hash = self._hash_password("admin", salt)
            
            default_admin = UserCredentials(
                username="admin",
                password_hash=password_hash,
                salt=salt,
                is_default_password=True,
                last_login=None,
                failed_attempts=0,
                locked_until=None,
                password_changed_at=datetime.now().isoformat(),
                requires_password_change=True
            )
            
            self._save_credentials({"admin": default_admin})

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.info("🔧 Default admin credentials initialized: admin/admin (change required)")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _save_credentials(self, credentials: Dict[str, UserCredentials]):
        """Save credentials to file"""
        data = {}
        for username, creds in credentials.items():
            data[username] = {
                "username": creds.username,
                "password_hash": creds.password_hash,
                "salt": creds.salt,
                "is_default_password": creds.is_default_password,
                "last_login": creds.last_login,
                "failed_attempts": creds.failed_attempts,
                "locked_until": creds.locked_until,
                "password_changed_at": creds.password_changed_at,
                "requires_password_change": creds.requires_password_change
            }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_credentials(self) -> Dict[str, UserCredentials]:
        """Load credentials from file"""
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
            
            credentials = {}
            for username, cred_data in data.items():
                credentials[username] = UserCredentials(**cred_data)
            
            return credentials
        except Exception as e:
            st.error(f"Failed to load credentials: {e}")
            return {}
    
    def _is_account_locked(self, credentials: UserCredentials) -> bool:
        """Check if account is locked due to failed attempts"""
        if not credentials.locked_until:
            return False
        
        locked_until = datetime.fromisoformat(credentials.locked_until)
        return datetime.now() < locked_until
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < self.min_password_length:
            return False, f"Password must be at least {self.min_password_length} characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        if password.lower() in ['password', 'admin', 'admin123', '12345678']:
            return False, "Password is too common and insecure"
        
        return True, "Password is strong"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, bool]:
        """
        Authenticate user
        Returns: (success, message, requires_password_change)
        """
        credentials_dict = self._load_credentials()
        
        if username not in credentials_dict:
            return False, "Invalid username or password", False
        
        user_creds = credentials_dict[username]
        
        # Check if account is locked
        if self._is_account_locked(user_creds):
            locked_until = datetime.fromisoformat(user_creds.locked_until)
            minutes_left = int((locked_until - datetime.now()).total_seconds() / 60)
            return False, f"Account locked for {minutes_left} more minutes", False
        
        # Verify password
        password_hash = self._hash_password(password, user_creds.salt)
        if password_hash != user_creds.password_hash:
            # Increment failed attempts
            user_creds.failed_attempts += 1
            
            if user_creds.failed_attempts >= self.max_failed_attempts:
                # Lock account
                user_creds.locked_until = (datetime.now() + timedelta(minutes=self.lockout_duration)).isoformat()
                credentials_dict[username] = user_creds
                self._save_credentials(credentials_dict)
                return False, f"Account locked for {self.lockout_duration} minutes due to multiple failed attempts", False
            
            credentials_dict[username] = user_creds
            self._save_credentials(credentials_dict)
            attempts_left = self.max_failed_attempts - user_creds.failed_attempts
            return False, f"Invalid credentials. {attempts_left} attempts remaining", False
        
        # Successful authentication
        user_creds.failed_attempts = 0
        user_creds.locked_until = None
        user_creds.last_login = datetime.now().isoformat()
        credentials_dict[username] = user_creds
        self._save_credentials(credentials_dict)
        
        return True, "Authentication successful", user_creds.requires_password_change
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        credentials_dict = self._load_credentials()
        
        if username not in credentials_dict:
            return False, "User not found"
        
        user_creds = credentials_dict[username]
        
        # Verify old password (unless it's the first change from default)
        if not user_creds.is_default_password:
            old_password_hash = self._hash_password(old_password, user_creds.salt)
            if old_password_hash != user_creds.password_hash:
                return False, "Current password is incorrect"
        
        # Validate new password strength
        is_strong, message = self._validate_password_strength(new_password)
        if not is_strong:
            return False, message
        
        # Check if new password is different from old
        new_password_hash = self._hash_password(new_password, user_creds.salt)
        if new_password_hash == user_creds.password_hash:
            return False, "New password must be different from current password"
        
        # Update password
        new_salt = secrets.token_hex(32)
        user_creds.password_hash = self._hash_password(new_password, new_salt)
        user_creds.salt = new_salt
        user_creds.is_default_password = False
        user_creds.requires_password_change = False
        user_creds.password_changed_at = datetime.now().isoformat()
        
        credentials_dict[username] = user_creds
        self._save_credentials(credentials_dict)
        
        return True, "Password changed successfully"
    
    def create_new_user(self, username: str, password: str, require_password_change: bool = True) -> Tuple[bool, str]:
        """Create new user account"""
        credentials_dict = self._load_credentials()
        
        if username in credentials_dict:
            return False, "Username already exists"
        
        # Validate password strength
        is_strong, message = self._validate_password_strength(password)
        if not is_strong:
            return False, message
        
        # Create new user
        salt = secrets.token_hex(32)
        password_hash = self._hash_password(password, salt)
        
        new_user = UserCredentials(
            username=username,
            password_hash=password_hash,
            salt=salt,
            is_default_password=False,
            last_login=None,
            failed_attempts=0,
            locked_until=None,
            password_changed_at=datetime.now().isoformat(),
            requires_password_change=require_password_change
        )
        
        credentials_dict[username] = new_user
        self._save_credentials(credentials_dict)
        
        return True, f"User '{username}' created successfully"


class SessionManager:
    """Enhanced session management with timeouts"""
    
    def __init__(self, session_timeout: int = 30):
        self.session_timeout = session_timeout  # minutes
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in and session is valid"""
        if 'logged_in' not in st.session_state:
            return False
        
        if not st.session_state.logged_in:
            return False
        
        # Check session timeout
        if 'login_time' in st.session_state:
            login_time = datetime.fromisoformat(st.session_state.login_time)
            if datetime.now() - login_time > timedelta(minutes=self.session_timeout):
                self.logout_user()
                st.warning(f"Session expired after {self.session_timeout} minutes of inactivity")
                return False
        
        return True
    
    def login_user(self, username: str):
        """Log in user and start session"""
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.login_time = datetime.now().isoformat()
        st.session_state.requires_password_change = False
    
    def set_password_change_required(self):
        """Mark that password change is required"""
        st.session_state.requires_password_change = True
    
    def clear_password_change_requirement(self):
        """Clear password change requirement"""
        st.session_state.requires_password_change = False
    
    def requires_password_change(self) -> bool:
        """Check if password change is required"""
        return st.session_state.get('requires_password_change', False)
    
    def logout_user(self):
        """Log out user and clear session"""
        keys_to_clear = ['logged_in', 'username', 'login_time', 'requires_password_change']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_username(self) -> str:
        """Get current logged in username"""
        return st.session_state.get('username', '')
    
    def update_activity(self):
        """Update last activity time"""
        if self.is_logged_in():
            st.session_state.login_time = datetime.now().isoformat()


def render_secure_login_interface():
    """Render secure login interface with password change enforcement"""
    authenticator = SecureAuthenticator()
    session_manager = SessionManager()
    
    # Check if user is logged in and password change is required
    if session_manager.is_logged_in():
        if session_manager.requires_password_change():
            st.error("🔒 **SECURITY NOTICE: You must change your password before accessing admin features**")
            render_password_change_interface(authenticator, session_manager)
            return False
        else:
            # Update activity and show logout option
            session_manager.update_activity()
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ Logged in as: **{session_manager.get_username()}**")
            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    session_manager.logout_user()
                    st.rerun()
            return True
    
    # Show login form
    st.markdown("### 🔐 Admin Portal Login")
    st.info("**Default Login:** Username: `admin` | Password: `admin`")
    st.warning("⚠️ **Security Notice:** You will be required to change the default password after login")
    
    with st.form("secure_login_form"):
        username = st.text_input("👤 Username", placeholder="Enter your username")
        password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("🚀 Login", use_container_width=True)
        with col2:
            show_password_requirements = st.form_submit_button("ℹ️ Password Requirements", use_container_width=True)
        
        if show_password_requirements:
            st.info("""
            **Password Requirements for New Passwords:**
            - Minimum 8 characters
            - At least one uppercase letter
            - At least one lowercase letter  
            - At least one digit
            - At least one special character (!@#$%^&*(),.?\":{}|<>)
            - Cannot be common passwords (password, admin, etc.)
            """)
        
        if login_button:
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                success, message, requires_change = authenticator.authenticate_user(username, password)
                
                if success:
                    session_manager.login_user(username)
                    if requires_change:
                        session_manager.set_password_change_required()
                    st.success(f"✅ {message}")
                    if requires_change:
                        st.warning("🔒 Password change required - redirecting...")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    return False


def render_password_change_interface(authenticator: SecureAuthenticator, session_manager: SessionManager):
    """Render password change interface"""
    st.markdown("### 🔒 Change Password Required")
    st.error("**You must change your password to continue using the admin portal**")
    
    username = session_manager.get_username()
    
    with st.form("password_change_form"):
        if not st.session_state.get('first_login_default', False):
            current_password = st.text_input("🔑 Current Password", type="password")
        else:
            current_password = "admin"  # Default password for first login
            st.info("Using default password for first-time change")
        
        new_password = st.text_input("🆕 New Password", type="password")
        confirm_password = st.text_input("✅ Confirm New Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            change_button = st.form_submit_button("🔄 Change Password", use_container_width=True)
        with col2:
            logout_button = st.form_submit_button("🚪 Logout", use_container_width=True)
        
        if logout_button:
            session_manager.logout_user()
            st.rerun()
        
        if change_button:
            if not new_password or not confirm_password:
                st.error("❌ Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("❌ New passwords do not match")
            else:
                success, message = authenticator.change_password(username, current_password, new_password)
                
                if success:
                    session_manager.clear_password_change_requirement()
                    st.success(f"✅ {message}")
                    st.success("🎉 You can now access all admin features!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")


# Example usage and testing functions
if __name__ == "__main__":
    st.title("🔐 Secure Authentication System Test")
    
    # Test the authentication system
    if render_secure_login_interface():
        st.success("🎉 Welcome to the Admin Portal!")
        st.markdown("### Available Admin Features:")
        st.markdown("- User Management")
        st.markdown("- Data Analysis")
        st.markdown("- System Monitoring")
        st.markdown("- AI Tools & Analytics")
    else:
        st.info("Please log in to access admin features")