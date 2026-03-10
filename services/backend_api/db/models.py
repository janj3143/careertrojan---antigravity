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


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    zendesk_ticket_id = Column(String, index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    subject = Column(String, nullable=False)
    status = Column(String, default="new", index=True)
    priority = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    request_id = Column(String, nullable=True, index=True)
    portal = Column(String, nullable=True)
    last_comment_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    user = relationship("User", backref="support_tickets")


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

    # ── Payment / Braintree linkage ──
    braintree_customer_id = Column(String, nullable=True, index=True)
    subscription_tier = Column(String, default="free")  # free, monthly, annual, elitepro
    subscription_id = Column(String, nullable=True)      # active Subscription.id FK (loose ref)
    stripe_customer_id = Column(String, nullable=True, index=True)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    resumes = relationship("Resume", back_populates="user")
    mentorship_requests = relationship("Mentorship", back_populates="mentee", foreign_keys="Mentorship.mentee_id")
    subscriptions = relationship("Subscription", back_populates="user", order_by="Subscription.created_at.desc()")
    payment_transactions = relationship("PaymentTransaction", back_populates="user", order_by="PaymentTransaction.created_at.desc()")

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


# ── Rewards & Referral System Models ──────────────────────────────────

class UserReward(Base):
    """Tracks individual reward tokens earned by users."""
    __tablename__ = "user_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reward_type = Column(String, nullable=False, index=True)  # referral, activity, milestone, bonus, suggestion
    tokens = Column(Integer, nullable=False)
    description = Column(String)
    status = Column(String, default="active", index=True)  # pending, active, redeemed, expired
    action_key = Column(String, index=True)  # e.g., "profile_complete", "resume_upload"
    source_id = Column(String, nullable=True)  # referral_id, suggestion_id, etc.
    earned_at = Column(DateTime, default=datetime.utcnow)
    redeemed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="rewards")


class UserReferral(Base):
    """Tracks user referral codes and their usage."""
    __tablename__ = "user_referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # null until user signs up
    referral_code = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="pending", index=True)  # pending, signed_up, subscribed, expired
    tokens_awarded = Column(Integer, default=0)
    signup_at = Column(DateTime, nullable=True)
    subscription_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", foreign_keys=[referrer_id], backref="referrals_sent")
    referee = relationship("User", foreign_keys=[referee_id], backref="referred_by")


class UserSuggestion(Base):
    """Tracks user feature suggestions and feedback."""
    __tablename__ = "user_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String, nullable=False)  # feature, improvement, bug, other
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="submitted", index=True)  # submitted, reviewed, accepted, implemented, rejected
    tokens_awarded = Column(Integer, default=0)
    admin_notes = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], backref="suggestions")


class UserCompletedAction(Base):
    """Tracks which reward actions a user has completed (for one-time rewards)."""
    __tablename__ = "user_completed_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_key = Column(String, nullable=False, index=True)  # profile_complete, resume_upload, etc.
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="completed_actions")

    __table_args__ = (
        # Prevent duplicate action completions per user
        {"sqlite_autoincrement": True},
    )


class RewardRedemption(Base):
    """Tracks reward redemption history."""
    __tablename__ = "reward_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    redemption_type = Column(String, nullable=False)  # premium_day, ai_boost, mentor_session
    tokens_spent = Column(Integer, nullable=False)
    description = Column(String)
    redeemed_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # when the granted benefit expires

    user = relationship("User", backref="redemptions")

# ── Payment & Subscription Models ─────────────────────────────────────

class Subscription(Base):
    """Tracks user subscriptions (Braintree recurring or manual)."""
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: f"sub_{uuid.uuid4().hex[:16]}")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String, nullable=False, index=True)        # free, monthly, annual, elitepro
    gateway = Column(String, default="braintree")                # braintree | stripe | manual
    gateway_subscription_id = Column(String, nullable=True)      # Braintree/Stripe subscription ID
    gateway_customer_id = Column(String, nullable=True)          # Braintree/Stripe customer ID

    status = Column(String, default="active", index=True)        # active, cancelled, past_due, expired, trialing
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    interval = Column(String, nullable=True)                     # month, year, null (one-time / free)
    promo_code = Column(String, nullable=True)
    discount_amount = Column(Float, default=0.0)

    started_at = Column(DateTime, default=datetime.utcnow)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)         # next_billing_date
    cancelled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    transactions = relationship("PaymentTransaction", back_populates="subscription")


class PaymentTransaction(Base):
    """Records every payment charge, refund, or void."""
    __tablename__ = "payment_transactions"

    id = Column(String, primary_key=True, default=lambda: f"tx_{uuid.uuid4().hex[:16]}")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(String, ForeignKey("subscriptions.id"), nullable=True, index=True)

    gateway = Column(String, default="braintree")                # braintree | stripe
    gateway_transaction_id = Column(String, nullable=True, index=True)  # Braintree/Stripe tx ID
    transaction_type = Column(String, default="charge")          # charge, refund, void
    status = Column(String, default="pending", index=True)       # pending, completed, failed, refunded, voided

    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    plan_id = Column(String, nullable=True)
    description = Column(String, nullable=True)

    payment_method_type = Column(String, nullable=True)          # card, paypal, apple_pay
    payment_method_last4 = Column(String, nullable=True)
    payment_method_brand = Column(String, nullable=True)         # visa, mastercard, amex

    gateway_response = Column(JSON, nullable=True)               # full gateway response (for debugging)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="payment_transactions")
    subscription = relationship("Subscription", back_populates="transactions")


class PromoCode(Base):
    """Discount promo codes for subscriptions."""
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    discount_type = Column(String, default="percent")            # percent | fixed
    discount_value = Column(Float, nullable=False)               # 20 = 20% or $20
    max_uses = Column(Integer, nullable=True)                    # null = unlimited
    times_used = Column(Integer, default=0)
    valid_plans = Column(String, nullable=True)                  # comma-separated plan IDs, null = all
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookEvent(Base):
    """Logs incoming webhook payloads for auditing and deduplication."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, nullable=False, index=True)  # gateway event ID (idempotency)
    source = Column(String, nullable=False, index=True)          # braintree | stripe | zendesk
    event_type = Column(String, nullable=False, index=True)      # e.g. subscription_charged_successfully
    payload = Column(JSON, nullable=True)
    status = Column(String, default="received", index=True)      # received, processed, failed, ignored
    error_message = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)