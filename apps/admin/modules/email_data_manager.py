"""
Enhanced Email Data Manager for IntelliCV Admin Portal
====================================================

This module provides comprehensive email data management:
- Secure credential storage
- Email scanning and attachment extraction
- CV document processing and storage
- Metadata management
- Comprehensive logging

Data Storage Structure:
- data/email_data/attachments/    - Raw email attachments
- data/email_data/extracted_cvs/  - Processed CV documents
- data/email_data/logs/           - Operation logs
- data/email_data/metadata/       - Email and document metadata
"""

import json
import os
import hashlib
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import imaplib
import email
import email.header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailDataManager:
    """Enhanced email data management with proper file storage"""
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Better container-aware path resolution
            try:
                # Try to determine if we're in a container environment
                admin_portal_root = Path(__file__).parent.parent
                
                # Ensure we have an absolute path and it exists
                if not admin_portal_root.is_absolute():
                    admin_portal_root = admin_portal_root.resolve()
                
                # Check if we're in a container (/app working directory)
                if str(admin_portal_root).startswith('/app'):
                    # In container - use /app/data
                    self.base_path = Path("/app/data/email_data")
                else:
                    # On host - use relative path from admin_portal
                    self.base_path = admin_portal_root / "data" / "email_data"
                    
            except Exception as e:
                print(f"Warning: Path resolution error: {e}")
                # Fallback to current working directory
                self.base_path = Path.cwd() / "data" / "email_data"
        else:
            self.base_path = Path(base_path)
        
        # Ensure directory exists with comprehensive error handling and user-writable fallbacks
        try:
            # First check if parent directory is writable
            if not self.base_path.parent.exists():
                # Check if we can create the parent directory
                test_parent = self.base_path.parent
                while test_parent and not test_parent.exists():
                    if os.access(test_parent.parent, os.W_OK) if test_parent.parent.exists() else False:
                        break
                    test_parent = test_parent.parent
                
                if not test_parent or not os.access(test_parent, os.W_OK):
                    raise PermissionError("Cannot write to target directory structure")
            
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions on created directory
            test_file = self.base_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                raise PermissionError("Directory created but not writable")
                
        except PermissionError as e:
            print(f"Permission error with {self.base_path}: {e}")
            # Fallback strategy: try multiple writable locations
            fallback_paths = [
                Path.home() / ".intellicv" / "email_data",  # User home directory
                Path("/tmp") / "intellicv_email_data",      # Temp directory (Linux/Mac)
                Path.cwd() / "email_data_local",            # Current working directory
            ]
            
            import tempfile
            fallback_paths.insert(1, Path(tempfile.gettempdir()) / "intellicv_email_data")  # System temp
            
            for fallback_path in fallback_paths:
                try:
                    fallback_path.mkdir(parents=True, exist_ok=True)
                    # Test write permissions
                    test_file = fallback_path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    self.base_path = fallback_path
                    print(f"Using writable fallback directory: {self.base_path}")
                    break
                except (PermissionError, OSError):
                    continue
            else:
                raise RuntimeError("Unable to find writable directory for email data storage")
                
        except Exception as e:
            print(f"Unexpected error creating directory {self.base_path}: {e}")
            # Emergency fallback - memory-only operation
            import tempfile
            self.base_path = Path(tempfile.gettempdir()) / f"intellicv_emergency_{os.getpid()}"
            try:
                self.base_path.mkdir(parents=True, exist_ok=True)
                print(f"Emergency fallback directory: {self.base_path}")
            except:
                print("WARNING: Operating in memory-only mode - data will not persist")
                self.base_path = None
        
        # Create subdirectories (only if we have a valid base path)
        if self.base_path:
            self.attachments_dir = self.base_path / "attachments"
            self.extracted_cvs_dir = self.base_path / "extracted_cvs" 
            self.logs_dir = self.base_path / "logs"
            self.metadata_dir = self.base_path / "metadata"
            
            try:
                for directory in [self.attachments_dir, self.extracted_cvs_dir, self.logs_dir, self.metadata_dir]:
                    directory.mkdir(parents=True, exist_ok=True)
                    
                # Create provider-specific directories
                for provider in ['gmail', 'outlook', 'yahoo', 'other']:
                    (self.attachments_dir / provider).mkdir(exist_ok=True)
                    
                # Create CV type directories
                for cv_type in ['pdf', 'word', 'text', 'parsed']:
                    (self.extracted_cvs_dir / cv_type).mkdir(exist_ok=True)
                    
                # Create log type directories  
                for log_type in ['connection', 'scanning', 'extraction']:
                    (self.logs_dir / log_type).mkdir(exist_ok=True)
            except PermissionError:
                print("Warning: Could not create all subdirectories due to permissions")
        else:
            # Memory-only mode - create placeholder attributes
            print("Operating in memory-only mode - directories not available")
            self.attachments_dir = None
            self.extracted_cvs_dir = None
            self.logs_dir = None
            self.metadata_dir = None
        
        # Setup logging
        self._setup_logging()
        
        # Initialize metadata files
        self._init_metadata_files()
    
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Main logger
        self.logger = logging.getLogger('EmailDataManager')
        self.logger.setLevel(logging.INFO)
        
        # File handler for general logs
        general_log = self.logs_dir / 'general.log'
        file_handler = logging.FileHandler(general_log)
        file_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(file_handler)
        
        # Connection logger
        self.connection_logger = logging.getLogger('EmailConnection')
        connection_log = self.logs_dir / 'connection' / f'connection_{datetime.now().strftime("%Y%m%d")}.log'
        connection_handler = logging.FileHandler(connection_log)
        connection_handler.setFormatter(logging.Formatter(log_format))
        self.connection_logger.addHandler(connection_handler)
        
        # Scanning logger
        self.scanning_logger = logging.getLogger('EmailScanning')
        scanning_log = self.logs_dir / 'scanning' / f'scanning_{datetime.now().strftime("%Y%m%d")}.log'
        scanning_handler = logging.FileHandler(scanning_log)
        scanning_handler.setFormatter(logging.Formatter(log_format))
        self.scanning_logger.addHandler(scanning_handler)
        
        # Extraction logger
        self.extraction_logger = logging.getLogger('DocumentExtraction')
        extraction_log = self.logs_dir / 'extraction' / f'extraction_{datetime.now().strftime("%Y%m%d")}.log'
        extraction_handler = logging.FileHandler(extraction_log)
        extraction_handler.setFormatter(logging.Formatter(log_format))
        self.extraction_logger.addHandler(extraction_handler)
    
    def _init_metadata_files(self):
        """Initialize metadata JSON files"""
        metadata_files = {
            'accounts.json': {
                'created': datetime.now().isoformat(),
                'accounts': {},
                'total_accounts': 0
            },
            'messages.json': {
                'created': datetime.now().isoformat(), 
                'messages': {},
                'total_messages': 0
            },
            'documents.json': {
                'created': datetime.now().isoformat(),
                'documents': {},
                'total_documents': 0
            }
        }
        
        for filename, default_content in metadata_files.items():
            file_path = self.metadata_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, indent=2, ensure_ascii=False)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        stats = {
            'base_path': str(self.base_path),
            'directories': {},
            'metadata': {},
            'logs': {}
        }
        
        # Directory statistics
        for directory_name in ['attachments', 'extracted_cvs', 'logs', 'metadata']:
            directory = self.base_path / directory_name
            if directory.exists():
                file_count = len(list(directory.rglob('*')))
                total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
                stats['directories'][directory_name] = {
                    'file_count': file_count,
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / (1024*1024), 2)
                }
        
        # Metadata statistics
        try:
            for metadata_file in ['accounts.json', 'messages.json', 'documents.json']:
                file_path = self.metadata_dir / metadata_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        stats['metadata'][metadata_file] = {
                            'total_items': data.get('total_accounts', data.get('total_messages', data.get('total_documents', 0))),
                            'last_updated': data.get('last_updated', 'Never'),
                            'file_size_bytes': file_path.stat().st_size
                        }
        except Exception as e:
            self.logger.error(f"Error reading metadata statistics: {e}")
        
        # Log statistics
        for log_type in ['connection', 'scanning', 'extraction']:
            log_dir = self.logs_dir / log_type
            if log_dir.exists():
                log_files = list(log_dir.glob('*.log'))
                stats['logs'][log_type] = {
                    'log_file_count': len(log_files),
                    'latest_log': max([f.name for f in log_files]) if log_files else 'None'
                }
        
        return stats
    
    def save_email_attachment(self, email_id: str, attachment_data: bytes, 
                            filename: str, provider: str = 'other') -> Dict[str, str]:
        """Save email attachment with metadata"""
        try:
            # Generate secure filename
            file_hash = hashlib.sha256(attachment_data).hexdigest()[:16]
            file_extension = Path(filename).suffix.lower()
            secure_filename = f"{email_id}_{file_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            
            # Save to provider directory
            provider_dir = self.attachments_dir / provider.lower()
            file_path = provider_dir / secure_filename
            
            with open(file_path, 'wb') as f:
                f.write(attachment_data)
            
            # Log the operation
            self.extraction_logger.info(f"Saved attachment: {filename} as {secure_filename} for email {email_id}")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'secure_filename': secure_filename,
                'original_filename': filename,
                'file_size': len(attachment_data),
                'file_hash': file_hash
            }
            
        except Exception as e:
            self.extraction_logger.error(f"Failed to save attachment {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_extracted_cv(self, cv_data: Dict[str, Any], cv_type: str = 'parsed') -> Dict[str, str]:
        """Save extracted CV data"""
        try:
            # Generate CV ID if not present
            if 'cv_id' not in cv_data:
                cv_data['cv_id'] = hashlib.sha256(
                    f"{cv_data.get('email_id', '')}{cv_data.get('filename', '')}{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
            
            # Create filename
            filename = f"cv_{cv_data['cv_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = self.extracted_cvs_dir / cv_type / filename
            
            # Add extraction metadata
            cv_data['extraction_metadata'] = {
                'extracted_at': datetime.now().isoformat(),
                'storage_path': str(file_path),
                'cv_type': cv_type
            }
            
            # Save CV data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cv_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update documents metadata
            self._update_documents_metadata(cv_data)
            
            self.extraction_logger.info(f"Saved extracted CV: {cv_data['cv_id']}")
            
            return {
                'success': True,
                'cv_id': cv_data['cv_id'],
                'file_path': str(file_path),
                'filename': filename
            }
            
        except Exception as e:
            self.extraction_logger.error(f"Failed to save extracted CV: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_documents_metadata(self, cv_data: Dict[str, Any]):
        """Update documents metadata file"""
        try:
            metadata_path = self.metadata_dir / 'documents.json'
            
            # Load existing metadata
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {'documents': {}, 'total_documents': 0}
            
            # Add new document
            metadata['documents'][cv_data['cv_id']] = {
                'filename': cv_data.get('filename', ''),
                'email_id': cv_data.get('email_id', ''),
                'extracted_at': cv_data.get('extraction_metadata', {}).get('extracted_at'),
                'cv_type': cv_data.get('extraction_metadata', {}).get('cv_type'),
                'file_path': cv_data.get('extraction_metadata', {}).get('storage_path')
            }
            
            metadata['total_documents'] = len(metadata['documents'])
            metadata['last_updated'] = datetime.now().isoformat()
            
            # Save updated metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to update documents metadata: {e}")
    
    def get_extracted_cvs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of extracted CVs"""
        try:
            cvs = []
            
            # Read from parsed directory
            parsed_dir = self.extracted_cvs_dir / 'parsed'
            if parsed_dir.exists():
                for cv_file in sorted(parsed_dir.glob('*.json'))[-limit:]:
                    try:
                        with open(cv_file, 'r', encoding='utf-8') as f:
                            cv_data = json.load(f)
                            cvs.append(cv_data)
                    except Exception as e:
                        self.logger.error(f"Failed to read CV file {cv_file}: {e}")
            
            return cvs
            
        except Exception as e:
            self.logger.error(f"Failed to get extracted CVs: {e}")
            return []
    
    def get_log_summary(self, log_type: str = 'general', lines: int = 50) -> List[str]:
        """Get recent log entries"""
        try:
            if log_type == 'general':
                log_file = self.logs_dir / 'general.log'
            else:
                log_dir = self.logs_dir / log_type
                if not log_dir.exists():
                    return []
                
                # Get most recent log file
                log_files = list(log_dir.glob('*.log'))
                if not log_files:
                    return []
                
                log_file = max(log_files, key=lambda x: x.stat().st_mtime)
            
            if not log_file.exists():
                return []
            
            # Read last N lines
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
                
        except Exception as e:
            self.logger.error(f"Failed to read log {log_type}: {e}")
            return []
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up old data files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cleanup_stats = {'files_removed': 0, 'bytes_freed': 0}
            
            # Clean old attachments
            for provider_dir in self.attachments_dir.iterdir():
                if provider_dir.is_dir():
                    for file_path in provider_dir.iterdir():
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time < cutoff_date:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                cleanup_stats['files_removed'] += 1
                                cleanup_stats['bytes_freed'] += file_size
            
            # Clean old logs
            for log_dir in self.logs_dir.iterdir():
                if log_dir.is_dir():
                    for log_file in log_dir.glob('*.log'):
                        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            file_size = log_file.stat().st_size
                            log_file.unlink()
                            cleanup_stats['files_removed'] += 1
                            cleanup_stats['bytes_freed'] += file_size
            
            self.logger.info(f"Cleanup completed: {cleanup_stats['files_removed']} files removed, "
                           f"{cleanup_stats['bytes_freed']} bytes freed")
            
            return cleanup_stats
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return {'files_removed': 0, 'bytes_freed': 0}


class ImprovedEmailConnectionTester:
    """Improved email connection testing with better error handling"""
    
    def __init__(self, data_manager: EmailDataManager):
        self.data_manager = data_manager
        self.logger = data_manager.connection_logger
    
    def test_email_connection(self, email_address: str, password: str, provider: str) -> Dict[str, Any]:
        """Test email connection with comprehensive error handling"""
        
        provider_configs = {
            "gmail": {
                "imap_server": "imap.gmail.com",
                "imap_port": 993,
                "use_ssl": True
            },
            "outlook": {
                "imap_server": "outlook.office365.com", 
                "imap_port": 993,
                "use_ssl": True
            },
            "yahoo": {
                "imap_server": "imap.mail.yahoo.com",
                "imap_port": 993, 
                "use_ssl": True
            }
        }
        
        if provider not in provider_configs:
            return {
                'success': False,
                'error': f'Unsupported email provider: {provider}',
                'error_type': 'UNSUPPORTED_PROVIDER'
            }
        
        config = provider_configs[provider]
        
        try:
            self.logger.info(f"Testing connection to {email_address} ({provider})")
            
            # Create IMAP connection
            if config['use_ssl']:
                mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
            else:
                mail = imaplib.IMAP4(config['imap_server'], config['imap_port'])
            
            # Attempt login
            try:
                mail.login(email_address, password)
                self.logger.info(f"Successfully authenticated {email_address}")
                
                # Get inbox info
                mail.select('INBOX')
                typ, messages = mail.search(None, 'ALL')
                
                if typ == 'OK':
                    message_ids = messages[0].split()
                    total_emails = len(message_ids)
                else:
                    total_emails = 0
                
                mail.logout()
                
                result = {
                    'success': True,
                    'total_emails_in_inbox': total_emails,
                    'server': config['imap_server'],
                    'port': config['imap_port'],
                    'provider': provider,
                    'test_time': datetime.now().isoformat()
                }
                
                self.logger.info(f"Connection test successful: {total_emails} emails found")
                return result
                
            except imaplib.IMAP4.error as auth_error:
                error_msg = str(auth_error).lower()
                self.logger.error(f"Authentication failed for {email_address}: {auth_error}")
                
                if 'authenticationfailed' in error_msg or 'invalid credentials' in error_msg:
                    return {
                        'success': False,
                        'error': f'IMAP error: {auth_error}',
                        'error_type': 'AUTHENTICATION_FAILED',
                        'troubleshooting': {
                            'gmail': [
                                'Enable 2-Factor Authentication on your Google account',
                                'Generate an App Password: Google Account → Security → App passwords',
                                'Use the 16-character App Password (not your regular Gmail password)',
                                'Ensure "Less secure app access" is enabled (if not using App Password)'
                            ],
                            'yahoo': [
                                'Enable 2-Factor Authentication on your Yahoo account',
                                'Generate App Password: Account Security → Generate app password',
                                'Select "Other app" and enter "IMAP" as the name',
                                'Use the generated App Password (not your Yahoo password)'
                            ],
                            'outlook': [
                                'Enable 2-Factor Authentication on your Microsoft account',
                                'Generate App Password: Security → Advanced security options → App passwords',
                                'Create password for "Email" category',
                                'Use the generated App Password (not your Outlook password)'
                            ]
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': f'IMAP error: {auth_error}',
                        'error_type': 'IMAP_ERROR'
                    }
            
        except ConnectionError as conn_error:
            self.logger.error(f"Connection error for {email_address}: {conn_error}")
            return {
                'success': False,
                'error': f'Connection error: {conn_error}',
                'error_type': 'CONNECTION_ERROR',
                'troubleshooting': [
                    'Check your internet connection',
                    'Verify the email server settings',
                    'Check if firewall is blocking the connection',
                    'Try again in a few minutes'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error testing {email_address}: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'UNEXPECTED_ERROR'
            }


# Initialize global email data manager
email_data_manager = EmailDataManager()