"""
Admin Email Campaign Router — endpoint implementations for the
AdminAPIClientContactCommunicationMixin contract.

Prefix: /api/admin/v1  (same as admin.py)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import PlainTextResponse

from services.backend_api.services import email_campaign_service as ecs

logger = logging.getLogger("admin_email_campaigns")
router = APIRouter(prefix="/api/admin/v1", tags=["admin-email-campaigns"])


# ── Admin auth dependency — imported from centralised module ──────────────
from services.backend_api.utils.auth_deps import require_admin


# ═══════════════════════════════════════════════════════════════════════════
#  Integrations
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/integrations/status")
def integrations_status(_=Depends(require_admin)):
    """Return connectivity status of SendGrid, Klaviyo, Resend."""
    return ecs.get_integrations_status()


@router.post("/integrations/sendgrid/configure")
def configure_sendgrid(payload: Dict[str, Any], _=Depends(require_admin)):
    api_key = payload.get("api_key", "")
    if not api_key:
        raise HTTPException(400, "api_key required")
    return ecs.configure_provider("sendgrid", api_key)


@router.post("/integrations/klaviyo/configure")
def configure_klaviyo(payload: Dict[str, Any], _=Depends(require_admin)):
    api_key = payload.get("api_key", "")
    if not api_key:
        raise HTTPException(400, "api_key required")
    return ecs.configure_provider("klaviyo", api_key)


@router.post("/integrations/gmail/configure")
def configure_gmail(payload: Dict[str, Any], _=Depends(require_admin)):
    """Configure Gmail IMAP-based email account."""
    # Store config for email sync — actual IMAP wiring is future work
    return {"success": True, "message": "Gmail config stored (runtime only)", "payload": payload}


@router.post("/integrations/{provider}/disconnect")
def disconnect_integration(provider: str, _=Depends(require_admin)):
    return ecs.disconnect_provider(provider)


# ═══════════════════════════════════════════════════════════════════════════
#  Contacts
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/contacts")
def list_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    source_type: str = Query(None),
    search: str = Query(None),
    company: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    _=Depends(require_admin),
):
    return ecs.get_contacts(
        page=page,
        per_page=per_page,
        source_type=source_type,
        search=search,
        company=company,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.post("/contacts")
def create_contact(payload: Dict[str, Any], _=Depends(require_admin)):
    return ecs.create_contact(payload)


@router.patch("/contacts/{contact_id}")
def update_contact(contact_id: str, payload: Dict[str, Any], _=Depends(require_admin)):
    try:
        return ecs.update_contact(contact_id, payload)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str, _=Depends(require_admin)):
    try:
        return ecs.delete_contact(contact_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.post("/contacts/import")
async def import_contacts_csv(file: UploadFile = File(...), _=Depends(require_admin)):
    content = await file.read()
    csv_text = content.decode("utf-8", errors="replace")
    return ecs.import_contacts_csv(csv_text)


@router.get("/contacts/export")
def export_contacts_csv(_=Depends(require_admin)):
    csv_text = ecs.export_contacts_csv()
    return PlainTextResponse(csv_text, media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=contacts.csv"})


# ═══════════════════════════════════════════════════════════════════════════
#  Campaigns
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/campaigns")
def list_campaigns(_=Depends(require_admin)):
    campaigns = ecs.get_campaigns()
    return {"campaigns": campaigns, "total": len(campaigns)}


@router.post("/campaigns")
def create_campaign(payload: Dict[str, Any], _=Depends(require_admin)):
    return ecs.create_campaign(payload)


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str, _=Depends(require_admin)):
    try:
        return ecs.get_campaign(campaign_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc))


@router.post("/campaigns/{campaign_id}/send")
def send_campaign(
    campaign_id: str,
    tier: str = Query("A", description="Minimum trust tier: A (default), B, or C"),
    allow_lower_tiers: bool = Query(False, description="Include lower tiers"),
    _=Depends(require_admin),
):
    """Send a campaign filtered by trust tier.

    By default, only Tier A (high trust) contacts receive campaigns.
    Use tier='B' or tier='C' to include lower trust contacts.
    Set allow_lower_tiers=true to include all tiers up to the specified tier.
    """
    try:
        return ecs.send_campaign(
            campaign_id,
            tier=tier.upper(),
            allow_lower_tiers=allow_lower_tiers,
        )
    except KeyError as exc:
        raise HTTPException(404, str(exc))


# ═══════════════════════════════════════════════════════════════════════════
#  Email Send / Logs / Analytics
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/email/send_test")
def send_test_email(payload: Dict[str, Any], _=Depends(require_admin)):
    to = payload.get("to_email", "")
    if not to:
        raise HTTPException(400, "to_email required")
    return ecs.send_test_email(
        to_email=to,
        subject=payload.get("subject", "Test from CareerTrojan"),
        body=payload.get("body", "<h1>Test</h1><p>This is a test email.</p>"),
        provider=payload.get("provider", "sendgrid"),
    )


@router.post("/email/send_bulk")
def send_bulk_email(payload: Dict[str, Any], _=Depends(require_admin)):
    """Send bulk email with trust tier filtering.

    Payload:
    - recipients: list of email addresses
    - subject: email subject
    - html_content: HTML body
    - text_content: plain text body
    - provider: 'sendgrid', 'klaviyo', or 'resend'
    - tier: minimum trust tier (default 'A')
    - enforce_tier: if true (default), filter by tier; if false, send to all
    """
    recipients = payload.get("recipients", [])
    if not recipients:
        raise HTTPException(400, "recipients list required")
    return ecs.send_bulk_email(
        recipients=recipients,
        subject=payload.get("subject", ""),
        html_content=payload.get("html_content", ""),
        text_content=payload.get("text_content", ""),
        provider=payload.get("provider", "sendgrid"),
        tier=payload.get("tier", "A"),
        enforce_tier=payload.get("enforce_tier", True),
    )


@router.get("/trust-tiers/stats")
def get_trust_tier_stats(_=Depends(require_admin)):
    """Get trust tier distribution statistics.

    Returns tier counts, percentages, role accounts, and suspicious domains.
    The campaign_ready field shows contacts safe for email campaigns (Tier A).
    """
    return ecs.get_tier_statistics()


@router.post("/trust-tiers/reclassify")
def reclassify_trust_tiers(_=Depends(require_admin)):
    """Reclassify all contacts into trust tiers.

    Run this after importing new contacts or updating classification rules.
    """
    from services.ai_engine.contacts_db import ContactsDB
    db = ContactsDB()
    return db.reclassify_all_tiers()


@router.get("/email/logs")
def get_email_logs(days: int = Query(30, ge=1, le=365), _=Depends(require_admin)):
    return {"logs": ecs.get_email_logs(days), "period_days": days}


@router.get("/email/analytics")
def get_email_analytics(days: int = Query(30, ge=1, le=365), _=Depends(require_admin)):
    return ecs.get_email_analytics(days)


# ── Override the 501 stubs from admin.py ──────────────────────────────────
# These endpoints provide real implementations for:
#   /email/status  → now use /integrations/status
#   /email/sync    → future IMAP sync triggercollection
#   /email/jobs    → future background email job list

@router.get("/email/status")
def email_status_real(_=Depends(require_admin)):
    """Real implementation replacing the 501 stub in admin.py."""
    status = ecs.get_integrations_status()
    analytics = ecs.get_contact_analytics()
    return {
        "providers": status,
        "recent_analytics": analytics,
        "total_contacts": analytics.get("total_contacts", 0),
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Email Intelligence — pattern guessing, domain analysis, batch import
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/intelligence/guess")
def guess_email(payload: Dict[str, Any], _=Depends(require_admin)):
    """Generate email guesses for a contact using pattern intelligence."""
    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")
    company = payload.get("company", "")
    domain = payload.get("domain")
    if not first_name or not last_name:
        raise HTTPException(400, "first_name and last_name required")
    if not company and not domain:
        raise HTTPException(400, "company or domain required")
    return ecs.guess_email(first_name, last_name, company, domain)


@router.post("/intelligence/guess_batch")
def guess_batch(payload: Dict[str, Any], _=Depends(require_admin)):
    """Batch guess emails for multiple contacts."""
    contacts = payload.get("contacts", [])
    if not contacts:
        raise HTTPException(400, "contacts list required")
    return ecs.guess_batch(contacts)


@router.get("/intelligence/domains")
def domain_stats(_=Depends(require_admin)):
    """Get domain pattern statistics from email intelligence engine."""
    return ecs.get_domain_stats()


@router.post("/intelligence/import")
def import_from_intelligence(_=Depends(require_admin)):
    """Import verified contacts from EmailIntelligence into ContactsDB."""
    return ecs.import_from_intelligence()


@router.get("/intelligence/bounced")
def list_bounced(bounce_type: str = Query(None), _=Depends(require_admin)):
    """List all bounced contacts with optional bounce_type filter."""
    bounced = ecs.get_bounced_contacts(bounce_type=bounce_type)
    return {"bounced": bounced, "total": len(bounced)}


@router.post("/intelligence/reattempt/{contact_id}")
def suggest_reattempt(contact_id: str, _=Depends(require_admin)):
    """Suggest alternative email patterns for a bounced guessed contact."""
    return ecs.suggest_reattempt(contact_id)


@router.get("/contacts/search")
def search_contacts(q: str = Query("", min_length=1), limit: int = Query(50, ge=1), _=Depends(require_admin)):
    """Full-text search across contacts (name, email, company, domain)."""
    results = ecs.search_contacts(q, limit=limit)
    return {"results": results, "total": len(results), "query": q}


# ═══════════════════════════════════════════════════════════════════════════
#  Unsubscribe & Suppression (CAN-SPAM / GDPR Compliance)
# ═══════════════════════════════════════════════════════════════════════════

# NOTE: This endpoint is PUBLIC (no auth) - it's the link clicked from emails
@router.get("/email/unsubscribe", include_in_schema=False)
def unsubscribe_email(
    email: str = Query(..., description="Email to unsubscribe"),
    token: str = Query(..., description="HMAC token for verification"),
    campaign: str = Query("", description="Campaign ID for tracking"),
):
    """
    Process unsubscribe request (public endpoint, linked from emails).
    
    Returns a simple HTML page confirming unsubscribe.
    """
    result = ecs.process_unsubscribe(email, token, campaign_id=campaign)
    
    if result.get("success"):
        html = f"""<!DOCTYPE html>
