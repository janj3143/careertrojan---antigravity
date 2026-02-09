Company Parser Module
"""
from pathlib import Path

def extract_company_info(file_path: Path) -> dict:
    # No fabricated outputs permitted.
    return {
        "filename": file_path.name,
        "company": None,
        "fields": {},
        "error": "Company extraction not integrated",
    }

def parse_all_companies(resume_dir: Path) -> list:
    return [extract_company_info(f) for f in resume_dir.glob("*.pdf")]

