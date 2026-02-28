"""
Contacts API Router - Exposes ContactsDB (30K+ contacts) via REST endpoints.

Prefix: /api/contacts/v1
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from services.backend_api.utils.auth_deps import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contacts/v1", tags=["contacts"], dependencies=[Depends(require_admin)])

# Lazy-load ContactsDB to avoid import issues during startup
_contacts_db = None


def _get_db():
    """Get or initialize the ContactsDB singleton."""
    global _contacts_db
    if _contacts_db is None:
        try:
            from services.ai_engine.contacts_db import ContactsDB
            _contacts_db = ContactsDB()
            logger.info("ContactsDB loaded with %d contacts", len(_contacts_db.contacts))
        except Exception as e:
            logger.error("Failed to load ContactsDB: %s", e)
            raise HTTPException(status_code=503, detail=f"ContactsDB unavailable: {e}")
    return _contacts_db


# ---------------------------------------------------------------------------
# List / Pagination
# ---------------------------------------------------------------------------

@router.get("/")
async def list_contacts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=500, description="Items per page"),
    source_type: str | None = Query(None, description="Filter: verified or guessed"),
    company: str | None = Query(None, description="Filter by company name (partial match)"),
    search: str | None = Query(None, description="Search across email, name, company, domain"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_dir: str = Query("desc", description="Sort direction: asc or desc"),
) -> dict[str, Any]:
    """
    List contacts with pagination and filtering.
    
    Returns paginated contact list with metadata.
    """
    db = _get_db()
    return db.list_all(
        source_type=source_type,
        page=page,
        per_page=per_page,
        search=search,
        company=company,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/verified")
async def list_verified_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """List only verified contacts."""
    db = _get_db()
    return db.get_verified(page=page, per_page=per_page)


@router.get("/guessed")
async def list_guessed_contacts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """List only guessed (pattern-generated) contacts."""
    db = _get_db()
    return db.get_guessed(page=page, per_page=per_page)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get("/search")
async def search_contacts(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
) -> dict[str, Any]:
    """
    Full-text search across email, name, company, domain, title.
    
    Returns up to `limit` matching contacts ordered by relevance.
    """
    db = _get_db()
    results = db.search(query=q, limit=limit)
    return {
        "query": q,
        "count": len(results),
        "contacts": results,
    }


# ---------------------------------------------------------------------------
# Single Contact
# ---------------------------------------------------------------------------

@router.get("/{contact_id}")
async def get_contact(contact_id: str) -> dict[str, Any]:
    """Get a single contact by ID."""
    db = _get_db()
    contact = db.get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return contact


@router.get("/by-email/{email:path}")
async def get_contact_by_email(email: str) -> dict[str, Any]:
    """Get a contact by email address (case-insensitive)."""
    db = _get_db()
    contact = db.get_by_email(email)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact with email {email} not found")
    return contact


# ---------------------------------------------------------------------------
# Trust Tiers
# ---------------------------------------------------------------------------

@router.get("/tier/{tier}")
async def get_contacts_by_tier(
    tier: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    sort_by: str = Query("data_richness_score", description="Sort field"),
    sort_dir: str = Query("desc"),
) -> dict[str, Any]:
    """
    Get contacts by trust tier (A, B, C, unclassified).
    
    Tier A = High trust (70+ data richness, engaged)
    Tier B = Medium trust (30-69 data richness)
    Tier C = Low trust (<30 data richness or role accounts)
    """
    db = _get_db()
    try:
        return db.get_contacts_by_tier(
            tier=tier.upper(),
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tier-stats")
async def get_tier_stats() -> dict[str, Any]:
    """
    Get trust tier statistics.
    
    Returns count and percentage for each tier, plus data richness metrics.
    """
    db = _get_db()
    return db.get_tier_stats()


# ---------------------------------------------------------------------------
# Analytics & Stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_contact_stats() -> dict[str, Any]:
    """
    Get basic contact statistics.
    
    Returns total counts, source breakdown, and conversion funnel.
    """
    db = _get_db()
    total = len(db.contacts)
    verified = sum(1 for c in db.contacts.values() if c.get("source_type") == "verified")
    guessed = total - verified
    funnel = db.get_funnel_stats()
    
    return {
        "total_contacts": total,
        "verified_count": verified,
        "guessed_count": guessed,
        "verified_pct": round(verified / total * 100, 2) if total else 0,
        "conversion_funnel": funnel,
    }


@router.get("/analytics")
async def get_contact_analytics() -> dict[str, Any]:
    """
    Get comprehensive contact analytics for admin dashboard.
    
    Includes send statistics, open/click rates, top domains/companies,
    and conversion funnel breakdown.
    """
    db = _get_db()
    return db.get_analytics()


@router.get("/funnel")
async def get_conversion_funnel() -> dict[str, int]:
    """
    Get conversion funnel statistics.
    
    Returns count for each status: none, freemium, trial, paid, churned.
    """
    db = _get_db()
    return db.get_funnel_stats()


# ---------------------------------------------------------------------------
# Bounced & Validation
# ---------------------------------------------------------------------------

@router.get("/bounced")
async def get_bounced_contacts(
    bounce_type: str | None = Query(None, description="Filter: hard or soft"),
) -> dict[str, Any]:
    """Get contacts with bounced sends."""
    db = _get_db()
    contacts = db.get_bounced(bounce_type=bounce_type)
    return {
        "count": len(contacts),
        "bounce_type_filter": bounce_type,
        "contacts": contacts,
    }


@router.get("/{contact_id}/suggest-reattempt")
async def suggest_email_reattempt(contact_id: str) -> dict[str, Any]:
    """
    For a bounced guessed contact, suggest alternative email patterns.
    
    Uses EmailIntelligence to generate new guesses for the same person,
    excluding already-tried addresses.
    """
    db = _get_db()
    contact = db.get(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    
    suggestions = db.suggest_reattempt(contact_id)
    return {
        "contact_id": contact_id,
        "email": contact.get("email"),
        "source_type": contact.get("source_type"),
        "suggestions_count": len(suggestions),
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Mutations (Write Operations)
# ---------------------------------------------------------------------------

@router.post("/")
async def add_contact(
    email: str,
    first_name: str = "",
    last_name: str = "",
    company: str = "",
    domain: str = "",
    title: str = "",
    source: str = "api",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Add a new verified contact.
    
    If the email exists, the record is upgraded to verified (if it was guessed)
    or enriched with new data.
    """
    db = _get_db()
    try:
        contact = db.add_verified(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            domain=domain,
            title=title,
            source=source,
            tags=tags,
        )
        return {"ok": True, "contact": contact}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{contact_id}")
