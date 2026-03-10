import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.backend_api.middleware.interaction_logger import InteractionLoggerMiddleware
from services.backend_api.middleware.rate_limiter import RateLimitMiddleware
from services.backend_api.middleware.request_correlation import RequestCorrelationMiddleware
from services.backend_api.config.logging_config import configure_logging, get_logger
# Addressing 1.3.2 Unified Config - verifying path later but assuming services.shared.config
try:
    from services.shared.config import config as settings
except ImportError:
    # Fallback/Mock for initial setup if config file isn't created yet
    class Settings:
        APP_NAME = "CareerTrojan"
        VERSION = "1.0.0"
        DEBUG = True
        CAREERTROJAN_DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "./data")
    settings = Settings()

# Import Routers
from services.backend_api.routers import admin, user, mentor, shared, auth, mentorship, intelligence, coaching, ops, resume, blockers, payment, rewards, credits, ai_data, jobs, taxonomy, sessions, ontology, support
from services.backend_api.routers import career_compass
from services.backend_api.routers import profile_coach_v1, profile_v1, user_vector_v1
from services.backend_api.routers import insights, touchpoints, mapping, analytics, lenses
from services.backend_api.routers import admin_abuse, admin_parsing, admin_tokens, anti_gaming, logs, telemetry
from services.backend_api.routers import gdpr, data_index
from services.backend_api.routers import admin_legacy
try:
    from services.backend_api.routers import webhooks
except ImportError:
    webhooks = None  # type: ignore

# Setup Structured Logging (structlog → JSON lines)
configure_logging()
logger = get_logger("backend")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:8500",  # Main Backend
    "http://localhost:8501",  # Admin Portal
    "http://localhost:8502",  # User Portal
    "http://localhost:8503",  # Mentor Portal
    "http://localhost:8600",  # Access via Docker
    "http://localhost:8601",  # Admin Portal (Docker)
    "http://localhost:8602",  # User Portal (Docker)
    "http://localhost:8603",  # Mentor Portal (Docker)
    "http://localhost:8000",
    "http://localhost:3000",  # React Dev (user)
    "http://localhost:3001",  # React Dev (admin)
    "http://localhost:3002",  # React Dev (mentor)
    "http://localhost:5173",  # Vite Dev
    "http://89.167.75.132",
    "http://89.167.75.132:3000",
    "http://89.167.75.132:3001",
    "http://89.167.75.132:3002",
    "http://89.167.75.132:8500",
    "http://89.167.75.132:8600",
    "http://89.167.75.132:8601",
    "http://89.167.75.132:8602",
    "http://89.167.75.132:8603",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/live")
def health_live():
    """Liveness probe: verifies process is running"""
    return {"status": "alive"}

@app.get("/health/ready")
def health_ready():
    """Readiness probe: verifies dependencies are accessible"""
    # TODO: Add specific ping logic for Postgres / Redis here if needed
    return {"status": "ready"}


# ── Request Correlation — assigns unique request_id + structured logs ──
app.add_middleware(RequestCorrelationMiddleware)

# ── AI Enrichment Loop — logs every request as interaction ────
app.add_middleware(InteractionLoggerMiddleware)

# ── Rate Limiting — prevent API abuse (100 req / 60s per IP) ──
app.add_middleware(RateLimitMiddleware)


def _include_optional_router(router_obj, router_name: str) -> None:
    """Mount optional routers with explicit error logging (no silent failures)."""
    try:
        app.include_router(router_obj)
    except Exception as exc:
        logger.exception("Failed to mount optional router '%s': %s", router_name, exc)

# ── Core Routers ──────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(admin_legacy.router)
app.include_router(shared.router)         # Was imported but never mounted — FIXED 2026-02-08
app.include_router(mentorship.router)
app.include_router(intelligence.router)
app.include_router(coaching.router)
app.include_router(ops.router)
app.include_router(resume.router)
app.include_router(blockers.router)
app.include_router(credits.router)
app.include_router(ai_data.router)
app.include_router(jobs.router)
app.include_router(taxonomy.router)
app.include_router(sessions.router)       # Session history, sync status, consolidated user view
app.include_router(ontology.router)
app.include_router(support.router)
app.include_router(career_compass.router)
app.include_router(career_compass.router, prefix="/api/v1")
app.include_router(profile_coach_v1.router)
app.include_router(profile_v1.router)
app.include_router(user_vector_v1.router)
app.include_router(data_index.router)     # AI data & parser indexing system

# ── Optional/Placeholder Routers ─────────────────────────────
_include_optional_router(payment.router, "payment")
_include_optional_router(rewards.router, "rewards")
_include_optional_router(mentor.router, "mentor")
# ── Webhooks (Braintree / Stripe / Zendesk) ──────────────────
if webhooks:
    _include_optional_router(webhooks.router, "webhooks")

# ── Visual / Mapping / Analytics Routers ─────────────────────
app.include_router(insights.router)       # Quadrant, word-cloud, graph, cohort
app.include_router(touchpoints.router)    # Evidence & touch-not lookups
app.include_router(mapping.router)        # Live endpoint map, visual registry
app.include_router(analytics.router)      # System statistics & dashboard data
app.include_router(lenses.router)         # Spider/Covey composite analytics lenses

# ── GDPR / Data Rights ──────────────────────────────────────
app.include_router(gdpr.router)           # Consent, data export, account deletion, audit log

# ── Admin Extension Routers ──────────────────────────────────
_include_optional_router(admin_abuse.router, "admin_abuse")
_include_optional_router(admin_parsing.router, "admin_parsing")
_include_optional_router(admin_tokens.router, "admin_tokens")
_include_optional_router(anti_gaming.router, "anti_gaming")
_include_optional_router(logs.router, "logs")
_include_optional_router(telemetry.router, "telemetry")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500)
