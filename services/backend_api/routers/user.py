
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from services.backend_api.db.connection import get_db
from services.backend_api.db import models
from services.backend_api.utils import security
# Import pydantic models if we had them, using dicts/params for now to save time in migration

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
