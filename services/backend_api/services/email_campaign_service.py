"""
Email Campaign Service — SendGrid + Klaviyo + Resend integration.

Provides a unified interface for:
  • Transactional email (SendGrid or Resend)
  • Campaign / bulk email (SendGrid Marketing or Klaviyo)
  • Contact list management  — backed by ContactsDB (30k+ extracted emails)
  • Email intelligence        — pattern guessing for corporate contacts
  • Analytics & logs

All API keys are read from env vars defined in .env.
Contact data persists to L:\\…\\contacts_database.json via ContactsDB.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
import hmac
import base64
from urllib.parse import urlencode

logger = logging.getLogger("email_campaign_service")


# ── Configuration ─────────────────────────────────────────────────────────

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@careertrojan.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "CareerTrojan")

KLAVIYO_API_KEY = os.getenv("KLAVIYO_API_KEY", "")

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "noreply@careertrojan.com")

# Unsubscribe configuration (CAN-SPAM / GDPR compliance)
UNSUBSCRIBE_BASE_URL = os.getenv("UNSUBSCRIBE_BASE_URL", "https://careertrojan.com/api/email/unsubscribe")
UNSUBSCRIBE_SECRET = os.getenv("UNSUBSCRIBE_SECRET", "change-me-in-production-abc123")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "CareerTrojan Ltd, 123 Business St, London EC1A 1BB")


# ── Persistent stores — backed by ContactsDB + EmailIntelligence ──────────

_contacts_db = None          # Lazy-initialised ContactsDB singleton
_email_intelligence = None   # Lazy-initialised EmailIntelligence singleton
_campaigns: Dict[str, Dict[str, Any]] = {}       # id → campaign dict (in-memory)
_email_logs: List[Dict[str, Any]] = []            # send log entries (in-memory)


def _get_contacts_db():
    """Return the singleton ContactsDB instance (lazy-loaded)."""
    global _contacts_db
    if _contacts_db is None:
        try:
            from services.ai_engine.contacts_db import ContactsDB
            _contacts_db = ContactsDB()
            logger.info(
                "ContactsDB loaded: %d contacts from %s",
                len(_contacts_db.contacts), _contacts_db.db_path,
            )
        except Exception as exc:
            logger.error("Failed to load ContactsDB: %s", exc)
            # Fallback: create a minimal in-memory stub
            from services.ai_engine.contacts_db import ContactsDB
            _contacts_db = ContactsDB.__new__(ContactsDB)
            _contacts_db.contacts = {}
            _contacts_db._email_index = {}
    return _contacts_db


def _get_email_intelligence():
    """Return the singleton EmailIntelligence instance (lazy-loaded)."""
    global _email_intelligence
    if _email_intelligence is None:
        try:
            from services.ai_engine.email_intelligence import EmailIntelligence
            _email_intelligence = EmailIntelligence()
            _email_intelligence.load_verified_emails()
            _email_intelligence.learn_patterns()
            logger.info(
                "EmailIntelligence loaded: %d verified contacts, %d corporate domains",
                len(_email_intelligence.verified_contacts),
                len(_email_intelligence.domain_patterns),
            )
        except Exception as exc:
            logger.error("Failed to load EmailIntelligence: %s", exc)
            _email_intelligence = None
    return _email_intelligence


# (removed broken module-level property — use _get_contacts_db() directly)


# ── Lazy SDK imports (fail gracefully if not installed) ────────────────────

def _get_sendgrid_client():
    """Return a configured SendGrid API client, or None."""
    if not SENDGRID_API_KEY:
        return None
    try:
        from sendgrid import SendGridAPIClient
        return SendGridAPIClient(api_key=SENDGRID_API_KEY)
    except ImportError:
        logger.warning("sendgrid package not installed — pip install sendgrid")
        return None


def _get_klaviyo_client():
    """Return a configured Klaviyo API client, or None."""
    if not KLAVIYO_API_KEY:
        return None
    try:
        import klaviyo_api
        return klaviyo_api.KlaviyoAPI(KLAVIYO_API_KEY)
    except ImportError:
        logger.warning("klaviyo-api package not installed — pip install klaviyo-api")
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  Unsubscribe Handling (CAN-SPAM / GDPR Compliance)
# ═══════════════════════════════════════════════════════════════════════════

def _generate_unsubscribe_token(email: str) -> str:
    """Generate a secure HMAC token for unsubscribe verification.

    This ensures only the recipient can unsubscribe their own email.
    """
    message = email.lower().encode("utf-8")
    signature = hmac.new(
        UNSUBSCRIBE_SECRET.encode("utf-8"),
        message,
        hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8")[:32]


def _verify_unsubscribe_token(email: str, token: str) -> bool:
    """Verify an unsubscribe token is valid for the given email."""
    expected = _generate_unsubscribe_token(email)
    return hmac.compare_digest(expected, token)


def generate_unsubscribe_link(email: str, campaign_id: str = "") -> str:
    """Generate a one-click unsubscribe link for an email address.

    Parameters
    ----------
    email : str
        The recipient's email address.
    campaign_id : str
        Optional campaign ID for tracking.

    Returns
    -------
    str
        Full unsubscribe URL with secure token.
    """
    token = _generate_unsubscribe_token(email)
    params = {
        "email": email,
        "token": token,
    }
    if campaign_id:
        params["campaign"] = campaign_id
    return f"{UNSUBSCRIBE_BASE_URL}?{urlencode(params)}"


def _inject_unsubscribe_footer(
    html_content: str,
    email: str,
    campaign_id: str = "",
) -> str:
    """Inject unsubscribe footer into HTML email content.

    This is REQUIRED for CAN-SPAM and GDPR compliance.
    """
    unsub_link = generate_unsubscribe_link(email, campaign_id)

    footer = f'''
    <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; text-align: center;">
        <p style="margin: 5px 0;">
            You received this email because you are in our professional network.
        </p>
        <p style="margin: 5px 0;">
            <a href="{unsub_link}" style="color: #666; text-decoration: underline;">Unsubscribe</a>
            &nbsp;|&nbsp;
            <a href="{UNSUBSCRIBE_BASE_URL.replace('/unsubscribe', '/preferences')}?email={email}" style="color: #666; text-decoration: underline;">Email Preferences</a>
        </p>
        <p style="margin: 10px 0; font-size: 11px; color: #999;">
            {COMPANY_ADDRESS}
        </p>
    </div>
    '''

    # Insert before </body> if present, otherwise append
    if "</body>" in html_content.lower():
        import re
        return re.sub(
            r"(</body>)",
            footer + r"\\1",
            html_content,
            flags=re.IGNORECASE
        )
    else:
        return html_content + footer


def _inject_text_unsubscribe_footer(
    text_content: str,
    email: str,
    campaign_id: str = "",
) -> str:
    """Inject unsubscribe footer into plain text email content."""
    unsub_link = generate_unsubscribe_link(email, campaign_id)

    footer = f'''

---
To unsubscribe from these emails, visit: {unsub_link}

{COMPANY_ADDRESS}
'''
    return text_content + footer


def process_unsubscribe(email: str, token: str, campaign_id: str = "") -> Dict[str, Any]:
    """Process an unsubscribe request.

    Verifies the token and updates the contact record.

    Parameters
    ----------
    email : str
        Email address to unsubscribe.
    token : str
        Security token from unsubscribe link.
    campaign_id : str
        Optional campaign ID for tracking.

    Returns
    -------
    dict
        {"success": bool, "message": str}
    """
    # Verify token
    if not _verify_unsubscribe_token(email, token):
        logger.warning("Invalid unsubscribe token for %s", email)
        return {"success": False, "message": "Invalid or expired unsubscribe link"}

    # Update contact in database
    db = _get_contacts_db()
    if db:
        contact = db.get_by_email(email)
        if contact:
            contact_id = contact["id"]
            # Add unsubscribed tag and update status
            contact["tags"] = list(set(contact.get("tags", [])) | {"unsubscribed"})
            contact["conversion_status"] = "unsubscribed"
            contact["unsubscribed_at"] = datetime.utcnow().isoformat()
            if campaign_id:
                contact["unsubscribe_campaign"] = campaign_id

            # Reclassify (will drop to Tier C)
            tier, reason = db.classify_trust_tier(contact)
            contact["trust_tier"] = tier
            contact["tier_reason"] = reason
            contact["updated_at"] = db._now()
            db.save()

            logger.info("Unsubscribed contact %s (%s)", contact_id, email)
            return {
                "success": True,
                "message": "You have been successfully unsubscribed.",
                "contact_id": contact_id,
            }

    # Email not in database, but still honor the request
    logger.info("Unsubscribe request for unknown email: %s", email)
    return {
        "success": True,
        "message": "You have been successfully unsubscribed.",
    }


def get_suppressed_emails() -> List[str]:
    """Get list of all suppressed/unsubscribed emails.

    These should NEVER receive marketing emails.
    """
    db = _get_contacts_db()
    if not db:
        return []

    suppressed = []
    for contact in db.contacts.values():
        tags = set(contact.get("tags", []))
        if tags & {"unsubscribed", "spam_complaint", "bounced"}:
            suppressed.append(contact.get("email", "").lower())

    return suppressed


def is_email_suppressed(email: str) -> bool:
    """Check if an email is on the suppression list."""
    return email.lower() in get_suppressed_emails()


# ═══════════════════════════════════════════════════════════════════════════
#  Integration Management
# ═══════════════════════════════════════════════════════════════════════════

def get_integrations_status() -> Dict[str, Any]:
    """Return connectivity status of all email providers."""
    result: Dict[str, Any] = {}

    # SendGrid
    sg = _get_sendgrid_client()
    if sg:
        try:
            resp = sg.client.api_keys.get()
            result["sendgrid"] = {
                "connected": resp.status_code == 200,
                "from_email": SENDGRID_FROM_EMAIL,
                "from_name": SENDGRID_FROM_NAME,
            }
        except Exception as exc:
            result["sendgrid"] = {"connected": False, "error": str(exc)}
    else:
        result["sendgrid"] = {"connected": False, "error": "No API key or SDK missing"}

    # Klaviyo
    kl = _get_klaviyo_client()
    if kl:
        try:
            # Simple ping: list 1 flow to verify the key
            kl.Flows.get_flows(page_size=1)
            result["klaviyo"] = {"connected": True}
        except Exception as exc:
            result["klaviyo"] = {"connected": False, "error": str(exc)}
    else:
        result["klaviyo"] = {"connected": False, "error": "No API key or SDK missing"}

    # Resend
    if RESEND_API_KEY:
        result["resend"] = {"connected": True, "from_email": RESEND_FROM_EMAIL}
    else:
        result["resend"] = {"connected": False, "error": "No API key"}

    return result


def configure_provider(provider: str, api_key: str) -> Dict[str, Any]:
    """Update a provider API key at runtime (does NOT persist to .env)."""
    global SENDGRID_API_KEY, KLAVIYO_API_KEY, RESEND_API_KEY

    provider = provider.lower()
    if provider == "sendgrid":
        SENDGRID_API_KEY = api_key
        os.environ["SENDGRID_API_KEY"] = api_key
    elif provider == "klaviyo":
        KLAVIYO_API_KEY = api_key
        os.environ["KLAVIYO_API_KEY"] = api_key
    elif provider == "resend":
        RESEND_API_KEY = api_key
        os.environ["RESEND_API_KEY"] = api_key
    else:
        return {"success": False, "error": f"Unknown provider: {provider}"}

    return {"success": True, "provider": provider, "message": "API key updated (runtime only)"}


def disconnect_provider(provider: str) -> Dict[str, Any]:
    """Clear a provider's API key."""
    return configure_provider(provider, "")


