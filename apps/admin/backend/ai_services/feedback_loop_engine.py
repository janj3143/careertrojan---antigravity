"""
Feedback Loop Engine for IntelliCV Backend

This engine orchestrates continuous learning across all AI engines:
- Connects Neural Network ↔ Expert System ↔ Bayesian ↔ NLP ↔ LLM ↔ Fuzzy Logic
- Distributes user corrections to all relevant engines
- Tracks prediction accuracy across engines
- Automatically triggers retraining when needed
- Implements ensemble voting for best results

Created: October 14, 2025
Part of: Backend-Admin Reorientation Project - Phase 2
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
from collections import defaultdict
import statistics

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class PredictionVote:
    """Represents a single engine's vote on a prediction."""
    
    def __init__(
        self,
        engine_name: str,
        prediction: Any,
        confidence: float,
        metadata: Optional[Dict] = None
    ):
        self.engine_name = engine_name
        self.prediction = prediction
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'engine_name': self.engine_name,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class FeedbackEntry:
    """Represents user feedback on a prediction."""
    
    def __init__(
        self,
        feedback_id: str,
        original_prediction: Any,
        user_correction: Any,
        context: Dict[str, Any],
        engines_involved: List[str]
    ):
        self.feedback_id = feedback_id
        self.original_prediction = original_prediction
        self.user_correction = user_correction
        self.context = context
        self.engines_involved = engines_involved
        self.timestamp = datetime.now().isoformat()
        self.processed = False
        self.distributed_to: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'feedback_id': self.feedback_id,
            'original_prediction': self.original_prediction,
            'user_correction': self.user_correction,
            'context': self.context,
            'engines_involved': self.engines_involved,
            'timestamp': self.timestamp,
            'processed': self.processed,
            'distributed_to': self.distributed_to
        }


