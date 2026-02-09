"""
=============================================================================
IntelliCV Unified AI Engine - Production Ready Intelligence System
=============================================================================

Combines ALL AI techniques into a single, cohesive engine:
- Bayesian Inference Engine for pattern recognition and probability analysis
- Advanced NLP Engine for semantic understanding and context analysis
- LLM Integration Engine for content enhancement and generation
- Fuzzy Logic Engine for handling uncertain and ambiguous data
- AI Learning Table with configurable thresholds
- Feedback Loop System for continuous improvement

This engine replaces the scattered AI functionality across pages 08 and 09,
providing a unified, production-ready AI system for the parser page 06.

Author: IntelliCV AI Integration Team
Purpose: Production-ready AI with real algorithms and learning capabilities
Environment: IntelliCV\env310 with full AI/ML stack
"""

import numpy as np
import pandas as pd
import json
import sqlite3
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging

# AI/ML Imports - Real implementations
try:
    from sklearn.naive_bayes import GaussianNB, MultinomialNB
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, confidence_interval
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import spacy
    from spacy import displacy
    from spacy.matcher import Matcher
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

try:
    import openai
    from transformers import pipeline, AutoTokenizer, AutoModel
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_BERT_AVAILABLE = True
except ImportError:
    SENTENCE_BERT_AVAILABLE = False

# =============================================================================
# AI LEARNING TABLE SYSTEM
# =============================================================================

@dataclass
class LearningEntry:
    """Single entry in the AI learning table"""
    term: str
    category: str
    count: int
    confidence: float
    contexts: List[str]
    last_seen: datetime
    verified: bool = False
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return {
            'term': self.term,
            'category': self.category,
            'count': self.count,
            'confidence': self.confidence,
            'contexts': self.contexts,
            'last_seen': self.last_seen.isoformat(),
            'verified': self.verified,
            'metadata': self.metadata or {}
        }

