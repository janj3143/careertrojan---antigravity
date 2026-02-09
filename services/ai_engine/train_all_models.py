"""
AI Model Training Pipeline for IntelliCV Platform
==================================================

This script trains all AI models on your 328k CV records:
1. Bayesian Classifier (sklearn) - Job categorization
2. TF-IDF Vectorizer - Text feature extraction
3. Sentence-BERT Embeddings - Semantic similarity
4. Statistical Models - Salary/experience prediction

Usage:
    python train_all_models.py

Output:
    - admin_portal/models/*.pkl (trained model files)
    - training_report.json (performance metrics)
"""

import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, r2_score

# Sentence Transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("⚠️  spaCy not installed. Install with: pip install spacy")
    SPACY_AVAILABLE = False


class IntelliCVModelTrainer:
    """Complete AI model training pipeline"""

    def __init__(self, data_dir: str = "ai_data_final"):
        self.data_dir = Path(data_dir)
        self.models_dir = Path("admin_portal/models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.training_report = {
            'timestamp': datetime.now().isoformat(),
            'data_stats': {},
            'model_performance': {},
            'files_created': []
        }

        print("\n" + "="*70)
        print("🤖 IntelliCV AI Model Training Pipeline")
        print("="*70)

    def load_cv_data(self) -> pd.DataFrame:
        """Load and prepare CV data from JSON files"""
        print("\n📂 Loading CV data...")

        # Try merged database first
        core_db_dir = self.data_dir / "core_databases"
        merged_db = core_db_dir / "Candidate_database_merged.json"

        if merged_db.exists():
            print(f"✅ Found merged database: {merged_db.name}")
            return self._load_from_merged_database(merged_db)

        normalized_dir = self.data_dir / "normalized"

        # Also check for direct profiles (from universal ingestor)
        profile_files = list(self.data_dir.glob("doc_profile_*.json"))

        if not normalized_dir.exists() and not profile_files:
            print(f"❌ Directory not found: {normalized_dir}")
            print("   Checking alternative locations...")

            # Check core databases
            if core_db_dir.exists():
                print(f"✅ Found core databases at: {core_db_dir}")
                return self._load_from_core_databases(core_db_dir)

            raise FileNotFoundError(f"No CV data found in {self.data_dir}")

        cvs = []
        if normalized_dir.exists():
            json_files = list(normalized_dir.glob("*.json"))
        else:
            json_files = profile_files

        print(f"   Found {len(json_files)} JSON files")

        for i, cv_file in enumerate(json_files[:50000]):  # Limit to 50k for speed
            try:
                with open(cv_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle different schemas
                text = data.get('text', data.get('raw_text', ''))

                # Infer job title if missing
                job_title = data.get('job_title', '')
                if not job_title and 'source_file' in data:
                    # Try to guess from filename
                    fname = data['source_file']
                    # Remove extension and common prefixes
                    clean_name = Path(fname).stem.replace('CV', '').replace('Resume', '').replace('_', ' ').strip()
                    job_title = clean_name

                # Extract relevant fields
                cv_record = {
                    'text': text,
                    'job_title': job_title,
                    'skills': data.get('skills', []),
                    'experience_years': data.get('years_experience', 0),
                    'education': data.get('education', ''),
                    'industry': data.get('industry', 'Unknown'),
                    'salary': data.get('salary', None)
                }

                # Only include CVs with meaningful text
                if len(cv_record['text']) > 100:
                    cvs.append(cv_record)

                if (i + 1) % 5000 == 0:
                    print(f"   Processed {i + 1} files...")

            except Exception as e:
                # Skip problematic files
                continue

        df = pd.DataFrame(cvs)

        print(f"\n✅ Loaded {len(df)} CV records")
        print(f"   Average text length: {df['text'].str.len().mean():.0f} chars")

        self.training_report['data_stats'] = {
            'total_records': len(df),
            'avg_text_length': float(df['text'].str.len().mean()),
            'unique_industries': df['industry'].nunique(),
        }

        return df

    def _load_from_merged_database(self, merged_db_path: Path) -> pd.DataFrame:
        """Load data from merged database file"""
        print("   Loading from merged database...")

        with open(merged_db_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)

        print(f"   Found {len(candidates)} candidates in merged database")

        cvs = []
        for candidate in candidates[:50000]:  # Limit for training speed
            # Use _build_cv_text for consistency
            text = self._build_cv_text(candidate)

            # Extract job title from multiple possible fields
            job_title = (candidate.get('Job Title') or
                        candidate.get('current_position') or
                        candidate.get('Position') or
                        candidate.get('name', ''))

            cv_record = {
                'text': text,
                'job_title': job_title,
                'skills': candidate.get('skills', candidate.get('Skills', [])),
                'experience_years': candidate.get('years_experience', candidate.get('experience_years', 0)),
                'education': candidate.get('education', candidate.get('Education', '')),
                'industry': candidate.get('industry', 'Unknown'),
                'salary': candidate.get('salary', candidate.get('expected_salary', None))
            }

            if len(cv_record['text']) > 50:  # Lower threshold for CSV data
                cvs.append(cv_record)

        df = pd.DataFrame(cvs)
        print(f"✅ Loaded {len(df)} records from merged database")

        return df

    def _load_from_core_databases(self, core_db_dir: Path) -> pd.DataFrame:
        """Load data from core database files"""
        print("   Loading from core databases...")

        cvs = []

        # Load candidates
        candidates_file = core_db_dir / "Candidates_database.json"
        if candidates_file.exists():
            with open(candidates_file, 'r', encoding='utf-8') as f:
                candidates = json.load(f)

            # Handle both array and object formats
            if isinstance(candidates, dict):
                candidates = candidates.get('candidates', [])

            print(f"   Found {len(candidates)} candidates")

            for candidate in candidates[:10000]:  # Limit for speed
                cv_record = {
                    'text': self._build_cv_text(candidate),
                    'job_title': candidate.get('current_position', ''),
                    'skills': candidate.get('skills', []),
                    'experience_years': candidate.get('years_experience', 0),
                    'education': candidate.get('education', ''),
                    'industry': candidate.get('industry', 'Unknown'),
                    'salary': candidate.get('expected_salary', None)
                }

                if len(cv_record['text']) > 100:
                    cvs.append(cv_record)

        df = pd.DataFrame(cvs)
        print(f"✅ Loaded {len(df)} records from core databases")

        return df

    def _build_cv_text(self, candidate: dict) -> str:
        """Build searchable text from candidate record (handles multiple schemas)"""
        parts = []

        # Core database schema
        if candidate.get('name'):
            parts.append(candidate['name'])
        if candidate.get('current_position'):
            parts.append(candidate['current_position'])
        if candidate.get('summary'):
            parts.append(candidate['summary'])
        if candidate.get('skills'):
            skills = candidate['skills']
            if isinstance(skills, list):
                parts.append(' '.join(skills))
        if candidate.get('education'):
            parts.append(str(candidate['education']))

        # CSV/merged database schema (capitalized fields)
        if candidate.get('Firstname'):
            parts.append(candidate['Firstname'])
        if candidate.get('Surname'):
            parts.append(candidate['Surname'])
        if candidate.get('Job Title'):
            parts.append(candidate['Job Title'])
        if candidate.get('Company'):
            parts.append(candidate['Company'])
        if candidate.get('Position'):
            parts.append(candidate['Position'])
        if candidate.get('Skills'):
            parts.append(str(candidate['Skills']))

        # MSG/email schema
        if candidate.get('subject'):
            parts.append(candidate['subject'])
        if candidate.get('body'):
            # Limit body to 500 chars to avoid noise
            body_text = candidate['body'][:500] if isinstance(candidate['body'], str) else ''
            parts.append(body_text)

        return ' '.join(parts).strip()

    def _infer_job_category(self, job_title: str, text: str) -> str:
        """Infer job category from title and text"""
        title_lower = job_title.lower()
        text_lower = text.lower()

        # Technology
        if any(word in title_lower for word in ['engineer', 'developer', 'programmer', 'software', 'data scientist', 'devops']):
            return 'Technology'

        # Healthcare
        if any(word in title_lower for word in ['doctor', 'nurse', 'physician', 'medical', 'healthcare']):
            return 'Healthcare'

        # Finance
        if any(word in title_lower for word in ['accountant', 'financial', 'analyst', 'banker', 'investment']):
            return 'Finance'

        # Sales/Marketing
        if any(word in title_lower for word in ['sales', 'marketing', 'business development', 'account manager']):
            return 'Sales & Marketing'

        # Management
        if any(word in title_lower for word in ['manager', 'director', 'executive', 'chief', 'head of']):
            return 'Management'

        # HR
        if any(word in title_lower for word in ['hr', 'human resources', 'recruiter', 'talent']):
            return 'Human Resources'

        # Education
        if any(word in title_lower for word in ['teacher', 'professor', 'instructor', 'educator']):
            return 'Education'

        # Default
        return 'Other'

    def train_bayesian_classifier(self, df: pd.DataFrame) -> Tuple[MultinomialNB, TfidfVectorizer]:
        """Train Bayesian job category classifier"""
        print("\n🧠 Training Bayesian Classifier...")

        # Add categories
        df['category'] = df.apply(
            lambda row: self._infer_job_category(row['job_title'], row['text']),
            axis=1
        )

        # Filter out categories with too few samples
        category_counts = df['category'].value_counts()
        valid_categories = category_counts[category_counts >= 50].index
        df_filtered = df[df['category'].isin(valid_categories)]

        print(f"   Categories: {list(valid_categories)}")
        print(f"   Training samples: {len(df_filtered)}")

        # Vectorize text
        vectorizer = TfidfVectorizer(
            max_features=5000,
            min_df=5,
            max_df=0.8,
            stop_words='english',
            ngram_range=(1, 2)
        )

        X = vectorizer.fit_transform(df_filtered['text'])
        y = df_filtered['category']

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train model
        model = MultinomialNB(alpha=0.1)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"\n   ✅ Accuracy: {accuracy:.2%}")
        print(f"   Training samples: {X_train.shape[0]}")
        print(f"   Test samples: {X_test.shape[0]}")

        # Save models
        model_file = self.models_dir / "bayesian_classifier.pkl"
        vectorizer_file = self.models_dir / "tfidf_vectorizer.pkl"

        pickle.dump(model, open(model_file, 'wb'))
        pickle.dump(vectorizer, open(vectorizer_file, 'wb'))

        print(f"   💾 Saved: {model_file.name}")
        print(f"   💾 Saved: {vectorizer_file.name}")

        self.training_report['model_performance']['bayesian_classifier'] = {
            'accuracy': float(accuracy),
            'training_samples': int(X_train.shape[0]),
            'test_samples': int(X_test.shape[0]),
            'categories': list(valid_categories),
            'model_file': str(model_file),
            'vectorizer_file': str(vectorizer_file)
        }

        self.training_report['files_created'].extend([
            str(model_file),
            str(vectorizer_file)
        ])

        return model, vectorizer

    def setup_sentence_embeddings(self):
        """Download and test Sentence-BERT model"""
        print("\n🔤 Setting up Sentence Embeddings...")

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("   ❌ sentence-transformers not available")
            return None

        try:
            # Load pre-trained model (auto-downloads if needed)
            model = SentenceTransformer('all-MiniLM-L6-v2')

            # Test embedding
            test_text = "Senior Python Developer with 5 years experience"
            embedding = model.encode(test_text)

            print(f"   ✅ Model loaded: all-MiniLM-L6-v2")
            print(f"   Embedding dimension: {len(embedding)}")
            print(f"   Sample embedding: {embedding[:5]}")

            # Save model info
            model_info = {
                'model_name': 'all-MiniLM-L6-v2',
                'embedding_dim': int(len(embedding)),
                'provider': 'sentence-transformers',
                'installed': True
            }

            info_file = self.models_dir / "sentence_bert_info.json"
            with open(info_file, 'w') as f:
                json.dump(model_info, f, indent=2)

            print(f"   💾 Saved: {info_file.name}")

            self.training_report['model_performance']['sentence_embeddings'] = model_info
            self.training_report['files_created'].append(str(info_file))

            return model

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def setup_spacy_model(self):
        """Download and test spaCy model"""
        print("\n📝 Setting up spaCy NER Model...")

        if not SPACY_AVAILABLE:
            print("   ❌ spaCy not available")
            print("   Install with: pip install spacy")
            print("   Then run: python -m spacy download en_core_web_sm")
            return None

        try:
            # Try to load model
            nlp = spacy.load("en_core_web_sm")

            # Test entity extraction
            test_text = "John Smith worked as Senior Python Developer at Google for 5 years"
            doc = nlp(test_text)

            entities = [(ent.text, ent.label_) for ent in doc.ents]

            print(f"   ✅ Model loaded: en_core_web_sm")
            print(f"   Test entities: {entities}")

            # Save model info
            model_info = {
                'model_name': 'en_core_web_sm',
                'version': nlp.meta.get('version', 'unknown'),
                'installed': True,
                'test_entities': entities
            }

            info_file = self.models_dir / "spacy_model_info.json"
            with open(info_file, 'w') as f:
                json.dump(model_info, f, indent=2)

            print(f"   💾 Saved: {info_file.name}")

            self.training_report['model_performance']['spacy_ner'] = model_info
            self.training_report['files_created'].append(str(info_file))

            return nlp

        except OSError:
            print("   ⚠️  spaCy model not downloaded")
            print("   Run: python -m spacy download en_core_web_sm")

            model_info = {
                'model_name': 'en_core_web_sm',
                'installed': False,
                'download_command': 'python -m spacy download en_core_web_sm'
            }

            info_file = self.models_dir / "spacy_model_info.json"
            with open(info_file, 'w') as f:
                json.dump(model_info, f, indent=2)

            self.training_report['model_performance']['spacy_ner'] = model_info

            return None

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def train_statistical_models(self, df: pd.DataFrame):
        """Train regression models for salary/experience prediction"""
        print("\n📊 Training Statistical Models...")

        # Filter data with valid salary and experience
        df_valid = df[
            (df['salary'].notna()) &
            (df['experience_years'] > 0) &
            (df['experience_years'] < 50)
        ].copy()

        if len(df_valid) < 100:
            print("   ⚠️  Not enough data for statistical models")
            print(f"   Need salary data (found {len(df_valid)} records)")
            return None

        print(f"   Training samples: {len(df_valid)}")

        # Features
        df_valid['skills_count'] = df_valid['skills'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
        df_valid['text_length'] = df_valid['text'].str.len()

        # Encode education level
        education_map = {
            'High School': 1,
            'Associate': 2,
            'Bachelor': 3,
            'Master': 4,
            'PhD': 5
        }
        df_valid['education_level'] = df_valid['education'].map(
            lambda x: education_map.get(x, 3)
        )

        X = df_valid[['experience_years', 'skills_count', 'education_level', 'text_length']]
        y = df_valid['salary']

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Train Random Forest
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)

        print(f"   ✅ R² Score: {r2:.3f}")

        # Save model
        model_file = self.models_dir / "salary_predictor.pkl"
        pickle.dump(model, open(model_file, 'wb'))

        print(f"   💾 Saved: {model_file.name}")

        self.training_report['model_performance']['salary_predictor'] = {
            'r2_score': float(r2),
            'training_samples': int(len(X_train)),
            'test_samples': int(len(X_test)),
            'model_file': str(model_file)
        }

        self.training_report['files_created'].append(str(model_file))

        return model

    def generate_report(self):
        """Generate training report"""
        report_file = Path("training_report.json")

        with open(report_file, 'w') as f:
            json.dump(self.training_report, f, indent=2)

        print("\n" + "="*70)
        print("📋 Training Report")
        print("="*70)

        print(f"\n📊 Data Statistics:")
        for key, value in self.training_report['data_stats'].items():
            print(f"   {key}: {value}")

        print(f"\n🎯 Model Performance:")
        for model_name, metrics in self.training_report['model_performance'].items():
            print(f"\n   {model_name}:")
            for metric, value in metrics.items():
                if metric not in ['model_file', 'vectorizer_file', 'test_entities', 'download_command']:
                    print(f"      {metric}: {value}")

        print(f"\n💾 Files Created ({len(self.training_report['files_created'])}):")
        for file_path in self.training_report['files_created']:
            print(f"   ✅ {file_path}")

        print(f"\n📄 Full report saved: {report_file}")
        print("="*70 + "\n")

    def run_full_training(self):
        """Execute complete training pipeline"""
        try:
            # Load data
            df = self.load_cv_data()

            # Train models
            self.train_bayesian_classifier(df)
            self.setup_sentence_embeddings()
            self.setup_spacy_model()
            self.train_statistical_models(df)

            # Generate report
            self.generate_report()

            print("\n✅ Training complete!")
            print("\n📌 Next Steps:")
            print("   1. Run: python update_ai_engines.py")
            print("   2. Run: python test_real_ai.py")
            print("   3. Launch admin portal to see real AI in action!")

            return True

        except Exception as e:
            print(f"\n❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    trainer = IntelliCVModelTrainer()
    success = trainer.run_full_training()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
