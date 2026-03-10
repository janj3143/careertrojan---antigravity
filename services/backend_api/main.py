import os
import logging
from pathlib import Path

# ── Load .env BEFORE any other import touches os.getenv() ─────────────────
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.backend_api.middleware.interaction_logger import InteractionLoggerMiddleware
from services.backend_api.middleware.rate_limiter import RateLimitMiddleware
from services.backend_api.middleware.request_correlation import RequestCorrelationMiddleware
from services.backend_api.config.logging_config import configure_logging, get_logger
from services.backend_api.utils.error_handlers import install_error_handlers
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
from services.backend_api.routers import ai_gateway  # AI Gateway (unified entry point)
from services.backend_api.routers import admin_abuse, admin_parsing, admin_tokens, anti_gaming, logs, telemetry
from services.backend_api.routers import admin_ai_control_plane  # AI Control Plane (drift, calibration, routing)
from services.backend_api.routers import gdpr
from services.backend_api.routers import webhooks
from services.backend_api.routers import api_health
from services.backend_api.routers import admin_tools  # Admin tools consolidated stubs
from services.backend_api.routers import admin_email_campaigns  # SendGrid/Klaviyo/Resend email campaigns
from services.backend_api.routers import contacts  # ContactsDB (30K+ contacts) API
from services.backend_api.routers import admin_data_index  # Data index management (parser + AI data)
from services.backend_api.routers import support  # Zendesk Support Bridge
from services.backend_api.routers import governance  # Route Governance

# ── Career Compass + Profile Coach module routers (spec §20) ─────
from services.backend_api.routers.career_compass import router as career_compass_router
from services.backend_api.routers.user_vector import router as user_vector_router
from services.backend_api.routers.market_signal import router as market_signal_router
from services.backend_api.routers.profile_builder import router as profile_builder_router
from services.backend_api.routers.mentor_search import router as mentor_search_router
from services.backend_api.routers.help import router as help_router

# Setup Structured Logging (structlog → JSON lines)
configure_logging()
logger = get_logger("backend")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# ── Global Error Handlers (canonical ErrorResponse envelope) ──
install_error_handlers(app)

