"""
Expert System Engine for IntelliCV Backend

This engine provides rule-based validation and explainability for:
- Validation of AI predictions against business rules
- Explainable AI (why a prediction was made)
- Admin-editable rules (human-in-the-loop)
- Quality control and consistency checking

Created: October 14, 2025
Part of: Backend-Admin Reorientation Project - Phase 2
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
import re

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


class Rule:
    """
    Represents a single business rule in the expert system.
    """
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: str,
        action: str,
        priority: int = 5,
        enabled: bool = True,
        category: str = 'general'
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.condition = condition  # Python expression or pattern
        self.action = action  # Action to take if condition matches
        self.priority = priority  # 1-10, higher = more important
        self.enabled = enabled
        self.category = category  # job_title, skills, company, etc.
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        self.trigger_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'condition': self.condition,
            'action': self.action,
            'priority': self.priority,
            'enabled': self.enabled,
            'category': self.category,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'trigger_count': self.trigger_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Create rule from dictionary."""
        rule = cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            condition=data['condition'],
            action=data['action'],
            priority=data.get('priority', 5),
            enabled=data.get('enabled', True),
            category=data.get('category', 'general')
        )
        rule.created_at = data.get('created_at', rule.created_at)
        rule.modified_at = data.get('modified_at', rule.modified_at)
        rule.trigger_count = data.get('trigger_count', 0)
        return rule


