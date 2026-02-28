
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security


# ═══════════════════════════════════════════════════════════
# Pydantic Request/Response Models
# ═══════════════════════════════════════════════════════════

class ProfileUpdateRequest(BaseModel):
    """Validated profile update payload."""
    bio: Optional[str] = Field(None, max_length=2000, description="User bio / summary")
    linkedin: Optional[str] = Field(None, max_length=500, pattern=r"^https?://(www\.)?linkedin\.com/.*$", description="LinkedIn profile URL")
    github: Optional[str] = Field(None, max_length=500, pattern=r"^https?://(www\.)?github\.com/.*$", description="GitHub profile URL")
    location: Optional[str] = Field(None, max_length=200, description="User location")


class UserResponse(BaseModel):
    """Canonical user info response."""
    id: int
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    """Canonical profile response."""
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Dashboard statistics."""
    job_matches: int = 0
    cv_score: int = 0
    applications_submitted: int = 0
    interviews_scheduled: int = 0
    messages_unread: int = 0
    profile_views: int = 0
    saved_jobs: int = 0
    profile_completion: int = 0


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    timestamp: str
    icon: str

router = APIRouter(prefix="/api/user/v1", tags=["user"])

# Dependency to get current user
def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except security.jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
    )

@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: models.User = Depends(get_current_user)):
    if not current_user.profile:
        return ProfileResponse()
    return ProfileResponse.model_validate(current_user.profile)

@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    profile = current_user.profile
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)
    
    if payload.bio is not None: profile.bio = payload.bio
    if payload.linkedin is not None: profile.linkedin_url = payload.linkedin
    if payload.github is not None: profile.github_url = payload.github
    if payload.location is not None: profile.location = payload.location
    
    db.commit()
    db.refresh(profile)
    return ProfileResponse.model_validate(profile)


# ============================================================================
# Statistics & Activity Endpoints
# ============================================================================

@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get user dashboard statistics including:
    - Job matches count
    - CV score (if analyzed)
    - Applications submitted
    - Interview invitations
    - Messages count
    """
    user_id = current_user.id
    
    # Calculate stats from database
    # For now, return demo stats - connect to real tables as they're built
    stats = {
        "job_matches": 12,
        "cv_score": 78,
        "applications_submitted": 8,
        "interviews_scheduled": 3,
        "messages_unread": 2,
        "profile_views": 45,
        "saved_jobs": 15,
        "profile_completion": 85
    }
    
    return stats


@router.get("/activity", response_model=List[ActivityItem])
def get_user_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = 10
):
    """
    Get recent user activity feed including:
    - Application submissions
    - Interview invitations
    - Profile views
    - Job matches
    """
    from datetime import datetime, timedelta
    
    # Demo activity feed - connect to real activity log when available
    now = datetime.now()
    activities = [
        {
            "id": "act_1",
            "type": "application",
            "title": "Applied to Senior Developer at TechCorp",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "icon": "briefcase"
        },
        {
            "id": "act_2",
            "type": "interview",
            "title": "Interview scheduled with DataSystems",
            "timestamp": (now - timedelta(hours=8)).isoformat(),
            "icon": "calendar"
        },
        {
            "id": "act_3",
            "type": "profile_view",
            "title": "Your profile was viewed by a recruiter",
            "timestamp": (now - timedelta(days=1)).isoformat(),
            "icon": "eye"
        },
        {
            "id": "act_4",
            "type": "match",
            "title": "New job match: ML Engineer at AI Labs",
            "timestamp": (now - timedelta(days=1, hours=5)).isoformat(),
            "icon": "zap"
        },
        {
            "id": "act_5",
            "type": "resume",
            "title": "Resume analyzed - Score: 78%",
            "timestamp": (now - timedelta(days=2)).isoformat(),
            "icon": "file-text"
        }
    ]
    
    return activities[:limit]
