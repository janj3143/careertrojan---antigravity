from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db.models import Resume
from services.backend_api.routers.career_compass import _vector_from_text
from services.backend_api.routers.runtime_contract import respond


router = APIRouter(prefix="/api/v1/user-vector", tags=["user-vector-v1"])


@router.get("/current")
def get_current_user_vector(
    user_id: int = Query(..., ge=1),
    resume_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    query = db.query(Resume).filter(Resume.user_id == user_id)
    if resume_id is not None:
        query = query.filter(Resume.id == resume_id)

    resume_row = query.order_by(Resume.created_at.desc()).first()
    if not resume_row:
        return respond(
            status="missing_resume",
            message="No live parsed resume available for this user.",
            data={"vector": None, "confidence": None},
            source_summary={
                "resume_id": None,
                "profile_response_count": 0,
            },
        )

    parsed_text = (resume_row.parsed_content or "").strip()
    if not parsed_text:
        return respond(
            status="missing_resume",
            message="The resolved resume does not contain parsed content.",
            data={"vector": None, "confidence": None},
            source_summary={
                "resume_id": str(resume_row.id),
                "profile_response_count": 0,
            },
        )

    vector = _vector_from_text(parsed_text)
    confidence = {key: 0.7 for key in vector.keys()}

    return respond(
        status="ok",
        data={"vector": vector, "confidence": confidence},
        source_summary={
            "resume_id": str(resume_row.id),
            "profile_response_count": 0,
        },
    )
