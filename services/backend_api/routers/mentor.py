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
import uuid

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
# IN-MEMORY STORAGE (Replace with database in production)
# ============================================================================

# Temporary storage - replace with PostgreSQL queries
_mentor_profiles: Dict[str, Dict[str, Any]] = {}
_service_packages: Dict[str, Dict[str, Any]] = {}

def _get_mentor_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get mentor profile by user ID"""
    for profile_id, profile in _mentor_profiles.items():
        if profile.get("user_id") == user_id:
            return profile
    return None

def _ensure_demo_mentor(user_id: str) -> Dict[str, Any]:
    """Ensure a demo mentor profile exists for testing"""
    existing = _get_mentor_by_user_id(user_id)
    if existing:
        return existing
    
    profile_id = f"mentor_{uuid.uuid4().hex[:8]}"
    profile = {
        "mentor_profile_id": profile_id,
        "user_id": user_id,
        "display_name": f"Mentor {user_id[:8]}",
        "bio": "Experienced career mentor helping professionals achieve their goals.",
        "expertise_areas": ["Career Coaching", "Leadership", "Interview Prep"],
        "years_experience": 10,
        "hourly_rate": 150.0,
        "availability_status": "available",
        "rating": 4.8,
        "total_sessions": 0,
        "created_at": datetime.utcnow()
    }
    _mentor_profiles[profile_id] = profile
    return profile

# ============================================================================
# MENTOR PROFILE ENDPOINTS
# ============================================================================

@router.get("/profile-by-user/{user_id}", response_model=MentorProfileOut)
async def get_mentor_profile_by_user(user_id: str):
    """
    Get mentor profile by user ID
    
    Used by mentor portal to resolve mentor_profile_id from authenticated user
    """
    profile = _get_mentor_by_user_id(user_id)
    if not profile:
        # Auto-create for demo purposes
        profile = _ensure_demo_mentor(user_id)
    
    return MentorProfileOut(**profile)

@router.get("/{mentor_profile_id}/profile", response_model=MentorProfileOut)
async def get_mentor_profile(mentor_profile_id: str):
    """Get mentor profile by mentor profile ID"""
    if mentor_profile_id not in _mentor_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor profile {mentor_profile_id} not found"
        )
    return MentorProfileOut(**_mentor_profiles[mentor_profile_id])

@router.put("/{mentor_profile_id}/availability")
async def update_availability(mentor_profile_id: str, update: AvailabilityUpdate):
    """Update mentor availability status"""
    if mentor_profile_id not in _mentor_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mentor profile {mentor_profile_id} not found"
        )
    
    _mentor_profiles[mentor_profile_id]["availability_status"] = update.availability_status
    if update.available_hours:
        _mentor_profiles[mentor_profile_id]["available_hours"] = update.available_hours
    
    return {"status": "updated", "availability_status": update.availability_status}

@router.get("/list", response_model=List[MentorProfileOut])
async def list_mentors(skip: int = 0, limit: int = 20):
    """
    List all active mentors.
    """
    mentors = list(_mentor_profiles.values())
    return mentors[skip : skip + limit]

# ============================================================================
# SERVICE PACKAGES ENDPOINTS
# ============================================================================

@router.get("/{mentor_profile_id}/packages")
async def get_mentor_packages(mentor_profile_id: str):
    """
    Get all service packages for a mentor
    
    Returns list of packages the mentor has created
    """
    packages = [
        pkg for pkg in _service_packages.values()
        if pkg.get("mentor_profile_id") == mentor_profile_id
    ]
    return {"packages": packages, "count": len(packages)}

@router.post("/{mentor_profile_id}/packages", status_code=status.HTTP_201_CREATED)
async def create_package(mentor_profile_id: str, package: ServicePackageCreate):
    """
    Create a new service package
    
    Mentors use this to define their monetized session offerings
    """
    if mentor_profile_id not in _mentor_profiles:
        # Auto-create profile for demo
        _mentor_profiles[mentor_profile_id] = {
            "mentor_profile_id": mentor_profile_id,
            "user_id": mentor_profile_id,
            "display_name": "New Mentor",
            "created_at": datetime.utcnow()
        }
    
    package_id = f"pkg_{uuid.uuid4().hex[:8]}"
    total_price = package.session_count * package.price_per_session
    
    new_package = {
        "package_id": package_id,
        "mentor_profile_id": mentor_profile_id,
        "package_name": package.package_name,
        "description": package.description,
        "session_count": package.session_count,
        "session_duration": package.session_duration,
        "price_per_session": package.price_per_session,
        "total_price": total_price,
        "deliverables": package.deliverables,
        "expected_outcomes": package.expected_outcomes,
        "is_active": package.is_active,
        "created_at": datetime.utcnow(),
        "updated_at": None
    }
    
    _service_packages[package_id] = new_package
    logger.info(f"Created package {package_id} for mentor {mentor_profile_id}")
    
    return ServicePackageOut(**new_package)

@router.get("/{mentor_profile_id}/packages/{package_id}", response_model=ServicePackageOut)
async def get_package(mentor_profile_id: str, package_id: str):
    """Get a specific service package"""
    if package_id not in _service_packages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package {package_id} not found"
        )
    
    package = _service_packages[package_id]
    if package.get("mentor_profile_id") != mentor_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Package does not belong to this mentor"
        )
    
    return ServicePackageOut(**package)

@router.put("/{mentor_profile_id}/packages/{package_id}", response_model=ServicePackageOut)
async def update_package(mentor_profile_id: str, package_id: str, update: ServicePackageUpdate):
    """Update a service package"""
    if package_id not in _service_packages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package {package_id} not found"
        )
    
    package = _service_packages[package_id]
    if package.get("mentor_profile_id") != mentor_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Package does not belong to this mentor"
        )
    
    # Update fields
    update_data = update.dict(exclude_unset=True)
    for field, value in update_data.items():
        package[field] = value
    
    # Recalculate total price if needed
    if "session_count" in update_data or "price_per_session" in update_data:
        package["total_price"] = package["session_count"] * package["price_per_session"]
    
    package["updated_at"] = datetime.utcnow()
    _service_packages[package_id] = package
    
    return ServicePackageOut(**package)

@router.delete("/{mentor_profile_id}/packages/{package_id}")
async def delete_package(mentor_profile_id: str, package_id: str):
    """Delete a service package"""
    if package_id not in _service_packages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package {package_id} not found"
        )
    
    package = _service_packages[package_id]
    if package.get("mentor_profile_id") != mentor_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Package does not belong to this mentor"
        )
    
    del _service_packages[package_id]
    logger.info(f"Deleted package {package_id} for mentor {mentor_profile_id}")
    
    return {"status": "deleted", "package_id": package_id}

# ============================================================================
# MENTOR DASHBOARD STATS ENDPOINT
# ============================================================================

@router.get("/{mentor_profile_id}/dashboard-stats")
async def get_dashboard_stats(mentor_profile_id: str):
    """
    Get aggregated stats for mentor dashboard
    
    Returns metrics like total earnings, session count, ratings, etc.
    """
    packages = [
        pkg for pkg in _service_packages.values()
        if pkg.get("mentor_profile_id") == mentor_profile_id
    ]
    
    profile = _mentor_profiles.get(mentor_profile_id, {})
    
    return {
        "mentor_profile_id": mentor_profile_id,
        "display_name": profile.get("display_name", "Mentor"),
        "total_packages": len(packages),
        "active_packages": sum(1 for p in packages if p.get("is_active", True)),
        "total_sessions": profile.get("total_sessions", 0),
        "rating": profile.get("rating", 0.0),
        "availability_status": profile.get("availability_status", "available"),
        "earnings_this_month": 0.0,  # TODO: Calculate from invoices
        "earnings_total": 0.0,  # TODO: Calculate from invoices
        "pending_sessions": 0,  # TODO: Calculate from links
        "active_mentees": 0  # TODO: Calculate from links
    }

@router.get("/health")
async def health_check():
    """Health check for mentor routes"""
    return {
        "status": "healthy",
        "service": "mentor-api",
        "profiles_loaded": len(_mentor_profiles),
        "packages_loaded": len(_service_packages)
    }
