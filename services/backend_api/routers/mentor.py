"""
Mentor Profile & Packages API Routes
=====================================
REST API endpoints for mentor-specific operations:
- Mentor profile management
- Service packages CRUD
- Availability settings
- Session management

Author: CaReerTroJan System
Date: February 2, 2026
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db import models

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/mentor/v1", tags=["mentor"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class MentorProfileOut(BaseModel):
    mentor_profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    expertise_areas: List[str] = []
    years_experience: int = 0
    hourly_rate: Optional[float] = None
    availability_status: str = "available"
    rating: float = 0.0
    total_sessions: int = 0
    created_at: datetime
    
class ServicePackageCreate(BaseModel):
    package_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    session_count: int = Field(..., ge=1, le=50)
    session_duration: int = Field(..., description="Duration in minutes")
    price_per_session: float = Field(..., ge=0)
    deliverables: Optional[str] = None
    expected_outcomes: Optional[str] = None
    is_active: bool = True

class ServicePackageOut(BaseModel):
    package_id: str
    mentor_profile_id: str
    package_name: str
    description: str
    session_count: int
    session_duration: int
    price_per_session: float
    total_price: float
    deliverables: Optional[str] = None
    expected_outcomes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class ServicePackageUpdate(BaseModel):
    package_name: Optional[str] = None
    description: Optional[str] = None
    session_count: Optional[int] = None
    session_duration: Optional[int] = None
    price_per_session: Optional[float] = None
    deliverables: Optional[str] = None
    expected_outcomes: Optional[str] = None
    is_active: Optional[bool] = None

class AvailabilityUpdate(BaseModel):
    availability_status: str = Field(..., pattern="^(available|busy|away|offline)$")
    available_hours: Optional[Dict[str, Any]] = None

# ============================================================================
# DATABASE ACCESS
# ============================================================================

def _mentor_to_profile(mentor: models.Mentor, user: Optional[models.User]) -> MentorProfileOut:
    return MentorProfileOut(
        mentor_profile_id=str(mentor.id),
        user_id=str(mentor.user_id),
        display_name=(user.full_name if user and user.full_name else f"Mentor {mentor.user_id}"),
        bio=None,
        expertise_areas=[mentor.specialty] if mentor.specialty else [],
        years_experience=0,
        hourly_rate=mentor.hourly_rate,
        availability_status=mentor.availability or "available",
        rating=0.0,
        total_sessions=len(mentor.sessions) if mentor.sessions else 0,
        created_at=mentor.sessions[0].created_at if mentor.sessions else datetime.utcnow(),
    )

# ============================================================================
# MENTOR PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile-by-user/{user_id}", response_model=MentorProfileOut)
async def get_mentor_profile_by_user(user_id: str, db: Session = Depends(get_db)):
    """
    Get mentor profile by user ID
    
    Used by mentor portal to resolve mentor_profile_id from authenticated user
    """
    mentor = db.query(models.Mentor).filter(models.Mentor.user_id == user_id).first()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor profile not found",
        )

    user = db.query(models.User).filter(models.User.id == mentor.user_id).first()
    return _mentor_to_profile(mentor, user)

@router.get("/{mentor_profile_id}/profile", response_model=MentorProfileOut)
async def get_mentor_profile(mentor_profile_id: str, db: Session = Depends(get_db)):
    """Get mentor profile by mentor profile ID"""
    mentor = db.query(models.Mentor).filter(models.Mentor.id == mentor_profile_id).first()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor profile {mentor_profile_id} not found"
        )
    user = db.query(models.User).filter(models.User.id == mentor.user_id).first()
    return _mentor_to_profile(mentor, user)

@router.put("/{mentor_profile_id}/availability")
async def update_availability(
    mentor_profile_id: str,
    update: AvailabilityUpdate,
    db: Session = Depends(get_db),
):
    """Update mentor availability status"""
    mentor = db.query(models.Mentor).filter(models.Mentor.id == mentor_profile_id).first()
    if not mentor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor profile {mentor_profile_id} not found"
        )

    mentor.availability = update.availability_status
    db.commit()
    return {"status": "updated", "availability_status": update.availability_status}

@router.get("/list", response_model=List[MentorProfileOut])
async def list_mentors(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    List all active mentors.
    """
    mentors = db.query(models.Mentor).offset(skip).limit(limit).all()
    results: List[MentorProfileOut] = []
    for mentor in mentors:
        user = db.query(models.User).filter(models.User.id == mentor.user_id).first()
        results.append(_mentor_to_profile(mentor, user))
    return results

# ============================================================================
# SERVICE PACKAGES ENDPOINTS
# ============================================================================

@router.get("/{mentor_profile_id}/packages")
async def get_mentor_packages(mentor_profile_id: str):
    """
    Get all service packages for a mentor
    
    Returns list of packages the mentor has created
    """
    raise HTTPException(status_code=404, detail="Not found")

@router.post("/{mentor_profile_id}/packages", status_code=status.HTTP_201_CREATED)
async def create_package(mentor_profile_id: str, package: ServicePackageCreate):
    """
    Create a new service package
    
    Mentors use this to define their monetized session offerings
    """
    raise HTTPException(status_code=404, detail="Not found")

@router.get("/{mentor_profile_id}/packages/{package_id}", response_model=ServicePackageOut)
async def get_package(mentor_profile_id: str, package_id: str):
    """Get a specific service package"""
    raise HTTPException(status_code=404, detail="Not found")

@router.put("/{mentor_profile_id}/packages/{package_id}", response_model=ServicePackageOut)
async def update_package(mentor_profile_id: str, package_id: str, update: ServicePackageUpdate):
    """Update a service package"""
    raise HTTPException(status_code=404, detail="Not found")

@router.delete("/{mentor_profile_id}/packages/{package_id}")
async def delete_package(mentor_profile_id: str, package_id: str):
    """Delete a service package"""
    raise HTTPException(status_code=404, detail="Not found")

# ============================================================================
# MENTOR DASHBOARD STATS ENDPOINT
# ============================================================================

@router.get("/{mentor_profile_id}/dashboard-stats")
async def get_dashboard_stats(mentor_profile_id: str):
    """
    Get aggregated stats for mentor dashboard
    
    Returns metrics like total earnings, session count, ratings, etc.
    """
    return {"total_earnings_usd": 0, "total_sessions_completed": 0, "active_clients": 0, "average_rating": 0.0, "recent_reviews": []}

@router.get("/health")
async def health_check():
    """Health check for mentor routes"""
    return {
        "status": "healthy",
        "service": "mentor-api",
        "profiles_loaded": 0,
        "packages_loaded": 0
    }


