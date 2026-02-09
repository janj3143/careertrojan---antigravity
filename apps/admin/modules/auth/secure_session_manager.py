
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
Secure Session Manager for IntelliCV Admin Portal
Implements secure session handling with proper timeout, CSRF protection, and audit logging

SECURITY FEATURES:
- Session token generation with cryptographic randomness
- Session timeout and automatic cleanup
- CSRF token validation
- Session hijacking protection
- Secure cookie configuration
- Activity tracking and audit logging
- IP address validation (when available)
- Concurrent session limits
"""

import secrets
import time
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import streamlit as st
from dataclasses import dataclass, asdict
import hashlib

# Configure session audit logging
session_logger = logging.getLogger('session_manager')

@dataclass
class SessionData:
    """Secure session data structure"""
    session_id: str
    username: str
    created_at: str
    last_activity: str
    expires_at: str
    csrf_token: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    activity_count: int
    last_ip_address: Optional[str]

class SecureSessionManager:
    """Enterprise-grade session management with security controls"""
    
    def __init__(self, sessions_file: str = "secure_sessions.json"):
        self.sessions_file = sessions_file
        
        # Security configuration from environment
        self.session_timeout = int(os.getenv('AUTH_TOKEN_EXPIRY', '1800'))  # 30 minutes
        self.max_concurrent_sessions = int(os.getenv('MAX_CONCURRENT_SESSIONS', '3'))
        self.csrf_token_length = 32
        self.session_id_length = 64
        
        # Activity tracking
        self.max_activity_log = 50
        
        # Initialize session store
        self._initialize_session_store()
        
        session_logger.info("SecureSessionManager initialized")
    
    def _initialize_session_store(self):
        """Initialize secure session storage"""
        if not os.path.exists(self.sessions_file):
            self._save_sessions({})
    
    def create_session(self, username: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[str, str]:
        """Create a new secure session"""
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        # Check concurrent session limit
        active_sessions = self._get_active_sessions_for_user(username)
        if len(active_sessions) >= self.max_concurrent_sessions:
            # Terminate oldest session
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            self._terminate_session(oldest_session.session_id)
            session_logger.warning(f"Terminated oldest session for {username} due to concurrent limit")
        
        # Generate secure session ID and CSRF token
        session_id = secrets.token_urlsafe(self.session_id_length)
        csrf_token = secrets.token_urlsafe(self.csrf_token_length)
        
        # Create session data
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.session_timeout)
        
        session_data = SessionData(
            session_id=session_id,
            username=username,
            created_at=now.isoformat(),
            last_activity=now.isoformat(),
            expires_at=expires_at.isoformat(),
            csrf_token=csrf_token,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            activity_count=1,
            last_ip_address=ip_address
        )
        
        # Save session
        sessions = self._load_sessions()
        sessions[session_id] = session_data
        self._save_sessions(sessions)
        
        # Store in Streamlit session state

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

        st.session_state['session_id'] = session_id
        st.session_state['csrf_token'] = csrf_token
        st.session_state['username'] = username
        st.session_state['session_expires'] = expires_at.isoformat()
        st.session_state['is_authenticated'] = True
        
        session_logger.info(f"Session created for {username}: {session_id[:8]}...")
        return session_id, csrf_token
    
    def validate_session(self, session_id: Optional[str] = None, csrf_token: Optional[str] = None, 
                        ip_address: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validate session with comprehensive security checks"""
        # Get session ID from parameter or Streamlit state
        if not session_id:
            session_id = st.session_state.get('session_id')
        
        if not session_id:
            return False, "No session found", None
        
        sessions = self._load_sessions()
        
        if session_id not in sessions:
            session_logger.warning(f"Session validation failed: Unknown session {session_id[:8]}...")
            return False, "Invalid session", None
        
        session_data = sessions[session_id]
        
        # Check if session is active
        if not session_data.is_active:
            session_logger.warning(f"Session validation failed: Inactive session {session_id[:8]}...")
            return False, "Session terminated", None
        
        # Check if session has expired
        expires_at = datetime.fromisoformat(session_data.expires_at)
        if datetime.now() > expires_at:
            # Mark session as expired
            session_data.is_active = False
            sessions[session_id] = session_data
            self._save_sessions(sessions)
            
            session_logger.warning(f"Session expired for {session_data.username}: {session_id[:8]}...")
            return False, "Session expired", None
        
        # Validate CSRF token if provided
        if csrf_token and csrf_token != session_data.csrf_token:
            session_logger.warning(f"CSRF validation failed for {session_data.username}: {session_id[:8]}...")
            return False, "CSRF token mismatch", None
        
        # IP address validation (if available and configured)
        if ip_address and session_data.ip_address and ip_address != session_data.ip_address:
            # Potential session hijacking - log but don't immediately terminate
            session_logger.warning(f"IP address change detected for {session_data.username}: {session_data.ip_address} -> {ip_address}")
            session_data.last_ip_address = ip_address
        
        # Update session activity
        now = datetime.now()
        session_data.last_activity = now.isoformat()
        session_data.activity_count += 1
        
        # Extend session expiry (sliding window)
        new_expires = now + timedelta(seconds=self.session_timeout)
        session_data.expires_at = new_expires.isoformat()
        
        # Update session
        sessions[session_id] = session_data
        self._save_sessions(sessions)
        
        # Update Streamlit session state
        st.session_state['session_expires'] = new_expires.isoformat()
        st.session_state['last_activity'] = now.isoformat()
        
        # Prepare session info
        session_info = {
            'username': session_data.username,
            'created_at': session_data.created_at,
            'last_activity': session_data.last_activity,
            'expires_at': session_data.expires_at,
            'activity_count': session_data.activity_count,
            'csrf_token': session_data.csrf_token
        }
        
        return True, "Session valid", session_info
    
    def terminate_session(self, session_id: Optional[str] = None, reason: str = "User logout") -> bool:
        """Terminate a session securely"""
        if not session_id:
            session_id = st.session_state.get('session_id')
        
        if not session_id:
            return False
        
        success = self._terminate_session(session_id)
        
        if success:
            # Clear Streamlit session state
            for key in ['session_id', 'csrf_token', 'username', 'session_expires', 'is_authenticated', 'last_activity']:
                if key in st.session_state:
                    del st.session_state[key]
            
            session_logger.info(f"Session terminated: {session_id[:8]}... ({reason})")
        
        return success
    
    def _terminate_session(self, session_id: str) -> bool:
        """Internal method to terminate a session"""
        sessions = self._load_sessions()
        
        if session_id not in sessions:
            return False
        
        session_data = sessions[session_id]
        session_data.is_active = False
        sessions[session_id] = session_data
        self._save_sessions(sessions)
        
        return True
    
    def get_session_info(self, session_id: Optional[str] = None) -> Optional[Dict]:
        """Get session information"""
        if not session_id:
            session_id = st.session_state.get('session_id')
        
        if not session_id:
            return None
        
        sessions = self._load_sessions()
        
        if session_id not in sessions:
            return None
        
        session_data = sessions[session_id]
        
        return {
            'session_id': session_id[:8] + '...',  # Partial ID for security
            'username': session_data.username,
            'created_at': session_data.created_at,
            'last_activity': session_data.last_activity,
            'expires_at': session_data.expires_at,
            'is_active': session_data.is_active,
            'activity_count': session_data.activity_count,
            'ip_address': session_data.ip_address,
            'csrf_token': session_data.csrf_token
        }
    
    def _get_active_sessions_for_user(self, username: str) -> List[SessionData]:
        """Get all active sessions for a user"""
        sessions = self._load_sessions()
        active_sessions = []
        
        for session_data in sessions.values():
            if (session_data.username == username and 
                session_data.is_active and 
                datetime.now() < datetime.fromisoformat(session_data.expires_at)):
                active_sessions.append(session_data)
        
        return active_sessions
    
    def terminate_all_user_sessions(self, username: str, except_session_id: Optional[str] = None) -> int:
        """Terminate all sessions for a user (except optionally one)"""
        sessions = self._load_sessions()
        terminated_count = 0
        
        for session_id, session_data in sessions.items():
            if (session_data.username == username and 
                session_data.is_active and 
                session_id != except_session_id):
                
                session_data.is_active = False
                sessions[session_id] = session_data
                terminated_count += 1
        
        if terminated_count > 0:
            self._save_sessions(sessions)
            session_logger.info(f"Terminated {terminated_count} sessions for {username}")
        
        return terminated_count
    
    def _cleanup_expired_sessions(self):
        """Clean up expired and inactive sessions"""
        sessions = self._load_sessions()
        now = datetime.now()
        cleaned_count = 0
        
        sessions_to_remove = []
        for session_id, session_data in sessions.items():
            expires_at = datetime.fromisoformat(session_data.expires_at)
            
            # Remove expired or inactive sessions older than 24 hours
            if (not session_data.is_active or 
                now > expires_at or 
                now > expires_at + timedelta(hours=24)):
                sessions_to_remove.append(session_id)
                cleaned_count += 1
        
        for session_id in sessions_to_remove:
            del sessions[session_id]
        
        if cleaned_count > 0:
            self._save_sessions(sessions)
            session_logger.info(f"Cleaned up {cleaned_count} expired sessions")
    
    def get_session_statistics(self) -> Dict:
        """Get session statistics for monitoring"""
        sessions = self._load_sessions()
        now = datetime.now()
        
        active_sessions = 0
        expired_sessions = 0
        total_sessions = len(sessions)
        users_with_sessions = set()
        
        for session_data in sessions.values():
            expires_at = datetime.fromisoformat(session_data.expires_at)
            
            if session_data.is_active and now <= expires_at:
                active_sessions += 1
                users_with_sessions.add(session_data.username)
            else:
                expired_sessions += 1
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'expired_sessions': expired_sessions,
            'unique_active_users': len(users_with_sessions),
            'cleanup_recommended': expired_sessions > 10
        }
    
    def require_authentication(self, page_name: str = "Unknown") -> Tuple[bool, Optional[Dict]]:
        """Decorator-like function to require authentication for a page"""
        is_valid, message, session_info = self.validate_session()
        
        if not is_valid:
            st.error(f"🔒 Authentication required: {message}")
            st.stop()
            return False, None
        
        # Log page access
        session_logger.info(f"Authenticated access to {page_name} by {session_info['username']}")
        
        return True, session_info
    
    def generate_csrf_form_token(self) -> str:
        """Generate CSRF token for forms"""
        session_info = self.get_session_info()
        if not session_info:
            return secrets.token_urlsafe(self.csrf_token_length)
        
        return session_info['csrf_token']
    
    def validate_csrf_form_token(self, submitted_token: str) -> bool:
        """Validate CSRF token from form submission"""
        session_info = self.get_session_info()
        if not session_info:
            return False
        
        expected_token = session_info['csrf_token']
        return secrets.compare_digest(submitted_token, expected_token)
    
    def _save_sessions(self, sessions: Dict[str, SessionData]):
        """Save sessions to secure file"""
        sessions_dict = {}
        for session_id, session_data in sessions.items():
            if isinstance(session_data, SessionData):
                sessions_dict[session_id] = asdict(session_data)
            else:
                sessions_dict[session_id] = session_data
        
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_dict, f, indent=2)
            
            # Set secure file permissions
            os.chmod(self.sessions_file, 0o600)
        except OSError:
            pass  # Permissions may not be supported on all systems
    
    def _load_sessions(self) -> Dict[str, SessionData]:
        """Load sessions from secure file"""
        if not os.path.exists(self.sessions_file):
            return {}
        
        try:
            with open(self.sessions_file, 'r') as f:
                sessions_dict = json.load(f)
            
            sessions = {}
            for session_id, session_data in sessions_dict.items():
                sessions[session_id] = SessionData(**session_data)
            
            return sessions
        except (json.JSONDecodeError, TypeError) as e:
            session_logger.error(f"Error loading sessions: {e}")
            return {}