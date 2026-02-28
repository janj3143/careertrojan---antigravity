"""
Unified Error Schema & Global Exception Handlers — CaReerTroJan
================================================================
Provides:
  1. ErrorResponse — canonical Pydantic model for ALL API errors
  2. Global exception handlers wired into FastAPI at startup
  3. Internal detail scrubbing (no stacktraces, SQL, or paths leak to clients)

Wire in main.py with:
    from services.backend_api.utils.error_handlers import install_error_handlers
    install_error_handlers(app)

Author: CaReerTroJan System
Date: February 26, 2026
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# Canonical Error Response Model
# ══════════════════════════════════════════════════════════════

class ErrorDetail(BaseModel):
    """Single validation or field-level error."""
    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Canonical error envelope returned by ALL API error responses.

    {
        "ok": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "status": 422,
            "details": [...]
        },
        "request_id": "abc-123"
    }
    """
    ok: bool = False
    error: Dict[str, Any]
    request_id: Optional[str] = None


# ── Error code mapping ───────────────────────────────────────
_STATUS_TO_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    402: "PAYMENT_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "BAD_GATEWAY",
    503: "SERVICE_UNAVAILABLE",
    504: "GATEWAY_TIMEOUT",
}


def _error_code(status: int) -> str:
    return _STATUS_TO_CODE.get(status, f"HTTP_{status}")


def _build_error_body(
    status: int,
    message: str,
    details: Optional[List[Dict[str, Any]]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the canonical error JSON envelope."""
    error_block: Dict[str, Any] = {
        "code": _error_code(status),
        "message": message,
        "status": status,
    }
    if details:
        error_block["details"] = details
    return {
        "ok": False,
        "error": error_block,
        "request_id": request_id,
    }


# ══════════════════════════════════════════════════════════════
# Global Exception Handlers
# ══════════════════════════════════════════════════════════════

# Phrases that should NEVER appear in client-facing error detail
_SCRUB_PATTERNS = (
    "Traceback",
    "File \"",
    "sqlalchemy",
    "psycopg2",
    "sqlite3",
    "\\\\",           # Windows paths
    "C:\\",
    "L:\\",
    "/home/",
    "/app/",
)


def _is_safe_detail(detail: str) -> bool:
    """Check if the error detail is safe to expose to clients."""
    if not detail:
        return True
    lower = detail.lower()
    for pattern in _SCRUB_PATTERNS:
        if pattern.lower() in lower:
            return False
    return len(detail) < 500  # Truncate overly long errors


def _get_request_id(request: Request) -> Optional[str]:
    """Extract request_id injected by RequestCorrelationMiddleware."""
    return getattr(request.state, "request_id", None) if hasattr(request, "state") else None


async def _handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException — preserve status code but wrap in canonical envelope.
    Scrub internal details on 5xx errors.
    """
    status = exc.status_code
    detail = str(exc.detail) if exc.detail else "An error occurred"

    # Scrub internal details on server errors
    if status >= 500 and not _is_safe_detail(detail):
        logger.error(
            "HTTP %d (scrubbed): %s [request_id=%s]",
            status, detail, _get_request_id(request),
        )
        detail = "Internal server error"

    body = _build_error_body(
        status=status,
        message=detail,
        request_id=_get_request_id(request),
    )
    return JSONResponse(
        status_code=status,
        content=body,
        headers=dict(exc.headers) if exc.headers else None,
    )


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic/FastAPI validation errors (422).
    Convert each error into a clean ErrorDetail dict.
    """
    details = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field_parts = [str(p) for p in loc if p != "body"]
        details.append({
            "field": ".".join(field_parts) if field_parts else None,
            "message": err.get("msg", "Validation error"),
            "type": err.get("type"),
        })

    body = _build_error_body(
        status=422,
        message="Request validation failed",
        details=details,
        request_id=_get_request_id(request),
    )
    return JSONResponse(status_code=422, content=body)


async def _handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled exceptions — NEVER leaks internals.
    Logs full traceback server-side, returns generic message to client.
    """
    request_id = _get_request_id(request)
    logger.error(
        "Unhandled exception [request_id=%s] %s: %s\n%s",
        request_id,
        type(exc).__name__,
        str(exc),
        traceback.format_exc(),
    )

    body = _build_error_body(
        status=500,
        message="Internal server error",
        request_id=request_id,
    )
    return JSONResponse(status_code=500, content=body)


# ══════════════════════════════════════════════════════════════
# Installer — call from main.py
# ══════════════════════════════════════════════════════════════

def install_error_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""
    app.add_exception_handler(HTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unhandled_exception)
    logger.info("Global error handlers installed (ErrorResponse envelope)")
