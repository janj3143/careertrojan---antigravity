"""
🔐 IntelliCV-AI Enhanced Authentication System
===========================================
Comprehensive authentication with password strength, 2FA, and security features
Includes dummy user credentials for testing and development
"""

import streamlit as st
import hashlib
import secrets
import pyotp
import qrcode
import io
import base64
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import time

class PasswordStrengthValidator:
    """Password strength validation with real-time feedback"""
    
    @staticmethod
    def check_password_strength(password):
        """Check password strength and return score with feedback"""
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password must be at least 8 characters long")
        
        if len(password) >= 12:
            score += 1
        
        # Character variety checks
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Add lowercase letters")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Add uppercase letters")
        
        if re.search(r'[0-9]', password):
            score += 1
        else:
            feedback.append("Add numbers")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Add special characters (!@#$%^&*)")
        
        # Complexity patterns
        if re.search(r'.{12,}', password):
            score += 1
        
        # Determine strength level
        if score <= 2:
            strength = "Very Weak"
            color = "#ff4444"
        elif score <= 3:
            strength = "Weak"
            color = "#ff8800"
        elif score <= 4:
            strength = "Fair"
            color = "#ffaa00"
        elif score <= 5:
            strength = "Good"
            color = "#88cc00"
        else:
            strength = "Strong"
            color = "#00cc44"
        
        return {
            'score': score,
            'max_score': 7,
            'strength': strength,
            'color': color,
            'feedback': feedback,
            'percentage': min(100, (score / 7) * 100)
        }

class TwoFactorAuth:
    """Two-Factor Authentication manager"""
    
    @staticmethod
    def generate_secret_key():
        """Generate a new secret key for 2FA"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email, secret_key, issuer_name="IntelliCV-AI"):
        """Generate QR code for authenticator app setup"""
        totp_uri = pyotp.totp.TOTP(secret_key).provisioning_uri(
            name=user_email,
            issuer_name=issuer_name
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        # Create image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        return img_base64, totp_uri
    
    @staticmethod
    def verify_token(secret_key, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret_key)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes():
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(8):
            code = '-'.join([secrets.token_hex(2).upper() for _ in range(2)])
            codes.append(code)
        return codes

class EnhancedAuthenticator:
    """Enhanced authentication system with all security features"""
    
    def __init__(self):
        self.users_file = Path("sandbox_user_credentials.json")
        self.session_timeout = 30  # minutes
        self.max_login_attempts = 5
        self.lockout_duration = 15  # minutes
        
        # Initialize default users
        self.init_default_users()
    
    def init_default_users(self):
        """Initialize with default test users"""
        default_users = {
            "janatmainswood@gmail.com": {
                "password_hash": self.hash_password("JanJ3143@?"),
                "full_name": "Jane Atmainswood",
                "user_id": "user_001",
                "created_date": datetime.now().isoformat(),
                "is_admin": True,
                "subscription_tier": "Enterprise",
                "tokens_remaining": 1000,
                "2fa_enabled": False,
                "2fa_secret": None,
                "backup_codes": [],
                "login_attempts": 0,
                "locked_until": None,
                "last_login": None,
                "session_token": None,
                "session_expires": None
            }
        }
        
        # Load existing users or create new file
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                existing_users = json.load(f)
            
            # Add default user if not exists
            for email, user_data in default_users.items():
                if email not in existing_users:
                    existing_users[email] = user_data
            
            self.users = existing_users
        else:
            self.users = default_users
        
        self.save_users()
    
    def save_users(self):
        """Save user data to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2, default=str)
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password, stored_hash):
        """Verify password against stored hash"""
        try:
            salt, hash_hex = stored_hash.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash.hex() == hash_hex
        except:
            return False
    
    def generate_session_token(self):
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def is_account_locked(self, email):
        """Check if account is currently locked"""
        if email not in self.users:
            return False
        
        user = self.users[email]
        if user.get('locked_until'):
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                return True
            else:
                # Unlock account
                user['locked_until'] = None
                user['login_attempts'] = 0
                self.save_users()
        
        return False
    
    def record_login_attempt(self, email, success):
        """Record login attempt and handle lockouts"""
        if email not in self.users:
            return
        
        user = self.users[email]
        
        if success:
            user['login_attempts'] = 0
            user['locked_until'] = None
            user['last_login'] = datetime.now().isoformat()
        else:
            user['login_attempts'] = user.get('login_attempts', 0) + 1
            
            if user['login_attempts'] >= self.max_login_attempts:
                user['locked_until'] = (datetime.now() + timedelta(minutes=self.lockout_duration)).isoformat()
        
        self.save_users()
    
    def authenticate_user(self, email, password, totp_token=None):
        """Authenticate user with optional 2FA"""
        # Check if account exists
        if email not in self.users:
            return {"success": False, "message": "Invalid email or password"}
        
        user = self.users[email]
        
        # Check if account is locked
        if self.is_account_locked(email):
            remaining_time = datetime.fromisoformat(user['locked_until']) - datetime.now()
            minutes = int(remaining_time.total_seconds() / 60)
            return {"success": False, "message": f"Account locked. Try again in {minutes} minutes."}
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            self.record_login_attempt(email, False)
            attempts_left = self.max_login_attempts - user.get('login_attempts', 0)
            return {"success": False, "message": f"Invalid email or password. {attempts_left} attempts remaining."}
        
        # Check 2FA if enabled
        if user.get('2fa_enabled', False):
            if not totp_token:
                return {"success": False, "message": "2FA token required", "requires_2fa": True}
            
            # Verify TOTP token or backup code
            totp_valid = TwoFactorAuth.verify_token(user['2fa_secret'], totp_token)
            backup_valid = totp_token in user.get('backup_codes', [])
            
            if not (totp_valid or backup_valid):
                self.record_login_attempt(email, False)
                return {"success": False, "message": "Invalid 2FA token"}
            
            # Remove used backup code
            if backup_valid:
                user['backup_codes'].remove(totp_token)
                self.save_users()
        
        # Successful login
        session_token = self.generate_session_token()
        session_expires = (datetime.now() + timedelta(minutes=self.session_timeout)).isoformat()
        
        user['session_token'] = session_token
        user['session_expires'] = session_expires
        
        self.record_login_attempt(email, True)
        
        return {
            "success": True,
            "message": "Login successful",
            "user_data": {
                "email": email,
                "full_name": user['full_name'],
                "user_id": user['user_id'],
                "subscription_tier": user['subscription_tier'],
                "tokens_remaining": user['tokens_remaining'],
                "is_admin": user.get('is_admin', False),
                "session_token": session_token
            }
        }
    
    def setup_2fa(self, email):
        """Setup 2FA for user"""
        if email not in self.users:
            return {"success": False, "message": "User not found"}
        
        user = self.users[email]
        
        if user.get('2fa_enabled', False):
            return {"success": False, "message": "2FA already enabled"}
        
        # Generate secret and backup codes
        secret_key = TwoFactorAuth.generate_secret_key()
        backup_codes = TwoFactorAuth.generate_backup_codes()
        
        # Generate QR code
        qr_code_base64, totp_uri = TwoFactorAuth.generate_qr_code(email, secret_key)
        
        # Store temporarily (will be confirmed after verification)
        user['2fa_secret_temp'] = secret_key
        user['backup_codes_temp'] = backup_codes
        
        self.save_users()
        
        return {
            "success": True,
            "secret_key": secret_key,
            "qr_code": qr_code_base64,
            "backup_codes": backup_codes,
            "manual_entry_key": secret_key
        }
    
    def confirm_2fa_setup(self, email, token):
        """Confirm 2FA setup with verification token"""
        if email not in self.users:
            return {"success": False, "message": "User not found"}
        
        user = self.users[email]
        temp_secret = user.get('2fa_secret_temp')
        
        if not temp_secret:
            return {"success": False, "message": "No 2FA setup in progress"}
        
        # Verify token
        if TwoFactorAuth.verify_token(temp_secret, token):
            # Confirm 2FA setup
            user['2fa_enabled'] = True
            user['2fa_secret'] = temp_secret
            user['backup_codes'] = user.get('backup_codes_temp', [])
            
            # Clean up temporary data
            del user['2fa_secret_temp']
            if 'backup_codes_temp' in user:
                del user['backup_codes_temp']
            
            self.save_users()
            return {"success": True, "message": "2FA enabled successfully"}
        else:
            return {"success": False, "message": "Invalid token"}
    
    def disable_2fa(self, email, password):
        """Disable 2FA for user"""
        if email not in self.users:
            return {"success": False, "message": "User not found"}
        
        user = self.users[email]
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return {"success": False, "message": "Invalid password"}
        
        # Disable 2FA
        user['2fa_enabled'] = False
        user['2fa_secret'] = None
        user['backup_codes'] = []
        
        self.save_users()
        return {"success": True, "message": "2FA disabled successfully"}
    
    def is_session_valid(self, email, session_token):
        """Check if session is valid"""
        if email not in self.users:
            return False
        
        user = self.users[email]
        
        if user.get('session_token') != session_token:
            return False
        
        if user.get('session_expires'):
            expires = datetime.fromisoformat(user['session_expires'])
            if datetime.now() > expires:
                return False
        
        return True
    
    def logout_user(self, email):
        """Logout user and invalidate session"""
        if email in self.users:
            user = self.users[email]
            user['session_token'] = None
            user['session_expires'] = None
            self.save_users()