# ═══════════════════════════════════════════════════════════════════════════
#  Contact Management — backed by ContactsDB (persistent JSON store)
# ═══════════════════════════════════════════════════════════════════════════

def get_contacts_count() -> int:
    """Total contact count for backward-compat (router uses len(ecs._contacts))."""
    db = _get_contacts_db()
    return len(db.contacts) if db else 0


def get_contacts(
    page: int = 1,
    per_page: int = 50,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    company: Optional[str] = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    """Paginated, filterable contact listing from ContactsDB."""
    db = _get_contacts_db()
    return db.list_all(
        source_type=source_type,
        page=page,
        per_page=per_page,
        search=search,
        company=company,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


def create_contact(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _get_contacts_db()
    email = payload.get("email", "")
    source_type = payload.get("source_type", "verified")
    if source_type == "guessed":
        return db.add_guessed(
            email=email,
            first_name=payload.get("first_name", ""),
            last_name=payload.get("last_name", ""),
            company=payload.get("company", ""),
            domain=payload.get("domain", ""),
            pattern=payload.get("pattern_used", "unknown"),
            confidence=float(payload.get("confidence", 0.0)),
            source=payload.get("source_detail", "manual_entry"),
        )
    return db.add_verified(
        email=email,
        first_name=payload.get("first_name", ""),
        last_name=payload.get("last_name", ""),
        company=payload.get("company", ""),
        domain=payload.get("domain", ""),
        title=payload.get("title", ""),
        source=payload.get("source_detail", "manual_entry"),
        tags=payload.get("tags"),
    )


def update_contact(contact_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    db = _get_contacts_db()
    result = db.update(contact_id, **{k: v for k, v in payload.items() if k != "id"})
    if result is None:
        raise KeyError(f"Contact {contact_id} not found")
    return result


def delete_contact(contact_id: str) -> Dict[str, Any]:
    db = _get_contacts_db()
    rec = db.get(contact_id)
    if rec is None:
        raise KeyError(f"Contact {contact_id} not found")
    db.delete(contact_id)
    return {"deleted": True, "contact": rec}


def import_contacts_csv(csv_text: str) -> Dict[str, Any]:
    """Import contacts from CSV text (email, first_name, last_name, tags)."""
    import csv
    import io

    db = _get_contacts_db()
    reader = csv.DictReader(io.StringIO(csv_text))
    imported = 0
    skipped = 0
    for row in reader:
        email = row.get("email", "").strip()
        if not email or "@" not in email:
            skipped += 1
            continue
        # Dedup by email
        if db.get_by_email(email):
            skipped += 1
            continue
        db.add_verified(
            email=email,
            first_name=row.get("first_name", ""),
            last_name=row.get("last_name", ""),
            company=row.get("company", ""),
            source="csv_import",
            tags=[t.strip() for t in row.get("tags", "").split(",") if t.strip()],
        )
        imported += 1

    return {"imported": imported, "skipped": skipped, "total_contacts": len(db.contacts)}


def export_contacts_csv() -> str:
    """Export all contacts as CSV string."""
    import csv
    import io

    db = _get_contacts_db()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "first_name", "last_name", "company", "domain",
                      "source_type", "confidence", "tags", "created_at"])
    for c in db.contacts.values():
        writer.writerow([
            c["id"], c["email"], c.get("first_name", ""),
            c.get("last_name", ""), c.get("company", ""),
            c.get("domain", ""), c.get("source_type", ""),
            c.get("confidence", ""),
            ",".join(c.get("tags", [])),
            c.get("created_at", ""),
        ])
    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
#  Campaign Management
# ═══════════════════════════════════════════════════════════════════════════

def get_campaigns() -> List[Dict[str, Any]]:
    return list(_campaigns.values())


def create_campaign(payload: Dict[str, Any]) -> Dict[str, Any]:
    campaign_id = str(uuid.uuid4())[:8]
    campaign = {
        "id": campaign_id,
        "name": payload.get("name", "Untitled Campaign"),
        "subject": payload.get("subject", ""),
        "body_html": payload.get("body_html", ""),
        "body_text": payload.get("body_text", ""),
        "provider": payload.get("provider", "sendgrid"),
        "recipients": payload.get("recipients", []),  # email list or tag filter
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
    }
    _campaigns[campaign_id] = campaign
    return campaign


def get_campaign(campaign_id: str) -> Dict[str, Any]:
    if campaign_id not in _campaigns:
        raise KeyError(f"Campaign {campaign_id} not found")
    return _campaigns[campaign_id]


def send_campaign(
    campaign_id: str,
    tier: str = "A",
    allow_lower_tiers: bool = False,
) -> Dict[str, Any]:
    """Send a campaign via its configured provider.

    Parameters
    ----------
    campaign_id : str
        The campaign ID to send.
    tier : str
        Minimum trust tier required: 'A' (default), 'B', or 'C'.
        Defaults to 'A' to ensure only high-trust contacts receive campaigns.
    allow_lower_tiers : bool
        If True, include lower tiers (e.g., tier='B' includes A and B).
        If False (default), only exact tier match.

    Returns
    -------
    dict
        {"success": bool, "sent": int, "failed": int, "filtered_out": int}
    """
    if campaign_id not in _campaigns:
        raise KeyError(f"Campaign {campaign_id} not found")

    campaign = _campaigns[campaign_id]
    provider = campaign.get("provider", "sendgrid")
    explicit_recipients = campaign.get("recipients", [])

    # Determine recipients based on trust tier
    db = _get_contacts_db()
    filtered_out = 0

    if explicit_recipients:
        # Filter explicit recipients by tier
        valid_recipients = []
        if db:
            for email in explicit_recipients:
                contact = db.get_by_email(email)
                if contact:
                    contact_tier = contact.get("trust_tier", "unclassified")
                    if _tier_allowed(contact_tier, tier, allow_lower_tiers):
                        valid_recipients.append(email)
                    else:
                        filtered_out += 1
                        logger.debug(
                            "Filtered out %s (tier %s, required %s)",
                            email, contact_tier, tier
                        )
                else:
                    # Unknown contact — skip for safety
                    filtered_out += 1
        else:
            valid_recipients = explicit_recipients
        recipients = valid_recipients
    else:
        # Get contacts by tier from ContactsDB
        if db:
            if allow_lower_tiers:
                # Collect all allowed tiers
                allowed_tiers = _get_allowed_tiers(tier)
                tier_contacts = []
                for t in allowed_tiers:
                    tier_contacts.extend(db.get_contacts_by_tier(t, exclude_bounced=True))
            else:
                tier_contacts = db.get_contacts_by_tier(tier, exclude_bounced=True)
            recipients = [c["email"] for c in tier_contacts]
            # Count filtered out (all contacts minus tier-allowed)
            total_contacts = len(db.contacts)
            filtered_out = total_contacts - len(recipients)
        else:
            recipients = []

    if not recipients:
        return {
            "success": False,
            "error": f"No recipients in tier {tier}",
            "filtered_out": filtered_out,
        }

    logger.info(
        "Sending campaign %s to %d recipients (tier=%s, filtered_out=%d)",
        campaign_id, len(recipients), tier, filtered_out
    )

    # Send via chosen provider
    results = []
    for email in recipients:
        result = _send_single_email(
            to_email=email,
            subject=campaign["subject"],
            html_content=campaign["body_html"],
            text_content=campaign["body_text"],
            provider=provider,
        )
        results.append(result)

    campaign["status"] = "sent"
    campaign["sent_at"] = datetime.utcnow().isoformat()
    campaign["send_count"] = len(results)
    campaign["tier_filter"] = tier

    return {
        "success": True,
        "campaign_id": campaign_id,
        "sent": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "filtered_out": filtered_out,
        "tier": tier,
    }


def _tier_allowed(contact_tier: str, required_tier: str, allow_lower: bool) -> bool:
    """Check if a contact's tier meets the required tier."""
    tier_order = {"A": 1, "B": 2, "C": 3, "unclassified": 4}
    contact_rank = tier_order.get(contact_tier, 4)
    required_rank = tier_order.get(required_tier, 1)

    if allow_lower:
        # Contact tier must be equal or better (lower rank number)
        return contact_rank <= required_rank
    else:
        # Exact match only
        return contact_tier == required_tier


def _get_allowed_tiers(min_tier: str) -> List[str]:
    """Get list of allowed tiers based on minimum tier."""
    tier_order = ["A", "B", "C"]
    try:
        idx = tier_order.index(min_tier)
        return tier_order[:idx + 1]
    except ValueError:
        return ["A"]  # Default to Tier A only


# ═══════════════════════════════════════════════════════════════════════════
#  Single Email Sending
# ═══════════════════════════════════════════════════════════════════════════

def send_test_email(to_email: str, subject: str = "Test from CareerTrojan",
                    body: str = "<h1>Test</h1><p>This is a test email.</p>",
                    provider: str = "sendgrid") -> Dict[str, Any]:
    return _send_single_email(to_email, subject, body, body, provider)


def send_bulk_email(
    recipients: List[str],
    subject: str,
    html_content: str,
    text_content: str = "",
    provider: str = "sendgrid",
    tier: str = "A",
    enforce_tier: bool = True,
) -> Dict[str, Any]:
    """Send bulk email with trust tier filtering.

    Parameters
    ----------
    recipients : list[str]
        List of email addresses.
    tier : str
        Minimum trust tier required ('A', 'B', 'C'). Default 'A'.
    enforce_tier : bool
        If True (default), filter recipients by tier.
        If False, send to all recipients regardless of tier.
    """
    db = _get_contacts_db()
    filtered_out = 0

    if enforce_tier and db:
        valid_recipients = []
        for email in recipients:
            contact = db.get_by_email(email)
            if contact:
                contact_tier = contact.get("trust_tier", "unclassified")
                if _tier_allowed(contact_tier, tier, allow_lower=True):
                    valid_recipients.append(email)
                else:
                    filtered_out += 1
                    logger.debug("Filtered out %s (tier %s)", email, contact_tier)
            else:
                # Unknown contact — skip for safety in tier-enforced mode
                filtered_out += 1
        recipients = valid_recipients

    results = []
    for email in recipients:
        r = _send_single_email(email, subject, html_content, text_content, provider)
        results.append(r)

    return {
        "total": len(results),
        "sent": len([r for r in results if r.get("success")]),
        "failed": len([r for r in results if not r.get("success")]),
        "filtered_out": filtered_out,
        "tier": tier if enforce_tier else "none",
    }


def get_tier_statistics() -> Dict[str, Any]:
    """Get trust tier statistics from ContactsDB."""
    db = _get_contacts_db()
    if not db:
        return {"error": "ContactsDB not available"}

    # Ensure contacts are classified
    stats = db.get_tier_stats()
    return {
        "tier_counts": stats["tier_counts"],
        "tier_percentages": stats["tier_percentages"],
        "role_accounts": stats["role_accounts"],
        "suspicious_domains": stats["suspicious_domains"],
        "total_contacts": stats["total_contacts"],
        "campaign_ready": stats["tier_counts"].get("A", 0),  # Tier A = safe to send
    }


def _send_single_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = "",
    provider: str = "sendgrid",
    campaign_id: str = "",
    is_marketing: bool = True,
) -> Dict[str, Any]:
    """Route a single email through the chosen provider.

    Parameters
    ----------
    to_email : str
        Recipient email address.
    subject : str
        Email subject.
    html_content : str
        HTML body content.
    text_content : str
        Plain text body content.
    provider : str
        "sendgrid", "klaviyo", or "resend".
    campaign_id : str
        Campaign ID for tracking.
    is_marketing : bool
        If True (default), adds unsubscribe footer and checks suppression list.
        Set False for transactional emails (password reset, etc.).
    """
    log_entry = {
        "id": str(uuid.uuid4())[:8],
        "to": to_email,
        "subject": subject,
        "provider": provider,
        "timestamp": datetime.utcnow().isoformat(),
        "campaign_id": campaign_id,
    }

    # Check suppression list for marketing emails
    if is_marketing and is_email_suppressed(to_email):
        logger.info("Blocked send to suppressed email: %s", to_email)
        log_entry["success"] = False
        log_entry["error"] = "Email is on suppression list (unsubscribed/bounced)"
        log_entry["suppressed"] = True
        _email_logs.append(log_entry)
        return log_entry

    # Inject unsubscribe footer for marketing emails
    if is_marketing:
        html_content = _inject_unsubscribe_footer(html_content, to_email, campaign_id)
        if text_content:
            text_content = _inject_text_unsubscribe_footer(text_content, to_email, campaign_id)

    try:
        if provider == "sendgrid":
            result = _send_via_sendgrid(
                to_email, subject, html_content, text_content,
                campaign_id=campaign_id, is_marketing=is_marketing
            )
        elif provider == "klaviyo":
            result = _send_via_klaviyo(to_email, subject, html_content)
        elif provider == "resend":
            result = _send_via_resend(
                to_email, subject, html_content,
                campaign_id=campaign_id, is_marketing=is_marketing
            )
        else:
            result = {"success": False, "error": f"Unknown provider: {provider}"}

        log_entry.update(result)
    except Exception as exc:
        log_entry["success"] = False
        log_entry["error"] = str(exc)
        result = log_entry

    _email_logs.append(log_entry)
    return result


def _send_via_sendgrid(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = "",
    campaign_id: str = "",
    is_marketing: bool = True,
) -> Dict[str, Any]:
    """Send via SendGrid with List-Unsubscribe header for compliance."""
    sg = _get_sendgrid_client()
    if not sg:
        return {"success": False, "error": "SendGrid not configured"}

    from sendgrid.helpers.mail import Mail, Email, To, Content, Header

    message = Mail(
        from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
        to_emails=To(to_email),
        subject=subject,
        html_content=Content("text/html", html_content),
    )
    if text_content:
        message.add_content(Content("text/plain", text_content))

    # Add List-Unsubscribe header for marketing emails (RFC 2369)
    # This enables one-click unsubscribe in email clients like Gmail
    if is_marketing:
        unsub_link = generate_unsubscribe_link(to_email, campaign_id)
        # List-Unsubscribe header format: <mailto:...>, <https://...>
        message.header = Header("List-Unsubscribe", f"<{unsub_link}>")
        message.header = Header("List-Unsubscribe-Post", "List-Unsubscribe=One-Click")

    response = sg.send(message)
    return {
        "success": response.status_code in (200, 201, 202),
        "status_code": response.status_code,
        "provider": "sendgrid",
    }


def _send_via_klaviyo(to_email: str, subject: str, html_content: str) -> Dict[str, Any]:
    """Klaviyo is primarily a marketing platform — we use their transactional email API."""
    if not KLAVIYO_API_KEY:
        return {"success": False, "error": "Klaviyo not configured"}

    try:
        import requests
        # Klaviyo transactional email endpoint
        resp = requests.post(
            "https://a.klaviyo.com/api/v1/email-template/send",
            data={
                "api_key": KLAVIYO_API_KEY,
                "to_email": to_email,
                "subject": subject,
                "html": html_content,
                "from_email": SENDGRID_FROM_EMAIL,
                "from_name": SENDGRID_FROM_NAME,
            },
            timeout=30,
        )
        return {
            "success": resp.status_code in (200, 201, 202),
            "status_code": resp.status_code,
            "provider": "klaviyo",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc), "provider": "klaviyo"}


