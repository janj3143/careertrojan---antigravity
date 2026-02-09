# Shared Router — includes deep health check for production readiness probes
import os
import time
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.backend_api.db.connection import get_db

router = APIRouter(
    prefix="/api/shared/v1",
    tags=["shared"],
    responses={404: {"description": "Not found"}},
)


@router.get("/health")
async def health_check():
    """Lightweight liveness probe — always returns fast."""
    return {"status": "ok"}


@router.get("/health/deep")
def deep_health_check(db: Session = Depends(get_db)):
    """
    Readiness probe — checks all critical dependencies:
    - Database connectivity
    - Disk space
    - AI data directory
    - Key runtime directories
    Returns overall status + per-component detail.
    """
    checks = {}
    overall = "ok"

    # 1. Database
    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_ms = round((time.perf_counter() - start) * 1000, 1)
        checks["database"] = {"status": "ok", "latency_ms": db_ms}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)[:200]}
        overall = "degraded"

    # 2. Disk space (working directory)
    try:
        usage = shutil.disk_usage(os.getcwd())
        free_gb = round(usage.free / (1024 ** 3), 2)
        total_gb = round(usage.total / (1024 ** 3), 2)
        checks["disk"] = {
            "status": "ok" if free_gb > 1.0 else "warning",
            "free_gb": free_gb,
            "total_gb": total_gb,
        }
        if free_gb < 1.0:
            overall = "degraded"
    except Exception as e:
        checks["disk"] = {"status": "error", "detail": str(e)[:200]}

    # 3. Key directories
    dirs_to_check = {
        "interactions": os.path.join(os.getcwd(), "interactions"),
        "ai_data_final": os.path.join(os.getcwd(), "ai_data_final"),
        "logs": os.path.join(os.getcwd(), "logs"),
    }
    dir_results = {}
    for name, path in dirs_to_check.items():
        dir_results[name] = {
            "exists": os.path.isdir(path),
            "writable": os.access(path, os.W_OK) if os.path.isdir(path) else False,
        }
    checks["directories"] = dir_results

    # 4. Redis (best-effort — not blocking if absent)
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = {"status": "ok"}
    except Exception:
        checks["redis"] = {"status": "unavailable", "detail": "Redis not reachable (non-blocking)"}

    return {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }

