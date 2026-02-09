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
    # Stub for Phase 1
    if credentials.get("username") == "janj3143" and credentials.get("password") == "Janj!3143@?":
         return {"token": "mock-jwt-token-for-phase-1", "user": "janj3143", "role": "premium"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/masquerade")
async def masquerade(target_user: str):
    # Stub for Admin Masquerade
    logger.warning(f"Masquerade attempt on {target_user}")
    return {"status": "active", "mode": "masquerade", "target": target_user}
