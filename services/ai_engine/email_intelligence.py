"""
Corporate Email Pattern Intelligence Engine
============================================

Learns email naming patterns from verified email data, then generates
probable email addresses for contacts where we have name + company but
no known email.

Data sources:
    - master_email_list.json  → flat list of all extracted emails
    - email_*.json            → individual parsed email files with
                                 sender / to / cc / subject / body

Usage:
    engine = EmailIntelligence()
    loaded = engine.load_verified_emails()
    engine.learn_patterns()
    guesses = engine.guess_email("Tony", "Ryan", "Amgen")
"""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default data root
# ---------------------------------------------------------------------------
DEFAULT_DATA_ROOT = Path(os.getenv("CAREERTROJAN_AI_DATA", os.path.join(os.getenv("CAREERTROJAN_DATA_ROOT", "./data"), "ai_data_final")))
DEFAULT_PATTERN_FILE = "email_patterns.json"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FREE_PROVIDERS: set[str] = {
    "gmail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "yahoo.co.in",
    "yahoo.fr",
    "yahoo.de",
    "hotmail.com",
    "hotmail.co.uk",
    "hotmail.fr",
    "hotmail.de",
    "outlook.com",
    "outlook.co.uk",
    "aol.com",
    "aol.co.uk",
    "live.com",
    "live.co.uk",
    "live.fr",
    "icloud.com",
    "me.com",
    "mac.com",
    "mail.com",
    "protonmail.com",
    "proton.me",
    "gmx.com",
    "gmx.net",
    "gmx.de",
    "ymail.com",
    "msn.com",
    "btinternet.com",
    "sky.com",
    "virginmedia.com",
    "talktalk.net",
    "ntlworld.com",
    "plus.net",
    "blueyonder.co.uk",
    "tiscali.co.uk",
    "wanadoo.fr",
    "laposte.net",
    "libero.it",
    "mail.ru",
    "yandex.ru",
    "web.de",
    "t-online.de",
    "bluewin.ch",
    "comcast.net",
    "sbcglobal.net",
    "att.net",
    "verizon.net",
    "cox.net",
    "charter.net",
    "earthlink.net",
    "optonline.net",
    "aim.com",
    "zoho.com",
    "fastmail.com",
    "hushmail.com",
    "rocketmail.com",
    "inbox.com",
    "rediffmail.com",
    "163.com",
    "126.com",
    "qq.com",
    "naver.com",
    "daum.net",
    "uwclub.net",
    "rgn.hr",
}

# ---------------------------------------------------------------------------
# Valid TLDs for domain validation & candidate generation
# Sourced from email domains.txt reference file (Wikipedia IANA list)
# ---------------------------------------------------------------------------
COMMON_TLDS: tuple[str, ...] = (
    # Generic
    ".com", ".net", ".org", ".info", ".biz",
    # Tech-centric
    ".io", ".ai", ".tech", ".dev", ".app", ".co",
    # Business
    ".pro", ".inc", ".llc", ".ltd", ".gmbh",
    # Commerce
    ".shop", ".store", ".online", ".xyz",
    # UK
    ".co.uk", ".org.uk", ".me.uk", ".ltd.uk",
    # Europe
    ".de", ".fr", ".nl", ".es", ".it", ".se", ".no", ".fi", ".dk",
    ".at", ".ch", ".be", ".pt", ".ie", ".pl", ".cz", ".ro", ".hu",
    ".bg", ".hr", ".sk", ".si", ".lt", ".lv", ".ee",
    # Americas
    ".us", ".ca", ".com.br", ".com.mx", ".com.ar", ".com.co",
    # Asia-Pacific
    ".com.au", ".co.nz", ".co.jp", ".co.kr", ".com.cn", ".cn",
    ".com.sg", ".co.in", ".com.hk", ".com.tw",
    # Middle East / Africa
    ".ae", ".sa", ".co.za", ".com.ng", ".co.ke",
    # Global / misc
    ".eu", ".asia", ".global", ".international",
)

