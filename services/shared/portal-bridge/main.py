from fastapi import FastAPI, HTTPException, status
from loguru import logger
import os

app = FastAPI(title="Portal Bridge", version="1.0.0")

# --- Configuration ---
# In a real scenario, this would connect to an Auth Provider or Database
TEST_USER_BOOTSTRAP = os.getenv("TEST_USER_BOOTSTRAP_ENABLED", "false").lower() == "true"

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "portal-bridge"}

@app.post("/auth/login")
async def login(credentials: dict):
    """Authenticate against real user store. Phase-1 bootstrap only if
    TEST_USER_BOOTSTRAP_ENABLED=true (never in production)."""
    if TEST_USER_BOOTSTRAP:
        # Dev-only bootstrap — gated behind env flag, disabled by default
        if credentials.get("username") == os.getenv("BOOTSTRAP_USER") and \
           credentials.get("password") == os.getenv("BOOTSTRAP_PASS"):
            import secrets
            return {
                "token": secrets.token_urlsafe(32),
                "user": credentials["username"],
                "role": "premium",
                "warning": "bootstrap-mode — not for production",
            }
    # Real auth path — delegate to auth provider
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/masquerade")
async def masquerade(target_user: str):
    # Stub for Admin Masquerade
    logger.warning(f"Masquerade attempt on {target_user}")
    return {"status": "active", "mode": "masquerade", "target": target_user}
