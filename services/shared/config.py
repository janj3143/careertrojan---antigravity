"""
=============================================================================
IntelliCV Shared Configuration Layer (Runtime Optimized)
=============================================================================

Central configuration for all data paths and directory structures.
Hardcoded to use L: drive for AI Data as per runtime requirements.

"""

from pathlib import Path
import os
from typing import Dict, List, Optional

# =============================================================================
# CORE DIRECTORY STRUCTURE
# =============================================================================

# Base IntelliCV directory (C:\careertrojan)
INTELLICV_ROOT = Path("C:/careertrojan")

# Core data directories
# CRITICAL: AI Data must come from L: drive
AI_DATA_DIR = Path("L:/antigravity_version_ai_data_final")
RAW_DATA_DIR = INTELLICV_ROOT / "raw_data" # Fallback or local
WORKING_COPY_DIR = INTELLICV_ROOT / "working"

AI_DATA_ROOT = AI_DATA_DIR

# Additional structure
LOGS_DIR = INTELLICV_ROOT / "logs"
SCRIPTS_DIR = INTELLICV_ROOT / "scripts"
SHARED_BACKEND_DIR = INTELLICV_ROOT / "shared_backend"

# Apps
USER_PORTAL_DIR = INTELLICV_ROOT / "apps" / "user-portal"
ADMIN_PORTAL_DIR = INTELLICV_ROOT / "apps" / "admin-portal"
MENTOR_PORTAL_DIR = INTELLICV_ROOT / "apps" / "mentor-portal"

# =============================================================================
# AI DATA FINAL STRUCTURE
# =============================================================================

AI_DATA_SUBDIRS = {
    "analysis_reports": AI_DATA_DIR / "analysis_reports",
    "candidate_analyses": AI_DATA_DIR / "candidate_analyses",
    "companies": AI_DATA_DIR / "companies",
    "email_extracted": AI_DATA_DIR / "email_extracted",
    "job_titles": AI_DATA_DIR / "job_titles",
    "locations": AI_DATA_DIR / "locations",
    "parsed_resumes": AI_DATA_DIR / "parsed_resumes",
    "company_corpora": AI_DATA_DIR / "company_corpora"
}

# =============================================================================
# WORKING COPY STRUCTURE
# =============================================================================

WORKING_COPY_SUBDIRS = {
    "stats_results": WORKING_COPY_DIR / "stats_results",
    "temp_uploads": WORKING_COPY_DIR / "temp_uploads",
    "batch_processing": WORKING_COPY_DIR / "batch_processing",
    "exports": WORKING_COPY_DIR / "exports"
}

# =============================================================================
# EXPORTS
# =============================================================================

def validate_directory_structure() -> Dict[str, bool]:
    results = {}
    core_dirs = {
        "AI_DATA_DIR": AI_DATA_DIR,
        "WORKING_COPY_DIR": WORKING_COPY_DIR,
        "LOGS_DIR": LOGS_DIR
    }
    for name, path in core_dirs.items():
        results[name] = path.exists() and path.is_dir()
    return results

def ensure_working_directories():
    for path in WORKING_COPY_SUBDIRS.values():
        path.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

ensure_working_directories()
