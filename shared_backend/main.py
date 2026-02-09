import os
import sys
from fastapi import FastAPI, HTTPException, status
from loguru import logger

# --- Configuration & Environment Validation ---
DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "/data/ai_data_final")
WORKING_ROOT = os.getenv("CAREERTROJAN_WORKING_ROOT", "/data/working_copy")
ALLOW_MOCK_DATA = os.getenv("ALLOW_MOCK_DATA", "false").lower() == "true"

def validate_runtime_state():
    logger.info("Starting Runtime Validation...")
    
    # 1. Check for Zero-Demo Policy
    if ALLOW_MOCK_DATA:
        logger.critical("CRITICAL: ALLOW_MOCK_DATA is set to true. Runtime aborted.")
        sys.exit(1)
    
    # 2. Check for ai_data_final mount
    if not os.path.exists(DATA_ROOT):
        logger.critical(f"CRITICAL: ai_data_final not found at {DATA_ROOT}. Runtime aborted.")
        sys.exit(1)
        
    # 3. Check for specific directory markers in ai_data_final to ensure it's not empty/mock
    required_dirs = ["directories", "taxonomies", "skills"]
    for d in required_dirs:
        if not os.path.isdir(os.path.join(DATA_ROOT, d)):
             logger.critical(f"CRITICAL: Required data directory '{d}' missing in {DATA_ROOT}.")
             sys.exit(1)

    logger.info("Runtime Validation [OK]")

# Run validation on import
validate_runtime_state()

app = FastAPI(title="CareerTrojan API", version="1.0.0")

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "online",
        "branding": "CareerTrojan",
        "data_mount": "verified",
        "zero_demo": True
    }

# Interaction Logging and logic will be added here...
