#!/usr/bin/env python3
"""Merge emails folder into email_extracted folder.

The legacy `emails/` folder contains 197 contacts, 30 of which are NOT
in the master email list. This script:
1. Reads both email sources
2. Identifies valid missing emails (not malformed)
3. Adds them to master_email_list.json
4. Backs up original files
"""
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

MASTER_PATH = Path(r"L:\antigravity_version_ai_data_final\ai_data_final\email_extracted\master_email_list.json")
LEGACY_PATH = Path(r"L:\antigravity_version_ai_data_final\ai_data_final\emails\emails_database.json")

# Simple email regex
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def is_valid_email(email: str) -> bool:
    """Check if email is well-formed (no garbage in local part)."""
    if not EMAIL_RE.match(email):
        return False
    # Reject emails with obvious parsing errors
    if 'Birthdate' in email or 'Summary' in email or 'E-mail' in email:
        return False
    if len(email) > 100:  # Too long
        return False
    if email.count('.') > 5:  # Likely garbage
        return False
    return True

def main():
    # Read both sources
    master = json.load(open(MASTER_PATH))
    legacy = json.load(open(LEGACY_PATH))
    
    master_emails = set(master['emails'])
    legacy_emails = [e['email'] for e in legacy]
    
    print(f"Master emails: {len(master_emails)}")
    print(f"Legacy emails: {len(legacy_emails)}")
    
    # Find valid missing emails
    missing = []
    invalid = []
    for email in legacy_emails:
        if email not in master_emails:
            if is_valid_email(email):
                missing.append(email)
            else:
                invalid.append(email)
    
    print(f"\nValid missing emails: {len(missing)}")
    print(f"Invalid/malformed: {len(invalid)}")
    
    if missing:
        print("\nAdding valid emails:")
        for e in missing:
            print(f"  + {e}")
    
    if invalid:
        print("\nRejected malformed emails:")
        for e in invalid:
            print(f"  X {e}")
    
    if not missing:
        print("\nNo new emails to add.")
        return
    
    # Backup original
    backup_path = MASTER_PATH.with_suffix(f'.backup_{datetime.now():%Y%m%d_%H%M%S}.json')
    shutil.copy(MASTER_PATH, backup_path)
    print(f"\nBackup saved to: {backup_path}")
    
    # Update master
    master['emails'].extend(missing)
    master['emails'] = sorted(set(master['emails']))  # Dedupe and sort
    master['total_unique_emails'] = len(master['emails'])
    master['merge_log'] = master.get('merge_log', [])
    master['merge_log'].append({
        'timestamp': datetime.now().isoformat(),
        'source': str(LEGACY_PATH),
        'added_count': len(missing),
        'added_emails': missing
    })
    
    # Save
    with open(MASTER_PATH, 'w') as f:
        json.dump(master, f, indent=2)
    
    print(f"\nMaster updated: {master['total_unique_emails']} total emails")

if __name__ == "__main__":
    main()