def _send_via_resend(
    to_email: str,
    subject: str,
    html_content: str,
    campaign_id: str = "",
    is_marketing: bool = True,
) -> Dict[str, Any]:
    """Send via Resend.com API with List-Unsubscribe header for compliance."""
    if not RESEND_API_KEY:
        return {"success": False, "error": "Resend not configured"}

    try:
        import requests
        
        payload = {
            "from": f"{SENDGRID_FROM_NAME} <{RESEND_FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }
        
        # Add List-Unsubscribe headers for marketing emails
        if is_marketing:
            unsub_link = generate_unsubscribe_link(to_email, campaign_id)
            payload["headers"] = {
                "List-Unsubscribe": f"<{unsub_link}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            }
        
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        return {
            "success": resp.status_code in (200, 201),
            "status_code": resp.status_code,
            "provider": "resend",
        }
    except Exception as exc:
        return {"success": False, "error": str(exc), "provider": "resend"}


# ═══════════════════════════════════════════════════════════════════════════
#  Logs & Analytics
# ═══════════════════════════════════════════════════════════════════════════

def get_email_logs(days: int = 30) -> List[Dict[str, Any]]:
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    return [e for e in _email_logs if e.get("timestamp", "") >= cutoff]


def get_email_analytics(days: int = 30) -> Dict[str, Any]:
    """Comprehensive analytics from ContactsDB + in-memory send logs."""
    db = _get_contacts_db()
    # Real analytics from the persistent database
    analytics = db.get_analytics()

    # Supplement with recent send log stats
    logs = get_email_logs(days)
    sent = sum(1 for e in logs if e.get("success"))
    failed = sum(1 for e in logs if not e.get("success"))
    by_provider: Dict[str, int] = {}
    for e in logs:
        p = e.get("provider", "unknown")
        by_provider[p] = by_provider.get(p, 0) + 1

    analytics.update({
        "period_days": days,
        "campaign_sends": sent,
        "campaign_failures": failed,
        "by_provider": by_provider,
        "total_campaigns": len(_campaigns),
    })
    return analytics


# ═══════════════════════════════════════════════════════════════════════════
#  Email Intelligence — pattern guessing & domain analysis
# ═══════════════════════════════════════════════════════════════════════════

def guess_email(
    first_name: str,
    last_name: str,
    company: str,
    domain: Optional[str] = None,
) -> Dict[str, Any]:
    """Use EmailIntelligence to generate email guesses for a contact."""
    engine = _get_email_intelligence()
    if engine is None:
        return {"success": False, "error": "Email intelligence engine unavailable", "guesses": []}

    guesses = engine.guess_email(
        first_name=first_name,
        last_name=last_name,
        company=company,
        domain=domain,
    )
    return {
        "success": True,
        "first_name": first_name,
        "last_name": last_name,
        "company": company,
        "guesses": guesses,
    }


def guess_batch(contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Batch guess emails for multiple contacts."""
    engine = _get_email_intelligence()
    if engine is None:
        return {"success": False, "error": "Email intelligence engine unavailable", "results": []}

    results = engine.guess_batch(contacts)
    return {"success": True, "results": results, "total": len(results)}


def get_domain_stats() -> Dict[str, Any]:
    """Get domain pattern statistics from EmailIntelligence."""
    engine = _get_email_intelligence()
    if engine is None:
        return {"success": False, "error": "Email intelligence engine unavailable"}

    stats = engine.get_domain_stats()
    stats["success"] = True
    return stats


def import_from_intelligence() -> Dict[str, Any]:
    """Import verified contacts from EmailIntelligence into ContactsDB."""
    engine = _get_email_intelligence()
    if engine is None:
        return {"success": False, "error": "Email intelligence engine unavailable"}

    db = _get_contacts_db()
    result = db.import_from_intelligence(engine)
    result["success"] = True
    result["total_contacts_after"] = len(db.contacts)
    return result


def get_bounced_contacts(bounce_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all bounced contacts."""
    db = _get_contacts_db()
    return db.get_bounced(bounce_type=bounce_type)


def suggest_reattempt(contact_id: str) -> Dict[str, Any]:
    """Suggest alternative email patterns for a bounced contact."""
    db = _get_contacts_db()
    suggestions = db.suggest_reattempt(contact_id)
    return {
        "contact_id": contact_id,
        "suggestions": suggestions,
        "count": len(suggestions),
    }


def get_contact_analytics() -> Dict[str, Any]:
    """Get pure contact database analytics (no campaign data)."""
    db = _get_contacts_db()
    return db.get_analytics()


def search_contacts(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Full-text search across contacts."""
    db = _get_contacts_db()
    return db.search(query, limit=limit)
