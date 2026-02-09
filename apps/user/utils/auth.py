"""
Authentication utilities for User Portal.
Provides session management, password security, and user authentication.
"""

import logging
import streamlit as st
import hashlib
import secrets
import hmac
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from functools import wraps

@dataclass
class UserSession:
    """User session data structure."""
    user_id: str
    username: str
    email: str
    role: str
    login_time: datetime
    last_activity: datetime
    session_token: str

class UserAuthenticationManager:
    """Manages user authentication for Streamlit application."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize authentication manager.
        
        Args:
            secret_key: Secret key for session security
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.logger = logging.getLogger("user_portal.auth")
        
        # Initialize session state variables
        self._init_session_state()
    
    def _init_session_state(self) -> None:
        """Initialize authentication-related session state variables."""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        
        if 'session_token' not in st.session_state:
            st.session_state.session_token = None
        
        if 'login_attempts' not in st.session_state:
            st.session_state.login_attempts = 0
        
        if 'lockout_until' not in st.session_state:
            st.session_state.lockout_until = None
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """
        Hash password with salt.
        
        Args:
            password: Plain text password
            salt: Optional salt (generates new if not provided)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Combine password and salt
        password_salt = f"{password}{salt}"
        
        # Hash with SHA-256
        hashed = hashlib.sha256(password_salt.encode()).hexdigest()
        
        return hashed, salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Stored password hash
            salt: Password salt
            
        Returns:
            True if password matches, False otherwise
        """
        test_hash, _ = self.hash_password(password, salt)
        return hmac.compare_digest(test_hash, hashed_password)
    
    def generate_session_token(self, user_data: Dict[str, Any]) -> str:
        """
        Generate secure session token.
        
        Args:
            user_data: User information
            
        Returns:
            Session token
        """
        timestamp = str(datetime.utcnow().timestamp())
        user_id = str(user_data.get('user_id', ''))
        
        # Create token data
        token_data = f"{user_id}:{timestamp}:{secrets.token_hex(16)}"
        
        # Sign with secret key
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{token_data}:{signature}"
    
    def verify_session_token(self, token: str, max_age_hours: int = 24) -> bool:
        """
        Verify session token validity.
        
        Args:
            token: Session token to verify
            max_age_hours: Maximum token age in hours
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            # Split token parts
            parts = token.split(':')
            if len(parts) != 4:
                return False
            
            user_id, timestamp, random_part, signature = parts
            
            # Verify signature
            token_data = f"{user_id}:{timestamp}:{random_part}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return False
            
            # Check token age
            token_time = datetime.utcfromtimestamp(float(timestamp))
            max_age = timedelta(hours=max_age_hours)
            
            if datetime.utcnow() - token_time > max_age:
                return False
            
            return True
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Invalid session token format: {str(e)}")
            return False
    
    def login_user(self, user_data: Dict[str, Any]) -> bool:
        """
        Log in user and create session.
        
        Args:
            user_data: User information dictionary
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Check if account is locked
            if self._is_account_locked():
                st.error("Account is temporarily locked due to too many failed attempts. Please try again later.")
                return False
            
            # Generate session token
            session_token = self.generate_session_token(user_data)
            
            # Create user session
            user_session = UserSession(
                user_id=str(user_data.get('user_id', '')),
                username=user_data.get('username', ''),
                email=user_data.get('email', ''),
                role=user_data.get('role', 'user'),
                login_time=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                session_token=session_token
            )
            
            # Update session state
            st.session_state.authenticated = True
            st.session_state.user_data = user_session
            st.session_state.session_token = session_token
            st.session_state.login_attempts = 0  # Reset failed attempts
            st.session_state.lockout_until = None
            
            self.logger.info(f"User logged in: {user_data.get('username', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Login error: {str(e)}")
            return False
    
    def logout_user(self) -> None:
        """Log out current user and clear session."""
        if st.session_state.get('user_data'):
            username = st.session_state.user_data.username
            self.logger.info(f"User logged out: {username}")
        
        # Clear authentication session state
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.session_token = None
        
        # Clear other user-specific session data
        keys_to_clear = [key for key in st.session_state.keys() 
                        if key.startswith(('user_', 'upload_', 'analysis_'))]
        
        for key in keys_to_clear:
            del st.session_state[key]
        
        st.success("You have been logged out successfully.")
        st.rerun()
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        if not st.session_state.get('authenticated', False):
            return False
        
        # Verify session token if present
        session_token = st.session_state.get('session_token')
        if session_token and not self.verify_session_token(session_token):
            self.logout_user()
            return False
        
        # Update last activity
        if st.session_state.get('user_data'):
            st.session_state.user_data.last_activity = datetime.utcnow()
        
        return True
    
    def get_current_user(self) -> Optional[UserSession]:
        """
        Get current user session data.
        
        Returns:
            UserSession if authenticated, None otherwise
        """
        if self.is_authenticated():
            return st.session_state.get('user_data')
        return None
    
    def require_role(self, required_roles: List[str]) -> bool:
        """
        Check if current user has required role.
        
        Args:
            required_roles: List of required roles
            
        Returns:
            True if user has required role, False otherwise
        """
        user = self.get_current_user()
        if not user:
            return False
        
        return user.role in required_roles
    
    def record_failed_login(self, identifier: str) -> None:
        """
        Record failed login attempt.
        
        Args:
            identifier: User identifier (username/email)
        """
        st.session_state.login_attempts = st.session_state.get('login_attempts', 0) + 1
        
        # Lock account after 5 failed attempts for 15 minutes
        if st.session_state.login_attempts >= 5:
            lockout_time = datetime.utcnow() + timedelta(minutes=15)
            st.session_state.lockout_until = lockout_time
            
            self.logger.warning(f"Account locked for failed attempts: {identifier}")
            st.error("Too many failed login attempts. Account locked for 15 minutes.")
    
    def _is_account_locked(self) -> bool:
        """
        Check if account is currently locked.
        
        Returns:
            True if locked, False otherwise
        """
        lockout_until = st.session_state.get('lockout_until')
        if lockout_until and datetime.utcnow() < lockout_until:
            return True
        
        # Clear lockout if expired
        if lockout_until:
            st.session_state.lockout_until = None
        
        return False

# Authentication decorators
def require_authentication(func):
    """
    Decorator to require authentication for function access.
    
    Args:
        func: Function to protect
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_manager = UserAuthenticationManager()
        
        if not auth_manager.is_authenticated():
            st.warning("Please log in to access this feature.")
            st.stop()
        
        return func(*args, **kwargs)
    
    return wrapper

