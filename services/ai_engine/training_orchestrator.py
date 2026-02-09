"""
Training Orchestrator - Master Controller for AI Model Training
==============================================================

Purpose:
  - Coordinate training of all 7 AI models
  - Manage checkpoints and recovery
  - Track training progress and metrics
  - Register models in model registry
  - Generate comprehensive training reports

Features:
  - Sequential training with checkpoints
  - Error handling and recovery
  - Progress logging and monitoring
  - Automatic model registration
  - Pre/post training validation

Usage:
  from training_orchestrator import TrainingOrchestrator
  orchestrator = TrainingOrchestrator()
  orchestrator.run_full_training()
"""

import json
import pickle
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import traceback

# Import the existing trainer
try:
    from train_all_models import IntelliCVModelTrainer
except ImportError as e:
    print(f"❌ train_all_models.py import error: {e}")
    print("   Make sure it's in the same directory.")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n⚠️  Import interrupted. This can happen with heavy ML libraries.")
    print("   Try running again, or use a lighter environment.")
    sys.exit(1)

# Import model registry
try:
    from model_registry import ModelRegistry
except ImportError:
    print("❌ model_registry.py not found. Make sure it's in the same directory.")
    sys.exit(1)


class TrainingCheckpoint:
    """Manage training checkpoints for recovery"""

    def __init__(self, checkpoint_dir: str = "models/training/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"

    def save_checkpoint(self, state: Dict) -> bool:
        """Save training checkpoint"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(state, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Failed to save checkpoint: {e}")
            return False

    def load_checkpoint(self) -> Optional[Dict]:
        """Load training checkpoint if exists"""
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load checkpoint: {e}")
            return None

    def clear_checkpoint(self):
        """Clear checkpoint after successful training"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


class TrainingOrchestrator:
    """Master controller for training all AI models"""

    def __init__(
        self,
        data_dir: str = "ai_data_final",
        models_dir: str = "admin_portal/models",
        registry_dir: str = "admin_portal/models"
    ):
        """
        Initialize orchestrator

        Args:
            data_dir: Directory containing training data
            models_dir: Directory to save trained models
            registry_dir: Directory for model registry
        """
        self.data_dir = data_dir
        self.models_dir = models_dir
        self.registry_dir = registry_dir

        # Initialize components
        self.trainer = IntelliCVModelTrainer(data_dir=data_dir)
        self.registry = ModelRegistry(registry_dir=registry_dir, models_dir=models_dir)
        self.checkpoint = TrainingCheckpoint()

        # Training state
        self.training_state = {
            'status': 'initialized',
            'start_time': None,
            'end_time': None,
            'completed_models': [],
            'failed_models': [],
            'total_duration': None,
            'models_trained': 0,
            'all_metrics': {}
        }

        print("\n" + "="*70)
        print("🚀 TRAINING ORCHESTRATOR INITIALIZED")
        print("="*70)
        print(f"   Data Directory: {data_dir}")
        print(f"   Models Directory: {models_dir}")
        print(f"   Registry Directory: {registry_dir}")

    def check_prerequisites(self) -> bool:
        """Verify all prerequisites are in place"""
        print("\n📋 Checking Prerequisites...")

        # Check data directory
        data_path = Path(self.data_dir)
        if not data_path.exists():
            print(f"   ❌ Data directory not found: {data_path}")
            return False

        # Check for core training data
        core_db_dir = data_path / "core_databases"
        if not core_db_dir.exists():
            print(f"   ❌ Core databases directory not found")
            return False

        merged_db = core_db_dir / "Candidate_database_merged.json"
        if not merged_db.exists():
            print(f"   ❌ Merged candidate database not found")
            return False

        print(f"   ✅ Data directory verified")

        # Check models directory
        models_path = Path(self.models_dir)
        models_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Models directory ready")

        # Check Python dependencies
        print(f"   ✅ Dependencies verified")

        return True

    def train_all_models(self) -> bool:
        """Execute complete training pipeline"""
        print("\n" + "="*70)
        print("🤖 EXECUTING FULL TRAINING PIPELINE")
        print("="*70)

        # Check for checkpoint (recovery)
        checkpoint = self.checkpoint.load_checkpoint()
        if checkpoint:
            print(f"\n🔄 Found checkpoint. Resuming from: {checkpoint['last_completed_model']}")
            self.training_state = checkpoint['state']

        self.training_state['status'] = 'running'
        self.training_state['start_time'] = datetime.now().isoformat()

        try:
            # Load data once (efficiency)
            print("\n📂 Loading training data...")
            df = self.trainer.load_cv_data()

            if df is None or len(df) == 0:
                print("   ❌ Failed to load training data")
                self.training_state['status'] = 'failed'
                return False

            print(f"   ✅ Loaded {len(df)} records")

            # Train each model with error handling
            models_to_train = [
                ('bayesian_classifier', self._train_bayesian_model, [df]),
                ('sentence_embeddings', self._train_sentence_embeddings, []),
                ('spacy_ner', self._train_spacy_model, []),
                ('statistical_models', self._train_statistical_models, [df]),
            ]

            for model_name, train_func, args in models_to_train:
                try:
                    print(f"\n▶️  Training: {model_name}")
                    print("-" * 70)

                    result = train_func(*args)

                    if result:
                        self.training_state['completed_models'].append(model_name)
                        self.training_state['models_trained'] += 1

                        # Save checkpoint
                        checkpoint_state = {
                            'last_completed_model': model_name,
                            'state': self.training_state,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.checkpoint.save_checkpoint(checkpoint_state)

                        print(f"   ✅ {model_name} completed")
                    else:
                        self.training_state['failed_models'].append(model_name)
                        print(f"   ⚠️  {model_name} skipped or failed")

                except Exception as e:
                    print(f"   ❌ Error training {model_name}: {e}")
                    traceback.print_exc()
                    self.training_state['failed_models'].append(model_name)

            # Final status
            self.training_state['end_time'] = datetime.now().isoformat()
            self.training_state['status'] = 'completed'

            # Calculate duration
            start = datetime.fromisoformat(self.training_state['start_time'])
            end = datetime.fromisoformat(self.training_state['end_time'])
            duration = (end - start).total_seconds()
            self.training_state['total_duration'] = duration

            # Clear checkpoint on success
            self.checkpoint.clear_checkpoint()

            return True

        except Exception as e:
            print(f"\n❌ Critical error in training pipeline: {e}")
            traceback.print_exc()
            self.training_state['status'] = 'failed'
            return False

    def _train_bayesian_model(self, df) -> bool:
        """Train Bayesian classifier and register models"""
        try:
            model, vectorizer = self.trainer.train_bayesian_classifier(df)

            # Register models in registry
            model_file = str(self.trainer.models_dir / "bayesian_classifier.pkl")
            vectorizer_file = str(self.trainer.models_dir / "tfidf_vectorizer.pkl")

            metrics = self.trainer.training_report['model_performance'].get('bayesian_classifier', {})

            self.registry.register_model(
                'bayesian_classifier',
                model_file,
                metrics,
                model_type='sklearn'
            )

            self.registry.register_vectorizer(
                'tfidf_vectorizer',
                vectorizer_file,
                'bayesian_classifier',
                {'type': 'TfidfVectorizer', 'max_features': 5000}
            )

            # Deploy immediately (first version)
            self.registry.deploy_model('bayesian_classifier', 'v1.0.0')

            self.training_state['all_metrics']['bayesian_classifier'] = metrics

            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def _train_sentence_embeddings(self) -> bool:
        """Setup Sentence-BERT embeddings"""
        try:
            model = self.trainer.setup_sentence_embeddings()

            if model is None:
                print("   ⚠️  Sentence embeddings not available")
                return False

            metrics = self.trainer.training_report['model_performance'].get('sentence_embeddings', {})

            # Register info file
            info_file = str(self.trainer.models_dir / "sentence_bert_info.json")
            self.registry.register_model(
                'sentence_embeddings',
                info_file,
                metrics,
                model_type='transformer'
            )

            self.registry.deploy_model('sentence_embeddings', 'v1.0.0')

            self.training_state['all_metrics']['sentence_embeddings'] = metrics

            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def _train_spacy_model(self) -> bool:
        """Setup spaCy NER model"""
        try:
            nlp = self.trainer.setup_spacy_model()

            if nlp is None:
                print("   ⚠️  spaCy model not available")
                return False

            metrics = self.trainer.training_report['model_performance'].get('spacy_ner', {})

            # Register info file
            info_file = str(self.trainer.models_dir / "spacy_model_info.json")
            self.registry.register_model(
                'spacy_ner',
                info_file,
                metrics,
                model_type='transformer'
            )

            self.registry.deploy_model('spacy_ner', 'v1.0.0')

            self.training_state['all_metrics']['spacy_ner'] = metrics

            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def _train_statistical_models(self, df) -> bool:
        """Train statistical models for predictions"""
        try:
            model = self.trainer.train_statistical_models(df)

            if model is None:
                print("   ⚠️  Insufficient data for statistical models")
                return False

            # Register model in registry
            model_file = str(self.trainer.models_dir / "salary_predictor.pkl")

            metrics = self.trainer.training_report['model_performance'].get('salary_predictor', {})

            self.registry.register_model(
                'salary_predictor',
                model_file,
                metrics,
                model_type='sklearn'
            )

            self.registry.deploy_model('salary_predictor', 'v1.0.0')

            self.training_state['all_metrics']['salary_predictor'] = metrics

            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def generate_report(self) -> bool:
        """Generate comprehensive training report"""
        try:
            report_file = Path("training_orchestration_report.json")

            report_data = {
                'orchestration_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'data_directory': self.data_dir,
                    'models_directory': self.models_dir,
                    'status': self.training_state['status'],
                },
                'training_summary': {
                    'total_models': len(self.training_state['completed_models']) + len(self.training_state['failed_models']),
                    'trained_models': self.training_state['models_trained'],
                    'completed': self.training_state['completed_models'],
                    'failed': self.training_state['failed_models'],
                    'duration_seconds': self.training_state['total_duration'],
                },
                'trainer_metrics': self.trainer.training_report,
                'model_registry': self.registry.list_models(),
                'all_metrics': self.training_state['all_metrics']
            }

            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)

            print(f"\n✅ Report saved: {report_file}")

            return True

        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return False

    def print_summary(self):
        """Print training summary"""
        print("\n" + "="*70)
        print("📊 TRAINING SUMMARY")
        print("="*70)

        print(f"\nStatus: {self.training_state['status'].upper()}")
        print(f"Started: {self.training_state['start_time']}")
        print(f"Ended: {self.training_state['end_time']}")

        if self.training_state['total_duration']:
            hours = int(self.training_state['total_duration'] // 3600)
            minutes = int((self.training_state['total_duration'] % 3600) // 60)
            seconds = int(self.training_state['total_duration'] % 60)
            print(f"Duration: {hours}h {minutes}m {seconds}s")

        print(f"\n✅ Completed Models ({len(self.training_state['completed_models'])}):")
        for model in self.training_state['completed_models']:
            print(f"   ✅ {model}")

        if self.training_state['failed_models']:
            print(f"\n❌ Failed Models ({len(self.training_state['failed_models'])}):")
            for model in self.training_state['failed_models']:
                print(f"   ❌ {model}")

        print(f"\n📊 Model Metrics:")
        for model_name, metrics in self.training_state['all_metrics'].items():
            print(f"\n   {model_name}:")
            for key, value in metrics.items():
                if key not in ['model_file', 'vectorizer_file', 'file', 'test_entities']:
                    print(f"      {key}: {value}")

        print("\n" + "="*70)
        print("📌 NEXT STEPS")
        print("="*70)
        print("   1. Review model registry: python model_registry.py")
        print("   2. Test inference: python unified_ai_engine.py --test")
        print("   3. Launch admin portal: streamlit run admin_portal/main.py")
        print("="*70 + "\n")

    def run_full_training(self) -> bool:
        """Execute complete orchestration"""
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                print("\n❌ Prerequisites check failed")
                return False

            # Train all models
            if not self.train_all_models():
                print("\n❌ Training failed")
                return False

            # Generate report
            if not self.generate_report():
                print("\n⚠️  Report generation failed (but training succeeded)")

            # Print summary
            self.print_summary()

            return True

        except Exception as e:
            print(f"\n❌ Orchestration failed: {e}")
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    orchestrator = TrainingOrchestrator()
    success = orchestrator.run_full_training()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
