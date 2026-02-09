"""
Configuration for Company Intelligence Parser
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_DATA_DIR = Path(os.getenv('AI_DATA_DIR', PROJECT_ROOT / 'ai_data'))
COMPANY_DB = AI_DATA_DIR / 'companies' / 'company_intelligence_database.json'
LOGOS_DIR = AI_DATA_DIR / 'companies' / 'logos'
LOGS_DIR = AI_DATA_DIR / 'companies' / 'logs'

# Regex patterns for company extraction (can be extended)
COMPANY_PATTERNS = [
    r'\\b[A-Z][A-Za-z0-9&.,\\- ]+(Ltd|Limited|Inc|Corporation|Corp|Company|Co|LLC|LLP|PLC|GmbH|AG|SA|Pvt)\\b',
    r'\\b[A-Z][A-Za-z0-9&.,\\- ]+(Group|Holdings|International|Global|Solutions|Services|Systems|Technologies|Tech)\\b',
    r'\\b[A-Z][A-Za-z0-9&.,\\- ]+(Consulting|Consultancy|Partners|Associates|Enterprises|Industries)\\b'
]
