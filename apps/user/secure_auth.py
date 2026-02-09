
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
Enhanced Authentication Module for IntelliCV-AI User Portal
Compatible with admin_portal_final authentication standards
Includes GDPR compliance and security features
"""

import streamlit as st
import hashlib
import secrets
import re
import pyotp
import qrcode
from io import BytesIO
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class UserAuthenticator:
    """Enhanced user authentication system matching admin portal standards"""
    
    def __init__(self):
        self.credentials_file = "user_credentials.json"
        self.consent_log_file = "user_consent_log.json"
        self.security_log_file = "security_events.json"
        self.min_password_length = 8
        self.max_login_attempts = 3
        self.lockout_duration = 3600  # 1 hour in seconds
        
    def _load_credentials(self) -> Dict:
        """Load user credentials from secure storage"""
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_credentials(self, credentials: Dict):
        """Save user credentials securely"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
        except Exception as e:
            st.error(f"Failed to save credentials: {e}")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Generate cryptographic salt"""
        return secrets.token_hex(32)
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, str, int]:
        """Validate password strength and return score"""
        score = 0
        feedback = []
        
        if len(password) >= self.min_password_length:
            score += 1
        else:
            feedback.append(f"At least {self.min_password_length} characters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("At least one uppercase letter")
        
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("At least one lowercase letter")
            
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("At least one number")
            
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("At least one special character")
        
        # Check for common weak passwords
        weak_passwords = ['password', 'admin', 'admin123', '12345678', 'qwerty', 'letmein']
        if password.lower() in weak_passwords:
            return False, "Password is too common and insecure", 0
        
        strength_levels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong", 5: "Very Strong"}
        strength = strength_levels[score]
        
        is_strong = score >= 3
        message = f"Password strength: {strength}"
        if feedback:
            message += f". Missing: {', '.join(feedback)}"
        
        return is_strong, message, score
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _check_lockout(self, email: str) -> Tuple[bool, int]:
        """Check if user is locked out due to failed attempts"""
        credentials = self._load_credentials()
        user_data = credentials.get(email, {})
        
        failed_attempts = user_data.get('failed_attempts', 0)
        last_attempt = user_data.get('last_failed_attempt')
        
        if failed_attempts >= self.max_login_attempts and last_attempt:
            last_attempt_time = datetime.fromisoformat(last_attempt)
            time_since_last = (datetime.now() - last_attempt_time).total_seconds()
            
            if time_since_last < self.lockout_duration:
                remaining_time = int(self.lockout_duration - time_since_last)
                return True, remaining_time
            else:
                # Reset failed attempts after lockout period
                user_data['failed_attempts'] = 0
                user_data['last_failed_attempt'] = None
                credentials[email] = user_data
                self._save_credentials(credentials)
        
        return False, 0
    
    def _log_security_event(self, event_type: str, email: str, details: Dict = None):
        """Log security events for audit trail"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'email': email,
            'ip_address': 'localhost',  # In production, get real IP
            'details': details or {}
        }
        
        try:
            if os.path.exists(self.security_log_file):
                with open(self.security_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(event)
            
            # Keep only last 1000 events
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.security_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception:
            pass  # Silent fail for logging
    
    def _log_consent(self, email: str, consent_type: str, consent_given: bool, details: Dict = None):
        """Log GDPR consent decisions"""
        consent_event = {
            'timestamp': datetime.now().isoformat(),
            'email': email,
            'consent_type': consent_type,
            'consent_given': consent_given,
            'details': details or {}
        }
        
        try:
            if os.path.exists(self.consent_log_file):
                with open(self.consent_log_file, 'r') as f:
                    consents = json.load(f)
            else:
                consents = []
            
            consents.append(consent_event)
            
            with open(self.consent_log_file, 'w') as f:
                json.dump(consents, f, indent=2)
        except Exception:
            pass
    
    def register_user(self, email: str, password: str, full_name: str, 
                     enable_2fa: bool = False, marketing_consent: bool = False) -> Tuple[bool, str]:
        """Register new user with enhanced security"""
        
        # Validate email format
        if not self._validate_email(email):
            return False, "Invalid email format"
        
        # Check if user already exists
        credentials = self._load_credentials()
        if email in credentials:
            self._log_security_event('registration_attempt_existing_user', email)
            return False, "Email already registered"
        
        # Validate password strength
        is_strong, message, score = self._validate_password_strength(password)
        if not is_strong:
            return False, message
        
        # Generate salt and hash password
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)
        
        # Generate 2FA secret if enabled
        totp_secret = pyotp.random_base32() if enable_2fa else None
        
        # Create user record
        user_data = {
            'email': email,
            'full_name': full_name,
            'password_hash': password_hash,
            'salt': salt,
            'created_at': datetime.now().isoformat(),
            'email_verified': False,  # In production, send verification email
            '2fa_enabled': enable_2fa,
            'totp_secret': totp_secret,
            'failed_attempts': 0,
            'last_login': None,
            'password_changed_at': datetime.now().isoformat(),
            'marketing_consent': marketing_consent,
            'data_processing_consent': True,  # Required for service
            'subscription_tier': 'free',
            'account_status': 'active'
        }
        
        credentials[email] = user_data
        self._save_credentials(credentials)
        
        # Log consent decisions
        self._log_consent(email, 'data_processing', True, {'purpose': 'service_provision'})
        self._log_consent(email, 'marketing', marketing_consent, {'source': 'registration'})
        
        # Log security event
        self._log_security_event('user_registration', email, {
            '2fa_enabled': enable_2fa,
            'marketing_consent': marketing_consent
        })
        
        return True, "Registration successful"
    
    def _load_admin_portal_users(self) -> Dict:
        """Load users from SANDBOX admin portal registration data"""
        import os
        from pathlib import Path
        
        admin_reg_path = Path("C:/IntelliCV/SANDBOX/admin_portal/data/user_registrations")
        admin_users = {}
        
        if admin_reg_path.exists():
            try:
                for user_file in admin_reg_path.glob("*.json"):
                    with open(user_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                        email = user_data.get('email')
                        if email:
                            admin_users[email] = user_data
            except Exception as e:
                self._log_security_event('admin_portal_sync_error', 'system', {'error': str(e)})
        
        return admin_users

    def _convert_admin_user_format(self, admin_user: Dict) -> Dict:
        """Convert admin portal user format to user portal format"""
        return {
            'email': admin_user.get('email', ''),
            'full_name': f"{admin_user.get('first_name', '')} {admin_user.get('last_name', '')}".strip(),
            'password_hash': admin_user.get('password_hash', ''),
            'salt': admin_user.get('salt', ''),
            'created_at': admin_user.get('registration_date', datetime.now().isoformat()),
            'email_verified': admin_user.get('email_confirmed', False),
            '2fa_enabled': admin_user.get('security_features', {}).get('two_factor_auth_enabled', False),
            'totp_secret': admin_user.get('security_features', {}).get('totp_secret', ''),
            'failed_attempts': 0,
            'last_login': admin_user.get('last_login', None),
            'password_changed_at': admin_user.get('password_changed_at', admin_user.get('registration_date', datetime.now().isoformat())),
            'marketing_consent': admin_user.get('newsletter_opt_in', False),
            'data_processing_consent': True,
            'subscription_tier': 'free',
            'account_status': 'active' if admin_user.get('status') == 'active' else 'pending'
        }

    def authenticate_user(self, email: str, password: str, totp_code: Optional[str] = None) -> Tuple[bool, str, Dict]:
        """Authenticate user with enhanced security and SANDBOX admin portal sync"""
        
        # Check if user is locked out
        is_locked, remaining_time = self._check_lockout(email)
        if is_locked:
            minutes = remaining_time // 60
            seconds = remaining_time % 60
            return False, f"Account locked. Try again in {minutes}m {seconds}s", {}
        
        # Load both local credentials and admin portal users
        credentials = self._load_credentials()
        admin_users = self._load_admin_portal_users()
        
        # Check if user exists in either system
        user_data = None
        auth_source = None
        
        if email in credentials:
            user_data = credentials[email]
            auth_source = "local"
        elif email in admin_users:
            user_data = admin_users[email]
            auth_source = "admin_portal"
            # Convert admin portal format to user portal format for authentication
            user_data = self._convert_admin_user_format(user_data)
        else:
            self._log_security_event('login_attempt_unknown_user', email)
            return False, "Invalid credentials", {}
        
        # Log the authentication source
        self._log_security_event('login_attempt', email, {'auth_source': auth_source})
        
        # Check account status
        if user_data.get('account_status') != 'active':
            return False, "Account suspended. Contact support.", {}
        
        # Verify password
        stored_hash = user_data['password_hash']
        salt = user_data['salt']
        provided_hash = self._hash_password(password, salt)
        
        if provided_hash != stored_hash:
            # Increment failed attempts
            user_data['failed_attempts'] = user_data.get('failed_attempts', 0) + 1
            user_data['last_failed_attempt'] = datetime.now().isoformat()
            
            # Only save to local credentials if it's a local user
            if auth_source == "local":
                credentials[email] = user_data
                self._save_credentials(credentials)
            
            self._log_security_event('login_failed_password', email, {'auth_source': auth_source})
            return False, "Invalid credentials", {}
        
        # Check 2FA if enabled
        if user_data.get('2fa_enabled'):
            if not totp_code:
                return False, "2FA code required", {'requires_2fa': True}
            
            totp = pyotp.TOTP(user_data['totp_secret'])
            if not totp.verify(totp_code):
                user_data['failed_attempts'] = user_data.get('failed_attempts', 0) + 1
                user_data['last_failed_attempt'] = datetime.now().isoformat()
                
                # Only save to local credentials if it's a local user
                if auth_source == "local":
                    credentials[email] = user_data
                    self._save_credentials(credentials)
                
                self._log_security_event('login_failed_2fa', email, {'auth_source': auth_source})
                return False, "Invalid 2FA code", {}
        
        # Reset failed attempts on successful login
        user_data['failed_attempts'] = 0
        user_data['last_failed_attempt'] = None
        user_data['last_login'] = datetime.now().isoformat()
        
        # Only save to local credentials if it's a local user
        if auth_source == "local":
            credentials[email] = user_data
            self._save_credentials(credentials)
        
        # Log successful login
        self._log_security_event('login_success', email, {'auth_source': auth_source})
        
        # Return user session data
        session_data = {
            'email': email,
            'full_name': user_data['full_name'],
            'subscription_tier': user_data.get('subscription_tier', 'free'),
            '2fa_enabled': user_data.get('2fa_enabled', False),
            'email_verified': user_data.get('email_verified', False),
            'marketing_consent': user_data.get('marketing_consent', False)
        }
        
        return True, "Login successful", session_data
    
    def get_user_info(self, email: str) -> Optional[Dict]:
        """Get user information from both local and admin portal sources"""
        credentials = self._load_credentials()
        admin_users = self._load_admin_portal_users()
        
        if email in credentials:
            return credentials[email]
        elif email in admin_users:
            return self._convert_admin_user_format(admin_users[email])
        
        return None
    
    def list_all_users(self) -> Dict[str, Dict]:
        """List all users from both local and admin portal sources"""
        all_users = {}
        
        # Add local users
        credentials = self._load_credentials()
        for email, user_data in credentials.items():
            all_users[email] = {**user_data, 'source': 'local'}
        
        # Add admin portal users
        admin_users = self._load_admin_portal_users()
        for email, user_data in admin_users.items():
            if email not in all_users:  # Don't override local users
                converted_user = self._convert_admin_user_format(user_data)
                all_users[email] = {**converted_user, 'source': 'admin_portal'}
        
        return all_users
    
    def generate_2fa_qr(self, email: str) -> Optional[BytesIO]:
        """Generate QR code for 2FA setup"""
        credentials = self._load_credentials()
        if email not in credentials:
            return None
        
        user_data = credentials[email]
        if not user_data.get('totp_secret'):
            return None
        
        totp = pyotp.TOTP(user_data['totp_secret'])
        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name="IntelliCV-AI"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    def reset_password_request(self, email: str) -> Tuple[bool, str]:
        """Request password reset (mock implementation)"""
        credentials = self._load_credentials()
        if email not in credentials:
            # Don't reveal if email exists for security
            return True, "If email exists, reset instructions have been sent"
        
        # In production, generate secure token and send email
        reset_token = secrets.token_urlsafe(32)
        reset_expires = (datetime.now() + timedelta(hours=1)).isoformat()
        
        user_data = credentials[email]
        user_data['reset_token'] = reset_token
        user_data['reset_expires'] = reset_expires
        credentials[email] = user_data
        self._save_credentials(credentials)
        
        self._log_security_event('password_reset_requested', email)
        
        return True, "Password reset instructions sent to your email"
    
    def get_user_data(self, email: str) -> Dict:
        """Get user data for authenticated user"""
        credentials = self._load_credentials()
        return credentials.get(email, {})
    
    def update_consent(self, email: str, consent_type: str, consent_given: bool, details: Dict = None):
        """Update user consent preferences"""
        credentials = self._load_credentials()
        if email in credentials:
            credentials[email][f'{consent_type}_consent'] = consent_given
            self._save_credentials(credentials)
            
            self._log_consent(email, consent_type, consent_given, details)
    
    def delete_user_data(self, email: str) -> bool:
        """Delete user data (GDPR right to be forgotten)"""
        credentials = self._load_credentials()
        if email in credentials:
            del credentials[email]
            self._save_credentials(credentials)
            
            self._log_security_event('user_data_deleted', email, {'reason': 'user_request'})
            return True
        return False

# GDPR Compliance Module
class GDPRCompliance:
    """GDPR compliance utilities for user portal"""
    
    @staticmethod
    def render_privacy_notice():
        """Render GDPR privacy notice"""
        st.markdown("""
        ### 🛡️ Privacy Notice (GDPR Compliance)
        
        **Data Controller**: IntelliCV-AI Platform
        
        **Data We Collect**:
        - Account information (name, email)
        - Resume and career data you upload
        - Usage analytics and platform interactions
        - Payment information (processed by Stripe)
        
        **Legal Basis**: 
        - Contract performance (providing our services)
        - Legitimate interest (improving our platform)
        - Consent (marketing communications)
        
        **Your Rights**:
        - Access your data
        - Rectify inaccurate data
        - Erase your data
        - Data portability
        - Withdraw consent
        
        **Data Retention**: Account data retained while account is active, then 30 days after deletion
        
        **Contact**: privacy@intellicv-ai.com
        """)
    
    @staticmethod
    def render_consent_checkboxes():
        """Render GDPR consent checkboxes"""
        st.markdown("### 📋 Consent Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            data_processing = st.checkbox(
                "✅ **Required**: Data processing for service provision",
                value=True,
                disabled=True,
                help="Required to provide our services. Cannot be disabled."
            )
            
            marketing_emails = st.checkbox(
                "📧 Marketing emails and product updates",
                value=False,
                help="Receive news, tips, and product updates via email"
            )
        
        with col2:
            analytics = st.checkbox(
                "📊 Anonymous usage analytics",
                value=True,
                help="Help us improve the platform with anonymous usage data"
            )
            
            third_party = st.checkbox(
                "🤝 Share anonymized data with partners",
                value=False,
                help="Allow sharing of anonymized insights with career partners"
            )
        
        return {
            'data_processing': data_processing,
            'marketing_emails': marketing_emails,
            'analytics': analytics,
            'third_party': third_party
        }
    
    @staticmethod
    def render_cookie_notice():
        """Render cookie consent notice"""
        if 'cookie_consent' not in st.session_state:
            st.session_state.cookie_consent = False
        
        if not st.session_state.cookie_consent:
            st.info("""
            🍪 **Cookie Notice**: We use essential cookies for authentication and optional cookies for analytics. 
            By continuing to use this site, you consent to our cookie policy.
            """)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("Accept All Cookies", type="primary"):
                    st.session_state.cookie_consent = True
                    st.rerun()
            with col3:
                if st.button("Essential Only"):
                    st.session_state.cookie_consent = True
                    st.session_state.analytics_cookies = False
                    st.rerun()

# Initialize global authenticator
if 'authenticator' not in st.session_state:
    st.session_state.authenticator = UserAuthenticator()