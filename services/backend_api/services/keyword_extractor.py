# --- User_final integration hook ---
def attach_keywords_to_user_profile(user_profile: dict, keywords: List[str]) -> dict:
    """
    Hook for User_final: Attach extracted keywords to user profile structure.
    """
    user_profile = user_profile.copy()
    user_profile["keywords"] = keywords
    return user_profile

# --- AI enrichment integration hook ---
def enrich_and_attach_keywords(user_profile: dict, text: str) -> dict:
    """
    Hook for User_final/AI enrichment: Extract, enrich, and attach keywords and similarities to user profile.
    """
    keywords = extract_keywords(text)
    thesaurus = build_thesaurus(keywords)
    user_profile = user_profile.copy()
    user_profile["keywords"] = keywords
    user_profile["keyword_thesaurus"] = thesaurus
    return user_profile

# --- Additional keyword enrichment elements ---
def extract_ngrams(text: str, n: int = 2, top_n: int = 20) -> List[str]:
    """
    Extracts top n-grams (bigrams, trigrams, etc.) from text.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    vectorizer = CountVectorizer(ngram_range=(n, n), stop_words='english').fit([text])
    ngrams = vectorizer.get_feature_names_out()
    counts = vectorizer.transform([text]).toarray().flatten()
    ngram_counts = sorted(zip(ngrams, counts), key=lambda x: -x[1])
    return [ng for ng, _ in ngram_counts[:top_n]]

# Future: Add context-aware keyword extraction (e.g., using transformers/LLMs)
# Future: Add keyword importance scoring (e.g., using TextRank, RAKE, or LLM-based relevance)
"""
Keyword Extractor & Thesaurus Builder (Optimized)
- Extracts keywords, noun phrases, and named entities
- Computes keyword similarity (for thesaurus/acronym/psuedo-acronym enrichment)
- Designed for AI enrichment and user profile integration
"""
import spacy
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

nlp = spacy.load("en_core_web_sm")

def extract_noun_chunks(text: str, top_n: int = 20) -> List[str]:
    doc = nlp(text)
    noun_chunks = [chunk.text.lower().strip() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 2]
    return [phrase for phrase, _ in Counter(noun_chunks).most_common(top_n)]

def extract_named_entities(text: str, top_n: int = 20) -> List[str]:
    doc = nlp(text)
    entities = [ent.text.lower() for ent in doc.ents if ent.label_ in {"ORG", "PRODUCT", "GPE", "PERSON"}]
    return [ent for ent, _ in Counter(entities).most_common(top_n)]

def extract_keywords(text: str, top_n: int = 30) -> List[str]:
    return list(set(extract_noun_chunks(text, top_n) + extract_named_entities(text, top_n)))

def compute_keyword_similarity(keywords: List[str]) -> Dict[Tuple[str, str], float]:
    # Use TF-IDF cosine similarity for keyword pairs
    if not keywords:
        return {}
    vectorizer = TfidfVectorizer().fit(keywords)
    tfidf = vectorizer.transform(keywords)
    sim_matrix = cosine_similarity(tfidf)
    sim_dict = {}
    for i, kw1 in enumerate(keywords):
        for j, kw2 in enumerate(keywords):
            if i < j:
                sim_dict[(kw1, kw2)] = float(sim_matrix[i, j])
    return sim_dict

def build_thesaurus(keywords: List[str], similarity_threshold: float = 0.7) -> Dict[str, List[str]]:
    sim_dict = compute_keyword_similarity(keywords)
    thesaurus = defaultdict(list)
    for (kw1, kw2), sim in sim_dict.items():
        if sim >= similarity_threshold:
            thesaurus[kw1].append(kw2)
            thesaurus[kw2].append(kw1)
    return dict(thesaurus)

def extract_acronyms(text: str) -> List[str]:
    # Simple acronym extraction (all-caps words, 2-6 chars)
    import re
    return list(set(re.findall(r'\b[A-Z]{2,6}\b', text)))

def extract_pseudo_acronyms(text: str) -> List[str]:
    # Extracts mixed-case or non-standard acronyms (e.g., iOS, eBay)
    import re
    return list(set(re.findall(r'\b[a-zA-Z]{2,6}\b', text)))
