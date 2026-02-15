"""
Salary & Package Parser Module
"""
from pathlib import Path

def extract_salary_info(file_path: Path, job_title: str = None, location: str = None) -> dict:
    """Extract salary data from file content — never returns fabricated numbers."""
    salary_info = {"filename": file_path.name, "salary": None, "package": None}

    # Attempt to extract salary mentions from the file text itself
    try:
        text = file_path.read_text(errors="replace") if file_path.suffix.lower() == ".txt" else ""
        if text:
            import re
            # Match common salary patterns: $120,000 | 120k | £80,000 etc.
            m = re.search(r'[\$\u00a3\u20ac]\s*[\d,]+(?:\.\d{2})?(?:\s*[kK])?', text)
            if m:
                salary_info["salary"] = m.group(0).strip()
    except Exception:
        pass  # Graceful — return None, never fabricate

    return salary_info

def parse_all_salaries(resume_dir: Path) -> list:
    return [extract_salary_info(f) for f in resume_dir.glob("*.pdf")]
