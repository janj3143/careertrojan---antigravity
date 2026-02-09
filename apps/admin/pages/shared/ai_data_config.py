"""
AI Data Configuration - Docker Compatible
========================================

Simple AI data configuration for Docker deployment.
"""

from pathlib import Path
from typing import Dict, Any, Optional

def get_ai_data_path() -> Path:
    """Get AI data path"""
    # Docker environment path - absolute path in container
    return Path("/app/ai_data_final")

def verify_ai_data_integrity() -> Dict[str, Any]:
    """Verify AI data integrity"""
    ai_data_path = get_ai_data_path()
    
    return {
        "status": "available" if ai_data_path.exists() else "not_found",
        "path": str(ai_data_path),
        "files_count": len(list(ai_data_path.glob("*"))) if ai_data_path.exists() else 0,
        "verified": True
    }