class FeedbackLoopEngine:
    """
    Feedback Loop Engine for orchestrating continuous learning.
    
    Features:
    - Ensemble prediction (all engines vote, best wins)
    - Feedback distribution to all engines
    - Cross-engine learning
    - Performance tracking per engine
    - Automatic retraining triggers
    - Confidence calibration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the Feedback Loop Engine.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.logger = self._setup_logging()
        self.config = config or self._default_config()
        
        # Engine registry
        self.engines: Dict[str, Any] = {}
        self.engine_weights: Dict[str, float] = {}
        
        # Feedback storage
        self.feedback_queue: List[FeedbackEntry] = []
        self.feedback_history: List[FeedbackEntry] = []
        
        # Performance tracking
        self.engine_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_predictions': 0,
            'correct_predictions': 0,
            'accuracy': 0.0,
            'avg_confidence': 0.0,
            'confidence_calibration': 0.0
        })
        
        # Ensemble history
        self.ensemble_history: List[Dict[str, Any]] = []
        
        # Data paths
        data_dir = Path(__file__).parent.parent / 'data' / 'feedback'
        data_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = data_dir / 'feedback_queue.json'
        self.performance_file = data_dir / 'engine_performance.json'
        
        self.logger.info(f"Feedback Loop Engine initialized with config: {self.config}")
        
        # Load persisted data
        self._load_feedback()
        self._load_performance()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup dedicated logger for Feedback Loop Engine."""
        logger = logging.getLogger('FeedbackLoopEngine')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'feedback_loop_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'ensemble_method': 'weighted_vote',  # weighted_vote, highest_confidence, majority_vote
            'min_confidence_threshold': 0.5,
            'auto_distribute_feedback': True,
            'retrain_threshold': 100,  # Retrain after N feedback items
            'confidence_calibration_window': 1000,
            'save_interval': 10,  # Save every N feedback items
            'max_queue_size': 10000
        }
    
    def register_engine(
        self,
        engine_name: str,
        engine_instance: Any,
        initial_weight: float = 1.0
    ) -> bool:
        """
        Register an AI engine with the feedback loop.
        
        Args:
            engine_name: Name of the engine (e.g., 'neural_network', 'bayesian')
            engine_instance: The engine instance
            initial_weight: Initial voting weight (0.0 to 1.0)
            
        Returns:
            True if registered successfully
        """
        try:
            self.engines[engine_name] = engine_instance
            self.engine_weights[engine_name] = initial_weight
            
            # Initialize performance tracking
            if engine_name not in self.engine_performance:
                self.engine_performance[engine_name] = {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0,
                    'avg_confidence': 0.0,
                    'confidence_calibration': 0.0
                }
            
            self.logger.info(f"Registered engine: {engine_name} (weight: {initial_weight})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering engine {engine_name}: {e}")
            return False
    
    def ensemble_predict(
        self,
        input_data: Dict[str, Any],
        task: str = 'classification',
        engines_to_use: Optional[List[str]] = None
    ) -> Tuple[Any, float, Dict[str, Any]]:
        """
        Get ensemble prediction from all registered engines.
        
        Args:
            input_data: Input data for prediction
            task: Type of task
            engines_to_use: List of engine names to use (None = all)
            
        Returns:
            Tuple of (prediction, confidence, metadata)
        """
        try:
            self.logger.info(f"Ensemble prediction for task: {task}")
            
            # Determine which engines to use
            if engines_to_use:
                active_engines = {k: v for k, v in self.engines.items() if k in engines_to_use}
            else:
                active_engines = self.engines
            
            # Collect votes from all engines
            votes: List[PredictionVote] = []
            
            for engine_name, engine_instance in active_engines.items():
                try:
                    # Get prediction from engine
                    if hasattr(engine_instance, 'predict_with_confidence'):
                        prediction, confidence, metadata = engine_instance.predict_with_confidence(
                            input_data, task
                        )
                    else:
                        # Fallback for engines without confidence scoring
                        prediction = engine_instance.predict(input_data)
                        confidence = 0.5
                        metadata = {}
                    
                    vote = PredictionVote(
                        engine_name=engine_name,
                        prediction=prediction,
                        confidence=confidence,
                        metadata=metadata
                    )
                    votes.append(vote)
                    
                    self.logger.debug(f"  {engine_name}: {prediction} (conf: {confidence:.4f})")
                    
                except Exception as e:
                    self.logger.error(f"Error getting prediction from {engine_name}: {e}")
            
            # Combine votes based on ensemble method
            if self.config['ensemble_method'] == 'weighted_vote':
                final_prediction, final_confidence = self._weighted_vote(votes)
            elif self.config['ensemble_method'] == 'highest_confidence':
                final_prediction, final_confidence = self._highest_confidence(votes)
            elif self.config['ensemble_method'] == 'majority_vote':
                final_prediction, final_confidence = self._majority_vote(votes)
            else:
                final_prediction, final_confidence = self._weighted_vote(votes)
            
            # Build metadata
            metadata = {
                'ensemble_method': self.config['ensemble_method'],
                'num_engines': len(votes),
                'votes': [v.to_dict() for v in votes],
                'timestamp': datetime.now().isoformat()
            }
            
            # Track ensemble history
            self.ensemble_history.append({
                'input_data': input_data,
                'task': task,
                'prediction': final_prediction,
                'confidence': final_confidence,
                'votes': [v.to_dict() for v in votes],
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"Ensemble prediction: {final_prediction} (confidence: {final_confidence:.4f})")
            
            return final_prediction, final_confidence, metadata
            
        except Exception as e:
            self.logger.error(f"Error in ensemble prediction: {e}")
            return None, 0.0, {'error': str(e)}
    
    def _weighted_vote(self, votes: List[PredictionVote]) -> Tuple[Any, float]:
        """Combine votes using weighted voting."""
        if not votes:
            return None, 0.0
        
        # Group votes by prediction
        prediction_scores: Dict[str, float] = defaultdict(float)
        
        for vote in votes:
            # Weight = engine_weight * confidence
            weight = self.engine_weights.get(vote.engine_name, 1.0)
            score = weight * vote.confidence
            
            prediction_key = str(vote.prediction)
            prediction_scores[prediction_key] += score
        
        # Find prediction with highest score
        best_prediction = max(prediction_scores.items(), key=lambda x: x[1])
        
        # Calculate confidence (average of votes for this prediction)
        relevant_votes = [v for v in votes if str(v.prediction) == best_prediction[0]]
        avg_confidence = statistics.mean([v.confidence for v in relevant_votes])
        
        return best_prediction[0], avg_confidence
    
    def _highest_confidence(self, votes: List[PredictionVote]) -> Tuple[Any, float]:
        """Select prediction with highest confidence."""
        if not votes:
            return None, 0.0
        
        best_vote = max(votes, key=lambda v: v.confidence)
        return best_vote.prediction, best_vote.confidence
    
    def _majority_vote(self, votes: List[PredictionVote]) -> Tuple[Any, float]:
        """Select prediction that appears most frequently."""
        if not votes:
            return None, 0.0
        
        # Count occurrences
        prediction_counts: Dict[str, int] = defaultdict(int)
        for vote in votes:
            prediction_counts[str(vote.prediction)] += 1
        
        # Find most common
        best_prediction = max(prediction_counts.items(), key=lambda x: x[1])
        
        # Calculate confidence based on agreement
        total_votes = len(votes)
        agreement_ratio = best_prediction[1] / total_votes
        
        return best_prediction[0], agreement_ratio
    
    def submit_feedback(
        self,
        original_prediction: Any,
        user_correction: Any,
        context: Dict[str, Any],
        engines_involved: Optional[List[str]] = None
    ) -> str:
        """
        Submit user feedback for continuous learning.
        
        Args:
            original_prediction: The prediction that was made
            user_correction: User's correction
            context: Context data
            engines_involved: Engines that contributed to prediction
            
        Returns:
            Feedback ID
        """
        try:
            # Generate feedback ID
            feedback_id = f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create feedback entry
            feedback = FeedbackEntry(
                feedback_id=feedback_id,
                original_prediction=original_prediction,
                user_correction=user_correction,
                context=context,
                engines_involved=engines_involved or list(self.engines.keys())
            )
            
            # Add to queue
            self.feedback_queue.append(feedback)
            
            self.logger.info(f"Feedback submitted: {feedback_id}")
            self.logger.info(f"  Original: {original_prediction}")
            self.logger.info(f"  Correction: {user_correction}")
            
            # Auto-distribute if enabled
            if self.config['auto_distribute_feedback']:
                self.distribute_feedback(feedback_id)
            
            # Save periodically
            if len(self.feedback_queue) % self.config['save_interval'] == 0:
                self._save_feedback()
            
            # Check if retraining needed
            if len(self.feedback_queue) >= self.config['retrain_threshold']:
                self._trigger_retraining()
            
            return feedback_id
            
        except Exception as e:
            self.logger.error(f"Error submitting feedback: {e}")
            return ""
    
    def distribute_feedback(self, feedback_id: str) -> bool:
        """
        Distribute feedback to all relevant engines.
        
        Args:
            feedback_id: ID of feedback to distribute
            
        Returns:
            True if distributed successfully
        """
        try:
            # Find feedback
            feedback = next((f for f in self.feedback_queue if f.feedback_id == feedback_id), None)
            if not feedback:
                self.logger.warning(f"Feedback {feedback_id} not found")
                return False
            
            self.logger.info(f"Distributing feedback: {feedback_id}")
            
            # Send to each engine
            for engine_name in feedback.engines_involved:
                if engine_name not in self.engines:
                    continue
                
                engine = self.engines[engine_name]
                
                try:
                    # Send feedback to engine
                    if hasattr(engine, 'process_feedback'):
                        engine.process_feedback(
                            prediction_id=feedback_id,
                            user_feedback={
                                'original': feedback.original_prediction,
                                'correction': feedback.user_correction,
                                'context': feedback.context
                            }
                        )
                        
                        feedback.distributed_to.append(engine_name)
                        self.logger.info(f"  Distributed to {engine_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error distributing to {engine_name}: {e}")
            
            # Mark as processed
            feedback.processed = True
            
            # Move to history
            self.feedback_history.append(feedback)
            self.feedback_queue.remove(feedback)
            
            self._save_feedback()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error distributing feedback: {e}")
            return False
    
    def update_engine_performance(
        self,
        engine_name: str,
        was_correct: bool,
        confidence: float
    ):
        """
        Update performance metrics for an engine.
        
        Args:
            engine_name: Name of the engine
            was_correct: Whether the prediction was correct
            confidence: Confidence of the prediction
        """
        try:
            if engine_name not in self.engine_performance:
                return
            
            perf = self.engine_performance[engine_name]
            
            # Update counters
            perf['total_predictions'] += 1
            if was_correct:
                perf['correct_predictions'] += 1
            
            # Calculate accuracy
            perf['accuracy'] = perf['correct_predictions'] / perf['total_predictions']
            
            # Update average confidence (moving average)
            n = perf['total_predictions']
            perf['avg_confidence'] = ((n - 1) * perf['avg_confidence'] + confidence) / n
            
            # Calculate confidence calibration (how well confidence predicts accuracy)
            # This is simplified - in production you'd use proper calibration metrics
            perf['confidence_calibration'] = abs(perf['accuracy'] - perf['avg_confidence'])
            
            # Auto-adjust engine weight based on performance
            if perf['total_predictions'] >= 50:  # Only after sufficient data
                self.engine_weights[engine_name] = perf['accuracy']
            
            self.logger.debug(f"Updated {engine_name} performance: {perf['accuracy']:.4f} accuracy")
            
            # Save periodically
            if perf['total_predictions'] % self.config['save_interval'] == 0:
                self._save_performance()
            
        except Exception as e:
            self.logger.error(f"Error updating performance for {engine_name}: {e}")
    
    def _trigger_retraining(self):
        """Trigger retraining for all engines."""
        try:
            self.logger.info("Triggering retraining for all engines...")
            
            for engine_name, engine in self.engines.items():
                try:
                    if hasattr(engine, '_trigger_retraining'):
                        engine._trigger_retraining()
                        self.logger.info(f"  Triggered retraining for {engine_name}")
                except Exception as e:
                    self.logger.error(f"Error retraining {engine_name}: {e}")
            
            # Clear processed feedback
            self.feedback_queue = []
            self._save_feedback()
            
        except Exception as e:
            self.logger.error(f"Error triggering retraining: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'engine_performance': dict(self.engine_performance),
            'engine_weights': self.engine_weights,
            'feedback_queue_size': len(self.feedback_queue),
            'feedback_history_size': len(self.feedback_history),
            'ensemble_predictions': len(self.ensemble_history),
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
    
    def _load_feedback(self):
        """Load feedback from disk."""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Reconstruct feedback entries
                self.feedback_queue = []
                for fb_data in data.get('queue', []):
                    fb = FeedbackEntry(
                        feedback_id=fb_data['feedback_id'],
                        original_prediction=fb_data['original_prediction'],
                        user_correction=fb_data['user_correction'],
                        context=fb_data['context'],
                        engines_involved=fb_data['engines_involved']
                    )
                    fb.timestamp = fb_data.get('timestamp', fb.timestamp)
                    fb.processed = fb_data.get('processed', False)
                    fb.distributed_to = fb_data.get('distributed_to', [])
                    self.feedback_queue.append(fb)
                
                self.logger.info(f"Loaded {len(self.feedback_queue)} feedback entries")
        except Exception as e:
            self.logger.error(f"Error loading feedback: {e}")
    
    def _save_feedback(self):
        """Save feedback to disk."""
        try:
            data = {
                'queue': [fb.to_dict() for fb in self.feedback_queue],
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(self.feedback_queue)} feedback entries")
        except Exception as e:
            self.logger.error(f"Error saving feedback: {e}")
    
    def _load_performance(self):
        """Load performance data from disk."""
        try:
            if self.performance_file.exists():
                with open(self.performance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.engine_performance = defaultdict(lambda: {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy': 0.0,
                    'avg_confidence': 0.0,
                    'confidence_calibration': 0.0
                }, data.get('engine_performance', {}))
                
                self.engine_weights = data.get('engine_weights', {})
                
                self.logger.info(f"Loaded performance data for {len(self.engine_performance)} engines")
        except Exception as e:
            self.logger.error(f"Error loading performance: {e}")
    
    def _save_performance(self):
        """Save performance data to disk."""
        try:
            data = {
                'engine_performance': dict(self.engine_performance),
                'engine_weights': self.engine_weights,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("Saved performance data")
        except Exception as e:
            self.logger.error(f"Error saving performance: {e}")


# Example usage and testing
if __name__ == '__main__':
    print("=" * 80)
    print("Feedback Loop Engine - Test Run")
    print("=" * 80)
    
    # Initialize feedback loop
    feedback_loop = FeedbackLoopEngine()
    
    # Simulate engine registration (using mock engines)
    class MockEngine:
        def __init__(self, name):
            self.name = name
        
        def predict_with_confidence(self, input_data, task):
            import random
            predictions = ['Senior Software Engineer', 'Lead Developer', 'Software Architect']
            pred = random.choice(predictions)
            conf = random.uniform(0.6, 0.95)
            return pred, conf, {'engine': self.name}
    
    # Register engines
    feedback_loop.register_engine('neural_network', MockEngine('NN'), 1.0)
    feedback_loop.register_engine('bayesian', MockEngine('Bayesian'), 0.9)
    feedback_loop.register_engine('expert_system', MockEngine('ES'), 0.8)
    
    print("\n1. Registered Engines:")
    for name, weight in feedback_loop.engine_weights.items():
        print(f"   - {name}: weight={weight:.2f}")
    
    # Test ensemble prediction
    print("\n2. Testing Ensemble Prediction:")
    prediction, confidence, metadata = feedback_loop.ensemble_predict(
        input_data={'job_description': 'Senior developer with 10 years experience'},
        task='classification'
    )
    print(f"   Final Prediction: {prediction}")
    print(f"   Confidence: {confidence:.4f}")
    print(f"   Engines Used: {metadata['num_engines']}")
    
    # Test feedback submission
    print("\n3. Testing Feedback Submission:")
    feedback_id = feedback_loop.submit_feedback(
        original_prediction="Senior Software Engineer",
        user_correction="Staff Software Engineer",
        context={'job_description': 'Senior developer with 10 years experience'},
        engines_involved=['neural_network', 'bayesian']
    )
    print(f"   Feedback ID: {feedback_id}")
    print(f"   Queue Size: {len(feedback_loop.feedback_queue)}")
    
    # Get performance report
    print("\n4. Performance Report:")
    report = feedback_loop.get_performance_report()
    print(f"   Registered Engines: {len(report['engine_performance'])}")
    print(f"   Feedback Queue: {report['feedback_queue_size']}")
    print(f"   Ensemble Method: {report['config']['ensemble_method']}")
    
    print("\n" + "=" * 80)
    print("Feedback Loop Engine - Ready for Integration!")
    print("=" * 80)