class AILearningTable:
    """
    Intelligent learning table with configurable thresholds for different data types.

    Thresholds:
    - Words: 5+ occurrences to learn (common words need validation)
    - Abbreviations: 3+ occurrences (less common, context-specific)
    - Terminology: 0 threshold (learn immediately - specialized knowledge)
    - Job Titles: 2+ occurrences (validate role legitimacy)
    - Industries: 1+ occurrence (broad categories, learn quickly)
    """

    def __init__(self, db_path: str = "ai_learning_table.db"):
        self.db_path = db_path
        self.thresholds = {
            'words': 5,           # Common words - need validation
            'abbreviations': 3,   # Context-specific - moderate threshold
            'terminology': 0,     # Specialized knowledge - learn immediately
            'job_titles': 2,      # Role validation - low threshold
            'industries': 1,      # Broad categories - learn quickly
            'companies': 2,       # Company validation - moderate threshold
            'skills': 2,          # Skill validation - moderate threshold
            'locations': 1        # Geographic data - learn quickly
        }
        self.learning_entries = defaultdict(dict)
        self._initialize_db()
        self._load_learning_data()

    def _initialize_db(self):
        """Initialize SQLite database for persistent learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                category TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.0,
                contexts TEXT,  -- JSON array
                last_seen TEXT,
                verified BOOLEAN DEFAULT FALSE,
                metadata TEXT,  -- JSON object
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(term, category)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_term ON learning_entries(term)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON learning_entries(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_count ON learning_entries(count)')

        conn.commit()
        conn.close()

    def _load_learning_data(self):
        """Load existing learning data from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM learning_entries')
        rows = cursor.fetchall()

        for row in rows:
            term = row[1]
            category = row[2]
            entry = LearningEntry(
                term=term,
                category=category,
                count=row[3],
                confidence=row[4],
                contexts=json.loads(row[5]) if row[5] else [],
                last_seen=datetime.fromisoformat(row[6]),
                verified=bool(row[7]),
                metadata=json.loads(row[8]) if row[8] else {}
            )
            self.learning_entries[category][term] = entry

        conn.close()
        logging.info(f"Loaded {len(rows)} learning entries from database")

    def add_term(self, term: str, category: str, context: str = "",
                 confidence: float = 0.5, metadata: Dict = None) -> bool:
        """
        Add or update a term in the learning table.
        Returns True if term should be learned (meets threshold).
        """
        term = term.strip().lower()
        if not term or len(term) < 2:
            return False

        # Get or create entry
        if term in self.learning_entries[category]:
            entry = self.learning_entries[category][term]
            entry.count += 1
            entry.last_seen = datetime.now()
            if context and context not in entry.contexts:
                entry.contexts.append(context)
            # Update confidence based on repeated occurrences
            entry.confidence = min(1.0, entry.confidence + 0.1)
        else:
            entry = LearningEntry(
                term=term,
                category=category,
                count=1,
                confidence=confidence,
                contexts=[context] if context else [],
                last_seen=datetime.now(),
                metadata=metadata or {}
            )
            self.learning_entries[category][term] = entry

        # Check if term meets learning threshold
        threshold = self.thresholds.get(category, 1)
        should_learn = entry.count >= threshold

        # Save to database
        self._save_entry(entry)

        return should_learn

    def _save_entry(self, entry: LearningEntry):
        """Save entry to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO learning_entries
            (term, category, count, confidence, contexts, last_seen, verified, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.term,
            entry.category,
            entry.count,
            entry.confidence,
            json.dumps(entry.contexts),
            entry.last_seen.isoformat(),
            entry.verified,
            json.dumps(entry.metadata)
        ))

        conn.commit()
        conn.close()

    def get_learned_terms(self, category: str = None) -> Dict[str, LearningEntry]:
        """Get all terms that meet the learning threshold"""
        learned = {}

        categories = [category] if category else self.learning_entries.keys()

        for cat in categories:
            threshold = self.thresholds.get(cat, 1)
            for term, entry in self.learning_entries[cat].items():
                if entry.count >= threshold:
                    learned[f"{cat}:{term}"] = entry

        return learned

    def get_stats(self) -> Dict[str, Any]:
        """Get learning table statistics"""
        stats = {
            'total_entries': 0,
            'learned_entries': 0,
            'categories': {}
        }

        for category, entries in self.learning_entries.items():
            threshold = self.thresholds.get(category, 1)
            learned_count = sum(1 for entry in entries.values() if entry.count >= threshold)

            stats['categories'][category] = {
                'total': len(entries),
                'learned': learned_count,
                'threshold': threshold
            }
            stats['total_entries'] += len(entries)
            stats['learned_entries'] += learned_count

        return stats

# =============================================================================
# BAYESIAN INFERENCE ENGINE
# =============================================================================

class BayesianInferenceEngine:
    """
    Real Bayesian inference engine for pattern recognition and probability analysis.
    Uses Naive Bayes for classification and probability estimation.
    """

    def __init__(self):
        self.models = {
            'job_classification': None,
            'skill_prediction': None,
            'industry_matching': None,
            'experience_estimation': None
        }
        self.vectorizers = {}
        self.label_encoders = {}
        self.training_data = {}
        self.is_trained = False

        # Load trained models if available
        models_dir = Path(__file__).parent.parent / "models"
        bayesian_file = models_dir / "bayesian_classifier.pkl"
        vectorizer_file = models_dir / "tfidf_vectorizer.pkl"

        if bayesian_file.exists() and vectorizer_file.exists():
            import pickle
            try:
                self.models['job_classification'] = pickle.load(open(bayesian_file, 'rb'))
                self.vectorizers['job_classification'] = pickle.load(open(vectorizer_file, 'rb'))
                self.is_trained = True
                logging.info("✅ Loaded trained Bayesian models")
            except Exception as e:
                logging.warning(f"Failed to load trained models: {e}")
                self.is_trained = False
        else:
            logging.info("ℹ️  No trained models found, using fallback mode")

    def train_models(self, training_data: Dict[str, pd.DataFrame]):
        """Train Bayesian models on provided data"""
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("Scikit-learn is required for Bayesian models; fallback training is disabled")

        self.training_data = training_data

        # Train job classification model
        if 'job_data' in training_data:
            self._train_job_classifier(training_data['job_data'])

        # Train skill prediction model
        if 'skill_data' in training_data:
            self._train_skill_predictor(training_data['skill_data'])

        # Train industry matching model
        if 'industry_data' in training_data:
            self._train_industry_matcher(training_data['industry_data'])

        self.is_trained = True
        logging.info("Bayesian models trained successfully")

    def _train_job_classifier(self, job_data: pd.DataFrame):
        """Train job title classification model"""
        if 'job_title' not in job_data.columns or 'category' not in job_data.columns:
            return

        # Vectorize job titles
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        X = vectorizer.fit_transform(job_data['job_title'])

        # Encode labels
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(job_data['category'])

        # Train model
        model = MultinomialNB()
        model.fit(X, y)

        self.models['job_classification'] = model
        self.vectorizers['job_classification'] = vectorizer
        self.label_encoders['job_classification'] = label_encoder

    def predict_job_category(self, job_title: str) -> Tuple[str, float]:
        """Predict job category with confidence"""
        if not self.models['job_classification']:
            return "unknown", 0.0

        try:
            # Vectorize input
            X = self.vectorizers['job_classification'].transform([job_title])

            # Get prediction and probability
            prediction = self.models['job_classification'].predict(X)[0]
            probabilities = self.models['job_classification'].predict_proba(X)[0]
            confidence = max(probabilities)

            # Decode label
            category = self.label_encoders['job_classification'].inverse_transform([prediction])[0]

            return category, confidence

        except Exception as e:
            logging.error(f"Job classification error: {e}")
            return "unknown", 0.0

    def calculate_skill_match_probability(self, candidate_skills: List[str],
                                        job_requirements: List[str]) -> float:
        """Calculate probability of skill match using Bayesian analysis"""
        if not candidate_skills or not job_requirements:
            return 0.0

        # Convert to sets for easier comparison
        candidate_set = set(skill.lower().strip() for skill in candidate_skills)
        requirement_set = set(req.lower().strip() for req in job_requirements)

        # Calculate overlap
        matches = len(candidate_set.intersection(requirement_set))
        total_requirements = len(requirement_set)

        if total_requirements == 0:
            return 0.0

        # Basic probability calculation
        base_probability = matches / total_requirements

        # Apply Bayesian prior (assume some baseline matching probability)
        prior = 0.3  # 30% baseline match probability
        likelihood = base_probability

        # Simple Bayesian update
        posterior = (likelihood * prior) / ((likelihood * prior) + ((1 - likelihood) * (1 - prior)))

        return min(1.0, posterior * 1.2)  # Slight boost for good matches

    def _train_fallback(self, training_data: Dict[str, pd.DataFrame]):
        raise RuntimeError("Fallback Bayesian training is disabled")

# =============================================================================
# ADVANCED NLP ENGINE
# =============================================================================

class AdvancedNLPEngine:
    """
    Advanced NLP engine using spaCy for semantic understanding and entity recognition.
    Handles multi-language support, entity extraction, and context analysis.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self.nlp = None
        self.matchers = {}
        self.entity_patterns = {}
        self.is_loaded = False

        self._initialize_nlp()

    def _initialize_nlp(self):
        """Initialize spaCy NLP model"""
        if not SPACY_AVAILABLE:
            self.is_loaded = False
            self.load_error = "spaCy is required for NLP; fallback NLP is disabled"
            return

        try:
            self.nlp = spacy.load(self.model_name)
            self._setup_custom_patterns()
            self.is_loaded = True
            self.load_error = None
            logging.info(f"NLP model {self.model_name} loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load NLP model: {e}")
            self.is_loaded = False
            self.load_error = f"Failed to load spaCy model: {e}"

    def _setup_custom_patterns(self):
        """Setup custom entity patterns for CV parsing"""
        if not self.nlp:
            return

        # Create matcher for custom patterns
        matcher = Matcher(self.nlp.vocab)

        # Email patterns
        email_pattern = [{"LIKE_EMAIL": True}]
        matcher.add("EMAIL", [email_pattern])

        # Phone patterns
        phone_pattern = [
            {"TEXT": {"REGEX": r"^\+?[\d\s\-\(\)]{10,}$"}},
        ]
        matcher.add("PHONE", [phone_pattern])

        # Skill patterns (programming languages)
        skills_patterns = [
            [{"LOWER": "python"}],
            [{"LOWER": "java"}],
            [{"LOWER": "javascript"}],
            [{"LOWER": "react"}],
            [{"LOWER": "node.js"}],
            [{"LOWER": "sql"}],
            [{"LOWER": "machine"}, {"LOWER": "learning"}],
            [{"LOWER": "deep"}, {"LOWER": "learning"}],
        ]

        for pattern in skills_patterns:
            matcher.add("SKILL", [pattern])

        self.matchers['general'] = matcher

    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """Extract entities from text using NLP"""
        if not self.is_loaded:
            raise RuntimeError(self.load_error or "NLP engine unavailable")

        doc = self.nlp(text)
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'emails': [],
            'phones': [],
            'skills': [],
            'dates': [],
            'other': []
        }

        # Standard spaCy entities
        for ent in doc.ents:
            entity_data = {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 0.8  # spaCy doesn't provide confidence scores directly
            }

            if ent.label_ in ['PERSON']:
                entities['persons'].append(entity_data)
            elif ent.label_ in ['ORG']:
                entities['organizations'].append(entity_data)
            elif ent.label_ in ['GPE', 'LOC']:
                entities['locations'].append(entity_data)
            elif ent.label_ in ['DATE']:
                entities['dates'].append(entity_data)
            else:
                entities['other'].append(entity_data)

        # Custom pattern matches
        if 'general' in self.matchers:
            matches = self.matchers['general'](doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                label = self.nlp.vocab.strings[match_id]

                entity_data = {
                    'text': span.text,
                    'label': label,
                    'start': span.start_char,
                    'end': span.end_char,
                    'confidence': 0.9  # Higher confidence for pattern matches
                }

                if label == 'EMAIL':
                    entities['emails'].append(entity_data)
                elif label == 'PHONE':
                    entities['phones'].append(entity_data)
                elif label == 'SKILL':
                    entities['skills'].append(entity_data)

        return entities

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment for career satisfaction and cultural fit"""
        if not self.is_loaded:
            raise RuntimeError(self.load_error or "NLP engine unavailable")

        doc = self.nlp(text)

        # Simple sentiment analysis based on keywords
        positive_words = ['excellent', 'great', 'amazing', 'successful', 'achieved',
                         'improved', 'optimized', 'enhanced', 'led', 'managed']
        negative_words = ['failed', 'poor', 'difficult', 'challenging', 'problems',
                         'issues', 'struggled', 'declined', 'reduced']

        positive_count = 0
        negative_count = 0
        total_words = len([token for token in doc if not token.is_stop and not token.is_punct])

        for token in doc:
            if token.lemma_.lower() in positive_words:
                positive_count += 1
            elif token.lemma_.lower() in negative_words:
                negative_count += 1

        if total_words == 0:
            return {'polarity': 0.0, 'subjectivity': 0.0, 'confidence': 0.0}

        # Calculate polarity (-1 to 1)
        polarity = (positive_count - negative_count) / total_words
        polarity = max(-1.0, min(1.0, polarity * 10))  # Scale and clamp

        # Calculate subjectivity (0 to 1)
        subjective_words = positive_count + negative_count
        subjectivity = min(1.0, subjective_words / total_words * 5)

        # Calculate confidence based on word count and subjectivity
        confidence = min(1.0, (subjective_words / 10) + (total_words / 100))

        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'confidence': confidence
        }

    def _fallback_entity_extraction(self, text: str) -> Dict[str, List[Dict]]:
        raise RuntimeError("Entity extraction fallback is disabled")

# =============================================================================
# NEURAL NETWORK ENGINE (Sentence-BERT)
# =============================================================================

class NeuralNetworkEngine:
    """
    Neural Network engine using Sentence-BERT for semantic embeddings.
    Handles semantic similarity, clustering, and deep learning features.
    """

    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.model_name = 'all-MiniLM-L6-v2'

        self._initialize_model()

    def _initialize_model(self):
        """Initialize Sentence-BERT model"""
        if not SENTENCE_BERT_AVAILABLE:
            self.is_loaded = False
            return

        try:
            # Load local model if available, otherwise download
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True
            logging.info(f"Neural Network (Sentence-BERT) loaded: {self.model_name}")
        except Exception as e:
            logging.error(f"Failed to load Neural Network: {e}")
            self.is_loaded = False

    def get_embedding(self, text: str) -> np.ndarray:
        """Generate semantic embedding for text"""
        if not self.is_loaded:
            return np.zeros(384)  # Return zero vector of correct dimension

        try:
            return self.model.encode(text)
        except Exception as e:
            logging.error(f"Embedding generation failed: {e}")
            return np.zeros(384)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        if not self.is_loaded:
            return 0.0

        try:
            emb1 = self.model.encode(text1)
            emb2 = self.model.encode(text2)

            # Cosine similarity
            return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        except Exception as e:
            logging.error(f"Similarity calculation failed: {e}")
            return 0.0

# =============================================================================
# FUZZY LOGIC ENGINE
# =============================================================================

class FuzzyLogicEngine:
    """
    Fuzzy logic engine for handling uncertain and ambiguous data.
    Uses fuzzy sets and rules to make decisions with partial information.
    """

    def __init__(self):
        self.fuzzy_systems = {}
        self.is_initialized = False

        if FUZZY_AVAILABLE:
            self._initialize_fuzzy_systems()
        else:
            self.is_initialized = False
            self.init_error = "scikit-fuzzy is required; fallback fuzzy logic is disabled"

    def _initialize_fuzzy_systems(self):
        """Initialize fuzzy control systems"""
        try:
            # Data Quality Assessment System
            self._create_data_quality_system()

            # Candidate Matching System
            self._create_candidate_matching_system()

            self.is_initialized = True
            logging.info("Fuzzy logic systems initialized")

        except Exception as e:
            logging.error(f"Failed to initialize fuzzy systems: {e}")
            self.is_initialized = False

    def _create_data_quality_system(self):
        """Create fuzzy system for data quality assessment"""
        if not FUZZY_AVAILABLE:
            return

        # Input variables
        completeness = ctrl.Antecedent(np.arange(0, 101, 1), 'completeness')
        accuracy = ctrl.Antecedent(np.arange(0, 101, 1), 'accuracy')
        consistency = ctrl.Antecedent(np.arange(0, 101, 1), 'consistency')

        # Output variable
        quality = ctrl.Consequent(np.arange(0, 101, 1), 'quality')

        # Membership functions
        completeness['low'] = fuzz.trimf(completeness.universe, [0, 0, 40])
        completeness['medium'] = fuzz.trimf(completeness.universe, [20, 50, 80])
        completeness['high'] = fuzz.trimf(completeness.universe, [60, 100, 100])

        accuracy['low'] = fuzz.trimf(accuracy.universe, [0, 0, 40])
        accuracy['medium'] = fuzz.trimf(accuracy.universe, [20, 50, 80])
        accuracy['high'] = fuzz.trimf(accuracy.universe, [60, 100, 100])

        consistency['low'] = fuzz.trimf(consistency.universe, [0, 0, 40])
        consistency['medium'] = fuzz.trimf(consistency.universe, [20, 50, 80])
        consistency['high'] = fuzz.trimf(consistency.universe, [60, 100, 100])

        quality['poor'] = fuzz.trimf(quality.universe, [0, 0, 30])
        quality['fair'] = fuzz.trimf(quality.universe, [10, 40, 70])
        quality['good'] = fuzz.trimf(quality.universe, [50, 75, 100])
        quality['excellent'] = fuzz.trimf(quality.universe, [75, 100, 100])

        # Rules
        rules = [
            ctrl.Rule(completeness['high'] & accuracy['high'] & consistency['high'], quality['excellent']),
            ctrl.Rule(completeness['high'] & accuracy['high'] & consistency['medium'], quality['good']),
            ctrl.Rule(completeness['medium'] & accuracy['high'] & consistency['high'], quality['good']),
            ctrl.Rule(completeness['low'] | accuracy['low'] | consistency['low'], quality['poor']),
            ctrl.Rule(completeness['medium'] & accuracy['medium'] & consistency['medium'], quality['fair'])
        ]

        # Control system
        quality_ctrl = ctrl.ControlSystem(rules)
        self.fuzzy_systems['data_quality'] = ctrl.ControlSystemSimulation(quality_ctrl)

    def assess_data_quality(self, completeness: float, accuracy: float, consistency: float) -> Dict[str, float]:
        """Assess data quality using fuzzy logic"""
        if not self.is_initialized or 'data_quality' not in self.fuzzy_systems:
            return {
                'score': 0.0,
                'level': 'unavailable',
                'confidence': 0.0,
                'error': getattr(self, 'init_error', 'Fuzzy engine unavailable')
            }

        try:
            # Set inputs
            system = self.fuzzy_systems['data_quality']
            system.input['completeness'] = completeness * 100
            system.input['accuracy'] = accuracy * 100
            system.input['consistency'] = consistency * 100

            # Compute result
            system.compute()

            quality_score = system.output['quality'] / 100

            # Determine quality level
            if quality_score >= 0.75:
                level = "excellent"
            elif quality_score >= 0.50:
                level = "good"
            elif quality_score >= 0.30:
                level = "fair"
            else:
                level = "poor"

            return {
                'score': quality_score,
                'level': level,
                'confidence': min(1.0, (completeness + accuracy + consistency) / 3 + 0.2)
            }

        except Exception as e:
            logging.error(f"Fuzzy data quality assessment error: {e}")
            return {
                'score': 0.0,
                'level': 'error',
                'confidence': 0.0,
                'error': str(e)
            }

    def _fallback_data_quality(self, completeness: float, accuracy: float, consistency: float) -> Dict[str, float]:
        raise RuntimeError("Fallback data quality assessment is disabled")

    def handle_ambiguous_data(self, data_value: str, possible_interpretations: List[str]) -> Dict[str, Any]:
        """Handle ambiguous data using fuzzy matching"""
        if not data_value or not possible_interpretations:
            return {'best_match': None, 'confidence': 0.0, 'alternatives': []}

        # Calculate fuzzy string similarity
        similarities = []

        for interpretation in possible_interpretations:
            similarity = self._fuzzy_string_match(data_value, interpretation)
            similarities.append({
                'interpretation': interpretation,
                'similarity': similarity
            })

        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        best_match = similarities[0] if similarities else None

        return {
            'best_match': best_match['interpretation'] if best_match else None,
            'confidence': best_match['similarity'] if best_match else 0.0,
            'alternatives': similarities[1:4]  # Top 3 alternatives
        }

    def _fuzzy_string_match(self, s1: str, s2: str) -> float:
        """Calculate fuzzy string similarity (Levenshtein-based)"""
        if not s1 or not s2:
            return 0.0

        s1, s2 = s1.lower().strip(), s2.lower().strip()

        if s1 == s2:
            return 1.0

        # Simple character-based similarity
        len1, len2 = len(s1), len(s2)
        max_len = max(len1, len2)

        if max_len == 0:
            return 1.0

        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(s1, s2))

        # Basic similarity calculation
        similarity = matches / max_len

        # Bonus for substring matches
        if s1 in s2 or s2 in s1:
            similarity += 0.2

        return min(1.0, similarity)

# =============================================================================
# LLM INTEGRATION ENGINE
# =============================================================================

class LLMIntegrationEngine:
    """
    LLM integration engine for content enhancement and generation.
    Supports OpenAI GPT models and local transformer models.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.openai_client = None
        self.local_models = {}
        self.is_initialized = False

        self._initialize_llm()

    def _initialize_llm(self):
        """Initialize LLM connections"""
        # Initialize OpenAI if API key available
        if self.api_key and LLM_AVAILABLE:
            try:
                openai.api_key = self.api_key
                self.openai_client = openai
                self.is_initialized = True
                logging.info("OpenAI client initialized")
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI: {e}")

        # Local transformer and template-based fallbacks are intentionally disabled
        # to comply with the no-fabrication policy.
        self.local_models = {}

        if not self.is_initialized:
            logging.warning("No LLM services available - LLM generation is unavailable")

    def _load_local_models(self):
        """Load local transformer models"""
        raise RuntimeError("Local transformer models are disabled (no fabricated generation).")

    def enhance_job_description(self, basic_description: str, target_industry: str = None) -> str:
        """Enhance basic job description with AI-generated content"""
        if self.openai_client:
            return self._openai_enhance_description(basic_description, target_industry)
        raise RuntimeError("LLM enhancement unavailable: configure an OpenAI API key")

    def _openai_enhance_description(self, description: str, industry: str) -> str:
        """Enhance description using OpenAI"""
        try:
            prompt = f"""
            Enhance this job responsibility into a professional, achievement-focused bullet point:

            Original: {description}
            Industry: {industry or 'General'}

            Requirements:
            - Use strong action verbs
            - Include quantifiable metrics where possible
            - Focus on impact and results
            - Keep professional tone
            - Maximum 2 lines

            Enhanced version:
            """

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logging.error(f"OpenAI enhancement error: {e}")
            raise

    def _local_enhance_description(self, description: str, industry: str) -> str:
        """Enhance description using local models"""
        raise RuntimeError("Local model enhancement is disabled (no fabricated generation).")

    def _fallback_enhance_description(self, description: str, industry: str) -> str:
        """Fallback enhancement using templates"""
        raise RuntimeError("Template fallback enhancement is disabled (no fabricated generation).")

    def generate_professional_summary(self, profile_data: Dict[str, Any]) -> str:
        """Generate professional summary from profile data"""
        experience = profile_data.get('years_experience', 'several years')
        skills = profile_data.get('skills', [])
        industry = profile_data.get('industry', 'professional')

        if self.openai_client:
            return self._openai_generate_summary(experience, skills, industry)
        raise RuntimeError("LLM summary generation unavailable: configure an OpenAI API key")

    def _openai_generate_summary(self, experience: str, skills: List[str], industry: str) -> str:
        """Generate summary using OpenAI"""
        try:
            skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
            prompt = f"""
            Write a professional resume summary for a {industry} professional.
            Experience: {experience}
            Key Skills: {skills_str}

            Requirements:
            - Professional and impactful tone
            - Highlight key achievements implied by experience
            - Maximum 3-4 sentences
            """

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI summary generation error: {e}")
            raise

    def generate_star_bullets(self, basic_description: str, target_industry: str, role_level: str) -> str:
        """Generate STAR method bullet points"""
        if not self.openai_client:
            raise RuntimeError("LLM generation unavailable: configure an OpenAI API key")

        try:
            prompt = f"""
            Convert this job description into STAR method bullet points (Situation, Task, Action, Result).

            Role Level: {role_level}
            Industry: {target_industry}
            Description: {basic_description}

            Requirements:
            - Start with strong action verbs
            - Quantify results where possible
            - Professional tone
            """

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI STAR generation error: {e}")
            raise

    def optimize_ats(self, content: str, target_role: str, keywords: List[str] = None) -> str:
        """Optimize content for ATS systems"""
        if not self.openai_client:
            raise RuntimeError("LLM generation unavailable: configure an OpenAI API key")

        try:
            keywords_str = ", ".join(keywords) if keywords else "relevant industry keywords"
            prompt = f"""
            Optimize this resume content for ATS (Applicant Tracking Systems).

            Target Role: {target_role}
            Keywords to include: {keywords_str}
            Content: {content}

            Requirements:
            - Naturally integrate keywords
            - Maintain readability
            - Use standard formatting
            """

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI ATS optimization error: {e}")
            raise

    def generate_cover_letter(self, candidate_data: Dict, job_data: Dict) -> str:
        """Generate a tailored cover letter"""
        if not self.openai_client:
            raise RuntimeError("LLM generation unavailable: configure an OpenAI API key")

        try:
            prompt = f"""
            Write a professional cover letter.

            Candidate: {candidate_data.get('name', 'Candidate')}
            Skills: {candidate_data.get('skills', '')}
            Experience: {candidate_data.get('experience', '')}

            Target Company: {job_data.get('company', 'Hiring Manager')}
            Target Role: {job_data.get('role', 'Professional')}
            Job Description: {job_data.get('description', '')}

            Requirements:
            - Professional and persuasive tone
            - Connect skills to job requirements
            - Standard business letter format
            """

            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI cover letter generation error: {e}")
            raise

    def _fallback_generate_summary(self, experience: str, skills: List[str], industry: str) -> str:
        """Fallback summary generation"""
        raise RuntimeError("Fallback summary generation is disabled (no fabricated summaries).")

# =============================================================================
# UNIFIED AI ENGINE - MAIN CLASS
# =============================================================================

class UnifiedIntelliCVAIEngine:
    """
    Unified AI engine that combines all AI techniques into a single, cohesive system.
    This is the main class that orchestrates all AI engines and provides a unified interface.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Initialize all engines
        self.learning_table = AILearningTable(
            db_path=self.config.get('learning_db_path', 'ai_learning_table.db')
        )
        self.bayesian_engine = BayesianInferenceEngine()
        self.neural_engine = NeuralNetworkEngine()
        self.nlp_engine = AdvancedNLPEngine(
            model_name=self.config.get('nlp_model', 'en_core_web_sm')
        )
        self.fuzzy_engine = FuzzyLogicEngine()
        self.llm_engine = LLMIntegrationEngine(
            api_key=self.config.get('openai_api_key')
        )

        # Processing statistics
        self.stats = {
            'documents_processed': 0,
            'entities_extracted': 0,
            'terms_learned': 0,
            'confidence_scores': [],
            'processing_times': []
        }

        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.logger.info("Unified IntelliCV AI Engine initialized successfully")

    def process_document_intelligent(self, document_path: str, run_mode: str = "medium") -> Dict[str, Any]:
        """
        Intelligently process a document using all AI engines.

        Args:
            document_path: Path to document to process
            run_mode: Processing intensity ("short", "medium", "full")

        Returns:
            Complete analysis results with all AI insights
        """
        start_time = time.time()

        try:
            # Load document content
            content = self._load_document(document_path)
            if not content:
                return self._empty_result("Failed to load document content")

            results = {
                'document_path': document_path,
                'processing_mode': run_mode,
                'timestamp': datetime.now().isoformat(),
                'content_length': len(content),
                'ai_analysis': {}
            }

            # 1. NLP Analysis - Extract entities and analyze sentiment
            self.logger.info("Running NLP analysis...")
            nlp_results = self.nlp_engine.extract_entities(content)
            sentiment = self.nlp_engine.analyze_sentiment(content)

            results['ai_analysis']['nlp'] = {
                'entities': nlp_results,
                'sentiment': sentiment,
                'confidence': sentiment.get('confidence', 0.5)
            }

            # 2. Learn from extracted entities
            self.logger.info("Updating learning table...")
            learning_updates = self._update_learning_table(nlp_results, content)
            results['ai_analysis']['learning'] = learning_updates

            # 3. Bayesian Analysis - Pattern recognition and predictions
            if run_mode in ["medium", "full"]:
                self.logger.info("Running Bayesian analysis...")
                bayesian_results = self._run_bayesian_analysis(nlp_results, content)
                results['ai_analysis']['bayesian'] = bayesian_results

            # 4. Neural Network Analysis - Semantic understanding
            if run_mode in ["medium", "full"]:
                self.logger.info("Running Neural Network analysis...")
                neural_results = self._run_neural_analysis(nlp_results, content)
                results['ai_analysis']['neural'] = neural_results

            # 5. Fuzzy Logic - Data quality and ambiguity handling
            self.logger.info("Running fuzzy logic analysis...")
            fuzzy_results = self._run_fuzzy_analysis(nlp_results, content)
            results['ai_analysis']['fuzzy'] = fuzzy_results

            # 6. LLM Enhancement - Content improvement (full mode only)
            if run_mode == "full":
                self.logger.info("Running LLM enhancement...")
                llm_results = self._run_llm_enhancement(nlp_results, content)
                results['ai_analysis']['llm'] = llm_results

            # 6. Calculate overall confidence and quality scores
            overall_analysis = self._calculate_overall_scores(results['ai_analysis'])
            results['overall_analysis'] = overall_analysis

            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(results, processing_time)

            results['processing_time'] = processing_time
            results['status'] = 'success'

            self.logger.info(f"Document processed successfully in {processing_time:.2f}s")
            return results

        except Exception as e:
            self.logger.error(f"Document processing error: {e}")
            return self._empty_result(f"Processing error: {str(e)}")

    def _load_document(self, document_path: str) -> str:
        """Load document content from various formats"""
        try:
            path = Path(document_path)

            if path.suffix.lower() == '.txt':
                return path.read_text(encoding='utf-8')
            elif path.suffix.lower() == '.json':
                data = json.loads(path.read_text(encoding='utf-8'))
                return json.dumps(data, indent=2)
            else:
                # For other formats, return path info for now
                return f"Document: {path.name}\nSize: {path.stat().st_size} bytes"

        except Exception as e:
            self.logger.error(f"Failed to load document {document_path}: {e}")
            return ""

    def _update_learning_table(self, nlp_results: Dict, content: str) -> Dict[str, Any]:
        """Update learning table with new terms from NLP results"""
        updates = {
            'new_terms': 0,
            'updated_terms': 0,
            'categories_updated': []
        }

        # Learn from extracted entities
        for category, entities in nlp_results.items():
            for entity in entities:
                term = entity['text'].strip()
                confidence = entity.get('confidence', 0.5)

                # Map NLP categories to learning categories
                learning_category = self._map_nlp_to_learning_category(category)

                if learning_category:
                    learned = self.learning_table.add_term(
                        term=term,
                        category=learning_category,
                        context=content[:200],  # First 200 chars as context
                        confidence=confidence
                    )

                    if learned:
                        updates['new_terms'] += 1
                        if learning_category not in updates['categories_updated']:
                            updates['categories_updated'].append(learning_category)

        return updates

    def _map_nlp_to_learning_category(self, nlp_category: str) -> str:
        """Map NLP entity categories to learning table categories"""
        mapping = {
            'persons': 'persons',
            'organizations': 'companies',
            'locations': 'locations',
            'emails': 'contacts',
            'phones': 'contacts',
            'skills': 'skills',
            'dates': 'temporal',
            'other': 'terminology'
        }
        return mapping.get(nlp_category, 'terminology')

    def _run_bayesian_analysis(self, nlp_results: Dict, content: str) -> Dict[str, Any]:
        """Run Bayesian analysis on extracted data"""
        results = {
            'job_predictions': [],
            'skill_matches': [],
            'industry_classification': None,
            'confidence_scores': {}
        }

        # Job title prediction from organizations and skills
        organizations = [e['text'] for e in nlp_results.get('organizations', [])]
        skills = [e['text'] for e in nlp_results.get('skills', [])]

        if organizations:
            for org in organizations[:3]:  # Top 3 organizations
                job_category, confidence = self.bayesian_engine.predict_job_category(org)
                results['job_predictions'].append({
                    'organization': org,
                    'predicted_category': job_category,
                    'confidence': confidence
                })

        # Skill matching analysis
        if skills:
            # Example: match against common job requirements
            common_tech_skills = ['python', 'java', 'sql', 'react', 'machine learning']
            match_probability = self.bayesian_engine.calculate_skill_match_probability(
                skills, common_tech_skills
            )
            results['skill_matches'].append({
                'skill_set': 'technology',
                'match_probability': match_probability,
                'matched_skills': list(set(skills) & set(common_tech_skills))
            })

        return results

    def _run_neural_analysis(self, nlp_results: Dict, content: str) -> Dict[str, Any]:
        """Run Neural Network analysis (Semantic Embeddings)"""
        results = {
            'semantic_embedding': None,
            'similar_roles': [],
            'embedding_dim': 0
        }

        if not self.neural_engine.is_loaded:
            return results

        # Generate embedding for the full document content (truncated)
        # We use the first 1000 chars to capture the essence
        doc_embedding = self.neural_engine.get_embedding(content[:1000])

        results['semantic_embedding'] = doc_embedding.tolist() # Convert to list for JSON serialization
        results['embedding_dim'] = len(doc_embedding)

        # Example: Check similarity with key roles
        key_roles = ['Software Engineer', 'Data Scientist', 'Project Manager', 'Sales Executive']
        for role in key_roles:
            similarity = self.neural_engine.calculate_similarity(content[:500], role)
            if similarity > 0.3: # Threshold
                results['similar_roles'].append({
                    'role': role,
                    'similarity': float(similarity)
                })

        # Sort by similarity
        results['similar_roles'].sort(key=lambda x: x['similarity'], reverse=True)

        return results

    def _run_fuzzy_analysis(self, nlp_results: Dict, content: str) -> Dict[str, Any]:
        """Run fuzzy logic analysis for data quality and ambiguity"""
        results = {
            'data_quality': {},
            'ambiguous_terms': [],
            'quality_assessment': {}
        }

        # Calculate data completeness, accuracy, and consistency
        total_entities = sum(len(entities) for entities in nlp_results.values())
        content_length = len(content)

        # Completeness: ratio of entities to content length
        completeness = min(1.0, total_entities / max(1, content_length / 100))

        # Accuracy: based on confidence scores
        confidence_scores = [e.get('confidence', 0.5) for entities in nlp_results.values() for e in entities]
        accuracy = sum(confidence_scores) / max(1, len(confidence_scores))

        # Consistency: check for duplicate/similar entities
        all_entities = [e['text'].lower() for entities in nlp_results.values() for e in entities]
        unique_entities = len(set(all_entities))
        consistency = unique_entities / max(1, len(all_entities)) if all_entities else 1.0

        # Fuzzy data quality assessment
        quality_assessment = self.fuzzy_engine.assess_data_quality(
            completeness, accuracy, consistency
        )

        results['data_quality'] = {
            'completeness': completeness,
            'accuracy': accuracy,
            'consistency': consistency
        }
        results['quality_assessment'] = quality_assessment

        # Handle ambiguous terms (entities with low confidence)
        for category, entities in nlp_results.items():
            for entity in entities:
                if entity.get('confidence', 1.0) < 0.7:
                    # Get learned terms from the same category for disambiguation
                    learned_terms = self.learning_table.get_learned_terms(
                        self._map_nlp_to_learning_category(category)
                    )

                    if learned_terms:
                        possible_interpretations = [term.split(':')[1] for term in learned_terms.keys()][:5]
                        disambiguation = self.fuzzy_engine.handle_ambiguous_data(
                            entity['text'], possible_interpretations
                        )

                        results['ambiguous_terms'].append({
                            'original_term': entity['text'],
                            'category': category,
                            'disambiguation': disambiguation
                        })

        return results

    def _run_llm_enhancement(self, nlp_results: Dict, content: str) -> Dict[str, Any]:
        """Run LLM enhancement for content improvement"""
        results = {
            'enhanced_content': [],
            'professional_summary': None,
            'improvement_suggestions': []
        }

        # Extract key information for profile creation
        organizations = [e['text'] for e in nlp_results.get('organizations', [])]
        skills = [e['text'] for e in nlp_results.get('skills', [])]

        profile_data = {
            'years_experience': 'several years',  # Could be extracted from dates
            'skills': skills,
            'industry': 'technology',  # Could be inferred from organizations/skills
            'companies': organizations
        }

        # Generate professional summary
        if skills or organizations:
            summary = self.llm_engine.generate_professional_summary(profile_data)
            results['professional_summary'] = summary

        # Enhance job descriptions (example with first organization)
        if organizations:
            for org in organizations[:2]:  # Limit to 2 for performance
                enhanced = self.llm_engine.enhance_job_description(
                    f"Worked at {org}",
                    target_industry=profile_data['industry']
                )
                results['enhanced_content'].append({
                    'original': f"Worked at {org}",
                    'enhanced': enhanced
                })

        return results

    def _calculate_overall_scores(self, ai_analysis: Dict) -> Dict[str, Any]:
        """Calculate overall confidence and quality scores"""
        scores = {
            'overall_confidence': 0.0,
            'data_quality_score': 0.0,
            'completeness_score': 0.0,
            'intelligence_score': 0.0,
            'recommendations': []
        }

        confidence_scores = []

        # NLP confidence
        if 'nlp' in ai_analysis:
            nlp_confidence = ai_analysis['nlp'].get('confidence', 0.5)
            confidence_scores.append(nlp_confidence)

        # Bayesian confidence
        if 'bayesian' in ai_analysis:
            bayesian_results = ai_analysis['bayesian']
            if bayesian_results.get('job_predictions'):
                avg_confidence = sum(p['confidence'] for p in bayesian_results['job_predictions']) / len(bayesian_results['job_predictions'])
                confidence_scores.append(avg_confidence)

        # Fuzzy quality assessment
        if 'fuzzy' in ai_analysis:
            fuzzy_results = ai_analysis['fuzzy']
            quality_score = fuzzy_results.get('quality_assessment', {}).get('score', 0.5)
            scores['data_quality_score'] = quality_score
            confidence_scores.append(quality_score)

        # Overall confidence
        if confidence_scores:
            scores['overall_confidence'] = sum(confidence_scores) / len(confidence_scores)

        # Intelligence score (based on number of AI techniques successfully applied)
        applied_techniques = len([k for k in ai_analysis.keys() if ai_analysis[k]])
        scores['intelligence_score'] = min(1.0, applied_techniques / 4.0)  # 4 max techniques

        # Generate recommendations
        if scores['overall_confidence'] < 0.6:
            scores['recommendations'].append("Consider manual review due to low confidence scores")

        if scores['data_quality_score'] < 0.5:
            scores['recommendations'].append("Data quality is below acceptable threshold")

        if scores['intelligence_score'] > 0.8:
            scores['recommendations'].append("High AI intelligence score - results are highly reliable")

        return scores

    def _update_stats(self, results: Dict, processing_time: float):
        """Update processing statistics"""
        self.stats['documents_processed'] += 1
        self.stats['processing_times'].append(processing_time)

        # Count entities
        if 'ai_analysis' in results and 'nlp' in results['ai_analysis']:
            entities = results['ai_analysis']['nlp'].get('entities', {})
            entity_count = sum(len(entity_list) for entity_list in entities.values())
            self.stats['entities_extracted'] += entity_count

        # Count learned terms
        if 'ai_analysis' in results and 'learning' in results['ai_analysis']:
            self.stats['terms_learned'] += results['ai_analysis']['learning'].get('new_terms', 0)

        # Store confidence scores
        if 'overall_analysis' in results:
            confidence = results['overall_analysis'].get('overall_confidence', 0.0)
            self.stats['confidence_scores'].append(confidence)

    def _empty_result(self, error_message: str) -> Dict[str, Any]:
        """Return empty result structure for failed processing"""
        return {
            'document_path': None,
            'processing_mode': 'failed',
            'timestamp': datetime.now().isoformat(),
            'content_length': 0,
            'ai_analysis': {},
            'overall_analysis': {
                'overall_confidence': 0.0,
                'data_quality_score': 0.0,
                'intelligence_score': 0.0
            },
            'status': 'failed',
            'error': error_message,
            'processing_time': 0.0
        }

    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of all AI engines"""
        return {
            'learning_table': {
                'status': 'active',
                'stats': self.learning_table.get_stats()
            },
            'bayesian_engine': {
                'status': 'active' if self.bayesian_engine.is_trained else 'untrained',
                'sklearn_available': SKLEARN_AVAILABLE
            },
            'neural_engine': {
                'status': 'active' if self.neural_engine.is_loaded else 'unavailable',
                'model': self.neural_engine.model_name
            },
            'nlp_engine': {
                'status': 'active' if self.nlp_engine.is_loaded else 'unavailable',
                'spacy_available': SPACY_AVAILABLE,
                'model': self.nlp_engine.model_name
            },
            'fuzzy_engine': {
                'status': 'active' if self.fuzzy_engine.is_initialized else 'fallback',
                'scikit_fuzzy_available': FUZZY_AVAILABLE
            },
            'llm_engine': {
                'status': 'active' if self.llm_engine.is_initialized else 'fallback',
                'llm_available': LLM_AVAILABLE,
                'openai_configured': bool(self.llm_engine.api_key)
            },
            'overall_stats': self.stats
        }

    def export_learning_data(self, export_path: str) -> bool:
        """Export learning table data for backup or analysis"""
        try:
            learned_terms = self.learning_table.get_learned_terms()
            stats = self.learning_table.get_stats()

            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'learning_table_stats': stats,
                'learned_terms': {k: v.to_dict() for k, v in learned_terms.items()},
                'processing_stats': self.stats
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Learning data exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export learning data: {e}")
            return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Example usage and testing
    print("IntelliCV Unified AI Engine - Testing")

    # Initialize engine
    config = {
        'learning_db_path': 'test_learning.db',
        'nlp_model': 'en_core_web_sm',
        'openai_api_key': None  # Add your API key here for full functionality
    }

    engine = UnifiedIntelliCVAIEngine(config)

    # Test with sample document
    sample_content = """
    John Smith
    Software Engineer at Google
    Email: john.smith@gmail.com
    Phone: +1-555-123-4567

    Experience:
    - Developed Python applications for machine learning
    - Led team of 5 engineers in React development
    - Improved system performance by 40%

    Skills: Python, Java, React, SQL, Machine Learning
    """

    # Save sample content to test file
    test_file = "test_cv.txt"
    with open(test_file, 'w') as f:
        f.write(sample_content)

    # Process document
    print(f"\nProcessing test document: {test_file}")
    results = engine.process_document_intelligent(test_file, run_mode="full")

    # Display results
    print(f"\nProcessing Status: {results['status']}")
    print(f"Processing Time: {results.get('processing_time', 0):.2f}s")
    print(f"Overall Confidence: {results['overall_analysis']['overall_confidence']:.2f}")
    print(f"Data Quality Score: {results['overall_analysis']['data_quality_score']:.2f}")
    print(f"Intelligence Score: {results['overall_analysis']['intelligence_score']:.2f}")

    # Show engine status
    print("\n" + "="*50)
    print("AI Engine Status:")
    status = engine.get_engine_status()
    for engine_name, engine_status in status.items():
        if engine_name != 'overall_stats':
            print(f"  {engine_name}: {engine_status['status']}")

    # Export learning data
    engine.export_learning_data("learning_export.json")
    print(f"\nLearning data exported to learning_export.json")

    # Clean up test file
    Path(test_file).unlink(missing_ok=True)

    print("\nUnified AI Engine testing completed!")
