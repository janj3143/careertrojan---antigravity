"""
Data Capture Policy — CareerTrojan (Track E, Step E2)
======================================================

Central definition of WHAT user data is captured, WHY, and HOW LONG it's kept.
This file serves as both code documentation and the source of truth for:
  - GDPR Article 30 data processing records
  - Privacy policy content generation
  - Interaction logger classification
  - Data retention automation

All captured data categories are listed here with:
  - Category name
  - Data points collected
  - Legal basis (GDPR)
  - Retention period
  - Where stored
  - Whether anonymised copy goes to AI training
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DataCategory:
    """A category of user data that CareerTrojan collects."""
    name: str
    description: str
    data_points: List[str]
    legal_basis: str           # "consent", "contract", "legitimate_interest"
    retention_days: int        # How long raw data is kept (0 = until account deletion)
    storage: str               # Where primary data lives
    feeds_ai: bool             # Whether anonymised copy goes to AI pipeline
    ai_target: Optional[str]   # Which ai_data_final subdirectory it enriches
    gdpr_exportable: bool      # Included in Art. 20 data export
    gdpr_deletable: bool       # Deleted on Art. 17 account deletion


# ============================================================================
# THE FULL DATA CAPTURE POLICY
# ============================================================================

DATA_CAPTURE_POLICY: List[DataCategory] = [

    DataCategory(
        name="Profile Data",
        description="Core identity and professional information provided by the user",
        data_points=[
            "Full name",
            "Email address",
            "Phone number (optional)",
            "Location / city",
            "LinkedIn URL (optional)",
            "GitHub URL (optional)",
            "Bio / summary",
            "Skills list",
            "Experience level",
            "Industry preferences",
        ],
        legal_basis="contract",
        retention_days=0,  # kept until account deletion
        storage="PostgreSQL: users + user_profiles",
        feeds_ai=True,
        ai_target="profiles",
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="CV / Resume Uploads",
        description="Document files uploaded by users for AI analysis and tuning",
        data_points=[
            "Original file (PDF/DOCX)",
            "Parsed text content (JSON)",
            "Extracted skills and keywords",
            "Version history",
            "AI analysis scores",
        ],
        legal_basis="contract",
        retention_days=0,
        storage="PostgreSQL: resumes + file storage (local volume / S3)",
        feeds_ai=True,
        ai_target="parsed_resumes",
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="Job Search Queries",
        description="What jobs users search for — powers the matching engine",
        data_points=[
            "Search keywords",
            "Location filters",
            "Salary range preferences",
            "Industry / sector filters",
            "Remote / hybrid preferences",
            "Results viewed",
            "Results clicked",
        ],
        legal_basis="contract",
        retention_days=365,
        storage="PostgreSQL: interactions (action_type='job_search')",
        feeds_ai=True,
        ai_target="job_matching",
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="AI Match Results",
        description="What the AI suggested and how the user responded",
        data_points=[
            "Job recommendations shown",
            "Match confidence scores",
            "User accepted / dismissed / saved",
            "Application started from recommendation",
        ],
        legal_basis="legitimate_interest",
        retention_days=365,
        storage="PostgreSQL: interactions + Redis cache",
        feeds_ai=True,
        ai_target="job_matching",
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="Coaching Interactions",
        description="Questions asked and advice given in AI coaching sessions",
        data_points=[
            "Questions / prompts submitted",
            "AI responses generated",
            "Session duration",
            "Topics discussed (classified)",
            "User feedback (helpful / not helpful)",
        ],
        legal_basis="contract",
        retention_days=365,
        storage="PostgreSQL: interactions (action_type='coaching_session')",
        feeds_ai=True,
        ai_target="learning_library",
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="Session Logs",
        description="Technical session data for security and analytics",
        data_points=[
            "Login timestamps",
            "Pages visited (path, not content)",
            "Time on page (response_time_ms)",
            "Device / user-agent",
            "IP address (hashed after 30 days)",
            "Session ID",
        ],
        legal_basis="legitimate_interest",
        retention_days=90,
        storage="PostgreSQL: interactions + disk (JSON files)",
        feeds_ai=False,
        ai_target=None,
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="Feedback Signals",
        description="Implicit and explicit user feedback that improves AI quality",
        data_points=[
            "Applied to recommended job (yes/no)",
            "Clicked on suggestion (yes/no)",
            "Dismissed recommendation (yes/no)",
            "Star rating on coaching response",
            "Blocker marked as resolved",
            "Improvement plan progress",
        ],
        legal_basis="legitimate_interest",
        retention_days=730,  # 2 years — critical for model training
        storage="PostgreSQL: interactions + blocker tables",
        feeds_ai=True,
        ai_target="job_matching",
        gdpr_exportable=True,
        gdpr_deletable=True,
    ),

    DataCategory(
        name="Payment Data",
        description="Transaction and subscription records (card details held by Braintree, not us)",
        data_points=[
            "Plan selected",
            "Amount charged",
            "Transaction ID (Braintree)",
            "Subscription status",
            "Billing dates",
            "Promo codes used",
            "Refund history",
        ],
        legal_basis="contract",
        retention_days=2555,  # 7 years — UK tax/accounting requirement
        storage="PostgreSQL: subscriptions + payment_transactions",
        feeds_ai=False,
        ai_target=None,
        gdpr_exportable=True,
        gdpr_deletable=False,  # Cannot delete — legal/tax requirement. Anonymised instead.
    ),

    DataCategory(
        name="Consent Records",
        description="GDPR consent audit trail — immutable",
        data_points=[
            "Consent type (terms, marketing, data_processing, cookies)",
            "Granted / revoked",
            "Timestamp",
            "IP address",
            "Policy version consented to",
        ],
        legal_basis="legal_obligation",
        retention_days=2555,  # 7 years
        storage="PostgreSQL: consent_records",
        feeds_ai=False,
        ai_target=None,
        gdpr_exportable=True,
        gdpr_deletable=False,  # Must retain for compliance proof
    ),
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_retention_summary() -> dict:
    """Return a summary suitable for a privacy policy or admin dashboard."""
    return {
        cat.name: {
            "retention": f"{cat.retention_days} days" if cat.retention_days > 0 else "Until account deletion",
            "legal_basis": cat.legal_basis,
            "feeds_ai": cat.feeds_ai,
            "deletable": cat.gdpr_deletable,
        }
        for cat in DATA_CAPTURE_POLICY
    }


def get_ai_pipeline_sources() -> dict:
    """Return which data categories feed each AI pipeline target."""
    targets: dict = {}
    for cat in DATA_CAPTURE_POLICY:
        if cat.feeds_ai and cat.ai_target:
            if cat.ai_target not in targets:
                targets[cat.ai_target] = []
            targets[cat.ai_target].append(cat.name)
    return targets


def get_gdpr_article30_records() -> list:
    """Generate GDPR Article 30 processing records from the policy."""
    return [
        {
            "processing_activity": cat.name,
            "purpose": cat.description,
            "data_subjects": "Registered users of CareerTrojan",
            "categories_of_data": cat.data_points,
            "legal_basis": cat.legal_basis,
            "retention_period": f"{cat.retention_days} days" if cat.retention_days > 0 else "Until account deletion",
            "storage_location": cat.storage,
            "shared_with_third_parties": "Braintree (payment processing only)" if "payment" in cat.name.lower() else "None",
            "transfer_outside_uk": "No",
        }
        for cat in DATA_CAPTURE_POLICY
    ]
