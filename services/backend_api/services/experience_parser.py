"""
Job Experience Parser Module
- Extracts job experience history from structured/unstructured data
- Designed for modular enrichment and user profile integration
"""
from pathlib import Path
from typing import List, Dict, Any

def extract_experience(file_path: Path) -> List[Dict[str, Any]]:
    """Extract experience from a file by delegating to ResumeParser."""
    try:
        from services.backend_api.services.resume_parser import ResumeParser
        parser = ResumeParser()
        text = parser._extract_text_from_file(file_path)
        if not text:
            return [{"filename": file_path.name, "experience": []}]
        exp = parser._extract_experience_from_text(text)
        return [{"filename": file_path.name, "experience": exp}]
    except Exception:
        return [{"filename": file_path.name, "experience": []}]

def parse_all_experience(resume_dir: Path) -> List[Dict[str, Any]]:
    return [extract_experience(f) for f in resume_dir.glob("*.pdf")]

# Hook for enrichment (to be implemented in enrichment/experience_enricher.py)
def enrich_experience(experience_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Placeholder: call enrichment logic here
    return experience_data
