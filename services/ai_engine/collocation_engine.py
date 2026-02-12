"""
CareerTrojan — Self-Learning Collocation & N-gram Engine
=========================================================

CRITICAL DESIGN PRINCIPLE: This engine LEARNS from every user interaction.
Unlike a static gazetteer that never grows, this engine has a full feedback loop:

  User uploads CV / searches / browses jobs
    → interaction_logger captures text
    → enrichment_ingest() feeds new text to the engine
    → discover new collocations via PMI / n-gram / co-occurrence
    → persist_learned_phrases() writes back to L: drive source of truth
    → next user gets richer phrase matching

Five complementary techniques:
  1. N-gram Extraction        — bigrams/trigrams as first-class tokens
  2. PMI Scoring              — statistical "glue" score for word pairs
  3. spaCy PhraseMatcher      — exact match on known domain phrases
  4. spaCy EntityRuler        — pattern-based custom NER (SKILL, CERT, etc.)
  5. Window Co-occurrence     — sliding window for near-but-not-adjacent pairs

Data flow:
  L:/antigravity_version_ai_data_final/ai_data_final/
    ├── gazetteers/              ← READS seed gazetteers
    ├── consolidated_terms.json  ← READS + WRITES (grows over time)
    ├── canonical_glossary.json  ← READS
    ├── learned_collocations.json ← READS + WRITES (engine's learned phrases)
    ├── collocation_analysis.json ← WRITES (full analysis reports)
    └── USER DATA/interactions/  ← READS (user interaction text for learning)

Usage:
    from services.ai_engine.collocation_engine import collocation_engine

    # Ingest new text from a user interaction (called by enrichment pipeline)
    collocation_engine.enrichment_ingest(["uploaded CV text", "search query text"])

    # Phrase-aware tokenization (uses both seed + learned phrases)
    tokens = collocation_engine.tokenize_with_phrases("Blue Hydrogen is key")
    # → ["Blue Hydrogen", "is", "key"]

    # Persist learned phrases back to L: drive (called periodically)
    collocation_engine.persist_learned_phrases()
"""

import os
import re
import json
import math
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)

# ── Data paths ───────────────────────────────────────────────────────────
_DATA_ROOT = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
AI_DATA_DIR = _DATA_ROOT / "ai_data_final"
GAZETTEERS_DIR = AI_DATA_DIR / "gazetteers"
LEARNED_PHRASES_PATH = GAZETTEERS_DIR / "learned_collocations.json"
INTERACTION_DIR = _DATA_ROOT / "USER DATA" / "interactions"
COLLOCATION_ANALYSIS_PATH = AI_DATA_DIR / "collocation_analysis.json"

# Local project mirror (for Docker / production where L: isn't mounted)
_LOCAL_DATA_ROOT = Path(os.getenv("CAREERTROJAN_LOCAL_DATA", r"C:\careertrojan\data\ai_data_final"))
LOCAL_GAZETTEERS_DIR = _LOCAL_DATA_ROOT / "gazetteers"


@dataclass
class CollocationResult:
    """A discovered collocation (multi-word expression)."""
    phrase: str
    score: float
    method: str  # "pmi", "chi2", "frequency", "gazetteer", "cooccurrence"
    frequency: int = 0
    label: Optional[str] = None  # NER label if applicable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phrase": self.phrase,
            "score": round(self.score, 4),
            "method": self.method,
            "frequency": self.frequency,
            "label": self.label,
        }


