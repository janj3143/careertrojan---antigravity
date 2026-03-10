from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, APIRouter

state = {"started": False, "db_ready": False, "redis_ready": False, "started_at": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    state["started_at"] = datetime.utcnow().isoformat()
    state["db_ready"] = True
    state["redis_ready"] = True
    state["started"] = True
    yield
    state["started"] = False

app = FastAPI(lifespan=lifespan)
router = APIRouter(tags=["health"])

@router.get("/health/live")
async def health_live():
    return {"status": "live"}

@router.get("/health/ready")
async def health_ready():
    ready = state["started"] and state["db_ready"] and state["redis_ready"]
    return {"status": "ready" if ready else "not_ready", "started_at": state["started_at"]}
