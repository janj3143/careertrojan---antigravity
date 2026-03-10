
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.services.blocker_connector import get_blocker_connector
from services.backend_api.services.blocker.service import BlockerService
from services.backend_api.utils.auth_deps import get_current_user
from typing import List, Dict, Any

router = APIRouter(prefix="/api/blockers/v1", tags=["blockers"])

@router.post("/detect")
def detect_blockers(
    payload: Dict[str, Any],
    current_user: models.User = Depends(get_current_user),
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Generate improvement plans for a specific blocker
    Payload: { "blocker_id": str, "user_id": int }
    """
    blocker_id = payload.get("blocker_id")
    if not blocker_id:
        raise HTTPException(status_code=400, detail="blocker_id is required")

    from services.backend_api.db.models import ApplicationBlocker
    blocker = db.query(ApplicationBlocker).filter(ApplicationBlocker.blocker_id == blocker_id).first()
    if not blocker:
        raise HTTPException(status_code=404, detail="Blocker not found")

    connector = get_blocker_connector()
    
    # Convert DB model to dict for the connector
    blocker_dict = {
        "id": blocker.blocker_id,
        "type": blocker.blocker_type,
        "description": blocker.gap_description,
        "severity": blocker.criticality_score,
        "details": blocker.details if hasattr(blocker, 'details') else {}
    }
    
    try:
        suggestions = connector.get_improvement_suggestions(blocker_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    service = BlockerService(db)
    
    plan_ids = []
    rank = 1
    for sug in suggestions:
        plan_id = service.create_improvement_plan(
            blocker_id=blocker.blocker_id,
            plan_type="auto_generated",
            title=sug.get("title", "Plan " + str(rank)),
            description=sug.get("description", ""),
            action_items=sug.get("action_items", []),
            estimated_effort_hours=sug.get("estimated_effort", 1.0),
            priority_rank=rank
        )
        plan_ids.append(plan_id)
        rank += 1

    return {"status": "success", "generated_plans": len(plan_ids), "suggestions": suggestions}

