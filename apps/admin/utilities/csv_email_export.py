"""
=============================================================================
CSV Email Export Utility for Contact Communications
=============================================================================

Standalone utility to export emails from the emails_database.json to CSV format
for use in contact communications and marketing campaigns.
"""

import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

# Canonical AI data directory (repo-root ai_data_final)
try:
    from shared.config import AI_DATA_DIR
except Exception:  # pragma: no cover
    AI_DATA_DIR = Path(__file__).resolve().parents[2] / "ai_data_final"

def load_emails_database(db_path: Optional[str] = None) -> List[Dict]:
    """Load emails from the JSON database"""
    if db_path is None:
        db_path = str(AI_DATA_DIR / "emails" / "emails_database.json")
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading database: {e}")
        return []

def filter_emails_by_provider(emails: List[Dict], providers: List[str]) -> List[Dict]:
    """Filter emails by provider(s)"""
    if not providers or 'all' in [p.lower() for p in providers]:
        return emails

    return [email for email in emails if email.get('provider', '').lower() in [p.lower() for p in providers]]

def filter_emails_by_domain(emails: List[Dict], domain_pattern: str) -> List[Dict]:
    """Filter emails by domain pattern"""
    if not domain_pattern:
        return emails

    return [email for email in emails if domain_pattern.lower() in email.get('domain', '').lower()]

def add_marketing_fields(emails: List[Dict], app_offer_eligible: bool = True) -> List[Dict]:
    """Add marketing and contact management fields to email records"""
    enhanced_emails = []

    for email in emails:
        enhanced_email = email.copy()
        enhanced_email.update({
            'contact_status': 'new',
            'marketing_consent': 'unknown',
            'app_offer_eligible': 'yes' if app_offer_eligible else 'no',
            'contact_source': 'email_extraction',
            'last_updated': datetime.now().isoformat(),
            'campaign_eligible': 'yes',
            'contact_name': email.get('email', '').split('@')[0],  # Use email prefix as name
            'contact_company': email.get('domain', ''),
            'contact_role': 'Captured Contact',
            'contact_tags': f"email_capture,{email.get('provider', 'unknown')},marketing_eligible"
        })
        enhanced_emails.append(enhanced_email)

    return enhanced_emails

def export_emails_to_csv(emails: List[Dict], output_path: str, filename: Optional[str] = None) -> str:
    """Export emails to CSV format"""
    if not emails:
        raise ValueError("No emails to export")

    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"email_contacts_{timestamp}.csv"

    # Ensure output directory exists
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full path to CSV file
    csv_path = output_dir / filename

    # Convert to DataFrame and export
    df = pd.DataFrame(emails)
    df.to_csv(csv_path, index=False)

    return str(csv_path)

def export_app_offer_targets(providers: List[str] = ['gmail', 'yahoo', 'outlook'],
                           output_path: Optional[str] = None) -> str:
    """Export emails specifically for app offer campaigns"""

    if not output_path:
        output_path = str(Path(__file__).parent.parent / "data" / "csv_exports")

    # Load emails
    emails = load_emails_database()

    # Filter by providers
    filtered_emails = filter_emails_by_provider(emails, providers)

    # Add app offer specific fields
    app_offer_emails = []
    for email in filtered_emails:
        app_email = email.copy()
        app_email.update({
            'campaign_type': 'app_download_promotion',
            'offer_type': 'free_download',
            'app_offer_eligible': 'yes',
            'priority': 'high' if email.get('provider') in ['gmail', 'yahoo', 'outlook'] else 'medium',
            'target_segment': f"{email.get('provider', 'unknown')}_users",
            'marketing_consent': 'pending',
            'contact_source': 'email_extraction_app_targeting'
        })
        app_offer_emails.append(app_email)

    # Export to CSV
    filename = f"app_offer_targets_{datetime.now().strftime('%Y%m%d')}.csv"
    csv_path = export_emails_to_csv(app_offer_emails, output_path, filename)

    return csv_path

def export_provider_specific_csvs(output_path: Optional[str] = None) -> Dict[str, str]:
    """Export separate CSV files for each provider"""

    if not output_path:
        output_path = str(Path(__file__).parent.parent / "data" / "csv_exports")

    # Load emails
    emails = load_emails_database()

    # Group by provider
    providers = {}
    for email in emails:
        provider = email.get('provider', 'unknown')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(email)

    # Export each provider
    exported_files = {}
    for provider, provider_emails in providers.items():
        if provider != 'unknown' and provider_emails:
            # Add marketing fields
            enhanced_emails = add_marketing_fields(provider_emails, app_offer_eligible=True)

            # Export
            filename = f"{provider}_contacts_{datetime.now().strftime('%Y%m%d')}.csv"
            csv_path = export_emails_to_csv(enhanced_emails, output_path, filename)
            exported_files[provider] = csv_path

    return exported_files

def get_email_statistics() -> Dict[str, Any]:
    """Get statistics about the email database"""
    emails = load_emails_database()

    if not emails:
        return {'error': 'No emails found'}

    # Calculate statistics
    provider_counts = {}
    domain_counts = {}

    for email in emails:
        provider = email.get('provider', 'unknown')
        domain = email.get('domain', 'unknown')

        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # Top domains
    top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'total_emails': len(emails),
        'provider_breakdown': provider_counts,
        'top_domains': dict(top_domains),
        'gmail_count': provider_counts.get('gmail', 0),
        'yahoo_count': provider_counts.get('yahoo', 0),
        'outlook_count': provider_counts.get('outlook', 0),
        'other_count': provider_counts.get('other', 0),
        'last_updated': datetime.now().isoformat()
    }

# Command line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export emails from database to CSV")
    parser.add_argument("--provider", nargs='+', default=['all'],
                       help="Provider(s) to export: gmail, yahoo, outlook, or all")
    parser.add_argument("--output", default="./csv_exports",
                       help="Output directory for CSV files")
    parser.add_argument("--app-offers", action="store_true",
                       help="Export for app offer campaigns")
    parser.add_argument("--separate", action="store_true",
                       help="Export separate files for each provider")
    parser.add_argument("--stats", action="store_true",
                       help="Show database statistics only")

    args = parser.parse_args()

    if args.stats:
        stats = get_email_statistics()
        print("\n📊 Email Database Statistics:")
        print(f"Total emails: {stats.get('total_emails', 0):,}")
        print(f"Gmail: {stats.get('gmail_count', 0):,}")
        print(f"Yahoo: {stats.get('yahoo_count', 0):,}")
        print(f"Outlook: {stats.get('outlook_count', 0):,}")
        print(f"Other: {stats.get('other_count', 0):,}")

    elif args.app_offers:
        csv_path = export_app_offer_targets(args.provider, args.output)
        print(f"✅ App offer targets exported to: {csv_path}")

    elif args.separate:
        exported_files = export_provider_specific_csvs(args.output)
        print(f"✅ Provider-specific CSVs exported:")
        for provider, path in exported_files.items():
            print(f"  {provider}: {path}")

    else:
        # Standard export
        emails = load_emails_database()
        filtered_emails = filter_emails_by_provider(emails, args.provider)
        enhanced_emails = add_marketing_fields(filtered_emails, app_offer_eligible=True)

        csv_path = export_emails_to_csv(enhanced_emails, args.output)
        print(f"✅ Emails exported to: {csv_path}")
        print(f"📊 Exported {len(enhanced_emails)} emails")
