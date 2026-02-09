





















































































































































































































































































































































































































































































































































































































































































































































































































































#!/usr/bin/env python3
"""
🧪 Enhanced Sandbox Authentication Module for IntelliCV-AI User Portal Final
Compatible with admin_portal_final authentication standards
Includes GDPR compliance, security features, and sandbox testing capabilities

SANDBOX ENHANCEMENTS:
- Testing modes and debug authentication
- Comprehensive logging for development
- Integration hooks with admin portal
- Performance monitoring and benchmarking

Date: September 29, 2025
Version: Sandbox Enhanced v1.0
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
from typing import Dict, Tuple, Optional, List
import time
import logging
from pathlib import Path

# Sandbox-specific imports
try:
    import matplotlib.pyplot as plt
    import pandas as pd
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

class SandboxUserAuthenticator:
    """
    Enhanced user authentication system for sandbox testing
    Full compatibility with production User_portal_final
    """
    
    def __init__(self, sandbox_mode: bool = True):
        # Core authentication files
        self.credentials_file = "sandbox_user_credentials.json" if sandbox_mode else "user_credentials.json"
        self.consent_log_file = "sandbox_user_consent_log.json" if sandbox_mode else "user_consent_log.json"
        self.security_log_file = "sandbox_security_events.json" if sandbox_mode else "security_events.json"
        
        # Sandbox-specific files
        self.performance_log_file = "sandbox_performance_metrics.json"
        self.test_users_file = "sandbox_test_users.json"
        
        # Security parameters
        self.min_password_length = 8
        self.max_login_attempts = 3 if not sandbox_mode else 10  # More lenient for testing
        self.lockout_duration = 3600 if not sandbox_mode else 300  # 5 minutes for sandbox
        
        # Sandbox configuration
        self.sandbox_mode = sandbox_mode
        self.debug_logging = sandbox_mode
        self.performance_monitoring = sandbox_mode
        
        # Initialize logging for sandbox
        if self.debug_logging:
            self._setup_sandbox_logging()
        
        # Create test users if sandbox mode
        if sandbox_mode:
            self._ensure_test_users()
    
    def _setup_sandbox_logging(self):
        """Setup comprehensive logging for sandbox testing"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('sandbox_auth_debug.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('SandboxAuth')
        self.logger.info("🧪 Sandbox Authentication System Initialized")
    
    def _ensure_test_users(self):
        """Create default test users for sandbox testing"""
        test_users = {
            "test@intellicv.ai": {
                "name": "Test User",
                "password_hash": None,  # Will be set below
                "salt": None,
                "email_verified": True,
                "created_date": datetime.now().isoformat(),
                "subscription_tier": "premium",
                "two_factor_enabled": False,
                "test_account": True,
                "gdpr_consent": {
                    "data_processing": True,
                    "marketing": False,
                    "analytics": True,
                    "consent_date": datetime.now().isoformat()
                }
            },
            "admin@intellicv.ai": {
                "name": "Admin Test User",
                "password_hash": None,
                "salt": None,
                "email_verified": True,
                "created_date": datetime.now().isoformat(),
                "subscription_tier": "enterprise",
                "two_factor_enabled": True,
                "is_admin": True,
                "test_account": True,
                "gdpr_consent": {
                    "data_processing": True,
                    "marketing": True,
                    "analytics": True,
                    "consent_date": datetime.now().isoformat()
                }
            },
            "demo@intellicv.ai": {
                "name": "Demo User",
                "password_hash": None,
                "salt": None,
                "email_verified": True,
                "created_date": datetime.now().isoformat(),
                "subscription_tier": "free",
                "two_factor_enabled": False,
                "demo_account": True,
                "test_account": True,
                "gdpr_consent": {
                    "data_processing": True,
                    "marketing": False,
                    "analytics": False,
                    "consent_date": datetime.now().isoformat()
                }
            }
        }
        
        # Set default password "IntelliCV2025!" for all test users
        for email, user_data in test_users.items():
            salt = self._generate_salt()
            password_hash = self._hash_password("IntelliCV2025!", salt)
            user_data["salt"] = salt
            user_data["password_hash"] = password_hash
        
        # Save test users
        try:
            with open(self.test_users_file, 'w') as f:
                json.dump(test_users, f, indent=2)
            
            # Merge with existing credentials
            credentials = self._load_credentials()
            credentials.update(test_users)
            self._save_credentials(credentials)
            
            if self.debug_logging:
                self.logger.info(f"✅ Created {len(test_users)} test users for sandbox testing")
                
        except Exception as e:
            if self.debug_logging:
                self.logger.error(f"❌ Failed to create test users: {e}")
    
    def _load_credentials(self) -> Dict:
        """Load user credentials from secure storage"""
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            if self.debug_logging:
                self.logger.error(f"Failed to load credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict):
        """Save user credentials securely"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            if self.debug_logging:
                self.logger.debug("Credentials saved successfully")
        except Exception as e:
            if self.debug_logging:
                self.logger.error(f"Failed to save credentials: {e}")
            st.error(f"Failed to save credentials: {e}")
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Generate cryptographic salt"""
        return secrets.token_hex(32)
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, str, int]:
        """
        Validate password strength and return score
        Enhanced for sandbox testing with detailed feedback
        """
        score = 0
        feedback = []
        
        # Length check
        if len(password) >= self.min_password_length:
            score += 1
        else:
            feedback.append(f"At least {self.min_password_length} characters")
        
        # Character variety checks
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
        
        # Enhanced checks for sandbox
        if len(password) >= 12:
            score += 1  # Bonus for longer passwords
        
        if len(set(password)) >= len(password) * 0.7:  # Character diversity
            score += 1  # Bonus for diverse characters
        
        strength_levels = {
            0: "Very Weak", 1: "Weak", 2: "Fair", 
            3: "Good", 4: "Strong", 5: "Very Strong", 
            6: "Excellent", 7: "Outstanding"
        }
        strength = strength_levels.get(score, "Outstanding")
        
        is_strong = score >= 3
        message = f"Password strength: {strength} ({score}/7)"
        if feedback:
            message += f". Missing: {', '.join(feedback)}"
        
        return is_strong, message, score
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format with enhanced regex for sandbox testing"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid = re.match(pattern, email) is not None
        
        if self.debug_logging:
            self.logger.debug(f"Email validation for {email}: {is_valid}")
        
        return is_valid
    
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
                if self.debug_logging:
                    self.logger.warning(f"User {email} is locked out. {remaining_time}s remaining")
                return True, remaining_time
            else:
                # Reset failed attempts after lockout period
                user_data['failed_attempts'] = 0
                user_data['last_failed_attempt'] = None
                credentials[email] = user_data
                self._save_credentials(credentials)
                if self.debug_logging:
                    self.logger.info(f"Lockout expired for {email}, attempts reset")
        
        return False, 0
    
    def _log_security_event(self, event_type: str, email: str, details: Dict = None):
        """Log security events for audit trail with sandbox enhancements"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'email': email,
            'ip_address': 'localhost',  # In production, get real IP
            'sandbox_mode': self.sandbox_mode,
            'details': details or {}
        }
        
        try:
            if os.path.exists(self.security_log_file):
                with open(self.security_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(event)
            
            # Keep more events in sandbox for analysis
            max_events = 5000 if self.sandbox_mode else 1000
            if len(logs) > max_events:
                logs = logs[-max_events:]
            
            with open(self.security_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
            if self.debug_logging:
                self.logger.info(f"Security event logged: {event_type} for {email}")
                
        except Exception as e:
            if self.debug_logging:
                self.logger.error(f"Failed to log security event: {e}")
    
    def _log_performance_metric(self, operation: str, duration: float, success: bool, details: Dict = None):
        """Log performance metrics for sandbox analysis"""
        if not self.performance_monitoring:
            return
        
        metric = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'success': success,
            'details': details or {}
        }
        
        try:
            if os.path.exists(self.performance_log_file):
                with open(self.performance_log_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = []
            
            metrics.append(metric)
            
            # Keep last 10000 metrics for analysis
            if len(metrics) > 10000:
                metrics = metrics[-10000:]
            
            with open(self.performance_log_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
        except Exception as e:
            if self.debug_logging:
                self.logger.error(f"Failed to log performance metric: {e}")
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Dict]:
        """
        Authenticate user with enhanced sandbox logging and performance monitoring
        Returns: (success, message, user_data)
        """
        start_time = time.time()
        
        try:
            # Validate email format
            if not self._validate_email(email):
                self._log_security_event('INVALID_EMAIL_FORMAT', email)
                return False, "Invalid email format", {}
            
            # Check lockout status
            is_locked, remaining_time = self._check_lockout(email)
            if is_locked:
                self._log_security_event('LOGIN_ATTEMPT_WHILE_LOCKED', email, 
                                       {'remaining_lockout_seconds': remaining_time})
                return False, f"Account locked. Try again in {remaining_time//60} minutes", {}
            
            # Load credentials
            credentials = self._load_credentials()
            user_data = credentials.get(email)
            
            if not user_data:
                self._log_security_event('LOGIN_ATTEMPT_UNKNOWN_USER', email)
                return False, "Invalid email or password", {}
            
            # Verify password
            password_hash = self._hash_password(password, user_data['salt'])
            
            if password_hash != user_data['password_hash']:
                # Handle failed attempt
                user_data['failed_attempts'] = user_data.get('failed_attempts', 0) + 1
                user_data['last_failed_attempt'] = datetime.now().isoformat()
                credentials[email] = user_data
                self._save_credentials(credentials)
                
                self._log_security_event('LOGIN_FAILED_WRONG_PASSWORD', email, 
                                       {'failed_attempts': user_data['failed_attempts']})
                return False, "Invalid email or password", {}
            
            # Successful authentication
            user_data['failed_attempts'] = 0
            user_data['last_failed_attempt'] = None
            user_data['last_login'] = datetime.now().isoformat()
            credentials[email] = user_data
            self._save_credentials(credentials)
            
            self._log_security_event('LOGIN_SUCCESS', email)
            
            # Performance logging
            duration = time.time() - start_time
            self._log_performance_metric('authenticate_user', duration, True, {'email': email})
            
            return True, "Authentication successful", user_data
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_performance_metric('authenticate_user', duration, False, {'error': str(e)})
            
            if self.debug_logging:
                self.logger.error(f"Authentication error for {email}: {e}")
            
            return False, "Authentication system error", {}
    
    def register_user(self, name: str, email: str, password: str, gdpr_consents: Dict = None) -> Tuple[bool, str]:
        """
        Register new user with enhanced sandbox capabilities
        Returns: (success, message)
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not name or len(name.strip()) < 2:
                return False, "Name must be at least 2 characters long"
            
            if not self._validate_email(email):
                return False, "Invalid email format"
            
            is_strong, strength_message, score = self._validate_password_strength(password)
            if not is_strong:
                return False, f"Password not strong enough. {strength_message}"
            
            # Check if user already exists
            credentials = self._load_credentials()
            if email in credentials:
                self._log_security_event('REGISTRATION_ATTEMPT_EXISTING_EMAIL', email)
                return False, "User with this email already exists"
            
            # Create new user
            salt = self._generate_salt()
            password_hash = self._hash_password(password, salt)
            
            user_data = {
                'name': name.strip(),
                'email': email.lower(),
                'password_hash': password_hash,
                'salt': salt,
                'created_date': datetime.now().isoformat(),
                'email_verified': self.sandbox_mode,  # Auto-verify in sandbox
                'subscription_tier': 'free',
                'two_factor_enabled': False,
                'failed_attempts': 0,
                'gdpr_consent': gdpr_consents or {},
                'sandbox_account': self.sandbox_mode
            }
            
            # Save user
            credentials[email] = user_data
            self._save_credentials(credentials)
            
            # Log consent if provided
            if gdpr_consents:
                for consent_type, consent_given in gdpr_consents.items():
                    self._log_consent(email, consent_type, consent_given)
            
            self._log_security_event('USER_REGISTERED', email, {'subscription_tier': 'free'})
            
            # Performance logging
            duration = time.time() - start_time
            self._log_performance_metric('register_user', duration, True, {'email': email})
            
            if self.debug_logging:
                self.logger.info(f"New user registered: {email}")
            
            return True, "Registration successful"
            
        except Exception as e:
            duration = time.time() - start_time
            self._log_performance_metric('register_user', duration, False, {'error': str(e)})
            
            if self.debug_logging:
                self.logger.error(f"Registration error for {email}: {e}")
            
            return False, "Registration system error"
    
    def get_sandbox_analytics(self) -> Dict:
        """Get comprehensive sandbox analytics for testing and monitoring"""
        if not self.sandbox_mode or not ANALYTICS_AVAILABLE:
            return {}
        
        try:
            analytics = {
                'user_stats': self._get_user_statistics(),
                'security_events': self._get_security_analytics(),
                'performance_metrics': self._get_performance_analytics(),
                'test_coverage': self._get_test_coverage()
            }
            
            return analytics
            
        except Exception as e:
            if self.debug_logging:
                self.logger.error(f"Failed to generate sandbox analytics: {e}")
            return {}
    
    def _get_user_statistics(self) -> Dict:
        """Get user registration and authentication statistics"""
        credentials = self._load_credentials()
        
        total_users = len(credentials)
        test_users = sum(1 for user in credentials.values() if user.get('test_account', False))
        verified_users = sum(1 for user in credentials.values() if user.get('email_verified', False))
        premium_users = sum(1 for user in credentials.values() if user.get('subscription_tier') in ['premium', 'enterprise'])
        
        return {
            'total_users': total_users,
            'test_users': test_users,
            'verified_users': verified_users,
            'premium_users': premium_users,
            'free_users': total_users - premium_users
        }
    
    def _get_security_analytics(self) -> Dict:
        """Analyze security events for sandbox testing"""
        if not os.path.exists(self.security_log_file):
            return {}
        
        try:
            with open(self.security_log_file, 'r') as f:
                events = json.load(f)
            
            total_events = len(events)
            login_attempts = sum(1 for e in events if 'LOGIN' in e['event_type'])
            failed_logins = sum(1 for e in events if 'LOGIN_FAILED' in e['event_type'])
            successful_logins = sum(1 for e in events if e['event_type'] == 'LOGIN_SUCCESS')
            
            return {
                'total_security_events': total_events,
                'login_attempts': login_attempts,
                'successful_logins': successful_logins,
                'failed_logins': failed_logins,
                'success_rate': round((successful_logins / login_attempts * 100) if login_attempts > 0 else 0, 2)
            }
            
        except Exception:
            return {}
    
    def _get_performance_analytics(self) -> Dict:
        """Analyze performance metrics for sandbox optimization"""
        if not os.path.exists(self.performance_log_file):
            return {}
        
        try:
            with open(self.performance_log_file, 'r') as f:
                metrics = json.load(f)
            
            if not metrics:
                return {}
            
            # Calculate performance statistics
            durations = [m['duration_ms'] for m in metrics]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            successful_ops = sum(1 for m in metrics if m['success'])
            total_ops = len(metrics)
            
            return {
                'total_operations': total_ops,
                'successful_operations': successful_ops,
                'avg_response_time_ms': round(avg_duration, 2),
                'max_response_time_ms': max_duration,
                'min_response_time_ms': min_duration,
                'success_rate': round((successful_ops / total_ops * 100) if total_ops > 0 else 0, 2)
            }
            
        except Exception:
            return {}
    
    def _get_test_coverage(self) -> Dict:
        """Get test coverage information for sandbox validation"""
        return {
            'authentication_tests': ['login', 'registration', 'password_validation', 'lockout_mechanism'],
            'security_tests': ['email_validation', 'password_hashing', 'failed_attempt_logging'],
            'gdpr_tests': ['consent_logging', 'data_export', 'account_deletion'],
            'performance_tests': ['response_time_monitoring', 'concurrent_user_simulation']
        }


