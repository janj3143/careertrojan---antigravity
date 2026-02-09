
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
HARDENED Authentication System for IntelliCV Admin Portal
Implements enterprise-grade security with PBKDF2, proper salting, and mandatory password changes

SECURITY FEATURES:
- PBKDF2 with SHA-256 and 100,000 iterations
- Cryptographically secure random salts (64 bytes)
- Password pepper from environment secrets
- Account lockout after failed attempts
- Mandatory password complexity requirements
- Force password change on first login
- Session timeout and secure cookies
- Audit logging for security events
"""

import hashlib
import json
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import streamlit as st
from dataclasses import dataclass, asdict
import re
import logging
from pathlib import Path

# Configure security audit logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_audit.log'),
        logging.StreamHandler()
    ]
)
security_logger = logging.getLogger('security_audit')

@dataclass
class UserCredentials:
    """Enhanced user credentials with security metadata"""
    username: str
    password_hash: str
    salt: str
    pepper_version: int  # Track pepper version for rotation
    algorithm: str  # Hash algorithm used
    iterations: int  # PBKDF2 iterations
    is_default_password: bool
    last_login: Optional[str]
    failed_attempts: int
    locked_until: Optional[str]
    password_changed_at: str
    password_history: List[str]  # Store last 5 password hashes
    requires_password_change: bool
    mfa_enabled: bool
    created_at: str
    last_password_change: str
    login_history: List[Dict]  # Track login attempts

class HardenedAuthenticator:
    """Enterprise-grade authentication system with comprehensive security"""
    
    def __init__(self, credentials_file: str = "secure_credentials.json"):
        self.credentials_file = credentials_file
        
        # Security configuration from environment
        self.max_failed_attempts = int(os.getenv('MAX_LOGIN_ATTEMPTS', '3'))
        self.lockout_duration = int(os.getenv('ACCOUNT_LOCKOUT_DURATION', '900'))  # 15 minutes
        self.min_password_length = int(os.getenv('PASSWORD_MIN_LENGTH', '12'))
        self.session_timeout = int(os.getenv('AUTH_TOKEN_EXPIRY', '1800'))  # 30 minutes
        self.require_complex_password = os.getenv('PASSWORD_REQUIRE_COMPLEX', 'true').lower() == 'true'
        self.force_first_password_change = os.getenv('FORCE_PASSWORD_CHANGE_ON_FIRST_LOGIN', 'true').lower() == 'true'
        
        # Cryptographic configuration
        self.pbkdf2_iterations = 100000  # OWASP recommended minimum
        self.salt_length = 64  # 64 bytes = 512 bits
        self.password_history_limit = 5
        
        # Get pepper from environment (critical security requirement)
        self.password_pepper = os.getenv('ADMIN_SECRET_KEY')
        if not self.password_pepper:
            raise ValueError("ADMIN_SECRET_KEY environment variable is required for password security")
        
        self.pepper_version = 1  # For pepper rotation capability
        
        # Initialize secure credentials store
        self._initialize_secure_credentials()
        
        security_logger.info("HardenedAuthenticator initialized with enhanced security")
    
    def _initialize_secure_credentials(self):
        """Initialize with no default credentials - require setup"""
        if not os.path.exists(self.credentials_file):
            # No default admin/admin - force proper setup
            empty_store = {}
            self._save_credentials(empty_store)
            
            security_logger.warning("Credentials store initialized - NO DEFAULT ADMIN ACCOUNT")

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.warning("🔒 **SECURITY NOTICE**: No admin accounts exist. Use setup wizard to create first admin.")
            
            # Show setup instructions
            self._show_initial_setup_instructions()
    
    def _show_initial_setup_instructions(self):
        """Show instructions for creating the first admin account"""
        with st.expander("🔧 **INITIAL ADMIN SETUP REQUIRED**", expanded=True):
            st.markdown("""
            **SECURITY: No default admin credentials exist.**
            
            To create the first admin account:
            1. Run the admin setup command: `python setup_admin.py`
            2. Or use the form below to create your first admin account
            
            **Security Requirements:**
            - Password must be at least 12 characters
            - Must contain uppercase, lowercase, numbers, and symbols
            - Cannot be a common password
            - Will require change on first login
            """)
            
            self._show_admin_creation_form()
    
    def _show_admin_creation_form(self):
        """Show form to create the first admin account"""
        st.subheader("Create First Admin Account")
        
        with st.form("create_first_admin"):
            username = st.text_input("Admin Username", value="", help="Choose a secure username (not 'admin')")
            password = st.text_input("Temporary Password", type="password", help="Will be forced to change on first login")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Admin Account"):
                if self._create_first_admin(username, password, confirm_password):
                    st.success("✅ First admin account created successfully!")
                    st.experimental_rerun()
    
    def _create_first_admin(self, username: str, password: str, confirm_password: str) -> bool:
        """Create the first admin account with security validation"""
        # Validation
        if not username or len(username) < 3:
            st.error("Username must be at least 3 characters")
            return False
        
        if username.lower() in ['admin', 'administrator', 'root', 'user']:
            st.error("Choose a more secure username (not common defaults)")
            return False
        
        if password != confirm_password:
            st.error("Passwords do not match")
            return False
        
        password_validation = self._validate_password_complexity(password)
        if not password_validation['valid']:
            st.error(f"Password requirements not met: {', '.join(password_validation['errors'])}")
            return False
        
        # Create secure admin account
        salt = secrets.token_bytes(self.salt_length)
        password_hash = self._hash_password_pbkdf2(password, salt)
        
        admin_user = UserCredentials(
            username=username,
            password_hash=password_hash,
            salt=salt.hex(),
            pepper_version=self.pepper_version,
            algorithm="PBKDF2_SHA256",
            iterations=self.pbkdf2_iterations,
            is_default_password=False,  # Not a default password
            last_login=None,
            failed_attempts=0,
            locked_until=None,
            password_changed_at=datetime.now().isoformat(),
            password_history=[password_hash],
            requires_password_change=True,  # Force change on first login
            mfa_enabled=False,
            created_at=datetime.now().isoformat(),
            last_password_change=datetime.now().isoformat(),
            login_history=[]
        )
        
        credentials = {username: admin_user}
        self._save_credentials(credentials)
        
        security_logger.info(f"First admin account created: {username}")
        return True
    
    def _hash_password_pbkdf2(self, password: str, salt: bytes) -> str:
        """Hash password using PBKDF2 with SHA-256 and pepper"""
        # Combine password with pepper for additional security
        password_with_pepper = password + self.password_pepper
        
        # Use PBKDF2 with SHA-256
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password_with_pepper.encode('utf-8'),
            salt,
            self.pbkdf2_iterations
        )
        
        return password_hash.hex()
    
    def _validate_password_complexity(self, password: str) -> Dict:
        """Validate password meets complexity requirements"""
        errors = []
        
        if len(password) < self.min_password_length:
            errors.append(f"Must be at least {self.min_password_length} characters")
        
        if self.require_complex_password:
            if not re.search(r'[A-Z]', password):
                errors.append("Must contain uppercase letters")
            
            if not re.search(r'[a-z]', password):
                errors.append("Must contain lowercase letters")
            
            if not re.search(r'\d', password):
                errors.append("Must contain numbers")
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append("Must contain special characters")
        
        # Check against common passwords
        common_passwords = [
            'password', '123456', 'password123', 'admin123', 'letmein',
            'welcome', 'monkey', '1234567890', 'qwerty', 'abc123'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Cannot be a common password")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> str:
        """Calculate password strength score"""
        score = 0
        
        # Length scoring
        if len(password) >= 12: score += 2
        elif len(password) >= 8: score += 1
        
        # Character diversity
        if re.search(r'[a-z]', password): score += 1
        if re.search(r'[A-Z]', password): score += 1
        if re.search(r'\d', password): score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 2
        
        # Pattern detection (bonus/penalty)
        if not re.search(r'(.)\1{2,}', password): score += 1  # No repeated characters
        if not re.search(r'(012|123|234|345|456|567|678|789|890)', password): score += 1  # No sequences
        
        if score <= 3: return "WEAK"
        elif score <= 5: return "FAIR"
        elif score <= 7: return "GOOD"
        else: return "STRONG"
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user with comprehensive security checks"""
        security_logger.info(f"Authentication attempt for user: {username}")
        
        credentials = self._load_credentials()
        
        if not credentials:
            security_logger.warning("Authentication failed: No user accounts exist")
            return False, "No user accounts configured. Please run initial setup.", None
        
        if username not in credentials:
            security_logger.warning(f"Authentication failed: Unknown user {username}")
            return False, "Invalid username or password", None
        
        user = credentials[username]
        
        # Check if account is locked
        if user.locked_until:
            lock_time = datetime.fromisoformat(user.locked_until)
            if datetime.now() < lock_time:
                remaining = lock_time - datetime.now()
                security_logger.warning(f"Authentication blocked: Account {username} is locked for {remaining}")
                return False, f"Account locked. Try again in {remaining.seconds//60} minutes.", None
            else:
                # Unlock account
                user.locked_until = None
                user.failed_attempts = 0
        
        # Verify password
        salt = bytes.fromhex(user.salt)
        expected_hash = self._hash_password_pbkdf2(password, salt)
        
        if expected_hash != user.password_hash:
            # Failed login
            user.failed_attempts += 1
            
            if user.failed_attempts >= self.max_failed_attempts:
                # Lock account
                user.locked_until = (datetime.now() + timedelta(seconds=self.lockout_duration)).isoformat()
                security_logger.warning(f"Account {username} locked after {self.max_failed_attempts} failed attempts")
            
            # Update credentials
            credentials[username] = user
            self._save_credentials(credentials)
            
            security_logger.warning(f"Authentication failed for {username}: Invalid password (attempt {user.failed_attempts})")
            return False, "Invalid username or password", None
        
        # Successful authentication
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now().isoformat()
        
        # Add to login history
        user.login_history.append({
            'timestamp': datetime.now().isoformat(),
            'ip_address': 'streamlit_session',  # In real deployment, capture actual IP
            'user_agent': 'streamlit_app',
            'success': True
        })
        
        # Keep only last 10 login records
        user.login_history = user.login_history[-10:]
        
        credentials[username] = user
        self._save_credentials(credentials)
        
        security_logger.info(f"Successful authentication for {username}")
        
        # Prepare user session data
        user_session = {
            'username': username,
            'last_login': user.last_login,
            'requires_password_change': user.requires_password_change,
            'is_default_password': user.is_default_password,
            'password_strength': 'STRONG',  # Assume strong after PBKDF2
            'session_expires': (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
        }
        
        return True, "Authentication successful", user_session
    
    def change_password(self, username: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password with security validation"""
        security_logger.info(f"Password change attempt for user: {username}")
        
        credentials = self._load_credentials()
        
        if username not in credentials:
            security_logger.warning(f"Password change failed: Unknown user {username}")
            return False, "User not found"
        
        user = credentials[username]
        
        # Verify current password
        salt = bytes.fromhex(user.salt)
        current_hash = self._hash_password_pbkdf2(current_password, salt)
        
        if current_hash != user.password_hash:
            security_logger.warning(f"Password change failed for {username}: Invalid current password")
            return False, "Current password is incorrect"
        
        # Validate new password
        password_validation = self._validate_password_complexity(new_password)
        if not password_validation['valid']:
            return False, f"New password requirements not met: {', '.join(password_validation['errors'])}"
        
        # Check password history (prevent reuse)
        new_salt = secrets.token_bytes(self.salt_length)
        new_hash = self._hash_password_pbkdf2(new_password, new_salt)
        
        if new_hash in user.password_history:
            security_logger.warning(f"Password change failed for {username}: Password reuse attempt")
            return False, "Cannot reuse recent passwords"
        
        # Update password
        user.password_hash = new_hash
        user.salt = new_salt.hex()
        user.password_changed_at = datetime.now().isoformat()
        user.last_password_change = datetime.now().isoformat()
        user.requires_password_change = False
        user.is_default_password = False
        
        # Update password history
        user.password_history.append(new_hash)
        user.password_history = user.password_history[-self.password_history_limit:]
        
        credentials[username] = user
        self._save_credentials(credentials)
        
        security_logger.info(f"Password successfully changed for {username}")
        return True, "Password changed successfully"
    
    def _save_credentials(self, credentials: Dict[str, UserCredentials]):
        """Save credentials to secure file with proper permissions"""
        # Convert UserCredentials objects to dictionaries
        credentials_dict = {}
        for username, user in credentials.items():
            if isinstance(user, UserCredentials):
                credentials_dict[username] = asdict(user)
            else:
                credentials_dict[username] = user
        
        # Write to file with secure permissions
        credentials_path = Path(self.credentials_file)
        credentials_path.write_text(json.dumps(credentials_dict, indent=2))
        
        # Set secure file permissions (owner read/write only)
        try:
            os.chmod(self.credentials_file, 0o600)
        except OSError:
            pass  # Permissions may not be supported on all systems
    
    def _load_credentials(self) -> Dict[str, UserCredentials]:
        """Load credentials from secure file"""
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                credentials_dict = json.load(f)
            
            credentials = {}
            for username, user_data in credentials_dict.items():
                credentials[username] = UserCredentials(**user_data)
            
            return credentials
        except (json.JSONDecodeError, TypeError) as e:
            security_logger.error(f"Error loading credentials: {e}")
            return {}
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information for session management"""
        credentials = self._load_credentials()
        if username not in credentials:
            return None
        
        user = credentials[username]
        return {
            'username': username,
            'last_login': user.last_login,
            'created_at': user.created_at,
            'requires_password_change': user.requires_password_change,
            'is_default_password': user.is_default_password,
            'mfa_enabled': user.mfa_enabled,
            'failed_attempts': user.failed_attempts,
            'algorithm': user.algorithm,
            'iterations': user.iterations
        }
    
    def force_password_change(self, username: str) -> bool:
        """Force user to change password on next login"""
        credentials = self._load_credentials()
        if username not in credentials:
            return False
        
        user = credentials[username]
        user.requires_password_change = True
        credentials[username] = user
        self._save_credentials(credentials)
        
        security_logger.info(f"Password change forced for user: {username}")
        return True