"""
Keyword Enrichment Module
- Integrates keyword extraction, similarity, and thesaurus building into the enrichment pipeline
- Ready for LLM/NLP/Bayesian hybrid enrichment
"""
from typing import List, Dict, Iterable, Tuple
from services.backend_api.services.keyword_extractor import extract_keywords, build_thesaurus


import re
from services.backend_api.services.enrichment.job_title_similarity import detect_industry_migrations, job_title_similarity

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


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def extract_ngrams(text: str, n: int) -> List[str]:
    tokens = _tokenize(text)
    return [" ".join(tokens[i:i + n]) for i in range(0, max(len(tokens) - n + 1, 0))]


def extract_collocations(
    texts: Iterable[str],
    ngram_range: Tuple[int, int] = (2, 3),
    min_freq: int = 2,
) -> List[str]:
    """
    Lightweight collocation extractor over a corpus of texts.
    Returns n-grams that meet a minimum frequency threshold.
    """
    from collections import Counter

    ngram_counts = Counter()
    for text in texts:
        for n in range(ngram_range[0], ngram_range[1] + 1):
            ngram_counts.update(extract_ngrams(text, n))

    return [ngram for ngram, count in ngram_counts.items() if count >= min_freq]


def _normalize_collocation_phrases(collocation_phrases: Iterable) -> List[str]:
    phrases: List[str] = []
    for item in collocation_phrases:
        if isinstance(item, dict):
            phrase = item.get("phrase") or item.get("ngram")
        else:
            phrase = str(item)
        if phrase:
            phrases.append(phrase)
    return phrases


def match_collocations(text: str, collocation_phrases: Iterable) -> List[str]:
    """
    Return collocation phrases found in the provided text.
    Uses word-boundary regex matching for precision.
    """
    if not text or not collocation_phrases:
        return []

    phrases = _normalize_collocation_phrases(collocation_phrases)
    hits: List[str] = []
    for phrase in phrases:
        pattern = rf"\b{re.escape(phrase.lower())}\b"
        if re.search(pattern, text.lower()):
            hits.append(phrase)
    return hits


def score_pmi(
    texts: Iterable[str],
    ngram: str,
) -> float:
    """
    Compute a simple PMI score for a given bigram using a corpus.
    Returns 0.0 if counts are insufficient.
    """
    from collections import Counter
    import math

    tokens = []
    for text in texts:
        tokens.extend(_tokenize(text))

    words = ngram.split()
    if len(words) != 2:
        return 0.0

    word_counts = Counter(tokens)
    bigram_counts = Counter(zip(tokens, tokens[1:]))

    total_tokens = len(tokens)
    if total_tokens < 2:
        return 0.0

    w1, w2 = words
    bigram_count = bigram_counts.get((w1, w2), 0)
    if bigram_count == 0:
        return 0.0

    p_w1 = word_counts[w1] / total_tokens
    p_w2 = word_counts[w2] / total_tokens
    p_w1_w2 = bigram_count / (total_tokens - 1)
    if p_w1 == 0 or p_w2 == 0:
        return 0.0

    return math.log2(p_w1_w2 / (p_w1 * p_w2))

def enrich_keywords(
    text: str,
    job_titles: List[str] = None,
    job_desc: str = None,
    corpus_texts: Iterable[str] = None,
    collocation_phrases: Iterable[str] = None,
) -> Dict[str, List[str]]:
    """
    Advanced keyword enrichment: keywords, acronyms, pseudo-acronyms, near-phrases, industry migrations, and job title similarity.
    Links to job titles, job descriptions, and user hooks.
    """
    keywords = extract_keywords(text)
    acronyms = extract_acronyms(text)
    near_phrases = extract_near_phrases(text)
    bigrams = extract_ngrams(text, 2)
    trigrams = extract_ngrams(text, 3)
    collocations = extract_collocations(corpus_texts, (2, 3)) if corpus_texts else []
    collocation_matches = match_collocations(text, collocation_phrases) if collocation_phrases else []
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
        "bigrams": bigrams,
        "trigrams": trigrams,
        "collocations": collocations,
        "collocation_matches": collocation_matches,
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
            "bigrams",
            "trigrams",
            "collocations",
            "collocation_matches",
            "industry_migrations",
            "job_title_similarity",
            "job_desc_keywords"
        ]
    }
