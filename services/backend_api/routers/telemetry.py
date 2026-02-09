
from fastapi import APIRouter
from typing import Dict

router = APIRouter(prefix="/api/telemetry/v1", tags=["telemetry"])

@router.get("/status")
def status() -> Dict:
    return {"status": "ok"}
