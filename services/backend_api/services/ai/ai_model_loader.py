"""
Centralized AI Model Loader
============================

Loads all trained models at startup and provides global access.
"""

from pathlib import Path
import pickle
import logging

logger = logging.getLogger(__name__)

def _get_embedding_model() -> str:
    """Read embedding model name from config/models.yaml."""
    try:
        from config.model_config import model_config
        return model_config.get_embedding_model()
    except Exception:
        return "all-MiniLM-L6-v2"

def _get_models_dir() -> Path:
    """Read trained models dir from config/models.yaml."""
    try:
        from config.model_config import model_config
        return model_config.get_ml_base_dir()
    except Exception:
        return Path(__file__).parent.parent / "models"

class AIModelLoader:
    """Central model loading and caching — reads paths from config/models.yaml"""

    def __init__(self):
        self.models_dir = _get_models_dir()
        self.models = {}
        self.loaded = False

    def load_all_models(self):
        """Load all available trained models"""
        if self.loaded:
            return self.models

        logger.info("Loading AI models...")

        # Bayesian Classifier
        try:
            bayesian_file = self.models_dir / "bayesian_classifier.pkl"
            vectorizer_file = self.models_dir / "tfidf_vectorizer.pkl"

            if bayesian_file.exists() and vectorizer_file.exists():
                self.models['bayesian'] = pickle.load(open(bayesian_file, 'rb'))
                self.models['vectorizer'] = pickle.load(open(vectorizer_file, 'rb'))
                logger.info("✅ Loaded Bayesian classifier")
        except Exception as e:
            logger.warning(f"Failed to load Bayesian: {e}")

        # Sentence-BERT (model name from config/models.yaml)
        try:
            from sentence_transformers import SentenceTransformer
            emb_model = _get_embedding_model()
            self.models['embedder'] = SentenceTransformer(emb_model)
            logger.info(f"✅ Loaded Sentence-BERT embedder: {emb_model}")
        except ImportError:
            logger.warning("sentence-transformers not installed")
        except Exception as e:
            logger.warning(f"Failed to load embedder: {e}")

        # spaCy NER
        try:
            import spacy
            self.models['spacy'] = spacy.load("en_core_web_sm")
            logger.info("✅ Loaded spaCy NER model")
        except Exception as e:
            logger.warning(f"Failed to load spaCy: {e}")

        # Salary Predictor
        try:
            salary_file = self.models_dir / "salary_predictor.pkl"
            if salary_file.exists():
                self.models['salary'] = pickle.load(open(salary_file, 'rb'))
                logger.info("✅ Loaded salary predictor")
        except Exception as e:
            logger.warning(f"Failed to load salary predictor: {e}")

        self.loaded = True
        logger.info(f"Loaded {len(self.models)} models")

        return self.models

    def get_model(self, name: str):
        """Get specific model by name"""
        if not self.loaded:
            self.load_all_models()

        return self.models.get(name)

# Global instance
_loader = AIModelLoader()

def get_trained_models():
    """Get all trained models (global access)"""
    return _loader.load_all_models()

def get_model(name: str):
    """Get specific model by name"""
    return _loader.get_model(name)
