"""
=============================================================================
IntelliCV Email Capture System - Multi-Provider Email Extraction
=============================================================================

Comprehensive email capture system that extracts unique emails from:
- Gmail (using existing app password)
- Yahoo (using existing app password)
- Outlook (new app password to be added)

Features:
- Unique email extraction from all three providers
- CSV export for contact communications
- Integration with emails_database.json
- Filter capabilities for marketing communications
- App offer targeting functionality
"""

import streamlit as st
import imaplib
import email
import ssl
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional
import re
import hashlib
from email.header import decode_header
import logging

# Canonical AI data directory (repo-root ai_data_final)
try:
    from shared.config import AI_DATA_DIR
except Exception:  # pragma: no cover
    AI_DATA_DIR = Path(__file__).resolve().parents[2] / "ai_data_final"

class MultiProviderEmailCapture:
    """Multi-provider email capture system for Gmail, Yahoo, and Outlook"""

    def __init__(self, data_path: str = None):
        """Initialize the email capture system"""
        self.data_path = Path(data_path) if data_path else Path(__file__).parent.parent / "data" / "email_capture"
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Email database integration
        self.emails_db_path = AI_DATA_DIR / "emails" / "emails_database.json"
        self.emails_db_path.parent.mkdir(parents=True, exist_ok=True)

        # CSV export paths
        self.csv_exports_path = self.data_path / "csv_exports"
        self.csv_exports_path.mkdir(exist_ok=True)

        # Provider configurations
        self.provider_configs = {
            'gmail': {
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'use_ssl': True,
                'domains': ['gmail.com', 'googlemail.com']
            },
            'yahoo': {
                'imap_server': 'imap.mail.yahoo.com',
                'imap_port': 993,
                'use_ssl': True,
                'domains': ['yahoo.com', 'yahoo.co.uk', 'yahoo.fr', 'yahoo.ca', 'yahoo.de']
            },
            'outlook': {
                'imap_server': 'outlook.office365.com',
                'imap_port': 993,
                'use_ssl': True,
                'domains': ['outlook.com', 'hotmail.com', 'live.com', 'msn.com']
            }
        }

        # Initialize logging
        self.setup_logging()

        # Load existing emails database
        self.existing_emails = self.load_existing_emails()

    def setup_logging(self):
        """Setup logging for email capture operations"""
        log_path = self.data_path / "logs"
        log_path.mkdir(exist_ok=True)

        logging.basicConfig(
            filename=log_path / f"email_capture_{datetime.now().strftime('%Y%m%d')}.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_existing_emails(self) -> Set[str]:
        """Load existing emails from the database"""
        try:
            if self.emails_db_path.exists():
                with open(self.emails_db_path, 'r', encoding='utf-8') as f:
                    emails_data = json.load(f)
                return {item['email'].lower() for item in emails_data if 'email' in item}
            return set()
        except Exception as e:
            self.logger.error(f"Error loading existing emails: {e}")
            return set()

    def connect_to_email_provider(self, provider: str, email_address: str, app_password: str) -> Optional[imaplib.IMAP4_SSL]:
        """Connect to email provider using app password"""
        try:
            config = self.provider_configs[provider]

            # Create SSL context
            context = ssl.create_default_context()

            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'], ssl_context=context)
            mail.login(email_address, app_password)

            self.logger.info(f"Successfully connected to {provider} for {email_address}")
            return mail

        except Exception as e:
            self.logger.error(f"Failed to connect to {provider}: {e}")
            return None

    def extract_emails_from_message(self, msg) -> Set[str]:
        """Extract email addresses from an email message"""
        emails = set()

        try:
            # Extract from headers
            for header in ['From', 'To', 'Cc', 'Bcc', 'Reply-To']:
                header_value = msg.get(header, '')
                if header_value:
                    # Use regex to find email addresses
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    found_emails = re.findall(email_pattern, header_value)
                    emails.update(email.lower() for email in found_emails)

            # Extract from message body if it's text
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                            found_emails = re.findall(email_pattern, body)
                            emails.update(email.lower() for email in found_emails)
                        except:
                            pass
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    found_emails = re.findall(email_pattern, body)
                    emails.update(email.lower() for email in found_emails)
                except:
                    pass

        except Exception as e:
            self.logger.error(f"Error extracting emails from message: {e}")

        return emails

    def scan_provider_emails(self, provider: str, email_address: str, app_password: str,
                           days_back: int = 365, max_emails: int = 1000) -> Set[str]:
        """Scan emails from a specific provider to extract email addresses"""
        unique_emails = set()

        try:
            # Connect to provider
            mail = self.connect_to_email_provider(provider, email_address, app_password)
            if not mail:
                return unique_emails

            # Select inbox
            mail.select('INBOX')

            # Calculate date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

            # Search for emails
            search_criteria = f'(SINCE {since_date})'
            status, message_ids = mail.search(None, search_criteria)

            if status != 'OK':
                self.logger.error(f"Search failed for {provider}")
                return unique_emails

            message_ids = message_ids[0].split()
            total_messages = len(message_ids)

            # Process emails (limit to max_emails)
            for i, msg_id in enumerate(message_ids[:max_emails]):
                try:
                    # Fetch message
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status == 'OK':
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # Extract emails from this message
                        message_emails = self.extract_emails_from_message(email_message)
                        unique_emails.update(message_emails)

                        # Progress feedback
                        if (i + 1) % 100 == 0:
                            self.logger.info(f"Processed {i + 1}/{min(total_messages, max_emails)} emails from {provider}")

                except Exception as e:
                    self.logger.error(f"Error processing message {msg_id}: {e}")
                    continue

            # Clean up
            mail.close()
            mail.logout()

            self.logger.info(f"Extracted {len(unique_emails)} unique emails from {provider}")

        except Exception as e:
            self.logger.error(f"Error scanning {provider}: {e}")

        return unique_emails

    def validate_email(self, email_addr: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email_addr) is not None

    def get_email_domain_info(self, email_addr: str) -> Dict[str, str]:
        """Get domain information for an email address"""
        domain = email_addr.split('@')[1].lower()

        # Determine provider based on domain
        provider = 'other'
        for prov, config in self.provider_configs.items():
            if domain in config['domains']:
                provider = prov
                break

        return {
            'email': email_addr,
            'domain': domain,
            'provider': provider,
            'first_seen': datetime.now().isoformat()
        }

    def save_emails_to_database(self, new_emails: Set[str]) -> Dict[str, int]:
        """Save new emails to the JSON database"""
        try:
            # Load existing database
            existing_data = []
            if self.emails_db_path.exists():
                with open(self.emails_db_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # Filter out already existing emails
            existing_emails_set = {item['email'].lower() for item in existing_data if 'email' in item}
            truly_new_emails = new_emails - existing_emails_set

            # Add new emails
            for email_addr in truly_new_emails:
                if self.validate_email(email_addr):
                    email_info = self.get_email_domain_info(email_addr)
                    existing_data.append(email_info)

            # Save updated database
            with open(self.emails_db_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved {len(truly_new_emails)} new emails to database")

            return {
                'total_processed': len(new_emails),
                'new_emails': len(truly_new_emails),
                'duplicates_filtered': len(new_emails - truly_new_emails),
                'total_in_database': len(existing_data)
            }

        except Exception as e:
            self.logger.error(f"Error saving emails to database: {e}")
            return {'error': str(e)}

    def export_emails_to_csv(self, provider_filter: Optional[str] = None,
                           domain_filter: Optional[str] = None,
                           include_app_targeting: bool = True) -> str:
        """Export emails to CSV format for contact communications"""
        try:
            # Load current database
            with open(self.emails_db_path, 'r', encoding='utf-8') as f:
                emails_data = json.load(f)

            # Filter data if needed
            filtered_data = emails_data

            if provider_filter:
                filtered_data = [item for item in filtered_data
                               if item.get('provider', '').lower() == provider_filter.lower()]

            if domain_filter:
                filtered_data = [item for item in filtered_data
                               if domain_filter.lower() in item.get('domain', '').lower()]

            # Prepare CSV data with additional marketing fields
            csv_data = []
            for item in filtered_data:
                csv_row = {
                    'email': item.get('email', ''),
                    'domain': item.get('domain', ''),
                    'provider': item.get('provider', ''),
                    'first_seen': item.get('first_seen', ''),
                    'contact_status': 'new',  # For contact communications
                    'marketing_consent': 'unknown',  # For GDPR compliance
                    'app_offer_eligible': 'yes' if include_app_targeting else 'no',
                    'contact_source': 'email_extraction',
                    'last_updated': datetime.now().isoformat()
                }
                csv_data.append(csv_row)

            # Generate CSV filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"email_contacts_{timestamp}.csv"
            if provider_filter:
                csv_filename = f"email_contacts_{provider_filter}_{timestamp}.csv"

            csv_path = self.csv_exports_path / csv_filename

            # Write CSV file
            if csv_data:
                df = pd.DataFrame(csv_data)
                df.to_csv(csv_path, index=False)

                self.logger.info(f"Exported {len(csv_data)} emails to {csv_filename}")
                return str(csv_path)
            else:
                self.logger.warning("No data to export")
                return ""

        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            return ""

    def get_capture_statistics(self) -> Dict[str, any]:
        """Get statistics about captured emails"""
        try:
            with open(self.emails_db_path, 'r', encoding='utf-8') as f:
                emails_data = json.load(f)

            # Calculate statistics by provider
            provider_stats = {}
            domain_stats = {}

            for item in emails_data:
                provider = item.get('provider', 'unknown')
                domain = item.get('domain', 'unknown')

                provider_stats[provider] = provider_stats.get(provider, 0) + 1
                domain_stats[domain] = domain_stats.get(domain, 0) + 1

            # Get top domains
            top_domains = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                'total_emails': len(emails_data),
                'provider_breakdown': provider_stats,
                'top_domains': dict(top_domains),
                'gmail_count': provider_stats.get('gmail', 0),
                'yahoo_count': provider_stats.get('yahoo', 0),
                'outlook_count': provider_stats.get('outlook', 0),
                'other_count': provider_stats.get('other', 0),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}

    def run_multi_provider_capture(self, account_configs: List[Dict[str, str]],
                                 days_back: int = 365, max_emails_per_provider: int = 1000) -> Dict[str, any]:
        """Run email capture across multiple providers"""
        results = {
            'providers_processed': [],
            'total_emails_found': 0,
            'new_emails_added': 0,
            'errors': [],
            'processing_time': None
        }

        start_time = datetime.now()
        all_captured_emails = set()

        try:
            for config in account_configs:
                provider = config['provider']
                email_address = config['email_address']
                app_password = config['app_password']

                st.info(f"🔍 Scanning {provider.title()} account: {email_address}")

                # Capture emails from this provider
                provider_emails = self.scan_provider_emails(
                    provider, email_address, app_password, days_back, max_emails_per_provider
                )

                all_captured_emails.update(provider_emails)

                results['providers_processed'].append({
                    'provider': provider,
                    'email_address': email_address,
                    'emails_found': len(provider_emails),
                    'status': 'success'
                })

                st.success(f"✅ {provider.title()}: Found {len(provider_emails)} unique emails")

            # Save all captured emails to database
            if all_captured_emails:
                save_results = self.save_emails_to_database(all_captured_emails)
                results.update(save_results)

            results['total_emails_found'] = len(all_captured_emails)
            results['processing_time'] = str(datetime.now() - start_time)

            self.logger.info(f"Multi-provider capture completed: {len(all_captured_emails)} emails processed")

        except Exception as e:
            results['errors'].append(str(e))
            self.logger.error(f"Error in multi-provider capture: {e}")

        return results

# Integration function for Contact Communications page
def get_email_capture_manager():
    """Get email capture manager instance for integration"""
    return MultiProviderEmailCapture()

def export_emails_for_contact_communications(provider_filter: str = None) -> str:
    """Export emails in format suitable for contact communications"""
    manager = MultiProviderEmailCapture()
    return manager.export_emails_to_csv(provider_filter=provider_filter, include_app_targeting=True)
