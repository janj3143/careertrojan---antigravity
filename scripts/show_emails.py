#!/usr/bin/env python3
"""Show full email list from master_email_list.json"""
import json
from collections import Counter
from pathlib import Path

MASTER_PATH = Path(r"L:\antigravity_version_ai_data_final\ai_data_final\email_extracted\master_email_list.json")

def main():
    master = json.load(open(MASTER_PATH))
    
    total = master.get('total_unique_emails', len(master.get('emails', [])))
    emails = master.get('emails', [])
    files_scanned = master.get('total_files_scanned', 0)
    
    print("=" * 70)
    print("MASTER EMAIL LIST")
    print("=" * 70)
    print(f"Total unique emails: {total}")
    print(f"Extracted from {files_scanned} files")
    print()
    
    print("First 50 emails:")
    for i, email in enumerate(emails[:50], 1):
        print(f"  {i:3d}. {email}")
    
    print()
    print("Last 50 emails:")
    for i, email in enumerate(emails[-50:], total - 49):
        print(f"  {i:5d}. {email}")
    
    print()
    print("=" * 70)
    print("DOMAIN DISTRIBUTION (top 30):")
    print("=" * 70)
    
    domains = Counter(e.split('@')[1] if '@' in e else 'invalid' for e in emails)
    for domain, count in domains.most_common(30):
        print(f"  {domain:45s} {count:5d}")
    
    print()
    print("=" * 70)
    print("CORPORATE DOMAINS (non-free email):")
    print("=" * 70)
    
    free_domains = {'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 
                   'live.com', 'aol.com', 'icloud.com', 'msn.com', 'ymail.com',
                   'yahoo.co.uk', 'hotmail.co.uk', 'btinternet.com', 'googlemail.com',
                   'yahoo.fr', 'yahoo.de', 'web.de', 'gmx.com', 'gmx.de', 'mail.com',
                   'fastmail.com', 'protonmail.com', 'zoho.com', 'me.com'}
    
    corporate = {d: c for d, c in domains.items() if d not in free_domains and c >= 2}
    for domain, count in sorted(corporate.items(), key=lambda x: -x[1])[:50]:
        print(f"  {domain:45s} {count:5d}")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
