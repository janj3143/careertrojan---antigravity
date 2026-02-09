"""
🔐 IntelliCV-AI Enhanced Authentication System
=============================================
Comprehensive authentication with:
- Password strength validation
- 2FA support (Authenticator app & Mobile PIN)
- Secure login with bcrypt hashing
- Pre-configured test user credentials
"""

import streamlit as st
import hashlib
import re
import pyotp
import qrcode
from io import BytesIO
import base64
import bcrypt
import json
import os
from datetime import datetime, timedelta
import random
import string

class PasswordValidator:
    """Enhanced password strength validation"""
    
    @staticmethod
    def check_strength(password):
        """Check password strength and return score with feedback"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 2
        else:
            feedback.append("❌ At least 8 characters required")
        
        if len(password) >= 12:
            score += 1
            
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("❌ Add lowercase letters")
            
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("❌ Add uppercase letters")
            
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("❌ Add numbers")
            
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', password):
            score += 2
        else:
            feedback.append("❌ Add special characters (!@#$%^&*)")
            
        # Complexity patterns
        if re.search(r'(.)\1{2,}', password):
            score -= 1
            feedback.append("❌ Avoid repeating characters")
            
        # Password strength levels
        if score >= 7:
            strength = "🟢 Very Strong"
            color = "green"
        elif score >= 5:
            strength = "🟡 Strong"
            color = "orange"
        elif score >= 3:
            strength = "🟠 Medium"
            color = "orange"
        else:
            strength = "🔴 Weak"
            color = "red"
            
        return {
            'score': score,
            'strength': strength,
            'color': color,
            'feedback': feedback,
            'is_strong': score >= 5
        }

class TwoFactorAuth:
    """2FA implementation with Authenticator app and Mobile PIN"""
    
    def __init__(self):
        self.app_name = "IntelliCV-AI"
        
    def generate_secret(self, email):
        """Generate a secret key for TOTP"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, email, secret):
        """Generate QR code for authenticator app setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=self.app_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str, totp_uri
    
    def verify_totp_code(self, secret, code):
        """Verify TOTP code from authenticator app"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=2)  # Allow 2 time windows for clock drift
    
    def generate_mobile_pin(self):
        """Generate 6-digit PIN for mobile verification"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_mobile_pin(self, phone_number, pin):
        """Simulate sending PIN to mobile (in production, integrate with SMS service)"""
        # In production, integrate with Twilio, AWS SNS, or similar
        return {
            'success': True,
            'message': f"PIN {pin} sent to {phone_number}",
            'expires_at': datetime.now() + timedelta(minutes=5)
        }

class EnhancedAuthenticator:
    """Enhanced authentication system with 2FA support"""
    
    def __init__(self):
        self.password_validator = PasswordValidator()
        self.two_factor = TwoFactorAuth()
        self.users_file = "secure_users.json"
        self.init_default_users()
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def init_default_users(self):
        """Initialize with default test user"""
        default_users = {
            "janatmainswood@gmail.com": {
                "password_hash": self.hash_password("JanJ3143@?"),
                "name": "Jan Atmainswood",
                "created_at": datetime.now().isoformat(),
                "is_verified": True,
                "two_factor_enabled": False,
                "totp_secret": None,
                "phone_number": None,
                "preferred_2fa": "authenticator",  # or "mobile"
                "failed_attempts": 0,
                "locked_until": None
            }
        }
        
        # Only create if file doesn't exist
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump(default_users, f, indent=2)
    
    def load_users(self):
        """Load users from secure file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_users(self, users):
        """Save users to secure file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def is_account_locked(self, email):
        """Check if account is locked due to failed attempts"""
        users = self.load_users()
        if email in users:
            locked_until = users[email].get('locked_until')
            if locked_until:
                lock_time = datetime.fromisoformat(locked_until)
                if datetime.now() < lock_time:
                    return True, lock_time
                else:
                    # Unlock account
                    users[email]['locked_until'] = None
                    users[email]['failed_attempts'] = 0
                    self.save_users(users)
        return False, None
    
    def handle_failed_login(self, email):
        """Handle failed login attempt"""
        users = self.load_users()
        if email in users:
            users[email]['failed_attempts'] = users[email].get('failed_attempts', 0) + 1
            
            # Lock account after 5 failed attempts for 30 minutes
            if users[email]['failed_attempts'] >= 5:
                users[email]['locked_until'] = (datetime.now() + timedelta(minutes=30)).isoformat()
            
            self.save_users(users)
    
    def authenticate_user(self, email, password):
        """Authenticate user with email and password"""
        # Check if account is locked
        is_locked, locked_until = self.is_account_locked(email)
        if is_locked:
            return {
                'success': False,
                'message': f'Account locked until {locked_until.strftime("%H:%M:%S")}',
                'locked': True
            }
        
        users = self.load_users()
        
        if email in users:
            if self.verify_password(password, users[email]['password_hash']):
                # Reset failed attempts on successful login
                users[email]['failed_attempts'] = 0
                users[email]['locked_until'] = None
                self.save_users(users)
                
                return {
                    'success': True,
                    'user': users[email],
                    'requires_2fa': users[email].get('two_factor_enabled', False)
                }
            else:
                self.handle_failed_login(email)
                return {
                    'success': False,
                    'message': 'Invalid email or password',
                    'locked': False
                }
        else:
            return {
                'success': False,
                'message': 'Invalid email or password',
                'locked': False
            }
    
    def setup_2fa_authenticator(self, email):
        """Setup 2FA with authenticator app"""
        users = self.load_users()
        if email in users:
            secret = self.two_factor.generate_secret(email)
            qr_code, totp_uri = self.two_factor.generate_qr_code(email, secret)
            
            # Store secret temporarily (will be confirmed when user verifies)
            users[email]['temp_totp_secret'] = secret
            self.save_users(users)
            
            return {
                'success': True,
                'qr_code': qr_code,
                'secret': secret,
                'totp_uri': totp_uri
            }
        return {'success': False, 'message': 'User not found'}
    
    def verify_2fa_setup(self, email, code):
        """Verify 2FA setup with code from authenticator"""
        users = self.load_users()
        if email in users and 'temp_totp_secret' in users[email]:
            secret = users[email]['temp_totp_secret']
            if self.two_factor.verify_totp_code(secret, code):
                # Activate 2FA
                users[email]['two_factor_enabled'] = True
                users[email]['totp_secret'] = secret
                users[email]['preferred_2fa'] = 'authenticator'
                del users[email]['temp_totp_secret']
                self.save_users(users)
                
                return {'success': True, 'message': '2FA activated successfully!'}
            else:
                return {'success': False, 'message': 'Invalid verification code'}
        return {'success': False, 'message': 'Setup not found'}
    
    def verify_2fa_login(self, email, code, method='authenticator'):
        """Verify 2FA during login"""
        users = self.load_users()
        if email in users:
            if method == 'authenticator':
                secret = users[email].get('totp_secret')
                if secret and self.two_factor.verify_totp_code(secret, code):
                    return {'success': True, 'message': 'Authentication successful'}
                else:
                    return {'success': False, 'message': 'Invalid authentication code'}
            elif method == 'mobile':
                # Check stored PIN (in production, this would be more sophisticated)
                stored_pin = st.session_state.get('mobile_pin')
                if stored_pin and stored_pin == code:
                    return {'success': True, 'message': 'Authentication successful'}
                else:
                    return {'success': False, 'message': 'Invalid PIN'}
        return {'success': False, 'message': 'User not found'}

def render_password_strength_indicator(password):
    """Render real-time password strength indicator"""
    if password:
        validator = PasswordValidator()
        result = validator.check_strength(password)
        
        # Progress bar
        progress = min(result['score'] / 8, 1.0)
        st.progress(progress)
        
        # Strength label
        st.markdown(f"**Password Strength: {result['strength']}**")
        
        # Feedback
        if result['feedback']:
            st.markdown("**Recommendations:**")
            for feedback in result['feedback']:
                st.write(feedback)
        else:
            st.success("✅ Password meets all security requirements!")
        
        return result['is_strong']
    return False

def render_2fa_setup(authenticator, email):
    """Render 2FA setup interface"""
    st.markdown("### 🔐 Two-Factor Authentication Setup")
    
    method = st.radio(
        "Choose your preferred 2FA method:",
        ["Authenticator App (Recommended)", "Mobile PIN"],
        help="Authenticator apps like Google Authenticator, Authy, or Microsoft Authenticator provide better security"
    )
    
    if method == "Authenticator App (Recommended)":
        st.markdown("#### 📱 Setup Authenticator App")
        st.info("Use Google Authenticator, Authy, Microsoft Authenticator, or similar apps")
        
        if st.button("Generate QR Code"):
            result = authenticator.setup_2fa_authenticator(email)
            if result['success']:
                st.markdown("**Step 1:** Scan this QR code with your authenticator app:")
                st.image(f"data:image/png;base64,{result['qr_code']}", width=200)
                
                st.markdown("**Step 2:** Enter the 6-digit code from your authenticator app:")
                verification_code = st.text_input("Verification Code", max_chars=6, placeholder="123456")
                
                if st.button("Verify & Activate 2FA"):
                    if verification_code:
                        verify_result = authenticator.verify_2fa_setup(email, verification_code)
                        if verify_result['success']:
                            st.success(verify_result['message'])
                            st.session_state['2fa_enabled'] = True
                            st.rerun()
                        else:
                            st.error(verify_result['message'])
                    else:
                        st.warning("Please enter the verification code")
    
    elif method == "Mobile PIN":
        st.markdown("#### 📱 Setup Mobile PIN")
        phone = st.text_input("Phone Number", placeholder="+1234567890")
        
        if st.button("Send Test PIN"):
            if phone:
                pin = authenticator.two_factor.generate_mobile_pin()
                result = authenticator.two_factor.send_mobile_pin(phone, pin)
                
                if result['success']:
                    st.success(f"📱 {result['message']}")
                    st.session_state['mobile_pin'] = pin
                    st.session_state['phone_number'] = phone
                    
                    # Verification
                    entered_pin = st.text_input("Enter PIN received", max_chars=6)
                    if st.button("Verify PIN"):
                        if entered_pin == pin:
                            st.success("✅ Mobile 2FA activated!")
                            st.session_state['2fa_enabled'] = True
                            st.rerun()
                        else:
                            st.error("Invalid PIN")
                else:
                    st.error("Failed to send PIN")
            else:
                st.warning("Please enter your phone number")

def render_login_form(authenticator):
    """Render the main login form"""
    st.markdown("""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0; font-size: 3em;'>🔐 IntelliCV-AI Login</h1>
        <p style='color: white; margin: 10px 0 0 0; font-size: 1.3em;'>Secure Authentication with 2FA Support</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        st.markdown("### 📧 Login Credentials")
        email = st.text_input("Email Address", placeholder="janatmainswood@gmail.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        # Password strength indicator for new users
        if password and email not in ["janatmainswood@gmail.com"]:
            render_password_strength_indicator(password)
        
        submitted = st.form_submit_button("🔑 Login", use_container_width=True)
        
        if submitted:
            if email and password:
                auth_result = authenticator.authenticate_user(email, password)
                
                if auth_result['success']:
                    if auth_result['requires_2fa']:
                        st.session_state['pending_2fa_email'] = email
                        st.session_state['show_2fa'] = True
                        st.success("✅ Credentials verified! Please complete 2FA verification.")
                        st.rerun()
                    else:
                        # Complete login
                        st.session_state['authenticated_user'] = email
                        st.session_state['user_data'] = auth_result['user']
                        st.success("🎉 Login successful!")
                        st.rerun()
                else:
                    if auth_result.get('locked'):
                        st.error(f"🔒 {auth_result['message']}")
                    else:
                        st.error(f"❌ {auth_result['message']}")
            else:
                st.warning("Please enter both email and password")
    
    # Demo credentials info
    with st.expander("🧪 Demo Credentials", expanded=True):
        st.info("""
        **Test Account:**
        - Email: `janatmainswood@gmail.com`
        - Password: `JanJ3143@?`
        
        **Security Features:**
        - Password strength validation
        - Account lockout after 5 failed attempts
        - 2FA support (Authenticator app & Mobile PIN)
        - Secure bcrypt password hashing
        """)

def render_2fa_verification(authenticator):
    """Render 2FA verification form"""
    st.markdown("### 🔐 Two-Factor Authentication")
    
    email = st.session_state.get('pending_2fa_email')
    
    # Get user's preferred 2FA method
    users = authenticator.load_users()
    preferred_method = users[email].get('preferred_2fa', 'authenticator')
    
    if preferred_method == 'authenticator':
        st.markdown("#### 📱 Enter Authenticator Code")
        st.info("Open your authenticator app and enter the 6-digit code")
        
        code = st.text_input("Authentication Code", max_chars=6, placeholder="123456")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Verify Code", use_container_width=True):
                if code:
                    result = authenticator.verify_2fa_login(email, code, 'authenticator')
                    if result['success']:
                        st.session_state['authenticated_user'] = email
                        st.session_state['user_data'] = users[email]
                        del st.session_state['pending_2fa_email']
                        del st.session_state['show_2fa']
                        st.success("🎉 Authentication successful!")
                        st.rerun()
                    else:
                        st.error(result['message'])
                else:
                    st.warning("Please enter the authentication code")
        
        with col2:
            if st.button("🔙 Back to Login", use_container_width=True):
                del st.session_state['pending_2fa_email']
                del st.session_state['show_2fa']
                st.rerun()
    
    elif preferred_method == 'mobile':
        st.markdown("#### 📱 Mobile PIN Verification")
        
        if st.button("Send PIN"):
            pin = authenticator.two_factor.generate_mobile_pin()
            phone = users[email].get('phone_number', '+1234567890')
            result = authenticator.two_factor.send_mobile_pin(phone, pin)
            
            st.success(f"📱 PIN sent to {phone}")
            st.session_state['mobile_pin'] = pin
        
        pin_code = st.text_input("Enter PIN", max_chars=6, placeholder="123456")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Verify PIN", use_container_width=True):
                if pin_code:
                    result = authenticator.verify_2fa_login(email, pin_code, 'mobile')
                    if result['success']:
                        st.session_state['authenticated_user'] = email
                        st.session_state['user_data'] = users[email]
                        del st.session_state['pending_2fa_email']
                        del st.session_state['show_2fa']
                        st.success("🎉 Authentication successful!")
                        st.rerun()
                    else:
                        st.error(result['message'])
                else:
                    st.warning("Please enter the PIN")
        
        with col2:
            if st.button("🔙 Back to Login", use_container_width=True):
                del st.session_state['pending_2fa_email']
                del st.session_state['show_2fa']
                st.rerun()

def main():
    """Main authentication interface"""
    st.set_page_config(
        page_title="🔐 IntelliCV-AI Authentication",
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize authenticator
    authenticator = EnhancedAuthenticator()
    
    # Check authentication state
    if st.session_state.get('authenticated_user'):
        # User is logged in
        st.success(f"✅ Welcome back, {st.session_state.get('user_data', {}).get('name', 'User')}!")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 Go to Dashboard", use_container_width=True):
                st.switch_page("pages/01_Dashboard.py")
        
        with col2:
            if st.button("⚙️ Account Settings", use_container_width=True):
                st.session_state['show_settings'] = True
                st.rerun()
        
        with col3:
            if st.button("🚪 Logout", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # Account settings
        if st.session_state.get('show_settings'):
            st.divider()
            st.markdown("### ⚙️ Account Settings")
            
            user_data = st.session_state.get('user_data', {})
            
            # 2FA Settings
            if not user_data.get('two_factor_enabled'):
                st.markdown("#### 🔐 Enable Two-Factor Authentication")
                st.warning("2FA is not enabled. Enable it for better security.")
                
                if st.button("🛡️ Setup 2FA"):
                    st.session_state['setup_2fa'] = True
                    st.rerun()
                
                if st.session_state.get('setup_2fa'):
                    render_2fa_setup(authenticator, st.session_state.get('authenticated_user'))
            else:
                st.success("✅ Two-Factor Authentication is enabled")
                if st.button("🔧 Manage 2FA Settings"):
                    st.info("2FA management options would be here in production")
    
    elif st.session_state.get('show_2fa'):
        # Show 2FA verification
        render_2fa_verification(authenticator)
    
    else:
        # Show login form
        render_login_form(authenticator)

if __name__ == "__main__":
    main()