class ExpertSystemEngine:
    """
    Expert System Engine for rule-based validation and explainability.
    
    Features:
    - Business rules validation
    - Explainable AI decisions
    - Admin-editable rules
    - Quality control and consistency checking
    - Integration with Neural Network and other AI engines
    """
    
    def __init__(self, rules_path: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize the Expert System Engine.
        
        Args:
            rules_path: Path to rules JSON file (optional)
            config: Configuration dictionary (optional)
        """
        self.logger = self._setup_logging()
        self.config = config or self._default_config()
        
        # Rules storage
        self.rules: Dict[str, Rule] = {}
        self.rules_by_category: Dict[str, List[str]] = {}
        
        # Rules file path
        if rules_path:
            self.rules_path = Path(rules_path)
        else:
            rules_dir = Path(__file__).parent.parent / 'data' / 'rules'
            rules_dir.mkdir(parents=True, exist_ok=True)
            self.rules_path = rules_dir / 'expert_rules.json'
        
        # Validation history
        self.validation_history = []
        
        # Performance tracking
        self.rule_performance = {}
        
        self.logger.info(f"Expert System Engine initialized with config: {self.config}")
        
        # Load rules if available
        if self.rules_path.exists():
            self._load_rules()
        else:
            self.logger.info("No existing rules found. Initializing with default rules.")
            self._initialize_default_rules()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup dedicated logger for Expert System Engine."""
        logger = logging.getLogger('ExpertSystemEngine')
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # File handler
        log_file = log_dir / f'expert_system_{datetime.now().strftime("%Y%m%d")}.log'
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
            'strict_validation': False,  # If True, all rules must pass
            'explain_all_decisions': True,
            'track_rule_performance': True,
            'auto_save_rules': True,
            'max_validation_history': 10000
        }
    
    def _initialize_default_rules(self):
        """Initialize default business rules."""
        default_rules = [
            # Job Title Rules
            Rule(
                rule_id='JT001',
                name='Senior Requires Experience',
                description='Senior titles require 5+ years experience',
                condition="'senior' in prediction.lower() and experience_years < 5",
                action='flag_confidence_low',
                priority=8,
                category='job_title'
            ),
            Rule(
                rule_id='JT002',
                name='CXO Requires Leadership',
                description='C-level positions require leadership skills',
                condition="prediction.lower() in ['ceo', 'cto', 'cfo', 'coo'] and 'leadership' not in skills",
                action='flag_missing_skills',
                priority=9,
                category='job_title'
            ),
            Rule(
                rule_id='JT003',
                name='Junior vs Senior Consistency',
                description='Cannot be both junior and senior',
                condition="'junior' in prediction.lower() and 'senior' in prediction.lower()",
                action='reject_prediction',
                priority=10,
                category='job_title'
            ),
            
            # Skills Rules
            Rule(
                rule_id='SK001',
                name='Programming Language Required for Developer',
                description='Developer roles must have programming languages',
                condition="'developer' in job_title.lower() and not any(lang in skills for lang in ['python', 'java', 'javascript', 'c++', 'c#'])",
                action='flag_missing_skills',
                priority=8,
                category='skills'
            ),
            Rule(
                rule_id='SK002',
                name='Duplicate Skills',
                description='Flag duplicate or redundant skills',
                condition='len(skills) != len(set(skills))',
                action='flag_duplicates',
                priority=5,
                category='skills'
            ),
            
            # Company Rules
            Rule(
                rule_id='CO001',
                name='Company Name Formatting',
                description='Company names should be properly capitalized',
                condition='company_name and company_name.islower()',
                action='suggest_formatting',
                priority=4,
                category='company'
            ),
            Rule(
                rule_id='CO002',
                name='Company vs Freelance Consistency',
                description='Cannot have company and be freelance',
                condition="company_name and 'freelance' in job_title.lower()",
                action='flag_inconsistency',
                priority=7,
                category='company'
            ),
            
            # Industry Rules
            Rule(
                rule_id='IN001',
                name='Industry-Skills Alignment',
                description='Skills should align with industry',
                condition="industry == 'Healthcare' and 'medical' not in skills and 'healthcare' not in skills",
                action='flag_misalignment',
                priority=6,
                category='industry'
            ),
            
            # Experience Rules
            Rule(
                rule_id='EX001',
                name='Reasonable Experience Years',
                description='Experience years should be reasonable (0-50)',
                condition='experience_years < 0 or experience_years > 50',
                action='reject_prediction',
                priority=10,
                category='experience'
            ),
            Rule(
                rule_id='EX002',
                name='Experience Matches Timeline',
                description='Total experience should not exceed career timeline',
                condition='experience_years > (current_year - graduation_year + 5)',
                action='flag_timeline_mismatch',
                priority=8,
                category='experience'
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
        
        self.logger.info(f"Initialized {len(default_rules)} default rules")
        
        # Save default rules
        if self.config['auto_save_rules']:
            self._save_rules()
    
    def add_rule(self, rule: Rule) -> bool:
        """
        Add a new rule to the expert system.
        
        Args:
            rule: Rule object to add
            
        Returns:
            True if added successfully
        """
        try:
            self.rules[rule.rule_id] = rule
            
            # Add to category index
            if rule.category not in self.rules_by_category:
                self.rules_by_category[rule.category] = []
            if rule.rule_id not in self.rules_by_category[rule.category]:
                self.rules_by_category[rule.category].append(rule.rule_id)
            
            self.logger.info(f"Added rule: {rule.rule_id} - {rule.name}")
            
            if self.config['auto_save_rules']:
                self._save_rules()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding rule: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing rule.
        
        Args:
            rule_id: ID of rule to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            if rule_id not in self.rules:
                self.logger.warning(f"Rule {rule_id} not found")
                return False
            
            rule = self.rules[rule_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.modified_at = datetime.now().isoformat()
            
            self.logger.info(f"Updated rule: {rule_id}")
            
            if self.config['auto_save_rules']:
                self._save_rules()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating rule: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        try:
            if rule_id not in self.rules:
                self.logger.warning(f"Rule {rule_id} not found")
                return False
            
            rule = self.rules[rule_id]
            
            # Remove from category index
            if rule.category in self.rules_by_category:
                self.rules_by_category[rule.category].remove(rule_id)
            
            # Remove rule
            del self.rules[rule_id]
            
            self.logger.info(f"Deleted rule: {rule_id}")
            
            if self.config['auto_save_rules']:
                self._save_rules()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting rule: {e}")
            return False
    
    def validate_prediction(
        self,
        prediction: Any,
        context: Dict[str, Any],
        category: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Validate a prediction against expert rules.
        
        Args:
            prediction: The prediction to validate
            context: Context data for rule evaluation
            category: Optional category filter
            
        Returns:
            Tuple of (is_valid, triggered_rules, explanation)
        """
        try:
            self.logger.info(f"Validating prediction: {prediction} (category: {category})")
            
            triggered_rules = []
            is_valid = True
            explanation_parts = []
            
            # Get rules to check
            if category and category in self.rules_by_category:
                rule_ids = self.rules_by_category[category]
            else:
                rule_ids = list(self.rules.keys())
            
            # Check each rule
            for rule_id in rule_ids:
                rule = self.rules[rule_id]
                
                # Skip disabled rules
                if not rule.enabled:
                    continue
                
                # Evaluate rule condition
                try:
                    # Build evaluation context
                    eval_context = {
                        'prediction': prediction,
                        **context
                    }
                    
                    # Evaluate condition (safely)
                    condition_met = self._safe_eval(rule.condition, eval_context)
                    
                    if condition_met:
                        # Rule triggered
                        rule.trigger_count += 1
                        
                        triggered_rule = {
                            'rule_id': rule.rule_id,
                            'name': rule.name,
                            'description': rule.description,
                            'action': rule.action,
                            'priority': rule.priority
                        }
                        
                        triggered_rules.append(triggered_rule)
                        
                        # Add to explanation
                        explanation_parts.append(f"Rule '{rule.name}': {rule.description}")
                        
                        # Check if this invalidates the prediction
                        if rule.action in ['reject_prediction', 'flag_inconsistency']:
                            is_valid = False
                        
                        self.logger.info(f"Rule triggered: {rule.rule_id} - {rule.name}")
                
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule_id}: {e}")
            
            # Sort triggered rules by priority
            triggered_rules.sort(key=lambda x: x['priority'], reverse=True)
            
            # Build explanation
            if triggered_rules:
                explanation = "Validation issues found:\n" + "\n".join(explanation_parts)
            else:
                explanation = "No validation issues found. Prediction passes all expert rules."
            
            # Track validation
            if self.config['track_rule_performance']:
                self._track_validation(prediction, context, is_valid, triggered_rules)
            
            self.logger.info(f"Validation result: {'VALID' if is_valid else 'INVALID'} ({len(triggered_rules)} rules triggered)")
            
            return is_valid, triggered_rules, explanation
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            return True, [], f"Validation error: {e}"
    
    def _safe_eval(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate a condition with context.
        
        Args:
            condition: Python expression to evaluate
            context: Variables available for evaluation
            
        Returns:
            True if condition is met
        """
        try:
            # Create safe evaluation environment
            safe_globals = {
                '__builtins__': {},
                'len': len,
                'any': any,
                'all': all,
                'set': set,
                're': re
            }
            
            # Evaluate
            result = eval(condition, safe_globals, context)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def _track_validation(
        self,
        prediction: Any,
        context: Dict[str, Any],
        is_valid: bool,
        triggered_rules: List[Dict[str, Any]]
    ):
        """Track validation for performance analysis."""
        validation_entry = {
            'timestamp': datetime.now().isoformat(),
            'prediction': str(prediction),
            'context': {k: str(v) for k, v in context.items()},
            'is_valid': is_valid,
            'triggered_rules': [r['rule_id'] for r in triggered_rules]
        }
        
        self.validation_history.append(validation_entry)
        
        # Trim history if too long
        if len(self.validation_history) > self.config['max_validation_history']:
            self.validation_history = self.validation_history[-self.config['max_validation_history']:]
    
    def _load_rules(self):
        """Load rules from JSON file."""
        try:
            self.logger.info(f"Loading rules from {self.rules_path}")
            
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing rules
            self.rules = {}
            self.rules_by_category = {}
            
            # Load rules
            for rule_data in data.get('rules', []):
                rule = Rule.from_dict(rule_data)
                self.add_rule(rule)
            
            self.logger.info(f"Loaded {len(self.rules)} rules")
            
        except Exception as e:
            self.logger.error(f"Error loading rules: {e}")
    
    def _save_rules(self):
        """Save rules to JSON file."""
        try:
            data = {
                'rules': [rule.to_dict() for rule in self.rules.values()],
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.rules_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.rules)} rules to {self.rules_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving rules: {e}")
    
    def get_rules(self, category: Optional[str] = None, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """Get all rules, optionally filtered by category."""
        if category and category in self.rules_by_category:
            rule_ids = self.rules_by_category[category]
        else:
            rule_ids = list(self.rules.keys())
        
        rules = [self.rules[rid] for rid in rule_ids]
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        return [r.to_dict() for r in rules]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the expert system."""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
            'categories': list(self.rules_by_category.keys()),
            'total_validations': len(self.validation_history),
            'most_triggered_rules': self._get_most_triggered_rules(5),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_most_triggered_rules(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently triggered rules."""
        rules_with_counts = [
            {
                'rule_id': r.rule_id,
                'name': r.name,
                'trigger_count': r.trigger_count
            }
            for r in self.rules.values()
        ]
        
        rules_with_counts.sort(key=lambda x: x['trigger_count'], reverse=True)
        
        return rules_with_counts[:limit]


# Example usage and testing
if __name__ == '__main__':
    print("=" * 80)
    print("Expert System Engine - Test Run")
    print("=" * 80)
    
    # Initialize engine
    es_engine = ExpertSystemEngine()
    
    # Test 1: Valid prediction
    print("\n1. Testing Valid Prediction:")
    is_valid, triggered, explanation = es_engine.validate_prediction(
        prediction="Senior Software Engineer",
        context={
            'experience_years': 8,
            'skills': ['python', 'java', 'leadership'],
            'job_title': 'Senior Software Engineer',
            'company_name': 'Google Inc'
        },
        category='job_title'
    )
    print(f"   Valid: {is_valid}")
    print(f"   Triggered Rules: {len(triggered)}")
    print(f"   Explanation: {explanation}")
    
    # Test 2: Invalid prediction (senior without experience)
    print("\n2. Testing Invalid Prediction (Senior without experience):")
    is_valid, triggered, explanation = es_engine.validate_prediction(
        prediction="Senior Software Engineer",
        context={
            'experience_years': 2,
            'skills': ['python'],
            'job_title': 'Senior Software Engineer',
            'company_name': 'Startup Inc'
        },
        category='job_title'
    )
    print(f"   Valid: {is_valid}")
    print(f"   Triggered Rules: {len(triggered)}")
    for rule in triggered:
        print(f"     - {rule['name']} (Priority: {rule['priority']})")
    
    # Test 3: Get performance metrics
    print("\n3. Performance Metrics:")
    metrics = es_engine.get_performance_metrics()
    for key, value in metrics.items():
        if key != 'most_triggered_rules':
            print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("Expert System Engine - Ready for Integration!")
    print("=" * 80)
