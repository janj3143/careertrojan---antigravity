from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


# ── GDPR & Audit Models ──────────────────────────────────────

class ConsentRecord(Base):
    """Tracks explicit user consent for data processing (GDPR Art. 7)."""
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String, nullable=False)   # "terms", "marketing", "data_processing", "cookies"
    granted = Column(Boolean, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    version = Column(String, default="1.0")         # policy version consented to
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="consent_records")


class AuditLog(Base):
    """Immutable audit trail for data-sensitive operations (GDPR Art. 30)."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # who triggered it (admin or user)
    action = Column(String, nullable=False, index=True)    # "data_export", "account_delete", "consent_grant", etc.
    resource_type = Column(String)                          # "user", "resume", "profile", etc.
    resource_id = Column(String)
    detail = Column(Text)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class DataExportRequest(Base):
    """Tracks data export requests (GDPR Art. 20 — right to data portability)."""
    __tablename__ = "data_export_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, default="pending")  # "pending", "processing", "completed", "failed"
    file_path = Column(String, nullable=True)   # path to generated export file
    requested_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # export link expiry

    user = relationship("User", backref="export_requests")


class Interaction(Base):
    """Database-backed interaction log for queryable analytics.
    Supplements the file-based interaction logger middleware."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String, index=True)
    action_type = Column(String, index=True)   # "cv_upload", "job_search", "coaching_session", "login", etc.
    method = Column(String)                     # HTTP method
    path = Column(String)                       # request path
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    ip_address = Column(String)
    user_agent = Column(String)
    metadata_json = Column(Text)                # extra context as JSON
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ── Payment & Subscription Models (Track D) ──────────────────