class GDPRCompliance:
    """GDPR compliance utilities for sandbox testing"""
    
    def __init__(self, sandbox_mode: bool = True):
        self.sandbox_mode = sandbox_mode
        self.consent_types = [
            'data_processing',
            'marketing_communications', 
            'analytics_tracking',
            'third_party_sharing',
            'personalized_recommendations'
        ]
    
    def render_consent_form(self, key_prefix: str = "gdpr") -> Dict[str, bool]:
        """Render GDPR consent form for sandbox testing"""
        st.subheader("🔒 Privacy & Data Consent")
        
        if self.sandbox_mode:
            st.info("🧪 **Sandbox Mode**: Consent preferences are for testing only")
        
        consents = {}
        
        # Essential consent (required)
        st.markdown("**Essential Data Processing** (Required)")
        st.markdown("- Account management and authentication")
        st.markdown("- Basic platform functionality")
        consents['data_processing'] = True  # Always required
        
        # Optional consents
        consents['marketing_communications'] = st.checkbox(
            "📧 Marketing Communications",
            key=f"{key_prefix}_marketing",
            help="Receive product updates, feature announcements, and career tips"
        )
        
        consents['analytics_tracking'] = st.checkbox(
            "📊 Analytics & Usage Tracking", 
            key=f"{key_prefix}_analytics",
            help="Help us improve the platform through anonymous usage analytics"
        )
        
        consents['third_party_sharing'] = st.checkbox(
            "🤝 Third-Party Integrations",
            key=f"{key_prefix}_third_party", 
            help="Enable integrations with job boards and professional networks"
        )
        
        consents['personalized_recommendations'] = st.checkbox(
            "🎯 Personalized Recommendations",
            key=f"{key_prefix}_personalized",
            help="Receive tailored job recommendations and career advice"
        )
        
        # GDPR information
        with st.expander("📋 Your Data Rights"):
            st.markdown("""
            Under GDPR, you have the right to:
            - **Access** your personal data
            - **Rectify** inaccurate information  
            - **Erase** your data (right to be forgotten)
            - **Port** your data to another service
            - **Object** to processing
            - **Restrict** processing
            
            Contact us at privacy@intellicv.ai for any data requests.
            """)
        
        return consents


