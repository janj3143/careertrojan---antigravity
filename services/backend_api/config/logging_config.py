"""
Structured Logging Configuration — CareerTrojan Backend
========================================================

Uses structlog to produce JSON-formatted log lines with:
 - Timestamp (ISO 8601)
 - Log level
 - Logger name
 - Request correlation ID (when available)
 - Caller info (module, function, line)

Usage:
    from services.backend_api.config.logging_config import get_logger
    logger = get_logger("my_module")
    logger.info("something happened", user_id=42, action="login")

Output (single line, shown expanded for readability):
    {"timestamp": "2026-02-09T14:23:01.123Z", "level": "info",
     "logger": "my_module", "event": "something happened",
     "user_id": 42, "action": "login"}
"""

import logging
import sys
import os

import structlog

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # "json" or "console"


def configure_logging():
    """
    One-time logging setup. Call once at app startup (main.py).
    Configures both structlog and the stdlib logging bridge so
    all loggers — including third-party libs — output structured JSON.
    """

    # Shared processors for every log line
    shared_processors = [
        structlog.contextvars.merge_contextvars,      # pull in bound context (e.g. request_id)
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if LOG_FORMAT == "console":
        # Human-readable coloured output (dev mode)
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # JSON lines (production)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Formatter that stdlib loggers will use — so uvicorn, sqlalchemy, etc.
    # all produce the same structured output
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Root handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "uvicorn.error", "httpcore", "httpx", "watchdog"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to the given name."""
    return structlog.get_logger(name)
