"""
Job Title Parser Module
"""
from pathlib import Path

def extract_job_titles(file_path: Path) -> dict:
    """Extract job titles from a file by delegating to ResumeParser."""
    try:
        from services.backend_api.services.resume_parser import ResumeParser
        parser = ResumeParser()
        text = parser._extract_text_from_file(file_path)
        if not text:
            return {"filename": file_path.name, "job_titles": []}
        exp = parser._extract_experience_from_text(text)
        titles = list({e["job_title"] for e in exp if e.get("job_title")})
        return {"filename": file_path.name, "job_titles": titles}
    except Exception:
        return {"filename": file_path.name, "job_titles": []}

def parse_all_job_titles(resume_dir: Path) -> list:
    return [extract_job_titles(f) for f in resume_dir.glob("*.pdf")]
