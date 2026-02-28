#!/usr/bin/env python3
"""
import_all_contacts.py
======================
Full import of all extracted emails into ContactsDB with metadata enrichment.

This script:
1. Loads the master_email_list.json (30k+ emails)
2. Scans parsed JSON files to extract contact metadata (names, companies, phones)
3. Imports all emails into ContactsDB (adds as verified)
4. Runs trust tier classification on all contacts
5. Generates summary statistics

Output:
  - Updates L:\...\contacts_database.json
  - Prints summary with tier distribution

Usage:
    python import_all_contacts.py [--dry-run]
"""

import json
import os
import re
import sys
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ai_engine.contacts_db import ContactsDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
DATA_ROOT = Path(os.getenv("CAREERTROJAN_AI_DATA", os.path.join(os.getenv("CAREERTROJAN_DATA_ROOT", "./data"), "ai_data_final")))

MASTER_EMAIL_LIST = DATA_ROOT / "email_extracted" / "master_email_list.json"

PARSED_DIRS = [
    DATA_ROOT / "parsed_resumes",
    DATA_ROOT / "parsed_from_automated",
    DATA_ROOT / "parsed_cv_files",
]

# Email regex for extraction
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE)

# Name extraction from filename pattern: "(12345) John Smith_..."
FILENAME_NAME_PATTERN = re.compile(r'\(?\d+\)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)')


def extract_name_from_text(text: str) -> tuple[str, str]:
    """Extract first and last name from the beginning of raw text."""
    if not text:
        return "", ""
    
    # First line often contains the name
    lines = text.strip().split('\n')[:5]  # Check first 5 lines
    
    for line in lines:
        line = line.strip()
        # Skip empty or very short lines
        if len(line) < 3 or len(line) > 50:
            continue
        # Skip lines that look like addresses/phone/email
        if any(x in line.lower() for x in ['@', 'tel', 'phone', 'mobile', 'address', 'street', 'avenue', 'road']):
            continue
        # Check if it looks like a name (2-3 capitalized words)
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            # Likely a name
            return words[0], words[-1]
    
    return "", ""


def extract_name_from_filename(filename: str) -> tuple[str, str]:
    """Extract name from filename like '(39129) David Egenes_...'"""
    match = FILENAME_NAME_PATTERN.search(filename)
    if match:
        name_part = match.group(1)
        parts = name_part.split()
        if len(parts) >= 2:
            return parts[0], parts[-1]
    return "", ""


def extract_domain_from_email(email: str) -> str:
    """Extract domain from email address."""
    if '@' in email:
        return email.split('@')[1].lower()
    return ""


def load_master_email_list() -> list[str]:
    """Load the master email list."""
    if not MASTER_EMAIL_LIST.exists():
        logger.error("Master email list not found: %s", MASTER_EMAIL_LIST)
        return []
    
    with open(MASTER_EMAIL_LIST, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('emails', [])


def build_email_metadata_index() -> dict[str, dict[str, Any]]:
    """Scan parsed JSON files and build email -> metadata index."""
    logger.info("Building email metadata index from parsed files...")
    
    email_metadata: dict[str, dict[str, Any]] = {}
    files_scanned = 0
    files_with_contacts = 0
    
    for parsed_dir in PARSED_DIRS:
        if not parsed_dir.exists():
            logger.warning("Directory not found: %s", parsed_dir)
            continue
        
        logger.info("Scanning: %s", parsed_dir)
        
        for filepath in parsed_dir.rglob("*.json"):
            files_scanned += 1
            
            if files_scanned % 5000 == 0:
                logger.info("  ... %d files scanned, %d with contacts", files_scanned, files_with_contacts)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)
                
                if not isinstance(data, dict):
                    continue
                
                # Extract contact info
                contact_info = data.get('contact_info', {})
                emails = contact_info.get('emails', [])
                phones = contact_info.get('phones', [])
                
                if not emails:
                    continue
                
                files_with_contacts += 1
                
                # Extract name
                first_name, last_name = "", ""
                raw_text = data.get('raw_text', '')
                if raw_text:
                    first_name, last_name = extract_name_from_text(raw_text)
                if not first_name:
                    first_name, last_name = extract_name_from_filename(filepath.name)
                
                # Extract companies and job titles
                companies = data.get('companies', [])
                job_titles = data.get('job_titles', [])
                skills = data.get('skills', [])
                
                # Store metadata for each email
                for email in emails:
                    email_lower = email.lower()
                    
                    # Check if we already have better data
                    existing = email_metadata.get(email_lower, {})
                    
                    # Merge/update metadata (prefer richer data)
                    new_data = {
                        'first_name': first_name or existing.get('first_name', ''),
                        'last_name': last_name or existing.get('last_name', ''),
                        'phone': phones[0] if phones else existing.get('phone', ''),
                        'company': companies[0] if companies else existing.get('company', ''),
                        'title': job_titles[0] if job_titles else existing.get('title', ''),
                        'domain': extract_domain_from_email(email_lower),
                        'source_file': str(filepath.name),
                        'skills': skills[:10] if skills else existing.get('skills', []),
                        'has_full_profile': bool(raw_text and len(raw_text) > 500),
                    }
                    
                    email_metadata[email_lower] = new_data
                    
            except (json.JSONDecodeError, OSError, KeyError):
                continue
    
    logger.info("Metadata index complete: %d emails with metadata from %d files", 
                len(email_metadata), files_scanned)
    return email_metadata


