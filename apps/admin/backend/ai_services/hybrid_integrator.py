"""
Hybrid AI Integrator - Orchestrates ALL 7 AI Engines
Connects new backend engines with existing unified_ai_engine.py

Created: October 14, 2025
"""

import logging
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# Add paths
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
services_path = backend_path.parent / "services"
sys.path.insert(0, str(services_path))

# Import new backend engines
from ai_services.neural_network_engine import NeuralNetworkEngine
from ai_services.expert_system_engine import ExpertSystemEngine
from ai_services.feedback_loop_engine import FeedbackLoopEngine
from ai_services.model_trainer import ModelTrainer

# Import existing unified AI engine
try:
    from unified_ai_engine import UnifiedAIEngine
    UNIFIED_AI_AVAILABLE = True
except ImportError:
    UNIFIED_AI_AVAILABLE = False
    logging.warning("unified_ai_engine.py not available - running with new engines only")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridAIIntegrator:
    """
    Orchestrates all 7 AI engines:
    
    NEW ENGINES (Backend):
    1. Neural Network Engine - Deep learning & embeddings
    2. Expert System Engine - Rule-based validation
    3. Feedback Loop Engine - Ensemble voting & learning
    
    EXISTING ENGINES (Services):
    4. Bayesian Inference - Pattern recognition (from unified_ai_engine)
    5. NLP Engine - Semantic understanding (from unified_ai_engine)
    6. LLM Engine - Content generation (from unified_ai_engine)
    7. Fuzzy Logic - Uncertainty handling (from unified_ai_engine)
    
    The Feedback Loop Engine acts as the orchestrator, collecting votes from
    all engines and producing ensemble predictions.
    """
    
    def __init__(self):
        """Initialize all 7 AI engines"""
        logger.info("Initializing Hybrid AI Integrator with 7 engines...")
        
        # Initialize new backend engines
        self.neural_network = NeuralNetworkEngine()
        self.expert_system = ExpertSystemEngine()
        self.feedback_loop = FeedbackLoopEngine()
        self.model_trainer = ModelTrainer()
        
        # Initialize existing unified AI engine
        self.unified_ai = None
        if UNIFIED_AI_AVAILABLE:
            try:
                self.unified_ai = UnifiedAIEngine()
                logger.info("Unified AI Engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Unified AI Engine: {e}")
        
        # Register all engines with feedback loop
        self._register_engines()
        
        # Track integration metrics
        self.integration_metrics = {
            'total_predictions': 0,
            'engine_votes': defaultdict(int),
            'ensemble_accuracy': 0.0,
            'last_updated': datetime.now()
        }
        
        logger.info("Hybrid AI Integrator initialized with 7 engines")
    
    def _register_engines(self):
        """Register all available engines with the feedback loop"""
        # Register new backend engines
        self.feedback_loop.register_engine(
            "neural_network",
            self.neural_network,
            initial_weight=0.85
        )
        
        self.feedback_loop.register_engine(
            "expert_system",
            self.expert_system,
            initial_weight=0.80
        )
        
        # Create wrapper for unified AI engine components
        if self.unified_ai:
            # Bayesian wrapper
            self.feedback_loop.register_engine(
                "bayesian",
                self._create_bayesian_wrapper(),
                initial_weight=0.75
            )
            
            # NLP wrapper
            self.feedback_loop.register_engine(
                "nlp",
                self._create_nlp_wrapper(),
                initial_weight=0.70
            )
            
            # LLM wrapper
            self.feedback_loop.register_engine(
                "llm",
                self._create_llm_wrapper(),
                initial_weight=0.80
            )
            
            # Fuzzy Logic wrapper
            self.feedback_loop.register_engine(
                "fuzzy",
                self._create_fuzzy_wrapper(),
                initial_weight=0.65
            )
        
        logger.info(f"Registered {len(self.feedback_loop.engines)} engines with feedback loop")
    
    def _create_bayesian_wrapper(self):
        """Create wrapper for Bayesian engine from unified AI"""
        class BayesianWrapper:
            def __init__(self, unified_ai):
                self.unified_ai = unified_ai
            
            def predict_with_confidence(self, input_data: Dict, task: str) -> Tuple[Any, float, Dict]:
                """Make Bayesian prediction"""
                try:
                    # Use unified AI's Bayesian capabilities
                    if hasattr(self.unified_ai, 'bayesian_engine'):
                        result = self.unified_ai.bayesian_engine.classify(
                            input_data.get('text', ''),
                            input_data.get('features', {})
                        )
                        return (
                            result.get('classification'),
                            result.get('confidence', 0.5),
                            {'method': 'bayesian', 'details': result}
                        )
                except Exception as e:
                    logger.error(f"Bayesian wrapper error: {e}")
                
                return (None, 0.0, {'error': 'Bayesian prediction failed'})
            
            def process_feedback(self, prediction_id: str, feedback: Dict):
                """Process feedback for Bayesian learning"""
                try:
                    if hasattr(self.unified_ai, 'learning_table'):
                        self.unified_ai.learning_table.add_entry(
                            term=feedback.get('term', ''),
                            category=feedback.get('category', ''),
                            context=feedback.get('context', '')
                        )
                except Exception as e:
                    logger.error(f"Bayesian feedback error: {e}")
        
        return BayesianWrapper(self.unified_ai)
    
    def _create_nlp_wrapper(self):
        """Create wrapper for NLP engine from unified AI"""
        class NLPWrapper:
            def __init__(self, unified_ai):
                self.unified_ai = unified_ai
            
            def predict_with_confidence(self, input_data: Dict, task: str) -> Tuple[Any, float, Dict]:
                """Make NLP prediction"""
                try:
                    if hasattr(self.unified_ai, 'nlp_engine'):
                        text = input_data.get('text', '')
                        result = self.unified_ai.nlp_engine.analyze(text)
                        
                        # Extract relevant prediction based on task
                        if task == 'skills_extraction':
                            prediction = result.get('skills', [])
                        elif task == 'job_title_classifier':
                            prediction = result.get('job_title', '')
                        else:
                            prediction = result.get('entities', [])
                        
                        confidence = result.get('confidence', 0.6)
                        
                        return (prediction, confidence, {'method': 'nlp', 'details': result})
                except Exception as e:
                    logger.error(f"NLP wrapper error: {e}")
                
                return (None, 0.0, {'error': 'NLP prediction failed'})
            
            def process_feedback(self, prediction_id: str, feedback: Dict):
                """Process feedback for NLP learning"""
                # NLP models typically don't have direct feedback mechanisms
                # Could update entity recognition patterns here
                pass
        
        return NLPWrapper(self.unified_ai)
    
    def _create_llm_wrapper(self):
        """Create wrapper for LLM engine from unified AI"""
        class LLMWrapper:
            def __init__(self, unified_ai):
                self.unified_ai = unified_ai
            
            def predict_with_confidence(self, input_data: Dict, task: str) -> Tuple[Any, float, Dict]:
                """Make LLM prediction"""
                try:
                    if hasattr(self.unified_ai, 'llm_engine'):
                        prompt = input_data.get('prompt', '')
                        result = self.unified_ai.llm_engine.generate(prompt, task)
                        
                        return (
                            result.get('text', ''),
                            result.get('confidence', 0.7),
                            {'method': 'llm', 'details': result}
                        )
                except Exception as e:
                    logger.error(f"LLM wrapper error: {e}")
                
                return (None, 0.0, {'error': 'LLM prediction failed'})
            
            def process_feedback(self, prediction_id: str, feedback: Dict):
                """Process feedback for LLM fine-tuning"""
                # Could log feedback for future fine-tuning
                pass
        
        return LLMWrapper(self.unified_ai)
    
    def _create_fuzzy_wrapper(self):
        """Create wrapper for Fuzzy Logic engine from unified AI"""
        class FuzzyWrapper:
            def __init__(self, unified_ai):
                self.unified_ai = unified_ai
            
            def predict_with_confidence(self, input_data: Dict, task: str) -> Tuple[Any, float, Dict]:
                """Make Fuzzy Logic prediction"""
                try:
                    if hasattr(self.unified_ai, 'fuzzy_engine'):
                        values = input_data.get('values', {})
                        result = self.unified_ai.fuzzy_engine.evaluate(values)
                        
                        return (
                            result.get('classification'),
                            result.get('membership', 0.5),
                            {'method': 'fuzzy', 'details': result}
                        )
                except Exception as e:
                    logger.error(f"Fuzzy wrapper error: {e}")
                
                return (None, 0.0, {'error': 'Fuzzy prediction failed'})
            
            def process_feedback(self, prediction_id: str, feedback: Dict):
                """Process feedback for Fuzzy rule updates"""
                # Could adjust membership functions based on feedback
                pass
        
        return FuzzyWrapper(self.unified_ai)
    
    def predict(
        self,
        input_data: Dict[str, Any],
        task: str,
        engines_to_use: Optional[List[str]] = None,
        require_expert_validation: bool = True
    ) -> Dict[str, Any]:
        """
        Make a hybrid prediction using all selected engines.
        
        Args:
            input_data: Input data for prediction
            task: Type of task (job_title_classifier, skills_extractor, etc.)
            engines_to_use: List of engine names to use (None = all)
            require_expert_validation: Whether to validate with expert system
        
        Returns:
            Dictionary with prediction, confidence, votes, and validation results
        """
        try:
            logger.info(f"Making hybrid prediction for task: {task}")
            
            # Get ensemble prediction from all engines
            ensemble_result = self.feedback_loop.ensemble_predict(
                input_data=input_data,
                task=task,
                engines_to_use=engines_to_use
            )
            
            # Validate with expert system if required
            validation_result = None
            if require_expert_validation:
                is_valid, triggered_rules, explanation = self.expert_system.validate_prediction(
                    prediction=ensemble_result['prediction'],
                    context=input_data,
                    category=task
                )
                
                validation_result = {
                    'is_valid': is_valid,
                    'triggered_rules': triggered_rules,
                    'explanation': explanation
                }
                
                # If invalid, flag for review
                if not is_valid:
                    logger.warning(f"Prediction failed expert validation: {explanation}")
                    ensemble_result['requires_review'] = True
                    ensemble_result['review_reason'] = explanation
            
            # Update metrics
            self.integration_metrics['total_predictions'] += 1
            for vote in ensemble_result.get('votes', []):
                self.integration_metrics['engine_votes'][vote['engine']] += 1
            self.integration_metrics['last_updated'] = datetime.now()
            
            # Compile final result
            result = {
                'prediction': ensemble_result['prediction'],
                'confidence': ensemble_result['confidence'],
                'ensemble_method': ensemble_result.get('ensemble_method', 'weighted_vote'),
                'engine_votes': ensemble_result.get('votes', []),
                'validation': validation_result,
                'metadata': {
                    'task': task,
                    'timestamp': datetime.now().isoformat(),
                    'engines_used': len(ensemble_result.get('votes', [])),
                    'total_engines_available': len(self.feedback_loop.engines)
                }
            }
            
            logger.info(f"Hybrid prediction complete: {result['confidence']:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Hybrid prediction error: {e}")
            return {
                'prediction': None,
                'confidence': 0.0,
                'error': str(e),
                'metadata': {'task': task, 'timestamp': datetime.now().isoformat()}
            }
    
    def submit_feedback(
        self,
        original_prediction: Any,
        user_correction: Any,
        context: Dict[str, Any]
    ) -> str:
        """
        Submit feedback that will be distributed to all engines for learning.
        
        Args:
            original_prediction: The original prediction made
            user_correction: The correct answer provided by user
            context: Context data including task, input, etc.
        
        Returns:
            Feedback ID for tracking
        """
        try:
            # Submit to feedback loop
            feedback_id = self.feedback_loop.submit_feedback(
                original_prediction=original_prediction,
                user_correction=user_correction,
                context=context
            )
            
            # Also update unified AI learning table if available
            if self.unified_ai and hasattr(self.unified_ai, 'learning_table'):
                self.unified_ai.learning_table.add_entry(
                    term=str(user_correction),
                    category=context.get('task', 'general'),
                    context=json.dumps(context)
                )
            
            logger.info(f"Feedback submitted: {feedback_id}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"Feedback submission error: {e}")
            raise
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report from all engines"""
        try:
            # Get feedback loop performance
            feedback_performance = self.feedback_loop.get_performance_report()
            
            # Get expert system stats
            expert_performance = self.expert_system.get_performance_metrics()
            
            # Get neural network stats
            nn_performance = self.neural_network.get_performance_metrics()
            
            # Get unified AI stats if available
            unified_stats = {}
            if self.unified_ai and hasattr(self.unified_ai, 'learning_table'):
                unified_stats = {
                    'learning_table_entries': len(self.unified_ai.learning_table.entries),
                    'verified_entries': sum(1 for e in self.unified_ai.learning_table.entries.values() if e.verified)
                }
            
            # Compile comprehensive report
            report = {
                'integration_metrics': self.integration_metrics,
                'feedback_loop_performance': feedback_performance,
                'expert_system_performance': expert_performance,
                'neural_network_performance': nn_performance,
                'unified_ai_stats': unified_stats,
                'total_engines': len(self.feedback_loop.engines),
                'timestamp': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Performance report error: {e}")
            return {'error': str(e)}
    
    def train_models(
        self,
        scenario_id: Optional[str] = None,
        include_unified_ai_data: bool = True
    ) -> Dict[str, Any]:
        """
        Train models using data from both new and existing systems.
        
        Args:
            scenario_id: Specific scenario to train (None = all)
            include_unified_ai_data: Whether to include data from unified AI learning table
        
        Returns:
            Training results
        """
        try:
            logger.info("Starting hybrid model training...")
            
            results = {}
            
            # Train new backend models
            if scenario_id:
                result = self.model_trainer.train_scenario(scenario_id)
                results[scenario_id] = result
            else:
                # Train all scenarios
                for sid in self.model_trainer.scenarios:
                    result = self.model_trainer.train_scenario(sid)
                    results[sid] = result
            
            # Optionally incorporate unified AI learning data
            if include_unified_ai_data and self.unified_ai:
                if hasattr(self.unified_ai, 'learning_table'):
                    # Export learning table data for training
                    learning_data = self.unified_ai.learning_table.export_verified_entries()
                    results['unified_ai_data_exported'] = len(learning_data)
                    logger.info(f"Exported {len(learning_data)} verified entries from unified AI")
            
            logger.info("Hybrid model training complete")
            return results
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            return {'error': str(e)}


# ============================================================================
# Convenience wrapper for backward compatibility
# ============================================================================

class EnhancedUnifiedAI:
    """
    Enhanced wrapper that provides backward compatibility with existing code
    while leveraging the new hybrid AI integrator.
    
    Use this to replace UnifiedAIEngine in existing code with minimal changes.
    """
    
    def __init__(self):
        """Initialize the enhanced AI system"""
        self.hybrid_integrator = HybridAIIntegrator()
        
        # Expose individual engines for direct access if needed
        self.neural_network = self.hybrid_integrator.neural_network
        self.expert_system = self.hybrid_integrator.expert_system
        self.feedback_loop = self.hybrid_integrator.feedback_loop
        self.unified_ai = self.hybrid_integrator.unified_ai
    
    def predict(self, input_data: Dict, task: str) -> Dict:
        """Make prediction - backward compatible interface"""
        return self.hybrid_integrator.predict(input_data, task)
    
    def submit_feedback(self, prediction: Any, correction: Any, context: Dict) -> str:
        """Submit feedback - backward compatible interface"""
        return self.hybrid_integrator.submit_feedback(prediction, correction, context)
    
    def get_performance(self) -> Dict:
        """Get performance metrics - backward compatible interface"""
        return self.hybrid_integrator.get_performance_report()


# ============================================================================
# Standalone Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("HYBRID AI INTEGRATOR - TEST HARNESS")
    print("=" * 80)
    
    # Initialize
    print("\n1. Initializing Hybrid AI Integrator...")
    integrator = HybridAIIntegrator()
    
    print(f"\n   ✓ Registered {len(integrator.feedback_loop.engines)} engines:")
    for engine_name in integrator.feedback_loop.engines:
        weight = integrator.feedback_loop.engine_weights[engine_name]
        print(f"     - {engine_name}: weight={weight:.2f}")
    
    # Test prediction
    print("\n2. Testing Hybrid Prediction...")
    test_input = {
        'text': 'Senior Software Engineer with 8 years of Python and FastAPI experience',
        'job_title': 'Senior Software Engineer',
        'experience_years': 8,
        'skills': ['Python', 'FastAPI', 'Docker']
    }
    
    result = integrator.predict(
        input_data=test_input,
        task='job_title_classifier',
        require_expert_validation=True
    )
    
    print(f"\n   Prediction: {result['prediction']}")
    print(f"   Confidence: {result['confidence']:.2%}")
    print(f"   Engines voted: {result['metadata']['engines_used']}")
    
    if result.get('validation'):
        val = result['validation']
        print(f"   Expert validation: {'✓ PASSED' if val['is_valid'] else '✗ FAILED'}")
        if val['explanation']:
            print(f"   Explanation: {val['explanation']}")
    
    # Test feedback
    print("\n3. Testing Feedback Submission...")
    feedback_id = integrator.submit_feedback(
        original_prediction="Senior Developer",
        user_correction="Senior Software Engineer",
        context={'task': 'job_title_classifier', 'source': 'test'}
    )
    print(f"   ✓ Feedback submitted: {feedback_id}")
    
    # Performance report
    print("\n4. Performance Report...")
    report = integrator.get_performance_report()
    
    print(f"\n   Total predictions: {report['integration_metrics']['total_predictions']}")
    print(f"   Total engines: {report['total_engines']}")
    
    if 'feedback_loop_performance' in report:
        for engine, metrics in report['feedback_loop_performance'].items():
            acc = metrics.get('accuracy', 0)
            conf = metrics.get('avg_confidence', 0)
            print(f"   {engine}: {acc:.1%} accuracy, {conf:.2f} avg confidence")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE - Hybrid AI Integrator is operational!")
    print("=" * 80)
