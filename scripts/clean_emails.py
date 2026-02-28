#!/usr/bin/env python3
"""Clean up remaining malformed emails."""
import json
from pathlib import Path

path = Path(r'L:\antigravity_version_ai_data_final\ai_data_final\email_extracted\master_email_list.json')
data = json.load(open(path))

# Find and remove malformed emails that slipped through
bad = []
for email in data['emails']:
    # Check for obvious issues
    if any(x in email for x in ['Hobiler', 'CERTIFICATIONS', 'comDo', 'Birthdate', 'Summary']):
        bad.append(email)
    if email.count('@') > 1:
        bad.append(email)

print(f'Found {len(bad)} additional malformed emails:')
for e in bad:
    print(f'  X {e}')

if bad:
    # Remove them
    data['emails'] = [e for e in data['emails'] if e not in bad]
    data['total_unique_emails'] = len(data['emails'])

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Cleaned. New total: {data["total_unique_emails"]}')
else:
    print('No malformed emails found.')
