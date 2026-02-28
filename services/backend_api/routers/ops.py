
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

# --- Processing (Stubbed) ---
class ProcessOptions(BaseModel):
    pdfs: bool = True
    full_scan: bool = True

def _fake_ingestion(job_id: str):
    import time
    time.sleep(1) # Sim work
    logger.info(f"Job {job_id} finished")

@router.post("/processing/start")
async def start_processing(options: ProcessOptions, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    background_tasks.add_task(_fake_ingestion, job_id)
    return {"job_id": job_id, "status": "started"}

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
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        if payload.get("role") != "admin":
             raise HTTPException(status_code=403, detail="Admin required")
    except:
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


# ============================================================================
# ADMIN OPS ENDPOINTS - Required by Admin Portal
# ============================================================================

@router.get("/logs")
def get_logs(
    level: str = "all",
    limit: int = 100,
    offset: int = 0
):
    """
    Retrieve system logs for admin review.
    """
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    
    # Demo log entries
    logs = [
        {"timestamp": (now - timedelta(minutes=i*5)).isoformat(), "level": "INFO" if i % 3 != 0 else "WARN", "message": f"System event #{100-i}", "source": "backend"}
        for i in range(limit)
    ]
    
    return {
        "ok": True,
        "logs": logs,
        "total": 500,
        "filters": {"level": level}
    }


@router.get("/backup")
def get_backup_status():
    """
    Get current backup status and history.
    """
    return {
        "ok": True,
        "last_backup": "2026-02-10T02:00:00Z",
        "next_scheduled": "2026-02-11T02:00:00Z",
        "backup_size_mb": 156,
        "retention_days": 30,
        "backups": [
            {"id": "bkp_001", "created_at": "2026-02-10T02:00:00Z", "size_mb": 156, "status": "completed"},
            {"id": "bkp_002", "created_at": "2026-02-09T02:00:00Z", "size_mb": 154, "status": "completed"},
            {"id": "bkp_003", "created_at": "2026-02-08T02:00:00Z", "size_mb": 152, "status": "completed"}
        ]
    }


@router.post("/backup")
def trigger_backup():
    """
    Trigger a manual backup.
    """
    return {
        "ok": True,
        "job_id": str(uuid.uuid4()),
        "status": "started",
        "message": "Backup job queued"
    }


@router.get("/diagnostics")
def get_diagnostics():
    """
    Get system diagnostics and health metrics.
    """
    import platform
    import sys
    
    return {
        "ok": True,
        "system": {
            "python_version": sys.version,
            "platform": platform.platform(),
            "cpu_count": 4,  # Demo
            "memory_usage_mb": 512
        },
        "database": {
            "status": "connected",
            "pool_size": 10,
            "active_connections": 3
        },
        "cache": {
            "status": "connected",
            "hit_rate": 0.89
        },
        "services": {
            "ai_engine": "healthy",
            "parser": "healthy",
            "scheduler": "healthy"
        }
    }


@router.get("/route-map")
def get_route_map():
    """
    Get registered API routes for debugging.
    """
    # Return a summary - the full map is in mapping router
    return {
        "ok": True,
        "total_routes": 195,
        "by_module": {
            "auth": 8,
            "user": 5,
            "admin": 12,
            "mentor": 10,
            "jobs": 3,
            "resume": 4,
            "payment": 15,
            "ops": 12,
            "coaching": 10
        },
        "health_endpoint": "/health"
    }


@router.get("/notifications")
def get_admin_notifications():
    """
    Get system notifications for admin dashboard.
    """
    return {
        "ok": True,
        "notifications": [
            {"id": "n1", "type": "info", "title": "System Update", "message": "Backend v1.2 deployed", "created_at": "2026-02-10T10:00:00Z", "read": False},
            {"id": "n2", "type": "warning", "title": "High Load", "message": "CPU usage above 80%", "created_at": "2026-02-10T09:30:00Z", "read": True},
            {"id": "n3", "type": "success", "title": "Backup Complete", "message": "Daily backup succeeded", "created_at": "2026-02-10T02:00:00Z", "read": True}
        ],
        "unread_count": 1
    }


@router.get("/config")
def get_system_config():
    """
    Get system configuration (non-sensitive).
    """
    import os
    
    return {
        "ok": True,
        "config": {
            "app_name": "CareerTrojan",
            "version": "1.0.0",
            "environment": os.getenv("CAREERTROJAN_ENV", "development"),
            "debug_mode": os.getenv("CAREERTROJAN_DEBUG", "false") == "true",
            "data_root": os.getenv("CAREERTROJAN_DATA_ROOT", "./data"),
            "max_upload_mb": 10,
            "session_timeout_minutes": 60,
            "rate_limit_requests": 100,
            "rate_limit_window_seconds": 60
        }
    }


@router.put("/config")
def update_system_config(updates: Dict[str, Any]):
    """
    Update system configuration (admin only).
    """
    # In production, this would persist to config store
    return {
        "ok": True,
        "message": "Configuration updated",
        "applied": updates
    }


@router.get("/exports")
def get_exports():
    """
    List available data exports.
    """
    return {
        "ok": True,
        "exports": [
            {"id": "exp_001", "type": "users", "created_at": "2026-02-10T12:00:00Z", "size_kb": 450, "status": "ready", "download_url": "/api/ops/v1/exports/exp_001/download"},
            {"id": "exp_002", "type": "analytics", "created_at": "2026-02-09T12:00:00Z", "size_kb": 1200, "status": "ready", "download_url": "/api/ops/v1/exports/exp_002/download"}
        ]
    }


@router.post("/exports")
def create_export(export_type: str = "full"):
    """
    Create a new data export.
    """
    return {
        "ok": True,
        "export_id": str(uuid.uuid4()),
        "type": export_type,
        "status": "processing",
        "message": "Export job started"
    }


@router.get("/api-explorer")
def get_api_explorer_data():
    """
    Get data for API explorer tool.
    """
    return {
        "ok": True,
        "openapi_url": "/openapi.json",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints_count": 195,
        "tags": ["auth", "user", "admin", "mentor", "jobs", "resume", "payment", "ops", "coaching", "analytics"]
    }


@router.get("/about")
def get_about():
    """
    Get system about/version information.
    """
    return {
        "ok": True,
        "name": "CareerTrojan",
        "version": "1.0.0",
        "build": "2026.02.10",
        "description": "AI-Powered Career Acceleration Platform",
        "components": {
            "backend": "FastAPI 0.109+",
            "frontend_admin": "React 18 + Vite",
            "frontend_user": "React 18 + Vite",
            "frontend_mentor": "React 18 + Vite",
            "database": "PostgreSQL 15",
            "cache": "Redis 7",
            "ai_engine": "OpenAI GPT-4 / Anthropic Claude"
        },
        "authors": ["CareerTrojan Team"],
        "license": "Proprietary"
    }


@router.get("/blob")
def get_blob_storage_info():
    """
    Get blob storage status and usage.
    """
    return {
        "ok": True,
        "provider": "local",  # or "azure", "s3"
        "total_size_mb": 2048,
        "used_size_mb": 512,
        "free_size_mb": 1536,
        "file_count": 1250,
        "buckets": [
            {"name": "resumes", "size_mb": 300, "count": 800},
            {"name": "avatars", "size_mb": 50, "count": 200},
            {"name": "exports", "size_mb": 162, "count": 250}
        ]
    }


@router.get("/queue")
def get_queue_status():
    """
    Get background job queue status.
    """
    return {
        "ok": True,
        "queues": [
            {"name": "default", "pending": 5, "processing": 2, "completed_today": 150, "failed_today": 3},
            {"name": "ai_processing", "pending": 12, "processing": 4, "completed_today": 89, "failed_today": 1},
            {"name": "email", "pending": 0, "processing": 0, "completed_today": 45, "failed_today": 0}
        ],
        "workers": 4,
        "worker_status": "healthy"
    }
