"""
Rate Limiting Middleware — per-IP sliding-window request throttle.
================================================================

Prevents API abuse by enforcing a per-IP request limit within a
rolling time window.  Uses an in-memory dict (sufficient for single-
process deployments).  For multi-worker, swap to Redis-backed counters.

Default: 100 requests per 60 seconds per IP.
Override via env:
    RATE_LIMIT_MAX_REQUESTS=100
    RATE_LIMIT_WINDOW_SECONDS=60
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("rate_limiter")

MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100"))
WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Paths exempt from rate limiting (health checks, OpenAPI docs)
EXEMPT_PATHS = {"/docs", "/redoc", "/openapi.json", "/api/shared/v1/health", "/api/shared/v1/health/deep"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.
    Tracks timestamps of requests per client IP.
    Returns HTTP 429 when the window is exceeded.
    """

    def __init__(self, app, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # IP → list of timestamps
        self._hits: Dict[str, List[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        """Extract client IP (respects X-Forwarded-For behind reverse proxy)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _prune(self, ip: str, now: float):
        """Remove timestamps outside the current window."""
        cutoff = now - self.window_seconds
        self._hits[ip] = [t for t in self._hits[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        ip = self._client_ip(request)
        now = time.time()

        self._prune(ip, now)

        if len(self._hits[ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self._hits[ip][0])) + 1
            logger.warning(f"Rate limit exceeded for {ip} ({len(self._hits[ip])} requests in window)")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        self._hits[ip].append(now)
        return await call_next(request)