def clean_email(email: str) -> str | None:
    """Clean and validate an email address."""
    email = email.lower().strip()
    
    # Skip obviously invalid emails
    if not email or '@' not in email:
        return None
    
    # Skip emails that start with invalid characters
    if email[0] in '.-+%_':
        return None
    
    # Validate domain
    domain = email.split('@')[1] if '@' in email else ''
    if not domain or '.' not in domain:
        return None
    
    # Skip very short local parts
    local = email.split('@')[0]
    if len(local) < 2:
        return None
    
    return email


def import_contacts(dry_run: bool = False) -> dict[str, Any]:
    """Run the full import process."""
    print("=" * 70)
    print("  CareerTrojan Full Contact Import")
    print("=" * 70)
    
    # Load master email list
    print("\n1. Loading master email list...")
    all_emails = load_master_email_list()
    print(f"   Loaded {len(all_emails)} emails")
    
    # Build metadata index
    print("\n2. Building metadata index from parsed files...")
    metadata_index = build_email_metadata_index()
    print(f"   Found metadata for {len(metadata_index)} emails")
    
    # Initialize ContactsDB
    print("\n3. Initializing ContactsDB...")
    db = ContactsDB()
    existing_count = len(db.contacts)
    print(f"   Existing contacts: {existing_count}")
    
    if dry_run:
        print("\n   [DRY RUN] Would import contacts but not saving...")
    
    # Import contacts
    print("\n4. Importing contacts...")
    imported = 0
    updated = 0
    skipped = 0
    invalid = 0
    batch_size = 1000  # Save every N contacts
    
    for i, email in enumerate(all_emails):
        if (i + 1) % 5000 == 0:
            logger.info("  ... processed %d/%d emails", i + 1, len(all_emails))
        
        # Clean email
        clean = clean_email(email)
        if not clean:
            invalid += 1
            continue
        
        # Check if already exists
        existing = db.get_by_email(clean)
        
        # Get metadata
        meta = metadata_index.get(clean, {})
        
        first_name = meta.get('first_name', '')
        last_name = meta.get('last_name', '')
        company = meta.get('company', '')
        domain = meta.get('domain', '') or extract_domain_from_email(clean)
        title = meta.get('title', '')
        phone = meta.get('phone', '')
        
        # Determine source detail
        source = f"import:{meta.get('source_file', 'master_list')}"
        
        # Tags based on data richness
        tags = []
        if meta.get('has_full_profile'):
            tags.append('has_profile')
        if phone:
            tags.append('has_phone')
        if company:
            tags.append('has_company')
        
        if existing:
            # Update existing contact with any new data
            updates = {}
            if first_name and not existing.get('first_name'):
                updates['first_name'] = first_name
            if last_name and not existing.get('last_name'):
                updates['last_name'] = last_name
            if company and not existing.get('company'):
                updates['company'] = company
            if title and not existing.get('title'):
                updates['title'] = title
            if phone and not existing.get('phone'):
                updates['phone'] = phone
            if tags:
                existing_tags = set(existing.get('tags', []))
                existing_tags.update(tags)
                updates['tags'] = list(existing_tags)
            
            if updates and not dry_run:
                # Direct update without saving
                for k, v in updates.items():
                    existing[k] = v
                existing['updated_at'] = db._now()
                updated += 1
            elif updates:
                updated += 1
            else:
                skipped += 1
        else:
            # Add new contact (no auto-save for batch mode)
            if not dry_run:
                db.add_verified(
                    email=clean,
                    first_name=first_name,
                    last_name=last_name,
                    company=company,
                    domain=domain,
                    title=title,
                    source=source,
                    tags=tags,
                    auto_save=False,  # Batch mode - save manually
                )
            imported += 1
        
        # Periodic save every batch_size contacts
        if not dry_run and (imported + updated) > 0 and (imported + updated) % batch_size == 0:
            try:
                db.save()
                logger.info("  ... checkpoint save: %d imported, %d updated", imported, updated)
            except Exception as e:
                logger.warning("  ... checkpoint save failed (will retry): %s", e)
    
    # Final save
    if not dry_run:
        print("\n   Saving database...")
        try:
            db.save()
            print("   Database saved successfully")
        except Exception as e:
            logger.error("   Final save failed: %s", e)
            # Try alternative save
            import shutil
            backup_path = db.db_path.with_suffix('.json.new')
            try:
                import json
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "meta": {"version": 1, "saved_at": db._now(), "total_contacts": len(db.contacts)},
                        "contacts": db.contacts
                    }, f, indent=2, ensure_ascii=False, default=str)
                print(f"   Saved to alternate location: {backup_path}")
            except Exception as e2:
                logger.error("   Alternate save also failed: %s", e2)
    
    print(f"\n   Import complete:")
    print(f"     New:     {imported}")
    print(f"     Updated: {updated}")
    print(f"     Skipped: {skipped}")
    print(f"     Invalid: {invalid}")
    
    # Run tier classification
    print("\n5. Classifying trust tiers...")
    if not dry_run:
        tier_counts = db.reclassify_all_tiers()
        print(f"   Tier A: {tier_counts.get('A', 0)}")
        print(f"   Tier B: {tier_counts.get('B', 0)}")
        print(f"   Tier C: {tier_counts.get('C', 0)}")
    else:
        print("   [DRY RUN] Skipping tier classification")
    
    # Final stats
    print("\n" + "=" * 70)
    print("  IMPORT SUMMARY")
    print("=" * 70)
    final_count = len(db.contacts)
    print(f"  Total contacts before: {existing_count}")
    print(f"  Total contacts after:  {final_count}")
    print(f"  Net new contacts:      {final_count - existing_count}")
    
    if not dry_run:
        # Get tier stats
        tier_stats = db.get_tier_stats()
        print(f"\n  Trust Tier Distribution:")
        for tier, count in tier_stats['tier_counts'].items():
            pct = tier_stats['tier_percentages'].get(tier, 0)
            print(f"    Tier {tier}: {count:,} ({pct}%)")
        
        # Get validation stats
        vstats = db.get_validation_stats()
        print(f"\n  Validation Status:")
        print(f"    Validated:   {vstats['validated']}")
        print(f"    Invalid:     {vstats['invalid']}")
        print(f"    Unvalidated: {vstats['unvalidated']}")
        
        print(f"\n  Database saved to: {db.db_path}")
    
    print("=" * 70)
    
    return {
        'imported': imported,
        'updated': updated,
        'skipped': skipped,
        'invalid': invalid,
        'total_before': existing_count,
        'total_after': len(db.contacts),
        'dry_run': dry_run,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Import all contacts into ContactsDB")
    parser.add_argument('--dry-run', action='store_true', help="Preview without saving")
    args = parser.parse_args()
    
    result = import_contacts(dry_run=args.dry_run)
    
    if not result['dry_run']:
        print("\nImport complete!")


if __name__ == "__main__":
    main()
