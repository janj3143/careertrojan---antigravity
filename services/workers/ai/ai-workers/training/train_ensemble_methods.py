"""
ðŸŽ² Ensemble Methods Training Module
====================================
Trains all ensemble learning models:
- Random Forests
- Gradient Boosting (XGBoost, LightGBM, CatBoost)
- AdaBoost
- Voting Classifiers
- Stacking/Blending
"""

import sys
import os
import logging
from pathlib import Path
import json
import numpy as np
from datetime import datetime

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class EnsembleTrainer:
    """Comprehensive ensemble methods trainer"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.data_path = Path(r"L:\antigravity_version_ai_data_final\ai_data_final")
        self.models_path = self.base_path / "trained_models" / "ensemble"
        self.models_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Ensemble Methods Trainer initialized")
        logger.info(f"Models will be saved to: {self.models_path}")

    def load_training_data(self):
        """Load candidate profiles for training"""
        logger.info("Loading training data...")

        profiles_dir = self.data_path / "profiles"
        if not profiles_dir.exists():
            logger.error(f"Profiles directory not found")
            return None, None

        features = []
        labels = []
        json_files = list(profiles_dir.glob("*.json"))[:5000]

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)

                    skills = profile.get('skills', [])
                    experience = profile.get('work_experience', [])
                    education = profile.get('education', [])

                    feature_dict = {
                        'skills_count': len(skills),
                        'experience_years': len(experience),
                        'education_count': len(education),
                        'has_technical_skills': int(any('technical' in str(s).lower() for s in skills)),
                        'has_management': int(any('manag' in str(exp).lower() for exp in experience)),
                        'has_degree': int(any('degree' in str(edu).lower() for edu in education))
                    }

                    features.append(list(feature_dict.values()))

                    # Label: seniority level
                    label = len(experience) // 3
                    labels.append(min(label, 2))

            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        X = np.array(features)
        y = np.array(labels)

        logger.info(f"âœ… Loaded {len(X)} samples")
        return X, y

    def train_random_forest(self, X, y):
        """Train Random Forest classifier"""
        logger.info("\nðŸŽ² Training Random Forest...")

        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score, classification_report
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train Random Forest
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

            rf.fit(X_train, y_train)

            # Evaluate
            y_pred = rf.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Feature importances
            feature_names = ['skills_count', 'experience_years', 'education_count', 'has_technical_skills', 'has_management', 'has_degree']
            importances = {name: float(imp) for name, imp in zip(feature_names, rf.feature_importances_)}

            # Save model
            joblib.dump(rf, self.models_path / "random_forest.pkl")

            # Save metadata
            rf_metadata = {
                'accuracy': accuracy,
                'n_estimators': rf.n_estimators,
                'max_depth': rf.max_depth,
                'feature_importances': importances
            }

            with open(self.models_path / "random_forest_metadata.json", 'w') as f:
                json.dump(rf_metadata, f, indent=2)

            logger.info(f"âœ… Random Forest trained - Accuracy: {accuracy:.4f}")
            return rf_metadata

        except Exception as e:
            logger.error(f"âŒ Random Forest training failed: {e}")
            return None

    def train_xgboost(self, X, y):
        """Train XGBoost classifier"""
        logger.info("\nðŸŽ² Training XGBoost...")

        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train XGBoost
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )

            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            joblib.dump(model, self.models_path / "xgboost.pkl")

            logger.info(f"âœ… XGBoost trained - Accuracy: {accuracy:.4f}")
            return {'accuracy': accuracy}

        except Exception as e:
            logger.error(f"âŒ XGBoost training failed: {e}")
            return None

    def train_lightgbm(self, X, y):
        """Train LightGBM classifier"""
        logger.info("\nðŸŽ² Training LightGBM...")

        try:
            import lightgbm as lgb
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train LightGBM
            model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                verbose=-1
            )

            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            joblib.dump(model, self.models_path / "lightgbm.pkl")

            logger.info(f"âœ… LightGBM trained - Accuracy: {accuracy:.4f}")
            return {'accuracy': accuracy}

        except Exception as e:
            logger.error(f"âŒ LightGBM training failed: {e}")
            return None

    def train_catboost(self, X, y):
        """Train CatBoost classifier"""
        logger.info("\nðŸŽ² Training CatBoost...")

        try:
            from catboost import CatBoostClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train CatBoost
            model = CatBoostClassifier(
                iterations=100,
                depth=6,
                learning_rate=0.1,
                random_state=42,
                verbose=0
            )

            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            joblib.dump(model, self.models_path / "catboost.pkl")

            logger.info(f"âœ… CatBoost trained - Accuracy: {accuracy:.4f}")
            return {'accuracy': accuracy}

        except Exception as e:
            logger.error(f"âŒ CatBoost training failed: {e}")
            return None

    def train_adaboost(self, X, y):
        """Train AdaBoost classifier"""
        logger.info("\nðŸŽ² Training AdaBoost...")

        try:
            from sklearn.ensemble import AdaBoostClassifier
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Train AdaBoost
            base_estimator = DecisionTreeClassifier(max_depth=3)
            model = AdaBoostClassifier(
                base_estimator=base_estimator,
                n_estimators=50,
                random_state=42
            )

            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            joblib.dump(model, self.models_path / "adaboost.pkl")

            logger.info(f"âœ… AdaBoost trained - Accuracy: {accuracy:.4f}")
            return {'accuracy': accuracy}

        except Exception as e:
            logger.error(f"âŒ AdaBoost training failed: {e}")
            return None

    def train_voting_ensemble(self, X, y):
        """Train Voting Classifier ensemble"""
        logger.info("\nðŸŽ² Training Voting Ensemble...")

        try:
            from sklearn.ensemble import VotingClassifier, RandomForestClassifier, GradientBoostingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Create base models
            rf = RandomForestClassifier(n_estimators=50, random_state=42)
            gb = GradientBoostingClassifier(n_estimators=50, random_state=42)
            lr = LogisticRegression(max_iter=1000, random_state=42)

            # Create voting ensemble
            voting = VotingClassifier(
                estimators=[('rf', rf), ('gb', gb), ('lr', lr)],
                voting='soft'
            )

            voting.fit(X_train, y_train)

            # Evaluate
            y_pred = voting.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            joblib.dump(voting, self.models_path / "voting_ensemble.pkl")

            logger.info(f"âœ… Voting Ensemble trained - Accuracy: {accuracy:.4f}")
            return {'accuracy': accuracy, 'n_estimators': 3}

        except Exception as e:
            logger.error(f"âŒ Voting Ensemble training failed: {e}")
            return None

    def train_stacking_ensemble(self, X, y):
        """Train Stacking Classifier ensemble"""
        logger.info("\nðŸŽ² Training Stacking Ensemble...")

        try:
            from sklearn.ensemble import StackingClassifier, RandomForestClassifier, GradientBoostingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import joblib

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Base models
            estimators = [
                ('rf', RandomForestClassifier(n_estimators=50, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=50, random_state=42))
            ]

            # Meta-model
            meta_model = LogisticRegression(max_iter=1000, random_state=42)

            # Stacking ensemble
            stacking = StackingClassifier(
                estimators=estimators,
                final_estimator=meta_model,
                cv=5
            )

            stacking.fit(X_train, y_train)

            # Evaluate
            y_pred = stacking.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            # Save model
            joblib.dump(stacking, self.models_path / "stacking_ensemble.pkl")

            logger.info(f"âœ… Stacking Ensemble trained - Accuracy: {accuracy:.4f}")
            return {'accuracy': accuracy}

        except Exception as e:
            logger.error(f"âŒ Stacking Ensemble training failed: {e}")
            return None

    def train_all_ensembles(self):
        """Train all ensemble methods"""
        logger.info("\n" + "="*60)
        logger.info("ENSEMBLE METHODS TRAINING - ALL VARIANTS")
        logger.info("="*60)

        # Load data
        X, y = self.load_training_data()
        if X is None:
            logger.error("No training data available")
            return {}

        results = {}

        # Train each ensemble type
        results['random_forest'] = self.train_random_forest(X, y)
        results['xgboost'] = self.train_xgboost(X, y)
        results['lightgbm'] = self.train_lightgbm(X, y)
        results['catboost'] = self.train_catboost(X, y)
        results['adaboost'] = self.train_adaboost(X, y)
        results['voting'] = self.train_voting_ensemble(X, y)
        results['stacking'] = self.train_stacking_ensemble(X, y)

        # Summary
        logger.info("\n" + "="*60)
        logger.info("ENSEMBLE METHODS TRAINING COMPLETE")
        logger.info("="*60)
        for name, result in results.items():
            status = "âœ…" if result else "âŒ"
            logger.info(f"{status} {name.upper()}")

        return results


if __name__ == "__main__":
    trainer = EnsembleTrainer(str(Path(__file__).parent))
    results = trainer.train_all_ensembles()

