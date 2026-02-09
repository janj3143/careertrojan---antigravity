"""
Zero-Cost Feature Engineering for IntelliCV
Integrates with Hybrid AI Engine for ML-ready features
Uses: scikit-learn (free)
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from typing import Dict, List, Any, Optional, Tuple
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ZeroCostFeatureBuilder:
    """
    Free feature engineering for resume/job matching.
    No cloud ML services - pure scikit-learn transformations.
    """

    def __init__(self):
        """Initialize feature builder with transformers."""
        self.scaler = StandardScaler()
        self.min_max_scaler = MinMaxScaler()
        self.label_encoders = {}
        self.tfidf = TfidfVectorizer(max_features=100, stop_words='english')
        self.count_vectorizer = CountVectorizer(max_features=50, stop_words='english')

        logger.info("🔧 Feature Builder initialized")

    # ========== CANDIDATE FEATURES ==========

    def build_candidate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from candidate data (FREE).

        Args:
            df: Candidate DataFrame

        Returns:
            DataFrame with engineered features
        """
        if df.empty:
            logger.warning("⚠️ Empty DataFrame provided")
            return df

        features = df.copy()
        logger.info(f"🔧 Building features for {len(df)} candidates")

        # Numerical features
        if 'years_experience' in df.columns:
            features['years_experience_log'] = np.log1p(df['years_experience'].fillna(0))
            features['experience_squared'] = df['years_experience'].fillna(0) ** 2
            features['experience_category'] = pd.cut(
                df['years_experience'].fillna(0),
                bins=[0, 2, 5, 10, 100],
                labels=['Entry', 'Mid', 'Senior', 'Expert']
            )

        # Skills count
        if 'skills' in df.columns:
            features['skills_count'] = df['skills'].apply(
                lambda x: len(x) if isinstance(x, (list, set)) else 0
            )
            features['skills_diversity'] = df['skills'].apply(
                lambda x: len(set(x)) if isinstance(x, (list, set)) else 0
            )

        # Education scoring
        if 'education' in df.columns:
            education_map = {
                'PhD': 4,
                'Doctorate': 4,
                'Masters': 3,
                'Master': 3,
                'Bachelors': 2,
                'Bachelor': 2,
                'Associates': 1,
                'High School': 0,
                'Diploma': 0
            }
            features['education_score'] = df['education'].map(education_map).fillna(0)

        # Location features
        if 'location' in df.columns:
            features = self._encode_categorical(features, 'location', 'location')

        # Industry features
        if 'industry' in df.columns:
            features = self._encode_categorical(features, 'industry', 'industry')

        # Job title features
        if 'job_title' in df.columns:
            features = self._encode_categorical(features, 'job_title', 'job_title')

        # Text features from resume
        if 'resume_text' in df.columns:
            features = self._extract_text_features(features, 'resume_text', 'resume')

        # Salary expectations
        if 'salary_expectation' in df.columns:
            features['salary_log'] = np.log1p(df['salary_expectation'].fillna(0))
            features['salary_normalized'] = self.min_max_scaler.fit_transform(
                df[['salary_expectation']].fillna(0)
            )

        logger.info(f"✅ Built {len(features.columns)} features")
        return features

    def build_job_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from job posting data (FREE).

        Args:
            df: Job posting DataFrame

        Returns:
            DataFrame with engineered features
        """
        if df.empty:
            logger.warning("⚠️ Empty DataFrame provided")
            return df

        features = df.copy()
        logger.info(f"🔧 Building features for {len(df)} jobs")

        # Required experience
        if 'min_experience' in df.columns:
            features['experience_req_log'] = np.log1p(df['min_experience'].fillna(0))

        # Salary range features
        if 'salary_min' in df.columns and 'salary_max' in df.columns:
            features['salary_range'] = df['salary_max'].fillna(0) - df['salary_min'].fillna(0)
            features['salary_midpoint'] = (df['salary_min'].fillna(0) + df['salary_max'].fillna(0)) / 2
            features['salary_midpoint_log'] = np.log1p(features['salary_midpoint'])

        # Required skills count
        if 'required_skills' in df.columns:
            features['required_skills_count'] = df['required_skills'].apply(
                lambda x: len(x) if isinstance(x, (list, set)) else 0
            )

        # Job description text features
        if 'description' in df.columns:
            features = self._extract_text_features(features, 'description', 'job_desc')

        # Company features
        if 'company' in df.columns:
            features = self._encode_categorical(features, 'company', 'company')

        # Location features
        if 'location' in df.columns:
            features = self._encode_categorical(features, 'location', 'job_location')

        # Remote/hybrid flags
        if 'remote_type' in df.columns:
            features['is_remote'] = (df['remote_type'] == 'Remote').astype(int)
            features['is_hybrid'] = (df['remote_type'] == 'Hybrid').astype(int)

        logger.info(f"✅ Built {len(features.columns)} features")
        return features

    # ========== MATCHING FEATURES ==========

    def calculate_match_score(self, candidate_features: pd.Series,
                              job_requirements: Dict[str, Any]) -> float:
        """
        Simple matching algorithm (FREE - no ML inference costs).

        Args:
            candidate_features: Candidate feature series
            job_requirements: Job requirements dictionary

        Returns:
            Match score (0-100)
        """
        score = 0.0

        # Skills match (40 points)
        candidate_skills = set(candidate_features.get('skills', []))
        required_skills = set(job_requirements.get('required_skills', []))

        if required_skills:
            skill_match = len(candidate_skills & required_skills) / len(required_skills)
            score += skill_match * 40
        else:
            score += 20  # No requirements = partial credit

        # Experience match (30 points)
        exp_required = job_requirements.get('min_experience', 0)
        exp_candidate = candidate_features.get('years_experience', 0)

        if exp_candidate >= exp_required:
            score += 30
        elif exp_candidate >= exp_required * 0.75:
            score += 20  # Close match
        elif exp_candidate >= exp_required * 0.5:
            score += 10  # Partial match

        # Education match (20 points)
        education_map = {'PhD': 4, 'Masters': 3, 'Bachelors': 2, 'Associates': 1, 'High School': 0}

        candidate_edu = education_map.get(candidate_features.get('education', 'High School'), 0)
        required_edu = education_map.get(job_requirements.get('min_education', 'Bachelors'), 2)

        if candidate_edu >= required_edu:
            score += 20
        elif candidate_edu >= required_edu - 1:
            score += 10  # One level below

        # Location match (10 points)
        if 'location' in candidate_features and 'location' in job_requirements:
            if candidate_features['location'] == job_requirements['location']:
                score += 10
            elif job_requirements.get('remote', False):
                score += 10  # Remote jobs match any location

        match_score = min(score, 100.0)
        logger.info(f"🎯 Match score calculated: {match_score:.2f}")

        return match_score

    def batch_calculate_matches(self, candidates_df: pd.DataFrame,
                               jobs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate match scores for all candidate-job pairs.

        Args:
            candidates_df: DataFrame of candidates with features
            jobs_df: DataFrame of jobs with requirements

        Returns:
            DataFrame with match scores
        """
        logger.info(f"🎯 Calculating matches: {len(candidates_df)} candidates x {len(jobs_df)} jobs")

        matches = []

        for _, candidate in candidates_df.iterrows():
            for _, job in jobs_df.iterrows():
                job_reqs = job.to_dict()
                score = self.calculate_match_score(candidate, job_reqs)

                matches.append({
                    'candidate_id': candidate.get('id', candidate.name),
                    'job_id': job.get('id', job.name),
                    'match_score': score,
                    'candidate_name': candidate.get('name', 'Unknown'),
                    'job_title': job.get('title', 'Unknown'),
                    'company': job.get('company', 'Unknown')
                })

        matches_df = pd.DataFrame(matches)
        logger.info(f"✅ Calculated {len(matches_df)} matches")

        return matches_df

    # ========== HELPER METHODS ==========

    def _encode_categorical(self, df: pd.DataFrame, column: str,
                           encoder_name: str) -> pd.DataFrame:
        """
        Encode categorical variable using LabelEncoder.

        Args:
            df: DataFrame
            column: Column to encode
            encoder_name: Name for the encoder

        Returns:
            DataFrame with encoded column
        """
        if column not in df.columns:
            return df

        try:
            if encoder_name not in self.label_encoders:
                self.label_encoders[encoder_name] = LabelEncoder()

            # Fill NaN before encoding
            df_copy = df.copy()
            df_copy[column] = df_copy[column].fillna('Unknown')

            df_copy[f'{column}_encoded'] = self.label_encoders[encoder_name].fit_transform(
                df_copy[column].astype(str)
            )

            return df_copy

        except Exception as e:
            logger.warning(f"⚠️ Could not encode {column}: {e}")
            return df

    def _extract_text_features(self, df: pd.DataFrame, text_column: str,
                               prefix: str) -> pd.DataFrame:
        """
        Extract TF-IDF features from text column.

        Args:
            df: DataFrame
            text_column: Column containing text
            prefix: Prefix for feature names

        Returns:
            DataFrame with text features
        """
        if text_column not in df.columns:
            return df

        try:
            # Fill NaN and convert to string
            text_data = df[text_column].fillna('').astype(str)

            # TF-IDF features
            tfidf_matrix = self.tfidf.fit_transform(text_data)
            tfidf_df = pd.DataFrame(
                tfidf_matrix.toarray(),
                columns=[f'{prefix}_tfidf_{i}' for i in range(tfidf_matrix.shape[1])],
                index=df.index
            )

            # Basic text statistics
            df_copy = df.copy()
            df_copy[f'{prefix}_word_count'] = text_data.str.split().str.len()
            df_copy[f'{prefix}_char_count'] = text_data.str.len()
            df_copy[f'{prefix}_avg_word_length'] = (
                df_copy[f'{prefix}_char_count'] / df_copy[f'{prefix}_word_count']
            ).fillna(0)

            # Combine with TF-IDF features
            df_combined = pd.concat([df_copy, tfidf_df], axis=1)

            return df_combined

        except Exception as e:
            logger.warning(f"⚠️ Could not extract text features from {text_column}: {e}")
            return df

    # ========== FEATURE IMPORTANCE ==========

    def calculate_feature_importance(self, X: pd.DataFrame, y: pd.Series,
                                    method: str = 'correlation') -> Dict[str, float]:
        """
        Calculate feature importance using correlation or mutual information.

        Args:
            X: Feature DataFrame
            y: Target variable
            method: 'correlation' or 'mutual_info'

        Returns:
            Dictionary of feature importances
        """
        if method == 'correlation':
            # Correlation with target
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            importance = correlations.to_dict()

        elif method == 'mutual_info':
            from sklearn.feature_selection import mutual_info_regression

            # Mutual information
            mi_scores = mutual_info_regression(X, y)
            importance = dict(zip(X.columns, mi_scores))

        else:
            raise ValueError(f"Unknown method: {method}")

        logger.info(f"📊 Feature importance calculated using {method}")
        return importance

    # ========== SCALING ==========

    def scale_features(self, df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
        """
        Scale numeric features.

        Args:
            df: DataFrame with features
            method: 'standard' (z-score) or 'minmax' (0-1)

        Returns:
            DataFrame with scaled features
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) == 0:
            logger.warning("⚠️ No numeric columns to scale")
            return df

        df_scaled = df.copy()

        if method == 'standard':
            df_scaled[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
        elif method == 'minmax':
            df_scaled[numeric_cols] = self.min_max_scaler.fit_transform(df[numeric_cols])
        else:
            raise ValueError(f"Unknown scaling method: {method}")

        logger.info(f"📏 Scaled {len(numeric_cols)} features using {method}")
        return df_scaled

    # ========== PERSISTENCE ==========

    def save_transformers(self, filepath: Path) -> None:
        """Save all fitted transformers for later use."""
        import pickle

        transformers = {
            'scaler': self.scaler,
            'min_max_scaler': self.min_max_scaler,
            'label_encoders': self.label_encoders,
            'tfidf': self.tfidf,
            'count_vectorizer': self.count_vectorizer
        }

        with open(filepath, 'wb') as f:
            pickle.dump(transformers, f)

        logger.info(f"💾 Saved transformers to {filepath}")

    def load_transformers(self, filepath: Path) -> None:
        """Load previously fitted transformers."""
        import pickle

        with open(filepath, 'rb') as f:
            transformers = pickle.load(f)

        self.scaler = transformers['scaler']
        self.min_max_scaler = transformers['min_max_scaler']
        self.label_encoders = transformers['label_encoders']
        self.tfidf = transformers['tfidf']
        self.count_vectorizer = transformers['count_vectorizer']

        logger.info(f"📂 Loaded transformers from {filepath}")


# Singleton instance
_builder_instance = None


def get_feature_builder() -> ZeroCostFeatureBuilder:
    """Get or create the singleton feature builder instance."""
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = ZeroCostFeatureBuilder()
    return _builder_instance
