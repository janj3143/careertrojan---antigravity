"""
🔤 NLP & LLM Training Module
=============================
Trains all NLP and LLM models:
- Tokenization & Lemmatization
- Named Entity Recognition (NER)
- Sentiment Analysis (keyword-heuristic labels)
- Text Classification (real industry labels from schema adapter)
- Embedding Models (Word2Vec, BERT)
- GPT configuration
- Topic Modeling (LDA)

Data loading uses the unified schema adapter which normalises records
from all sources (cv_files, parsed_resumes, profiles, core_databases)
into a consistent format with: text, job_title, skills, experience_years,
education, industry, salary, source.
"""

import sys
import os
import logging
from pathlib import Path
import json
import numpy as np
from datetime import datetime

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

# ── Sentiment heuristic keyword sets ─────────────────────────────────────

_POSITIVE_KEYWORDS = {
    "experienced",
    "expert",
    "led",
    "managed",
    "achieved",
    "awarded",
    "successful",
    "proficient",
    "advanced",
    "accomplished",
    "improved",
    "exceeded",
    "delivered",
    "spearheaded",
    "recognised",
    "recognized",
    "promoted",
    "outstanding",
    "innovative",
    "strategic",
}

_NEGATIVE_KEYWORDS = {
    "unemployed",
    "terminated",
    "fired",
    "struggling",
    "gap",
    "redundant",
    "limited",
    "entry-level",
    "junior",
    "no experience",
    "unskilled",
}


def _score_sentiment(text: str) -> str:
    """
    Assign a sentiment label based on keyword heuristics.

    Positive keywords (experienced, expert, led, managed, achieved, awarded …)
    push the score up; negative keywords pull it down.  The net score
    determines the label:
        score > 0  → 'positive'
        score < 0  → 'negative'
        score == 0 → 'neutral'
    """
    text_lower = text.lower()
    pos = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text_lower)
    neg = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text_lower)
    score = pos - neg
    if score > 0:
        return "positive"
    elif score < 0:
        return "negative"
    return "neutral"


