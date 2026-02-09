from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String, default="user")  # 'admin', 'user', 'mentor'
    otp_secret = Column(String, nullable=True) # 2FA Secret
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    resumes = relationship("Resume", back_populates="user")
    mentorship_requests = relationship("Mentorship", back_populates="mentee", foreign_keys="Mentorship.mentee_id")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(Text)
    linkedin_url = Column(String)
    github_url = Column(String)
    website_url = Column(String)
    phone_number = Column(String)
    location = Column(String)
    
    user = relationship("User", back_populates="profile")

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String, nullable=False)
    version = Column(Integer, default=1)
    is_primary = Column(Boolean, default=False)
    parsed_content = Column(Text)  # JSON string or link to parsed data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="resumes")

class Mentor(Base):
    __tablename__ = "mentors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    specialty = Column(String)
    hourly_rate = Column(Float)
    availability = Column(String)
    
    user = relationship("User")
    sessions = relationship("Mentorship", back_populates="mentor", foreign_keys="Mentorship.mentor_id")

class Mentorship(Base):
    __tablename__ = "mentorships"
    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id"))
    mentee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending") # pending, accepted, rejected, completed
    scheduled_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    mentor = relationship("Mentor", back_populates="sessions")
    mentee = relationship("User", back_populates="mentorship_requests")

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    company = Column(String, index=True, nullable=False)
    description = Column(Text)
    requirements = Column(Text)
    location = Column(String)
    posted_at = Column(DateTime, default=datetime.utcnow)
    source_url = Column(String)
    is_active = Column(Boolean, default=True)

class MentorNote(Base):
    __tablename__ = "mentor_notes"
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("mentorships.id")) # Maps to mentorship_links.link_id concept
    mentor_id = Column(Integer, ForeignKey("users.id"))
    note_type = Column(String, default="session")
    note_content = Column(Text)
    note_title = Column(String)
    is_shared_with_user = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    mentorship = relationship("Mentorship")

class RequirementDocument(Base):
    __tablename__ = "requirement_documents"
    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"))
    title = Column(String)
    content = Column(Text)
    status = Column(String, default="draft")
    mentor_signed = Column(Boolean, default=False)
    user_signed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    mentorship_id = Column(Integer, ForeignKey("mentorships.id"))
    amount = Column(Float)
    description = Column(String)
    status = Column(String, default="pending")
    invoice_number = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MentorApplication(Base):
    __tablename__ = "mentor_applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    full_name = Column(String)
    email = Column(String)
    data_json = Column(Text) # JSON string
    status = Column(String, default="submitted")
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Blocker System Models ---
import uuid

class ApplicationBlocker(Base):
    __tablename__ = "application_blockers"

    blocker_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_id = Column(String, nullable=True) # Linking to legacy ID
    jd_id = Column(String, nullable=True)
    application_id = Column(String, nullable=True)
    
    blocker_type = Column(String) # skill_gap, experience_gap, etc.
    blocker_category = Column(String)
    requirement_text = Column(String)
    gap_description = Column(String)
    
    criticality_score = Column(Float)
    severity_level = Column(String) # Enum as string for SQLite compat
    impact_on_application = Column(Float)
    
    detected_by = Column(String)
    detection_method = Column(String)
    confidence_score = Column(Float)
    evidence_data = Column(JSON)
    
    is_addressable = Column(Boolean, default=True)
    improvement_timeline = Column(String)
    improvement_difficulty = Column(String)
    
    status = Column(String, default="active") # active, resolved, ignored
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    improvement_plans = relationship("BlockerImprovementPlan", back_populates="blocker")


class BlockerImprovementPlan(Base):
    __tablename__ = "blocker_improvement_plans"

    plan_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    blocker_id = Column(String, ForeignKey("application_blockers.blocker_id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    plan_title = Column(String)
    plan_description = Column(String)
    plan_type = Column(String) # course, project, mentorship
    
    resource_name = Column(String, nullable=True)
    resource_provider = Column(String, nullable=True)
    resource_url = Column(String, nullable=True)
    resource_cost = Column(Float, default=0.0)
    
    estimated_duration_hours = Column(Integer)
    estimated_completion_weeks = Column(Integer)
    expected_improvement_score = Column(Float)
    
    priority_rank = Column(Integer)
    ai_recommendation_score = Column(Float)
    success_probability = Column(Float)
    milestones_total = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    blocker = relationship("ApplicationBlocker", back_populates="improvement_plans")