class Subscription(Base):
    """Tracks active user subscriptions managed by Braintree."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String, nullable=False, index=True)   # free, monthly, annual, elite
    gateway = Column(String, default="braintree")           # braintree | stripe
    gateway_subscription_id = Column(String, nullable=True, index=True)  # Braintree/Stripe sub ID
    gateway_customer_id = Column(String, nullable=True)
    status = Column(String, default="active", index=True)   # active, past_due, canceled, expired
    amount = Column(Float)
    currency = Column(String, default="USD")
    interval = Column(String)                                # month, year, null
    started_at = Column(DateTime, default=datetime.utcnow)
    next_billing_date = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="subscriptions")


class PaymentTransaction(Base):
    """Records all payment transactions (charges, refunds, voids)."""
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    gateway = Column(String, default="braintree")           # braintree | stripe
    gateway_transaction_id = Column(String, index=True)     # Braintree/Stripe TX ID
    transaction_type = Column(String, default="charge")     # charge, refund, void
    amount = Column(Float, nullable=False)
    currency = Column(String, default="GBP")
    status = Column(String, index=True)                     # submitted_for_settlement, settled, refunded, voided, failed
    plan_id = Column(String, nullable=True)
    promo_code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", backref="payment_transactions")


# ── Credit Balance & Usage Models ──────────────────────────────

class UserCreditBalance(Base):
    """Persistent credit balance per user, per billing period.
    
    Created when a user signs up (free tier) or upgrades plan.
    Updated on every credit consumption and monthly reset.
    """
    __tablename__ = "user_credit_balances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    plan_tier = Column(String, nullable=False, default="free")     # free | monthly | annual | elite
    credits_total = Column(Integer, nullable=False, default=15)
    credits_remaining = Column(Integer, nullable=False, default=15)
    credits_used = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="credit_balance")


class CreditUsageLog(Base):
    """Immutable log of every credit consumption.
    
    Records each action, cost, and remaining balance after the action.
    Used for analytics, billing disputes, and admin audit.
    """
    __tablename__ = "credit_usage_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_id = Column(String, nullable=False, index=True)        # from CreditAction enum
    action_name = Column(String)                                   # human-readable label
    credits_consumed = Column(Integer, nullable=False)
    credits_remaining_after = Column(Integer, nullable=False)
    is_preview = Column(Boolean, default=False)
    context_json = Column(Text, nullable=True)                     # optional JSON context
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", backref="credit_usage")


# ── Core Application Models ──────────────────────────────────

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


# ── Interview Coaching Models ────────────────────────────────

class RoleFunctionDefinition(Base):
    """Defines role functions (Marketing, Technical, Sales, etc.) with classification keywords."""
    __tablename__ = "role_function_definitions"

    id = Column(Integer, primary_key=True, index=True)
    function_code = Column(String(50), unique=True, nullable=False, index=True)  # marketing, technical, development, finance, sales, engineering, management
    display_name = Column(String(100), nullable=False)  # "Marketing", "Technical (IT & Infrastructure)", etc.
    description = Column(Text)
    classification_keywords = Column(JSON)  # {"titles": ["Marketing Manager", ...], "skills": ["SEO", ...], "industries": [...]}
    seniority_indicators = Column(JSON)  # {"entry": [...], "mid": [...], "senior": [...], "executive": [...]}
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    questions = relationship("InterviewQuestionBank", back_populates="role_function")
    plan_templates = relationship("NinetyDayPlanTemplate", back_populates="role_function")


class InterviewQuestionBank(Base):
    """Role-specific interview questions with categories and strategic tips."""
    __tablename__ = "interview_question_bank"

    id = Column(Integer, primary_key=True, index=True)
    role_function_id = Column(Integer, ForeignKey("role_function_definitions.id"), nullable=False, index=True)
    question_category = Column(String(100), nullable=False, index=True)  # "Role-specific", "Culture", "Closing", "Good vs Great", "90-Day", etc.
    question_text = Column(Text, nullable=False)
    question_purpose = Column(Text)  # Why this question matters
    sample_answer_framework = Column(Text)  # STAR structure hints, key points
    interviewer_insight = Column(Text)  # What the interviewer is looking for
    difficulty_level = Column(String(20), default="standard")  # entry, standard, advanced, executive
    source_attribution = Column(String(255))  # "Harvard Business Review", "BetterUp", etc.
    tags = Column(JSON)  # ["closing", "strategic", "culture-fit", etc.]
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    effectiveness_score = Column(Float, default=0.0)  # Feedback-driven
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role_function = relationship("RoleFunctionDefinition", back_populates="questions")


class NinetyDayPlanTemplate(Base):
    """30-60-90 day plan templates per role function."""
    __tablename__ = "ninety_day_plan_templates"

    id = Column(Integer, primary_key=True, index=True)
    role_function_id = Column(Integer, ForeignKey("role_function_definitions.id"), nullable=False, index=True)
    seniority_level = Column(String(50), default="mid")  # entry, mid, senior, executive
    template_name = Column(String(200), nullable=False)
    focus_areas = Column(JSON)  # {"day_30": "Absorption", "day_60": "Application", "day_90": "Ownership"}
    day_30_actions = Column(JSON)  # ["Shadow key processes", "1-on-1s with stakeholders", ...]
    day_30_success_metric = Column(Text)  # SMART metric
    day_60_actions = Column(JSON)
    day_60_success_metric = Column(Text)
    day_90_actions = Column(JSON)
    day_90_success_metric = Column(Text)
    smart_reports = Column(JSON)  # {"day_30": "Onboarding Reflection", "day_60": "Quick Win Post-Mortem", "day_90": "Strategic Roadmap"}
    closing_statement = Column(Text)  # "What one result would earn me an A?"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    role_function = relationship("RoleFunctionDefinition", back_populates="plan_templates")


class UserInterviewSession(Base):
    """Tracks user interview practice sessions."""
    __tablename__ = "user_interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    detected_role_function_id = Column(Integer, ForeignKey("role_function_definitions.id"), nullable=True)
    confirmed_role_function_id = Column(Integer, ForeignKey("role_function_definitions.id"), nullable=True)
    session_type = Column(String(50), default="practice")  # practice, mock, real_prep
    questions_asked = Column(JSON)  # List of question IDs attempted
    answers_given = Column(JSON)  # {"question_id": {"answer": "...", "feedback": {...}, "score": 0.8}}
    overall_score = Column(Float)
    ai_feedback_summary = Column(Text)
    duration_minutes = Column(Integer)
    status = Column(String(50), default="in_progress")  # in_progress, completed, abandoned
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")
    detected_function = relationship("RoleFunctionDefinition", foreign_keys=[detected_role_function_id])
    confirmed_function = relationship("RoleFunctionDefinition", foreign_keys=[confirmed_role_function_id])


class UserNinetyDayPlan(Base):
    """User's customized 90-day plan based on template + job context."""
    __tablename__ = "user_ninety_day_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("ninety_day_plan_templates.id"), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    job_title_text = Column(String(255))  # Denormalized for quick display
    company_text = Column(String(255))
    customized_day_30 = Column(JSON)  # User edits
    customized_day_60 = Column(JSON)
    customized_day_90 = Column(JSON)
    customized_reports = Column(JSON)
    personal_closing_statement = Column(Text)
    is_exported = Column(Boolean, default=False)
    export_format = Column(String(50))  # pdf, docx, notion
    status = Column(String(50), default="draft")  # draft, finalized, used_in_interview
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    template = relationship("NinetyDayPlanTemplate")


# ── Support Tickets (Zendesk Bridge) ─────────────────────────

class SupportTicket(Base):
    """Internal support ticket tracking — synced with Zendesk."""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    zendesk_ticket_id = Column(Integer, unique=True, index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="new", index=True)  # new, open, pending, hold, solved, closed
    priority = Column(String(50), default="normal")  # low, normal, high, urgent
    category = Column(String(100), index=True)  # billing, login, ai_output, bugs, feature_request
    portal = Column(String(50), index=True)  # user_portal, admin_portal, mentor_portal
    request_id = Column(String(100), nullable=True, index=True)  # trace specific AI run
    resume_version_id = Column(Integer, nullable=True)  # if relevant
    subscription_tier = Column(String(50), nullable=True)  # free, premium, elite
    tokens_remaining = Column(Integer, nullable=True)
    zendesk_url = Column(String(500), nullable=True)
    last_comment_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # extra context (plan/tokens/request_id)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="support_tickets")
