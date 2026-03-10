from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi.responses import JSONResponse


STATUS_HTTP_MAP: Dict[str, int] = {
    "ok": 200,
    "processing": 202,
    "missing_resume": 409,
    "missing_profile_enrichment": 409,
    "missing_cluster": 409,
    "missing_market_data": 409,
    "missing_mentor_data": 409,
    "insufficient_live_records": 409,
    "model_unavailable": 503,
    "error": 500,
}


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def respond(
    *,
    status: str,
    data: Optional[Dict[str, Any]] = None,
    message: Optional[str] = None,
    source_summary: Optional[Dict[str, Any]] = None,
    http_status: Optional[int] = None,
) -> JSONResponse:
    summary = dict(source_summary or {})
    summary.setdefault("request_id", str(uuid.uuid4()))
    payload = {
        "status": status,
        "message": message,
        "data": data or {},
        "source_summary": summary,
        "generated_at": _now_iso(),
    }
    return JSONResponse(content=payload, status_code=http_status or STATUS_HTTP_MAP.get(status, 500))
