"""
Main runner for Company Intelligence Parser (modular, robust, scalable)
"""
import logging
import requests
from pathlib import Path
from .config import PROJECT_ROOT
from .extract import extract_companies
from .enrich import enrich_company
from .cache import load_company_database, save_company_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_file(file_path: Path, db: dict, session: requests.Session):
    logger.info(f"[PROCESS] {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        companies = extract_companies(text)
        for name in companies:
            if name not in db:
                enriched = enrich_company(name, session, db)
                db[name] = enriched
    except Exception as e:
        logger.error(f"[ERROR] {file_path}: {e}")

def run(input_dir=None):
    db = load_company_database()
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    data_dir = Path(input_dir) if input_dir else PROJECT_ROOT / "data"
    for file_path in data_dir.rglob("*.txt"):
        process_file(file_path, db, session)
    save_company_database(db)
    logger.info("[DONE] Company intelligence parsing complete.")

if __name__ == "__main__":
    run()
