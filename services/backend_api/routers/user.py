
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from services.shared.paths import CareerTrojanPaths

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security
# Import pydantic models if we had them, using dicts/params for now to save time in migration

router = APIRouter(prefix="/api/user/v1", tags=["user"])

# Dependency to get current user
def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except security.TokenValidationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

@router.get("/profile")
def get_profile(current_user: models.User = Depends(get_current_user)):
    if not current_user.profile:
        return {}
    return current_user.profile

@router.put("/profile")
def update_profile(
    bio: Optional[str] = None,
    linkedin: Optional[str] = None,
    github: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    profile = current_user.profile
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)
    
    if bio is not None: profile.bio = bio
    if linkedin is not None: profile.linkedin_url = linkedin
    if github is not None: profile.github_url = github
    if location is not None: profile.location = location
    
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/stats")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    resume_count = db.query(models.Resume).filter(models.Resume.user_id == current_user.id).count()
    interaction_count = db.query(models.Interaction).filter(models.Interaction.user_id == current_user.id).count()
    mentorship_count = db.query(models.Mentorship).filter(models.Mentorship.mentee_id == current_user.id).count()

    return {
        "resume_count": resume_count,
        "interaction_count": interaction_count,
        "mentorship_count": mentorship_count,
    }


@router.get("/activity")
def get_user_activity(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interactions = (
        db.query(models.Interaction)
        .filter(models.Interaction.user_id == current_user.id)
        .order_by(models.Interaction.created_at.desc())
        .limit(limit)
        .all()
    )

    activity = []
    for entry in interactions:
        try:
            metadata = json.loads(entry.metadata_json) if entry.metadata_json else None
        except Exception:
            metadata = None

        activity.append({
            "id": entry.id,
            "action_type": entry.action_type,
            "path": entry.path,
            "status_code": entry.status_code,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "metadata": metadata,
        })

    return {"activity": activity}


@router.get("/sessions/summary")
def get_user_session_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    interactions = (
        db.query(models.Interaction)
        .filter(models.Interaction.user_id == current_user.id)
        .order_by(models.Interaction.created_at.desc())
        .all()
    )

    total_sessions = len(interactions)
    total_page_views = sum(1 for i in interactions if i.action_type == "page_view")
    last_session_date = interactions[0].created_at.isoformat() if interactions else "Never"

    return {
        "totalSessions": total_sessions,
        "totalPageViews": total_page_views,
        "lastSessionDate": last_session_date,
        "averageDuration": "—",
    }


@router.get("/resume/latest")
def get_latest_resume(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    latest = (
        db.query(models.Resume)
        .filter(models.Resume.user_id == current_user.id)
        .order_by(models.Resume.created_at.desc())
        .first()
    )

    if not latest:
        return {}

    return {
        "resume_id": latest.id,
        "file_path": latest.file_path,
        "version": latest.version,
        "is_primary": latest.is_primary,
        "created_at": latest.created_at.isoformat() if latest.created_at else None,
    }


@router.get("/matches/summary")
def get_match_summary(
    current_user: models.User = Depends(get_current_user),
):
    paths = CareerTrojanPaths()
    matches_path = paths.user_data / "ai_matches" / f"{current_user.id}_matches.json"
    if not matches_path.exists():
        return {"matches": [], "summary": {"count": 0}}

    try:
        data = json.loads(matches_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read match summary: {exc}")

    matches = data.get("matches", []) if isinstance(data, dict) else data
    return {
        "matches": matches,
        "summary": {"count": len(matches)},
    }
