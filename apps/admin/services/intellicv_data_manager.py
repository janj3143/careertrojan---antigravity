"""
IntelliCV Data Directory Manager
==============================

Manages the proper data directory structure for IntelliCV, including:
- AI training data in SANDBOX/ai_data_final
- Email integration data
- CV/candidate data for processing
- Backend AI services data (neural network, expert system, etc.)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger, LoggingMixin
from utils.exception_handler import ExceptionHandler, SafeOperationsMixin

# Initialize logging
setup_logging()
logger = get_logger(__name__)


class IntelliCVDataDirectoryManager(LoggingMixin, SafeOperationsMixin):
    """Manages the proper data directory structure for IntelliCV"""
    
    def __init__(self):
        super().__init__()
        # Main IntelliCV root directory
        self.intellicv_root = Path("c:/IntelliCV-AI/IntelliCV")
        
        # SANDBOX data paths (primary location for AI training data)
        self.sandbox_root = self.intellicv_root / "SANDBOX" / "admin_portal"
        self.ai_data_path = self.sandbox_root / "ai_data_final"
        
        # Email integration data (can be in IntelliCV-data or SANDBOX)
        self.intellicv_data_path = self.intellicv_root / "IntelliCV-data"
        self.email_data_path = self.intellicv_data_path / "email_integration"
        self.email_extracted_path = self.intellicv_data_path / "email_extracted"
        
        # Candidate data paths (multiple sources)
        self.candidate_data_path = self.intellicv_data_path / "candidate_data"
        self.sandbox_candidate_data = self.sandbox_root / "candidate_data"
        
        # Backend AI services data (for neural network, expert system, etc.)
        self.backend_data_path = self.sandbox_root / "backend" / "data"
        self.backend_logs_path = self.sandbox_root / "backend" / "logs"
        self.backend_models_path = self.backend_data_path / "models"
        self.backend_rules_path = self.backend_data_path / "rules"
        self.backend_feedback_path = self.backend_data_path / "feedback"
        
        # Configuration and logs
        self.config_path = self.email_data_path / "config"
        self.logs_path = self.email_data_path / "logs"
        self.metadata_path = self.email_data_path / "metadata"
        
        # Build the directory structure
        self.build_directory_structure()
        
        # Setup logging
        self.setup_logging()
    
    def build_directory_structure(self):
        """Build the complete data directory structure"""
        directories_to_create = [
            # Main data directories
            self.intellicv_data_path,
            self.ai_data_path,
            self.sandbox_candidate_data,
            
            # Email integration directories
            self.email_data_path,
            self.email_extracted_path,
            self.candidate_data_path,
            self.config_path,
            self.logs_path,
            self.metadata_path,
            
            # Email subdirectories
            self.email_data_path / "attachments",
            self.email_data_path / "processed_cvs",
            self.email_data_path / "exports",
            
            # Provider-specific directories
            self.email_extracted_path / "gmail",
            self.email_extracted_path / "outlook", 
            self.email_extracted_path / "yahoo",
            
            # AI integration directories (SANDBOX/ai_data_final)
            self.ai_data_path / "exported_cvs",
            self.ai_data_path / "candidate_profiles",
            self.ai_data_path / "enrichment_results",
            self.ai_data_path / "training_data",
            
            # Backend AI services directories
            self.backend_data_path,
            self.backend_logs_path,
            self.backend_models_path,
            self.backend_rules_path,
            self.backend_feedback_path
        ]
        
        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create configuration files if they don't exist
        self.create_default_configurations()
    
    def create_default_configurations(self):
        """Create default configuration files"""
        
        # Email accounts configuration
        email_accounts_file = self.config_path / "email_accounts.json"
        if not email_accounts_file.exists():
            default_config = {
                "accounts": [],
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
            with open(email_accounts_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        
        # Data directory configuration
        directory_config_file = self.config_path / "directory_config.json"
        directory_config = {
            "intellicv_data_path": str(self.intellicv_data_path),
            "sandbox_ai_data_path": str(self.ai_data_path),
            "email_data_path": str(self.email_data_path),
            "email_extracted_path": str(self.email_extracted_path),
            "backend_data_path": str(self.backend_data_path),
            "backend_models_path": str(self.backend_models_path),
            "backend_rules_path": str(self.backend_rules_path),
            "backend_feedback_path": str(self.backend_feedback_path),
            "created_at": datetime.now().isoformat(),
            "version": "2.0"
        }
        with open(directory_config_file, 'w') as f:
            json.dump(directory_config, f, indent=2)
        
        # Extraction metadata file
        extraction_metadata_file = self.metadata_path / "extraction_metadata.json"
        if not extraction_metadata_file.exists():
            extraction_metadata = {
                "extractions": [],
                "total_extractions": 0,
                "last_extraction": None,
                "version": "1.0"
            }
            with open(extraction_metadata_file, 'w') as f:
                json.dump(extraction_metadata, f, indent=2)
    
    def setup_logging(self):
        """Setup logging for data operations"""
        log_file = self.logs_path / f"data_manager_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"IntelliCV Data Directory Manager initialized")
        self.logger.info(f"Main data path: {self.intellicv_data_path}")
    
    def get_directory_status(self):
        """Get the status of all directories"""
        status = {
            "main_directories": {},
            "email_directories": {},
            "ai_directories": {},
            "backend_directories": {},
            "file_counts": {},
            "total_size_mb": 0
        }
        
        # Check main directories
        main_dirs = [
            ("IntelliCV Data Root", self.intellicv_data_path),
            ("SANDBOX AI Data", self.ai_data_path),
            ("Email Integration", self.email_data_path),
            ("Email Extracted", self.email_extracted_path),
            ("Backend Data", self.backend_data_path),
            ("Config", self.config_path),
            ("Logs", self.logs_path),
            ("Metadata", self.metadata_path)
        ]
        
        for name, path in main_dirs:
            status["main_directories"][name] = {
                "exists": path.exists(),
                "path": str(path),
                "file_count": len(list(path.glob("*"))) if path.exists() else 0
            }
        
        # Check backend AI directories
        backend_dirs = [
            ("Models", self.backend_models_path),
            ("Rules", self.backend_rules_path),
            ("Feedback", self.backend_feedback_path),
            ("Logs", self.backend_logs_path)
        ]
        
        for name, path in backend_dirs:
            status["backend_directories"][name] = {
                "exists": path.exists(),
                "path": str(path),
                "file_count": len(list(path.glob("*"))) if path.exists() else 0
            }
        
        # Check email extracted files
        if self.email_extracted_path.exists():
            email_files = list(self.email_extracted_path.rglob("*"))
            pdf_files = [f for f in email_files if f.suffix.lower() == '.pdf']
            doc_files = [f for f in email_files if f.suffix.lower() in ['.doc', '.docx']]
            
            status["file_counts"]["email"] = {
                "total_files": len([f for f in email_files if f.is_file()]),
                "pdf_files": len(pdf_files),
                "doc_files": len(doc_files),
                "other_files": len(email_files) - len(pdf_files) - len(doc_files)
            }
        
        # Check AI data files (SANDBOX/ai_data_final)
        if self.ai_data_path.exists():
            ai_files = list(self.ai_data_path.rglob("*"))
            cv_files = [f for f in ai_files if f.suffix.lower() in ['.pdf', '.doc', '.docx']]
            json_files = [f for f in ai_files if f.suffix.lower() == '.json']
            
            status["file_counts"]["ai_data"] = {
                "total_files": len([f for f in ai_files if f.is_file()]),
                "cv_files": len(cv_files),
                "json_files": len(json_files)
            }
            
            # Calculate total size across all data sources
            all_files = list(self.email_extracted_path.rglob("*")) if self.email_extracted_path.exists() else []
            all_files.extend(ai_files)
            total_size = sum(f.stat().st_size for f in all_files if f.is_file())
            status["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return status
    
    def get_extracted_cv_list(self, limit=None, source='all'):
        """
        Get list of extracted CV files with metadata
        
        Args:
            limit: Maximum number of files to return
            source: 'email', 'ai_data', or 'all' to specify data source
        """
        cv_files = []
        
        # Collect from email extracted path
        if source in ['email', 'all'] and self.email_extracted_path.exists():
            email_files = list(self.email_extracted_path.rglob("*"))
            pdf_and_doc_files = [f for f in email_files if f.suffix.lower() in ['.pdf', '.doc', '.docx'] and f.is_file()]
            
            for file_path in pdf_and_doc_files:
                stat = file_path.stat()
                cv_files.append({
                    "filename": file_path.name,
                    "full_path": str(file_path),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 3),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "email_integration",
                    "provider": file_path.parent.name if file_path.parent.name in ['gmail', 'outlook', 'yahoo'] else 'unknown',
                    "extension": file_path.suffix.lower()
                })
        
        # Collect from SANDBOX/ai_data_final
        if source in ['ai_data', 'all'] and self.ai_data_path.exists():
            ai_files = list(self.ai_data_path.rglob("*"))
            pdf_and_doc_files = [f for f in ai_files if f.suffix.lower() in ['.pdf', '.doc', '.docx'] and f.is_file()]
            
            for file_path in pdf_and_doc_files:
                stat = file_path.stat()
                cv_files.append({
                    "filename": file_path.name,
                    "full_path": str(file_path),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 3),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "source": "ai_data_final",
                    "provider": "sandbox",
                    "extension": file_path.suffix.lower()
                })
        
        # Sort by modification time (newest first)
        cv_files.sort(key=lambda x: x['modified'], reverse=True)
        
        if limit:
            cv_files = cv_files[:limit]
        
        return cv_files
    
    def export_cvs_for_ai_processing(self, source='all'):
        """
        Export CV data for AI processing with detailed list
        
        Args:
            source: 'email', 'ai_data', or 'all' to specify data source
        """
        extracted_cvs = self.get_extracted_cv_list(source=source)
        
        if not extracted_cvs:
            return {
                "success": False,
                "message": "No CV files found for export",
                "extracted_count": 0,
                "cv_list": []
            }
        
        # Create export data
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_cvs": len(extracted_cvs),
            "cv_files": extracted_cvs,
            "export_summary": {
                "pdf_files": len([cv for cv in extracted_cvs if cv['extension'] == '.pdf']),
                "doc_files": len([cv for cv in extracted_cvs if cv['extension'] in ['.doc', '.docx']]),
                "total_size_mb": sum(cv['size_mb'] for cv in extracted_cvs),
                "providers": list(set(cv['provider'] for cv in extracted_cvs))
            }
        }
        
        # Save export data
        export_file = self.ai_data_path / "exported_cvs" / f"cv_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported {len(extracted_cvs)} CVs for AI processing")
        
        return {
            "success": True,
            "message": f"Successfully exported {len(extracted_cvs)} CV files for AI processing",
            "extracted_count": len(extracted_cvs),
            "cv_list": extracted_cvs,
            "export_file": str(export_file),
            "export_summary": export_data["export_summary"]
        }
    
    def check_email_accounts_config(self):
        """Check if email accounts are configured"""
        email_accounts_file = self.config_path / "email_accounts.json"
        
        if email_accounts_file.exists():
            with open(email_accounts_file, 'r') as f:
                config = json.load(f)
                return {
                    "configured": len(config.get("accounts", [])) > 0,
                    "account_count": len(config.get("accounts", [])),
                    "accounts": config.get("accounts", [])
                }
        
        return {
            "configured": False,
            "account_count": 0,
            "accounts": []
        }
    
    def get_real_data_stats(self):
        """Get real statistics from all data directories"""
        status = self.get_directory_status()
        email_config = self.check_email_accounts_config()
        
        # Aggregate file counts
        email_counts = status["file_counts"].get("email", {})
        ai_counts = status["file_counts"].get("ai_data", {})
        
        return {
            "data_directory_exists": self.intellicv_data_path.exists(),
            "sandbox_ai_data_exists": self.ai_data_path.exists(),
            "email_data_exists": self.email_data_path.exists(),
            "backend_data_exists": self.backend_data_path.exists(),
            
            # Email data stats
            "email_extracted_files": email_counts.get("total_files", 0),
            "email_pdf_files": email_counts.get("pdf_files", 0),
            "email_doc_files": email_counts.get("doc_files", 0),
            
            # AI data stats (SANDBOX/ai_data_final)
            "ai_data_files": ai_counts.get("total_files", 0),
            "ai_cv_files": ai_counts.get("cv_files", 0),
            "ai_json_files": ai_counts.get("json_files", 0),
            
            # Combined stats
            "total_size_mb": status["total_size_mb"],
            "email_accounts_configured": email_config["configured"],
            "email_account_count": email_config["account_count"],
            
            "data_paths": {
                "intellicv_data": str(self.intellicv_data_path),
                "sandbox_ai_data": str(self.ai_data_path),
                "email_data": str(self.email_data_path),
                "email_extracted": str(self.email_extracted_path),
                "backend_data": str(self.backend_data_path),
                "backend_models": str(self.backend_models_path),
                "backend_rules": str(self.backend_rules_path),
                "backend_feedback": str(self.backend_feedback_path)
            }
        }


def get_data_manager():
    """Get the IntelliCV Data Directory Manager instance"""
    return IntelliCVDataDirectoryManager()


if __name__ == "__main__":
    # Test the data manager
    manager = IntelliCVDataDirectoryManager()
    logger.info("Data directory structure built successfully!")
    logger.info(f"Main data path: {manager.intellicv_data_path}")
    
    status = manager.get_directory_status()
    logger.info("\nDirectory Status:")
    for name, info in status["main_directories"].items():
        logger.info(f"  {name}: {'✅' if info['exists'] else '❌'} ({info['file_count']} files)")
    
    logger.info(f"\nTotal extracted files: {status['file_counts'].get('total_files', 0)}")
    logger.info(f"Total size: {status['total_size_mb']} MB")