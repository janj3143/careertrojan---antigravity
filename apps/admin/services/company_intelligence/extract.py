"""
Company extraction and normalization logic
"""
import re
from typing import List
from .config import COMPANY_PATTERNS

def extract_companies(text: str) -> List[str]:
    """Extract and normalize company names from text."""
    companies = set()
    for pat in COMPANY_PATTERNS:
        companies.update(re.findall(pat, text))
    # Normalize: strip, lower, deduplicate, unify suffixes
    norm = lambda name: re.sub(r'\s+', ' ', name.strip())
    return sorted(set(norm(c) for c in companies if c))