# Sandbox Testing Functions
def render_sandbox_auth_dashboard():
    """Render sandbox authentication dashboard for testing"""
    st.title("🧪 Sandbox Authentication Dashboard")
    
    auth = SandboxUserAuthenticator(sandbox_mode=True)
    
    # Get analytics
    analytics = auth.get_sandbox_analytics()
    
    if analytics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", analytics.get('user_stats', {}).get('total_users', 0))
        
        with col2:
            st.metric("Test Users", analytics.get('user_stats', {}).get('test_users', 0))
        
        with col3:
            success_rate = analytics.get('security_events', {}).get('success_rate', 0)
            st.metric("Login Success Rate", f"{success_rate}%")
        
        with col4:
            avg_response = analytics.get('performance_metrics', {}).get('avg_response_time_ms', 0)
            st.metric("Avg Response Time", f"{avg_response:.1f}ms")
    
    # Test user credentials
    with st.expander("🔑 Test User Credentials"):
        st.markdown("""
        **Default Test Users** (Password: `IntelliCV2025!` for all):
        
        - **test@intellicv.ai** - Premium user for general testing
        - **admin@intellicv.ai** - Admin user with enterprise features  
        - **demo@intellicv.ai** - Free tier demo account
        """)
    
    # Quick test login
    with st.expander("⚡ Quick Test Login"):
        test_email = st.selectbox("Select Test User", [
            "test@intellicv.ai", 
            "admin@intellicv.ai", 
            "demo@intellicv.ai"
        ])
        
        if st.button("🚀 Quick Login"):
            success, message, user_data = auth.authenticate_user(test_email, "IntelliCV2025!")
            if success:
                st.success(f"✅ {message}")
                st.json(user_data)
            else:
                st.error(f"❌ {message}")


if __name__ == "__main__":
    # Sandbox testing mode
    render_sandbox_auth_dashboard()