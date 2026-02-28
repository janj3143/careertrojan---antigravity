"""
email_validator.py - Email Pattern Validator & Auto-Reply Intelligence
======================================================================

Provides:
1. 5-Level Email Pattern Validator
   - Tests common email patterns (firstname.lastname, f.lastname, etc.)
   - Marks emails as valid/invalid after pattern exhaustion

2. Auto-Reply Parser
   - Detects "Out of Office" messages and extracts return dates
   - Detects "Left Company" messages and extracts forwarding emails
   - Parses new contacts from auto-reply signatures

3. Bounce Handler
   - Processes bounce notifications
   - Extracts new email addresses from forwarding notices
   - Updates contact records with validation status

Common Email Patterns (ordered by frequency):
1. firstname.lastname@domain.com (john.smith@company.com)
2. firstnamelastname@domain.com  (johnsmith@company.com)
3. flastname@domain.com          (jsmith@company.com)
4. firstname@domain.com          (john@company.com)
5. f.lastname@domain.com         (j.smith@company.com)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Common TLDs for email pattern generation
# ---------------------------------------------------------------------------

COMMON_TLDS = [".com", ".co.uk", ".org", ".net", ".io", ".co", ".com.au"]


# ---------------------------------------------------------------------------
# Email Pattern Generator
# ---------------------------------------------------------------------------

@dataclass
class EmailPattern:
    """Represents a generated email pattern for validation."""
    email: str
    pattern_name: str
    priority: int  # 1 = most common, 5 = least common


def generate_email_patterns(
    first_name: str,
    last_name: str,
    domain: str,
) -> list[EmailPattern]:
    """Generate 5-level email patterns for validation testing.

    Patterns (in order of commonality):
    1. firstname.lastname@domain (most common)
    2. firstnamelastname@domain
    3. flastname@domain
    4. firstname@domain
    5. f.lastname@domain (least common)

    Parameters
    ----------
    first_name : str
        Contact's first name.
    last_name : str
        Contact's last name.
    domain : str
        Company domain (e.g., "company.com").

    Returns
    -------
    list[EmailPattern]
        List of email patterns to test, ordered by priority.
    """
    if not first_name or not last_name or not domain:
        return []

    first = first_name.lower().strip()
    last = last_name.lower().strip()
    domain = domain.lower().strip()

    # Remove any @ if accidentally included in domain
    if domain.startswith("@"):
        domain = domain[1:]

    patterns = [
        EmailPattern(
            email=f"{first}.{last}@{domain}",
            pattern_name="firstname.lastname",
            priority=1,
        ),
        EmailPattern(
            email=f"{first}{last}@{domain}",
            pattern_name="firstnamelastname",
            priority=2,
        ),
        EmailPattern(
            email=f"{first[0]}{last}@{domain}",
            pattern_name="flastname",
            priority=3,
        ),
        EmailPattern(
            email=f"{first}@{domain}",
            pattern_name="firstname",
            priority=4,
        ),
        EmailPattern(
            email=f"{first[0]}.{last}@{domain}",
            pattern_name="f.lastname",
            priority=5,
        ),
    ]

    return patterns


def generate_patterns_with_tlds(
    first_name: str,
    last_name: str,
    company: str,
) -> list[EmailPattern]:
    """Generate patterns across common TLDs when domain is unknown.

    Useful when we only know the company name, not the exact domain.

    Parameters
    ----------
    first_name : str
        Contact's first name.
    last_name : str
        Contact's last name.
    company : str
        Company name to convert to domain guesses.

    Returns
    -------
    list[EmailPattern]
        Expanded list with common TLD variations.
    """
    if not company:
        return []

    # Clean company name to domain-like format
    company_clean = re.sub(r"[^a-zA-Z0-9]", "", company.lower())

    all_patterns = []
    for tld in COMMON_TLDS:
        domain = f"{company_clean}{tld}"
        patterns = generate_email_patterns(first_name, last_name, domain)
        all_patterns.extend(patterns)

    return all_patterns


# ---------------------------------------------------------------------------
# Auto-Reply Parser
# ---------------------------------------------------------------------------

@dataclass
class AutoReplyResult:
    """Result of parsing an auto-reply email."""
    type: str  # "ooo" (out of office), "left_company", "forwarding", "unknown"
    return_date: datetime | None  # When they'll be back (OOO)
    forwarding_email: str | None  # New email to use
    new_contact_name: str | None  # Name of replacement contact
    new_contact_email: str | None  # Email of replacement contact
    raw_text: str  # Original auto-reply text


# OOO patterns
OOO_PATTERNS = [
    r"(?:out of (?:the )?office|ooo|away|on (?:annual )?leave|on vacation|on holiday)",
    r"(?:i am|i'm|i will be) (?:out of (?:the )?office|away|on leave)",
    r"(?:automatic reply|auto-?reply|away message)",
    r"(?:currently (?:out of|away from) the office)",
    r"(?:not in the office|not available)",
]

# Return date patterns
RETURN_DATE_PATTERNS = [
    r"(?:return(?:ing)?|back|available) (?:on|from)?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
    r"(?:return(?:ing)?|back|available) (?:on|from)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{2,4}?)",
    r"(?:until|till)\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
    r"(?:until|till)\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)",
]

# Left company patterns
LEFT_COMPANY_PATTERNS = [
    r"(?:no longer (?:works?|employed|with)|has left|left the company|moved on)",
    r"(?:is no longer at|no longer with|departed from)",
    r"(?:this email address is no longer (?:valid|active|monitored))",
    r"(?:this mailbox is no longer (?:active|monitored|in use))",
    r"(?:user (?:has )?left|account (?:has been )?(?:disabled|deactivated))",
]

# Email extraction pattern
EMAIL_PATTERN = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"

# Contact handoff patterns
HANDOFF_PATTERNS = [
    r"(?:please contact|reach out to|email|contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:at|on)?\s*<?(" + EMAIL_PATTERN + r")>?",
    r"(?:forward(?:ed)?|redirect(?:ed)?)\s+to\s+<?(" + EMAIL_PATTERN + r")>?",
    r"(?:my new email|new email address|reach me at)\s+<?(" + EMAIL_PATTERN + r")>?",
]


def parse_auto_reply(text: str) -> AutoReplyResult:
    """Parse an auto-reply email to extract intelligence.

    Detects:
    - Out of Office (OOO) with return dates
    - Left company notices with forwarding emails
    - New contact information (replacements)

    Parameters
    ----------
    text : str
        The auto-reply email body text.

    Returns
    -------
    AutoReplyResult
        Parsed information from the auto-reply.
    """
    text_lower = text.lower()
    result = AutoReplyResult(
        type="unknown",
        return_date=None,
        forwarding_email=None,
        new_contact_name=None,
        new_contact_email=None,
        raw_text=text,
    )

    # Check for OOO
    for pattern in OOO_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            result.type = "ooo"

            # Try to extract return date
            for date_pattern in RETURN_DATE_PATTERNS:
                match = re.search(date_pattern, text_lower, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        # Try common date formats
                        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y",
                                    "%d/%m/%y", "%m/%d/%y", "%d %B %Y", "%d %b %Y",
                                    "%d %B", "%d %b"]:
                            try:
                                result.return_date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                    break
            break

    # Check for left company
    for pattern in LEFT_COMPANY_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            result.type = "left_company"
            break

    # Extract forwarding email and new contact
    for pattern in HANDOFF_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            for g in groups:
                if g and "@" in g:
                    if not result.forwarding_email:
                        result.forwarding_email = g.strip("<>").lower()
                elif g and len(g) > 2:
                    result.new_contact_name = g

    # Fallback: find any email in the text that isn't the original
    if not result.forwarding_email:
        emails = re.findall(EMAIL_PATTERN, text)
        if emails:
            # Take the first email that looks like a person (not noreply, etc.)
            for email in emails:
                email_lower = email.lower()
                if not any(p in email_lower for p in ["noreply", "no-reply", "donotreply", "mailer-daemon"]):
                    result.forwarding_email = email_lower
                    break

    return result


# ---------------------------------------------------------------------------
# Email Validation Tracker
# ---------------------------------------------------------------------------

class EmailValidator:
    """Tracks email validation attempts and results.

    Integrates with ContactsDB to:
    - Generate email patterns for unvalidated contacts
    - Record validation attempts (tested patterns)
    - Mark emails as valid/invalid
    - Process auto-replies to extract intelligence
    """

    def __init__(self, contacts_db: Any = None):
        """Initialize with optional ContactsDB reference."""
        self.contacts_db = contacts_db
        self.validation_queue: list[dict] = []  # Pending validations

    def get_patterns_for_contact(self, contact: dict[str, Any]) -> list[EmailPattern]:
        """Get untested email patterns for a contact.

        Parameters
        ----------
        contact : dict
            Contact record from ContactsDB.

        Returns
        -------
        list[EmailPattern]
            Patterns that haven't been tested yet.
        """
        first_name = contact.get("first_name", "")
        last_name = contact.get("last_name", "")
        domain = contact.get("domain", "")
        company = contact.get("company", "")

        # Get all possible patterns
        if domain:
            patterns = generate_email_patterns(first_name, last_name, domain)
        elif company:
            patterns = generate_patterns_with_tlds(first_name, last_name, company)
        else:
            return []

        # Filter out already-tested patterns
        tested = {
            a.get("pattern") for a in contact.get("validation_attempts", [])
        }
        return [p for p in patterns if p.pattern_name not in tested]

    def record_validation_attempt(
        self,
        contact_id: str,
        pattern: EmailPattern,
        result: str,  # "valid", "bounced", "unknown"
    ) -> dict[str, Any] | None:
        """Record a validation attempt for a contact.

        Parameters
        ----------
        contact_id : str
            Contact ID.
        pattern : EmailPattern
            The pattern that was tested.
        result : str
            "valid", "bounced", or "unknown".

        Returns
        -------
        dict | None
            Updated contact record, or None if not found.
        """
        if not self.contacts_db:
            logger.warning("No ContactsDB connected to EmailValidator")
            return None

        rec = self.contacts_db.contacts.get(contact_id)
        if rec is None:
            return None

        # Add validation attempt
        attempt = {
            "pattern": pattern.pattern_name,
            "email_tested": pattern.email,
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
        }

        if "validation_attempts" not in rec:
            rec["validation_attempts"] = []
        rec["validation_attempts"].append(attempt)

        # Update email validation status
        if result == "valid":
            rec["email_validated"] = True
            rec["email_validation_date"] = datetime.now(timezone.utc).isoformat()
            rec["email"] = pattern.email  # Update to validated email
            rec["pattern_used"] = pattern.pattern_name
        elif result == "bounced":
            # Check if all patterns exhausted
            all_patterns = self.get_patterns_for_contact(rec)
            if not all_patterns:
                rec["email_validated"] = False
                rec["email_invalid_reason"] = "pattern_exhausted"
                rec["email_validation_date"] = datetime.now(timezone.utc).isoformat()

        rec["updated_at"] = self.contacts_db._now()
        self.contacts_db.save()

        return rec

    def process_auto_reply(
        self,
        contact_id: str,
        auto_reply_text: str,
    ) -> dict[str, Any]:
        """Process an auto-reply and update contact + create new contacts.

        Parameters
        ----------
        contact_id : str
            The contact who sent the auto-reply.
        auto_reply_text : str
            The auto-reply message body.

        Returns
        -------
        dict
            {
                "parsed": AutoReplyResult,
                "original_contact_updated": bool,
                "new_contact_created": str | None,  # New contact ID if created
            }
        """
        result = {
            "parsed": None,
            "original_contact_updated": False,
            "new_contact_created": None,
        }

        # Parse the auto-reply
        parsed = parse_auto_reply(auto_reply_text)
        result["parsed"] = parsed

        if not self.contacts_db:
            return result

        rec = self.contacts_db.contacts.get(contact_id)
        if rec is None:
            return result

        # Update original contact
        rec["auto_reply_detected"] = datetime.now(timezone.utc).isoformat()

        if parsed.type == "ooo":
            if parsed.return_date:
                rec["out_of_office_until"] = parsed.return_date.isoformat()
            logger.info("Contact %s is OOO until %s", contact_id, parsed.return_date)

        elif parsed.type == "left_company":
            rec["left_company_date"] = datetime.now(timezone.utc).isoformat()
            rec["tags"] = list(set(rec.get("tags", [])) | {"left_company"})

            if parsed.forwarding_email:
                rec["forwarding_email"] = parsed.forwarding_email
                # Don't demote if we have a forwarding address
                logger.info(
                    "Contact %s left company, forwarding to %s",
                    contact_id, parsed.forwarding_email
                )
            else:
                logger.info("Contact %s left company, no forwarding email", contact_id)

        # Create new contact from forwarding email
        if parsed.forwarding_email:
            existing = self.contacts_db.get_by_email(parsed.forwarding_email)
            if not existing:
                # Extract name from email if possible
                new_first = ""
                new_last = ""
                if parsed.new_contact_name:
                    parts = parsed.new_contact_name.split()
                    new_first = parts[0] if parts else ""
                    new_last = parts[-1] if len(parts) > 1 else ""
                else:
                    # Try to parse from email local part
                    local = parsed.forwarding_email.split("@")[0]
                    if "." in local:
                        parts = local.split(".")
                        new_first = parts[0].title()
                        new_last = parts[-1].title()

                # Get domain from forwarding email
                new_domain = parsed.forwarding_email.split("@")[-1] if "@" in parsed.forwarding_email else ""

                # Create the new contact
                new_contact = self.contacts_db.add_verified(
                    email=parsed.forwarding_email,
                    first_name=new_first,
                    last_name=new_last,
                    company=rec.get("company", ""),
                    domain=new_domain,
                    source=f"auto_reply_forward:{contact_id}",
                )
                if new_contact:
                    result["new_contact_created"] = new_contact["id"]
                    # Add note linking to original contact
                    new_contact["notes"] = f"Auto-discovered from {rec.get('email')} auto-reply"
                    logger.info(
                        "Created new contact %s from auto-reply: %s",
                        new_contact["id"], parsed.forwarding_email
                    )

        # Reclassify the original contact
        tier, reason = self.contacts_db.classify_trust_tier(rec)
        rec["trust_tier"] = tier
        rec["tier_reason"] = reason
        rec["updated_at"] = self.contacts_db._now()

        self.contacts_db.save()
        result["original_contact_updated"] = True

        return result

    def get_validation_stats(self) -> dict[str, Any]:
        """Get statistics on email validation across all contacts.

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
        if not self.contacts_db:
            return {}

        stats = {
            "total_contacts": 0,
            "validated": 0,
            "invalid": 0,
            "unvalidated": 0,
            "patterns_tested": 0,
            "ooo_detected": 0,
            "left_company": 0,
            "forwarding_captured": 0,
        }

        for rec in self.contacts_db.contacts.values():
            stats["total_contacts"] += 1

            if rec.get("email_validated") is True:
                stats["validated"] += 1
            elif rec.get("email_validated") is False:
                stats["invalid"] += 1
            else:
                stats["unvalidated"] += 1

            stats["patterns_tested"] += len(rec.get("validation_attempts", []))

            if rec.get("out_of_office_until"):
                stats["ooo_detected"] += 1

            if rec.get("left_company_date"):
                stats["left_company"] += 1

            if rec.get("forwarding_email"):
                stats["forwarding_captured"] += 1

        return stats


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def validate_email_patterns(
    first_name: str,
    last_name: str,
    domain: str,
) -> list[dict[str, Any]]:
    """Generate email patterns for manual testing.

    Returns a list of dicts suitable for API response.
    """
    patterns = generate_email_patterns(first_name, last_name, domain)
    return [
        {
            "email": p.email,
            "pattern": p.pattern_name,
            "priority": p.priority,
        }
        for p in patterns
    ]


# ---------------------------------------------------------------------------
# CLI / Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("  Email Validator - Demo")
    print("=" * 70)

    # Demo pattern generation
    print("\n1. Email Pattern Generation")
    patterns = generate_email_patterns("John", "Smith", "acme.com")
    for p in patterns:
        print(f"   [{p.priority}] {p.pattern_name}: {p.email}")

    # Demo auto-reply parsing
    print("\n2. Auto-Reply Parsing")

    ooo_text = """
    Thank you for your email. I am currently out of the office and will
    return on 15/03/2026. For urgent matters, please contact Sarah Jones
    at sarah.jones@acme.com.
    """
    result = parse_auto_reply(ooo_text)
    print(f"   Type: {result.type}")
    print(f"   Return date: {result.return_date}")
    print(f"   Forwarding: {result.forwarding_email}")
    print(f"   New contact: {result.new_contact_name}")

    left_text = """
    This mailbox is no longer active. John Smith has left the company.
    Please reach out to mike.brown@acme.com for assistance.
    """
    result = parse_auto_reply(left_text)
    print(f"\n   Type: {result.type}")
    print(f"   Forwarding: {result.forwarding_email}")

    print("\n" + "=" * 70)