# Country-code to common corporate TLD(s) — for region-aware inference
COUNTRY_TLDS: dict[str, tuple[str, ...]] = {
    "uk": (".co.uk", ".com"),
    "gb": (".co.uk", ".com"),
    "us": (".com", ".us"),
    "de": (".de", ".com"),
    "fr": (".fr", ".com"),
    "nl": (".nl", ".com"),
    "au": (".com.au", ".com"),
    "in": (".co.in", ".com"),
    "jp": (".co.jp", ".com"),
    "nz": (".co.nz", ".com"),
    "za": (".co.za", ".com"),
    "ie": (".ie", ".com"),
    "se": (".se", ".com"),
    "no": (".no", ".com"),
    "dk": (".dk", ".com"),
    "ch": (".ch", ".com"),
    "it": (".it", ".com"),
    "es": (".es", ".com"),
    "pt": (".pt", ".com"),
    "be": (".be", ".com"),
    "at": (".at", ".com"),
    "br": (".com.br", ".com"),
    "cn": (".com.cn", ".cn", ".com"),
}

# Honorifics / titles to strip from display names
_TITLES = {
    "mr", "mrs", "ms", "miss", "dr", "prof", "professor",
    "sir", "lord", "lady", "rev", "reverend", "hon", "honorable",
    "eng", "engr", "ir", "ing",
}

# All pattern names in priority order (most common first)
PATTERN_NAMES: list[str] = [
    "first.last",
    "firstlast",
    "f.last",
    "flast",
    "first",
    "last.first",
    "first_last",
    "first-last",
    "lastf",
    "last",
]

