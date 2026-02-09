"""
Request Correlation Middleware
==============================

Assigns a unique request_id to every incoming HTTP request and binds it
into structlog's context variables so all log lines emitted during
the request lifecycle carry the same correlation ID.

Also sets the X-Request-ID response header for client-side tracing.
"""

import uuid
import time
import structlog

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger("request")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4())[:12])
        start = time.perf_counter()

        # Bind request context for all downstream log calls
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        logger.info("request_started")

        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
