
from fastapi import APIRouter, Depends
from typing import Dict

from services.backend_api.utils.auth_deps import require_admin

router = APIRouter(prefix="/api/telemetry/v1", tags=["telemetry"], dependencies=[Depends(require_admin)])

@router.get("/status")
def status() -> Dict:
    return {"status": "ok"}
