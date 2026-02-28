"""
contacts_db.py - Contact Database with Verified/Guessed Separation
==================================================================

Manages a persistent contact store where each record tracks:
- The contact's identity (name, company, title, domain)
- Email status: "verified" (from real data) or "guessed" (pattern-generated)
- For guessed: which pattern was used and confidence level
- Send tracking: when emails were sent, delivery status, bounce info
- Conversion funnel: freemium/paid status

Storage: JSON file at L:\\antigravity_version_ai_data_final\\ai_data_final\\contacts_database.json
"""

from __future__ import annotations

import json
import logging
import os
import re
import statistics
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH = Path(
    os.getenv("CAREERTROJAN_AI_DATA", os.path.join(os.getenv("CAREERTROJAN_DATA_ROOT", "./data"), "ai_data_final"))
) / "contacts_database.json"

VALID_SOURCE_TYPES = {"verified", "guessed"}
VALID_SEND_STATUSES = {"delivered", "bounced", "opened", "clicked", "unsubscribed"}
VALID_BOUNCE_TYPES = {"hard", "soft"}
VALID_CONVERSION_STATUSES = {"none", "freemium", "trial", "paid", "churned"}

# ---------------------------------------------------------------------------
# Trust Tier Classification
# ---------------------------------------------------------------------------
# Tier A (High Trust): Known placed candidates, known clients, personal emails, engaged last 5 years
# Tier B (Medium Trust): Older candidates, unknown recency, corporate domains
# Tier C (Risk): Scraped, role accounts, old unknown, suspicious domains

TRUST_TIERS = {"A", "B", "C", "unclassified"}

TIER_A_TAGS = {
    "placed_candidate", "known_client", "engaged_5y", "responded", "opened_email",
    "clicked_email", "active_user", "paid_user", "mentor", "verified_personal",
}

TIER_B_TAGS = {
    "older_candidate", "unknown_recency", "corporate_domain", "cold_outreach",
    "imported", "conference", "event", "webinar",
}

TIER_C_TAGS = {
    "scraped", "role_account", "old_unknown", "suspicious_domain", "bounced",
    "unsubscribed", "spam_complaint", "purchased_list", "unknown_source",
}

# Role email patterns (not real people)
ROLE_EMAIL_PATTERNS = {
    "info@", "sales@", "support@", "admin@", "contact@", "hello@", "help@",
    "careers@", "jobs@", "hr@", "recruitment@", "enquiries@", "office@",
    "team@", "press@", "media@", "marketing@", "feedback@", "legal@",
    "billing@", "accounts@", "noreply@", "no-reply@", "donotreply@",
}

# Suspicious domains
SUSPICIOUS_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "throwaway.email", "fakeinbox.com", "trashmail.com", "getnada.com",
    "sharklasers.com", "maildrop.cc", "discard.email", "yopmail.com",
}


# ---------------------------------------------------------------------------
# Contact record factory
# ---------------------------------------------------------------------------

