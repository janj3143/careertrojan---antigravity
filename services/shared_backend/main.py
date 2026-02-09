from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.shared_backend.config import settings
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:8500",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    """Service Health Check"""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }

@app.get("/api/v1/stats")
async def get_stats():
    """Basic Data Stats"""
    data_root = settings.CAREERTROJAN_DATA_ROOT
    if not os.path.exists(data_root):
        raise HTTPException(status_code=500, detail="Data Root not mounted")

    # Simple count of automated parser files
    parser_path = os.path.join(data_root, "automated_parser")
    file_count = 0
    if os.path.exists(parser_path):
        file_count = len([f for f in os.listdir(parser_path) if os.path.isfile(os.path.join(parser_path, f))])

    return {
        "data_root": data_root,
        "parser_queue_count": file_count
    }

@app.get("/api/v1/users")
async def get_users():
    """Get all users (Mock for now)"""
    return [
        {"id": "1", "name": "Admin User", "email": "admin@careertrojan.com", "role": "Admin", "status": "Active"},
        {"id": "2", "name": "New User", "email": "user@gmail.com", "role": "User", "status": "Active"},
        {"id": "3", "name": "Test Account", "email": "test@careertrojan.com", "role": "User", "status": "Inactive"}
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
