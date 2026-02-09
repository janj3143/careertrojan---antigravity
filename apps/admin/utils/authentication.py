"""
Enhanced Authentication System for IntelliCV Admin Portal
Provides secure authentication with proper error handling, type hints, and session management
"""

from typing import Optional, Dict, Any, Tuple
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
import json
import sqlite3
from dataclasses import dataclass, asdict
import streamlit as st

from utils.logging_config import LoggingMixin, auth_logger


@dataclass
class UserSession:
    """User session data structure"""
    user_id: str
    username: str
    session_token: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class LoginAttempt:
    """Login attempt tracking"""
    username: str
    ip_address: Optional[str]
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None


class AuthenticationError(Exception):
    """Base authentication error"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    pass


class AccountLockedError(AuthenticationError):
    """Account temporarily locked due to failed attempts"""
    pass


class SessionExpiredError(AuthenticationError):
    """User session has expired"""
    pass


class AuthenticationManager(LoggingMixin):
    """Enhanced authentication manager with security features"""
    
    def __init__(self, 
                 db_path: Optional[Path] = None,
                 session_timeout: timedelta = timedelta(hours=1),
                 inactivity_timeout: timedelta = timedelta(minutes=30),
                 max_attempts: int = 3,
                 lockout_duration: timedelta = timedelta(minutes=30)):
        super().__init__()
        
        self.db_path = db_path or Path("secure_credentials.db")
        self.session_timeout = session_timeout
        self.inactivity_timeout = inactivity_timeout  # New: timeout for inactive users
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        
        # In-memory session storage (use Redis in production)
        self.active_sessions: Dict[str, UserSession] = {}
        self.failed_attempts: Dict[str, list] = {}
        
        self._initialize_database()
        self.log_info("Authentication manager initialized", 
                     session_timeout=session_timeout.total_seconds(),
                     inactivity_timeout=inactivity_timeout.total_seconds(),
                     max_attempts=max_attempts,
                     lockout_duration=lockout_duration.total_seconds())
    
    def _initialize_database(self) -> None:
        """Initialize the authentication database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_login TEXT,
                        is_active INTEGER DEFAULT 1,
                        failed_attempts INTEGER DEFAULT 0,
                        locked_until TEXT
                    )
                ''')
                
                # Login attempts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS login_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        ip_address TEXT,
                        timestamp TEXT NOT NULL,
                        success INTEGER NOT NULL,
                        failure_reason TEXT
                    )
                ''')
                
                # Sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_token TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_activity TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        is_active INTEGER DEFAULT 1
                    )
                ''')
                
                conn.commit()
                self.log_info("Database initialized successfully")
                
        except Exception as e:
            self.log_error("Failed to initialize database", exc_info=True)
            raise AuthenticationError(f"Database initialization failed: {e}")
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        
        return password_hash, salt
    
    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        password_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(password_hash, stored_hash)
    
    def _generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def _is_account_locked(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """Check if account is currently locked"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT locked_until FROM users WHERE username = ?',
                    (username,)
                )
                result = cursor.fetchone()
                
                if result and result[0]:
                    locked_until = datetime.fromisoformat(result[0])
                    if datetime.now() < locked_until:
                        return True, locked_until
                    else:
                        # Unlock account
                        cursor.execute(
                            'UPDATE users SET locked_until = NULL, failed_attempts = 0 WHERE username = ?',
                            (username,)
                        )
                        conn.commit()
                        return False, None
                
                return False, None
                
        except Exception as e:
            self.log_error("Error checking account lock status", exc_info=True)
            return True, None  # Fail safe
    
    def _record_login_attempt(self, username: str, success: bool, 
                            ip_address: Optional[str] = None,
                            failure_reason: Optional[str] = None) -> None:
        """Record login attempt in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO login_attempts 
                    (username, ip_address, timestamp, success, failure_reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    username,
                    ip_address,
                    datetime.now().isoformat(),
                    1 if success else 0,
                    failure_reason
                ))
                conn.commit()
                
        except Exception as e:
            self.log_error("Failed to record login attempt", exc_info=True)
    
    def _update_failed_attempts(self, username: str, increment: bool = True) -> None:
        """Update failed attempt count for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if increment:
                    cursor.execute('''
                        UPDATE users 
                        SET failed_attempts = failed_attempts + 1 
                        WHERE username = ?
                    ''', (username,))
                    
                    # Check if we need to lock the account
                    cursor.execute(
                        'SELECT failed_attempts FROM users WHERE username = ?',
                        (username,)
                    )
                    result = cursor.fetchone()
                    
                    if result and result[0] >= self.max_attempts:
                        locked_until = datetime.now() + self.lockout_duration
                        cursor.execute('''
                            UPDATE users 
                            SET locked_until = ? 
                            WHERE username = ?
                        ''', (locked_until.isoformat(), username))
                        
                        self.log_warning("Account locked due to failed attempts",
                                       username=username,
                                       locked_until=locked_until.isoformat())
                else:
                    # Reset failed attempts on successful login
                    cursor.execute('''
                        UPDATE users 
                        SET failed_attempts = 0, locked_until = NULL, last_login = ?
                        WHERE username = ?
                    ''', (datetime.now().isoformat(), username))
                
                conn.commit()
                
        except Exception as e:
            self.log_error("Failed to update failed attempts", exc_info=True)
    
    def create_user(self, username: str, password: str, user_id: Optional[str] = None) -> bool:
        """Create a new user account"""
        try:
            if user_id is None:
                user_id = secrets.token_urlsafe(16)
            
            password_hash, salt = self._hash_password(password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users 
                    (user_id, username, password_hash, salt, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    username,
                    password_hash,
                    salt,
                    datetime.now().isoformat()
                ))
                conn.commit()
            
            self.log_info("User created successfully", username=username, user_id=user_id)
            return True
            
        except sqlite3.IntegrityError:
            self.log_warning("Username already exists", username=username)
            return False
        except Exception as e:
            self.log_error("Failed to create user", exc_info=True)
            return False
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: Optional[str] = None) -> Optional[UserSession]:
        """Authenticate user and create session"""
        self.log_info("Authentication attempt", username=username, ip_address=ip_address)
        
        try:
            # Check if account is locked
            is_locked, locked_until = self._is_account_locked(username)
            if is_locked:
                self.log_warning("Authentication failed - account locked", 
                               username=username, locked_until=locked_until)
                self._record_login_attempt(username, False, ip_address, "account_locked")
                raise AccountLockedError(f"Account locked until {locked_until}")
            
            # Verify credentials
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_id, password_hash, salt, is_active 
                    FROM users 
                    WHERE username = ?
                ''', (username,))
                result = cursor.fetchone()
                
                if not result:
                    self.log_warning("Authentication failed - user not found", username=username)
                    self._record_login_attempt(username, False, ip_address, "user_not_found")
                    raise InvalidCredentialsError("Invalid username or password")
                
                user_id, stored_hash, salt, is_active = result
                
                if not is_active:
                    self.log_warning("Authentication failed - account disabled", username=username)
                    self._record_login_attempt(username, False, ip_address, "account_disabled")
                    raise InvalidCredentialsError("Account is disabled")
                
                if not self._verify_password(password, stored_hash, salt):
                    self.log_warning("Authentication failed - invalid password", username=username)
                    self._record_login_attempt(username, False, ip_address, "invalid_password")
                    self._update_failed_attempts(username, increment=True)
                    raise InvalidCredentialsError("Invalid username or password")
            
            # Create session
            session_token = self._generate_session_token()
            now = datetime.now()
            expires_at = now + self.session_timeout
            
            session = UserSession(
                user_id=user_id,
                username=username,
                session_token=session_token,
                created_at=now,
                last_activity=now,
                expires_at=expires_at,
                ip_address=ip_address
            )
            
            # Store session
            self.active_sessions[session_token] = session
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_sessions 
                    (session_token, user_id, created_at, last_activity, expires_at, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_token,
                    user_id,
                    now.isoformat(),
                    now.isoformat(),
                    expires_at.isoformat(),
                    ip_address
                ))
                conn.commit()
            
            # Reset failed attempts
            self._update_failed_attempts(username, increment=False)
            self._record_login_attempt(username, True, ip_address)
            
            self.log_info("Authentication successful", 
                         username=username, user_id=user_id, session_token=session_token)
            
            return session
            
        except (InvalidCredentialsError, AccountLockedError):
            raise
        except Exception as e:
            self.log_error("Authentication system error", exc_info=True)
            raise AuthenticationError(f"Authentication system error: {e}")
    
    def validate_session(self, session_token: str) -> Optional[UserSession]:
        """Validate and refresh session"""
        if session_token not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_token]
        now = datetime.now()
        
        # Check if session expired (absolute timeout)
        if now > session.expires_at:
            self.logout(session_token)
            self.log_info("Session expired (absolute timeout)", session_token=session_token, user_id=session.user_id)
            raise SessionExpiredError("Session has expired")
        
        # Check if user has been inactive too long
        inactive_duration = now - session.last_activity
        if inactive_duration > self.inactivity_timeout:
            self.logout(session_token)
            self.log_info("Session expired due to inactivity", 
                         session_token=session_token, 
                         user_id=session.user_id,
                         inactive_duration_minutes=inactive_duration.total_seconds() / 60)
            raise SessionExpiredError(f"Session expired due to inactivity after {self.inactivity_timeout}")
        
        # Update last activity but keep original expiration time
        session.last_activity = now
        
        # Update in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = ?, expires_at = ?
                    WHERE session_token = ?
                ''', (
                    now.isoformat(),
                    session.expires_at.isoformat(),
                    session_token
                ))
                conn.commit()
        except Exception as e:
            self.log_error("Failed to update session", exc_info=True)
        
        return session
    
    def logout(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        try:
            if session_token in self.active_sessions:
                session = self.active_sessions[session_token]
                del self.active_sessions[session_token]
                
                # Deactivate in database
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE user_sessions 
                        SET is_active = 0 
                        WHERE session_token = ?
                    ''', (session_token,))
                    conn.commit()
                
                self.log_info("User logged out", session_token=session_token, user_id=session.user_id)
                return True
            
            return False
            
        except Exception as e:
            self.log_error("Logout error", exc_info=True)
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        try:
            now = datetime.now()
            expired_tokens = [
                token for token, session in self.active_sessions.items()
                if now > session.expires_at
            ]
            
            for token in expired_tokens:
                del self.active_sessions[token]
            
            # Clean up database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE user_sessions 
                    SET is_active = 0 
                    WHERE expires_at < ? AND is_active = 1
                ''', (now.isoformat(),))
                conn.commit()
            
            if expired_tokens:
                self.log_info("Cleaned up expired sessions", count=len(expired_tokens))
            
            return len(expired_tokens)
            
        except Exception as e:
            self.log_error("Failed to cleanup expired sessions", exc_info=True)
            return 0


# Streamlit integration helpers
def get_current_session() -> Optional[UserSession]:
    """Get current user session from Streamlit session state"""
    if 'session_token' not in st.session_state:
        return None
    
    auth_manager = AuthenticationManager()
    try:
        return auth_manager.validate_session(st.session_state.session_token)
    except SessionExpiredError:
        st.session_state.clear()
        return None


def require_authentication() -> UserSession:
    """Decorator/helper to require authentication for Streamlit pages"""
    session = get_current_session()
    if not session:
        st.error("Please log in to access this page")
        st.switch_page("main.py")
        st.stop()
    return session


def check_session_activity() -> Optional[UserSession]:
    """Check session activity and show timeout warnings"""
    if 'session_token' not in st.session_state:
        return None
    
    auth_manager = AuthenticationManager()
    try:
        session = auth_manager.validate_session(st.session_state.session_token)
        
        # Calculate time until inactivity timeout
        now = datetime.now()
        time_since_activity = now - session.last_activity
        time_until_timeout = auth_manager.inactivity_timeout - time_since_activity
        
        # Show warning if close to timeout (5 minutes remaining)
        if time_until_timeout.total_seconds() < 300:  # 5 minutes
            minutes_left = int(time_until_timeout.total_seconds() / 60)
            if minutes_left > 0:
                st.warning(f"⚠️ Your session will expire in {minutes_left} minute(s) due to inactivity. Click anywhere to stay active.")
            else:
                st.error("🔒 Your session has expired due to inactivity. Please log in again.")
                st.session_state.clear()
                st.rerun()
        
        return session
        
    except SessionExpiredError as e:
        st.error(f"🔒 {str(e)}")
        st.session_state.clear()
        st.rerun()
        return None


def login_form() -> Optional[UserSession]:
    """Display login form and handle authentication"""
    with st.form("login_form"):
        st.subheader("Admin Portal Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit and username and password:
            try:
                auth_manager = AuthenticationManager()
                session = auth_manager.authenticate_user(username, password)
                st.session_state.session_token = session.session_token
                st.session_state.user_id = session.user_id
                st.session_state.username = session.username
                st.success("Login successful!")
                st.rerun()
                return session
            except InvalidCredentialsError:
                st.error("Invalid username or password")
            except AccountLockedError as e:
                st.error(str(e))
            except AuthenticationError as e:
                st.error(f"Authentication error: {e}")
    
    return None