# Default fallback pattern ranking when we have zero evidence for a domain.
# Weights approximate how common each pattern is across all corporations.
_DEFAULT_PATTERN_WEIGHTS: dict[str, float] = {
    "first.last": 0.50,
    "flast": 0.15,
    "f.last": 0.10,
    "firstlast": 0.08,
    "first_last": 0.05,
    "first-last": 0.04,
    "first": 0.03,
    "last.first": 0.02,
    "lastf": 0.02,
    "last": 0.01,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase, strip accents, remove non-alpha characters."""
    text = text.strip().lower()
    # Decompose unicode → strip combining marks (accents)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _alpha_only(text: str) -> str:
    """Return only ASCII alpha chars, lowered."""
    return re.sub(r"[^a-z]", "", _normalize(text))


# Regex to pull email from  "Display Name <email>"  or bare email
_EMAIL_FIELD_RE = re.compile(
    r"""
    (?:                        # optional display-name part
        (?P<display>[^<]+)     #   everything before <
        \s*<\s*                #   opening <
        (?P<email_in_angle>[^\s>]+@[^\s>]+)
        \s*>                   #   closing >
    )
    |
    (?P<bare_email>[^\s;,<>]+@[^\s;,<>]+)   # bare email
    """,
    re.VERBOSE,
)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class EmailIntelligence:
    """Corporate email pattern intelligence engine.

    Learns naming-convention patterns from verified email data and uses
    them to generate probable email addresses for new contacts.
    """

    def __init__(self, data_root: Path | None = None) -> None:
        self.data_root: Path = Path(data_root) if data_root else DEFAULT_DATA_ROOT
        self.email_extracted_dir: Path = self.data_root / "email_extracted"

        # Pattern registry: domain → {pattern_name: count}
        self.domain_patterns: dict[str, dict[str, int]] = {}

        # Verified contacts: [{email, name, first_name, last_name, domain, source}]
        self.verified_contacts: list[dict[str, Any]] = []

        # domain → company name (learned from data)
        self.domain_to_company: dict[str, str] = {}

        # company name (lower) → domain (reverse of above, for inference)
        self._company_to_domain: dict[str, str] = {}

        logger.info(
            "EmailIntelligence initialised — data_root=%s", self.data_root
        )

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_verified_emails(self) -> int:
        """Load verified emails from master list AND individual email JSONs.

        Returns the total number of verified contacts loaded.
        """
        count_before = len(self.verified_contacts)

        self._load_master_list()
        self._load_individual_emails()

        loaded = len(self.verified_contacts) - count_before
        logger.info("Loaded %d verified contacts total.", loaded)
        return loaded

    def _load_master_list(self) -> None:
        """Parse master_email_list.json — a flat list of email addresses.

        We can't derive *names* from this file, but we can register every
        domain we see and add bare-email contacts for pattern counting later.
        """
        master_path = self.email_extracted_dir / "master_email_list.json"
        if not master_path.exists():
            logger.warning("Master email list not found at %s", master_path)
            return

        try:
            data = json.loads(master_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read master_email_list.json: %s", exc)
            return

        emails: list[str] = data.get("emails", [])
        logger.info(
            "master_email_list.json: %d unique emails reported, %d in list.",
            data.get("total_unique_emails", 0),
            len(emails),
        )

        for raw in emails:
            email = raw.strip().lower()
            if not self._looks_like_email(email):
                continue

            local, domain = email.rsplit("@", 1)
            if domain in FREE_PROVIDERS:
                continue

            self.verified_contacts.append(
                {
                    "email": email,
                    "name": "",
                    "first_name": "",
                    "last_name": "",
                    "domain": domain,
                    "source": "master_list",
                }
            )
            # We don't know the company name yet — will be enriched later
            # from individual emails that share the same domain.

    def _load_individual_emails(self) -> None:
        """Parse every email_*.json in the extracted directory.

        These files contain sender / to / cc with display names, giving us
        the name ↔ email ↔ domain associations needed for pattern learning.
        """
        if not self.email_extracted_dir.exists():
            logger.warning("email_extracted dir not found: %s", self.email_extracted_dir)
            return

        json_files = sorted(self.email_extracted_dir.glob("email_*.json"))
        logger.info("Found %d individual email JSON files.", len(json_files))

        for fp in json_files:
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.debug("Skipping %s: %s", fp.name, exc)
                continue

            # Extract contacts from sender, to, cc fields
            for field_name in ("sender", "to", "cc"):
                raw_field = data.get(field_name)
                if not raw_field:
                    continue
                self._extract_contacts_from_field(
                    str(raw_field), source=f"email_json:{fp.name}"
                )

    def _extract_contacts_from_field(self, field: str, source: str) -> None:
        """Parse one header field (possibly semicolon/comma-separated) and
        add each address as a verified contact."""
        # Split on ; or , to handle multiple recipients
        parts = re.split(r"[;,]", field)
        for part in parts:
            part = part.strip()
            if not part:
                continue

            display_name, email_addr = self._parse_email_from_field(part)
            if not email_addr:
                continue

            email_addr = email_addr.lower().strip()
            if not self._looks_like_email(email_addr):
                continue

            _local, domain = email_addr.rsplit("@", 1)

            first_name, last_name = "", ""
            if display_name:
                first_name, last_name = self._parse_name_from_display(display_name)

            # Learn domain→company from display-name context if corporate
            if domain not in FREE_PROVIDERS and display_name:
                self._maybe_learn_company(domain, display_name, source)

            self.verified_contacts.append(
                {
                    "email": email_addr,
                    "name": display_name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "domain": domain,
                    "source": source,
                }
            )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_email_from_field(field: str) -> tuple[str, str]:
        """Extract (display_name, email_address) from a header value.

        Handles:
            "John Smith <john.smith@acme.com>"
            "<john.smith@acme.com>"
            "john.smith@acme.com"

        Returns ``('', '')`` when nothing can be parsed.
        """
        field = field.strip()
        if not field:
            return ("", "")

        m = _EMAIL_FIELD_RE.search(field)
        if not m:
            return ("", "")

        if m.group("email_in_angle"):
            display = (m.group("display") or "").strip().strip('"').strip("'")
            return (display, m.group("email_in_angle"))

        bare = m.group("bare_email")
        if bare:
            return ("", bare)

        return ("", "")

    @staticmethod
    def _parse_name_from_display(display: str) -> tuple[str, str]:
        """Extract (first_name, last_name) from a display name.

        Handles:
            "John Smith"
            "Dr. John A. Smith"
            "Smith, John"
            "JOHN SMITH"
            "John"
            "John Smith-Jones"
        """
        if not display:
            return ("", "")

        name = display.strip().strip('"').strip("'")

        # Handle "Last, First" → "First Last"
        if "," in name:
            parts = [p.strip() for p in name.split(",", 1)]
            if len(parts) == 2 and parts[1]:
                name = f"{parts[1]} {parts[0]}"

        # Tokenise
        tokens = name.split()
        if not tokens:
            return ("", "")

        # Strip titles / honorifics
        cleaned: list[str] = []
        for tok in tokens:
            low = tok.lower().rstrip(".")
            if low in _TITLES:
                continue
            # Skip single-letter middle initials (e.g., "A.", "J")
            if len(tok.rstrip(".")) == 1 and cleaned:
                continue
            cleaned.append(tok)

        if not cleaned:
            # Everything was stripped — fall back to original tokens
            cleaned = tokens

        first = cleaned[0] if cleaned else ""
        last = cleaned[-1] if len(cleaned) > 1 else ""

        return (_normalize(first), _normalize(last))

    @staticmethod
    def _looks_like_email(addr: str) -> bool:
        """Quick sanity check — must have exactly one @ and a dot in domain."""
        if addr.count("@") != 1:
            return False
        local, domain = addr.rsplit("@", 1)
        if not local or not domain:
            return False
        if "." not in domain:
            return False
        # Reject obviously broken addresses
        if domain.startswith(".") or domain.endswith("."):
            return False
        return True

    # ------------------------------------------------------------------
    # Domain → company learning
    # ------------------------------------------------------------------

    def _maybe_learn_company(self, domain: str, display: str, source: str) -> None:
        """Heuristically associate a domain with a company name.

        We only record the mapping if we don't already have one, and only
        from individual-email sources (where display names are trustworthy).
        """
        if domain in self.domain_to_company:
            return
        if not source.startswith("email_json:"):
            return

        # The display name itself isn't the company, but the *domain* often
        # encodes it.  We derive a readable company from the domain.
        company_guess = domain.split(".")[0]
        # Capitalise nicely
        company_guess = company_guess.replace("-", " ").replace("_", " ").title()
        self.domain_to_company[domain] = company_guess
        self._company_to_domain[company_guess.lower()] = domain

    # ------------------------------------------------------------------
    # Pattern learning
    # ------------------------------------------------------------------

    def learn_patterns(self) -> dict[str, dict[str, int]]:
        """Analyse verified contacts to build per-domain pattern counts.

        Only considers contacts where we have *both* a name and a corporate
        email address.

        Returns ``self.domain_patterns``.
        """
        self.domain_patterns.clear()

        for contact in self.verified_contacts:
            domain = contact["domain"]
            first = contact.get("first_name", "")
            last = contact.get("last_name", "")
            email = contact["email"]

            if domain in FREE_PROVIDERS:
                continue
            if not first or not last:
                continue

            pattern = self._detect_pattern(email, first, last)
            if pattern is None:
                continue

            self.domain_patterns.setdefault(domain, {})
            self.domain_patterns[domain].setdefault(pattern, 0)
            self.domain_patterns[domain][pattern] += 1

        logger.info(
            "Learned patterns for %d corporate domains.", len(self.domain_patterns)
        )
        return self.domain_patterns

    def _detect_pattern(
        self, email: str, first_name: str, last_name: str
    ) -> str | None:
        """Determine which naming pattern an email uses given the person's name.

        Returns a pattern name string or ``None`` if it cannot be matched.
        """
        if "@" not in email:
            return None

        local = email.rsplit("@", 1)[0].lower()
        first = _alpha_only(first_name)
        last = _alpha_only(last_name)

        if not first or not last:
            return None

        f_initial = first[0]
        l_initial = last[0]

        # Check each pattern explicitly (order matters — most specific first)
        checks: list[tuple[str, str]] = [
            ("first.last",  f"{first}.{last}"),
            ("last.first",  f"{last}.{first}"),
            ("first_last",  f"{first}_{last}"),
            ("first-last",  f"{first}-{last}"),
            ("f.last",      f"{f_initial}.{last}"),
            ("flast",       f"{f_initial}{last}"),
            ("lastf",       f"{last}{f_initial}"),
            ("firstlast",   f"{first}{last}"),
            ("first",       first),
            ("last",        last),
        ]

        for pattern_name, expected_local in checks:
            if local == expected_local:
                return pattern_name

        # Handle hyphenated last names: e.g. "Smith-Jones" → try both parts
        if "-" in last_name:
            last_parts = [_alpha_only(p) for p in last_name.split("-")]
            joined_last = "".join(last_parts)
            hyph_last = "-".join(last_parts)
            dot_last = ".".join(last_parts)

            extra_checks: list[tuple[str, str]] = [
                ("first.last",  f"{first}.{joined_last}"),
                ("first.last",  f"{first}.{hyph_last}"),
                ("first.last",  f"{first}.{dot_last}"),
                ("flast",       f"{f_initial}{joined_last}"),
                ("f.last",      f"{f_initial}.{joined_last}"),
                ("firstlast",   f"{first}{joined_last}"),
            ]
            for pattern_name, expected_local in extra_checks:
                if local == expected_local:
                    return pattern_name

        # Handle hyphenated first names similarly
        if "-" in first_name:
            first_parts = [_alpha_only(p) for p in first_name.split("-")]
            joined_first = "".join(first_parts)
            extra_checks2: list[tuple[str, str]] = [
                ("first.last",  f"{joined_first}.{last}"),
                ("firstlast",   f"{joined_first}{last}"),
                ("flast",       f"{joined_first[0]}{last}" if joined_first else ""),
            ]
            for pattern_name, expected_local in extra_checks2:
                if expected_local and local == expected_local:
                    return pattern_name

        return None

    # ------------------------------------------------------------------
    # Email guessing
    # ------------------------------------------------------------------

    def guess_email(
        self,
        first_name: str,
        last_name: str,
        company: str,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate probable email addresses for a person at a company.

        Parameters
        ----------
        first_name : str
        last_name : str
        company : str
            Company name (used for domain inference if *domain* is ``None``).
        domain : str, optional
            If known, the corporate email domain.

        Returns
        -------
        list[dict]
            Each dict: ``{email, pattern, confidence, domain}``,
            sorted by descending confidence.
        """
        first = _normalize(first_name)
        last = _normalize(last_name)
        f_initial = first[0] if first else ""
        l_initial = last[0] if last else ""

        if not first or not last:
            logger.warning(
                "Cannot guess email — need both first and last name "
                "(got first=%r, last=%r).",
                first_name,
                last_name,
            )
            return []

        # Resolve domain(s)
        domains: list[str] = []
        if domain:
            domains = [domain.lower().strip()]
        else:
            domains = self._infer_domain(company)

        if not domains:
            logger.warning(
                "Could not determine domain for company %r.", company
            )
            return []

        results: list[dict[str, Any]] = []

        for dom in domains:
            dom_patterns = self.domain_patterns.get(dom)

            if dom_patterns:
                total_hits = sum(dom_patterns.values())
                # Sort patterns by frequency descending
                sorted_patterns = sorted(
                    dom_patterns.items(), key=lambda kv: kv[1], reverse=True
                )
                top_pattern, top_count = sorted_patterns[0]
                top_ratio = top_count / total_hits if total_hits else 0.0

                for rank, (pat, count) in enumerate(sorted_patterns):
                    ratio = count / total_hits if total_hits else 0.0
                    confidence = self._compute_confidence(
                        rank=rank,
                        ratio=ratio,
                        top_ratio=top_ratio,
                        total_hits=total_hits,
                        is_known_domain=True,
                    )
                    addr = self._build_address(first, last, f_initial, pat, dom)
                    if addr:
                        results.append(
                            {
                                "email": addr,
                                "pattern": pat,
                                "confidence": round(confidence, 3),
                                "domain": dom,
                            }
                        )
            else:
                # Unknown domain — emit fallback guesses
                for pat, weight in _DEFAULT_PATTERN_WEIGHTS.items():
                    confidence = self._compute_confidence(
                        rank=None,
                        ratio=weight,
                        top_ratio=None,
                        total_hits=0,
                        is_known_domain=False,
                    )
                    addr = self._build_address(first, last, f_initial, pat, dom)
                    if addr:
                        results.append(
                            {
                                "email": addr,
                                "pattern": pat,
                                "confidence": round(confidence, 3),
                                "domain": dom,
                            }
                        )

        # De-duplicate (same email can appear from multiple domains/patterns)
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for r in results:
            key = r["email"]
            if key not in seen:
                seen.add(key)
                unique.append(r)

        unique.sort(key=lambda r: r["confidence"], reverse=True)
        return unique

    def guess_batch(self, contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Batch-guess emails for a list of contacts.

        Each contact dict should have:
            ``first_name``, ``last_name``, ``company``, and optionally ``domain``.

        Returns the same dicts enriched with ``guessed_emails`` (list) and
        ``top_guess`` (str or ``None``).
        """
        enriched: list[dict[str, Any]] = []
        for contact in contacts:
            guesses = self.guess_email(
                first_name=contact.get("first_name", ""),
                last_name=contact.get("last_name", ""),
                company=contact.get("company", ""),
                domain=contact.get("domain"),
            )
            out = dict(contact)
            out["guessed_emails"] = guesses
            out["top_guess"] = guesses[0]["email"] if guesses else None
            out["top_confidence"] = guesses[0]["confidence"] if guesses else 0.0
            enriched.append(out)

        return enriched

    # ------------------------------------------------------------------
    # Confidence scoring
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_confidence(
        *,
        rank: int | None,
        ratio: float,
        top_ratio: float | None,
        total_hits: int,
        is_known_domain: bool,
    ) -> float:
        """Compute a confidence score for a single email guess.

        Scoring rules (from spec):
            0.95 — known domain, this pattern matches ≥80% of verified emails
            0.85 — known domain, this is the #1 pattern (but <80%)
            0.70 — known domain, secondary patterns
            0.50 — unknown domain, first.last fallback
            0.30 — unknown domain, other fallback patterns
        """
        if is_known_domain and total_hits > 0:
            if ratio >= 0.80:
                return 0.95
            if rank == 0:
                # Most common but <80%
                return 0.85
            # Known domain, not the top pattern
            # Scale between 0.55 and 0.75 based on ratio
            return max(0.55, min(0.75, 0.55 + ratio * 0.40))

        # Unknown domain — fallback
        if ratio >= 0.40:
            return 0.50
        return 0.30

    # ------------------------------------------------------------------
    # Address construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_address(
        first: str, last: str, f_initial: str, pattern: str, domain: str
    ) -> str | None:
        """Build an email address from name components and a pattern."""
        local: str | None = None
        l_initial = last[0] if last else ""

        match pattern:
            case "first.last":
                local = f"{first}.{last}"
            case "firstlast":
                local = f"{first}{last}"
            case "f.last":
                local = f"{f_initial}.{last}"
            case "flast":
                local = f"{f_initial}{last}"
            case "first":
                local = first
            case "last.first":
                local = f"{last}.{first}"
            case "first_last":
                local = f"{first}_{last}"
            case "first-last":
                local = f"{first}-{last}"
            case "lastf":
                local = f"{last}{f_initial}"
            case "last":
                local = last
            case _:
                return None

        if not local:
            return None

        # Ensure only valid email chars
        local = re.sub(r"[^a-z0-9._\-]", "", local)
        if not local:
            return None

        return f"{local}@{domain}"

    # ------------------------------------------------------------------
    # Domain inference
    # ------------------------------------------------------------------

    def _infer_domain(self, company: str) -> list[str]:
        """Infer probable corporate domain(s) from a company name.

        Strategy:
            1. Check our learned domain_to_company map (reverse lookup).
            2. Generate candidates: company.com, company.co.uk, etc.
            3. Return any candidates that match known domains first,
               then the generated ones.

        Returns a list of domain strings (best first).
        """
        if not company:
            return []

        company_lower = company.strip().lower()
        company_clean = re.sub(r"[^a-z0-9 ]", "", company_lower).strip()

        # 1. Exact reverse-lookup
        if company_lower in self._company_to_domain:
            return [self._company_to_domain[company_lower]]

        # Also try cleaned version
        if company_clean in self._company_to_domain:
            return [self._company_to_domain[company_clean]]

        # 2. Check all known domain_to_company values for a fuzzy match
        for domain, comp_name in self.domain_to_company.items():
            if comp_name.lower() == company_lower or comp_name.lower() == company_clean:
                return [domain]

        # 3. Generate candidate domains using comprehensive TLD list
        slug_nospace = company_clean.replace(" ", "")
        slug_hyphen = company_clean.replace(" ", "-")
        slug_dot = company_clean.replace(" ", ".")

        candidates: list[str] = []
        # Primary TLDs to try (most common corporate domains)
        primary_tlds = (".com", ".co.uk", ".io", ".co", ".net", ".org")
        for slug in dict.fromkeys([slug_nospace, slug_hyphen, slug_dot]):
            for tld in primary_tlds:
                candidates.append(f"{slug}{tld}")

        # Promote any candidate that we've actually seen in verified data
        known_domains = {c["domain"] for c in self.verified_contacts}
        promoted: list[str] = [d for d in candidates if d in known_domains]
        remaining: list[str] = [d for d in candidates if d not in known_domains]

        return promoted + remaining

    def validate_domain_tld(self, domain: str) -> bool:
        """Check if a domain ends with a recognised TLD from the reference list."""
        domain = domain.lower().strip()
        for tld in COMMON_TLDS:
            if domain.endswith(tld):
                return True
        return False

    # ------------------------------------------------------------------
    # Statistics & reporting
    # ------------------------------------------------------------------

    def get_domain_stats(self) -> dict[str, Any]:
        """Return statistics about learned patterns.

        Returns a dict with:
            - ``total_domains``: number of corporate domains with patterns
            - ``total_verified_contacts``: count of all loaded contacts
            - ``corporate_contacts``: contacts on non-free domains
            - ``domains``: list of {domain, company, patterns, total_emails}
              sorted by total_emails descending
        """
        corporate = [
            c for c in self.verified_contacts if c["domain"] not in FREE_PROVIDERS
        ]

        domain_info: list[dict[str, Any]] = []
        for domain, patterns in sorted(
            self.domain_patterns.items(),
            key=lambda kv: sum(kv[1].values()),
            reverse=True,
        ):
            domain_info.append(
                {
                    "domain": domain,
                    "company": self.domain_to_company.get(domain, ""),
                    "patterns": patterns,
                    "total_emails": sum(patterns.values()),
                    "primary_pattern": max(patterns, key=patterns.get)  # type: ignore[arg-type]
                    if patterns
                    else None,
                }
            )

        return {
            "total_domains": len(self.domain_patterns),
            "total_verified_contacts": len(self.verified_contacts),
            "corporate_contacts": len(corporate),
            "domains": domain_info,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_patterns(self, filepath: Path | None = None) -> None:
        """Save learned patterns, domain→company map, and stats to JSON."""
        fp = filepath or (self.data_root / DEFAULT_PATTERN_FILE)
        payload = {
            "domain_patterns": self.domain_patterns,
            "domain_to_company": self.domain_to_company,
            "stats": {
                "total_domains": len(self.domain_patterns),
                "total_verified_contacts": len(self.verified_contacts),
            },
        }
        fp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Patterns saved to %s", fp)

    def load_patterns(self, filepath: Path | None = None) -> None:
        """Load previously saved patterns from JSON."""
        fp = filepath or (self.data_root / DEFAULT_PATTERN_FILE)
        if not fp.exists():
            logger.warning("Pattern file not found: %s", fp)
            return

        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load patterns from %s: %s", fp, exc)
            return

        self.domain_patterns = data.get("domain_patterns", {})
        self.domain_to_company = data.get("domain_to_company", {})
        # Rebuild reverse map
        self._company_to_domain = {
            v.lower(): k for k, v in self.domain_to_company.items()
        }
        logger.info(
            "Loaded patterns for %d domains from %s.",
            len(self.domain_patterns),
            fp,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise engine state for API responses."""
        stats = self.get_domain_stats()
        return {
            "domain_patterns": self.domain_patterns,
            "domain_to_company": self.domain_to_company,
            "stats": stats,
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Demo / smoke-test the engine from the command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 70)
    print("  Corporate Email Pattern Intelligence Engine")
    print("=" * 70)

    engine = EmailIntelligence()

    # 1. Load
    count = engine.load_verified_emails()
    print(f"\n  Loaded {count} verified contacts.\n")

    # 2. Learn
    patterns = engine.learn_patterns()
    print(f"  Learned patterns for {len(patterns)} corporate domains.\n")

    # 3. Top 20 domains by verified email count
    stats = engine.get_domain_stats()
    print("  Top 20 corporate domains by verified email count:")
    print("  " + "-" * 60)
    print(f"  {'Domain':<30} {'Emails':>6}  {'Primary Pattern':<15} Company")
    print("  " + "-" * 60)
    for info in stats["domains"][:20]:
        print(
            f"  {info['domain']:<30} {info['total_emails']:>6}  "
            f"{info['primary_pattern'] or '?':<15} {info['company']}"
        )
    print()

    # 4. Demo guess
    print("  Demo: guessing email for Tony Ryan at Amgen")
    print("  " + "-" * 60)
    guesses = engine.guess_email("Tony", "Ryan", "Amgen")
    for g in guesses:
        print(
            f"    {g['email']:<40} pattern={g['pattern']:<12} "
            f"confidence={g['confidence']:.2f}  domain={g['domain']}"
        )
    print()

    # 5. Batch demo
    demo_contacts = [
        {"first_name": "Sarah", "last_name": "Chen", "company": "BASF"},
        {"first_name": "James", "last_name": "O'Brien", "company": "Shell"},
        {"first_name": "Maria", "last_name": "Garcia-Lopez", "company": "Pfizer"},
    ]
    print("  Batch guess demo:")
    print("  " + "-" * 60)
    enriched = engine.guess_batch(demo_contacts)
    for c in enriched:
        top = c.get("top_guess", "N/A")
        conf = c.get("top_confidence", 0.0)
        n_guesses = len(c.get("guessed_emails", []))
        print(
            f"    {c['first_name']} {c['last_name']} @ {c['company']}: "
            f"top={top}  conf={conf:.2f}  ({n_guesses} guesses)"
        )
    print()

    # 6. Save patterns
    engine.save_patterns()
    print(f"  Patterns saved to {engine.data_root / DEFAULT_PATTERN_FILE}")
    print()

    # 7. Summary
    print("  Domain → Company mappings learned:")
    print("  " + "-" * 60)
    for domain, company in sorted(engine.domain_to_company.items()):
        print(f"    {domain:<35} → {company}")

    print("\n" + "=" * 70)
    print("  Done.")
    print("=" * 70)


if __name__ == "__main__":
    main()
