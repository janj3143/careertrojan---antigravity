"""
Email Verification Service
Handles email verification tokens, sending verification emails, and managing verification status.
"""

import os
import uuid
import hashlib
import smtplib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import streamlit as st

class EmailVerificationService:
    """
    Manages email verification process for user accounts.
    Handles token generation, email sending, and verification status.
    """
    
    def __init__(self, data_dir: str = "data/verifications"):
        """
        Initialize email verification service.
        
        Args:
            data_dir: Directory to store verification data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.verification_file = self.data_dir / "email_verifications.json"
        self.config = self._load_config()
        
        # Initialize verification storage
        if not self.verification_file.exists():
            self._save_verifications({})
    
    def _load_config(self) -> Dict[str, Any]:
        """Load email configuration from environment or config."""
        return {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'smtp_username': os.getenv('SMTP_USERNAME', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@intellicv.ai'),
            'from_name': os.getenv('FROM_NAME', 'IntelliCV Team'),
            'base_url': os.getenv('BASE_URL', 'http://localhost:8501'),
            'token_expiry_hours': int(os.getenv('VERIFICATION_TOKEN_EXPIRY', 48))
        }
    
    def _load_verifications(self) -> Dict[str, Any]:
        """Load verification data from file."""
        try:
            if self.verification_file.exists():
                with open(self.verification_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading verifications: {str(e)}")
        return {}
    
    def _save_verifications(self, data: Dict[str, Any]) -> None:
        """Save verification data to file."""
        try:
            with open(self.verification_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            st.error(f"Error saving verifications: {str(e)}")
    
    def generate_verification_token(self, user_email: str, user_id: Optional[str] = None) -> str:
        """
        Generate a unique verification token for a user.
        
        Args:
            user_email: User's email address
            user_id: Optional user ID
            
        Returns:
            Verification token (UUID)
        """
        # Generate UUID token
        token = str(uuid.uuid4())
        
        # Calculate expiry time
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=self.config['token_expiry_hours'])
        
        # Store verification data
        verifications = self._load_verifications()
        verifications[token] = {
            'user_email': user_email,
            'user_id': user_id,
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'verified': False,
            'verified_at': None,
            'ip_address': None,
            'user_agent': None
        }
        
        self._save_verifications(verifications)
        
        return token
    
    def verify_token(self, token: str, metadata: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
        """
        Verify an email verification token.
        
        Args:
            token: Verification token to check
            metadata: Optional metadata (IP, user agent, etc.)
            
        Returns:
            Tuple of (success, message)
        """
        verifications = self._load_verifications()
        
        # Check if token exists
        if token not in verifications:
            return False, "Invalid verification token. Please request a new verification email."
        
        verification = verifications[token]
        
        # Check if already verified
        if verification['verified']:
            return True, "Email already verified!"
        
        # Check if expired
        expires_at = datetime.fromisoformat(verification['expires_at'])
        if datetime.now() > expires_at:
            return False, f"Verification token expired. Tokens are valid for {self.config['token_expiry_hours']} hours. Please request a new verification email."
        
        # Mark as verified
        verification['verified'] = True
        verification['verified_at'] = datetime.now().isoformat()
        
        if metadata:
            verification['ip_address'] = metadata.get('ip_address')
            verification['user_agent'] = metadata.get('user_agent')
        
        verifications[token] = verification
        self._save_verifications(verifications)
        
        return True, "Email successfully verified! You can now access all features."
    
    def is_email_verified(self, user_email: str) -> bool:
        """
        Check if an email address has been verified.
        
        Args:
            user_email: Email address to check
            
        Returns:
            True if verified, False otherwise
        """
        verifications = self._load_verifications()
        
        for token, data in verifications.items():
            if data['user_email'] == user_email and data['verified']:
                return True
        
        return False
    
    def get_verification_status(self, user_email: str) -> Dict[str, Any]:
        """
        Get detailed verification status for a user.
        
        Args:
            user_email: Email address
            
        Returns:
            Dictionary with verification details
        """
        verifications = self._load_verifications()
        
        for token, data in verifications.items():
            if data['user_email'] == user_email:
                return {
                    'verified': data['verified'],
                    'created_at': data['created_at'],
                    'expires_at': data['expires_at'],
                    'verified_at': data['verified_at'],
                    'token': token,
                    'is_expired': datetime.now() > datetime.fromisoformat(data['expires_at'])
                }
        
        return {
            'verified': False,
            'created_at': None,
            'expires_at': None,
            'verified_at': None,
            'token': None,
            'is_expired': False
        }
    
    def send_verification_email(self, user_email: str, user_name: Optional[str] = None, 
                               resend: bool = False) -> Tuple[bool, str]:
        """
        Send verification email to user.
        
        Args:
            user_email: User's email address
            user_name: Optional user's name
            resend: Whether this is a resend request
            
        Returns:
            Tuple of (success, message)
        """
        # Check configuration
        if not self.config['smtp_username'] or not self.config['smtp_password']:
            return False, "Email service not configured. Please contact support."
        
        # Generate verification token
        token = self.generate_verification_token(user_email)
        
        # Build verification URL
        verification_url = f"{self.config['base_url']}/?verify_email={token}"
        
        # Create email content
        subject = "Verify Your IntelliCV Account" if not resend else "Resend: Verify Your IntelliCV Account"
        
        html_body = self._create_verification_email_html(
            user_name or user_email,
            verification_url,
            self.config['token_expiry_hours'],
            resend
        )
        
        text_body = self._create_verification_email_text(
            user_name or user_email,
            verification_url,
            self.config['token_expiry_hours'],
            resend
        )
        
        # Send email
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config['from_name']} <{self.config['from_email']}>"
            msg['To'] = user_email
            
            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['smtp_username'], self.config['smtp_password'])
                server.send_message(msg)
            
            action = "resent" if resend else "sent"
            return True, f"Verification email {action} successfully! Please check your inbox (and spam folder)."
            
        except smtplib.SMTPAuthenticationError:
            return False, "Email authentication failed. Please contact support."
        except smtplib.SMTPException as e:
            return False, f"Failed to send email: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _create_verification_email_html(self, user_name: str, verification_url: str, 
                                       expiry_hours: int, resend: bool = False) -> str:
        """Create HTML email body."""
        resend_text = "<p><em>This is a resend of your verification email.</em></p>" if resend else ""
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 0 0 10px 10px;
        }}
        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: bold;
            text-align: center;
        }}
        .footer {{
            text-align: center;
            color: #888;
            font-size: 12px;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .code {{
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Welcome to IntelliCV!</h1>
    </div>
    
    <div class="content">
        <h2>Hello {user_name}! 👋</h2>
        
        {resend_text}
        
        <p>Thank you for creating an account with IntelliCV. To get started and unlock all features, please verify your email address.</p>
        
        <div style="text-align: center;">
            <a href="{verification_url}" class="button">
                ✅ Verify My Email
            </a>
        </div>
        
        <p>Or copy and paste this link into your browser:</p>
        <div class="code">{verification_url}</div>
        
        <div class="warning">
            <strong>⏰ Important:</strong> This verification link expires in <strong>{expiry_hours} hours</strong>.
        </div>
        
        <p><strong>What happens after verification?</strong></p>
        <ul>
            <li>✅ Full access to all IntelliCV features</li>
            <li>✅ Ability to upload and analyze resumes</li>
            <li>✅ AI-powered career intelligence tools</li>
            <li>✅ Premium subscription options</li>
        </ul>
        
        <p>If you didn't create an account with IntelliCV, please ignore this email or contact our support team.</p>
        
        <p>Best regards,<br>
        <strong>The IntelliCV Team</strong></p>
    </div>
    
    <div class="footer">
        <p>© {datetime.now().year} IntelliCV. All rights reserved.</p>
        <p>This is an automated email. Please do not reply to this message.</p>
        <p>Need help? Contact us at support@intellicv.ai</p>
    </div>
</body>
</html>
"""
    
    def _create_verification_email_text(self, user_name: str, verification_url: str, 
                                       expiry_hours: int, resend: bool = False) -> str:
        """Create plain text email body."""
        resend_text = "(This is a resend of your verification email)\n\n" if resend else ""
        
        return f"""
IntelliCV - Email Verification
{'=' * 50}

Hello {user_name}!

{resend_text}Thank you for creating an account with IntelliCV. To get started and unlock all features, please verify your email address.

Verify your email by clicking this link:
{verification_url}

⏰ IMPORTANT: This verification link expires in {expiry_hours} hours.

What happens after verification?
- ✅ Full access to all IntelliCV features
- ✅ Ability to upload and analyze resumes
- ✅ AI-powered career intelligence tools
- ✅ Premium subscription options

If you didn't create an account with IntelliCV, please ignore this email or contact our support team.

Best regards,
The IntelliCV Team

{'=' * 50}
© {datetime.now().year} IntelliCV. All rights reserved.
This is an automated email. Please do not reply to this message.
Need help? Contact us at support@intellicv.ai
"""
    
    def resend_verification_email(self, user_email: str, user_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Resend verification email to user.
        
        Args:
            user_email: User's email address
            user_name: Optional user's name
            
        Returns:
            Tuple of (success, message)
        """
        # Check if already verified
        if self.is_email_verified(user_email):
            return False, "Email is already verified. No need to resend."
        
        # Send verification email with resend flag
        return self.send_verification_email(user_email, user_name, resend=True)
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired verification tokens from storage.
        
        Returns:
            Number of tokens cleaned up
        """
        verifications = self._load_verifications()
        now = datetime.now()
        
        expired_tokens = []
        for token, data in verifications.items():
            expires_at = datetime.fromisoformat(data['expires_at'])
            # Clean up tokens expired more than 7 days ago
            if now > (expires_at + timedelta(days=7)) and not data['verified']:
                expired_tokens.append(token)
        
        # Remove expired tokens
        for token in expired_tokens:
            del verifications[token]
        
        if expired_tokens:
            self._save_verifications(verifications)
        
        return len(expired_tokens)
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """
        Get statistics about email verifications.
        
        Returns:
            Dictionary with verification statistics
        """
        verifications = self._load_verifications()
        now = datetime.now()
        
        total = len(verifications)
        verified = sum(1 for v in verifications.values() if v['verified'])
        pending = total - verified
        expired = sum(
            1 for v in verifications.values() 
            if now > datetime.fromisoformat(v['expires_at']) and not v['verified']
        )
        
        return {
            'total_tokens': total,
            'verified_count': verified,
            'pending_count': pending,
            'expired_count': expired,
            'verification_rate': (verified / total * 100) if total > 0 else 0
        }


# Singleton instance
_email_service = None

def get_email_verification_service() -> EmailVerificationService:
    """
    Get singleton instance of email verification service.
    
    Returns:
        EmailVerificationService instance
    """
    global _email_service
    
    if _email_service is None:
        _email_service = EmailVerificationService()
    
    return _email_service
