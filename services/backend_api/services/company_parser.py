Company Parser Module
"""
from pathlib import Path

def extract_company_info(file_path: Path) -> dict:
    """Extract company information from a file by delegating to ResumeParser."""
    try:
        from services.backend_api.services.resume_parser import ResumeParser
        parser = ResumeParser()
        companies = parser._extract_company_data_from_file(file_path)
        return {
            "filename": file_path.name,
            "company": companies[0] if companies else None,
            "fields": {},
        }
    except Exception:
        return {"filename": file_path.name, "company": None, "fields": {}}

def parse_all_companies(resume_dir: Path) -> list:
    return [extract_company_info(f) for f in resume_dir.glob("*.pdf")]

