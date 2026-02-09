from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "user"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

# User Profile
class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int
    user_id: int
    
    class Config:
        orm_mode = True

# Resume
class ResumeBase(BaseModel):
    is_primary: bool = False

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    user_id: int
    file_path: str
    version: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Job
class JobBase(BaseModel):
    title: str
    company: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    source_url: Optional[str] = None

class JobCreate(JobBase):
    pass

class Job(JobBase):
    id: int
    posted_at: datetime
    is_active: bool
    
    class Config:
        orm_mode = True
