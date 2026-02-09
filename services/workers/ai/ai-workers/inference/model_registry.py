"""
Model Registry - Unified Management of Trained AI Models
=========================================================

Purpose:
  - Track all trained model versions, metrics, and metadata
  - Load best/latest models for inference
  - Manage model deployment and versioning
  - Support A/B testing between model versions

Usage:
  from model_registry import ModelRegistry
  registry = ModelRegistry()
  model = registry.get_model('bayesian_classifier', version='latest')
"""

import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any
import hashlib


class ModelRegistry:
    """Central registry for all trained AI models"""

    def __init__(self, registry_dir: str = "trained_models", models_dir: str = "trained_models"):
        """
        Initialize model registry
        
        Args:
            registry_dir: Directory where registry.json is stored
            models_dir: Directory where model files are stored
        """
        self.registry_dir = Path(registry_dir)
        self.models_dir = Path(models_dir)
        self.registry_file = self.registry_dir / "registry.json"

        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load existing registry or create new one"""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)

        return {
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat(),
            'models': {},
            'deployments': {}
        }

    def _save_registry(self):
        """Persist registry to disk"""
        self.registry['updated'] = datetime.now().isoformat()

        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register_model(
        self,
        model_name: str,
        model_file: str,
        metadata: Dict[str, Any],
        model_type: str = 'sklearn'
    ) -> str:
        """Register a newly trained model"""
        if model_name not in self.registry['models']:
            self.registry['models'][model_name] = {
                'versions': {},
                'latest': None,
                'current_deployment': None
            }

        existing_versions = len(self.registry['models'][model_name]['versions'])
        version_id = f"v{existing_versions + 1}.0.0"
        file_hash = self._calculate_file_hash(model_file)

        self.registry['models'][model_name]['versions'][version_id] = {
            'timestamp': datetime.now().isoformat(),
            'file': model_file,
            'file_hash': file_hash,
            'type': model_type,
            'metadata': metadata,
            'status': 'trained',
            'deployed': False
        }

        self.registry['models'][model_name]['latest'] = version_id
        self._save_registry()
        print(f"✅ Registered {model_name} version {version_id}")
        return version_id

    def get_model(
        self,
        model_name: str,
        version: str = 'latest'
    ) -> Optional[Any]:
        """Load a trained model"""
        if model_name not in self.registry['models']:
            print(f"❌ Model not found: {model_name}")
            return None

        model_info = self.registry['models'][model_name]

        if version == 'latest':
            version = model_info['latest']
        elif version == 'deployed':
            version = model_info['current_deployment']

        if not version or version not in model_info['versions']:
            print(f"❌ Version not found: {model_name} {version}")
            return None

        version_info = model_info['versions'][version]
        model_file = Path(version_info['file'])

        # Fix relative paths if needed, assuming models are relative to registry root
        if not model_file.is_absolute():
            model_file = self.models_dir / model_file

        if not model_file.exists():
            print(f"❌ Model file not found: {model_file}")
            return None

        try:
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            print(f"✅ Loaded {model_name} {version}")
            return model
        except Exception as e:
            print(f"❌ Error loading {model_name}: {e}")
            return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
             return "hash_calc_error"

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        return self.registry['models']
