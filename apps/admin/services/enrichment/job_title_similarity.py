"""
Job Title Similarity and Migration Module
- Computes similarity between job titles (fuzzy, semantic, and industry-aware)
- Tracks industry term migrations (e.g., MRP → ERP) and synonym trends
- Designed for integration with keyword enrichment and user-facing analytics
"""
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from services.keyword_extractor import extract_keywords, build_thesaurus

# Example: Industry migration map (expandable)
INDUSTRY_MIGRATIONS = {
    "MRP": "ERP",
    "MIS": "IT",
    "Personnel": "HR",
    # Add more as detected
}


def job_title_similarity(title1: str, title2: str) -> float:
    """
    Compute fuzzy similarity between two job titles.
    """
    return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()


def detect_industry_migrations(keywords: List[str]) -> Dict[str, str]:
    """
    Detect and map industry term migrations in a set of keywords.
    """
    migrations = {}
    for kw in keywords:
        if kw in INDUSTRY_MIGRATIONS:
            migrations[kw] = INDUSTRY_MIGRATIONS[kw]
    return migrations


def enrich_job_titles_with_similarity_and_migration(job_titles: List[str], all_keywords: List[str]) -> Dict[str, any]:
    """
    Enrich job titles with similarity matrix and detected industry migrations.
    """
    similarity_matrix = {
        (t1, t2): job_title_similarity(t1, t2)
        for i, t1 in enumerate(job_titles)
        for t2 in job_titles[i+1:]
    }
    migrations = detect_industry_migrations(all_keywords)
    return {
        "similarity_matrix": similarity_matrix,
        "industry_migrations": migrations
    }

# TODO: Integrate with keyword enrichment pipeline and user-facing analytics