# UI Components for Authentication
def render_password_strength_indicator(password):
    """Render real-time password strength indicator"""
    if not password:
        return
    
    strength_data = PasswordStrengthValidator.check_password_strength(password)
    
    # Progress bar
    st.markdown(f"""
    <div style='margin: 10px 0;'>
        <div style='background: #f0f0f0; border-radius: 10px; height: 8px; overflow: hidden;'>
            <div style='background: {strength_data["color"]}; height: 100%; width: {strength_data["percentage"]}%; transition: all 0.3s ease;'></div>
        </div>
        <div style='display: flex; justify-content: space-between; margin-top: 5px;'>
            <span style='color: {strength_data["color"]}; font-weight: bold;'>{strength_data["strength"]}</span>
            <span style='color: #666; font-size: 0.9em;'>{strength_data["score"]}/{strength_data["max_score"]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Feedback
    if strength_data['feedback']:
        st.caption("💡 Improve your password:")
        for tip in strength_data['feedback']:
            st.caption(f"   • {tip}")

def render_2fa_setup_modal(authenticator, email):
    """Render 2FA setup modal"""
    st.markdown("### 🔐 Enable Two-Factor Authentication")
    st.info("Two-factor authentication adds an extra layer of security to your account.")
    
    if st.button("🚀 Start 2FA Setup"):
        setup_result = authenticator.setup_2fa(email)
        
        if setup_result["success"]:
            st.success("2FA setup initiated! Follow the steps below:")
            
            # Method selection
            st.markdown("#### Choose your preferred method:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📱 Authenticator App (Recommended)**")
                st.markdown("1. Download an authenticator app (Google Authenticator, Authy, etc.)")
                st.markdown("2. Scan the QR code below:")
                
                # Display QR code
                qr_html = f'<img src="data:image/png;base64,{setup_result["qr_code"]}" style="border: 1px solid #ddd; border-radius: 8px;">'
                st.markdown(qr_html, unsafe_allow_html=True)
                
                st.markdown("3. Enter the 6-digit code from your app:")
            
            with col2:
                st.markdown("**🔑 Manual Entry**")
                st.markdown("If you can't scan the QR code, manually enter this key:")
                st.code(setup_result["manual_entry_key"])
                
                st.markdown("**🔒 Backup Codes**")
                st.warning("Save these backup codes in a secure location:")
                for i, code in enumerate(setup_result["backup_codes"], 1):
                    st.code(f"{i}. {code}")
            
            # Verification
            verification_token = st.text_input(
                "Enter 6-digit verification code:",
                max_chars=6,
                placeholder="123456",
                help="Enter the code from your authenticator app"
            )
            
            if st.button("✅ Verify and Enable 2FA"):
                if verification_token:
                    confirm_result = authenticator.confirm_2fa_setup(email, verification_token)
                    
                    if confirm_result["success"]:
                        st.success("🎉 2FA enabled successfully!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(confirm_result["message"])
                else:
                    st.error("Please enter the verification code")
        else:
            st.error(setup_result["message"])

def render_login_form(authenticator):
    """Render enhanced login form with all features"""
    st.markdown("""
    <div style='text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0; font-size: 3em;'>🔐 IntelliCV-AI Login</h1>
        <p style='color: white; margin: 10px 0 0 0; font-size: 1.2em;'>Secure Authentication Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 📧 Sign In to Your Account")
            
            email = st.text_input(
                "Email Address",
                placeholder="janatmainswood@gmail.com",
                value="janatmainswood@gmail.com"  # Pre-filled for testing
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                value="JanJ3143@?"  # Pre-filled for testing
            )
            
            # Real-time password strength (only show when typing)
            if password and email != "janatmainswood@gmail.com":  # Don't show for demo user
                render_password_strength_indicator(password)
            
            # 2FA token input (conditional)
            totp_token = None
            if email in authenticator.users and authenticator.users[email].get('2fa_enabled', False):
                totp_token = st.text_input(
                    "🔐 Two-Factor Authentication Code",
                    max_chars=6,
                    placeholder="Enter 6-digit code",
                    help="Enter the code from your authenticator app or use a backup code"
                )
            
            # Remember me option
            remember_me = st.checkbox("🔒 Keep me signed in", help="Stay logged in for 30 days")
            
            # Login button
            login_submitted = st.form_submit_button("🚀 Sign In", use_container_width=True)
    
    # Process login
    if login_submitted:
        if not email or not password:
            st.error("Please enter both email and password")
            return None
        
        # Show loading
        with st.spinner("🔐 Authenticating..."):
            time.sleep(1)  # Simulate authentication delay
            result = authenticator.authenticate_user(email, password, totp_token)
        
        if result["success"]:
            # Store session data
            for key, value in result["user_data"].items():
                st.session_state[f"authenticated_{key}"] = value
            
            st.session_state.authenticated_user = True
            st.session_state.remember_me = remember_me
            
            st.success(f"🎉 Welcome back, {result['user_data']['full_name']}!")
            st.balloons()
            
            # Show user info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Subscription", result['user_data']['subscription_tier'])
            with col2:
                st.metric("Tokens", result['user_data']['tokens_remaining'])
            with col3:
                if result['user_data']['is_admin']:
                    st.metric("Role", "Admin 👑")
                else:
                    st.metric("Role", "User")
            
            time.sleep(2)
            st.rerun()
        
        elif result.get("requires_2fa"):
            st.warning("🔐 Two-factor authentication required. Please enter your 6-digit code.")
        
        else:
            st.error(result["message"])
    
    # Additional options
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📱 Setup 2FA", help="Enable two-factor authentication"):
            if email and email in authenticator.users:
                st.session_state.show_2fa_setup = True
            else:
                st.error("Please enter a valid email address first")
    
    with col2:
        if st.button("❓ Forgot Password", help="Reset your password"):
            st.info("Password reset functionality would be implemented here")
    
    # Show 2FA setup if requested
    if st.session_state.get('show_2fa_setup') and email:
        render_2fa_setup_modal(authenticator, email)
    
    return None

# Initialize the authenticator
@st.cache_resource
def get_authenticator():
    """Get cached authenticator instance"""
    return EnhancedAuthenticator()

# Main authentication check function
def check_authentication():
    """Check if user is authenticated"""
    if st.session_state.get('authenticated_user'):
        return True
    return False

def render_user_menu():
    """Render authenticated user menu"""
    if not check_authentication():
        return
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 👋 Hello, {st.session_state.get('authenticated_full_name', 'User')}!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("👤 Profile"):
                st.switch_page("pages/08_Profile_Complete.py")
        
        with col2:
            if st.button("🚪 Logout"):
                # Clear session
                for key in list(st.session_state.keys()):
                    if key.startswith('authenticated_'):
                        del st.session_state[key]
                st.session_state.authenticated_user = False
                st.rerun()

if __name__ == "__main__":
    st.set_page_config(
        page_title="🔐 IntelliCV-AI Login",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize authenticator
    authenticator = get_authenticator()
    
    # Show login or user menu
    if not check_authentication():
        render_login_form(authenticator)
    else:
        st.success("✅ You are already logged in!")
        render_user_menu()
        
        if st.button("🏠 Go to Dashboard"):
            st.switch_page("pages/01_Dashboard.py")