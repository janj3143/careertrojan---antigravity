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

    def __init__(self, registry_dir: str = "admin_portal/models", models_dir: str = "admin_portal/models"):
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
        """
        Register a newly trained model

        Args:
            model_name: Name of the model (e.g., 'bayesian_classifier')
            model_file: Path to saved model file
            metadata: Model metadata (accuracy, training_samples, etc.)
            model_type: Type of model ('sklearn', 'neural', 'custom')

        Returns:
            Version ID (e.g., 'v1.0.0')
        """
        if model_name not in self.registry['models']:
            self.registry['models'][model_name] = {
                'versions': {},
                'latest': None,
                'current_deployment': None
            }

        # Calculate version number
        existing_versions = len(self.registry['models'][model_name]['versions'])
        version_id = f"v{existing_versions + 1}.0.0"

        # Calculate file hash for integrity checking
        file_hash = self._calculate_file_hash(model_file)

        # Store model metadata
        self.registry['models'][model_name]['versions'][version_id] = {
            'timestamp': datetime.now().isoformat(),
            'file': model_file,
            'file_hash': file_hash,
            'type': model_type,
            'metadata': metadata,
            'status': 'trained',
            'deployed': False
        }

        # Update latest version
        self.registry['models'][model_name]['latest'] = version_id

        self._save_registry()

        print(f"✅ Registered {model_name} version {version_id}")

        return version_id

    def register_vectorizer(
        self,
        vectorizer_name: str,
        vectorizer_file: str,
        model_name: str,
        metadata: Dict[str, Any]
    ):
        """Register a vectorizer associated with a model"""
        model_key = f"{model_name}_vectorizer"

        if model_key not in self.registry['models']:
            self.registry['models'][model_key] = {
                'versions': {},
                'latest': None,
                'current_deployment': None,
                'associated_model': model_name
            }

        # Use same version as associated model
        version_id = self.registry['models'][model_name]['latest']

        file_hash = self._calculate_file_hash(vectorizer_file)

        self.registry['models'][model_key]['versions'][version_id] = {
            'timestamp': datetime.now().isoformat(),
            'file': vectorizer_file,
            'file_hash': file_hash,
            'type': 'vectorizer',
            'metadata': metadata,
            'status': 'trained',
            'deployed': False,
            'associated_model': model_name
        }

        self.registry['models'][model_key]['latest'] = version_id

        self._save_registry()

        print(f"✅ Registered {model_key} version {version_id}")

    def get_model(
        self,
        model_name: str,
        version: str = 'latest'
    ) -> Optional[Any]:
        """
        Load a trained model

        Args:
            model_name: Name of the model
            version: Version to load ('latest', 'deployed', or specific version like 'v1.0.0')

        Returns:
            Loaded model object or None if not found
        """
        if model_name not in self.registry['models']:
            print(f"❌ Model not found: {model_name}")
            return None

        model_info = self.registry['models'][model_name]

        # Resolve version
        if version == 'latest':
            version = model_info['latest']
        elif version == 'deployed':
            version = model_info['current_deployment']

        if version not in model_info['versions']:
            print(f"❌ Version not found: {model_name} {version}")
            return None

        version_info = model_info['versions'][version]
        model_file = Path(version_info['file'])

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

    def get_vectorizer(self, model_name: str, version: str = 'latest') -> Optional[Any]:
        """Load vectorizer associated with a model"""
        vectorizer_key = f"{model_name}_vectorizer"
        return self.get_model(vectorizer_key, version)

    def deploy_model(self, model_name: str, version: str = 'latest'):
        """
        Mark a model version as deployed/active

        Args:
            model_name: Name of the model
            version: Version to deploy
        """
        if model_name not in self.registry['models']:
            print(f"❌ Model not found: {model_name}")
            return False

        model_info = self.registry['models'][model_name]

        if version == 'latest':
            version = model_info['latest']

        if version not in model_info['versions']:
            print(f"❌ Version not found: {model_name} {version}")
            return False

        # Mark all versions as not deployed
        for v_id, v_info in model_info['versions'].items():
            v_info['deployed'] = False

        # Mark this version as deployed
        model_info['versions'][version]['deployed'] = True
        model_info['current_deployment'] = version

        # If this is a model with vectorizer, deploy vectorizer too
        vectorizer_key = f"{model_name}_vectorizer"
        if vectorizer_key in self.registry['models']:
            vectorizer_info = self.registry['models'][vectorizer_key]
            for v_id, v_info in vectorizer_info['versions'].items():
                v_info['deployed'] = False
            if version in vectorizer_info['versions']:
                vectorizer_info['versions'][version]['deployed'] = True
                vectorizer_info['current_deployment'] = version

        self._save_registry()
        print(f"✅ Deployed {model_name} {version}")
        return True

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered models and their versions"""
        return self.registry['models']

    def get_model_info(self, model_name: str, version: str = 'latest') -> Optional[Dict[str, Any]]:
        """Get metadata about a specific model version"""
        if model_name not in self.registry['models']:
            return None

        model_info = self.registry['models'][model_name]

        if version == 'latest':
            version = model_info['latest']
        elif version == 'deployed':
            version = model_info['current_deployment']

        if version not in model_info['versions']:
            return None

        return model_info['versions'][version]

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of model file for integrity checking"""
        sha256_hash = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def verify_integrity(self, model_name: str, version: str = 'latest') -> bool:
        """Verify model file hasn't been corrupted"""
        version_info = self.get_model_info(model_name, version)

        if not version_info:
            return False

        file_hash = self._calculate_file_hash(version_info['file'])
        return file_hash == version_info['file_hash']

    def rollback_deployment(self, model_name: str) -> bool:
        """Rollback to previous model version"""
        if model_name not in self.registry['models']:
            print(f"❌ Model not found: {model_name}")
            return False

        model_info = self.registry['models'][model_name]
        versions = list(model_info['versions'].keys())

        if len(versions) < 2:
            print(f"❌ No previous version to rollback to")
            return False

        # Find previous deployed version
        previous_version = None
        for v_id in reversed(versions[:-1]):  # All except latest
            if model_info['versions'][v_id]['deployed']:
                previous_version = v_id
                break

        if not previous_version:
            previous_version = versions[-2]

        return self.deploy_model(model_name, previous_version)

    def generate_registry_report(self) -> str:
        """Generate human-readable registry report"""
        report = []
        report.append("\n" + "="*70)
        report.append("MODEL REGISTRY REPORT")
        report.append("="*70)

        for model_name, model_info in self.registry['models'].items():
            report.append(f"\n📦 {model_name}")
            report.append(f"   Latest: {model_info['latest']}")
            report.append(f"   Deployed: {model_info['current_deployment']}")

            report.append(f"   Versions:")
            for version_id, version_info in model_info['versions'].items():
                deployed = "✅" if version_info['deployed'] else "  "
                report.append(f"      {deployed} {version_id} ({version_info['status']})")
                report.append(f"         Timestamp: {version_info['timestamp']}")

                if 'metadata' in version_info:
                    for key, value in version_info['metadata'].items():
                        if key not in ['model_file', 'vectorizer_file']:
                            report.append(f"         {key}: {value}")

        report.append("\n" + "="*70 + "\n")

        return "\n".join(report)

    def print_registry(self):
        """Print registry report to console"""
        print(self.generate_registry_report())


if __name__ == "__main__":
    # Test registry
    registry = ModelRegistry()
    registry.print_registry()
