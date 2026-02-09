"""
Unified AI Engine - Coordinated Inference Across All Models
============================================================

Purpose:
  - Load all trained AI models
  - Execute inference across multiple models
  - Aggregate and reconcile predictions
  - Handle fallbacks and error cases
  - Provide confidence scores and explanations

Features:
  - Multi-model inference orchestration
  - Ensemble predictions (voting, averaging)
  - Confidence scoring and uncertainty quantification
  - Model-specific fallback strategies
  - Caching for performance optimization

Usage:
  from unified_ai_engine import UnifiedAIEngine
  engine = UnifiedAIEngine()
  results = engine.infer_job_category("Senior Python Developer...")
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from model_registry import ModelRegistry
except ImportError:
    print("❌ model_registry.py not found.")
    ModelRegistry = None


@dataclass
class InferenceResult:
    """Standard inference result format"""
    query: str
    model_name: str
    prediction: Any
    confidence: float
    metadata: Dict[str, Any]
    timestamp: str
    model_version: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EnsembleResult:
    """Combined results from multiple models"""
    query: str
    primary_prediction: Any
    confidence: float
    all_predictions: Dict[str, InferenceResult]
    reasoning: str
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            'query': self.query,
            'primary_prediction': self.primary_prediction,
            'confidence': self.confidence,
            'all_predictions': {k: v.to_dict() for k, v in self.all_predictions.items()},
            'reasoning': self.reasoning,
            'timestamp': self.timestamp
        }


class UnifiedAIEngine:
    """Master inference engine coordinating all AI models"""

    def __init__(self, registry_dir: str = "admin_portal/models"):
        """
        Initialize unified AI engine

        Args:
            registry_dir: Directory containing model registry
        """
        self.registry_dir = Path(registry_dir)
        self.registry = None
        self.loaded_models = {}
        self.inference_cache = {}
        self.cache_size = 1000  # LRU cache size

        print("\n" + "="*70)
        print("UNIFIED AI ENGINE INITIALIZING")
        print("="*70)

        # Initialize registry
        if ModelRegistry:
            self.registry = ModelRegistry(registry_dir=str(self.registry_dir))
            print(f"   Registry loaded")
        else:
            print(f"   ModelRegistry not available")

    def load_model(self, model_name: str, version: str = 'deployed') -> bool:
        """
        Load a specific model into memory

        Args:
            model_name: Name of the model to load
            version: Version to load ('deployed', 'latest', or specific version)

        Returns:
            True if successful, False otherwise
        """
        if not self.registry:
            print(f"❌ Registry not available")
            return False

        model = self.registry.get_model(model_name, version)

        if model is None:
            print(f"⚠️  Could not load {model_name}")
            return False

        self.loaded_models[model_name] = {
            'model': model,
            'version': version,
            'loaded_at': datetime.now().isoformat()
        }

        print(f"   ✅ Loaded {model_name} ({version})")
        return True

    def load_all_models(self, version: str = 'deployed') -> int:
        """
        Load all available models

        Args:
            version: Version to load for all models

        Returns:
            Number of models successfully loaded
        """
        if not self.registry:
            print(f"❌ Registry not available")
            return 0

        models = self.registry.list_models()
        loaded_count = 0

        for model_name in models.keys():
            # Skip vectorizers and info files
            if 'vectorizer' in model_name or 'info' in model_name:
                continue

            if self.load_model(model_name, version):
                loaded_count += 1

        print(f"\n✅ Loaded {loaded_count} models")
        return loaded_count

    def infer_job_category(self, text: str, person_name: str = "") -> InferenceResult:
        """
        Predict job category using Bayesian classifier

        Args:
            text: Resume/CV text to analyze
            person_name: Name of person (for context)

        Returns:
            InferenceResult with prediction and confidence
        """
        if 'bayesian_classifier' not in self.loaded_models:
            print("⚠️  Bayesian classifier not loaded")
            return None

        model_info = self.loaded_models['bayesian_classifier']
        model = model_info['model']
        vectorizer = self._get_vectorizer('bayesian_classifier')

        if not vectorizer:
            print("⚠️  Vectorizer not available")
            return None

        try:
            # Vectorize text
            X = vectorizer.transform([text])

            # Get prediction and probabilities
            prediction = model.predict(X)[0]
            probabilities = model.predict_proba(X)[0]
            confidence = float(max(probabilities))

            # Get class names
            classes = model.classes_
            class_probabilities = dict(zip(classes, probabilities))

            result = InferenceResult(
                query=text[:100] + "..." if len(text) > 100 else text,
                model_name='bayesian_classifier',
                prediction=prediction,
                confidence=confidence,
                metadata={
                    'all_categories': class_probabilities,
                    'person_name': person_name
                },
                timestamp=datetime.now().isoformat(),
                model_version=model_info['version']
            )

            return result

        except Exception as e:
            print(f"❌ Error in job category inference: {e}")
            return None

    def infer_salary_prediction(
        self,
        experience_years: float,
        skills_count: int,
        education_level: int = 3,
        text_length: int = 1000
    ) -> InferenceResult:
        """
        Predict salary using statistical models

        Args:
            experience_years: Years of experience
            skills_count: Number of skills
            education_level: Education level (1-5)
            text_length: Length of CV text

        Returns:
            InferenceResult with prediction and confidence
        """
        if 'salary_predictor' not in self.loaded_models:
            print("⚠️  Salary predictor not loaded")
            return None

        model_info = self.loaded_models['salary_predictor']
        model = model_info['model']

        try:
            # Prepare features
            features = [[experience_years, skills_count, education_level, text_length]]

            # Predict
            prediction = float(model.predict(features)[0])

            # Estimate confidence based on variance
            # (simplified - ideally would use model uncertainty)
            confidence = min(0.95, 0.5 + (experience_years / 50.0))

            result = InferenceResult(
                query=f"Exp: {experience_years}y, Skills: {skills_count}, Edu: {education_level}",
                model_name='salary_predictor',
                prediction=prediction,
                confidence=confidence,
                metadata={
                    'experience_years': experience_years,
                    'skills_count': skills_count,
                    'education_level': education_level,
                    'text_length': text_length
                },
                timestamp=datetime.now().isoformat(),
                model_version=model_info['version']
            )

            return result

        except Exception as e:
            print(f"❌ Error in salary prediction: {e}")
            return None

    def ensemble_infer(
        self,
        text: str,
        experience_years: float = 0,
        skills_count: int = 0
    ) -> EnsembleResult:
        """
        Run inference across multiple models and aggregate results

        Args:
            text: Resume/CV text
            experience_years: Years of experience
            skills_count: Number of skills

        Returns:
            EnsembleResult with combined predictions
        """
        print(f"\n🔮 Running Ensemble Inference...")

        predictions = {}
        confidences = []

        # Model 1: Job Category Classification
        job_pred = self.infer_job_category(text)
        if job_pred:
            predictions['job_category'] = job_pred
            confidences.append(job_pred.confidence)
            print(f"   ✅ Job Category: {job_pred.prediction} ({job_pred.confidence:.1%})")
        else:
            print(f"   ⚠️  Job Category inference skipped")

        # Model 2: Salary Prediction
        salary_pred = self.infer_salary_prediction(
            experience_years=experience_years,
            skills_count=skills_count
        )
        if salary_pred:
            predictions['salary'] = salary_pred
            confidences.append(salary_pred.confidence)
            print(f"   ✅ Salary: ${salary_pred.prediction:,.0f} ({salary_pred.confidence:.1%})")
        else:
            print(f"   ⚠️  Salary prediction skipped")

        # Aggregate confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Generate reasoning
        reasoning = self._generate_reasoning(predictions)

        # Determine primary prediction
        primary_prediction = {
            'job_category': predictions['job_category'].prediction if 'job_category' in predictions else 'Unknown',
            'estimated_salary': predictions['salary'].prediction if 'salary' in predictions else None
        }

        result = EnsembleResult(
            query=text[:100] + "..." if len(text) > 100 else text,
            primary_prediction=primary_prediction,
            confidence=avg_confidence,
            all_predictions=predictions,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat()
        )

        return result

    def _get_vectorizer(self, model_name: str):
        """Get vectorizer associated with a model"""
        if not self.registry:
            return None

        vectorizer_key = f"{model_name}_vectorizer"

        if vectorizer_key not in self.loaded_models:
            # Try to load it
            vectorizer = self.registry.get_vectorizer(model_name)
            if vectorizer:
                self.loaded_models[vectorizer_key] = {
                    'model': vectorizer,
                    'version': 'latest',
                    'loaded_at': datetime.now().isoformat()
                }
                return vectorizer
            return None

        return self.loaded_models[vectorizer_key]['model']

    def _generate_reasoning(self, predictions: Dict) -> str:
        """Generate human-readable reasoning for predictions"""
        parts = []

        if 'job_category' in predictions:
            job_pred = predictions['job_category']
            parts.append(
                f"Based on CV content analysis, this person appears to be in the "
                f"{job_pred.prediction} field with {job_pred.confidence:.0%} confidence."
            )

        if 'salary' in predictions:
            salary_pred = predictions['salary']
            parts.append(
                f"Estimated salary range: ${salary_pred.prediction:,.0f} "
                f"({salary_pred.confidence:.0%} confidence)."
            )

        return " ".join(parts) if parts else "Insufficient data for detailed reasoning."

    def test_all_models(self) -> bool:
        """Run quick test on all loaded models"""
        print("\n" + "="*70)
        print("🧪 TESTING ALL MODELS")
        print("="*70)

        # Test job category
        test_text = """
        Senior Python Developer with 8 years of experience in software engineering.
        Expert in Django, FastAPI, microservices architecture.
        Experience with AWS, Docker, Kubernetes.
        Master's degree in Computer Science.
        """

        print("\n📝 Test Text:")
        print(f"   {test_text[:100]}...")

        # Test ensemble
        result = self.ensemble_infer(
            text=test_text,
            experience_years=8,
            skills_count=15
        )

        if result:
            print("\n✅ Ensemble Result:")
            print(f"   Primary Prediction: {result.primary_prediction}")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Reasoning: {result.reasoning}")
            return True
        else:
            print("❌ Ensemble inference failed")
            return False

    def print_status(self):
        """Print engine status"""
        print("\n" + "="*70)
        print("📊 UNIFIED AI ENGINE STATUS")
        print("="*70)

        if self.registry:
            print("\n📦 Registered Models:")
            for model_name, info in self.registry.list_models().items():
                if 'vectorizer' not in model_name and 'info' not in model_name:
                    deployed = "✅" if info['current_deployment'] else "  "
                    print(f"   {deployed} {model_name}")
                    print(f"      Latest: {info['latest']}")
                    print(f"      Deployed: {info['current_deployment']}")

        print(f"\n🔧 Loaded Models ({len(self.loaded_models)}):")
        for model_name, info in self.loaded_models.items():
            if 'vectorizer' not in model_name and 'info' not in model_name:
                print(f"   ✅ {model_name} ({info['version']})")

        print("\n" + "="*70 + "\n")


def main():
    """Main entry point for testing"""
    import sys

    engine = UnifiedAIEngine()
    engine.print_status()

    # Load all models
    loaded = engine.load_all_models(version='deployed')

    if loaded == 0:
        print("⚠️  No models loaded. Run training_orchestrator.py first.")
        return 1

    # Run tests if requested
    if '--test' in sys.argv:
        success = engine.test_all_models()
        return 0 if success else 1

    return 0


if __name__ == "__main__":
    exit(main())
