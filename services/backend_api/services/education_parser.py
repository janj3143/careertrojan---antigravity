"""
Education Parser Module
- Extracts education history from structured/unstructured data
- Designed for modular enrichment and user profile integration
"""
from pathlib import Path
from typing import List, Dict, Any


def extract_education(file_path: Path) -> List[Dict[str, Any]]:
    """Extract education from a file by delegating to ResumeParser."""
    try:
        from services.backend_api.services.resume_parser import ResumeParser
        parser = ResumeParser()
        text = parser._extract_text_from_file(file_path)
        if not text:
            return [{"filename": file_path.name, "education": []}]
        edu = parser._extract_education_from_text(text)
        return [{"filename": file_path.name, "education": edu}]
    except Exception:
        return [{"filename": file_path.name, "education": []}]

# --- User_final integration hook ---
def attach_education_to_user_profile(user_profile: dict, education_data: List[Dict[str, Any]]) -> dict:
    """
    Hook for User_final: Attach parsed education data to user profile structure.
    """
    user_profile = user_profile.copy()
    user_profile["education"] = education_data
    return user_profile

# --- Enrichment integration hook ---
def enrich_and_attach_education(user_profile: dict, education_data: List[Dict[str, Any]]) -> dict:
    """
    Hook for User_final: Enrich education data and attach to user profile.
    """
    # Placeholder: call enrichment logic here
    enriched = enrich_education(education_data)
    user_profile = user_profile.copy()
    user_profile["education"] = enriched
    return user_profile

def parse_all_education(resume_dir: Path) -> List[Dict[str, Any]]:
    return [extract_education(f) for f in resume_dir.glob("*.pdf")]

# Hook for enrichment (to be implemented in enrichment/education_enricher.py)
def enrich_education(education_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # No enrichment fallback is performed here.
    return education_data
