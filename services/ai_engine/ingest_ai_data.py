"""
Unified Data Ingestion Runner for CareerTrojan AI Engine.
Bridges L: Drive Data -> AI Runtime.
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Add local directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import AI_DATA_DIR, RAW_DATA_DIR, log_root

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_root / "ai_ingestion.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AI_Ingest")

@dataclass
class IngestionResult:
    step: str
    success: bool
    details: str

class DataIngestionEngine:
    def __init__(self):
        self.data_dir = AI_DATA_DIR
        logger.info(f"Initialized Data Ingestion Engine. Root: {self.data_dir}")

    def scan_profiles(self) -> IngestionResult:
        """Scan and register profile data from L: drive"""
        try:
            profiles_dir = self.data_dir / "profiles"
            if not profiles_dir.exists():
                return IngestionResult("Scan Profiles", False, f"Directory not found: {profiles_dir}")
            
            count = len(list(profiles_dir.glob("*.json")))
            logger.info(f"Found {count} profiles in {profiles_dir}")
            return IngestionResult("Scan Profiles", True, f"Registered {count} profiles")
        except Exception as e:
            return IngestionResult("Scan Profiles", False, str(e))

    def scan_companies(self) -> IngestionResult:
        """Scan and register company data"""
        try:
            companies_file = self.data_dir / "companies_clean_all.json"
            if not companies_file.exists():
                return IngestionResult("Scan Companies", False, "companies_clean_all.json missing")
            
            return IngestionResult("Scan Companies", True, "Company registry found")
        except Exception as e:
            return IngestionResult("Scan Companies", False, str(e))

    def run_all(self):
        logger.info("Starting Full Data Ingestion...")
        results = []
        results.append(self.scan_profiles())
        results.append(self.scan_companies())
        
        return results

if __name__ == "__main__":
    engine = DataIngestionEngine()
    results = engine.run_all()
    
    print("\n=== INGESTION SUMMARY ===")
    for res in results:
        icon = "✅" if res.success else "❌"
        print(f"{icon} {res.step}: {res.details}")