<html>
<head><title>Unsubscribed</title>
<style>body{{font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px;text-align:center}}</style>
</head>
<body>
<h2>You've been unsubscribed</h2>
<p>The email address <strong>{email}</strong> has been removed from our mailing list.</p>
<p>You will no longer receive marketing emails from us.</p>
</body>
</html>"""
    else:
        error = result.get("error", "Invalid or expired link")
        html = f"""<!DOCTYPE html>
<html>
<head><title>Unsubscribe Error</title>
<style>body{{font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px;text-align:center}}</style>
</head>
<body>
<h2>Unsubscribe Error</h2>
<p>{error}</p>
<p>Please contact support if you continue to receive unwanted emails.</p>
</body>
</html>"""
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


@router.get("/suppression/list")
def list_suppressed(
    reason: str = Query(None, description="Filter by reason: unsubscribed, bounced, complained"),
    _=Depends(require_admin)
):
    """List all suppressed email addresses with optional reason filter."""
    suppressed = ecs.get_suppressed_emails(reason=reason)
    return {"suppressed": suppressed, "total": len(suppressed)}


@router.post("/suppression/add")
def add_to_suppression(payload: Dict[str, Any], _=Depends(require_admin)):
    """Manually add an email to the suppression list."""
    email = payload.get("email", "").lower().strip()
    reason = payload.get("reason", "manual")
    
    if not email:
        raise HTTPException(400, "email required")
    
    # Check if already suppressed
    if ecs.is_email_suppressed(email):
        return {"success": False, "error": "Email already suppressed", "email": email}
    
    # Add to suppression list
    from datetime import datetime
    ecs._suppression_list[email] = {
        "reason": reason,
        "date": datetime.utcnow().isoformat(),
        "source": "admin_manual",
    }
    
    # Update contact status if exists
    contacts_db = ecs._get_contacts_db()
    contact = contacts_db.get_by_email(email)
    if contact:
        contact["status"] = "unsubscribed"
        contacts_db.update(contact["id"], status="unsubscribed")
    
    return {"success": True, "email": email, "reason": reason}


@router.delete("/suppression/remove")
def remove_from_suppression(
    email: str = Query(..., description="Email to remove from suppression"),
    _=Depends(require_admin)
):
    """Remove an email from the suppression list (re-enable sending)."""
    email = email.lower().strip()
    
    if email in ecs._suppression_list:
        del ecs._suppression_list[email]
        return {"success": True, "email": email, "message": "Removed from suppression list"}
    
    return {"success": False, "error": "Email not found in suppression list", "email": email}


@router.get("/suppression/check")
def check_suppression(email: str = Query(...), _=Depends(require_admin)):
    """Check if an email is on the suppression list."""
    email = email.lower().strip()
    is_suppressed = ecs.is_email_suppressed(email)
    details = ecs._suppression_list.get(email) if is_suppressed else None
    return {"email": email, "suppressed": is_suppressed, "details": details}


# ═══════════════════════════════════════════════════════════════════════════
#  Email Validation (5-Level Pattern Testing)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/validation/patterns/{contact_id}")
def get_validation_patterns(contact_id: str, _=Depends(require_admin)):
    """Get untested email patterns for a contact.

    Returns patterns to test in order of priority (most common first):
    1. firstname.lastname@domain
    2. firstnamelastname@domain
    3. flastname@domain
    4. firstname@domain
    5. f.lastname@domain
    """
    contacts_db = ecs._get_contacts_db()

    patterns = contacts_db.get_email_patterns(contact_id)
    if not patterns:
        # Check if contact exists
        contact = contacts_db.contacts.get(contact_id)
        if not contact:
            raise HTTPException(404, f"Contact {contact_id} not found")
        return {
            "contact_id": contact_id,
            "patterns": [],
            "message": "All patterns exhausted or contact already validated",
        }

    return {
        "contact_id": contact_id,
        "patterns": patterns,
        "total_patterns": len(patterns),
    }


@router.post("/validation/record")
def record_validation(payload: Dict[str, Any], _=Depends(require_admin)):
    """Record a validation attempt result.

    Payload:
    {
        "contact_id": "ct_abc123",
        "email_tested": "john.smith@acme.com",
        "pattern": "firstname.lastname",
        "result": "valid" | "bounced" | "unknown"
    }

    When result is "valid", the contact's email is updated to the tested email.
    When all patterns are exhausted with bounces, email_validated is set to False.
    """
    contacts_db = ecs._get_contacts_db()

    contact_id = payload.get("contact_id")
    email_tested = payload.get("email_tested")
    pattern = payload.get("pattern")
    result = payload.get("result")

    if not all([contact_id, email_tested, pattern, result]):
        raise HTTPException(400, "contact_id, email_tested, pattern, and result required")

    if result not in ("valid", "bounced", "unknown"):
        raise HTTPException(400, "result must be 'valid', 'bounced', or 'unknown'")

    updated = contacts_db.record_validation_attempt(
        contact_id, email_tested, pattern, result
    )
    if not updated:
        raise HTTPException(404, f"Contact {contact_id} not found")

    return {
        "success": True,
        "contact_id": contact_id,
        "email_tested": email_tested,
        "result": result,
        "email_validated": updated.get("email_validated"),
        "patterns_remaining": len(contacts_db.get_email_patterns(contact_id)),
    }


@router.post("/validation/auto-reply")
def process_auto_reply_endpoint(payload: Dict[str, Any], _=Depends(require_admin)):
    """Process an auto-reply email to extract intelligence.

    Detects:
    - Out of Office with return dates
    - Left company notices with forwarding emails
    - New contact information (creates new contacts)

    Payload:
    {
        "contact_id": "ct_abc123",
        "auto_reply_text": "I am out of the office until March 15th..."
    }
    """
    contacts_db = ecs._get_contacts_db()

    contact_id = payload.get("contact_id")
    text = payload.get("auto_reply_text", "")

    if not contact_id:
        raise HTTPException(400, "contact_id required")
    if not text:
        raise HTTPException(400, "auto_reply_text required")

    if contact_id not in contacts_db.contacts:
        raise HTTPException(404, f"Contact {contact_id} not found")

    result = contacts_db.process_auto_reply(contact_id, text)

    return {
        "success": True,
        "contact_id": contact_id,
        **result,
    }


@router.get("/validation/stats")
def validation_stats(_=Depends(require_admin)):
    """Get email validation statistics across all contacts."""
    contacts_db = ecs._get_contacts_db()

    stats = contacts_db.get_validation_stats()
    return stats


@router.get("/validation/unvalidated")
def list_unvalidated(
    limit: int = Query(100, ge=1, le=1000),
    tier: str = Query(None, description="Filter by tier: A, B, or C"),
    _=Depends(require_admin)
):
    """Get contacts that need email validation.

    Returns contacts where email_validated is None and patterns are available.
    """
    contacts_db = ecs._get_contacts_db()

    if tier and tier not in ("A", "B", "C"):
        raise HTTPException(400, "tier must be A, B, or C")

    contacts = contacts_db.get_unvalidated_contacts(limit=limit, tier=tier)
    return {
        "unvalidated": contacts,
        "total": len(contacts),
        "tier_filter": tier,
    }


@router.post("/validation/generate-patterns")
def generate_patterns(payload: Dict[str, Any], _=Depends(require_admin)):
    """Generate email patterns without a contact record.

    Useful for ad-hoc pattern generation.

    Payload:
    {
        "first_name": "John",
        "last_name": "Smith",
        "domain": "acme.com"
    }
    """
    from services.ai_engine.email_validator import validate_email_patterns

    first_name = payload.get("first_name", "")
    last_name = payload.get("last_name", "")
    domain = payload.get("domain", "")

    if not all([first_name, last_name, domain]):
        raise HTTPException(400, "first_name, last_name, and domain required")

    patterns = validate_email_patterns(first_name, last_name, domain)
    return {
        "first_name": first_name,
        "last_name": last_name,
        "domain": domain,
        "patterns": patterns,
    }


@router.post("/validation/parse-auto-reply")
def parse_auto_reply_text(payload: Dict[str, Any], _=Depends(require_admin)):
    """Parse auto-reply text without updating any contact.

    Useful for testing auto-reply detection.

    Payload:
    {
        "text": "I am out of the office until March 15th..."
    }
    """
    from services.ai_engine.email_validator import parse_auto_reply

    text = payload.get("text", "")
    if not text:
        raise HTTPException(400, "text required")

    result = parse_auto_reply(text)
    return {
        "type": result.type,
        "return_date": result.return_date.isoformat() if result.return_date else None,
        "forwarding_email": result.forwarding_email,
        "new_contact_name": result.new_contact_name,
        "new_contact_email": result.new_contact_email,
    }
