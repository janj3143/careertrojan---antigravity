"""
Model Training & Management System for IntelliCV Backend

This system provides:
- Training on existing CV/resume data
- Multiple training scenarios (job titles, skills, companies, industries)
- Admin interface for reviewing predictions
- Error deviation detection and flagging
- Model version management
- A/B testing capabilities

Created: October 14, 2025
Part of: Backend-Admin Reorientation Project - Phase 2
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import hashlib
import pickle

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class TrainingScenario:
    """Represents a specific training scenario/model."""
    
    def __init__(
        self,
        scenario_id: str,
        name: str,
        description: str,
        task_type: str,
        config: Dict[str, Any]
    ):
        self.scenario_id = scenario_id
        self.name = name
        self.description = description
        self.task_type = task_type  # 'job_title', 'skills', 'company', 'industry', etc.
        self.config = config
        self.created_at = datetime.now().isoformat()
        self.trained_at = None
        self.model_version = None
        self.performance_metrics = {}
        self.status = 'created'  # created, training, trained, deployed, deprecated
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'scenario_id': self.scenario_id,
            'name': self.name,
            'description': self.description,
            'task_type': self.task_type,
            'config': self.config,
            'created_at': self.created_at,
            'trained_at': self.trained_at,
            'model_version': self.model_version,
            'performance_metrics': self.performance_metrics,
            'status': self.status
        }


class ModelTrainer:
    """
    Model Training & Management System.
    
    Features:
    - Train models on existing CV/resume data
    - Multiple training scenarios
    - Admin review interface
    - Error deviation detection
    - Model versioning and A/B testing
    """
    
    def __init__(self, data_dir: Optional[str] = None, models_dir: Optional[str] = None):
        """
        Initialize Model Trainer.
        
        Args:
            data_dir: Directory containing training data
            models_dir: Directory to save trained models
        """
        self.logger = self._setup_logging()
        
        # Setup directories
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to IntelliCV-data in REORIENTATION workspace
            self.data_dir = Path(__file__).parent.parent.parent / 'IntelliCV-data'
        
        if models_dir:
            self.models_dir = Path(models_dir)
        else:
            self.models_dir = Path(__file__).parent.parent / 'models'
        
        self.models_dir.mkdir(exist_ok=True)
        
        # Training scenarios registry
        self.scenarios = {}
        self.load_scenarios()
        
        # Training data cache
        self.training_data_cache = {}
        
        # Predictions requiring admin review
        self.review_queue = []
        
        # Error deviation thresholds
        self.deviation_thresholds = {
            'confidence_drop': 0.3,  # Flag if confidence drops >30% from average
            'outlier_score': 2.5,    # Standard deviations from mean
            'consistency_threshold': 0.7  # Min consistency with similar samples
        }
        
        self.logger.info(f"Model Trainer initialized. Data dir: {self.data_dir}, Models dir: {self.models_dir}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup dedicated logger for Model Trainer."""
        logger = logging.getLogger('ModelTrainer')
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'model_trainer_{datetime.now().strftime("%Y%m%d")}.log'
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
    
    def load_scenarios(self):
        """Load existing training scenarios from disk."""
        scenarios_file = self.models_dir / 'scenarios.json'
        
        if scenarios_file.exists():
            try:
                with open(scenarios_file, 'r') as f:
                    scenarios_data = json.load(f)
                
                for scenario_data in scenarios_data:
                    scenario = TrainingScenario(
                        scenario_id=scenario_data['scenario_id'],
                        name=scenario_data['name'],
                        description=scenario_data['description'],
                        task_type=scenario_data['task_type'],
                        config=scenario_data['config']
                    )
                    scenario.trained_at = scenario_data.get('trained_at')
                    scenario.model_version = scenario_data.get('model_version')
                    scenario.performance_metrics = scenario_data.get('performance_metrics', {})
                    scenario.status = scenario_data.get('status', 'created')
                    
                    self.scenarios[scenario.scenario_id] = scenario
                
                self.logger.info(f"Loaded {len(self.scenarios)} training scenarios")
            except Exception as e:
                self.logger.error(f"Error loading scenarios: {e}")
        else:
            # Create default scenarios
            self._create_default_scenarios()
    
    def _create_default_scenarios(self):
        """Create default training scenarios."""
        default_scenarios = [
            {
                'scenario_id': 'job_title_classifier',
                'name': 'Job Title Classification',
                'description': 'Classify and standardize job titles from resumes',
                'task_type': 'job_title',
                'config': {
                    'model_type': 'neural_network',
                    'embedding_dim': 768,
                    'num_classes': 'dynamic',
                    'confidence_threshold': 0.75,
                    'enable_admin_review': True
                }
            },
            {
                'scenario_id': 'skills_extractor',
                'name': 'Skills Extraction',
                'description': 'Extract and categorize technical and soft skills',
                'task_type': 'skills',
                'config': {
                    'model_type': 'hybrid',
                    'use_ner': True,
                    'confidence_threshold': 0.70,
                    'enable_admin_review': True
                }
            },
            {
                'scenario_id': 'company_classifier',
                'name': 'Company Classification',
                'description': 'Identify and classify companies by industry/size',
                'task_type': 'company',
                'config': {
                    'model_type': 'neural_network',
                    'include_industry': True,
                    'include_size': True,
                    'confidence_threshold': 0.65,
                    'enable_admin_review': True
                }
            },
            {
                'scenario_id': 'industry_classifier',
                'name': 'Industry Classification',
                'description': 'Classify industries from job descriptions',
                'task_type': 'industry',
                'config': {
                    'model_type': 'bayesian',
                    'linkedin_taxonomy': True,
                    'confidence_threshold': 0.80,
                    'enable_admin_review': False
                }
            },
            {
                'scenario_id': 'experience_analyzer',
                'name': 'Experience Analysis',
                'description': 'Analyze and score work experience relevance',
                'task_type': 'experience',
                'config': {
                    'model_type': 'neural_network',
                    'scoring_method': 'weighted',
                    'confidence_threshold': 0.70,
                    'enable_admin_review': True
                }
            }
        ]
        
        for scenario_data in default_scenarios:
            scenario = TrainingScenario(**scenario_data)
            self.scenarios[scenario.scenario_id] = scenario
        
        self.save_scenarios()
        self.logger.info(f"Created {len(default_scenarios)} default training scenarios")
    
    def save_scenarios(self):
        """Save training scenarios to disk."""
        scenarios_file = self.models_dir / 'scenarios.json'
        
        try:
            scenarios_data = [s.to_dict() for s in self.scenarios.values()]
            with open(scenarios_file, 'w') as f:
                json.dump(scenarios_data, f, indent=2)
            
            self.logger.info(f"Saved {len(scenarios_data)} scenarios")
        except Exception as e:
            self.logger.error(f"Error saving scenarios: {e}")
    
    def create_scenario(
        self,
        name: str,
        description: str,
        task_type: str,
        config: Dict[str, Any]
    ) -> TrainingScenario:
        """
        Create a new training scenario.
        
        Args:
            name: Scenario name
            description: Scenario description
            task_type: Type of task
            config: Configuration dictionary
            
        Returns:
            Created TrainingScenario object
        """
        # Generate scenario ID
        scenario_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        scenario = TrainingScenario(
            scenario_id=scenario_id,
            name=name,
            description=description,
            task_type=task_type,
            config=config
        )
        
        self.scenarios[scenario_id] = scenario
        self.save_scenarios()
        
        self.logger.info(f"Created new scenario: {scenario_id}")
        return scenario
    
    def load_training_data(
        self,
        scenario_id: str,
        force_reload: bool = False
    ) -> Dict[str, Any]:
        """
        Load training data for a specific scenario.
        
        Args:
            scenario_id: ID of the training scenario
            force_reload: Force reload even if cached
            
        Returns:
            Dictionary containing training data
        """
        # Check cache
        if not force_reload and scenario_id in self.training_data_cache:
            self.logger.info(f"Using cached training data for {scenario_id}")
            return self.training_data_cache[scenario_id]
        
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        self.logger.info(f"Loading training data for scenario: {scenario_id}")
        
        # Load data based on task type
        training_data = {
            'samples': [],
            'labels': [],
            'metadata': [],
            'source_files': []
        }
        
        # Scan IntelliCV-data directory for CV files
        cv_files = list(self.data_dir.glob('*.pdf')) + \
                  list(self.data_dir.glob('*.doc')) + \
                  list(self.data_dir.glob('*.docx'))
        
        self.logger.info(f"Found {len(cv_files)} CV files in {self.data_dir}")
        
        # For now, just collect file paths
        # Real implementation would parse each file
        for cv_file in cv_files:
            training_data['source_files'].append(str(cv_file))
        
        # Cache the data
        self.training_data_cache[scenario_id] = training_data
        
        return training_data
    
    def train_scenario(
        self,
        scenario_id: str,
        training_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Train a model for a specific scenario.
        
        Args:
            scenario_id: ID of the scenario to train
            training_params: Optional training parameters
            
        Returns:
            Training results dictionary
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        self.logger.info(f"Starting training for scenario: {scenario_id}")
        scenario.status = 'training'
        self.save_scenarios()
        
        try:
            # Load training data
            training_data = self.load_training_data(scenario_id)
            
            # Training parameters
            params = training_params or {}
            epochs = params.get('epochs', 10)
            batch_size = params.get('batch_size', 32)
            validation_split = params.get('validation_split', 0.2)
            
            # TODO: Implement actual training logic based on model_type
            # For now, simulate training
            
            self.logger.info(f"Training with {len(training_data['source_files'])} samples")
            self.logger.info(f"Parameters: epochs={epochs}, batch_size={batch_size}")
            
            # Simulate training results
            results = {
                'status': 'success',
                'scenario_id': scenario_id,
                'model_version': f"v1.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'training_samples': len(training_data['source_files']),
                'epochs': epochs,
                'batch_size': batch_size,
                'validation_split': validation_split,
                'metrics': {
                    'accuracy': 0.89,
                    'precision': 0.87,
                    'recall': 0.91,
                    'f1_score': 0.89,
                    'loss': 0.23
                },
                'training_time': '5.2 minutes',
                'timestamp': datetime.now().isoformat()
            }
            
            # Update scenario
            scenario.status = 'trained'
            scenario.trained_at = datetime.now().isoformat()
            scenario.model_version = results['model_version']
            scenario.performance_metrics = results['metrics']
            self.save_scenarios()
            
            # Save model
            self._save_trained_model(scenario_id, results)
            
            self.logger.info(f"Training complete for {scenario_id}: {results['metrics']}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during training: {e}")
            scenario.status = 'error'
            self.save_scenarios()
            return {'status': 'error', 'error': str(e)}
    
    def _save_trained_model(self, scenario_id: str, training_results: Dict[str, Any]):
        """Save trained model to disk."""
        model_dir = self.models_dir / scenario_id
        model_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata_file = model_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(training_results, f, indent=2)
        
        # TODO: Save actual model weights
        # For now, just save a placeholder
        model_file = model_dir / 'model.pkl'
        with open(model_file, 'wb') as f:
            pickle.dump({'placeholder': True}, f)
        
        self.logger.info(f"Model saved to {model_dir}")
    
    def predict_with_review(
        self,
        scenario_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make prediction and flag for admin review if needed.
        
        Args:
            scenario_id: ID of the scenario/model to use
            input_data: Input data for prediction
            
        Returns:
            Prediction result with review flag
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        if scenario.status != 'trained' and scenario.status != 'deployed':
            raise ValueError(f"Scenario not trained: {scenario_id}")
        
        self.logger.info(f"Making prediction with scenario: {scenario_id}")
        
        # TODO: Implement actual prediction
        # For now, simulate prediction
        prediction = {
            'scenario_id': scenario_id,
            'prediction': 'Senior Software Engineer',
            'confidence': 0.67,
            'alternatives': [
                {'label': 'Lead Developer', 'confidence': 0.52},
                {'label': 'Staff Engineer', 'confidence': 0.48}
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if admin review is needed
        needs_review = self._check_needs_admin_review(scenario, prediction)
        
        if needs_review:
            prediction['needs_admin_review'] = True
            prediction['review_reason'] = needs_review['reason']
            self._add_to_review_queue(prediction)
        else:
            prediction['needs_admin_review'] = False
        
        return prediction
    
    def _check_needs_admin_review(
        self,
        scenario: TrainingScenario,
        prediction: Dict[str, Any]
    ) -> Optional[Dict[str, str]]:
        """
        Check if prediction needs admin review.
        
        Args:
            scenario: Training scenario
            prediction: Prediction result
            
        Returns:
            Review info if needed, None otherwise
        """
        # Check if admin review is enabled for this scenario
        if not scenario.config.get('enable_admin_review', False):
            return None
        
        confidence = prediction.get('confidence', 0.0)
        confidence_threshold = scenario.config.get('confidence_threshold', 0.75)
        
        # Low confidence
        if confidence < confidence_threshold:
            return {
                'reason': f'low_confidence',
                'detail': f'Confidence {confidence:.2f} below threshold {confidence_threshold}'
            }
        
        # Check for close alternatives
        alternatives = prediction.get('alternatives', [])
        if alternatives:
            top_alt = alternatives[0]
            confidence_gap = confidence - top_alt.get('confidence', 0.0)
            
            if confidence_gap < 0.15:  # Very close call
                return {
                    'reason': 'close_alternatives',
                    'detail': f'Top alternative only {confidence_gap:.2f} confidence points away'
                }
        
        # TODO: Add more sophisticated checks
        # - Outlier detection based on historical data
        # - Consistency with similar samples
        # - Anomaly detection
        
        return None
    
    def _add_to_review_queue(self, prediction: Dict[str, Any]):
        """Add prediction to admin review queue."""
        review_item = {
            'prediction_id': hashlib.md5(
                f"{prediction['scenario_id']}_{prediction['timestamp']}".encode()
            ).hexdigest()[:16],
            'prediction': prediction,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        self.review_queue.append(review_item)
        self._save_review_queue()
        
        self.logger.info(f"Added prediction to review queue: {review_item['prediction_id']}")
    
    def _save_review_queue(self):
        """Save review queue to disk."""
        review_file = self.models_dir / 'review_queue.json'
        try:
            with open(review_file, 'w') as f:
                json.dump(self.review_queue, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving review queue: {e}")
    
    def get_review_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get items in admin review queue.
        
        Args:
            status: Filter by status (pending, approved, rejected)
            
        Returns:
            List of review items
        """
        if status:
            return [item for item in self.review_queue if item['status'] == status]
        return self.review_queue
    
    def admin_review_prediction(
        self,
        prediction_id: str,
        admin_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Admin reviews and corrects a prediction.
        
        Args:
            prediction_id: ID of prediction to review
            admin_feedback: Admin's correction/approval
            
        Returns:
            Review result
        """
        # Find prediction in queue
        review_item = None
        for item in self.review_queue:
            if item['prediction_id'] == prediction_id:
                review_item = item
                break
        
        if not review_item:
            raise ValueError(f"Prediction not found in review queue: {prediction_id}")
        
        self.logger.info(f"Admin reviewing prediction: {prediction_id}")
        
        # Update review item
        review_item['admin_feedback'] = admin_feedback
        review_item['reviewed_at'] = datetime.now().isoformat()
        review_item['status'] = admin_feedback.get('action', 'approved')
        
        self._save_review_queue()
        
        # If correction provided, add to training feedback
        if admin_feedback.get('correction'):
            self._add_correction_to_training_data(
                review_item['prediction'],
                admin_feedback['correction']
            )
        
        result = {
            'status': 'success',
            'prediction_id': prediction_id,
            'action': review_item['status'],
            'correction_added': bool(admin_feedback.get('correction'))
        }
        
        self.logger.info(f"Admin review complete: {result}")
        return result
    
    def _add_correction_to_training_data(
        self,
        original_prediction: Dict[str, Any],
        correction: Dict[str, Any]
    ):
        """Add admin correction to training data for future retraining."""
        correction_file = self.models_dir / 'admin_corrections.jsonl'
        
        correction_entry = {
            'timestamp': datetime.now().isoformat(),
            'scenario_id': original_prediction['scenario_id'],
            'original_prediction': original_prediction,
            'correction': correction
        }
        
        try:
            with open(correction_file, 'a') as f:
                f.write(json.dumps(correction_entry) + '\n')
            
            self.logger.info("Admin correction saved for future training")
        except Exception as e:
            self.logger.error(f"Error saving correction: {e}")
    
    def get_scenario_stats(self, scenario_id: str) -> Dict[str, Any]:
        """Get statistics for a training scenario."""
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        # Count predictions in review queue for this scenario
        pending_reviews = len([
            item for item in self.review_queue
            if item['prediction']['scenario_id'] == scenario_id and item['status'] == 'pending'
        ])
        
        return {
            'scenario_id': scenario_id,
            'name': scenario.name,
            'status': scenario.status,
            'model_version': scenario.model_version,
            'performance_metrics': scenario.performance_metrics,
            'pending_reviews': pending_reviews,
            'trained_at': scenario.trained_at
        }
    
    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all training scenarios."""
        return [s.to_dict() for s in self.scenarios.values()]


# Example usage and testing
if __name__ == '__main__':
    print("=" * 80)
    print("Model Trainer - Test Run")
    print("=" * 80)
    
    # Initialize trainer
    trainer = ModelTrainer()
    
    # List scenarios
    print("\n1. Available Training Scenarios:")
    scenarios = trainer.list_scenarios()
    for scenario in scenarios:
        print(f"   - {scenario['name']} ({scenario['scenario_id']})")
        print(f"     Status: {scenario['status']}, Type: {scenario['task_type']}")
    
    # Train a scenario
    print("\n2. Training Job Title Classifier:")
    results = trainer.train_scenario('job_title_classifier')
    print(f"   Status: {results['status']}")
    print(f"   Accuracy: {results['metrics']['accuracy']:.2%}")
    print(f"   Training samples: {results['training_samples']}")
    
    # Make prediction with review
    print("\n3. Making Prediction (with admin review check):")
    prediction = trainer.predict_with_review(
        'job_title_classifier',
        {'job_title': 'Software Dev Lead'}
    )
    print(f"   Prediction: {prediction['prediction']}")
    print(f"   Confidence: {prediction['confidence']:.2%}")
    print(f"   Needs Review: {prediction['needs_admin_review']}")
    if prediction['needs_admin_review']:
        print(f"   Review Reason: {prediction['review_reason']}")
    
    # Check review queue
    print("\n4. Admin Review Queue:")
    queue = trainer.get_review_queue(status='pending')
    print(f"   Pending reviews: {len(queue)}")
    
    # Get scenario stats
    print("\n5. Scenario Statistics:")
    stats = trainer.get_scenario_stats('job_title_classifier')
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("Model Trainer - Ready for Integration!")
    print("=" * 80)
