"""
AI Training Orchestrator
========================

Comprehensive AI model training pipeline that integrates:
1. Data ingestion from ai_data_final
2. Statistical methods (embeddings, clustering, TF-IDF)
3. Model training (job matching, skill extraction, industry classification)
4. Performance evaluation and metrics
5. Model persistence and versioning

Statistical Methods Integrated:
- Sentence Transformers (embeddings)
- TF-IDF vectorization
- K-Means clustering
- DBSCAN clustering
- Cosine similarity
- Topic modeling (LDA)
- PCA dimensionality reduction
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import Counter
import pickle
import sys
import os

# Set UTF-8 encoding for Python
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ML and NLP imports
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import PCA, LatentDirichletAllocation
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, accuracy_score
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize

    ML_AVAILABLE = True
    logger.info("âœ… ML libraries loaded successfully")
except ImportError as e:
    ML_AVAILABLE = False
    logger.warning(f"âš ï¸ ML libraries not available: {e}")


class AITrainingOrchestrator:
    """
    Orchestrates the complete AI training pipeline from data ingestion to model deployment.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.ai_data_path = self.base_path / "ai_data_final"
        self.models_path = self.base_path / "trained_models"
        self.models_path.mkdir(parents=True, exist_ok=True)

        # Initialize paths
        self.profiles_path = self.ai_data_path / "profiles"
        self.companies_path = self.ai_data_path / "companies"
        self.job_titles_path = self.ai_data_path / "job_titles"

        # ML models
        self.sentence_model = None
        self.tfidf_vectorizer = None
        self.kmeans_model = None
        self.dbscan_model = None
        self.job_classifier = None

        # Training data
        self.candidate_data = []
        self.company_data = []
        self.job_title_data = []

        # Statistics
        self.training_stats = {
            'data_loaded': 0,
            'embeddings_created': 0,
            'models_trained': 0,
            'training_time': 0
        }

        logger.info(f"ðŸ¤– AI Training Orchestrator initialized")
        logger.info(f"   Base path: {self.base_path}")
        logger.info(f"   Models path: {self.models_path}")

    def load_data(self) -> Dict[str, int]:
        """
        Load all ingested data from ai_data_final.

        Returns:
            Dictionary with counts of loaded data
        """
        logger.info("="*80)
        logger.info("ðŸ“Š LOADING DATA FROM AI_DATA_FINAL")
        logger.info("="*80)

        stats = {
            'candidates': 0,
            'companies': 0,
            'job_titles': 0
        }

        # Load candidate profiles
        if self.profiles_path.exists():
            profile_files = list(self.profiles_path.glob("*.json"))
            for profile_file in profile_files:
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.candidate_data.append(data)
                        stats['candidates'] += 1
                except Exception as e:
                    logger.error(f"Error loading {profile_file.name}: {e}")

            logger.info(f"âœ… Loaded {stats['candidates']} candidate profiles")

        # Load companies
        if self.companies_path.exists():
            company_files = list(self.companies_path.glob("*.json"))
            for company_file in company_files:
                try:
                    with open(company_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.company_data.append(data)
                        stats['companies'] += 1
                except Exception as e:
                    logger.error(f"Error loading {company_file.name}: {e}")

            logger.info(f"âœ… Loaded {stats['companies']} companies")

        # Load job titles if available
        if self.job_titles_path.exists():
            job_files = list(self.job_titles_path.glob("*.json"))
            for job_file in job_files:
                try:
                    with open(job_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.job_title_data.append(data)
                        stats['job_titles'] += 1
                except Exception as e:
                    logger.error(f"Error loading {job_file.name}: {e}")

            logger.info(f"âœ… Loaded {stats['job_titles']} job titles")

        self.training_stats['data_loaded'] = sum(stats.values())

        logger.info("="*80)
        return stats

    def prepare_text_data(self) -> Tuple[List[str], List[str]]:
        """
        Extract and prepare text data for training.

        Returns:
            Tuple of (candidate_texts, job_title_texts)
        """
        logger.info("ðŸ“ Preparing text data for training...")

        candidate_texts = []
        job_title_texts = []

        # Extract candidate information
        for candidate in self.candidate_data:
            text_parts = []

            # Add job title if available
            if 'job_title' in candidate:
                text_parts.append(str(candidate['job_title']))
                job_title_texts.append(str(candidate['job_title']))
            elif 'Job Title' in candidate:
                text_parts.append(str(candidate['Job Title']))
                job_title_texts.append(str(candidate['Job Title']))

            # Add company if available
            if 'company' in candidate:
                text_parts.append(str(candidate['company']))
            elif 'Company' in candidate:
                text_parts.append(str(candidate['Company']))

            # Add raw text if available (from parsed CVs)
            if 'raw_text' in candidate:
                # Take first 500 chars to avoid overwhelming the model
                text_parts.append(str(candidate['raw_text'])[:500])

            if text_parts:
                candidate_texts.append(" | ".join(text_parts))

        logger.info(f"âœ… Prepared {len(candidate_texts)} candidate texts")
        logger.info(f"âœ… Extracted {len(job_title_texts)} job titles")

        return candidate_texts, job_title_texts

    def train_embeddings(self, texts: List[str], model_name: str = 'all-MiniLM-L6-v2') -> np.ndarray:
        """
        Train sentence transformer embeddings.

        Args:
            texts: List of texts to embed
            model_name: Sentence transformer model name

        Returns:
            Numpy array of embeddings
        """
        if not ML_AVAILABLE:
            logger.error("ML libraries not available")
            return np.array([])

        logger.info(f"ðŸ§  Training Sentence Transformer embeddings ({model_name})...")

        try:
            # Load model
            if self.sentence_model is None:
                self.sentence_model = SentenceTransformer(model_name)

            # Generate embeddings
            embeddings = self.sentence_model.encode(texts, show_progress_bar=True)

            self.training_stats['embeddings_created'] = len(embeddings)
            logger.info(f"âœ… Created {len(embeddings)} embeddings with {embeddings.shape[1]} dimensions")

            # Save embeddings
            embeddings_path = self.models_path / "candidate_embeddings.npy"
            np.save(embeddings_path, embeddings)
            logger.info(f"ðŸ’¾ Saved embeddings to {embeddings_path}")

            return embeddings

        except Exception as e:
            logger.error(f"Error training embeddings: {e}")
            return np.array([])

    def train_tfidf(self, texts: List[str], max_features: int = 1000) -> np.ndarray:
        """
        Train TF-IDF vectorizer.

        Args:
            texts: List of texts to vectorize
            max_features: Maximum number of features

        Returns:
            TF-IDF matrix
        """
        if not ML_AVAILABLE:
            logger.error("ML libraries not available")
            return np.array([])

        logger.info(f"ðŸ“Š Training TF-IDF vectorizer (max_features={max_features})...")

        try:
            # Initialize vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=max_features,
                stop_words='english',
                ngram_range=(1, 2)
            )

            # Fit and transform
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)

            logger.info(f"âœ… TF-IDF matrix shape: {tfidf_matrix.shape}")
            logger.info(f"âœ… Vocabulary size: {len(self.tfidf_vectorizer.vocabulary_)}")

            # Save vectorizer
            vectorizer_path = self.models_path / "tfidf_vectorizer.pkl"
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
            logger.info(f"ðŸ’¾ Saved TF-IDF vectorizer to {vectorizer_path}")

            # Save top features
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            top_features_path = self.models_path / "tfidf_top_features.json"
            with open(top_features_path, 'w', encoding='utf-8') as f:
                json.dump(list(feature_names[:100]), f, indent=2)

            return tfidf_matrix.toarray()

        except Exception as e:
            logger.error(f"Error training TF-IDF: {e}")
            return np.array([])

    def train_clustering(self, embeddings: np.ndarray, n_clusters: int = 10) -> Dict[str, Any]:
        """
        Train clustering models (K-Means and DBSCAN).

        Args:
            embeddings: Embedding matrix
            n_clusters: Number of clusters for K-Means

        Returns:
            Dictionary with clustering results
        """
        if not ML_AVAILABLE or len(embeddings) == 0:
            logger.error("ML libraries not available or no embeddings")
            return {}

        logger.info(f"ðŸ” Training clustering models...")

        results = {}

        try:
            # K-Means clustering
            logger.info(f"   Training K-Means (n_clusters={n_clusters})...")
            self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans_labels = self.kmeans_model.fit_predict(embeddings)

            results['kmeans'] = {
                'n_clusters': n_clusters,
                'labels': kmeans_labels.tolist(),
                'cluster_counts': {str(k): int(v) for k, v in Counter(kmeans_labels).items()},
                'inertia': float(self.kmeans_model.inertia_)
            }

            logger.info(f"   âœ… K-Means clustering complete")
            logger.info(f"      Inertia: {self.kmeans_model.inertia_:.2f}")

            # Save K-Means model
            kmeans_path = self.models_path / "kmeans_model.pkl"
            with open(kmeans_path, 'wb') as f:
                pickle.dump(self.kmeans_model, f)

            # DBSCAN clustering
            logger.info(f"   Training DBSCAN...")
            self.dbscan_model = DBSCAN(eps=0.5, min_samples=5)
            dbscan_labels = self.dbscan_model.fit_predict(embeddings)

            n_clusters_dbscan = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
            n_noise = list(dbscan_labels).count(-1)

            results['dbscan'] = {
                'n_clusters': n_clusters_dbscan,
                'n_noise': n_noise,
                'labels': dbscan_labels.tolist(),
                'cluster_counts': {str(k): int(v) for k, v in Counter(dbscan_labels).items()}
            }

            logger.info(f"   âœ… DBSCAN clustering complete")
            logger.info(f"      Clusters: {n_clusters_dbscan}, Noise points: {n_noise}")

            # Save clustering results
            clustering_path = self.models_path / "clustering_results.json"
            # Convert Counter objects to regular dicts for JSON serialization
            results_json = {
                'kmeans': {
                    'n_clusters': results['kmeans']['n_clusters'],
                    'cluster_counts': dict(results['kmeans']['cluster_counts']),
                    'inertia': results['kmeans']['inertia']
                },
                'dbscan': {
                    'n_clusters': results['dbscan']['n_clusters'],
                    'n_noise': results['dbscan']['n_noise'],
                    'cluster_counts': dict(results['dbscan']['cluster_counts'])
                }
            }
            with open(clustering_path, 'w', encoding='utf-8') as f:
                json.dump(results_json, f, indent=2)

            self.training_stats['models_trained'] += 2

        except Exception as e:
            logger.error(f"Error training clustering: {e}")

        return results

    def calculate_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity matrix.

        Args:
            embeddings: Embedding matrix

        Returns:
            Similarity matrix
        """
        if not ML_AVAILABLE or len(embeddings) == 0:
            return np.array([])

        logger.info("ðŸ”— Calculating cosine similarity matrix...")

        try:
            similarity_matrix = cosine_similarity(embeddings)

            logger.info(f"âœ… Similarity matrix shape: {similarity_matrix.shape}")
            logger.info(f"   Mean similarity: {similarity_matrix.mean():.3f}")
            logger.info(f"   Max similarity: {similarity_matrix.max():.3f}")

            # Save similarity matrix
            similarity_path = self.models_path / "similarity_matrix.npy"
            np.save(similarity_path, similarity_matrix)

            return similarity_matrix

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return np.array([])

    def train_job_classifier(self, job_titles: List[str], categories: List[str] = None) -> Dict[str, Any]:
        """
        Train a job title classifier using Random Forest.

        Args:
            job_titles: List of job titles
            categories: List of job categories (if None, will auto-generate)

        Returns:
            Dictionary with training results
        """
        if not ML_AVAILABLE or len(job_titles) == 0:
            logger.error("ML libraries not available or no job titles")
            return {}

        logger.info("ðŸŽ¯ Training job title classifier...")

        try:
            # Auto-generate categories from job titles if not provided
            if categories is None:
                # Simple categorization based on keywords
                categories = []
                for title in job_titles:
                    title_lower = title.lower()
                    if any(word in title_lower for word in ['manager', 'director', 'lead', 'head']):
                        categories.append('Management')
                    elif any(word in title_lower for word in ['engineer', 'developer', 'programmer']):
                        categories.append('Engineering')
                    elif any(word in title_lower for word in ['analyst', 'data', 'scientist']):
                        categories.append('Analytics')
                    elif any(word in title_lower for word in ['sales', 'account', 'business development']):
                        categories.append('Sales')
                    elif any(word in title_lower for word in ['marketing', 'content', 'social']):
                        categories.append('Marketing')
                    else:
                        categories.append('Other')

            # Create TF-IDF features
            vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
            X = vectorizer.fit_transform(job_titles)
            y = categories

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Train classifier
            self.job_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.job_classifier.fit(X_train, y_train)

            # Evaluate
            y_pred = self.job_classifier.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            logger.info(f"âœ… Job classifier trained")
            logger.info(f"   Accuracy: {accuracy:.3f}")
            logger.info(f"   Categories: {set(categories)}")

            # Save models
            classifier_path = self.models_path / "job_classifier.pkl"
            with open(classifier_path, 'wb') as f:
                pickle.dump(self.job_classifier, f)

            vectorizer_path = self.models_path / "job_classifier_vectorizer.pkl"
            with open(vectorizer_path, 'wb') as f:
                pickle.dump(vectorizer, f)

            self.training_stats['models_trained'] += 1

            return {
                'accuracy': accuracy,
                'n_categories': len(set(categories)),
                'category_distribution': dict(Counter(categories))
            }

        except Exception as e:
            logger.error(f"Error training job classifier: {e}")
            return {}

    def run_full_training_pipeline(self) -> Dict[str, Any]:
        """
        Execute the complete training pipeline.

        Returns:
            Dictionary with all training results
        """
        start_time = datetime.now()

        logger.info("="*80)
        logger.info("ðŸš€ STARTING FULL AI TRAINING PIPELINE")
        logger.info("="*80)

        results = {}

        # 1. Load data
        results['data'] = self.load_data()

        # 2. Prepare text data
        candidate_texts, job_titles = self.prepare_text_data()

        if len(candidate_texts) == 0:
            logger.error("âŒ No candidate data available for training")
            return results

        # 3. Train embeddings
        embeddings = self.train_embeddings(candidate_texts)
        results['embeddings'] = {
            'count': len(embeddings),
            'dimensions': embeddings.shape[1] if len(embeddings) > 0 else 0
        }

        # 4. Train TF-IDF
        tfidf_matrix = self.train_tfidf(candidate_texts)
        results['tfidf'] = {
            'shape': tfidf_matrix.shape if len(tfidf_matrix) > 0 else (0, 0)
        }

        # 5. Train clustering
        if len(embeddings) > 0:
            n_clusters = min(10, len(embeddings) // 5)  # Adjust cluster count based on data size
            if n_clusters >= 2:
                results['clustering'] = self.train_clustering(embeddings, n_clusters)

        # 6. Calculate similarity
        if len(embeddings) > 0:
            similarity_matrix = self.calculate_similarity_matrix(embeddings)
            results['similarity'] = {
                'shape': similarity_matrix.shape if len(similarity_matrix) > 0 else (0, 0)
            }

        # 7. Train job classifier
        if len(job_titles) > 10:  # Need minimum data for classification
            results['job_classifier'] = self.train_job_classifier(job_titles)

        # Calculate total training time
        end_time = datetime.now()
        training_time = (end_time - start_time).total_seconds()
        self.training_stats['training_time'] = training_time

        # Save training results
        results['statistics'] = self.training_stats
        results['training_time'] = training_time
        results['timestamp'] = datetime.now().isoformat()

        results_path = self.models_path / "training_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("="*80)
        logger.info("âœ… TRAINING PIPELINE COMPLETE")
        logger.info(f"   Total time: {training_time:.2f} seconds")
        logger.info(f"   Data loaded: {self.training_stats['data_loaded']}")
        logger.info(f"   Embeddings created: {self.training_stats['embeddings_created']}")
        logger.info(f"   Models trained: {self.training_stats['models_trained']}")
        logger.info(f"   Results saved to: {results_path}")
        logger.info("="*80)

        return results


def main():
    """Main entry point for training orchestrator."""
    base_path = Path(__file__).parent

    orchestrator = AITrainingOrchestrator(str(base_path))
    results = orchestrator.run_full_training_pipeline()

    return results


if __name__ == "__main__":
    main()