# ── CORS Configuration (env-driven for production) ───────────
_DEFAULT_ORIGINS = [
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
_env_origins = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept"],
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
app.include_router(ai_gateway.router)     # AI Gateway (control plane entry point)
app.include_router(jobs.router)
app.include_router(taxonomy.router)
app.include_router(sessions.router)       # Session history, sync status, consolidated user view

# ── Optional/Placeholder Routers ─────────────────────────────
try:
    app.include_router(payment.router)
except Exception as exc:
    logger.error("Failed to mount payment router: %s", exc)
try:
    app.include_router(rewards.router)
except Exception as exc:
    logger.error("Failed to mount rewards router: %s", exc)
try:
    app.include_router(mentor.router)
except Exception as exc:
    logger.error("Failed to mount mentor router: %s", exc)

# ── Visual / Mapping / Analytics Routers ─────────────────────
app.include_router(insights.router)       # Quadrant, word-cloud, graph, cohort
app.include_router(touchpoints.router)    # Evidence & touch-not lookups
app.include_router(mapping.router)        # Live endpoint map, visual registry

# -- New GenAI Integrations -----------------------------------
from services.backend_api.routers.profile_coach import router as profile_coach_router
app.include_router(profile_coach_router)
app.include_router(analytics.router)      # System statistics & dashboard data

# ── Career Compass Module (spec §20 — full route tree) ───────
app.include_router(career_compass_router)
app.include_router(user_vector_router)
app.include_router(market_signal_router)
app.include_router(profile_builder_router)
app.include_router(mentor_search_router)

# ── Help Icon System (contextual page help) ──────────────────
app.include_router(help_router)

# ── GDPR / Data Rights ──────────────────────────────────────
app.include_router(gdpr.router)           # Consent, data export, account deletion, audit log

# ── Support Bridge (Zendesk) ─────────────────────────────────
app.include_router(support.router)        # Support tickets, Zendesk integration, webhooks
app.include_router(support.webhooks_router)  # Webhook alias: /api/webhooks/v1/zendesk

# ── API Health Check ─────────────────────────────────────────
app.include_router(api_health.router)     # Live endpoint probing, run-all, summary
app.include_router(admin_email_campaigns.router)  # SendGrid/Klaviyo/Resend email campaigns
app.include_router(contacts.router)       # ContactsDB (30K+ contacts) API

# ── Root-level Kubernetes-style probes (no prefix) ───────────
@app.get("/health", tags=["probes"])
def health():
    """Simple health endpoint for Zendesk / uptime monitors."""
    return {"status": "ok"}


@app.get("/healthz", tags=["probes"], include_in_schema=False)
async def _liveness():
    """Root liveness probe — returns instantly."""
    return {"status": "ok"}


@app.get("/readyz", tags=["probes"], include_in_schema=False)
async def _readiness():
    """Root readiness probe — delegates to deep health check."""
    from services.backend_api.routers.shared import deep_health_check
    from services.backend_api.db.connection import get_db
    db = next(get_db())
    try:
        result = deep_health_check(db=db)
        return result
    finally:
        db.close()

# ── Payment Webhooks ─────────────────────────────────────────
try:
    app.include_router(webhooks.router)     # Braintree webhook notifications
except Exception as exc:
    logger.error("Failed to mount webhooks router: %s", exc)

# ── Admin Extension Routers ──────────────────────────────────
try:
    app.include_router(admin_abuse.router)
except Exception as exc:
    logger.error("Failed to mount admin_abuse router: %s", exc)
try:
    app.include_router(admin_parsing.router)
except Exception as exc:
    logger.error("Failed to mount admin_parsing router: %s", exc)
try:
    app.include_router(admin_tokens.router)
except Exception as exc:
    logger.error("Failed to mount admin_tokens router: %s", exc)
try:
    app.include_router(anti_gaming.router)
except Exception as exc:
    logger.error("Failed to mount anti_gaming router: %s", exc)
try:
    app.include_router(logs.router)
except Exception as exc:
    logger.error("Failed to mount logs router: %s", exc)
try:
    app.include_router(telemetry.router)
except Exception as exc:
    logger.error("Failed to mount telemetry router: %s", exc)

# ── Admin Tools (Consolidated Stubs) ─────────────────────────
app.include_router(admin_tools.router)

# ── Data Index Management ─────────────────────────────────────
app.include_router(admin_data_index.router)

# ── AI Control Plane (Admin Dashboard for ML Observability) ──
app.include_router(admin_ai_control_plane.router)

# ── Route Governance (Drift Detection + Policy Enforcement) ──
app.include_router(governance.router)

# ── Route Governance Startup Check ────────────────────────────────────
@app.on_event("startup")
async def _governance_check():
    """Run route governance policy check at startup and warn on errors."""
    if os.environ.get("TESTING"):
        return
    try:
        from services.backend_api.governance.route_governance import quick_summary
        result = quick_summary(app)
        if result["policy_errors"] > 0:
            logger.warning(
                "Route governance: %d policy ERRORS, %d warnings across %d routes (checksum=%s)",
                result["policy_errors"], result["policy_warnings"],
                result["total_routes"], result["checksum"],
            )
        else:
            logger.info(
                "Route governance: CLEAN — %d routes, %d warnings (checksum=%s)",
                result["total_routes"], result["policy_warnings"], result["checksum"],
            )
    except Exception as e:
        logger.warning("Route governance check failed (non-fatal): %s", e)

# ── Test User Bootstrap (Phase 1) ─────────────────────────────────────
@app.on_event("startup")
async def _seed_test_user():
    """Seed the janj3143 premium test user on first boot (idempotent).

    Runs when TEST_USER_BOOTSTRAP_ENABLED=true  (set by bootstrap.ps1).
    Skipped entirely in test mode — tests use their own fixtures.
    """
    if os.environ.get("TESTING"):
        return
    if os.environ.get("TEST_USER_BOOTSTRAP_ENABLED", "").lower() != "true":
        return
    try:
        from services.backend_api.db.connection import SessionLocal
        from services.backend_api.db import models
        from services.backend_api.utils.security import get_password_hash

        db = SessionLocal()
        try:
            existing = db.query(models.User).filter(models.User.email == "janj3143@careertrojan.internal").first()
            if existing:
                logger.info("Test user janj3143 already exists (id=%s) — skipping seed", existing.id)
                return
            user = models.User(
                email="janj3143@careertrojan.internal",
                hashed_password=get_password_hash("JanJ3143@?"),
                full_name="Jan J (Test Premium)",
                role="premium",
                is_active=True,
            )
            db.add(user)
            db.commit()
            logger.info("Test user janj3143 seeded into DB (id=%s, role=premium)", user.id)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Test user seed failed (non-fatal): %s", e)

# ── Data Index Freshness Check ────────────────────────────────────────
@app.on_event("startup")
async def _check_data_index_freshness():
    """Warn if data indexes are stale (>24h) or missing."""
    if os.environ.get("TESTING"):
        return
    try:
        from services.shared.data_index import get_index_registry
        reg = get_index_registry()
        freshness = reg.is_fresh(max_age_hours=24)
        for idx_type, is_fresh in freshness.items():
            if not is_fresh:
                logger.warning("Data index '%s' is STALE or MISSING — run POST /api/admin/v1/index/rebuild", idx_type)
            else:
                logger.info("Data index '%s' is fresh", idx_type)
    except Exception as e:
        logger.warning("Data index freshness check failed (non-fatal): %s", e)

# ── Collocation Engine Bootstrap + Enrichment Watchdog ────────────────
@app.on_event("startup")
async def _bootstrap_collocation_engine():
    """Load all 1,979 gazetteer terms into the collocation engine at startup."""
    if os.environ.get("TESTING"):
        logger.info("TESTING mode — skipping collocation engine bootstrap")
        return
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
    if os.environ.get("TESTING"):
        logger.info("TESTING mode — skipping enrichment watchdog")
        return
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
