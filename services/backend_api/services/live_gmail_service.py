"""
Live Gmail Service for IntelliCV Admin Portal
===========================================

Real-time Gmail integration service that provides live data instead of mock data.
This service connects to the actual Gmail account and extracts CV documents.

Author: IntelliCV AI System
Date: October 11, 2025
"""

import os
import json
import imaplib
import email
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveGmailService:
    """Live Gmail service for real-time email extraction"""
    
    def __init__(self):
        """Initialize the live Gmail service"""
        self.sandbox_root = Path(__file__).parent.parent.parent
        self.email_config_path = self.sandbox_root / "IntelliCV-data" / "email_integration" / "email_accounts.json"
        self.email_extracted_path = self.sandbox_root / "IntelliCV-data" / "email_extracted"
        
        # Ensure directories exist
        self.email_extracted_path.mkdir(parents=True, exist_ok=True)
        
        # Load email account configuration
        self.gmail_account = self._load_gmail_config()
        
        # CV-related keywords
        self.cv_keywords = [
            'cv', 'resume', 'curriculum vitae', 
            'application', 'job application',
            'candidate', 'applicant', 'curriculum'
        ]
        
        # Supported file extensions
        self.supported_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf']
        
        self.stats = {
            'emails_processed': 0,
            'attachments_found': 0,
            'cvs_extracted': 0,
            'errors': 0,
            'last_scan': None
        }
    
    def _load_gmail_config(self) -> Optional[Dict]:
        """Load Gmail configuration from email_accounts.json"""
        try:
            if not self.email_config_path.exists():
                logger.error(f"Email config not found: {self.email_config_path}")
                return None
            
            with open(self.email_config_path, 'r') as f:
                accounts = json.load(f)
            
            # Find Gmail account
            for account_id, account_data in accounts.items():
                if account_data.get('provider') == 'gmail':
                    logger.info(f"Found Gmail account: {account_data.get('email_address')}")
                    return account_data
            
            logger.error("No Gmail account found in configuration")
            return None
            
        except Exception as e:
            logger.error(f"Error loading Gmail config: {e}")
            return None
    
    def test_gmail_connection(self) -> Tuple[bool, str]:
        """Test Gmail connection"""
        if not self.gmail_account:
            return False, "Gmail account not configured"
        
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.gmail_account['email_address'], self.gmail_account['password'].strip())
            mail.select('INBOX')
            mail.logout()
            
            return True, f"✅ Connected to {self.gmail_account['email_address']}"
            
        except Exception as e:
            return False, f"❌ Connection failed: {str(e)}"
    
    def get_real_email_stats(self) -> Dict:
        """Get real statistics from Gmail and extracted files"""
        stats = {
            'gmail_connection': False,
            'total_emails': 0,
            'cv_emails': 0,
            'extracted_files': 0,
            'recent_extractions': 0,
            'account_email': 'Not configured',
            'last_extraction': 'Never',
            'error_message': None
        }
        
        # Check Gmail connection
        connection_ok, connection_msg = self.test_gmail_connection()
        stats['gmail_connection'] = connection_ok
        stats['connection_message'] = connection_msg
        
        if self.gmail_account:
            stats['account_email'] = self.gmail_account['email_address']
        
        # Count extracted files
        if self.email_extracted_path.exists():
            extracted_files = list(self.email_extracted_path.glob("email_*.pdf")) + \
                            list(self.email_extracted_path.glob("email_*.doc*"))
            
            stats['extracted_files'] = len(extracted_files)
            
            # Find recent extractions (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_files = [f for f in extracted_files 
                          if datetime.fromtimestamp(f.stat().st_ctime) > week_ago]
            stats['recent_extractions'] = len(recent_files)
            
            # Find last extraction date
            if extracted_files:
                latest_file = max(extracted_files, key=lambda f: f.stat().st_ctime)
                stats['last_extraction'] = datetime.fromtimestamp(latest_file.stat().st_ctime).strftime("%Y-%m-%d %H:%M")
        
        # If connected, get email stats
        if connection_ok and self.gmail_account:
            try:
                email_stats = self._get_gmail_email_stats()
                stats.update(email_stats)
            except Exception as e:
                stats['error_message'] = f"Error getting email stats: {e}"
        
        return stats
    
    def _get_gmail_email_stats(self) -> Dict:
        """Get email statistics from Gmail"""
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.gmail_account['email_address'], self.gmail_account['password'].strip())
            mail.select('INBOX')
            
            # Get total emails in last 30 days
            since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
            status, messages = mail.search(None, f'(SINCE {since_date})')
            
            total_recent = len(messages[0].split()) if status == 'OK' and messages[0] else 0
            
            # Search for CV-related emails
            cv_search_terms = []
            for keyword in self.cv_keywords[:3]:  # Limit search terms
                cv_search_terms.append(f'(SUBJECT "{keyword}")')
                cv_search_terms.append(f'(BODY "{keyword}")')
            
            search_query = f'(SINCE {since_date}) ({" OR ".join(cv_search_terms)})'
            status, cv_messages = mail.search(None, search_query)
            
            cv_emails = len(cv_messages[0].split()) if status == 'OK' and cv_messages[0] else 0
            
            mail.logout()
            
            return {
                'total_emails': total_recent,
                'cv_emails': cv_emails
            }
            
        except Exception as e:
            logger.error(f"Error getting Gmail stats: {e}")
            return {
                'total_emails': 0,
                'cv_emails': 0
            }
    
    def extract_new_cvs(self, days_back: int = 7) -> Dict:
        """Extract new CVs from Gmail"""
        if not self.gmail_account:
            return {'success': False, 'message': 'Gmail account not configured'}
        
        try:
            connection_ok, connection_msg = self.test_gmail_connection()
            if not connection_ok:
                return {'success': False, 'message': connection_msg}
            
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.gmail_account['email_address'], self.gmail_account['password'].strip())
            mail.select('INBOX')
            
            # Search for recent CV emails
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Build search query
            cv_search_terms = []
            for keyword in self.cv_keywords:
                cv_search_terms.append(f'(SUBJECT "{keyword}")')
                cv_search_terms.append(f'(BODY "{keyword}")')
            
            search_query = f'(SINCE {since_date}) ({" OR ".join(cv_search_terms[:6])})'  # Limit terms
            logger.info(f"Searching Gmail with: {search_query}")
            
            status, messages = mail.search(None, search_query)
            
            if status != 'OK' or not messages[0]:
                mail.logout()
                return {'success': True, 'message': 'No new CV emails found', 'extracted': 0}
            
            email_ids = messages[0].split()
            logger.info(f"Found {len(email_ids)} potential CV emails")
            
            extracted_count = 0
            
            # Process each email
            for i, email_id in enumerate(email_ids[:10]):  # Limit to 10 emails per extraction
                try:
                    new_cvs = self._extract_attachments_from_email(mail, email_id)
                    extracted_count += len(new_cvs)
                    
                    if i % 3 == 0:  # Update progress every 3 emails
                        logger.info(f"Processed {i+1}/{len(email_ids[:10])} emails")
                
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue
            
            mail.logout()
            
            self.stats['last_scan'] = datetime.now().isoformat()
            
            return {
                'success': True, 
                'message': f'Successfully extracted {extracted_count} new CVs',
                'extracted': extracted_count,
                'emails_scanned': len(email_ids[:10])
            }
            
        except Exception as e:
            logger.error(f"Error during CV extraction: {e}")
            return {'success': False, 'message': f'Extraction failed: {str(e)}'}
    
    def _extract_attachments_from_email(self, mail, email_id) -> List[str]:
        """Extract attachments from a specific email"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            if status != 'OK':
                return []
            
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Get email metadata
            subject = email_message.get('Subject', 'No Subject')
            sender = email_message.get('From', 'Unknown')
            date = email_message.get('Date', 'Unknown')
            
            extracted_files = []
            
            # Process multipart emails
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        
                        if filename and self._is_cv_file(filename):
                            # Extract attachment data
                            attachment_data = part.get_payload(decode=True)
                            
                            if attachment_data:
                                saved_file = self._save_attachment(
                                    filename, attachment_data, subject, sender, date
                                )
                                if saved_file:
                                    extracted_files.append(saved_file)
                                    logger.info(f"📎 Extracted: {filename}")
            
            return extracted_files
            
        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")
            return []
    
    def _is_cv_file(self, filename: str) -> bool:
        """Check if filename suggests it's a CV/Resume"""
        if not filename:
            return False
        
        filename_lower = filename.lower()
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_extensions:
            return False
        
        # Check for CV-related keywords in filename
        for keyword in self.cv_keywords:
            if keyword in filename_lower:
                return True
        
        # Additional checks for common CV filename patterns
        cv_patterns = ['resume', 'cv_', '_cv', 'curriculum']
        for pattern in cv_patterns:
            if pattern in filename_lower:
                return True
        
        return False
    
    def _save_attachment(self, filename: str, data: bytes, subject: str, sender: str, date: str) -> Optional[str]:
        """Save attachment to email_extracted directory"""
        try:
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Clean filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
            
            # Create unique filename
            file_ext = Path(filename).suffix
            account_id = self.gmail_account['account_id'] if self.gmail_account else 'unknown'
            new_filename = f"email_{account_id}_{timestamp}_{safe_filename}"
            
            file_path = self.email_extracted_path / new_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(data)
            
            # Save metadata
            metadata = {
                'original_filename': filename,
                'extracted_from_email': True,
                'account_id': account_id,
                'extraction_date': datetime.now().isoformat(),
                'file_path': str(file_path),
                'file_size': len(data),
                'email_subject': subject,
                'email_sender': sender,
                'email_date': date,
                'content_type': self._get_content_type(filename)
            }
            
            metadata_path = file_path.with_suffix(file_path.suffix + '.metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"💾 Saved: {new_filename} ({len(data)} bytes)")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving attachment: {e}")
            return None
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on file extension"""
        ext = Path(filename).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def get_recent_extractions(self, limit: int = 10) -> List[Dict]:
        """Get list of recent email extractions"""
        try:
            if not self.email_extracted_path.exists():
                return []
            
            # Get all email extraction files
            email_files = list(self.email_extracted_path.glob("email_*.pdf")) + \
                         list(self.email_extracted_path.glob("email_*.doc*"))
            
            # Sort by creation time (newest first)
            email_files.sort(key=lambda f: f.stat().st_ctime, reverse=True)
            
            recent_files = []
            for file_path in email_files[:limit]:
                # Try to load metadata
                metadata_path = file_path.with_suffix(file_path.suffix + '.metadata.json')
                
                file_info = {
                    'filename': file_path.name,
                    'size': file_path.stat().st_size,
                    'created': datetime.fromtimestamp(file_path.stat().st_ctime).strftime("%Y-%m-%d %H:%M"),
                    'original_filename': file_path.name,
                    'email_subject': 'Unknown',
                    'email_sender': 'Unknown'
                }
                
                # Load metadata if available
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        file_info.update({
                            'original_filename': metadata.get('original_filename', file_path.name),
                            'email_subject': metadata.get('email_subject', 'Unknown'),
                            'email_sender': metadata.get('email_sender', 'Unknown')
                        })
                    except Exception:
                        pass  # Use default values
                
                recent_files.append(file_info)
            
            return recent_files
            
        except Exception as e:
            logger.error(f"Error getting recent extractions: {e}")
            return []

# Singleton instance
_gmail_service = None

def get_gmail_service() -> LiveGmailService:
    """Get singleton Gmail service instance"""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = LiveGmailService()
    return _gmail_service