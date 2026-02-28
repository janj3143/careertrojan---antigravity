"""
Company Intelligence Auto-Enrichment Service
- Extracts company names from user-uploaded resumes/data
- Runs enrichment for each unique company in the background
- Updates results for dashboard integration
"""
from pathlib import Path
from typing import List, Dict, Optional
import logging

from company_intelligence_parser import get_company_intelligence, db, DB_PATH
from market_intelligence.extract import extract_companies
import threading
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Example: Directory containing user-uploaded resumes (PDF/text)
USER_RESUME_DIR = Path("../user_uploads/resumes/")


def extract_text_from_resume(file_path: Path) -> str:
    """
    Extract text content from resume files (PDF, DOCX, TXT).
    
    Uses pypdf for PDFs, python-docx for DOCX, plain read for TXT.
    Falls back to raw text read on error.
    """
    suffix = file_path.suffix.lower()
    
    try:
        if suffix == '.pdf':
            # Use pypdf for PDF extraction
            try:
                import pypdf
                text_parts = []
                with open(file_path, 'rb') as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        text_parts.append(page.extract_text() or "")
                return "\n".join(text_parts)
            except ImportError:
                logger.warning("pypdf not installed, trying pdfplumber")
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        return "\n".join(page.extract_text() or "" for page in pdf.pages)
                except ImportError:
                    logger.warning("No PDF library available")
                    return ""
                    
        elif suffix in ('.docx', '.doc'):
            # Use python-docx for Word documents
            try:
                import docx
                doc = docx.Document(file_path)
                return "\n".join(para.text for para in doc.paragraphs)
            except ImportError:
                logger.warning("python-docx not installed")
                return ""
            except Exception as e:
                # .doc files need different handling
                logger.warning(f"Could not read {suffix} file: {e}")
                return ""
                
        elif suffix in ('.txt', '.text', '.rtf'):
            # Plain text files
            return file_path.read_text(errors='ignore')
            
        else:
            # Attempt raw text read for unknown formats
            return file_path.read_text(errors='ignore')
            
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        return file_path.read_text(errors='ignore') if file_path.exists() else ""

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
