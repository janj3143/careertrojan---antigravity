"""
IntelliCV AI Data Central Configuration
======================================

Centralized configuration for all AI data paths and access across admin portal pages.
All JSON data is now consolidated in SANDBOX/ai_data_final directory.

Directory Structure:
- Total JSON Files: 3,418
- Main Categories: parsed_resumes, companies, job_titles, locations, emails, metadata
- Email Integration: email_extracted (56 JSON files from email processing)
- Parser Output: complete_parsing_output (10 JSON result files)
- Normalized Data: normalized (1,536 JSON files)
- Metadata: metadata (1,543 JSON files)

Usage: Import this configuration in all admin portal pages for consistent AI data access.
"""

from pathlib import Path
from typing import Dict, List, Any
import json

# CENTRALIZED AI DATA PATHS - All point to SANDBOX ai_data_final
class AIDataPaths:
    """Centralized AI data path configuration"""
    
    def __init__(self):
        # Base paths
        self.admin_portal_root = Path(__file__).parent.parent
        self.sandbox_root = self.admin_portal_root.parent 
        
        # Main AI data directory - CENTRALIZED
        self.ai_data_final = self.sandbox_root / "ai_data_final"
        
        # Subdirectories
        self.parsed_resumes = self.ai_data_final / "parsed_resumes"
        self.companies = self.ai_data_final / "companies" 
        self.job_titles = self.ai_data_final / "job_titles"
        self.locations = self.ai_data_final / "locations"
        self.emails = self.ai_data_final / "emails"
        self.metadata = self.ai_data_final / "metadata"
        self.normalized = self.ai_data_final / "normalized"
        self.email_extracted = self.ai_data_final / "email_extracted"
        self.complete_parsing_output = self.ai_data_final / "complete_parsing_output"
        
        # Legacy paths for compatibility
        self.intellicv_data = self.sandbox_root / "IntelliCV-data"
        self.email_data = self.sandbox_root / "data" / "email_data"
        
    def get_json_file_count(self, directory_path: Path) -> int:
        """Get count of JSON files in a directory"""
        if directory_path.exists():
            return len(list(directory_path.glob("*.json")))
        return 0
    
    def get_total_json_count(self) -> int:
        """Get total count of all JSON files in ai_data_final"""
        if self.ai_data_final.exists():
            return len(list(self.ai_data_final.rglob("*.json")))
        return 0
    
    def get_directory_summary(self) -> Dict[str, int]:
        """Get summary of JSON files by directory"""
        summary = {}
        
        directories = [
            ("parsed_resumes", self.parsed_resumes),
            ("companies", self.companies),
            ("job_titles", self.job_titles), 
            ("locations", self.locations),
            ("emails", self.emails),
            ("metadata", self.metadata),
            ("normalized", self.normalized),
            ("email_extracted", self.email_extracted),
            ("complete_parsing_output", self.complete_parsing_output)
        ]
        
        for name, path in directories:
            summary[name] = self.get_json_file_count(path)
            
        return summary
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """Verify all data directories exist and report status"""
        status = {
            "ai_data_final_exists": self.ai_data_final.exists(),
            "total_json_files": self.get_total_json_count(),
            "directory_breakdown": self.get_directory_summary(),
            "missing_directories": []
        }
        
        # Check for missing critical directories
        critical_dirs = [self.parsed_resumes, self.companies, self.metadata]
        for dir_path in critical_dirs:
            if not dir_path.exists():
                status["missing_directories"].append(str(dir_path))
                
        return status

# Global instance for easy import
ai_data_paths = AIDataPaths()

# Convenience functions for backward compatibility
def get_ai_data_path() -> Path:
    """Get main AI data directory path"""
    return ai_data_paths.ai_data_final

def get_json_file_count() -> int:
    """Get total JSON file count"""
    return ai_data_paths.get_total_json_count()

def get_data_summary() -> Dict[str, int]:
    """Get data directory summary"""
    return ai_data_paths.get_directory_summary()