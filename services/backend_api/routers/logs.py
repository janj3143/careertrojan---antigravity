
from fastapi import APIRouter, Query, Depends
from pathlib import Path
import re
import os
from pydantic import BaseModel
from typing import List
from services.backend_api.routers.auth import get_current_active_admin as require_admin

class LogTailResponse(BaseModel):
    file: str
    lines: List[str]
    matched_errors: List[str]

router = APIRouter(prefix="/api/admin/v1/logs", tags=["admin-logs"])

@router.get("/tail", response_model=LogTailResponse, dependencies=[Depends(require_admin)])
def tail_log(
    file: str = Query("app.log"),
    n: int = Query(200, ge=10, le=5000),
    error_pattern: str = Query("ERROR|Traceback"),
):
    # Default log folder: sibling 'logs' next to your data_root
    log_dir = Path(os.environ.get("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")).parent / "logs"
    fp = (log_dir / file).resolve()

    if not fp.exists():
        return LogTailResponse(file=str(fp), lines=[], matched_errors=[])

    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-n:]

    pat = re.compile(error_pattern)
    matched = [ln for ln in lines if pat.search(ln)]

    return LogTailResponse(
        file=str(fp),
        lines=[ln.rstrip("\n") for ln in lines],
        matched_errors=[ln.rstrip("\n") for ln in matched],
    )
