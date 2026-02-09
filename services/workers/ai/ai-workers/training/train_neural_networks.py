"""
ðŸ§  Neural Network Training Module
===================================
Trains all neural network architectures:
- Deep Neural Networks (DNNs)
- Convolutional Neural Networks (CNNs)
- Recurrent Neural Networks (RNNs/LSTMs)
- Transformers (BERT-style encoders)
- Autoencoders
"""

import sys
import os
import logging
from pathlib import Path
import json
import numpy as np
import pandas as pd
from datetime import datetime

# UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class NeuralNetworkTrainer:
    """Comprehensive neural network trainer"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.data_path = Path(r"L:\antigravity_version_ai_data_final\ai_data_final")
        self.models_path = self.base_path / "trained_models" / "neural"
        self.models_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Neural Network Trainer initialized")
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Models will be saved to: {self.models_path}")

    def load_training_data(self):
        """Load all candidate profiles for training"""
        logger.info("Loading training data...")

        profiles_dir = self.data_path / "profiles"
        if not profiles_dir.exists():
            logger.error(f"Profiles directory not found: {profiles_dir}")
            return None

        all_profiles = []
        json_files = list(profiles_dir.glob("*.json"))

        logger.info(f"Found {len(json_files)} profile files")

        for i, json_file in enumerate(json_files[:10000], 1):  # Limit for training
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    all_profiles.append(profile)

                if i % 1000 == 0:
                    logger.info(f"Loaded {i} profiles...")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        logger.info(f"âœ… Loaded {len(all_profiles)} profiles for training")
        return all_profiles

    def prepare_features(self, profiles):
        """Extract features from profiles for neural network training"""
        logger.info("Preparing features for neural networks...")

        features = []
        labels = []

        for profile in profiles:
            try:
                # Extract text features
                skills = profile.get('skills', [])
                experience = profile.get('work_experience', [])
                education = profile.get('education', [])

                # Create feature vector
                feature_dict = {
                    'skills_count': len(skills),
                    'experience_years': len(experience),
                    'education_count': len(education),
                    'has_technical_skills': any('technical' in str(s).lower() for s in skills),
                    'has_management': any('manag' in str(exp).lower() for exp in experience),
                    'has_degree': any('degree' in str(edu).lower() for edu in education)
                }

                features.append(list(feature_dict.values()))

                # Create label (for classification - e.g., seniority level)
                label = self._infer_seniority(profile)
                labels.append(label)

            except Exception as e:
                logger.error(f"Error preparing features: {e}")

        X = np.array(features)
        y = np.array(labels)

        logger.info(f"âœ… Prepared {len(X)} feature vectors with shape {X.shape}")
        return X, y

    def _infer_seniority(self, profile):
        """Infer seniority level from profile (0=Junior, 1=Mid, 2=Senior)"""
        exp_count = len(profile.get('work_experience', []))
        if exp_count >= 10:
            return 2  # Senior
        elif exp_count >= 5:
            return 1  # Mid
        else:
            return 0  # Junior

    def train_dnn_classifier(self, X, y):
        """Train Deep Neural Network classifier"""
        logger.info("\nðŸ§  Training Deep Neural Network (DNN)...")

        try:
            import tensorflow as tf
            from tensorflow import keras
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            # Build DNN
            model = keras.Sequential([
                keras.layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
                keras.layers.Dropout(0.3),
                keras.layers.Dense(64, activation='relu'),
                keras.layers.Dropout(0.2),
                keras.layers.Dense(32, activation='relu'),
                keras.layers.Dense(3, activation='softmax')  # 3 seniority levels
            ])

            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

            # Train
            history = model.fit(
                X_train_scaled, y_train,
                epochs=50,
                batch_size=32,
                validation_split=0.2,
                verbose=0
            )

            # Evaluate
            loss, accuracy = model.evaluate(X_test_scaled, y_test, verbose=0)
            logger.info(f"âœ… DNN trained - Accuracy: {accuracy:.4f}")

            # Save model
            model.save(self.models_path / "dnn_classifier.h5")

            # Save scaler
            import joblib
            joblib.dump(scaler, self.models_path / "dnn_scaler.pkl")

            return {'accuracy': accuracy, 'loss': loss, 'history': history.history}

        except Exception as e:
            logger.error(f"âŒ DNN training failed: {e}")
            return None

    def train_cnn_embedder(self, X, y):
        """Train CNN for feature embedding"""
        logger.info("\nðŸ§  Training Convolutional Neural Network (CNN)...")

        try:
            import tensorflow as tf
            from tensorflow import keras

            # Reshape for CNN (add channel dimension)
            X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)

            # Build CNN
            model = keras.Sequential([
                keras.layers.Conv1D(64, 3, activation='relu', input_shape=(X.shape[1], 1)),
                keras.layers.MaxPooling1D(2),
                keras.layers.Conv1D(32, 3, activation='relu'),
                keras.layers.GlobalAveragePooling1D(),
                keras.layers.Dense(16, activation='relu'),
                keras.layers.Dense(3, activation='softmax')
            ])

            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

            # Train
            model.fit(X_reshaped, y, epochs=30, batch_size=32, validation_split=0.2, verbose=0)

            # Save
            model.save(self.models_path / "cnn_embedder.h5")

            logger.info("âœ… CNN trained and saved")
            return {'status': 'success'}

        except Exception as e:
            logger.error(f"âŒ CNN training failed: {e}")
            return None

    def train_lstm_sequence(self, X, y):
        """Train LSTM for sequence modeling"""
        logger.info("\nðŸ§  Training LSTM/RNN...")

        try:
            import tensorflow as tf
            from tensorflow import keras

            # Reshape for LSTM (add time steps)
            X_reshaped = X.reshape(X.shape[0], X.shape[1], 1)

            # Build LSTM
            model = keras.Sequential([
                keras.layers.LSTM(64, return_sequences=True, input_shape=(X.shape[1], 1)),
                keras.layers.Dropout(0.2),
                keras.layers.LSTM(32),
                keras.layers.Dense(16, activation='relu'),
                keras.layers.Dense(3, activation='softmax')
            ])

            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

            # Train
            model.fit(X_reshaped, y, epochs=30, batch_size=32, validation_split=0.2, verbose=0)

            # Save
            model.save(self.models_path / "lstm_sequence.h5")

            logger.info("âœ… LSTM trained and saved")
            return {'status': 'success'}

        except Exception as e:
            logger.error(f"âŒ LSTM training failed: {e}")
            return None

    def train_transformer_encoder(self, X, y):
        """Train Transformer encoder"""
        logger.info("\nðŸ§  Training Transformer Encoder...")

        try:
            import tensorflow as tf
            from tensorflow import keras

            # Simple transformer-inspired architecture
            model = keras.Sequential([
                keras.layers.Dense(128, activation='relu', input_shape=(X.shape[1],)),
                keras.layers.LayerNormalization(),
                keras.layers.Dense(64, activation='relu'),
                keras.layers.LayerNormalization(),
                keras.layers.Dense(32, activation='relu'),
                keras.layers.Dense(3, activation='softmax')
            ])

            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

            # Train
            model.fit(X, y, epochs=30, batch_size=32, validation_split=0.2, verbose=0)

            # Save
            model.save(self.models_path / "transformer_encoder.h5")

            logger.info("âœ… Transformer encoder trained and saved")
            return {'status': 'success'}

        except Exception as e:
            logger.error(f"âŒ Transformer training failed: {e}")
            return None

    def train_autoencoder(self, X):
        """Train Autoencoder for dimensionality reduction"""
        logger.info("\nðŸ§  Training Autoencoder...")

        try:
            import tensorflow as tf
            from tensorflow import keras
            from sklearn.preprocessing import StandardScaler

            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Build autoencoder
            encoding_dim = 3

            encoder = keras.Sequential([
                keras.layers.Dense(64, activation='relu', input_shape=(X.shape[1],)),
                keras.layers.Dense(32, activation='relu'),
                keras.layers.Dense(encoding_dim, activation='relu')
            ])

            decoder = keras.Sequential([
                keras.layers.Dense(32, activation='relu', input_shape=(encoding_dim,)),
                keras.layers.Dense(64, activation='relu'),
                keras.layers.Dense(X.shape[1], activation='sigmoid')
            ])

            autoencoder = keras.Sequential([encoder, decoder])
            autoencoder.compile(optimizer='adam', loss='mse')

            # Train
            autoencoder.fit(X_scaled, X_scaled, epochs=50, batch_size=32, validation_split=0.2, verbose=0)

            # Save
            autoencoder.save(self.models_path / "autoencoder.h5")

            import joblib
            joblib.dump(scaler, self.models_path / "autoencoder_scaler.pkl")

            logger.info("âœ… Autoencoder trained and saved")
            return {'status': 'success'}

        except Exception as e:
            logger.error(f"âŒ Autoencoder training failed: {e}")
            return None

    def train_all_architectures(self):
        """Train all neural network architectures"""
        logger.info("\n" + "="*60)
        logger.info("NEURAL NETWORK TRAINING - ALL ARCHITECTURES")
        logger.info("="*60)

        # Load data
        profiles = self.load_training_data()
        if not profiles:
            logger.error("No training data available")
            return {}

        # Prepare features
        X, y = self.prepare_features(profiles)

        results = {}

        # Train each architecture
        results['dnn'] = self.train_dnn_classifier(X, y)
        results['cnn'] = self.train_cnn_embedder(X, y)
        results['lstm'] = self.train_lstm_sequence(X, y)
        results['transformer'] = self.train_transformer_encoder(X, y)
        results['autoencoder'] = self.train_autoencoder(X)

        # Summary
        logger.info("\n" + "="*60)
        logger.info("NEURAL NETWORK TRAINING COMPLETE")
        logger.info("="*60)
        for name, result in results.items():
            status = "âœ…" if result else "âŒ"
            logger.info(f"{status} {name.upper()}")

        return results


if __name__ == "__main__":
    trainer = NeuralNetworkTrainer(str(Path(__file__).parent))
    results = trainer.train_all_architectures()

