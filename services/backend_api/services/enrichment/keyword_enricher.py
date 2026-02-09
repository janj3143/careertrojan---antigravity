"""
Keyword Enrichment Module
- Integrates keyword extraction, similarity, and thesaurus building into the enrichment pipeline
- Ready for LLM/NLP/Bayesian hybrid enrichment
"""
from typing import List, Dict
from services.keyword_extractor import extract_keywords, build_thesaurus


import re
from services.enrichment.job_title_similarity import detect_industry_migrations, job_title_similarity

def extract_acronyms(text: str) -> List[str]:
    """
    Extracts acronyms and pseudo-acronyms (all-caps, CamelCase, or capitalized joined words).
    """
    # True acronyms: 2+ uppercase letters
    acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
    # Pseudo-acronyms: CamelCase or joined capitalized words
    pseudo = re.findall(r'\b(?:[A-Z][a-z]+){2,}\b', text)
    return list(set(acronyms + pseudo))

def extract_near_phrases(text: str, window: int = 3) -> List[str]:
    """
    Extracts multi-word phrases where words appear near each other (within window).
    E.g., 'Robot Automation', 'Hydrogen ... Catalyst'.
    """
    tokens = re.findall(r'\w+', text)
    phrases = set()
    for i, word in enumerate(tokens):
        for j in range(i+1, min(i+window+1, len(tokens))):
            phrase = f"{tokens[i]} {tokens[j]}"
            phrases.add(phrase)
    return list(phrases)

def enrich_keywords(text: str, job_titles: List[str] = None, job_desc: str = None) -> Dict[str, List[str]]:
    """
    Advanced keyword enrichment: keywords, acronyms, pseudo-acronyms, near-phrases, industry migrations, and job title similarity.
    Links to job titles, job descriptions, and user hooks.
    """
    keywords = extract_keywords(text)
    acronyms = extract_acronyms(text)
    near_phrases = extract_near_phrases(text)
    thesaurus = build_thesaurus(keywords)
    # Industry migration detection
    migrations = detect_industry_migrations(keywords + acronyms)
    # Job title similarity (if job_titles provided)
    similarity = {}
    if job_titles:
        for jt in job_titles:
            similarity[jt] = {other: job_title_similarity(jt, other) for other in job_titles if other != jt}
    # Optionally link to job description
    job_desc_keywords = extract_keywords(job_desc) if job_desc else []
    return {
        "keywords": keywords,
        "acronyms": acronyms,
        "pseudo_acronyms": [a for a in acronyms if len(a) > 2],
        "near_phrases": near_phrases,
        "thesaurus": thesaurus,
        "industry_migrations": migrations,
        "job_title_similarity": similarity,
        "job_desc_keywords": job_desc_keywords,
        # User-facing hooks
        "user_hooks": [
            "keywords",
            "acronyms",
            "pseudo_acronyms",
            "near_phrases",
            "industry_migrations",
            "job_title_similarity",
            "job_desc_keywords"
        ]
    }