def require_role(roles: List[str]):
    """
    Decorator to require specific roles for function access.
    
    Args:
        roles: List of required roles
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_manager = UserAuthenticationManager()
            
            if not auth_manager.is_authenticated():
                st.warning("Please log in to access this feature.")
                st.stop()
            
            if not auth_manager.require_role(roles):
                st.error("You don't have permission to access this feature.")
                st.stop()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Utility functions
def check_password_strength(password: str) -> Dict[str, Any]:
    """
    Check password strength and provide feedback.
    
    Args:
        password: Password to check
        
    Returns:
        Dictionary with strength assessment
    """
    strength = {
        'score': 0,
        'feedback': [],
        'is_strong': False
    }
    
    if len(password) >= 8:
        strength['score'] += 1
    else:
        strength['feedback'].append("Password should be at least 8 characters long")
    
    if any(c.isupper() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append("Password should contain uppercase letters")
    
    if any(c.islower() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append("Password should contain lowercase letters")
    
    if any(c.isdigit() for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append("Password should contain numbers")
    
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        strength['score'] += 1
    else:
        strength['feedback'].append("Password should contain special characters")
    
    strength['is_strong'] = strength['score'] >= 4
    
    return strength

def create_login_form() -> Optional[Dict[str, str]]:
    """
    Create standardized login form.
    
    Returns:
        Login credentials if submitted, None otherwise
    """
    with st.form("login_form"):
        st.subheader("🔐 User Login")
        
        username = st.text_input(
            "Username or Email",
            placeholder="Enter your username or email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            login_submitted = st.form_submit_button("Login", type="primary")
        
        with col2:
            forgot_password = st.form_submit_button("Forgot Password?")
        
        if login_submitted:
            if username and password:
                return {
                    'username': username,
                    'password': password
                }
            else:
                st.error("Please enter both username and password")
        
        if forgot_password:
            st.info("Password reset functionality coming soon!")
    
    return None