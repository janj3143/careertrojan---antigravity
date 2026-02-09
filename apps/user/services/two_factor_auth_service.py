"""
Two-Factor Authentication (2FA) Service
Handles TOTP-based 2FA, QR code generation, recovery codes, and verification.
"""

import os
import json
import pyotp
import qrcode
import secrets
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from io import BytesIO
import base64
import streamlit as st

class TwoFactorAuthService:
    """
    Manages Two-Factor Authentication using TOTP (Time-based One-Time Password).
    Compatible with Google Authenticator, Microsoft Authenticator, Authy, etc.
    """
    
    def __init__(self, data_dir: str = "data/2fa"):
        """
        Initialize 2FA service.
        
        Args:
            data_dir: Directory to store 2FA data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_file = self.data_dir / "2fa_secrets.json"
        self.recovery_codes_file = self.data_dir / "recovery_codes.json"
        
        # Initialize storage
        if not self.secrets_file.exists():
            self._save_secrets({})
        if not self.recovery_codes_file.exists():
            self._save_recovery_codes({})
        
        # Configuration
        self.app_name = os.getenv('APP_NAME', 'IntelliCV')
        self.issuer_name = os.getenv('ISSUER_NAME', 'IntelliCV.ai')
        self.recovery_codes_count = 10
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load 2FA secrets from file."""
        try:
            with open(self.secrets_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading 2FA secrets: {str(e)}")
            return {}
    
    def _save_secrets(self, data: Dict[str, Any]) -> None:
        """Save 2FA secrets to file."""
        try:
            with open(self.secrets_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            st.error(f"Error saving 2FA secrets: {str(e)}")
    
    def _load_recovery_codes(self) -> Dict[str, Any]:
        """Load recovery codes from file."""
        try:
            with open(self.recovery_codes_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading recovery codes: {str(e)}")
            return {}
    
    def _save_recovery_codes(self, data: Dict[str, Any]) -> None:
        """Save recovery codes to file."""
        try:
            with open(self.recovery_codes_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            st.error(f"Error saving recovery codes: {str(e)}")
    
    def _hash_code(self, code: str) -> str:
        """Hash a code for secure storage."""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def generate_secret(self, user_email: str) -> str:
        """
        Generate a new TOTP secret for a user.
        
        Args:
            user_email: User's email address
            
        Returns:
            Base32 encoded secret
        """
        # Generate random secret
        secret = pyotp.random_base32()
        
        # Store secret
        secrets = self._load_secrets()
        secrets[user_email] = {
            'secret': secret,
            'enabled': False,
            'enabled_at': None,
            'created_at': datetime.now().isoformat(),
            'backup_phone': None,
            'verified': False
        }
        self._save_secrets(secrets)
        
        return secret
    
    def get_totp_uri(self, user_email: str, secret: Optional[str] = None) -> str:
        """
        Generate TOTP provisioning URI for QR code.
        
        Args:
            user_email: User's email address
            secret: Optional secret (will load from storage if not provided)
            
        Returns:
            TOTP provisioning URI
        """
        if not secret:
            secrets = self._load_secrets()
            if user_email not in secrets:
                secret = self.generate_secret(user_email)
            else:
                secret = secrets[user_email]['secret']
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Generate provisioning URI
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        return uri
    
    def generate_qr_code(self, user_email: str) -> str:
        """
        Generate QR code for TOTP setup.
        
        Args:
            user_email: User's email address
            
        Returns:
            Base64 encoded QR code image
        """
        # Get TOTP URI
        uri = self.get_totp_uri(user_email)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        
        return img_base64
    
    def generate_recovery_codes(self, user_email: str) -> List[str]:
        """
        Generate recovery codes for account access.
        
        Args:
            user_email: User's email address
            
        Returns:
            List of recovery codes
        """
        # Generate random recovery codes
        codes = []
        for _ in range(self.recovery_codes_count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        # Store hashed codes
        recovery_data = self._load_recovery_codes()
        recovery_data[user_email] = {
            'codes': [self._hash_code(code) for code in codes],
            'used_codes': [],
            'generated_at': datetime.now().isoformat()
        }
        self._save_recovery_codes(recovery_data)
        
        return codes
    
    def verify_totp_code(self, user_email: str, code: str) -> Tuple[bool, str]:
        """
        Verify a TOTP code.
        
        Args:
            user_email: User's email address
            code: 6-digit TOTP code
            
        Returns:
            Tuple of (success, message)
        """
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return False, "2FA is not set up for this account."
        
        secret = secrets[user_email]['secret']
        
        # Create TOTP object
        totp = pyotp.TOTP(secret)
        
        # Verify code (allows 30 second window before/after)
        is_valid = totp.verify(code, valid_window=1)
        
        if is_valid:
            return True, "Code verified successfully!"
        else:
            return False, "Invalid or expired code. Please try again."
    
    def verify_recovery_code(self, user_email: str, code: str) -> Tuple[bool, str]:
        """
        Verify a recovery code.
        
        Args:
            user_email: User's email address
            code: Recovery code
            
        Returns:
            Tuple of (success, message)
        """
        recovery_data = self._load_recovery_codes()
        
        if user_email not in recovery_data:
            return False, "No recovery codes found for this account."
        
        user_recovery = recovery_data[user_email]
        code_hash = self._hash_code(code)
        
        # Check if code exists and hasn't been used
        if code_hash in user_recovery['codes']:
            if code_hash not in user_recovery['used_codes']:
                # Mark code as used
                user_recovery['used_codes'].append(code_hash)
                user_recovery['used_at'] = datetime.now().isoformat()
                recovery_data[user_email] = user_recovery
                self._save_recovery_codes(recovery_data)
                
                remaining = len(user_recovery['codes']) - len(user_recovery['used_codes'])
                return True, f"Recovery code accepted! {remaining} codes remaining."
            else:
                return False, "This recovery code has already been used."
        else:
            return False, "Invalid recovery code."
    
    def enable_2fa(self, user_email: str, verification_code: str) -> Tuple[bool, str]:
        """
        Enable 2FA for a user after verifying setup.
        
        Args:
            user_email: User's email address
            verification_code: TOTP code to verify setup
            
        Returns:
            Tuple of (success, message)
        """
        # First verify the code works
        success, message = self.verify_totp_code(user_email, verification_code)
        
        if not success:
            return False, f"Cannot enable 2FA: {message}"
        
        # Enable 2FA
        secrets = self._load_secrets()
        if user_email in secrets:
            secrets[user_email]['enabled'] = True
            secrets[user_email]['verified'] = True
            secrets[user_email]['enabled_at'] = datetime.now().isoformat()
            self._save_secrets(secrets)
            
            return True, "🎉 2FA successfully enabled! Your account is now more secure."
        else:
            return False, "2FA setup not found. Please scan the QR code first."
    
    def disable_2fa(self, user_email: str, verification_code: str, password: Optional[str] = None) -> Tuple[bool, str]:
        """
        Disable 2FA for a user.
        
        Args:
            user_email: User's email address
            verification_code: TOTP code or recovery code
            password: Optional password verification
            
        Returns:
            Tuple of (success, message)
        """
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return False, "2FA is not enabled for this account."
        
        # Verify code (TOTP or recovery)
        totp_success, _ = self.verify_totp_code(user_email, verification_code)
        recovery_success, _ = self.verify_recovery_code(user_email, verification_code)
        
        if not (totp_success or recovery_success):
            return False, "Invalid verification code. Cannot disable 2FA."
        
        # Disable 2FA
        secrets[user_email]['enabled'] = False
        secrets[user_email]['disabled_at'] = datetime.now().isoformat()
        self._save_secrets(secrets)
        
        return True, "2FA has been disabled for your account."
    
    def is_2fa_enabled(self, user_email: str) -> bool:
        """
        Check if 2FA is enabled for a user.
        
        Args:
            user_email: User's email address
            
        Returns:
            True if 2FA is enabled
        """
        secrets = self._load_secrets()
        
        if user_email in secrets:
            return secrets[user_email].get('enabled', False)
        
        return False
    
    def get_2fa_status(self, user_email: str) -> Dict[str, Any]:
        """
        Get detailed 2FA status for a user.
        
        Args:
            user_email: User's email address
            
        Returns:
            Dictionary with 2FA status
        """
        secrets = self._load_secrets()
        recovery_data = self._load_recovery_codes()
        
        if user_email not in secrets:
            return {
                'enabled': False,
                'setup': False,
                'verified': False,
                'created_at': None,
                'enabled_at': None,
                'recovery_codes_generated': False,
                'recovery_codes_remaining': 0
            }
        
        user_secret = secrets[user_email]
        
        recovery_codes_remaining = 0
        if user_email in recovery_data:
            total_codes = len(recovery_data[user_email]['codes'])
            used_codes = len(recovery_data[user_email].get('used_codes', []))
            recovery_codes_remaining = total_codes - used_codes
        
        return {
            'enabled': user_secret.get('enabled', False),
            'setup': True,
            'verified': user_secret.get('verified', False),
            'created_at': user_secret.get('created_at'),
            'enabled_at': user_secret.get('enabled_at'),
            'backup_phone': user_secret.get('backup_phone'),
            'recovery_codes_generated': user_email in recovery_data,
            'recovery_codes_remaining': recovery_codes_remaining
        }
    
    def get_current_totp_code(self, user_email: str) -> Optional[str]:
        """
        Get current TOTP code (for testing/demo purposes only).
        
        Args:
            user_email: User's email address
            
        Returns:
            Current 6-digit TOTP code or None
        """
        secrets = self._load_secrets()
        
        if user_email not in secrets:
            return None
        
        secret = secrets[user_email]['secret']
        totp = pyotp.TOTP(secret)
        
        return totp.now()
    
    def get_2fa_stats(self) -> Dict[str, Any]:
        """
        Get statistics about 2FA usage.
        
        Returns:
            Dictionary with 2FA statistics
        """
        secrets = self._load_secrets()
        recovery_data = self._load_recovery_codes()
        
        total_users = len(secrets)
        enabled_count = sum(1 for s in secrets.values() if s.get('enabled', False))
        verified_count = sum(1 for s in secrets.values() if s.get('verified', False))
        
        total_recovery_codes = sum(len(r['codes']) for r in recovery_data.values())
        used_recovery_codes = sum(len(r.get('used_codes', [])) for r in recovery_data.values())
        
        return {
            'total_users_with_2fa': total_users,
            'enabled_count': enabled_count,
            'verified_count': verified_count,
            'setup_but_not_enabled': total_users - enabled_count,
            'total_recovery_codes': total_recovery_codes,
            'used_recovery_codes': used_recovery_codes,
            'remaining_recovery_codes': total_recovery_codes - used_recovery_codes,
            'adoption_rate': (enabled_count / total_users * 100) if total_users > 0 else 0
        }


# Singleton instance
_2fa_service = None

def get_2fa_service() -> TwoFactorAuthService:
    """
    Get singleton instance of 2FA service.
    
    Returns:
        TwoFactorAuthService instance
    """
    global _2fa_service
    
    if _2fa_service is None:
        _2fa_service = TwoFactorAuthService()
    
    return _2fa_service
