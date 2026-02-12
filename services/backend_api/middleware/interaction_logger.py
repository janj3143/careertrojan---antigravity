"""
InteractionLoggerMiddleware — AI Data Enrichment Loop (Section 13)

Captures every API request as an interaction record for the AI enrichment pipeline.
Records: user_id, endpoint, method, timestamp, response_time, status_code, payload_hash.

The ai_orchestrator_enrichment.py watchdog picks up these files and routes them
to the appropriate enrichment pipeline (embedding, ranking feedback, coaching, UX).

Data flows:
  [User Request] → [This Middleware] → interactions/{date}/{timestamp}.json
                                            ↓
                              [ai_orchestrator_enrichment.py] (watchdog)
                                            ↓
                              [ai_data_final/ enriched datasets]
"""

import os
import sys
import json
import time
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("interaction_logger")

# ── Resolve data root (portable) — L: drive is source of truth ─
_DATA_ROOT = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))

INTERACTIONS_DIR = _DATA_ROOT / "USER DATA" / "interactions"

# ── Redis queue (optional — degrades gracefully) ─────────────
INTERACTION_QUEUE = "careertrojan:interactions"
_redis_client = None
REDIS_AVAILABLE = False
try:
    import redis as _redis_mod
    _redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    _redis_client = _redis_mod.from_url(_redis_url, decode_responses=True)
    _redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connected — interaction queue enabled")
except Exception:
    logger.debug("Redis not available — file + DB logging only")

# ── Endpoints to SKIP (health checks, static, docs) ──────────
SKIP_PREFIXES = (
    "/docs", "/redoc", "/openapi.json",
    "/api/telemetry/v1/status",
    "/favicon.ico",
)


def _payload_hash(body: bytes) -> str:
    """SHA-256 hash of request body — stored instead of raw PII."""
    if not body:
        return ""
    return hashlib.sha256(body).hexdigest()[:16]


def _extract_user_id(request: Request) -> Optional[str]:
    """
    Best-effort extraction of user_id from the request.
    Checks: JWT claim, query param, header, or 'anonymous'.
    """
    # 1. From request.state (set by auth dependency)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return str(user_id)

    # 2. From Authorization header (decode JWT sub claim)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import base64
            token = auth_header.split(" ", 1)[1]
            # Decode payload without verification — we just need the sub claim
            payload_b64 = token.split(".")[1]
            # Add padding
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            if "sub" in payload:
                return str(payload["sub"])
        except Exception:
            pass

    # 3. From query param (some endpoints use ?user_id=)
    user_id = request.query_params.get("user_id")
    if user_id:
        return user_id

    return "anonymous"


def _classify_action(method: str, path: str) -> str:
    """Classify the request into an action_type for the enrichment router."""
    path_lower = path.lower()

    if "/resume" in path_lower and method == "POST":
        return "cv_upload"
    if "/ai-data" in path_lower or "/ai_data" in path_lower:
        return "ai_query"
    if "/jobs" in path_lower:
        return "job_search"
    if "/coaching" in path_lower:
        return "coaching_session"
    if "/mentorship" in path_lower or "/mentor" in path_lower:
        return "mentor_interaction"
    if "/auth" in path_lower:
        return "auth_event"
    if "/payment" in path_lower or "/credits" in path_lower or "/rewards" in path_lower:
        return "payment"
    if "/insights" in path_lower or "/analytics" in path_lower:
        return "analytics_view"
    if "/admin" in path_lower:
        return "admin_action"
    if method == "GET":
        return "browse_click"

    return "api_call"


class InteractionLoggerMiddleware(BaseHTTPMiddleware):
    """
    Logs every API request as a JSON interaction record.
    Zero-admin, always-on — feeds the AI enrichment loop.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip non-API paths
        if request.url.path.startswith(SKIP_PREFIXES):
            return await call_next(request)

        start = time.monotonic()

        # Read body for hashing (without consuming it)
        body = b""
        try:
            body = await request.body()
        except Exception:
            pass

        # Process the request
        response: Response = await call_next(request)
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)

        # Build interaction record
        now = datetime.now(timezone.utc)
        user_id = _extract_user_id(request)

        record = {
            "timestamp": now.isoformat(),
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "status_code": response.status_code,
            "response_time_ms": elapsed_ms,
            "payload_hash": _payload_hash(body),
            "action_type": _classify_action(request.method, request.url.path),
            "user_agent": request.headers.get("user-agent", "")[:200],
            "ip": request.client.host if request.client else None,
        }

        # 1. Write to disk (for AI orchestrator watchdog)
        try:
            day_dir = INTERACTIONS_DIR / now.strftime("%Y-%m-%d")
            day_dir.mkdir(parents=True, exist_ok=True)
            filename = f"{now.strftime('%H%M%S')}_{user_id}_{record['action_type']}.json"
            filepath = day_dir / filename
            filepath.write_text(json.dumps(record, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"InteractionLogger: disk write failed: {e}")

        # 2. Push to Redis queue (for real-time AI enrichment worker)
        if REDIS_AVAILABLE and _redis_client:
            try:
                _redis_client.lpush(INTERACTION_QUEUE, json.dumps(record))
            except Exception as e:
                logger.debug(f"InteractionLogger: Redis push failed: {e}")

        # 3. Write to database (for analytics + GDPR queryable history)
        try:
            from services.backend_api.db.connection import SessionLocal
            from services.backend_api.db.models import Interaction
            db = SessionLocal()
            try:
                uid = None
                if user_id and user_id != "anonymous":
                    try:
                        uid = int(user_id)
                    except (ValueError, TypeError):
                        pass
                db_record = Interaction(
                    user_id=uid,
                    session_id=None,
                    action_type=record["action_type"],
                    method=record["method"],
                    path=record["path"],
                    status_code=record["status_code"],
                    response_time_ms=record["response_time_ms"],
                    ip_address=record.get("ip"),
                    user_agent=record.get("user_agent"),
                    metadata_json=json.dumps({"payload_hash": record["payload_hash"], "query": record.get("query")}),
                )
                db.add(db_record)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"InteractionLogger: DB write failed: {e}")

        return response