def _empty_contact() -> dict[str, Any]:
    """Return a blank contact record with all default fields."""
    return {
        "id": "",
        "email": "",
        "first_name": "",
        "last_name": "",
        "company": "",
        "domain": "",
        "title": "",
        "phone": "",               # Phone number if available
        "source_type": "guessed",
        "source_detail": "",
        "pattern_used": None,
        "confidence": 0.0,
        "tags": [],
        "send_history": [],
        "conversion_status": "none",
        "created_at": "",
        "updated_at": "",
        "notes": "",               # Free-text notes
        "journal": [],             # List of dated journal entries
        "transactions": [],        # List of transaction records
        # Trust tier fields (data-richness based)
        "trust_tier": "unclassified",
        "tier_reason": "",
        "data_richness_score": 0,  # 0-100 based on data completeness
        "last_engagement": None,   # ISO timestamp of last positive engagement
        "engagement_score": 0,     # 0-100 based on activity
        "is_role_account": False,
        "placement_date": None,    # When they were placed (for candidates)
        "client_since": None,      # When they became a client
        # Email validation fields
        "email_validated": None,   # True/False/None (unvalidated)
        "email_validation_date": None,
        "validation_attempts": [],  # List of {pattern, tested_at, result}
        "email_invalid_reason": None,  # "bounced", "pattern_exhausted", "domain_invalid"
        "alternate_emails": [],    # Other known emails for this person
        # Auto-reply intelligence
        "auto_reply_detected": None,  # Last auto-reply timestamp
        "forwarding_email": None,  # New email from "left company" notice
        "out_of_office_until": None,  # OOO return date if detected
        "left_company_date": None,  # When they left (from auto-reply)
    }


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class ContactsDB:
    """Persistent contact database with verified/guessed email separation.

    Stores contacts in a JSON file, deduplicates by email address, and
    provides CRUD, querying, send-tracking, conversion-funnel management,
    and analytics suitable for an admin dashboard.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path: Path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.contacts: dict[str, dict[str, Any]] = {}  # id → contact record
        self._email_index: dict[str, str] = {}  # lowercase email → id
        self.load()

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _generate_id() -> str:
        """Generate a unique contact ID with ``ct_`` prefix."""
        return f"ct_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _now() -> str:
        """Current UTC timestamp in ISO-8601 format."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalise_email(email: str) -> str:
        return email.strip().lower()

    def _rebuild_email_index(self) -> None:
        """Rebuild ``_email_index`` from current contacts dict."""
        self._email_index.clear()
        for cid, rec in self.contacts.items():
            email_key = self._normalise_email(rec.get("email", ""))
            if email_key:
                self._email_index[email_key] = cid

    # ── CRUD ───────────────────────────────────────────────────────────

    def add_verified(
        self,
        email: str,
        first_name: str = "",
        last_name: str = "",
        company: str = "",
        domain: str = "",
        title: str = "",
        source: str = "",
        tags: list[str] | None = None,
        auto_save: bool = True,
    ) -> dict[str, Any]:
        """Add or update a verified email contact.

        If the email already exists as *guessed*, the record is upgraded to
        *verified* (confidence → 1.0).  If it already exists as verified the
        record is enriched with any new non-empty fields supplied here.

        Parameters
        ----------
        auto_save : bool
            If True (default), saves to disk after each add.
            Set False for batch imports, then call save() manually.

        Returns the contact record.
        """
        email_key = self._normalise_email(email)
        if not email_key:
            raise ValueError("email must not be empty")

        if not domain and "@" in email_key:
            domain = email_key.rsplit("@", 1)[1]

        existing_id = self._email_index.get(email_key)
        now = self._now()

        if existing_id:
            rec = self.contacts[existing_id]
            # Upgrade guessed → verified
            rec["source_type"] = "verified"
            rec["confidence"] = 1.0
            rec["pattern_used"] = None
            if source:
                rec["source_detail"] = source
            # Fill in any blank fields with new data
            for field, value in [
                ("first_name", first_name),
                ("last_name", last_name),
                ("company", company),
                ("domain", domain),
                ("title", title),
            ]:
                if value and not rec.get(field):
                    rec[field] = value
            if tags:
                existing_tags = set(rec.get("tags") or [])
                existing_tags.update(tags)
                rec["tags"] = sorted(existing_tags)
            rec["updated_at"] = now
            if auto_save:
                self.save()
            logger.debug("Verified-updated contact %s (%s)", existing_id, email_key)
            return rec

        # New contact
        cid = self._generate_id()
        rec = _empty_contact()
        rec.update(
            {
                "id": cid,
                "email": email_key,
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "domain": domain,
                "title": title,
                "source_type": "verified",
                "source_detail": source,
                "pattern_used": None,
                "confidence": 1.0,
                "tags": list(tags) if tags else [],
                "created_at": now,
                "updated_at": now,
            }
        )
        self.contacts[cid] = rec
        self._email_index[email_key] = cid
        if auto_save:
            self.save()
        logger.debug("Added verified contact %s (%s)", cid, email_key)
        return rec

    def add_guessed(
        self,
        email: str,
        first_name: str,
        last_name: str,
        company: str,
        domain: str,
        pattern: str,
        confidence: float,
        source: str = "",
    ) -> dict[str, Any]:
        """Add a guessed email contact.

        Will **not** overwrite a contact already stored as *verified*.
        If the email already exists as guessed, the record is updated only
        when the new confidence is higher.

        Returns the contact record.
        """
        email_key = self._normalise_email(email)
        if not email_key:
            raise ValueError("email must not be empty")

        if not domain and "@" in email_key:
            domain = email_key.rsplit("@", 1)[1]

        existing_id = self._email_index.get(email_key)
        now = self._now()

        if existing_id:
            rec = self.contacts[existing_id]
            if rec["source_type"] == "verified":
                logger.debug(
                    "Skipped guessed add for %s — already verified.", email_key
                )
                return rec
            # Update guessed record only if confidence improved
            if confidence > rec.get("confidence", 0.0):
                rec["pattern_used"] = pattern
                rec["confidence"] = confidence
                rec["source_detail"] = source or rec.get("source_detail", "")
                rec["updated_at"] = now
                self.save()
            return rec

        cid = self._generate_id()
        rec = _empty_contact()
        rec.update(
            {
                "id": cid,
                "email": email_key,
                "first_name": first_name,
                "last_name": last_name,
                "company": company,
                "domain": domain,
                "source_type": "guessed",
                "source_detail": source or f"pattern:{pattern}@{domain}",
                "pattern_used": pattern,
                "confidence": confidence,
                "created_at": now,
                "updated_at": now,
            }
        )
        self.contacts[cid] = rec
        self._email_index[email_key] = cid
        self.save()
        logger.debug("Added guessed contact %s (%s, conf=%.3f)", cid, email_key, confidence)
        return rec

    def get(self, contact_id: str) -> dict[str, Any] | None:
        """Get a contact by ID."""
        return self.contacts.get(contact_id)

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Get a contact by email address (case-insensitive)."""
        email_key = self._normalise_email(email)
        cid = self._email_index.get(email_key)
        return self.contacts.get(cid) if cid else None

    def update(self, contact_id: str, **fields: Any) -> dict[str, Any] | None:
        """Update specific fields on a contact.

        Immutable fields (``id``, ``created_at``) are silently ignored.
        If the email changes, the email index is updated accordingly.

        Returns the updated record, or ``None`` if not found.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        immutable = {"id", "created_at"}
        for key, value in fields.items():
            if key in immutable:
                continue
            if key == "email":
                # Re-index email
                old_email = self._normalise_email(rec.get("email", ""))
                new_email = self._normalise_email(value)
                if new_email != old_email:
                    # Check for conflict
                    if new_email in self._email_index:
                        raise ValueError(
                            f"Cannot change email to {new_email} — already exists."
                        )
                    self._email_index.pop(old_email, None)
                    self._email_index[new_email] = contact_id
                rec["email"] = new_email
            elif key in rec:
                rec[key] = value

        rec["updated_at"] = self._now()
        self.save()
        return rec

    def delete(self, contact_id: str) -> bool:
        """Delete a contact by ID.  Returns ``True`` if deleted."""
        rec = self.contacts.pop(contact_id, None)
        if rec is None:
            return False
        email_key = self._normalise_email(rec.get("email", ""))
        self._email_index.pop(email_key, None)
        self.save()
        logger.debug("Deleted contact %s (%s)", contact_id, email_key)
        return True

    # ── Queries ────────────────────────────────────────────────────────

    def list_all(
        self,
        source_type: str | None = None,
        page: int = 1,
        per_page: int = 50,
        search: str | None = None,
        company: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> dict[str, Any]:
        """List contacts with filtering, sorting, and pagination.

        Returns::

            {
                "contacts": [...],
                "total": N,
                "page": N,
                "per_page": N,
                "pages": N,
            }
        """
        items = list(self.contacts.values())

        # --- Filters ---
        if source_type and source_type in VALID_SOURCE_TYPES:
            items = [c for c in items if c.get("source_type") == source_type]

        if company:
            company_lower = company.lower()
            items = [c for c in items if company_lower in (c.get("company") or "").lower()]

        if search:
            search_lower = search.lower()
            items = [
                c
                for c in items
                if search_lower in (c.get("email") or "").lower()
                or search_lower in (c.get("first_name") or "").lower()
                or search_lower in (c.get("last_name") or "").lower()
                or search_lower in (c.get("company") or "").lower()
                or search_lower in (c.get("domain") or "").lower()
            ]

        # --- Sort ---
        reverse = sort_dir.lower() == "desc"
        items.sort(key=lambda c: c.get(sort_by) or "", reverse=reverse)

        # --- Paginate ---
        total = len(items)
        pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, pages))
        start = (page - 1) * per_page
        end = start + per_page

        return {
            "contacts": items[start:end],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    def get_verified(self, page: int = 1, per_page: int = 50) -> dict[str, Any]:
        """Shortcut: list only verified contacts."""
        return self.list_all(source_type="verified", page=page, per_page=per_page)

    def get_guessed(self, page: int = 1, per_page: int = 50) -> dict[str, Any]:
        """Shortcut: list only guessed contacts."""
        return self.list_all(source_type="guessed", page=page, per_page=per_page)

    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Full-text search across name, email, company, domain and title.

        Returns up to *limit* matching records ordered by relevance
        (number of fields matched).
        """
        if not query:
            return []

        q = query.lower()
        scored: list[tuple[int, dict[str, Any]]] = []

        for rec in self.contacts.values():
            score = 0
            for field in ("email", "first_name", "last_name", "company", "domain", "title"):
                if q in (rec.get(field) or "").lower():
                    score += 1
            if score > 0:
                scored.append((score, rec))

        scored.sort(key=lambda t: t[0], reverse=True)
        return [rec for _, rec in scored[:limit]]

    # ── Send tracking ─────────────────────────────────────────────────

    def record_send(self, contact_id: str, campaign_id: str) -> dict[str, Any] | None:
        """Record that an email was sent to a contact.

        Appends an entry to the contact's ``send_history``.
        Returns the updated contact record, or ``None`` if not found.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        now = self._now()
        entry: dict[str, Any] = {
            "sent_at": now,
            "campaign_id": campaign_id,
            "status": "delivered",
            "bounce_type": None,
            "updated_at": now,
        }
        rec.setdefault("send_history", []).append(entry)
        rec["updated_at"] = now
        self.save()
        logger.debug("Recorded send for %s (campaign %s)", contact_id, campaign_id)
        return rec

    def update_send_status(
        self,
        contact_id: str,
        campaign_id: str,
        status: str,
        bounce_type: str | None = None,
    ) -> dict[str, Any] | None:
        """Update delivery status for a specific send entry.

        Finds the most recent send_history entry matching *campaign_id* and
        updates its status.  Returns the contact record, or ``None``.
        """
        if status not in VALID_SEND_STATUSES:
            raise ValueError(
                f"Invalid status {status!r}. Must be one of {VALID_SEND_STATUSES}"
            )
        if bounce_type and bounce_type not in VALID_BOUNCE_TYPES:
            raise ValueError(
                f"Invalid bounce_type {bounce_type!r}. Must be one of {VALID_BOUNCE_TYPES}"
            )

        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        now = self._now()
        # Find the matching send entry (most recent first)
        for entry in reversed(rec.get("send_history", [])):
            if entry.get("campaign_id") == campaign_id:
                entry["status"] = status
                if bounce_type:
                    entry["bounce_type"] = bounce_type
                entry["updated_at"] = now
                break
        else:
            logger.warning(
                "No send_history entry found for contact %s / campaign %s",
                contact_id,
                campaign_id,
            )
            return rec

        rec["updated_at"] = now
        self.save()
        return rec

    def get_bounced(self, bounce_type: str | None = None) -> list[dict[str, Any]]:
        """Get all contacts that have at least one bounced send.

        Optionally filter by ``bounce_type`` ('hard' or 'soft').
        """
        results: list[dict[str, Any]] = []
        for rec in self.contacts.values():
            for entry in rec.get("send_history", []):
                if entry.get("status") == "bounced":
                    if bounce_type and entry.get("bounce_type") != bounce_type:
                        continue
                    results.append(rec)
                    break  # one match per contact is enough
        return results

    def suggest_reattempt(self, contact_id: str) -> list[dict[str, Any]]:
        """For a bounced *guessed* contact, suggest alternative email patterns.

        Uses :class:`EmailIntelligence` to regenerate guesses for the same
        name/company, excluding the bounced address and any other addresses
        already present in the database for this person.

        Returns a list of ``{email, pattern, confidence, domain}`` dicts.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            logger.warning("suggest_reattempt: contact %s not found.", contact_id)
            return []

        if rec.get("source_type") != "guessed":
            logger.info(
                "suggest_reattempt: contact %s is verified — no reattempt needed.",
                contact_id,
            )
            return []

        # Lazy-import to avoid circular dependency
        from services.ai_engine.email_intelligence import EmailIntelligence

        engine = EmailIntelligence()
        engine.load_verified_emails()
        engine.learn_patterns()

        guesses = engine.guess_email(
            first_name=rec.get("first_name", ""),
            last_name=rec.get("last_name", ""),
            company=rec.get("company", ""),
            domain=rec.get("domain"),
        )

        # Exclude the current (bounced) email and any other emails we already
        # have on record for this person/domain combination
        exclude_emails: set[str] = set()
        exclude_emails.add(self._normalise_email(rec.get("email", "")))

        # Also exclude any other contacts with the same name + domain
        name_key = (
            (rec.get("first_name") or "").lower(),
            (rec.get("last_name") or "").lower(),
            (rec.get("domain") or "").lower(),
        )
        for other in self.contacts.values():
            other_key = (
                (other.get("first_name") or "").lower(),
                (other.get("last_name") or "").lower(),
                (other.get("domain") or "").lower(),
            )
            if other_key == name_key:
                exclude_emails.add(self._normalise_email(other.get("email", "")))

        return [g for g in guesses if g["email"].lower() not in exclude_emails]

    # ── Conversion funnel ─────────────────────────────────────────────

    def update_conversion(self, contact_id: str, status: str) -> dict[str, Any] | None:
        """Update conversion status for a contact.

        Valid statuses: none, freemium, trial, paid, churned.
        Returns the updated contact record, or ``None`` if not found.
        """
        if status not in VALID_CONVERSION_STATUSES:
            raise ValueError(
                f"Invalid conversion status {status!r}. "
                f"Must be one of {VALID_CONVERSION_STATUSES}"
            )
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        rec["conversion_status"] = status
        rec["updated_at"] = self._now()
        self.save()
        logger.debug("Updated conversion for %s → %s", contact_id, status)
        return rec

    def get_funnel_stats(self) -> dict[str, int]:
        """Get conversion funnel statistics.

        Returns::

            {"none": N, "freemium": N, "trial": N, "paid": N, "churned": N, "total": N}
        """
        stats: dict[str, int] = {s: 0 for s in VALID_CONVERSION_STATUSES}
        for rec in self.contacts.values():
            status = rec.get("conversion_status", "none")
            if status in stats:
                stats[status] += 1
            else:
                stats["none"] += 1
        stats["total"] = len(self.contacts)
        return stats

    # ── Analytics ──────────────────────────────────────────────────────

    def get_analytics(self) -> dict[str, Any]:
        """Comprehensive analytics for the admin dashboard.

        Returns::

            {
                "total_contacts": int,
                "verified_count": int,
                "guessed_count": int,
                "avg_confidence": float,
                "sends_total": int,
                "delivered": int,
                "bounced": int,
                "opened": int,
                "clicked": int,
                "open_rate": float,
                "click_rate": float,
                "bounce_rate": float,
                "top_domains": [{"domain": str, "count": int}, ...],
                "top_companies": [{"company": str, "count": int}, ...],
                "conversion_funnel": {"none": N, "freemium": N, ...},
                "recent_sends": [... last 10 ...],
            }
        """
        verified_count = 0
        guessed_count = 0
        confidences: list[float] = []

        sends_total = 0
        delivered = 0
        bounced = 0
        opened = 0
        clicked = 0

        domain_counts: dict[str, int] = {}
        company_counts: dict[str, int] = {}
        all_sends: list[dict[str, Any]] = []

        for rec in self.contacts.values():
            # Source type counts
            if rec.get("source_type") == "verified":
                verified_count += 1
            else:
                guessed_count += 1

            # Confidence
            conf = rec.get("confidence")
            if conf is not None:
                confidences.append(float(conf))

            # Domain / company aggregation
            dom = rec.get("domain", "")
            if dom:
                domain_counts[dom] = domain_counts.get(dom, 0) + 1
            comp = rec.get("company", "")
            if comp:
                company_counts[comp] = company_counts.get(comp, 0) + 1

            # Send history
            for entry in rec.get("send_history", []):
                sends_total += 1
                status = entry.get("status", "")
                if status == "delivered":
                    delivered += 1
                elif status == "bounced":
                    bounced += 1
                elif status == "opened":
                    opened += 1
                elif status == "clicked":
                    clicked += 1
                all_sends.append(
                    {
                        "contact_id": rec["id"],
                        "email": rec.get("email", ""),
                        **entry,
                    }
                )

        # Rates (guard against division by zero)
        # opened and clicked contacts are considered a subset of delivered
        total_delivered = delivered + opened + clicked
        open_rate = (opened + clicked) / total_delivered if total_delivered else 0.0
        click_rate = clicked / total_delivered if total_delivered else 0.0
        bounce_rate = bounced / sends_total if sends_total else 0.0
        avg_confidence = statistics.mean(confidences) if confidences else 0.0

        # Top domains / companies
        top_domains = sorted(domain_counts.items(), key=lambda kv: kv[1], reverse=True)[:20]
        top_companies = sorted(company_counts.items(), key=lambda kv: kv[1], reverse=True)[:20]

        # Recent sends (last 10 by sent_at)
        all_sends.sort(key=lambda s: s.get("sent_at", ""), reverse=True)
        recent_sends = all_sends[:10]

        return {
            "total_contacts": len(self.contacts),
            "verified_count": verified_count,
            "guessed_count": guessed_count,
            "avg_confidence": round(avg_confidence, 4),
            "sends_total": sends_total,
            "delivered": delivered,
            "bounced": bounced,
            "opened": opened,
            "clicked": clicked,
            "open_rate": round(open_rate, 4),
            "click_rate": round(click_rate, 4),
            "bounce_rate": round(bounce_rate, 4),
            "top_domains": [{"domain": d, "count": c} for d, c in top_domains],
            "top_companies": [{"company": co, "count": c} for co, c in top_companies],
            "conversion_funnel": self.get_funnel_stats(),
            "recent_sends": recent_sends,
        }

    # ── Bulk operations ───────────────────────────────────────────────

    def import_from_intelligence(self, engine: Any) -> dict[str, int]:
        """Import verified contacts from an :class:`EmailIntelligence` instance.

        Only imports contacts that have **both** a name (first + last) and a
        corporate domain (not a free provider).  Deduplicates by email.

        Parameters
        ----------
        engine :
            An ``EmailIntelligence`` instance whose ``verified_contacts``
            have already been loaded.

        Returns
        -------
        dict
            ``{"imported": N, "skipped": N, "upgraded": N}``
        """
        # Import FREE_PROVIDERS from the intelligence module for filtering
        try:
            from services.ai_engine.email_intelligence import FREE_PROVIDERS
        except ImportError:
            FREE_PROVIDERS = set()  # type: ignore[assignment]

        imported = 0
        skipped = 0
        upgraded = 0

        for contact in getattr(engine, "verified_contacts", []):
            email = (contact.get("email") or "").strip().lower()
            first_name = contact.get("first_name", "")
            last_name = contact.get("last_name", "")
            domain = contact.get("domain", "")

            # Must have name and corporate domain
            if not email or not first_name or not last_name:
                skipped += 1
                continue
            if domain in FREE_PROVIDERS:
                skipped += 1
                continue

            email_key = self._normalise_email(email)
            existing_id = self._email_index.get(email_key)

            if existing_id:
                rec = self.contacts[existing_id]
                if rec.get("source_type") == "guessed":
                    # Upgrade guessed → verified
                    self.add_verified(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        company=contact.get("company", ""),
                        domain=domain,
                        source=contact.get("source", "intelligence_import"),
                    )
                    upgraded += 1
                else:
                    skipped += 1
            else:
                company = contact.get("company", "")
                # Try to resolve company from engine's domain mapping
                if not company:
                    company = getattr(engine, "domain_to_company", {}).get(domain, "")
                self.add_verified(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    company=company,
                    domain=domain,
                    source=contact.get("source", "intelligence_import"),
                )
                imported += 1

        logger.info(
            "import_from_intelligence: imported=%d, skipped=%d, upgraded=%d",
            imported,
            skipped,
            upgraded,
        )
        return {"imported": imported, "skipped": skipped, "upgraded": upgraded}

    def import_guessed_batch(self, guesses: list[dict[str, Any]]) -> dict[str, int]:
        """Import a batch of guessed contacts.

        Each dict should come from ``EmailIntelligence.guess_batch()`` output
        and contain at minimum: ``first_name``, ``last_name``, ``company``,
        and ``guessed_emails`` (a list of ``{email, pattern, confidence, domain}``).

        Only the **top guess** (highest confidence) is imported per contact.

        Returns
        -------
        dict
            ``{"imported": N, "skipped": N}``
        """
        imported = 0
        skipped = 0

        for item in guesses:
            first_name = item.get("first_name", "")
            last_name = item.get("last_name", "")
            company = item.get("company", "")
            guessed_emails = item.get("guessed_emails", [])

            if not guessed_emails:
                skipped += 1
                continue

            # Take the top guess
            top = guessed_emails[0]
            email = top.get("email", "")
            pattern = top.get("pattern", "")
            confidence = top.get("confidence", 0.0)
            domain = top.get("domain", "")

            if not email:
                skipped += 1
                continue

            email_key = self._normalise_email(email)
            if email_key in self._email_index:
                skipped += 1
                continue

            self.add_guessed(
                email=email,
                first_name=first_name,
                last_name=last_name,
                company=company,
                domain=domain,
                pattern=pattern,
                confidence=confidence,
                source=f"guess_batch:{pattern}@{domain}",
            )
            imported += 1

        logger.info(
            "import_guessed_batch: imported=%d, skipped=%d", imported, skipped
        )
        return {"imported": imported, "skipped": skipped}

    # ── Persistence ───────────────────────────────────────────────────

    def load(self) -> int:
        """Load contacts from the JSON file.

        Returns the number of contacts loaded.  If the file does not exist
        or is unreadable the database starts empty.
        """
        if not self.db_path.exists():
            logger.info("No existing database at %s — starting fresh.", self.db_path)
            return 0

        try:
            raw = self.db_path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load contacts database: %s", exc)
            return 0

        if isinstance(data, list):
            # Legacy format: list of records
            for rec in data:
                cid = rec.get("id")
                if cid:
                    self.contacts[cid] = rec
        elif isinstance(data, dict):
            # Preferred format: {"contacts": {id: record, ...}, ...}
            contacts_section = data.get("contacts", data)
            if isinstance(contacts_section, dict):
                self.contacts = contacts_section
            elif isinstance(contacts_section, list):
                for rec in contacts_section:
                    cid = rec.get("id")
                    if cid:
                        self.contacts[cid] = rec
        else:
            logger.warning("Unexpected data format in %s — starting fresh.", self.db_path)
            return 0

        self._rebuild_email_index()
        count = len(self.contacts)
        logger.info("Loaded %d contacts from %s", count, self.db_path)
        return count

    def save(self) -> None:
        """Save contacts to the JSON file (atomic write via temp + rename).

        The directory is created if it doesn't exist.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "meta": {
                "version": 1,
                "saved_at": self._now(),
                "total_contacts": len(self.contacts),
            },
            "contacts": self.contacts,
        }

        tmp_path = self.db_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            # Atomic rename (on Windows this replaces the target if it exists
            # only from Python 3.3+ with os.replace)
            os.replace(str(tmp_path), str(self.db_path))
            logger.debug("Saved %d contacts to %s", len(self.contacts), self.db_path)
        except OSError as exc:
            logger.error("Failed to save contacts database: %s", exc)
            # Try to clean up temp file
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    # ── Trust Tier Classification ─────────────────────────────────────

    def calculate_data_richness_score(self, contact: dict[str, Any]) -> int:
        """Calculate data richness score (0-100) based on available fields.

        Scoring breakdown:
        - Email present: 10 pts
        - First + Last name: 15 pts
        - Phone number: 15 pts
        - Company/domain: 10 pts
        - Title: 5 pts
        - Notes present: 10 pts
        - Journal entries: 10 pts (up to 3)
        - Transactions: 15 pts (up to 3)
        - Engagement history: 10 pts
        """
        score = 0

        # Email (required, but worth points)
        if contact.get("email"):
            score += 10

        # Name completeness
        if contact.get("first_name") and contact.get("last_name"):
            score += 15
        elif contact.get("first_name") or contact.get("last_name"):
            score += 7

        # Phone number (valuable for contact quality)
        if contact.get("phone"):
            score += 15

        # Company/domain
        if contact.get("company") or contact.get("domain"):
            score += 10

        # Title
        if contact.get("title"):
            score += 5

        # Notes (free-text info)
        notes = contact.get("notes", "")
        if notes and len(notes) > 10:
            score += 10

        # Journal entries (dated interactions)
        journal = contact.get("journal") or []
        journal_pts = min(len(journal), 3) * 3  # Up to 10 pts
        score += journal_pts

        # Transactions (business interactions)
        transactions = contact.get("transactions") or []
        tx_pts = min(len(transactions), 3) * 5  # Up to 15 pts
        score += tx_pts

        # Engagement history
        send_history = contact.get("send_history") or []
        has_engagement = any(
            e.get("status") in ("opened", "clicked", "replied")
            for e in send_history
        )
        if has_engagement or contact.get("last_engagement"):
            score += 10

        return min(score, 100)

    def classify_trust_tier(self, contact: dict[str, Any]) -> tuple[str, str]:
        """Classify a contact into Trust Tier A/B/C based on data richness.

        Tier A (70+ score): Rich data - name, phone, email, notes, journal, transactions
        Tier B (30-69 score): Partial data - some fields populated
        Tier C (<30 score): Sparse data - minimal information, unvalidated emails

        Auto-demotes:
        - Role accounts (info@, sales@) → Tier C
        - Invalid/bounced emails → Tier C
        - Suspicious domains → Tier C
        - Left company detected → Tier C (unless forwarding email)

        Returns
        -------
        tuple[str, str]
            (tier, reason) where tier is 'A', 'B', 'C', or 'unclassified'
        """
        email = (contact.get("email") or "").lower()
        domain = contact.get("domain", "").lower()
        tags = set(contact.get("tags") or [])

        # ── Auto-demote checks (Tier C) ────────────────────────────

        # Check for role account (info@, sales@, etc.)
        local_part = email.split("@")[0] if "@" in email else ""
        is_role = any(
            re.match(pattern.replace("@", ""), local_part, re.IGNORECASE)
            for pattern in ROLE_EMAIL_PATTERNS
        )
        if is_role:
            return ("C", "role_account")

        # Check for suspicious/temporary email domain
        if domain in SUSPICIOUS_DOMAINS:
            return ("C", "suspicious_domain")

        # Email explicitly marked invalid
        if contact.get("email_validated") is False:
            return ("C", f"email_invalid:{contact.get('email_invalid_reason', 'unknown')}")

        # Left company and no forwarding
        if contact.get("left_company_date") and not contact.get("forwarding_email"):
            return ("C", "left_company_no_forward")

        # Has Tier C tags (bounced, spam, etc.)
        if tags & TIER_C_TAGS:
            tag_match = tags & TIER_C_TAGS
            return ("C", f"tag:{list(tag_match)[0]}")

        # ── Data Richness Scoring ──────────────────────────────────

        richness_score = self.calculate_data_richness_score(contact)

        # Store the score on the contact
        contact["data_richness_score"] = richness_score

        # Tier A: Rich data (70+ score)
        if richness_score >= 70:
            return ("A", f"data_rich:{richness_score}")

        # Tier B: Partial data (30-69 score)
        if richness_score >= 30:
            return ("B", f"data_partial:{richness_score}")

        # Tier C: Sparse data (<30 score)
        return ("C", f"data_sparse:{richness_score}")

    def _is_role_account(self, email: str) -> bool:
        """Check if email is a role account (info@, sales@, etc.)."""
        local_part = email.split("@")[0] if "@" in email else ""
        return any(
            re.match(pattern, local_part, re.IGNORECASE)
            for pattern in ROLE_EMAIL_PATTERNS
        )

    def update_trust_tier(self, contact_id: str) -> dict[str, Any] | None:
        """Classify and update trust tier for a single contact.

        Returns the updated contact record, or None if not found.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        tier, reason = self.classify_trust_tier(rec)
        rec["trust_tier"] = tier
        rec["tier_reason"] = reason
        rec["is_role_account"] = self._is_role_account(rec.get("email", ""))
        rec["updated_at"] = self._now()

        self.save()
        logger.debug("Updated trust tier for %s → %s (%s)", contact_id, tier, reason)
        return rec

    def reclassify_all_tiers(self) -> dict[str, int]:
        """Batch reclassify all contacts into trust tiers.

        Returns
        -------
        dict
            {"A": count, "B": count, "C": count, "unclassified": count, "total": count}
        """
        counts = {"A": 0, "B": 0, "C": 0, "unclassified": 0}

        for contact_id, rec in self.contacts.items():
            tier, reason = self.classify_trust_tier(rec)
            rec["trust_tier"] = tier
            rec["tier_reason"] = reason
            rec["is_role_account"] = self._is_role_account(rec.get("email", ""))
            counts[tier] = counts.get(tier, 0) + 1

        self.save()
        counts["total"] = len(self.contacts)
        logger.info(
            "Reclassified all contacts: A=%d, B=%d, C=%d, unclassified=%d",
            counts["A"], counts["B"], counts["C"], counts["unclassified"]
        )
        return counts

    def get_tier_a_contacts(
        self,
        limit: int | None = None,
        exclude_bounced: bool = True,
    ) -> list[dict[str, Any]]:
        """Get all Tier A (high trust) contacts for campaigns.

        Parameters
        ----------
        limit : int | None
            Maximum number of contacts to return.
        exclude_bounced : bool
            If True, exclude contacts with hard bounces.

        Returns
        -------
        list[dict]
            List of Tier A contact records.
        """
        results: list[dict[str, Any]] = []

        for rec in self.contacts.values():
            if rec.get("trust_tier") != "A":
                continue

            # Optionally exclude hard-bounced
            if exclude_bounced:
                has_hard_bounce = any(
                    e.get("status") == "bounced" and e.get("bounce_type") == "hard"
                    for e in rec.get("send_history", [])
                )
                if has_hard_bounce:
                    continue

            results.append(rec)
            if limit and len(results) >= limit:
                break

        return results

    def get_contacts_by_tier(
        self,
        tier: str,
        limit: int | None = None,
        exclude_bounced: bool = True,
    ) -> list[dict[str, Any]]:
        """Get contacts by specific trust tier.

        Parameters
        ----------
        tier : str
            Trust tier: 'A', 'B', 'C', or 'unclassified'
        limit : int | None
            Maximum number of contacts to return.
        exclude_bounced : bool
            If True, exclude contacts with hard bounces.

        Returns
        -------
        list[dict]
            List of contact records in the specified tier.
        """
        if tier not in TRUST_TIERS:
            raise ValueError(f"Invalid tier {tier!r}. Must be one of {TRUST_TIERS}")

        results: list[dict[str, Any]] = []

        for rec in self.contacts.values():
            if rec.get("trust_tier") != tier:
                continue

            if exclude_bounced:
                has_hard_bounce = any(
                    e.get("status") == "bounced" and e.get("bounce_type") == "hard"
                    for e in rec.get("send_history", [])
                )
                if has_hard_bounce:
                    continue

            results.append(rec)
            if limit and len(results) >= limit:
                break

        return results

    def get_tier_stats(self) -> dict[str, Any]:
        """Get statistics on trust tier distribution.

        Returns
        -------
        dict
            {
                "tier_counts": {"A": N, "B": N, "C": N, "unclassified": N},
                "tier_percentages": {"A": pct, "B": pct, ...},
                "role_accounts": N,
                "suspicious_domains": N,
                "reason_breakdown": {"placed_candidate": N, ...}
            }
        """
        tier_counts = {"A": 0, "B": 0, "C": 0, "unclassified": 0}
        reason_counts: dict[str, int] = {}
        role_accounts = 0
        suspicious_domains = 0

        for rec in self.contacts.values():
            tier = rec.get("trust_tier", "unclassified")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            reason = rec.get("tier_reason", "")
            if reason:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

            if rec.get("is_role_account"):
                role_accounts += 1

            domain = rec.get("domain", "").lower()
            if domain in SUSPICIOUS_DOMAINS:
                suspicious_domains += 1

        total = len(self.contacts) or 1
        tier_pcts = {
            tier: round(count / total * 100, 2)
            for tier, count in tier_counts.items()
        }

        return {
            "tier_counts": tier_counts,
            "tier_percentages": tier_pcts,
            "role_accounts": role_accounts,
            "suspicious_domains": suspicious_domains,
            "reason_breakdown": dict(sorted(reason_counts.items(), key=lambda kv: -kv[1])),
            "total_contacts": total,
        }

    def mark_placed_candidate(
        self,
        contact_id: str,
        placement_date: str | None = None,
    ) -> dict[str, Any] | None:
        """Mark a contact as a placed candidate (auto-promotes to Tier A).

        Parameters
        ----------
        contact_id : str
            The contact ID.
        placement_date : str | None
            ISO format date of placement. Defaults to now if not provided.

        Returns
        -------
        dict | None
            Updated contact record, or None if not found.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        rec["placement_date"] = placement_date or self._now()
        rec["tags"] = list(set(rec.get("tags") or []) | {"placed"})

        # Reclassify (will become Tier A)
        tier, reason = self.classify_trust_tier(rec)
        rec["trust_tier"] = tier
        rec["tier_reason"] = reason
        rec["updated_at"] = self._now()

        self.save()
        logger.info("Marked contact %s as placed candidate → Tier %s", contact_id, tier)
        return rec

    def mark_client(
        self,
        contact_id: str,
        client_since: str | None = None,
    ) -> dict[str, Any] | None:
        """Mark a contact as a known client (auto-promotes to Tier A).

        Parameters
        ----------
        contact_id : str
            The contact ID.
        client_since : str | None
            ISO format date when became client. Defaults to now if not provided.

        Returns
        -------
        dict | None
            Updated contact record, or None if not found.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        rec["client_since"] = client_since or self._now()
        rec["tags"] = list(set(rec.get("tags") or []) | {"client"})

        # Reclassify (will become Tier A)
        tier, reason = self.classify_trust_tier(rec)
        rec["trust_tier"] = tier
        rec["tier_reason"] = reason
        rec["updated_at"] = self._now()

        self.save()
        logger.info("Marked contact %s as client → Tier %s", contact_id, tier)
        return rec

    def record_engagement(
        self,
        contact_id: str,
        engagement_date: str | None = None,
        score_delta: int = 1,
    ) -> dict[str, Any] | None:
        """Record an engagement (reply, click, meeting) for a contact.

        Engagements can promote contacts to higher trust tiers.

        Parameters
        ----------
        contact_id : str
            The contact ID.
        engagement_date : str | None
            ISO format date of engagement. Defaults to now.
        score_delta : int
            How much to increase the engagement score (default 1).

        Returns
        -------
        dict | None
            Updated contact record, or None if not found.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        rec["last_engagement"] = engagement_date or self._now()
        rec["engagement_score"] = rec.get("engagement_score", 0) + score_delta
        rec["tags"] = list(set(rec.get("tags") or []) | {"engaged"})

        # Reclassify (engagement may promote tier)
        tier, reason = self.classify_trust_tier(rec)
        rec["trust_tier"] = tier
        rec["tier_reason"] = reason
        rec["updated_at"] = self._now()

        self.save()
        logger.debug(
            "Recorded engagement for %s: score=%d → Tier %s",
            contact_id, rec["engagement_score"], tier
        )
        return rec

    # ── Email Validation Integration ───────────────────────────────────

    def get_email_validator(self):
        """Get an EmailValidator instance wired to this ContactsDB.

        Returns
        -------
        EmailValidator
            Validator instance with access to this database.
        """
        from services.ai_engine.email_validator import EmailValidator
        return EmailValidator(contacts_db=self)

    def get_email_patterns(self, contact_id: str) -> list[dict[str, Any]]:
        """Get untested email patterns for a contact.

        Parameters
        ----------
        contact_id : str
            Contact ID to generate patterns for.

        Returns
        -------
        list[dict]
            List of {email, pattern_name, priority} dicts.
        """
        rec = self.contacts.get(contact_id)
        if rec is None:
            return []

        validator = self.get_email_validator()
        patterns = validator.get_patterns_for_contact(rec)

        return [
            {
                "email": p.email,
                "pattern": p.pattern_name,
                "priority": p.priority,
            }
            for p in patterns
        ]

    def record_validation_attempt(
        self,
        contact_id: str,
        email_tested: str,
        pattern_name: str,
        result: str,  # "valid", "bounced", "unknown"
    ) -> dict[str, Any] | None:
        """Record a validation attempt for a contact.

        Parameters
        ----------
        contact_id : str
            Contact ID.
        email_tested : str
            The email address that was tested.
        pattern_name : str
            The pattern name (e.g., "firstname.lastname").
        result : str
            "valid", "bounced", or "unknown".

        Returns
        -------
        dict | None
            Updated contact record, or None if not found.
        """
        from services.ai_engine.email_validator import EmailPattern

        rec = self.contacts.get(contact_id)
        if rec is None:
            return None

        # Create pattern object for the validator
        pattern = EmailPattern(
            email=email_tested,
            pattern_name=pattern_name,
            priority=0,  # Not used for recording
        )

        validator = self.get_email_validator()
        return validator.record_validation_attempt(contact_id, pattern, result)

    def process_auto_reply(
        self,
        contact_id: str,
        auto_reply_text: str,
    ) -> dict[str, Any]:
        """Process an auto-reply email and extract intelligence.

        Detects OOO messages (with return dates) and left-company notices
        (with forwarding emails). Creates new contacts from auto-replies.

        Parameters
        ----------
        contact_id : str
            Contact who sent the auto-reply.
        auto_reply_text : str
            The auto-reply message body.

        Returns
        -------
        dict
            {
                "type": "ooo" | "left_company" | "forwarding" | "unknown",
                "return_date": str | None,
                "forwarding_email": str | None,
                "new_contact_id": str | None,
                "original_contact_updated": bool,
            }
        """
        validator = self.get_email_validator()
        result = validator.process_auto_reply(contact_id, auto_reply_text)

        # Flatten the result for API response
        parsed = result.get("parsed")
        return {
            "type": parsed.type if parsed else "unknown",
            "return_date": parsed.return_date.isoformat() if parsed and parsed.return_date else None,
            "forwarding_email": parsed.forwarding_email if parsed else None,
            "new_contact_name": parsed.new_contact_name if parsed else None,
            "new_contact_email": parsed.new_contact_email if parsed else None,
            "new_contact_id": result.get("new_contact_created"),
            "original_contact_updated": result.get("original_contact_updated", False),
        }

    def get_validation_stats(self) -> dict[str, Any]:
        """Get email validation statistics across all contacts.

        Returns
        -------
        dict
            {
                "total_contacts": int,
                "validated": int,
                "invalid": int,
                "unvalidated": int,
                "patterns_tested": int,
                "ooo_detected": int,
                "left_company": int,
                "forwarding_captured": int,
            }
        """
        validator = self.get_email_validator()
        return validator.get_validation_stats()

    def get_unvalidated_contacts(
        self,
        limit: int = 100,
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get contacts that haven't been validated yet.

        Parameters
        ----------
        limit : int
            Maximum number to return.
        tier : str | None
            Filter by trust tier (A, B, C).

        Returns
        -------
        list[dict]
            Contacts with email_validated = None and untested patterns.
        """
        results = []
        for rec in self.contacts.values():
            if rec.get("email_validated") is not None:
                continue  # Already validated (True or False)

            if tier and rec.get("trust_tier") != tier:
                continue

            # Check if has patterns remaining
            patterns = self.get_email_patterns(rec["id"])
            if patterns:
                results.append({
                    **rec,
                    "patterns_remaining": len(patterns),
                })

            if len(results) >= limit:
                break

        return results


# ---------------------------------------------------------------------------
# CLI / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    print("=" * 70)
    print("  ContactsDB — Demo / Smoke-test")
    print("=" * 70)

    db = ContactsDB()
    print(f"\nLoaded {len(db.contacts)} existing contacts from {db.db_path}")

    # ── Add some verified contacts ────────────────────────────────────
    print("\n── Adding verified contacts ──")
    v1 = db.add_verified(
        email="john.smith@basf.com",
        first_name="John",
        last_name="Smith",
        company="BASF",
        domain="basf.com",
        title="Process Engineer",
        source="email_json:email_CV for John Smith.json",
        tags=["engineering", "pharma"],
    )
    print(f"  Added/updated: {v1['id']}  {v1['email']}  [{v1['source_type']}]")

    v2 = db.add_verified(
        email="anna.jones@amgen.com",
        first_name="Anna",
        last_name="Jones",
        company="Amgen",
        domain="amgen.com",
        source="email_json:email_CV for Anna Jones.json",
    )
    print(f"  Added/updated: {v2['id']}  {v2['email']}  [{v2['source_type']}]")

    # ── Add some guessed contacts ─────────────────────────────────────
    print("\n── Adding guessed contacts ──")
    g1 = db.add_guessed(
        email="tony.ryan@amgen.com",
        first_name="Tony",
        last_name="Ryan",
        company="Amgen",
        domain="amgen.com",
        pattern="first.last",
        confidence=0.85,
    )
    print(f"  Added/updated: {g1['id']}  {g1['email']}  [{g1['source_type']}  conf={g1['confidence']}]")

    g2 = db.add_guessed(
        email="m.mueller@bayer.com",
        first_name="Michael",
        last_name="Mueller",
        company="Bayer",
        domain="bayer.com",
        pattern="f.last",
        confidence=0.72,
    )
    print(f"  Added/updated: {g2['id']}  {g2['email']}  [{g2['source_type']}  conf={g2['confidence']}]")

    # ── Upgrade: add verified email that already exists as guessed ────
    print("\n── Upgrading guessed → verified ──")
    upgraded = db.add_verified(
        email="tony.ryan@amgen.com",
        first_name="Tony",
        last_name="Ryan",
        company="Amgen",
        domain="amgen.com",
        source="email_json:email_CV for Tony Ryan.json",
    )
    print(
        f"  tony.ryan@amgen.com now: source_type={upgraded['source_type']}, "
        f"confidence={upgraded['confidence']}"
    )

    # ── Search ────────────────────────────────────────────────────────
    print("\n── Search for 'amgen' ──")
    results = db.search("amgen")
    for r in results:
        print(f"  {r['email']:40s}  {r['source_type']:10s}  {r['company']}")

    # ── Record sends & update status ──────────────────────────────────
    print("\n── Send tracking ──")
    db.record_send(g2["id"], "camp_001")
    db.update_send_status(g2["id"], "camp_001", "bounced", bounce_type="hard")
    print(f"  Recorded send + bounce for {g2['email']}")

    bounced = db.get_bounced()
    print(f"  Bounced contacts: {len(bounced)}")
    for b in bounced:
        print(f"    {b['email']}")

    # ── Conversion funnel ─────────────────────────────────────────────
    print("\n── Conversion funnel ──")
    db.update_conversion(v1["id"], "freemium")
    db.update_conversion(v2["id"], "trial")
    funnel = db.get_funnel_stats()
    for status, count in funnel.items():
        print(f"  {status:12s}: {count}")

    # ── Analytics ─────────────────────────────────────────────────────
    print("\n── Analytics ──")
    analytics = db.get_analytics()
    for key in (
        "total_contacts",
        "verified_count",
        "guessed_count",
        "avg_confidence",
        "sends_total",
        "bounce_rate",
        "open_rate",
        "click_rate",
    ):
        print(f"  {key:20s}: {analytics[key]}")

    print("\n  Top domains:")
    for d in analytics["top_domains"][:5]:
        print(f"    {d['domain']:30s}  {d['count']}")

    print("\n  Top companies:")
    for c in analytics["top_companies"][:5]:
        print(f"    {c['company']:30s}  {c['count']}")

    # ── Listing ───────────────────────────────────────────────────────
    print("\n── Paginated listing (all, page 1) ──")
    page = db.list_all(page=1, per_page=10)
    print(f"  Total: {page['total']}, Page {page['page']}/{page['pages']}")
    for c in page["contacts"]:
        print(
            f"  {c['id']}  {c['email']:40s}  {c['source_type']:10s}  "
            f"conf={c['confidence']:.2f}  {c['company']}"
        )

    print("\n" + "=" * 70)
    print(f"  Database saved to: {db.db_path}")
    print(f"  Total contacts: {len(db.contacts)}")
    print("=" * 70)