async def update_contact(contact_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update a contact's fields."""
    db = _get_db()
    contact = db.update(contact_id, **updates)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return {"ok": True, "contact": contact}


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str) -> dict[str, Any]:
    """Delete a contact by ID."""
    db = _get_db()
    deleted = db.delete(contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return {"ok": True, "deleted": contact_id}


# ---------------------------------------------------------------------------
# Send Tracking
# ---------------------------------------------------------------------------

@router.post("/{contact_id}/send")
async def record_send(contact_id: str, campaign_id: str) -> dict[str, Any]:
    """Record that an email was sent to a contact."""
    db = _get_db()
    contact = db.record_send(contact_id, campaign_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return {"ok": True, "contact": contact}


@router.patch("/{contact_id}/send-status")
async def update_send_status(
    contact_id: str,
    campaign_id: str,
    status: str,
    bounce_type: str | None = None,
) -> dict[str, Any]:
    """
    Update delivery status for a send.
    
    Valid statuses: delivered, bounced, opened, clicked, unsubscribed.
    If bounced, optionally specify bounce_type: hard or soft.
    """
    db = _get_db()
    try:
        contact = db.update_send_status(contact_id, campaign_id, status, bounce_type)
        if not contact:
            raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
        return {"ok": True, "contact": contact}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Conversion Funnel
# ---------------------------------------------------------------------------

@router.patch("/{contact_id}/conversion")
async def update_conversion(contact_id: str, status: str) -> dict[str, Any]:
    """
    Update conversion status for a contact.
    
    Valid statuses: none, freemium, trial, paid, churned.
    """
    db = _get_db()
    try:
        contact = db.update_conversion(contact_id, status)
        if not contact:
            raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
        return {"ok": True, "contact": contact}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Trust Tier Updates
# ---------------------------------------------------------------------------

@router.post("/{contact_id}/reclassify-tier")
async def reclassify_contact_tier(contact_id: str) -> dict[str, Any]:
    """Reclassify a single contact's trust tier based on current data."""
    db = _get_db()
    contact = db.update_trust_tier(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    return {
        "ok": True,
        "contact_id": contact_id,
        "trust_tier": contact.get("trust_tier"),
        "tier_reason": contact.get("tier_reason"),
        "data_richness_score": contact.get("data_richness_score"),
    }


@router.post("/reclassify-all-tiers")
async def reclassify_all_tiers() -> dict[str, Any]:
    """
    Reclassify trust tiers for ALL contacts.
    
    Warning: This can take a while for large databases.
    """
    db = _get_db()
    stats = db.reclassify_all_tiers()
    return {
        "ok": True,
        "message": "All contacts reclassified",
        "tier_counts": stats,
    }