class CollocationEngine:
    """
    Self-learning phrase-aware NLP engine for domain-specific term extraction.
    Combines statistical methods (PMI, chi-square) with rule-based matching
    (gazetteers, EntityRuler) AND persistent learning from user interactions.

    Key difference from a static gazetteer:
      - `load_learned_phrases()` restores all previously discovered phrases from disk
      - `enrichment_ingest()` discovers new phrases from fresh user text
      - `persist_learned_phrases()` writes discoveries back to L: drive
      - known_phrases grows over time and SURVIVES restart
    """

    # ── Seed gazetteers ──────────────────────────────────────────────────
    # These ship with the engine and are always available even before any
    # learning has occurred. They act as the baseline domain dictionary.
    SEED_PHRASES: Dict[str, str] = {
        # TECH_SKILL
        "machine learning": "TECH_SKILL", "deep learning": "TECH_SKILL",
        "natural language processing": "TECH_SKILL", "computer vision": "TECH_SKILL",
        "data science": "TECH_SKILL", "data engineering": "TECH_SKILL",
        "cloud computing": "TECH_SKILL", "devops": "TECH_SKILL",
        "full stack": "TECH_SKILL", "front end": "TECH_SKILL",
        "back end": "TECH_SKILL", "mobile development": "TECH_SKILL",
        "embedded systems": "TECH_SKILL", "cyber security": "TECH_SKILL",
        "artificial intelligence": "TECH_SKILL", "data analytics": "TECH_SKILL",
        "business intelligence": "TECH_SKILL", "quality assurance": "TECH_SKILL",
        "test automation": "TECH_SKILL", "continuous integration": "TECH_SKILL",
        "continuous deployment": "TECH_SKILL", "infrastructure as code": "TECH_SKILL",
        "site reliability": "TECH_SKILL", "blue hydrogen": "TECH_SKILL",
        "green hydrogen": "TECH_SKILL", "ladder logic": "TECH_SKILL",
        "plc programming": "TECH_SKILL", "scada systems": "TECH_SKILL",
        "process control": "TECH_SKILL", "industrial automation": "TECH_SKILL",
        "robotic process automation": "TECH_SKILL",
        # CLOUD_PLATFORM
        "amazon web services": "CLOUD_PLATFORM", "microsoft azure": "CLOUD_PLATFORM",
        "google cloud platform": "CLOUD_PLATFORM", "google cloud": "CLOUD_PLATFORM",
        "digital ocean": "CLOUD_PLATFORM",
        # CERTIFICATION
        "project management professional": "CERTIFICATION",
        "certified scrum master": "CERTIFICATION", "aws certified": "CERTIFICATION",
        "azure fundamentals": "CERTIFICATION", "six sigma": "CERTIFICATION",
        "lean six sigma": "CERTIFICATION", "green belt": "CERTIFICATION",
        "black belt": "CERTIFICATION", "itil foundation": "CERTIFICATION",
        "comptia security": "CERTIFICATION", "cissp certified": "CERTIFICATION",
        # JOB_TITLE
        "software engineer": "JOB_TITLE", "data scientist": "JOB_TITLE",
        "product manager": "JOB_TITLE", "project manager": "JOB_TITLE",
        "engineering manager": "JOB_TITLE", "chief technology officer": "JOB_TITLE",
        "solutions architect": "JOB_TITLE", "business analyst": "JOB_TITLE",
        "systems administrator": "JOB_TITLE", "database administrator": "JOB_TITLE",
        "network engineer": "JOB_TITLE", "security analyst": "JOB_TITLE",
        "ux designer": "JOB_TITLE", "ui developer": "JOB_TITLE",
        "machine learning engineer": "JOB_TITLE", "devops engineer": "JOB_TITLE",
        "site reliability engineer": "JOB_TITLE", "data engineer": "JOB_TITLE",
        "platform engineer": "JOB_TITLE", "technical lead": "JOB_TITLE",
        # METHODOLOGY
        "agile methodology": "METHODOLOGY", "scrum framework": "METHODOLOGY",
        "waterfall methodology": "METHODOLOGY", "kanban board": "METHODOLOGY",
        "design thinking": "METHODOLOGY", "test driven development": "METHODOLOGY",
        "behavior driven development": "METHODOLOGY", "pair programming": "METHODOLOGY",
        "code review": "METHODOLOGY", "continuous improvement": "METHODOLOGY",
        "circular economy": "METHODOLOGY", "lean manufacturing": "METHODOLOGY",
        # SOFT_SKILL
        "team leadership": "SOFT_SKILL", "project management": "SOFT_SKILL",
        "cross functional": "SOFT_SKILL", "stakeholder management": "SOFT_SKILL",
        "change management": "SOFT_SKILL", "conflict resolution": "SOFT_SKILL",
        "problem solving": "SOFT_SKILL", "critical thinking": "SOFT_SKILL",
        "communication skills": "SOFT_SKILL", "time management": "SOFT_SKILL",
        # INDUSTRY_TERM
        "supply chain": "INDUSTRY_TERM", "due diligence": "INDUSTRY_TERM",
        "risk assessment": "INDUSTRY_TERM", "regulatory compliance": "INDUSTRY_TERM",
        "intellectual property": "INDUSTRY_TERM", "market analysis": "INDUSTRY_TERM",
        "customer experience": "INDUSTRY_TERM", "user experience": "INDUSTRY_TERM",
        "digital transformation": "INDUSTRY_TERM", "internet of things": "INDUSTRY_TERM",
        "augmented reality": "INDUSTRY_TERM", "virtual reality": "INDUSTRY_TERM",
    }

    ABBREVIATION_MAP: Dict[str, str] = {
        "ML": "machine learning", "DL": "deep learning", "NLP": "natural language processing",
        "CV": "computer vision", "AI": "artificial intelligence", "DS": "data science",
        "DE": "data engineering", "BI": "business intelligence", "QA": "quality assurance",
        "CI": "continuous integration", "CD": "continuous deployment",
        "IaC": "infrastructure as code", "SRE": "site reliability",
        "AWS": "amazon web services", "GCP": "google cloud platform",
        "PMP": "project management professional", "CSM": "certified scrum master",
        "RPA": "robotic process automation", "IoT": "internet of things",
        "AR": "augmented reality", "VR": "virtual reality",
        "PLC": "plc programming", "SCADA": "scada systems",
    }

    def __init__(self, min_freq: int = 3, pmi_threshold: float = 3.0, window_size: int = 5):
        self.min_freq = min_freq
        self.pmi_threshold = pmi_threshold
        self.window_size = window_size

        # Thread safety for concurrent ingestion
        self._lock = Lock()

        # Discovered phrase sets (grows over time, persisted to disk)
        self.known_phrases: Set[str] = set()
        self.gazetteers: Dict[str, List[str]] = {}
        self.collocation_scores: Dict[str, CollocationResult] = {}

        # Learning state — tracks newly discovered phrases since last persist
        self._learned_phrases: Dict[str, Dict[str, Any]] = {}  # phrase → {label, score, method, discovered_at, frequency}
        self._ingestion_count: int = 0
        self._last_persist_time: float = 0.0

        # spaCy pipeline (lazy-loaded)
        self._nlp = None
        self._phrase_matcher = None

        # ── Bootstrap: seed phrases + persisted learned phrases ──────────
        self._load_seed_phrases()
        self._load_learned_phrases()

        logger.info(
            "CollocationEngine initialized (min_freq=%d, pmi=%.1f, window=%d) — "
            "%d seed phrases + %d learned phrases = %d total known",
            min_freq, pmi_threshold, window_size,
            len(self.SEED_PHRASES), len(self._learned_phrases), len(self.known_phrases),
        )

    # ── Bootstrap helpers ────────────────────────────────────────────────

    def _load_seed_phrases(self) -> None:
        """Load hardcoded seed phrases into known_phrases and gazetteers."""
        by_label: Dict[str, List[str]] = defaultdict(list)
        for phrase, label in self.SEED_PHRASES.items():
            self.known_phrases.add(phrase.lower())
            by_label[label].append(phrase)
        for label, terms in by_label.items():
            self.gazetteers.setdefault(label, []).extend(terms)

    def _load_learned_phrases(self) -> None:
        """
        Restore previously persisted learned phrases from L: drive.
        This is what makes the engine survive restarts with all its learning intact.
        """
        if not LEARNED_PHRASES_PATH.exists():
            logger.info("No learned_collocations.json found — starting fresh learning")
            return
        try:
            with open(LEARNED_PHRASES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            phrases = data.get("phrases", {})
            for phrase, meta in phrases.items():
                key = phrase.lower()
                self._learned_phrases[key] = meta
                self.known_phrases.add(key)
                label = meta.get("label")
                if label:
                    self.gazetteers.setdefault(label, []).append(phrase)
            self._ingestion_count = data.get("total_ingestions", 0)
            logger.info("Restored %d learned phrases from %s", len(phrases), LEARNED_PHRASES_PATH)
        except Exception as e:
            logger.warning("Failed to load learned phrases: %s — starting fresh", e)

    # ── 1. N-gram Tokenization ───────────────────────────────────────────

    def extract_ngrams(self, texts: List[str], n_range: Tuple[int, int] = (2, 3),
                       top_k: int = 500) -> List[CollocationResult]:
        """
        Extract frequency-ranked n-grams from a corpus.
        Uses sklearn CountVectorizer for efficient n-gram extraction.
        """
        try:
            from sklearn.feature_extraction.text import CountVectorizer
        except ImportError:
            logger.error("sklearn not available — falling back to manual n-grams")
            return self._manual_ngrams(texts, n_range, top_k)

        vectorizer = CountVectorizer(
            ngram_range=n_range,
            min_df=self.min_freq,
            stop_words="english",
            max_features=top_k * 3,  # over-extract, then filter
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]+\b",  # allow hyphens in tokens
        )

        try:
            X = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            freqs = X.sum(axis=0).A1  # sum across documents

            results = []
            for phrase, freq in sorted(zip(feature_names, freqs), key=lambda x: -x[1])[:top_k]:
                if freq >= self.min_freq:
                    results.append(CollocationResult(
                        phrase=phrase,
                        score=float(freq),
                        method="frequency",
                        frequency=int(freq),
                    ))
                    self.known_phrases.add(phrase.lower())

            logger.info("Extracted %d n-grams (range %s) from %d texts", len(results), n_range, len(texts))
            return results

        except Exception as e:
            logger.error("N-gram extraction failed: %s", e)
            return []

    def _manual_ngrams(self, texts: List[str], n_range: Tuple[int, int], top_k: int) -> List[CollocationResult]:
        """Fallback manual n-gram extraction without sklearn."""
        counter = Counter()
        for text in texts:
            words = re.findall(r"\b[a-zA-Z][a-zA-Z-]+\b", text.lower())
            for n in range(n_range[0], n_range[1] + 1):
                for i in range(len(words) - n + 1):
                    gram = " ".join(words[i:i + n])
                    counter[gram] += 1

        results = []
        for phrase, freq in counter.most_common(top_k):
            if freq >= self.min_freq:
                results.append(CollocationResult(phrase=phrase, score=float(freq),
                                                method="frequency", frequency=freq))
                self.known_phrases.add(phrase)
        return results

    # ── 2. Pointwise Mutual Information (PMI) ────────────────────────────

    def compute_pmi(self, texts: List[str], top_k: int = 300) -> List[CollocationResult]:
        """
        Compute PMI scores for word pairs.
        PMI(x,y) = log2( P(x,y) / (P(x) * P(y)) )
        High PMI = words appear together far more than chance.
        """
        unigram_counts = Counter()
        bigram_counts = Counter()
        total_words = 0

        for text in texts:
            words = re.findall(r"\b[a-zA-Z][a-zA-Z-]+\b", text.lower())
            total_words += len(words)
            unigram_counts.update(words)
            for i in range(len(words) - 1):
                bigram_counts[(words[i], words[i + 1])] += 1

        total_bigrams = sum(bigram_counts.values())
        if total_bigrams == 0:
            return []

        results = []
        for (w1, w2), freq in bigram_counts.items():
            if freq < self.min_freq:
                continue

            p_xy = freq / total_bigrams
            p_x = unigram_counts[w1] / total_words
            p_y = unigram_counts[w2] / total_words

            if p_x > 0 and p_y > 0:
                pmi = math.log2(p_xy / (p_x * p_y))
                if pmi >= self.pmi_threshold:
                    phrase = f"{w1} {w2}"
                    results.append(CollocationResult(
                        phrase=phrase,
                        score=pmi,
                        method="pmi",
                        frequency=freq,
                    ))
                    self.known_phrases.add(phrase)

        results.sort(key=lambda r: -r.score)
        logger.info("Found %d high-PMI collocations (threshold=%.1f)", len(results[:top_k]), self.pmi_threshold)
        return results[:top_k]

    # ── 3. NLTK Collocation Integration ──────────────────────────────────

    def find_nltk_collocations(self, texts: List[str], top_k: int = 200,
                                method: str = "pmi") -> List[CollocationResult]:
        """
        Use NLTK's collocation finders with multiple scoring methods.
        Methods: pmi, chi_sq, likelihood_ratio, student_t, raw_freq
        """
        try:
            from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder
            from nltk.metrics import BigramAssocMeasures, TrigramAssocMeasures
            from nltk.tokenize import word_tokenize
        except ImportError:
            logger.warning("NLTK not available — skipping NLTK collocations")
            return []

        # Tokenize all texts
        all_words = []
        for text in texts:
            try:
                all_words.extend(word_tokenize(text.lower()))
            except Exception:
                all_words.extend(text.lower().split())

        results = []

        # Bigrams
        bigram_finder = BigramCollocationFinder.from_words(all_words)
        bigram_finder.apply_freq_filter(self.min_freq)

        scoring_map = {
            "pmi": BigramAssocMeasures.pmi,
            "chi_sq": BigramAssocMeasures.chi_sq,
            "likelihood_ratio": BigramAssocMeasures.likelihood_ratio,
            "student_t": BigramAssocMeasures.student_t,
            "raw_freq": BigramAssocMeasures.raw_freq,
        }
        score_fn = scoring_map.get(method, BigramAssocMeasures.pmi)

        for (w1, w2), score in bigram_finder.score_ngrams(score_fn)[:top_k]:
            if w1.isalpha() and w2.isalpha():
                phrase = f"{w1} {w2}"
                results.append(CollocationResult(
                    phrase=phrase, score=score, method=f"nltk_{method}",
                    frequency=bigram_finder.ngram_fd[(w1, w2)],
                ))
                self.known_phrases.add(phrase)

        # Trigrams
        trigram_finder = TrigramCollocationFinder.from_words(all_words)
        trigram_finder.apply_freq_filter(self.min_freq)

        tri_scoring = {
            "pmi": TrigramAssocMeasures.pmi,
            "chi_sq": TrigramAssocMeasures.chi_sq,
            "likelihood_ratio": TrigramAssocMeasures.likelihood_ratio,
        }
        tri_fn = tri_scoring.get(method, TrigramAssocMeasures.pmi)

        for (w1, w2, w3), score in trigram_finder.score_ngrams(tri_fn)[:top_k // 2]:
            if w1.isalpha() and w2.isalpha() and w3.isalpha():
                phrase = f"{w1} {w2} {w3}"
                results.append(CollocationResult(
                    phrase=phrase, score=score, method=f"nltk_{method}_trigram",
                    frequency=trigram_finder.ngram_fd[(w1, w2, w3)],
                ))
                self.known_phrases.add(phrase)

        logger.info("NLTK found %d collocations (method=%s)", len(results), method)
        return results

    # ── 4. Named Entity Recognition with Custom Gazetteers ──────────────

    def load_gazetteers(self, gazetteers_path: Optional[Path] = None) -> int:
        """
        Load domain-specific gazetteers (multi-word term dictionaries).
        Each gazetteer is a JSON file: { "label": "LABEL", "terms": ["term1", ...] }
        Also loads from consolidated_terms.json and canonical_glossary.json in ai_data_final.
        """
        loaded = 0

        # Load from gazetteers directory (L: drive, then local mirror)
        gaz_dirs = [gazetteers_path or GAZETTEERS_DIR]
        if LOCAL_GAZETTEERS_DIR.exists() and LOCAL_GAZETTEERS_DIR != gaz_dirs[0]:
            gaz_dirs.append(LOCAL_GAZETTEERS_DIR)

        for gaz_dir in gaz_dirs:
            if not gaz_dir.exists():
                continue
            for gaz_file in gaz_dir.glob("*.json"):
                # Skip the learned_collocations file (loaded separately)
                if gaz_file.stem == "learned_collocations":
                    continue
                try:
                    with open(gaz_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    label = data.get("label", gaz_file.stem.upper())

                    # Handle terms list (standard gazetteers)
                    terms = data.get("terms", [])
                    if terms:
                        existing = self.gazetteers.get(label, [])
                        new_terms = [t for t in terms if t.lower() not in {e.lower() for e in existing}]
                        self.gazetteers.setdefault(label, []).extend(new_terms)
                        self.known_phrases.update(t.lower() for t in terms)
                        loaded += len(new_terms)

                    # Handle abbreviations map
                    abbrevs = data.get("abbreviations", {})
                    if abbrevs:
                        for abbr, expansion in abbrevs.items():
                            if abbr not in self.ABBREVIATION_MAP:
                                self.ABBREVIATION_MAP[abbr] = expansion
                        loaded += len(abbrevs)
                        logger.info("Loaded %d abbreviations from %s", len(abbrevs), gaz_file.name)

                except Exception as e:
                    logger.warning("Failed to load gazetteer %s: %s", gaz_file, e)

        # Auto-load from existing ai_data_final glossaries
        for glossary_name in ["consolidated_terms.json", "canonical_glossary.json"]:
            glossary_path = AI_DATA_DIR / glossary_name
            if glossary_path.exists():
                try:
                    with open(glossary_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Handle both list and dict formats
                    terms = []
                    if isinstance(data, list):
                        terms = [str(t) for t in data if isinstance(t, str)]
                    elif isinstance(data, dict):
                        for v in data.values():
                            if isinstance(v, list):
                                terms.extend([str(t) for t in v if isinstance(t, str)])
                            elif isinstance(v, str):
                                terms.append(v)
                    if terms:
                        self.gazetteers[f"GLOSSARY_{glossary_name.split('.')[0].upper()}"] = terms
                        self.known_phrases.update(t.lower() for t in terms if " " in t)
                        loaded += len(terms)
                        logger.info("Loaded %d terms from %s", len(terms), glossary_name)
                except Exception as e:
                    logger.warning("Failed to load %s: %s", glossary_name, e)

        logger.info("Loaded %d gazetteer terms across %d categories", loaded, len(self.gazetteers))
        return loaded

    def _get_nlp(self):
        """Lazy-load spaCy with custom EntityRuler and PhraseMatcher."""
        if self._nlp is not None:
            return self._nlp

        try:
            import spacy
            from spacy.language import Language

            try:
                self._nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("en_core_web_sm not found — using blank English model")
                self._nlp = spacy.blank("en")

            # Add EntityRuler with gazetteer patterns
            if self.gazetteers:
                ruler = self._nlp.add_pipe("entity_ruler", before="ner" if "ner" in self._nlp.pipe_names else None)
                patterns = []
                for label, terms in self.gazetteers.items():
                    for term in terms:
                        patterns.append({"label": label, "pattern": term})
                        # Also add lowercase variant
                        if term != term.lower():
                            patterns.append({"label": label, "pattern": term.lower()})
                ruler.add_patterns(patterns[:5000])  # Limit for performance
                logger.info("EntityRuler loaded with %d patterns", min(len(patterns), 5000))

            # Add PhraseMatcher for known collocations
            if self.known_phrases:
                from spacy.matcher import PhraseMatcher
                self._phrase_matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
                phrase_patterns = [self._nlp.make_doc(p) for p in list(self.known_phrases)[:10000]]
                if phrase_patterns:
                    self._phrase_matcher.add("COLLOCATION", phrase_patterns)
                    logger.info("PhraseMatcher loaded with %d patterns", len(phrase_patterns))

        except ImportError:
            logger.warning("spaCy not available — NER features disabled")
            self._nlp = None

        return self._nlp

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy + custom gazetteers."""
        nlp = self._get_nlp()
        if nlp is None:
            return []

        doc = nlp(text)
        entities = []
        seen = set()

        for ent in doc.ents:
            key = (ent.text.lower(), ent.label_)
            if key not in seen:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })
                seen.add(key)

        return entities

    # ── 5. Window-Based Co-occurrence ────────────────────────────────────

    def find_cooccurrences(self, texts: List[str], window: int = None,
                           top_k: int = 200) -> List[CollocationResult]:
        """
        Find frequently co-occurring words within a sliding window.
        Unlike bigrams, these words may be separated by other words.
        """
        window = window or self.window_size
        pair_counts = Counter()
        word_counts = Counter()

        for text in texts:
            words = [w.lower() for w in re.findall(r"\b[a-zA-Z][a-zA-Z-]+\b", text)]
            word_counts.update(words)
            for i, word_a in enumerate(words):
                for j in range(i + 1, min(i + window + 1, len(words))):
                    word_b = words[j]
                    if word_a != word_b:
                        pair = tuple(sorted([word_a, word_b]))
                        pair_counts[pair] += 1

        total = sum(word_counts.values())
        results = []

        for (w1, w2), freq in pair_counts.most_common(top_k * 3):
            if freq < self.min_freq:
                continue

            # Compute PMI for the co-occurrence pair
            p_xy = freq / max(sum(pair_counts.values()), 1)
            p_x = word_counts[w1] / total if total > 0 else 0
            p_y = word_counts[w2] / total if total > 0 else 0

            if p_x > 0 and p_y > 0:
                pmi = math.log2(p_xy / (p_x * p_y))
                if pmi >= self.pmi_threshold * 0.5:  # lower threshold for windowed pairs
                    results.append(CollocationResult(
                        phrase=f"{w1} ... {w2}",
                        score=pmi,
                        method="cooccurrence",
                        frequency=freq,
                    ))

        results.sort(key=lambda r: -r.score)
        logger.info("Found %d co-occurrence pairs (window=%d)", len(results[:top_k]), window)
        return results[:top_k]

    # ── 6. Phrase-Aware Tokenization ─────────────────────────────────────

    def tokenize_with_phrases(self, text: str) -> List[str]:
        """
        Tokenize text preserving known multi-word phrases.
        "Blue Hydrogen is key" → ["Blue Hydrogen", "is", "key"]
        """
        # Sort phrases by length (longest first) for greedy matching
        sorted_phrases = sorted(self.known_phrases, key=len, reverse=True)

        # Replace known phrases with underscored versions
        processed = text
        phrase_map = {}
        for phrase in sorted_phrases:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            replacement = phrase.replace(" ", "_PHRASE_SEP_")
            if pattern.search(processed):
                phrase_map[replacement] = phrase
                processed = pattern.sub(replacement, processed)

        # Tokenize
        raw_tokens = re.findall(r"\b[\w_]+(?:_PHRASE_SEP_[\w_]+)*\b", processed)

        # Restore phrase separators
        tokens = []
        for token in raw_tokens:
            if "_PHRASE_SEP_" in token:
                restored = token.replace("_PHRASE_SEP_", " ")
                # Find the original-cased version from known phrases
                tokens.append(phrase_map.get(token, restored))
            else:
                tokens.append(token)

        return tokens

    # ── 7. Full Corpus Analysis Pipeline ─────────────────────────────────

    def analyze_corpus(self, texts: List[str], save_results: bool = True) -> Dict[str, Any]:
        """
        Run all collocation discovery methods on a corpus.
        Returns a comprehensive report with all discovered phrases.
        """
        logger.info("Starting corpus analysis on %d texts...", len(texts))

        # Load gazetteers first (adds to known_phrases)
        self.load_gazetteers()

        # Run all methods
        ngram_results = self.extract_ngrams(texts, n_range=(2, 3))
        pmi_results = self.compute_pmi(texts)
        nltk_results = self.find_nltk_collocations(texts, method="pmi")
        cooccurrence_results = self.find_cooccurrences(texts)

        # Merge and deduplicate
        all_results = {}
        for result in ngram_results + pmi_results + nltk_results + cooccurrence_results:
            key = result.phrase.lower()
            if key not in all_results or result.score > all_results[key].score:
                all_results[key] = result

        # Build report
        report = {
            "timestamp": datetime.now().isoformat(),
            "corpus_size": len(texts),
            "total_phrases_discovered": len(all_results),
            "known_phrases_count": len(self.known_phrases),
            "methods": {
                "ngrams": {"count": len(ngram_results), "top_10": [r.to_dict() for r in ngram_results[:10]]},
                "pmi": {"count": len(pmi_results), "top_10": [r.to_dict() for r in pmi_results[:10]]},
                "nltk": {"count": len(nltk_results), "top_10": [r.to_dict() for r in nltk_results[:10]]},
                "cooccurrence": {"count": len(cooccurrence_results), "top_10": [r.to_dict() for r in cooccurrence_results[:10]]},
            },
            "all_phrases": [r.to_dict() for r in sorted(all_results.values(), key=lambda r: -r.score)],
            "gazetteers_loaded": {k: len(v) for k, v in self.gazetteers.items()},
        }

        if save_results:
            output_path = AI_DATA_DIR / "collocation_analysis.json"
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info("Results saved to %s", output_path)
            except Exception as e:
                logger.warning("Could not save results: %s", e)

        return report

    # ── 8. Enrichment Ingestion (THE LEARNING LOOP) ──────────────────────

    def enrichment_ingest(self, texts: List[str], source: str = "user_interaction") -> Dict[str, Any]:
        """
        Ingest new texts from user interactions and discover new collocations.
        This is the CORE LEARNING METHOD — called by the enrichment pipeline
        whenever new user data arrives (CV upload, search query, job browse).

        Returns a summary of what was discovered and whether persistence is needed.
        """
        if not texts:
            return {"discovered": 0, "total_known": len(self.known_phrases)}

        with self._lock:
            before_count = len(self.known_phrases)

            # Run lightweight discovery pipeline (skip heavy NLTK for speed)
            # 1. PMI on the fresh texts (min_freq=2 for small batches)
            old_min = self.min_freq
            self.min_freq = max(2, min(old_min, len(texts) // 5))
            pmi_results = self.compute_pmi(texts, top_k=100)

            # 2. N-gram frequency (bigrams/trigrams)
            ngram_results = self.extract_ngrams(texts, n_range=(2, 3), top_k=100)

            # 3. Co-occurrence for near-misses
            cooc_results = self.find_cooccurrences(texts, top_k=50)

            self.min_freq = old_min

            # Track newly discovered phrases with metadata
            now = datetime.now().isoformat()
            new_discoveries = 0
            for result in pmi_results + ngram_results + cooc_results:
                key = result.phrase.lower()
                if key not in self._learned_phrases and key not in self.SEED_PHRASES:
                    self._learned_phrases[key] = {
                        "label": result.label or self._infer_label(result.phrase),
                        "score": result.score,
                        "method": result.method,
                        "frequency": result.frequency,
                        "discovered_at": now,
                        "source": source,
                    }
                    new_discoveries += 1
                elif key in self._learned_phrases:
                    # Update frequency for already-known learned phrases
                    self._learned_phrases[key]["frequency"] = (
                        self._learned_phrases[key].get("frequency", 0) + result.frequency
                    )

            self._ingestion_count += 1
            after_count = len(self.known_phrases)

            # Auto-persist every 10 ingestions or when significant discoveries happen
            should_persist = (
                new_discoveries >= 20
                or self._ingestion_count % 10 == 0
                or (time.time() - self._last_persist_time) > 300  # 5 minutes
            )
            if should_persist and self._learned_phrases:
                self.persist_learned_phrases()

            summary = {
                "texts_ingested": len(texts),
                "new_discoveries": new_discoveries,
                "total_known_before": before_count,
                "total_known_after": after_count,
                "total_learned": len(self._learned_phrases),
                "ingestion_count": self._ingestion_count,
                "persisted": should_persist,
                "source": source,
            }
            logger.info(
                "Enrichment ingest: %d texts → %d new phrases (total known: %d)",
                len(texts), new_discoveries, after_count,
            )
            return summary

    def _infer_label(self, phrase: str) -> Optional[str]:
        """
        Attempt to infer a label for a newly discovered phrase by checking
        if it overlaps with known labeled terms or abbreviation expansions.
        """
        lower = phrase.lower()
        # Check if any seed phrase is a substring
        for seed, label in self.SEED_PHRASES.items():
            if seed in lower or lower in seed:
                return label
        # Check abbreviation expansions
        words = lower.split()
        for w in words:
            expanded = self.ABBREVIATION_MAP.get(w.upper())
            if expanded and expanded in self.SEED_PHRASES:
                return self.SEED_PHRASES[expanded]
        return None

    def persist_learned_phrases(self) -> bool:
        """
        Write all learned phrases to L: drive so they survive restart.
        This is the WRITE-BACK that makes the system actually learn.
        """
        if not self._learned_phrases:
            logger.info("No learned phrases to persist")
            return True

        output = {
            "version": 2,
            "persisted_at": datetime.now().isoformat(),
            "total_ingestions": self._ingestion_count,
            "phrase_count": len(self._learned_phrases),
            "phrases": self._learned_phrases,
        }

        try:
            LEARNED_PHRASES_PATH.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write: write to temp then rename
            tmp_path = LEARNED_PHRASES_PATH.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            tmp_path.replace(LEARNED_PHRASES_PATH)
            self._last_persist_time = time.time()
            logger.info("Persisted %d learned phrases to %s", len(self._learned_phrases), LEARNED_PHRASES_PATH)
            return True
        except Exception as e:
            logger.error("Failed to persist learned phrases: %s", e)
            return False

    def ingest_interaction_files(self, since_hours: int = 24) -> Dict[str, Any]:
        """
        Bulk-ingest user interaction files from the interaction_logger output directory.
        Called by enrichment_watchdog or as a periodic cron-style task.

        Reads JSON files from L:/antigravity_version_ai_data_final/USER DATA/interactions/
        and feeds their text content through enrichment_ingest().
        """
        if not INTERACTION_DIR.exists():
            logger.warning("Interaction directory does not exist: %s", INTERACTION_DIR)
            return {"error": "interaction_dir_missing", "path": str(INTERACTION_DIR)}

        cutoff = time.time() - (since_hours * 3600)
        texts = []
        files_read = 0

        for date_dir in sorted(INTERACTION_DIR.iterdir()):
            if not date_dir.is_dir():
                continue
            for json_file in date_dir.glob("*.json"):
                try:
                    if json_file.stat().st_mtime < cutoff:
                        continue
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Extract text fields from interaction records
                    for text_key in ("body", "text", "query", "content", "resume_text", "search_query"):
                        if text_key in data and isinstance(data[text_key], str) and len(data[text_key]) > 20:
                            texts.append(data[text_key])
                    files_read += 1
                except Exception as e:
                    logger.debug("Skipping interaction file %s: %s", json_file, e)

        if not texts:
            return {"files_scanned": files_read, "texts_found": 0, "status": "no_new_text"}

        result = self.enrichment_ingest(texts, source="interaction_files")
        result["files_scanned"] = files_read
        return result

    def expand_abbreviations(self, text: str) -> str:
        """
        Expand known abbreviations in text for better phrase matching.
        "Experienced ML and NLP engineer" → "Experienced machine learning and natural language processing engineer"
        """
        words = text.split()
        expanded = []
        for word in words:
            clean = word.strip(".,;:!?()[]{}\"'")
            replacement = self.ABBREVIATION_MAP.get(clean)
            if replacement:
                expanded.append(word.replace(clean, replacement))
            else:
                expanded.append(word)
        return " ".join(expanded)

    def get_learning_stats(self) -> Dict[str, Any]:
        """Return statistics about the engine's learning state."""
        label_counts: Dict[str, int] = Counter()
        method_counts: Dict[str, int] = Counter()
        for meta in self._learned_phrases.values():
            label = meta.get("label") or "UNLABELED"
            label_counts[label] += 1
            method_counts[meta.get("method", "unknown")] += 1

        return {
            "seed_phrase_count": len(self.SEED_PHRASES),
            "learned_phrase_count": len(self._learned_phrases),
            "total_known_phrases": len(self.known_phrases),
            "gazetteer_categories": len(self.gazetteers),
            "gazetteer_breakdown": {k: len(v) for k, v in self.gazetteers.items()},
            "ingestion_count": self._ingestion_count,
            "learned_by_label": dict(label_counts),
            "learned_by_method": dict(method_counts),
            "persistence_path": str(LEARNED_PHRASES_PATH),
            "gazetteers_dir": str(GAZETTEERS_DIR),
            "last_persist": datetime.fromtimestamp(self._last_persist_time).isoformat()
            if self._last_persist_time > 0 else "never",
        }

    # ── 9. Runtime Phrase Management (API for user-login enrichment) ─────

    def add_runtime_phrases(self, phrases: Dict[str, str], source: str = "api") -> Dict[str, Any]:
        """
        Add new phrases to the engine at runtime (e.g. from user login data,
        admin uploads, or discovered terms). These are persisted to disk.

        Args:
            phrases: {"new multi word term": "LABEL", "another term": "TECH_SKILL"}
            source: identifier for where the phrases came from

        Returns:
            Summary of what was added
        """
        with self._lock:
            added = 0
            now = datetime.now().isoformat()
            for phrase, label in phrases.items():
                key = phrase.lower()
                if key not in self.known_phrases:
                    self.known_phrases.add(key)
                    self.gazetteers.setdefault(label, []).append(phrase)
                    self._learned_phrases[key] = {
                        "label": label,
                        "score": 10.0,  # manually added = high confidence
                        "method": "manual",
                        "frequency": 1,
                        "discovered_at": now,
                        "source": source,
                    }
                    added += 1

            # Force PhraseMatcher / EntityRuler rebuild on next NLP call
            if added > 0:
                self._nlp = None
                self._phrase_matcher = None

            logger.info("add_runtime_phrases: added %d new phrases from %s", added, source)
            return {
                "added": added,
                "total_known": len(self.known_phrases),
                "source": source,
            }

    def on_user_login(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called when a user logs in — extracts text from their profile,
        recent searches, and CV snippets to discover new collocations.

        This is the primary hook for the learning loop from the user app.

        Args:
            user_data: dict with optional keys:
                - "skills": list of skills strings
                - "job_title": current or desired job title
                - "industry": industry keywords
                - "recent_searches": list of search query strings
                - "cv_text": raw CV/resume text
                - "bio": profile biography text

        Returns:
            Summary of enrichment results
        """
        texts = []

        # Collect all text fragments from user data
        for key in ("cv_text", "bio", "cover_letter"):
            if key in user_data and isinstance(user_data[key], str) and len(user_data[key]) > 20:
                texts.append(user_data[key])

        # Skills as a joined text block (for n-gram discovery across skill boundaries)
        skills = user_data.get("skills", [])
        if isinstance(skills, list) and skills:
            texts.append(" ".join(str(s) for s in skills))
            # Also directly add multi-word skills as known phrases
            new_phrases = {}
            for skill in skills:
                if isinstance(skill, str) and " " in skill and len(skill) > 3:
                    new_phrases[skill] = self._infer_label(skill) or "USER_SKILL"
            if new_phrases:
                self.add_runtime_phrases(new_phrases, source="user_login_skills")

        # Job title as known phrase
        job_title = user_data.get("job_title", "")
        if isinstance(job_title, str) and " " in job_title and len(job_title) > 3:
            self.add_runtime_phrases({job_title: "JOB_TITLE"}, source="user_login_title")

        # Recent searches
        searches = user_data.get("recent_searches", [])
        if isinstance(searches, list):
            texts.extend(str(s) for s in searches if isinstance(s, str) and len(str(s)) > 5)

        if not texts:
            return {"status": "no_text_found", "user_data_keys": list(user_data.keys())}

        result = self.enrichment_ingest(texts, source="user_login")
        return result

    def sync_gazetteers_to_local(self) -> Dict[str, Any]:
        """
        Sync gazetteers from L: drive source-of-truth to local project data folder.
        Used for Docker/production environments where L: isn't mounted.
        """
        if not GAZETTEERS_DIR.exists():
            return {"error": "source gazetteers dir does not exist", "path": str(GAZETTEERS_DIR)}

        LOCAL_GAZETTEERS_DIR.mkdir(parents=True, exist_ok=True)
        synced = 0
        for gaz_file in GAZETTEERS_DIR.glob("*.json"):
            try:
                dest = LOCAL_GAZETTEERS_DIR / gaz_file.name
                with open(gaz_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(dest, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                synced += 1
            except Exception as e:
                logger.warning("Failed to sync %s: %s", gaz_file.name, e)

        # Also sync the README
        readme_src = GAZETTEERS_DIR / "README.md"
        if readme_src.exists():
            import shutil
            shutil.copy2(readme_src, LOCAL_GAZETTEERS_DIR / "README.md")

        logger.info("Synced %d gazetteer files to %s", synced, LOCAL_GAZETTEERS_DIR)
        return {"synced": synced, "destination": str(LOCAL_GAZETTEERS_DIR)}


# ── Module-level singleton ───────────────────────────────────────────────
# Auto-loads seed gazetteers + any previously learned phrases from L: drive.
collocation_engine = CollocationEngine()
