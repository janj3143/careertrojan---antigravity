"""
User Portal Pages Integration Update Script
===========================================
Updates all user portal pages to use portal_bridge for admin backend integration.
"""

import os
from pathlib import Path

# Pages that need portal_bridge integration
PAGES_TO_UPDATE = {
    '09_Resume_Upload_Analysis.py': {
        'imports': [
            'from shared_backend.services.portal_bridge import portal_bridge'
        ],
        'updates': [
            'Replace local parsing with portal_bridge.resume.parse()',
            'Replace local analysis with portal_bridge.resume.analyze()'
        ]
    },
    '10_UMarketU_Suite.py': {
        'imports': [
            'from shared_backend.services.portal_bridge import portal_bridge'
        ],
        'updates': [
            'Replace local enrichment with portal_bridge.intelligence.enrich()',
            'Replace local market intel with portal_bridge.intelligence.get_market_intelligence()'
        ]
    },
    '11_Coaching_Hub.py': {
        'imports': [
            'from shared_backend.services.portal_bridge import portal_bridge'
        ],
        'updates': [
            'Replace local chat with portal_bridge.chat.ask()',
            'Replace local coaching with portal_bridge.chat.get_coaching_advice()'
        ]
    },
    'career_intelligence_update.py': {
        'imports': [
            'from shared_backend.services.portal_bridge import portal_bridge'
        ],
        'updates': [
            'Use portal_bridge.intelligence.analyze_career() for trajectory analysis'
        ]
    },
    'universal_cloud_maker.py': {
        'imports': [
            'from shared_backend.services.portal_bridge import portal_bridge'
        ],
        'updates': [
            'Use backend cloud maker via portal_bridge'
        ]
    }
}

print("User Portal Pages requiring portal_bridge integration:")
for page, config in PAGES_TO_UPDATE.items():
    print(f"\n{page}:")
    print(f"  Imports needed: {', '.join(config['imports'])}")
    print(f"  Updates:")
    for update in config['updates']:
        print(f"    - {update}")
