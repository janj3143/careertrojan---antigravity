#!/usr/bin/env python3
"""
Full ML Models Training Pipeline
=================================
Trains remaining 6 ML models:
1. Linear Regression (salary prediction)
2. Logistic Regression (placement success)
3. Multiple Regression (job match scoring)
4. Random Forest Regressor (advanced predictions)
5. PCA (dimensionality reduction)
6. Hierarchical Clustering (dendrograms)

Output: trained_models/ + ai_data_final/analytics/
"""

import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pickle
import sys
import os

# Set UTF-8 encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ML libraries
try:
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.decomposition import PCA
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
    import scipy.cluster.hierarchy as hierarchy
    ML_AVAILABLE = True
    logger.info("âœ… ML libraries loaded successfully")
except ImportError as e:
    ML_AVAILABLE = False
    logger.error(f"âŒ ML libraries error: {e}")
    sys.exit(1)


class FullMLTrainer:
    """Train remaining 6 ML models for IntelliCV."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or ".")
        self.ai_data_path = self.base_path / "ai_data_final"
        self.models_path = self.base_path / "trained_models"
        self.analytics_path = self.ai_data_path / "analytics"
        
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.analytics_path.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'models_trained': [],
            'training_details': {}
        }
    
    def load_training_data(self) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """Load embeddings and data for training."""
        logger.info("ðŸ“‚ Loading training data...")
        
        # Load candidate embeddings
        embeddings = np.load(self.models_path / "candidate_embeddings.npy")
        logger.info(f"   âœ… Embeddings: {embeddings.shape}")
        
        # Load training results to get context
        with open(self.models_path / "training_results.json") as f:
            training_meta = json.load(f)
        
        # Create synthetic training data for models (using embeddings)
        # In production, you'd have actual labeled data
        n_samples = embeddings.shape[0]
        
        # Simulated targets (in production, use real data)
        salary_target = np.random.uniform(50000, 200000, n_samples)  # Simulated salaries
        placement_target = np.random.binomial(1, 0.7, n_samples)  # 70% placement rate
        match_score = np.random.uniform(0, 100, n_samples)  # Simulated job match scores
        
        logger.info(f"   âœ… Generated {n_samples} training samples")
        
        return embeddings, {
            'salary': salary_target,
            'placement': placement_target,
            'match_score': match_score
        }, training_meta
    
    def train_linear_regression(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train Linear Regression for salary prediction."""
        logger.info("\nðŸ”¬ Training Linear Regression (Salary Prediction)...")
        
        try:
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            test_rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))
            
            # Save
            with open(self.models_path / "linear_regression_salary.pkl", 'wb') as f:
                pickle.dump(model, f)
            
            results = {
                'model': 'Linear Regression',
                'task': 'Salary Prediction',
                'train_r2': float(train_score),
                'test_r2': float(test_score),
                'rmse': float(test_rmse),
                'n_samples': len(X_train),
                'features': int(X.shape[1]),
                'status': 'Trained'
            }
            
            logger.info(f"   Linear Regression trained")
            logger.info(f"      Train RÂ²: {train_score:.4f}")
            logger.info(f"      Test RÂ²: {test_score:.4f}")
            logger.info(f"      RMSE: ${test_rmse:,.2f}")
            
            self.results['models_trained'].append('Linear Regression')
            self.results['training_details']['linear_regression'] = results
            
            return results
            
        except Exception as e:
            logger.error(f"   âŒ Linear Regression failed: {e}")
            return {'error': str(e)}
    
    def train_logistic_regression(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train Logistic Regression for placement success prediction."""
        logger.info("\nðŸ”¬ Training Logistic Regression (Placement Success)...")
        
        try:
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train
            model = LogisticRegression(max_iter=1000, random_state=42)
            model.fit(X_train, y_train)
            
            # Evaluate
            train_acc = model.score(X_train, y_train)
            test_acc = model.score(X_test, y_test)
            
            # Save
            with open(self.models_path / "logistic_regression_placement.pkl", 'wb') as f:
                pickle.dump(model, f)
            
            results = {
                'model': 'Logistic Regression',
                'task': 'Placement Success',
                'train_accuracy': float(train_acc),
                'test_accuracy': float(test_acc),
                'n_samples': len(X_train),
                'features': int(X.shape[1]),
                'status': 'Trained'
            }
            
            logger.info(f"   Logistic Regression trained")
            logger.info(f"      Train Accuracy: {train_acc:.1%}")
            logger.info(f"      Test Accuracy: {test_acc:.1%}")
            
            self.results['models_trained'].append('Logistic Regression')
            self.results['training_details']['logistic_regression'] = results
            
            return results
            
        except Exception as e:
            logger.error(f"   âŒ Logistic Regression failed: {e}")
            return {'error': str(e)}
    
    def train_multiple_regression(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train Multiple Regression for job match scoring."""
        logger.info("\nðŸ”¬ Training Multiple Regression (Job Match Scoring)...")
        
        try:
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Normalize (important for multiple regression)
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            test_rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test_scaled)))
            
            # Save model and scaler
            with open(self.models_path / "multiple_regression_match.pkl", 'wb') as f:
                pickle.dump((model, scaler), f)
            
            results = {
                'model': 'Multiple Regression',
                'task': 'Job Match Scoring (1-100)',
                'train_r2': float(train_score),
                'test_r2': float(test_score),
                'rmse': float(test_rmse),
                'n_samples': len(X_train),
                'features': int(X.shape[1]),
                'coefficients_count': len(model.coef_),
                'status': 'Trained'
            }
            
            logger.info(f"   Multiple Regression trained")
            logger.info(f"      Train RÂ²: {train_score:.4f}")
            logger.info(f"      Test RÂ²: {test_score:.4f}")
            logger.info(f"      RMSE: {test_rmse:.2f} points")
            
            self.results['models_trained'].append('Multiple Regression')
            self.results['training_details']['multiple_regression'] = results
            
            return results
            
        except Exception as e:
            logger.error(f"   âŒ Multiple Regression failed: {e}")
            return {'error': str(e)}
    
    def train_random_forest_regressor(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train Random Forest for advanced predictions."""
        logger.info("\nðŸ”¬ Training Random Forest Regressor (Advanced Predictions)...")
        
        try:
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Train
            model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            test_score = model.score(X_test, y_test)
            test_rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))
            
            # Feature importance
            feature_importance = sorted(
                zip(range(len(model.feature_importances_)), model.feature_importances_),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Save
            with open(self.models_path / "random_forest_regressor.pkl", 'wb') as f:
                pickle.dump(model, f)
            
            results = {
                'model': 'Random Forest Regressor',
                'task': 'Advanced Predictions',
                'train_r2': float(train_score),
                'test_r2': float(test_score),
                'rmse': float(test_rmse),
                'n_estimators': 100,
                'n_samples': len(X_train),
                'features': int(X.shape[1]),
                'top_features': [{'feature': f, 'importance': float(i)} for f, i in feature_importance],
                'status': 'Trained'
            }
            
            logger.info(f"   âœ… Random Forest Regressor trained")
            logger.info(f"      Train RÂ²: {train_score:.4f}")
            logger.info(f"      Test RÂ²: {test_score:.4f}")
            logger.info(f"      RMSE: {test_rmse:.2f}")
            
            self.results['models_trained'].append('Random Forest Regressor')
            self.results['training_details']['random_forest'] = results
            
            return results
            
        except Exception as e:
            logger.error(f"   âŒ Random Forest failed: {e}")
            return {'error': str(e)}
    
    def train_pca(self, X: np.ndarray) -> Dict[str, Any]:
        """Train PCA for dimensionality reduction."""
        logger.info("\nðŸ”¬ Training PCA (Dimensionality Reduction)...")
        
        try:
            # Normalize data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Determine optimal components (explain 95% variance)
            pca_full = PCA()
            pca_full.fit(X_scaled)
            
            # Find components for 95% variance
            cumsum = np.cumsum(pca_full.explained_variance_ratio_)
            n_components = np.argmax(cumsum >= 0.95) + 1
            
            # Train PCA with optimal components
            pca = PCA(n_components=n_components)
            X_reduced = pca.fit_transform(X_scaled)
            
            # Save model and scaler
            with open(self.models_path / "pca_reducer.pkl", 'wb') as f:
                pickle.dump((pca, scaler), f)
            
            results = {
                'model': 'PCA',
                'task': 'Dimensionality Reduction',
                'original_features': int(X.shape[1]),
                'reduced_features': int(n_components),
                'reduction_ratio': f"{100 * (1 - n_components / X.shape[1]):.1f}%",
                'variance_explained': float(cumsum[n_components - 1]),
                'n_samples': int(X.shape[0]),
                'status': 'Trained'
            }
            
            logger.info(f"   PCA trained")
            logger.info(f"      Original features: {X.shape[1]}")
            logger.info(f"      Reduced features: {n_components}")
            logger.info(f"      Reduction: {100 * (1 - n_components / X.shape[1]):.1f}%")
            logger.info(f"      Variance explained: {cumsum[n_components - 1]:.1%}")
            
            self.results['models_trained'].append('PCA')
            self.results['training_details']['pca'] = results
            
            return results
            
        except Exception as e:
            logger.error(f"   âŒ PCA failed: {e}")
            return {'error': str(e)}
    
    def train_hierarchical_clustering(self, X: np.ndarray) -> Dict[str, Any]:
        """Train Hierarchical Clustering for dendrograms."""
        logger.info("\nðŸ”¬ Training Hierarchical Clustering (Dendrograms)...")
        
        try:
            # Sample data if too large (hierarchical clustering is O(nÂ²))
            if len(X) > 2000:
                sample_idx = np.random.choice(len(X), 2000, replace=False)
                X_sample = X[sample_idx]
                logger.info(f"   ðŸ“Š Sampled 2000 from {len(X)} for efficiency")
            else:
                X_sample = X
            
            # Normalize
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_sample)
            
            # Train hierarchical clustering
            model = AgglomerativeClustering(n_clusters=10, linkage='ward')
            labels = model.fit_predict(X_scaled)
            
            # Save model and scaler
            with open(self.models_path / "hierarchical_clustering.pkl", 'wb') as f:
                pickle.dump((model, scaler), f)
            
            # Count samples per cluster
            unique, counts = np.unique(labels, return_counts=True)
            cluster_sizes = {int(k): int(v) for k, v in zip(unique, counts)}
            
            results = {
                'model': 'Hierarchical Clustering',
                'task': 'Multi-level Segmentation & Dendrograms',
                'n_clusters': 10,
                'linkage': 'ward',
                'n_samples': len(X_sample),
                'features': int(X.shape[1]),
                'cluster_distribution': cluster_sizes,
                'status': 'Trained'
            }
            
            logger.info(f"   Hierarchical Clustering trained")
            logger.info(f"      Clusters: 10")
            logger.info(f"      Linkage: Ward")
            logger.info(f"      Samples: {len(X_sample):,}")
            
            self.results['models_trained'].append('Hierarchical Clustering')
            self.results['training_details']['hierarchical_clustering'] = results
            
            return results
            
        except Exception as e:
            logger.error(f"   âŒ Hierarchical Clustering failed: {e}")
            return {'error': str(e)}
    
    def train_all(self):
        """Train all 6 ML models."""
        logger.info("\n" + "="*80)
        logger.info("ðŸš€ FULL ML MODELS TRAINING PIPELINE")
        logger.info("="*80)
        
        # Load data
        embeddings, targets, meta = self.load_training_data()
        
        # Train models
        self.train_linear_regression(embeddings, targets['salary'])
        self.train_logistic_regression(embeddings, targets['placement'])
        self.train_multiple_regression(embeddings, targets['match_score'])
        self.train_random_forest_regressor(embeddings, targets['salary'])
        self.train_pca(embeddings)
        self.train_hierarchical_clustering(embeddings)
        
        # Save results
        with open(self.models_path / "full_ml_training_results.json", 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Summary
        logger.info("\n" + "="*80)
        logger.info("âœ… FULL ML TRAINING COMPLETE")
        logger.info("="*80)
        logger.info(f"Models trained: {len(self.results['models_trained'])}")
        for model in self.results['models_trained']:
            logger.info(f"   âœ… {model}")
        
        logger.info(f"\nResults saved to: trained_models/full_ml_training_results.json")
        logger.info("="*80 + "\n")
        
        return self.results


if __name__ == '__main__':
    trainer = FullMLTrainer(base_path=".")
    trainer.train_all()

