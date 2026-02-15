"""
Job Description Parser Module
- Extracts job descriptions and related metadata from structured/unstructured data
- Designed to link with job title parser and enrichment modules
"""
import re
from pathlib import Path
from typing import List, Dict, Any

from .advanced_web_scraper import robust_get
from bs4 import BeautifulSoup

# ---- Lightweight section-level extraction helpers ----
_TITLE_RE = re.compile(
    r"(?:job\s*title|position|role)\s*[:–\-]\s*(.+)", re.IGNORECASE
)
_REQ_RE = re.compile(
    r"(?:requirements?|qualifications?|must\s*have)\s*[:–\-]?", re.IGNORECASE
)


def _extract_text(file_path: Path) -> str:
    """Pull raw text from a file using the shared file_parser utility."""
    try:
        from services.backend_api.utils.file_parser import extract_text
        return extract_text(file_path) or ""
    except Exception:
        if file_path.suffix.lower() == ".txt":
            return file_path.read_text(errors="replace")
        return ""


def _parse_sections(text: str) -> List[Dict[str, Any]]:
    """Best-effort extraction of title / description / requirements."""
    results: List[Dict[str, Any]] = []
    title_match = _TITLE_RE.search(text)
    title = title_match.group(1).strip() if title_match else None

    # Pull requirements list items (lines starting with bullet/dash/number)
    reqs: List[str] = []
    in_req_section = False
    for line in text.splitlines():
        if _REQ_RE.search(line):
            in_req_section = True
            continue
        if in_req_section:
            stripped = re.sub(r"^[\-\*•\d\.\)]+\s*", "", line).strip()
            if stripped:
                reqs.append(stripped)
            elif reqs:  # blank line ends section
                break

    desc = text[:500].strip() if text else ""
    results.append(
        {"title": title, "description": desc, "requirements": reqs}
    )
    return results


def extract_job_descriptions(file_path: Path, web_url: str = None) -> List[Dict[str, Any]]:
    """Extract job descriptions from a file — never hardcoded output."""
    raw = _extract_text(file_path)
    parsed = _parse_sections(raw) if raw else []
    job_descs = [{
        "filename": file_path.name,
        "job_descriptions": parsed,
    }]
    # --- Web scraping enrichment hook ---
    if web_url:
        resp = robust_get(web_url)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
            desc = soup.find('div', class_='job-description').get_text(strip=True) if soup.find('div', class_='job-description') else ''
            reqs = [li.get_text(strip=True) for li in soup.select('ul.requirements li')]
            job_descs.append({
                "web_url": web_url,
                "job_descriptions": [{"title": title, "description": desc, "requirements": reqs}]
            })
    return job_descs

def parse_all_job_descriptions(resume_dir: Path) -> List[Dict[str, Any]]:
    return [extract_job_descriptions(f) for f in resume_dir.glob("*.pdf")]

# Hook for enrichment (to be implemented in enrichment/job_description_enricher.py)
def enrich_job_descriptions(job_desc_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Placeholder: call enrichment logic here
    return job_desc_data
