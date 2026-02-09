"""
Unified AI Engine - Coordinated Inference Across All Models
============================================================

Purpose:
  - Integration Hub for:
    1. Classic ML Models (Bayesian, Regression)
    2. Real Data Patterns (Pattern Analysis)
    3. LLM Reasoning (Ollama)
  - Execute inference across multiple models
  - Aggregate and reconcile predictions

Usage:
  from unified_ai_engine import UnifiedAIEngine
  engine = UnifiedAIEngine()
  results = engine.ensemble_infer("Senior Python Developer...")
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add parent path to sys.path to allow sibling imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from model_registry import ModelRegistry
    from ollama_connector import OllamaConnector
    # Robust import for the data connector
    try:
        from shared.real_ai_connector import RealAIDataConnector
    except ImportError:
        # Fallback if running from this dir directly
        sys.path.append(str(Path(__file__).parent.parent / "shared"))
        from real_ai_connector import RealAIDataConnector
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    ModelRegistry = None
    OllamaConnector = None
    RealAIDataConnector = None


@dataclass
class InferenceResult:
    """Standard inference result format"""
    query: str
    model_name: str
    prediction: Any
    confidence: float
    metadata: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EnsembleResult:
    """Combined results from multiple models"""
    query: str
    primary_prediction: Any
    confidence: float
    all_predictions: Dict[str, Dict]
    reasoning: str
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            'query': self.query,
            'primary_prediction': self.primary_prediction,
            'confidence': self.confidence,
            'all_predictions': {k: (v.to_dict() if hasattr(v, 'to_dict') else v) for k, v in self.all_predictions.items()},
            'reasoning': self.reasoning,
            'timestamp': self.timestamp
        }


class UnifiedAIEngine:
    """Master inference engine coordinating all AI models"""

    def __init__(self, registry_dir: str = None):
        """Initialize engine with all 3 brains: ML, Data, LLM"""
        
        # Default registry to runtime root trained_models
        if not registry_dir:
            # Assuming we are in services/ai-workers/inference
            # Root is ../../../
            root = Path(__file__).resolve().parents[3]
            registry_dir = root / "trained_models"
            
        self.registry_dir = Path(registry_dir)
        self.loaded_models = {}
        
        print("\n" + "="*70)
        print("🦄 UNIFIED AI ENGINE INITIALIZING")
        print("="*70)

        # 1. Initialize ML Registry
        if ModelRegistry:
            self.registry = ModelRegistry(registry_dir=str(self.registry_dir), models_dir=str(self.registry_dir))
            print(f"   ✅ Registry loaded from {self.registry_dir}")
        else:
            self.registry = None
            print(f"   ❌ ModelRegistry not available")

        # 2. Initialize Real Data Connector
        if RealAIDataConnector:
            try:
                self.data_connector = RealAIDataConnector()
                print(f"   ✅ Real Data Connector attached (strictly {self.data_connector.base_path})")
            except Exception as e:
                print(f"   ❌ Real Data Connector init failed: {e}")
                self.data_connector = None
        else:
            self.data_connector = None

        # 3. Initialize Ollama Connector
        if OllamaConnector:
            try:
                self.ollama = OllamaConnector()
                if self.ollama.is_alive():
                    print(f"   ✅ Ollama LLM connected")
                else:
                    print(f"   ⚠️ Ollama service not reachable (will fallback)")
            except Exception as e:
                self.ollama = None
        else:
            self.ollama = None

    def load_model(self, model_name: str, version: str = 'deployed') -> bool:
        if not self.registry: return False
        model = self.registry.get_model(model_name, version)
        if model:
            self.loaded_models[model_name] = {'model': model, 'version': version}
            return True
        return False

    def load_all_models(self) -> int:
        if not self.registry: return 0
        models = self.registry.list_models()
        count = 0
        for name in models.keys():
            if 'vectorizer' not in name and self.load_model(name):
                count += 1
        return count

    # --- INFERENCE METHODS ---

    def infer_salary(self, experience: float, skills: int, edu_level: int) -> Optional[InferenceResult]:
        """Predict salary using ML model"""
        if 'salary_predictor' not in self.loaded_models:
            return None
            
        model = self.loaded_models['salary_predictor']['model']
        try:
            # Simple prediction wrapper
            prediction = float(model.predict([[experience, skills, edu_level, 1000]])[0])
            return InferenceResult(
                query=f"Exp:{experience}", model_name="salary_predictor",
                prediction=prediction, confidence=0.8, 
                metadata={"experience": experience}, timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            print(f"Salary inference error: {e}")
            return None

    def infer_with_ollama(self, prompt: str, context: Dict = None) -> Optional[str]:
        """Generate reasoning via Llama"""
        if not self.ollama: return None
        
        system_prompt = "You are an expert career counselor AI. Analyze the candidate profile."
        full_prompt = f"{prompt}\nContext: {json.dumps(context or {})}"
        
        return self.ollama.generate(full_prompt, system=system_prompt)

    def ensemble_infer(self, text: str, experience: float = 0, skills: int = 0) -> EnsembleResult:
        """
        The Main Brain function: Combines everything.
        """
        print(f"\n🔮 Running Hybrid Ensemble Inference...")
        
        predictions = {}
        confidences = []
        
        # 1. Real Data Pattern Analysis
        if self.data_connector:
            print("   🔍 Checking Real Data Patterns...")
            patterns = self.data_connector.analyze_resume_against_real_data(text)
            predictions['data_patterns'] = patterns
            confidences.append(0.9 if patterns['matched_patterns'] else 0.5)
            
        # 2. ML Salary Prediction
        salary_res = self.infer_salary(experience, skills, 3)
        if salary_res:
            print(f"   💰 ML Salary Prediction: ${salary_res.prediction:,.0f}")
            predictions['salary'] = salary_res
            confidences.append(salary_res.confidence)
            
        # 3. Ollama Reasoning
        if self.ollama and self.ollama.is_alive():
            print("   🧠 Asking Llama3 for analysis...")
            context = {
                "patterns": predictions.get('data_patterns', {}).get('matched_patterns', []),
                "estimated_salary": salary_res.prediction if salary_res else "N/A"
            }
            llm_reasoning = self.infer_with_ollama(
                f"Analyze this candidate profile summary and provide a 2 sentence assessment:\n{text[:500]}", 
                context
            )
            predictions['llm_analysis'] = llm_reasoning
            print(f"   🗣️ LLM: {llm_reasoning[:100]}...")
        else:
            llm_reasoning = "LLM unavailable."
            
        # Final Ensemble Result
        avg_confusion = sum(confidences) / len(confidences) if confidences else 0.0
        
        result = EnsembleResult(
            query=text[:50] + "...",
            primary_prediction="Analysis Complete",
            confidence=avg_confusion,
            all_predictions=predictions,
            reasoning=llm_reasoning,
            timestamp=datetime.now().isoformat()
        )
        
        return result

def main():
    """Test the Unified Brain"""
    engine = UnifiedAIEngine()
    engine.load_all_models()
    
    test_text = "Senior Python Developer with 8 years experience in AI."
    result = engine.ensemble_infer(test_text, experience=8, skills=10)
    
    print("\n✅ Final Result:")
    print(json.dumps(result.to_dict(), indent=2, default=str))

if __name__ == "__main__":
    main()
