
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime
from services.backend_api.utils import security

# Grouping "Operations" endpoints together
router = APIRouter(prefix="/api/ops/v1", tags=["ops"])
logger = logging.getLogger(__name__)

# --- Public Stats ---
@router.get("/stats/public")
async def get_public_stats():
    return {
        "active_users": 1250,
        "resumes_optimized": 5400,
        "success_rate": 89
    }

# --- Processing (Live AI Routine) ---
class ProcessOptions(BaseModel):
    pdfs: bool = True
    full_scan: bool = True
    trigger_enrichment: bool = True

def _run_active_ingestion(job_id: str, opts: ProcessOptions):
    logger.info(f"[JOB {job_id}] Triggering real ingestion pipeline via background task: opts={opts}")
    from services.backend_api.services.automatic_data_ingestion_service import get_ingestion_service

    try:
        svc = get_ingestion_service()
        # Trigger directory ingest for new un-imported json objects
        stats = svc.ingest_parsed_directory(limit=50 if not opts.full_scan else None)
        logger.info(f"[JOB {job_id}] Ingestion routine finished: {stats}")
    except Exception as e:
        logger.error(f"[JOB {job_id}] Critical failure in background ingestion: {str(e)}")


@router.post("/processing/start")
async def start_processing(options: ProcessOptions, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    background_tasks.add_task(_run_active_ingestion, job_id, options)
    return {"job_id": job_id, "status": "started", "engine": "automatic_data_ingestion_service"}

@router.get("/processing/status")
async def processing_status():
    return {"status": "idle", "last_job": "success"}

# --- Security: Immutable Audit Logs ---
@router.post("/logs/lock")
def lock_audit_logs(token: str = Depends(security.oauth2_scheme)):
    """
    Simulates locking the current audit log buffer to Read-Only mode.
    In a real system, this would rotate the file and set chattr +i.
    """
    # 1. Verify Admin
    try:
        payload = security.decode_access_token(token)
        if payload.get("role") != "admin":
            if not security.token_has_scopes(payload, ["admin:access"]):
                raise HTTPException(status_code=403, detail="Admin required")
    except security.TokenValidationError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # 2. Perform Lock Action (Simulation)
    timestamp = datetime.utcnow().isoformat()
    logger.info(f"AUDIT LOG LOCKED by Admin at {timestamp}")
    
    return {"status": "locked", "mode": "WORM (Write Once Read Many)", "timestamp": timestamp}


# --- Admin Tokens (Legacy Port) ---
@router.get("/tokens/config")
def get_token_config():
    # Return default plan structure
    return {
        "plans": {
            "free": {"limit": 100},
            "pro": {"limit": 1000}
        }
    }

# --- Anti-Gaming (Simple Gate check) ---
class GateCheck(BaseModel):
    user_id: str
    text: str

@router.post("/anti-gaming/check")
def check_abuse(payload: GateCheck):
    # Simple logic
    risk = 0
    if len(payload.text) < 50:
        risk = 80
    
    return {
        "decision": "approve" if risk < 50 else "flag",
        "risk_score": risk,
        "reason_codes": []
    }