class NLPLLMTrainer:
    """Comprehensive NLP & LLM trainer using unified schema adapter data."""

    def __init__(self, base_path: str = None):
        # Use centralised config for data paths (L: drive source of truth)
        try:
            from services.ai_engine.config import AI_DATA_DIR, models_path as _cfg_models

            self.data_path = AI_DATA_DIR
            self.models_path = _cfg_models / "nlp"
        except ImportError:
            _data_root = Path(
                os.getenv(
                    "CAREERTROJAN_DATA_ROOT",
                    "./data",
                )
            )
            self.data_path = _data_root / "ai_data_final"
            self.models_path = (
                Path(base_path or Path(__file__).parent)
                / "trained_models"
                / "nlp"
            )
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.models_path.mkdir(parents=True, exist_ok=True)

        logger.info("NLP & LLM Trainer initialized")
        logger.info(f"Data path: {self.data_path}")
        logger.info(f"Models will be saved to: {self.models_path}")

    # ── Data loading ─────────────────────────────────────────────────────

    def load_text_data(self) -> dict:
        """
        Load text data via the unified schema adapter.

        Returns a dict with:
            texts      – list[str]  (the 'text' field from every record)
            industries – list[str]  (the 'industry' field, for classification)

        Records with empty text are silently dropped.
        """
        logger.info("Loading text data via schema adapter...")

        try:
            from services.ai_engine.schema_adapter import load_all_training_data
        except ImportError:
            # Fallback for running as a standalone script
            parent = Path(__file__).resolve().parent
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            from schema_adapter import load_all_training_data

        records = load_all_training_data(self.data_path)

        if not records:
            logger.error("No training records returned by schema adapter")
            return {"texts": [], "industries": []}

        texts = []
        industries = []
        for rec in records:
            text = rec.get("text", "").strip()
            if text:
                texts.append(text)
                industries.append(rec.get("industry", "Unknown"))

        logger.info(f"✅ Loaded {len(texts)} text samples from schema adapter")

        # Quick breakdown by industry for visibility
        from collections import Counter

        top_industries = Counter(industries).most_common(5)
        for ind, cnt in top_industries:
            logger.info(f"   {ind}: {cnt} records")

        return {"texts": texts, "industries": industries}

    # ── Tokenizer & Lemmatizer (NLTK) ────────────────────────────────────

    def train_tokenizer(self, texts: list):
        """Train tokenizer and lemmatizer using NLTK."""
        logger.info("\n🔤 Training Tokenizer & Lemmatizer...")

        try:
            import nltk
            import joblib

            # Download required NLTK data
            for resource in ("punkt", "punkt_tab", "wordnet", "averaged_perceptron_tagger"):
                try:
                    nltk.download(resource, quiet=True)
                except Exception:
                    pass

            from nltk.tokenize import word_tokenize
            from nltk.stem import WordNetLemmatizer

            lemmatizer = WordNetLemmatizer()

            # Process sample texts
            tokenized_samples = []
            lemmatized_samples = []

            for text in texts[:100]:
                tokens = word_tokenize(text.lower())
                tokenized_samples.append(tokens)
                lemmas = [lemmatizer.lemmatize(token) for token in tokens]
                lemmatized_samples.append(lemmas)

            # Save lemmatizer model
            joblib.dump(lemmatizer, self.models_path / "lemmatizer.pkl")

            # Save tokenizer config
            tokenizer_config = {
                "type": "NLTK_WordTokenizer",
                "lemmatizer": "WordNetLemmatizer",
                "sample_tokens": (
                    tokenized_samples[0][:20] if tokenized_samples else []
                ),
                "trained_at": datetime.now().isoformat(),
            }
            with open(self.models_path / "tokenizer_config.json", "w") as f:
                json.dump(tokenizer_config, f, indent=2)

            logger.info("✅ Tokenizer & Lemmatizer trained")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"❌ Tokenizer training failed: {e}")
            return None

    # ── Named Entity Recognition (spaCy) ─────────────────────────────────

    def train_ner_model(self, texts: list):
        """Train / configure Named Entity Recognition model using spaCy."""
        logger.info("\n🔤 Training NER Model...")

        try:
            import spacy
            import joblib

            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning(
                    "spaCy model en_core_web_sm not found — saving config only"
                )
                ner_config = {
                    "model_type": "rule_based",
                    "entity_types": ["PERSON", "ORG", "GPE", "DATE", "SKILL"],
                    "status": "config_only",
                }
                with open(self.models_path / "ner_config.json", "w") as f:
                    json.dump(ner_config, f, indent=2)
                return {"status": "config_saved"}

            # Process sample texts to discover entity types
            entities_found = []
            for text in texts[:50]:
                doc = nlp(text)
                for ent in doc.ents:
                    entities_found.append({"text": ent.text, "label": ent.label_})

            ner_data = {
                "model": "en_core_web_sm",
                "entity_types": sorted(set(e["label"] for e in entities_found)),
                "sample_entities": entities_found[:20],
                "trained_at": datetime.now().isoformat(),
            }

            with open(self.models_path / "ner_model_config.json", "w") as f:
                json.dump(ner_data, f, indent=2)

            logger.info(
                f"✅ NER Model configured — {len(ner_data['entity_types'])} entity types"
            )
            return ner_data

        except Exception as e:
            logger.error(f"❌ NER training failed: {e}")
            return None

    # ── Sentiment Analyzer (heuristic labels) ────────────────────────────

    def train_sentiment_analyzer(self, texts: list):
        """
        Train a sentiment analysis model.

        Labels are generated using a keyword heuristic (positive keywords
        such as *experienced, expert, led, managed, achieved, awarded* vs
        negative keywords) instead of random assignment.  This gives the
        classifier a real, reproducible signal to learn from.
        """
        logger.info("\n🔤 Training Sentiment Analyzer...")

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            import joblib

            # Build labels from keyword heuristics (NOT random)
            labels = [_score_sentiment(t) for t in texts]

            # Log label distribution
            from collections import Counter

            dist = Counter(labels)
            logger.info(
                f"   Sentiment distribution — "
                f"positive: {dist.get('positive', 0)}, "
                f"neutral: {dist.get('neutral', 0)}, "
                f"negative: {dist.get('negative', 0)}"
            )

            # Vectorize
            vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
            X = vectorizer.fit_transform(texts)

            # Train Naïve Bayes classifier
            classifier = MultinomialNB()
            classifier.fit(X, labels)

            # Save artefacts
            joblib.dump(vectorizer, self.models_path / "sentiment_vectorizer.pkl")
            joblib.dump(classifier, self.models_path / "sentiment_classifier.pkl")

            logger.info("✅ Sentiment Analyzer trained")
            return {"status": "success", "label_distribution": dict(dist)}

        except Exception as e:
            logger.error(f"❌ Sentiment training failed: {e}")
            return None

    # ── Text Classifier (real industry labels) ───────────────────────────

    def train_text_classifier(self, texts: list, industries: list):
        """
        Train a text classifier using REAL industry labels from the
        unified schema adapter records (not synthetic random labels).

        Parameters
        ----------
        texts : list[str]
            Training texts.
        industries : list[str]
            Corresponding industry labels (e.g. 'Technology', 'Finance',
            'Oil & Gas', 'Healthcare', …).
        """
        logger.info("\n🔤 Training Text Classifier (industry labels)...")

        try:
            from sklearn.feature_extraction.text import CountVectorizer
            from sklearn.naive_bayes import MultinomialNB
            import joblib

            if len(texts) != len(industries):
                logger.error(
                    "Mismatch: %d texts vs %d industry labels",
                    len(texts),
                    len(industries),
                )
                return None

            # Log label distribution
            from collections import Counter

            dist = Counter(industries)
            logger.info(f"   Industry label counts (top 5): {dist.most_common(5)}")

            # Filter out "Unknown" labels if there are enough labelled samples
            known_idx = [i for i, ind in enumerate(industries) if ind != "Unknown"]
            if len(known_idx) >= 20:
                logger.info(
                    f"   Using {len(known_idx)} records with known industry "
                    f"(dropping {len(texts) - len(known_idx)} 'Unknown')"
                )
                texts_filtered = [texts[i] for i in known_idx]
                labels_filtered = [industries[i] for i in known_idx]
            else:
                logger.warning(
                    "   Fewer than 20 records with known industry — "
                    "using all records including 'Unknown'"
                )
                texts_filtered = texts
                labels_filtered = industries

            # Vectorize
            vectorizer = CountVectorizer(max_features=500, stop_words="english")
            X = vectorizer.fit_transform(texts_filtered)

            # Train Naïve Bayes classifier
            classifier = MultinomialNB()
            classifier.fit(X, labels_filtered)

            # Save artefacts
            joblib.dump(
                vectorizer, self.models_path / "text_classifier_vectorizer.pkl"
            )
            joblib.dump(classifier, self.models_path / "text_classifier.pkl")

            # Save label map for inference
            label_meta = {
                "labels": sorted(set(labels_filtered)),
                "count": len(labels_filtered),
                "trained_at": datetime.now().isoformat(),
            }
            with open(self.models_path / "text_classifier_labels.json", "w") as f:
                json.dump(label_meta, f, indent=2)

            logger.info("✅ Text Classifier trained")
            return {"status": "success", "num_classes": len(label_meta["labels"])}

        except Exception as e:
            logger.error(f"❌ Text classifier training failed: {e}")
            return None

    # ── Word2Vec Embeddings (gensim) ─────────────────────────────────────

    def train_word2vec(self, texts: list):
        """Train Word2Vec embeddings using gensim."""
        logger.info("\n🔤 Training Word2Vec Embeddings...")

        try:
            from gensim.models import Word2Vec
            from nltk.tokenize import word_tokenize

            tokenized_texts = [word_tokenize(text.lower()) for text in texts]

            model = Word2Vec(
                sentences=tokenized_texts,
                vector_size=100,
                window=5,
                min_count=2,
                workers=4,
                epochs=10,
            )

            model.save(str(self.models_path / "word2vec.model"))

            logger.info(f"✅ Word2Vec trained — vocab size: {len(model.wv)}")
            return {"vocab_size": len(model.wv)}

        except Exception as e:
            logger.error(f"❌ Word2Vec training failed: {e}")
            return None

    # ── BERT Embeddings (sentence-transformers) ──────────────────────────

    def setup_bert_embeddings(self):
        """Download / cache a BERT sentence-transformer model."""
        logger.info("\n🔤 Setting up BERT Embeddings...")

        try:
            from sentence_transformers import SentenceTransformer

            # Pull model name from config/models.yaml if available
            try:
                from config.model_config import model_config

                emb_name = model_config.get_embedding_model("sentence_transformers")
            except ImportError:
                emb_name = "all-MiniLM-L6-v2"

            model = SentenceTransformer(emb_name)

            bert_dir = self.models_path / "bert_embeddings"
            bert_dir.mkdir(exist_ok=True)
            model.save(str(bert_dir))

            logger.info("✅ BERT Embeddings configured")
            return {"model": emb_name, "status": "ready"}

        except Exception as e:
            logger.error(f"❌ BERT setup failed: {e}")
            return None

    # ── Topic Modeling (sklearn LDA) ─────────────────────────────────────

    def train_topic_model(self, texts: list):
        """Train Latent Dirichlet Allocation topic model."""
        logger.info("\n🔤 Training Topic Model (LDA)...")

        try:
            from sklearn.decomposition import LatentDirichletAllocation
            from sklearn.feature_extraction.text import CountVectorizer
            import joblib

            vectorizer = CountVectorizer(max_features=1000, stop_words="english")
            X = vectorizer.fit_transform(texts)

            lda = LatentDirichletAllocation(n_components=5, random_state=42)
            lda.fit(X)

            joblib.dump(vectorizer, self.models_path / "topic_vectorizer.pkl")
            joblib.dump(lda, self.models_path / "topic_model_lda.pkl")

            logger.info(f"✅ Topic Model trained — {lda.n_components} topics")
            return {"num_topics": lda.n_components}

        except Exception as e:
            logger.error(f"❌ Topic modeling failed: {e}")
            return None

    # ── GPT Configuration ────────────────────────────────────────────────

    def setup_gpt_config(self):
        """Save GPT prompt configuration to disk."""
        logger.info("\n🔤 Setting up GPT Configuration...")

        try:
            try:
                from config.model_config import model_config

                _gpt_model = model_config.get_llm_model("openai")
            except ImportError:
                _gpt_model = "gpt-4"

            gpt_config = {
                "model_type": "gpt",
                "model_name": _gpt_model,
                "temperature": 0.7,
                "max_tokens": 500,
                "use_case": "text_generation",
                "prompts": {
                    "summary": "Generate a professional summary for this candidate profile:",
                    "bullet_points": "Create 5 achievement bullet points for:",
                    "cover_letter": "Write a cover letter for this candidate:",
                },
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.models_path / "gpt_config.json", "w") as f:
                json.dump(gpt_config, f, indent=2)

            logger.info("✅ GPT Configuration saved")
            return gpt_config

        except Exception as e:
            logger.error(f"❌ GPT config failed: {e}")
            return None

    # ── Orchestrator ─────────────────────────────────────────────────────

    def train_all_nlp_models(self) -> dict:
        """
        Train all NLP & LLM models end-to-end.

        Workflow:
          1. Load unified data via schema adapter → texts + industry labels
          2. Tokenizer & Lemmatizer (NLTK)
          3. Named Entity Recognition (spaCy)
          4. Sentiment Analyzer (heuristic labels + Naïve Bayes)
          5. Text Classifier (real industry labels + Naïve Bayes)
          6. Word2Vec Embeddings (gensim)
          7. BERT Embeddings (sentence-transformers)
          8. Topic Model — LDA (sklearn)
          9. GPT config
        """
        logger.info("\n" + "=" * 60)
        logger.info("NLP & LLM TRAINING — ALL MODELS")
        logger.info("=" * 60)

        # Step 1: load data
        data = self.load_text_data()
        texts = data["texts"]
        industries = data["industries"]

        if not texts:
            logger.error("No text data available — aborting training")
            return {}

        results = {}

        # Step 2–9: train each model
        results["tokenizer"] = self.train_tokenizer(texts)
        results["ner"] = self.train_ner_model(texts)
        results["sentiment"] = self.train_sentiment_analyzer(texts)
        results["text_classifier"] = self.train_text_classifier(texts, industries)
        results["word2vec"] = self.train_word2vec(texts)
        results["bert"] = self.setup_bert_embeddings()
        results["topic_model"] = self.train_topic_model(texts)
        results["gpt"] = self.setup_gpt_config()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("NLP & LLM TRAINING COMPLETE")
        logger.info("=" * 60)
        for name, result in results.items():
            status = "✅" if result else "❌"
            logger.info(f"{status} {name.upper()}")

        return results


if __name__ == "__main__":
    trainer = NLPLLMTrainer(str(Path(__file__).parent))
    results = trainer.train_all_nlp_models()
