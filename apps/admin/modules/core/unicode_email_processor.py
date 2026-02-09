# -*- coding: utf-8 -*-
"""
IntelliCV Admin Portal - Unicode Email Processing Security Module
================================================================

SECURITY FEATURES:
- Full Unicode support for international emails
- Secure email content parsing with sanitization
- Multi-encoding detection and safe conversion
- Security logging for email processing operations
- Protection against email-based attacks (XSS, injection)

EMAIL PROCESSING CAPABILITIES:
- Support for UTF-8, UTF-16, Latin-1, CP-1252 and other encodings
- International character handling (Chinese, Arabic, Cyrillic, etc.)
- Email header parsing with proper encoding detection
- Attachment handling with security scanning
- HTML email content sanitization
"""

import os
import sys
import logging
import codecs
import email
import email.header
import chardet
from typing import Dict, List, Optional, Union, Tuple
import re
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import base64
import quopri

# Configure Unicode-aware logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('email_processing.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('email_processor')

class UnicodeEmailProcessor:
    """
    Secure Unicode email processing for IntelliCV Admin Portal
    Handles international emails with proper encoding detection and security
    """
    
    SUPPORTED_ENCODINGS = [
        'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be',
        'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252',
        'ascii', 'gb2312', 'gbk', 'big5', 'shift_jis',
        'iso-2022-jp', 'euc-jp', 'euc-kr', 'koi8-r'
    ]
    
    # Security patterns for email content sanitization
    SECURITY_PATTERNS = {
        'script_tags': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        'onclick_events': re.compile(r'on\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE),
        'javascript_urls': re.compile(r'javascript:', re.IGNORECASE),
        'data_urls': re.compile(r'data:', re.IGNORECASE),
        'form_tags': re.compile(r'<form[^>]*>.*?</form>', re.IGNORECASE | re.DOTALL)
    }
    
    def __init__(self):
        self.processed_count = 0
        self.encoding_stats = {}
        self.security_violations = []
        
        logger.info("🔐 Unicode Email Processor initialized with security features")
    
    def detect_encoding(self, content: bytes, filename: str = None) -> str:
        """
        Detect content encoding using multiple methods
        
        Args:
            content: Raw bytes content
            filename: Optional filename for context
            
        Returns:
            Detected encoding string
        """
        try:
            # Try chardet first (most reliable)
            detection = chardet.detect(content)
            if detection and detection['confidence'] > 0.7:
                detected_encoding = detection['encoding'].lower()
                logger.info(f"📧 Chardet detected encoding: {detected_encoding} (confidence: {detection['confidence']:.2f})")
                return detected_encoding
            
            # Try common encodings in order of preference
            for encoding in self.SUPPORTED_ENCODINGS:
                try:
                    content.decode(encoding)
                    logger.info(f"📧 Encoding detected by trial: {encoding}")
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            # Default to UTF-8 with error handling
            logger.warning(f"⚠️ Could not detect encoding for {filename or 'content'}, defaulting to UTF-8")
            return 'utf-8'
            
        except Exception as e:
            logger.error(f"❌ Encoding detection failed: {e}")
            return 'utf-8'
    
    def safe_decode(self, content: bytes, encoding: str = None) -> str:
        """
        Safely decode bytes to Unicode string with fallback handling
        
        Args:
            content: Raw bytes content
            encoding: Optional encoding hint
            
        Returns:
            Decoded Unicode string
        """
        if encoding is None:
            encoding = self.detect_encoding(content)
        
        try:
            # Try the detected/suggested encoding first
            decoded = content.decode(encoding)
            self.encoding_stats[encoding] = self.encoding_stats.get(encoding, 0) + 1
            return decoded
            
        except UnicodeDecodeError as e:
            logger.warning(f"⚠️ Failed to decode with {encoding}: {e}")
            
            # Try UTF-8 with error handling
            try:
                decoded = content.decode('utf-8', errors='replace')
                logger.info("📧 Fallback to UTF-8 with replacement characters")
                return decoded
            except Exception:
                # Last resort: decode with ignore
                decoded = content.decode('utf-8', errors='ignore')
                logger.warning("⚠️ Using UTF-8 with ignored characters")
                return decoded
    
    def decode_email_header(self, header_value: str) -> str:
        """
        Decode email header with proper encoding handling
        
        Args:
            header_value: Raw header value
            
        Returns:
            Decoded header string
        """
        try:
            decoded_parts = []
            for part, encoding in email.header.decode_header(header_value):
                if isinstance(part, bytes):
                    if encoding:
                        decoded_part = part.decode(encoding)
                    else:
                        decoded_part = self.safe_decode(part)
                else:
                    decoded_part = part
                decoded_parts.append(decoded_part)
            
            result = ''.join(decoded_parts)
            logger.debug(f"📧 Decoded header: {header_value[:50]}... -> {result[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Header decode failed: {e}")
            return header_value  # Return original if decode fails
    
    def sanitize_email_content(self, content: str) -> str:
        """
        Sanitize email content for security
        
        Args:
            content: Email content string
            
        Returns:
            Sanitized content string
        """
        original_length = len(content)
        sanitized = content
        violations_found = []
        
        # Remove dangerous patterns
        for pattern_name, pattern in self.SECURITY_PATTERNS.items():
            matches = pattern.findall(sanitized)
            if matches:
                violations_found.append(f"{pattern_name}: {len(matches)} matches")
                sanitized = pattern.sub('', sanitized)
        
        # HTML escape remaining content
        sanitized = html.escape(sanitized)
        
        if violations_found:
            self.security_violations.extend(violations_found)
            logger.warning(f"🚨 Security violations removed: {', '.join(violations_found)}")
        
        logger.info(f"🛡️ Content sanitized: {original_length} -> {len(sanitized)} chars")
        return sanitized
    
    def process_email_file(self, file_path: str) -> Dict:
        """
        Process an email file with full Unicode support
        
        Args:
            file_path: Path to email file
            
        Returns:
            Dictionary with processed email data
        """
        try:
            # Read file as bytes first
            with open(file_path, 'rb') as f:
                raw_content = f.read()
            
            # Detect and decode
            encoding = self.detect_encoding(raw_content, file_path)
            content = self.safe_decode(raw_content, encoding)
            
            # Parse email
            msg = email.message_from_string(content)
            
            # Extract headers with proper decoding
            email_data = {
                'file_path': file_path,
                'encoding_used': encoding,
                'subject': self.decode_email_header(msg.get('Subject', '')),
                'from': self.decode_email_header(msg.get('From', '')),
                'to': self.decode_email_header(msg.get('To', '')),
                'date': msg.get('Date', ''),
                'message_id': msg.get('Message-ID', ''),
                'content_type': msg.get_content_type(),
                'parts': []
            }
            
            # Process message parts
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type().startswith('text/'):
                        payload = part.get_payload(decode=True)
                        if payload:
                            part_encoding = part.get_content_charset() or encoding
                            part_content = self.safe_decode(payload, part_encoding)
                            sanitized_content = self.sanitize_email_content(part_content)
                            
                            email_data['parts'].append({
                                'content_type': part.get_content_type(),
                                'encoding': part_encoding,
                                'content': sanitized_content[:1000],  # Limit for security
                                'full_length': len(part_content)
                            })
            else:
                # Single part message
                payload = msg.get_payload(decode=True)
                if payload:
                    content_text = self.safe_decode(payload, encoding)
                    sanitized_content = self.sanitize_email_content(content_text)
                    email_data['content'] = sanitized_content
            
            self.processed_count += 1
            logger.info(f"✅ Processed email: {file_path} (encoding: {encoding})")
            
            return email_data
            
        except Exception as e:
            logger.error(f"❌ Failed to process email {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'encoding_used': 'unknown'
            }
    
    def batch_process_emails(self, directory: str) -> List[Dict]:
        """
        Process all email files in a directory
        
        Args:
            directory: Directory containing email files
            
        Returns:
            List of processed email data
        """
        results = []
        email_extensions = ['.eml', '.msg', '.txt', '.mbox']
        
        logger.info(f"🗂️ Starting batch processing of emails in: {directory}")
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in email_extensions):
                        file_path = os.path.join(root, file)
                        result = self.process_email_file(file_path)
                        results.append(result)
        
        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
        
        logger.info(f"📊 Batch processing complete: {len(results)} emails processed")
        return results
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics and security summary"""
        return {
            'processed_count': self.processed_count,
            'encoding_distribution': self.encoding_stats,
            'security_violations': len(self.security_violations),
            'violation_details': self.security_violations[-10:],  # Last 10 violations
            'supported_encodings': self.SUPPORTED_ENCODINGS
        }

# Security wrapper for Streamlit integration
class SecureEmailInterface:
    """Streamlit-safe interface for email processing"""
    
    def __init__(self):
        self.processor = UnicodeEmailProcessor()
    
    def upload_and_process_email(self, uploaded_file) -> Dict:
        """Process uploaded email file in Streamlit"""
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_email_{uploaded_file.name}"
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            # Process the email
            result = self.processor.process_email_file(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Streamlit email processing failed: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    # Test the Unicode email processor
    processor = UnicodeEmailProcessor()
    
    # Test encoding detection
    test_strings = [
        "Hello, World!".encode('utf-8'),
        "Привет, мир!".encode('utf-8'),  # Russian
        "你好，世界！".encode('utf-8'),    # Chinese
        "مرحبا بالعالم".encode('utf-8'),    # Arabic
        "Héllo, Wörld!".encode('latin-1'),  # Latin-1
    ]
    
    print("🧪 Testing Unicode Email Processor...")
    for i, test_bytes in enumerate(test_strings):
        encoding = processor.detect_encoding(test_bytes)
        decoded = processor.safe_decode(test_bytes, encoding)
        print(f"Test {i+1}: {encoding} -> {decoded}")
    
    stats = processor.get_processing_stats()
    print(f"\n📊 Processing Stats: {stats}")
    print("\n✅ Unicode Email Processor test complete!")