import time, uuid, logging
from starlette.middleware.base import BaseHTTPMiddleware
logger = logging.getLogger("careertrojan.request")

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
        logger.info("request_complete", extra={"request_id": request_id, "path": request.url.path, "status_code": response.status_code, "duration_ms": duration_ms})
        return response
