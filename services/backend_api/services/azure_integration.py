"""
Azure Integration Framework for IntelliCV
Comprehensive Azure cloud services integration with security and scalability
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import base64

# Azure SDK imports with fallbacks
AZURE_AVAILABLE = {}

# Azure Storage
try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    from azure.storage.blob import ContentSettings
    AZURE_AVAILABLE['storage'] = True
except ImportError:
    AZURE_AVAILABLE['storage'] = False
    print("[WARNING] Azure Storage SDK not available - install: pip install azure-storage-blob")

# Azure Identity
try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.identity import ManagedIdentityCredential
    AZURE_AVAILABLE['identity'] = True
except ImportError:
    AZURE_AVAILABLE['identity'] = False
    print("[WARNING] Azure Identity SDK not available - install: pip install azure-identity")

# Azure Key Vault
try:
    from azure.keyvault.secrets import SecretClient
    AZURE_AVAILABLE['keyvault'] = True
except ImportError:
    AZURE_AVAILABLE['keyvault'] = False
    print("[WARNING] Azure Key Vault SDK not available - install: pip install azure-keyvault-secrets")

# Azure Cognitive Services
try:
    from azure.cognitiveservices.textanalytics import TextAnalyticsClient
    from azure.cognitiveservices.textanalytics.models import TextAnalyticsClientError
    AZURE_AVAILABLE['cognitive'] = True
except ImportError:
    AZURE_AVAILABLE['cognitive'] = False
    print("[WARNING] Azure Cognitive Services SDK not available - install: pip install azure-cognitiveservices-textanalytics")

# Azure OpenAI
try:
    from azure.ai.openai import OpenAIClient
    AZURE_AVAILABLE['openai'] = True
except ImportError:
    AZURE_AVAILABLE['openai'] = False
    print("[WARNING] Azure OpenAI SDK not available - install: pip install azure-ai-openai")

class AzureConfigurationManager:
    """
    Secure Azure configuration and credentials management
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Azure configuration manager"""
        self.config_path = config_path or "config/azure_settings.json"
        self.config_dir = Path(self.config_path).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Security keys storage
        self.keys_file = self.config_dir / "azure_keys.encrypted"
        self.local_config_file = Path(self.config_path)

        self.config = self._load_configuration()
        self.credentials = None

    def _load_configuration(self) -> Dict[str, Any]:
        """Load Azure configuration with secure defaults"""
        default_config = {
            "subscription_id": "",
            "tenant_id": "",
            "client_id": "",
            "resource_group": "intellicv-rg",
            "location": "eastus",
            "storage_account": "intellicvstorage",
            "keyvault_name": "intellicv-keyvault",
            "cognitive_services": {
                "text_analytics_endpoint": "",
                "openai_endpoint": "",
                "speech_service_endpoint": ""
            },
            "containers": {
                "ai_data": "ai-data-container",
                "processed_cvs": "processed-cvs",
                "company_data": "company-intelligence",
                "backups": "system-backups"
            },
            "security": {
                "use_managed_identity": True,
                "enable_encryption": True,
                "access_tier": "Hot",
                "retention_days": 90
            },
            "performance": {
                "connection_timeout": 30,
                "read_timeout": 60,
                "max_retries": 3,
                "backoff_factor": 0.3
            }
        }

        if self.local_config_file.exists():
            try:
                saved_config = json.loads(self.local_config_file.read_text())
                # Merge with defaults
                default_config.update(saved_config)
            except Exception as e:
                print(f"⚠️ Error loading Azure config: {e}")

        return default_config

    def save_configuration(self):
        """Save current configuration to file"""
        try:
            self.local_config_file.write_text(
                json.dumps(self.config, indent=2)
            )
            print("[OK] Azure configuration saved")
        except Exception as e:
            print(f"[ERROR] Error saving Azure config: {e}")

    def set_credentials(self,
                       subscription_id: str,
                       tenant_id: str,
                       client_id: str,
                       client_secret: Optional[str] = None):
        """Set Azure credentials securely"""
        self.config.update({
            "subscription_id": subscription_id,
            "tenant_id": tenant_id,
            "client_id": client_id
        })

        if client_secret:
            # In a real implementation, encrypt the secret
            self._store_encrypted_secret("client_secret", client_secret)

        self.save_configuration()

    def _store_encrypted_secret(self, key: str, value: str):
        """Store encrypted secret (simplified implementation)"""
        # In production, use proper encryption
        encoded = base64.b64encode(value.encode()).decode()

        secrets = {}
        if self.keys_file.exists():
            try:
                secrets = json.loads(
                    base64.b64decode(self.keys_file.read_text()).decode()
                )
            except:
                pass

        secrets[key] = encoded

        encrypted_data = base64.b64encode(
            json.dumps(secrets).encode()
        ).decode()

        self.keys_file.write_text(encrypted_data)

    def _get_encrypted_secret(self, key: str) -> Optional[str]:
        """Retrieve encrypted secret"""
        try:
            if not self.keys_file.exists():
                return None

            encrypted_data = self.keys_file.read_text()
            secrets = json.loads(
                base64.b64decode(encrypted_data).decode()
            )

            if key in secrets:
                return base64.b64decode(secrets[key]).decode()

        except Exception as e:
            print(f"⚠️ Error retrieving secret: {e}")

        return None

    def get_credential(self):
        """Get Azure credential object"""
        if not AZURE_AVAILABLE['identity']:
            print("[ERROR] Azure Identity SDK not available")
            return None

        if self.credentials:
            return self.credentials

        try:
            # Try managed identity first (for production)
            if self.config.get("security", {}).get("use_managed_identity", False):
                self.credentials = ManagedIdentityCredential()
                print("[OK] Using Managed Identity credential")
            else:
                # Use service principal
                client_secret = self._get_encrypted_secret("client_secret")
                if client_secret:
                    self.credentials = ClientSecretCredential(
                        tenant_id=self.config["tenant_id"],
                        client_id=self.config["client_id"],
                        client_secret=client_secret
                    )
                    print("[OK] Using Service Principal credential")
                else:
                    # Fallback to default credential
                    self.credentials = DefaultAzureCredential()
                    print("[OK] Using Default Azure credential")

        except Exception as e:
            print(f"[ERROR] Error creating Azure credential: {e}")
            return None

        return self.credentials

class AzureStorageManager:
    """
    Azure Blob Storage management for IntelliCV data
    """

    def __init__(self, config_manager: AzureConfigurationManager):
        """Initialize Azure Storage manager"""
        self.config_manager = config_manager
        self.config = config_manager.config
        self.blob_service_client = None
        self.storage_available = AZURE_AVAILABLE['storage']

        if self.storage_available:
            self._initialize_blob_service()

    def _initialize_blob_service(self):
        """Initialize Blob Storage service client"""
        try:
            credential = self.config_manager.get_credential()
            if not credential:
                print("❌ No Azure credential available")
                return

            storage_account = self.config["storage_account"]
            account_url = f"https://{storage_account}.blob.core.windows.net"

            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )

            print("✅ Azure Blob Storage client initialized")

        except Exception as e:
            print(f"❌ Error initializing Blob Storage: {e}")
            self.storage_available = False

    def create_containers(self) -> bool:
        """Create required storage containers"""
        if not self.storage_available or not self.blob_service_client:
            print("❌ Azure Storage not available")
            return False

        containers = self.config["containers"]
        created_count = 0

        for container_name in containers.values():
            try:
                container_client = self.blob_service_client.get_container_client(container_name)

                if not container_client.exists():
                    container_client.create_container()
                    print(f"✅ Created container: {container_name}")
                else:
                    print(f"ℹ️ Container exists: {container_name}")

                created_count += 1

            except Exception as e:
                print(f"❌ Error with container {container_name}: {e}")

        return created_count == len(containers)

    def upload_file(self,
                   local_file_path: str,
                   container_name: str,
                   blob_name: str,
                   overwrite: bool = False) -> bool:
        """Upload file to Azure Blob Storage"""

        if not self.storage_available or not self.blob_service_client:
            print("❌ Azure Storage not available")
            return False

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )

            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(
                    data,
                    overwrite=overwrite,
                    content_settings=ContentSettings(
                        content_type=self._get_content_type(local_file_path)
                    )
                )

            print(f"✅ Uploaded: {blob_name} to {container_name}")
            return True

        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False

    def download_file(self,
                     container_name: str,
                     blob_name: str,
                     local_file_path: str) -> bool:
        """Download file from Azure Blob Storage"""

        if not self.storage_available or not self.blob_service_client:
            print("❌ Azure Storage not available")
            return False

        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )

            # Create directory if it doesn't exist
            Path(local_file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(local_file_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())

            print(f"✅ Downloaded: {blob_name} from {container_name}")
            return True

        except Exception as e:
            print(f"❌ Download error: {e}")
            return False

    def list_blobs(self, container_name: str) -> List[str]:
        """List blobs in container"""

        if not self.storage_available or not self.blob_service_client:
            return []

        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            return [blob.name for blob in container_client.list_blobs()]

        except Exception as e:
            print(f"❌ List blobs error: {e}")
            return []

    def _get_content_type(self, file_path: str) -> str:
        """Get content type for file"""
        extension = Path(file_path).suffix.lower()

        content_types = {
            '.json': 'application/json',
            '.csv': 'text/csv',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.html': 'text/html'
        }

        return content_types.get(extension, 'application/octet-stream')

class AzureCognitiveServicesManager:
    """
    Azure Cognitive Services integration for advanced AI capabilities
    """

    def __init__(self, config_manager: AzureConfigurationManager):
        """Initialize Cognitive Services manager"""
        self.config_manager = config_manager
        self.config = config_manager.config
        self.cognitive_available = AZURE_AVAILABLE['cognitive']
        self.openai_available = AZURE_AVAILABLE['openai']

        self.text_analytics_client = None
        self.openai_client = None

        if self.cognitive_available:
            self._initialize_text_analytics()

        if self.openai_available:
            self._initialize_openai()

    def _initialize_text_analytics(self):
        """Initialize Text Analytics client"""
        try:
            endpoint = self.config["cognitive_services"]["text_analytics_endpoint"]
            if not endpoint:
                print("⚠️ Text Analytics endpoint not configured")
                return

            credential = self.config_manager.get_credential()
            if credential:
                self.text_analytics_client = TextAnalyticsClient(
                    endpoint=endpoint,
                    credential=credential
                )
                print("✅ Text Analytics client initialized")

        except Exception as e:
            print(f"❌ Text Analytics initialization error: {e}")

    def _initialize_openai(self):
        """Initialize Azure OpenAI client"""
        try:
            endpoint = self.config["cognitive_services"]["openai_endpoint"]
            if not endpoint:
                print("⚠️ Azure OpenAI endpoint not configured")
                return

            credential = self.config_manager.get_credential()
            if credential:
                self.openai_client = OpenAIClient(
                    endpoint=endpoint,
                    credential=credential
                )
                print("✅ Azure OpenAI client initialized")

        except Exception as e:
            print(f"❌ Azure OpenAI initialization error: {e}")

    def analyze_sentiment(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment using Azure Text Analytics"""

        if not self.text_analytics_client:
            print("❌ Text Analytics client not available")
            return []

        try:
            results = []
            response = self.text_analytics_client.analyze_sentiment(documents=texts)

            for idx, doc in enumerate(response):
                if hasattr(doc, 'error'):
                    results.append({
                        'text': texts[idx],
                        'error': str(doc.error)
                    })
                else:
                    results.append({
                        'text': texts[idx],
                        'sentiment': doc.sentiment,
                        'confidence_scores': {
                            'positive': doc.confidence_scores.positive,
                            'neutral': doc.confidence_scores.neutral,
                            'negative': doc.confidence_scores.negative
                        }
                    })

            return results

        except Exception as e:
            print(f"❌ Sentiment analysis error: {e}")
            return []

    def extract_key_phrases(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Extract key phrases using Azure Text Analytics"""

        if not self.text_analytics_client:
            print("❌ Text Analytics client not available")
            return []

        try:
            results = []
            response = self.text_analytics_client.extract_key_phrases(documents=texts)

            for idx, doc in enumerate(response):
                if hasattr(doc, 'error'):
                    results.append({
                        'text': texts[idx],
                        'error': str(doc.error)
                    })
                else:
                    results.append({
                        'text': texts[idx],
                        'key_phrases': doc.key_phrases
                    })

            return results

        except Exception as e:
            print(f"❌ Key phrase extraction error: {e}")
            return []

class IntelliCVAzureIntegration:
    """
    Main Azure integration class for IntelliCV
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize complete Azure integration"""
        self.config_manager = AzureConfigurationManager(config_path)
        self.storage_manager = AzureStorageManager(self.config_manager)
        self.cognitive_manager = AzureCognitiveServicesManager(self.config_manager)

        self.integration_status = {
            'config_loaded': True,
            'storage_available': self.storage_manager.storage_available,
            'cognitive_available': self.cognitive_manager.cognitive_available,
            'openai_available': self.cognitive_manager.openai_available,
            'credentials_configured': self.config_manager.get_credential() is not None
        }

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Azure integration status"""
        return {
            'azure_sdk_availability': AZURE_AVAILABLE,
            'integration_status': self.integration_status,
            'configuration': {
                'resource_group': self.config_manager.config.get('resource_group'),
                'location': self.config_manager.config.get('location'),
                'storage_account': self.config_manager.config.get('storage_account'),
                'containers_configured': len(self.config_manager.config.get('containers', {}))
            }
        }

    def setup_azure_account(self,
                           subscription_id: str,
                           tenant_id: str,
                           client_id: str,
                           client_secret: str) -> bool:
        """Setup Azure account credentials"""

        try:
            self.config_manager.set_credentials(
                subscription_id=subscription_id,
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

            # Test connection
            credential = self.config_manager.get_credential()
            if credential:
                # Reinitialize services with new credentials
                self.storage_manager = AzureStorageManager(self.config_manager)
                self.cognitive_manager = AzureCognitiveServicesManager(self.config_manager)

                # Create containers
                if self.storage_manager.storage_available:
                    self.storage_manager.create_containers()

                print("✅ Azure account setup completed")
                return True

        except Exception as e:
            print(f"❌ Azure account setup error: {e}")

        return False

    def upload_ai_data(self, data_directory: str) -> Dict[str, Any]:
        """Upload AI data to Azure Storage"""

        if not self.storage_manager.storage_available:
            return {'error': 'Azure Storage not available'}

        results = {
            'uploaded': 0,
            'failed': 0,
            'files': []
        }

        data_path = Path(data_directory)
        if not data_path.exists():
            return {'error': f'Directory not found: {data_directory}'}

        container = self.config_manager.config['containers']['ai_data']

        for file_path in data_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(data_path)
                blob_name = str(relative_path).replace('\\', '/')

                if self.storage_manager.upload_file(
                    str(file_path),
                    container,
                    blob_name
                ):
                    results['uploaded'] += 1
                    results['files'].append(f'✅ {blob_name}')
                else:
                    results['failed'] += 1
                    results['files'].append(f'❌ {blob_name}')

        return results

    def process_with_azure_ai(self, texts: List[str]) -> Dict[str, Any]:
        """Process texts with Azure Cognitive Services"""

        results = {
            'sentiment_analysis': [],
            'key_phrases': [],
            'processing_successful': False
        }

        if self.cognitive_manager.cognitive_available:
            results['sentiment_analysis'] = self.cognitive_manager.analyze_sentiment(texts)
            results['key_phrases'] = self.cognitive_manager.extract_key_phrases(texts)
            results['processing_successful'] = True
        else:
            results['error'] = 'Azure Cognitive Services not available'

        return results

# Global Azure integration instance
_azure_integration = None

def get_azure_integration() -> IntelliCVAzureIntegration:
    """Get global Azure integration instance"""
    global _azure_integration
    if _azure_integration is None:
        _azure_integration = IntelliCVAzureIntegration()
    return _azure_integration

def test_azure_integration():
    """Test Azure integration functionality"""
    azure = get_azure_integration()

    print("🔍 Testing Azure Integration:")
    print("=" * 50)

    status = azure.get_status()
    print(f"📊 Azure Status: {json.dumps(status, indent=2)}")

    # Test with sample data if cognitive services available
    if status['integration_status']['cognitive_available']:
        sample_texts = [
            "I am very satisfied with the AI processing results.",
            "The system performance could be improved.",
            "Excellent integration with Azure services."
        ]

        results = azure.process_with_azure_ai(sample_texts)
        print(f"🧠 AI Processing Results: {json.dumps(results, indent=2)}")

    return azure

if __name__ == "__main__":
    test_azure_integration()
