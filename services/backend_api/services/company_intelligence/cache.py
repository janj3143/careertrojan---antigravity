"""
Caching logic for company enrichment (file-based, can be extended to Redis)
"""
import json
from pathlib import Path
from typing import Dict
from .config import COMPANY_DB

def load_company_database() -> Dict:
    if COMPANY_DB.exists():
        with open(COMPANY_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_company_database(db: Dict):
    with open(COMPANY_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
