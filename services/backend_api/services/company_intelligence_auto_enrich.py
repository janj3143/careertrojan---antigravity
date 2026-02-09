"""
Company Intelligence Auto-Enrichment Service
- Extracts company names from user-uploaded resumes/data
- Runs enrichment for each unique company in the background
- Updates results for dashboard integration
"""
from pathlib import Path
from typing import List, Dict

from company_intelligence_parser import get_company_intelligence, db, DB_PATH
from market_intelligence.extract import extract_companies
import threading
import sqlite3
from datetime import datetime, timedelta

# Example: Directory containing user-uploaded resumes (PDF/text)
USER_RESUME_DIR = Path("../user_uploads/resumes/")

# Placeholder: Function to extract text from resumes (implement as needed)
def extract_text_from_resume(file_path: Path) -> str:
    # TODO: Use PDF/text extraction logic
    return file_path.read_text(errors='ignore')

def auto_enrich_all_companies(resume_dir: Path = USER_RESUME_DIR) -> Dict[str, Dict]:
    enriched_results = {}
    seen_companies = set()
    progress = {"total": 0, "completed": 0, "skipped": 0}
    # Load existing companies from DB
    def get_existing_companies():
        try:
            with db() as con:
                cur = con.execute("SELECT name, last_updated FROM companies")
                return {row[0]: row[1] for row in cur.fetchall()}
        except Exception:
            return {}
    existing_companies = get_existing_companies()
    now = datetime.now()
    for resume_file in resume_dir.glob("*.pdf"):
        text = extract_text_from_resume(resume_file)
        companies = extract_companies(text)
        for company in companies:
            if company not in seen_companies:
                seen_companies.add(company)
                # Check if company is in DB and up-to-date
                last_updated = existing_companies.get(company)
                if last_updated:
                    try:
                        last_dt = datetime.fromisoformat(last_updated)
                        if (now - last_dt).days < 30:
                            progress["skipped"] += 1
                            continue
                    except Exception:
                        pass
                progress["total"] += 1
                # Run enrichment in a background thread
                def enrich_and_store(c):
                    enriched_results[c] = get_market_intelligence(c)
                    progress["completed"] += 1
                threading.Thread(target=enrich_and_store, args=(company,)).start()
    return {"results": enriched_results, "progress": progress}

# For dashboard: Call auto_enrich_all_companies() and display/update results as needed.
