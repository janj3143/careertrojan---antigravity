
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.backend_api.db.connection import get_db
from services.backend_api.services.blocker_connector import get_blocker_connector
from services.backend_api.services.blocker.service import BlockerService
from typing import List, Dict, Any

router = APIRouter(prefix="/api/blockers/v1", tags=["blockers"])

@router.post("/detect")
def detect_blockers(
    payload: Dict[str, Any],
):
    """
    Detect blockers from JD and Resume Data (No DB persistence required for quick check)
    Payload: { "jd_text": str, "resume_data": dict }
    """
    connector = get_blocker_connector()
    return connector.detect_blockers_for_user(
        payload.get("jd_text", ""), 
        payload.get("resume_data", {})
    )

@router.get("/user/{user_id}")
def get_user_blockers(user_id: int, db: Session = Depends(get_db)):
    service = BlockerService(db)
    return service.get_user_blockers(user_id)

@router.post("/improvement-plans/generate")
def generate_plans(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Generate improvement plans for a specific blocker
    Payload: { "blocker_id": str, "user_id": int }
    """
    # Note: Connector implementation of this specific method needs a refactor 
    # because the original logic was mixed in the service class.
    # For now, we will expose what we have or placeholder.
    # The original BlockerService.generate_improvement_plans logic handles this.
    service = BlockerService(db)
    # The full generation pipeline is not yet ported. Return 501 so
    # callers know the feature isn't available rather than getting a fake success.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Improvement plan generation pending full port from legacy service",
    )
