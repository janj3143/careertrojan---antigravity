"""
Authentication module for IntelliCV Admin Portal
"""

from .secure_authenticator import (
    SecureAuthenticator,
    SessionManager,
    render_secure_login_interface,
    render_password_change_interface,
    UserCredentials
)

__all__ = [
    'SecureAuthenticator',
    'SessionManager', 
    'render_secure_login_interface',
    'render_password_change_interface',
    'UserCredentials'
]