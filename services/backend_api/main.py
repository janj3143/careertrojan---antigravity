import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.backend_api.middleware.interaction_logger import InteractionLoggerMiddleware
from services.backend_api.middleware.rate_limiter import RateLimitMiddleware
from services.backend_api.middleware.request_correlation import RequestCorrelationMiddleware
from services.backend_api.config.logging_config import configure_logging, get_logger
# Addressing 1.3.2 Unified Config - verifying path later but assuming services.shared.config
try:
    from services.shared.config import config as settings
except ImportError:
    # Fallback for initial setup if config file isn't created yet
    class Settings:
        APP_NAME = "CareerTrojan"
        VERSION = "1.0.0"
        DEBUG = os.getenv("CAREERTROJAN_DEBUG", "false").lower() == "true"
        CAREERTROJAN_DATA_ROOT = os.getenv("CAREERTROJAN_DATA_ROOT", "./data/ai_data_final")
    settings = Settings()

# Import Routers
from services.backend_api.routers import admin, user, mentor, shared, auth, mentorship, intelligence, coaching, ops, resume, blockers, payment, rewards, credits, ai_data, jobs, taxonomy, sessions
from services.backend_api.routers import insights, touchpoints, mapping, analytics
from services.backend_api.routers import admin_abuse, admin_parsing, admin_tokens, anti_gaming, logs, telemetry
from services.backend_api.routers import gdpr
from services.backend_api.routers import webhooks
from services.backend_api.routers import api_health

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
    "http://localhost:8000",
    "http://localhost:3000",  # React Dev (user)
    "http://localhost:3001",  # React Dev (admin)
    "http://localhost:3002",  # React Dev (mentor)
    "http://localhost:5173",  # Vite Dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Correlation — assigns unique request_id + structured logs ──
app.add_middleware(RequestCorrelationMiddleware)

# ── AI Enrichment Loop — logs every request as interaction ────
app.add_middleware(InteractionLoggerMiddleware)

# ── Rate Limiting — prevent API abuse (100 req / 60s per IP) ──
app.add_middleware(RateLimitMiddleware)

# ── Core Routers ──────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)
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

# ── Optional/Placeholder Routers ─────────────────────────────
try: app.include_router(payment.router)
except: pass
try: app.include_router(rewards.router)
except: pass
try: app.include_router(mentor.router)
except: pass

# ── Visual / Mapping / Analytics Routers ─────────────────────
app.include_router(insights.router)       # Quadrant, word-cloud, graph, cohort
app.include_router(touchpoints.router)    # Evidence & touch-not lookups
app.include_router(mapping.router)        # Live endpoint map, visual registry
app.include_router(analytics.router)      # System statistics & dashboard data

# ── GDPR / Data Rights ──────────────────────────────────────
app.include_router(gdpr.router)           # Consent, data export, account deletion, audit log

# ── API Health Check ─────────────────────────────────────────
app.include_router(api_health.router)     # Live endpoint probing, run-all, summary

# ── Payment Webhooks ─────────────────────────────────────────
try: app.include_router(webhooks.router)     # Braintree webhook notifications
except Exception: pass

# ── Admin Extension Routers ──────────────────────────────────
try: app.include_router(admin_abuse.router)
except Exception: pass
try: app.include_router(admin_parsing.router)
except Exception: pass
try: app.include_router(admin_tokens.router)
except Exception: pass
try: app.include_router(anti_gaming.router)
except Exception: pass
try: app.include_router(logs.router)
except Exception: pass
try: app.include_router(telemetry.router)
except Exception: pass

# ── Collocation Engine Bootstrap + Enrichment Watchdog ────────────────
@app.on_event("startup")
async def _bootstrap_collocation_engine():
    """Load all 1,979 gazetteer terms into the collocation engine at startup."""
    try:
        from services.ai_engine.collocation_data_loader import bootstrap_collocation_engine
        stats = bootstrap_collocation_engine(sync_local=True)
        logger.info(
            "Collocation engine bootstrapped: %d total phrases across %d categories",
            stats.get("total_known_phrases", 0),
            stats.get("gazetteer_categories", 0),
        )
    except Exception as e:
        logger.warning("Collocation engine bootstrap failed (non-fatal): %s", e)

@app.on_event("startup")
async def _start_enrichment_watchdog():
    try:
        from services.ai_engine.enrichment_watchdog import start_enrichment_loop
        start_enrichment_loop(interval_seconds=300)  # every 5 minutes
        logger.info("Enrichment watchdog started (5-min interval)")
    except Exception as e:
        logger.warning("Enrichment watchdog failed to start: %s", e)

@app.on_event("shutdown")
async def _stop_enrichment_watchdog():
    try:
        from services.ai_engine.enrichment_watchdog import stop_enrichment_loop
        stop_enrichment_loop()
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8500)
