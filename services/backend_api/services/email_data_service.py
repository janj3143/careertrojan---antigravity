from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import os
import re
from typing import Any
from urllib.parse import quote_plus


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _normalize_email(value: str) -> str:
    return (value or "").strip().strip("<>()[]{}\"'`.,;:").lower()


PERSONAL_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "me.com",
    "yahoo.com",
    "yahoo.co.uk",
    "aol.com",
    "proton.me",
    "protonmail.com",
}


ROLE_ACCOUNT_PREFIXES = {
    "admin",
    "support",
    "help",
    "info",
    "sales",
    "noreply",
    "no-reply",
    "billing",
    "accounts",
    "hr",
    "jobs",
    "career",
    "careers",
    "marketing",
    "contact",
    "team",
    "office",
    "hello",
    "enquiries",
    "enquiry",
    "recruitment",
}


SUSPICIOUS_DOMAIN_MARKERS = {
    "temp",
    "mailinator",
    "guerrilla",
    "10minutemail",
    "trashmail",
    "disposable",
    "example",
    "invalid",
}


KNOWN_RELATIONSHIP_MARKERS = {
    "placed",
    "placement",
    "client",
    "candidate",
    "mentorship",
    "mentor",
    "coaching",
    "interaction",
    "payment",
    "invoice",
    "verified_contact",
}


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


FORWARDING_MARKERS = {
    "no longer",
    "left the company",
    "left our company",
    "please contact",
    "contact instead",
    "reach out to",
    "new email",
    "forward",
    "reroute",
}


HOLIDAY_MARKERS = {
    "out of office",
    "ooo",
    "on holiday",
    "vacation",
    "away until",
    "auto-reply",
    "automatic reply",
}


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _email_trust_tier(row: dict[str, Any]) -> tuple[str, list[str]]:
    email = _normalize_email(str(row.get("email") or ""))
    local_part, _, domain = email.partition("@")
    domain = domain.lower().strip()

    email_type = str(row.get("email_type") or "verified").lower().strip()
    is_inferred = bool(row.get("is_inferred", False)) or email_type == "inferred"
    first_seen_at = _parse_datetime(row.get("first_seen"))
    now = datetime.now(timezone.utc)
    engaged_within_5y = bool(first_seen_at and (now - first_seen_at).days <= (5 * 365))

    source_bits = []
    source_value = str(row.get("source") or "").lower().strip()
    if source_value:
        source_bits.append(source_value[:160])
    for src in (row.get("sources") or [])[:12]:
        if src:
            source_bits.append(str(src).lower().strip()[:160])
    source_blob = " ".join(source_bits)

    known_relationship = any(marker in source_blob for marker in KNOWN_RELATIONSHIP_MARKERS)
    is_personal_domain = domain in PERSONAL_EMAIL_DOMAINS
    is_role_account = local_part in ROLE_ACCOUNT_PREFIXES or any(local_part.startswith(f"{p}.") for p in ROLE_ACCOUNT_PREFIXES)
    suspicious_domain = any(marker in domain for marker in SUSPICIOUS_DOMAIN_MARKERS)
    very_old_or_unknown = not first_seen_at or (now - first_seen_at).days > (8 * 365)

    name_payload = row.get("name") or {}
    full_name = str(name_payload.get("full_name") or "").strip()
    first_name = str(name_payload.get("first_name") or "").strip()
    last_name = str(name_payload.get("last_name") or "").strip()
    has_name = bool(full_name or (first_name and last_name))

    phone = str(
        row.get("phone")
        or row.get("phone_number")
        or row.get("telephone")
        or row.get("mobile")
        or ""
    ).strip()
    has_phone = bool(phone)

    notes = row.get("notes")
    journal = row.get("journal")
    additional_transactions = row.get("additional_transactions")
    transactions = row.get("transactions")
    journal_entries = row.get("journal_entries")

    has_notes = bool(str(notes).strip()) if notes is not None else False
    has_journal = bool(journal) or bool(journal_entries)
    has_transactions = bool(additional_transactions) or bool(transactions)

    richness_score = sum(
        [
            bool(email),
            has_name,
            has_phone,
            has_notes,
            has_journal,
            has_transactions,
        ]
    )

    reasons: list[str] = []

    if suspicious_domain:
        reasons.append("suspicious_domain")
    if is_role_account:
        reasons.append("role_account")
    if very_old_or_unknown:
        reasons.append("old_or_unknown_recency")
    if "scrape" in source_blob:
        reasons.append("scraped_source")

    if reasons:
        return "C", reasons

    if (
        email_type == "verified"
        and not is_inferred
        and engaged_within_5y
        and richness_score >= 4
    ):
        high_reasons = [
            "verified_not_inferred",
            "engaged_last_5_years",
            "data_rich_profile",
        ]
        if has_name:
            high_reasons.append("has_name")
        if has_phone:
            high_reasons.append("has_phone")
        if has_notes:
            high_reasons.append("has_notes")
        if has_journal:
            high_reasons.append("has_journal")
        if has_transactions:
            high_reasons.append("has_transactions")
        if is_personal_domain:
            high_reasons.append("personal_email_domain")
        if known_relationship:
            high_reasons.append("known_relationship_signal")
        return "A", high_reasons

    medium_reasons = []
    if richness_score >= 2:
        medium_reasons.append("partial_profile_data")
    if domain and domain not in PERSONAL_EMAIL_DOMAINS:
        medium_reasons.append("corporate_domain")
    if not engaged_within_5y:
        medium_reasons.append("unknown_or_older_recency")
    if medium_reasons:
        return "B", medium_reasons

    return "C", ["low_integration_random_like"]


def _name_parts(row: dict[str, Any]) -> tuple[str, str, str]:
    name_payload = row.get("name") or {}
    first = str(name_payload.get("first_name") or "").strip().lower()
    last = str(name_payload.get("last_name") or "").strip().lower()
    full = str(name_payload.get("full_name") or "").strip().lower()

    if (not first or not last) and full:
        cleaned = re.sub(r"[^a-z\s\-']", " ", full)
        parts = [p for p in cleaned.split() if p]
        if len(parts) >= 2:
            if not first:
                first = parts[0]
            if not last:
                last = parts[-1]
    return first, last, full


def _domain_variants(domain: str) -> list[str]:
    d = str(domain or "").strip().lower()
    if not d:
        return []
    variants = {d}
    if d.endswith(".com"):
        variants.add(d[:-4] + ".co.uk")
    elif d.endswith(".co.uk"):
        variants.add(d[:-6] + ".com")
    return sorted(variants)


def _five_level_candidates(row: dict[str, Any]) -> list[dict[str, Any]]:
    first, last, _ = _name_parts(row)
    domain = str(row.get("domain") or "").strip().lower()
    if not first and not last:
        return []

    fi = first[:1] if first else ""
    levels = [
        {"level": 1, "label": "firstlast", "local": f"{first}{last}"},
        {"level": 2, "label": "first.last", "local": f"{first}.{last}"},
        {"level": 3, "label": "f.last", "local": f"{fi}.{last}"},
        {"level": 4, "label": "first", "local": f"{first}"},
        {"level": 5, "label": "first_last", "local": f"{first}_{last}"},
    ]

    valid_levels: list[dict[str, Any]] = []
    domains = _domain_variants(domain)
    if not domains:
        return []

    for level in levels:
        local = str(level.get("local") or "").strip("._-")
        if not local:
            continue
        if ".." in local:
            local = local.replace("..", ".")
        candidates = [f"{local}@{d}" for d in domains if d]
        valid_levels.append(
            {
                "level": level["level"],
                "label": level["label"],
                "candidates": candidates,
            }
        )
    return valid_levels


def _run_five_level_email_test(
    row: dict[str, Any],
    known_emails: set[str],
    known_domains: set[str],
) -> dict[str, Any]:
    levels = _five_level_candidates(row)
    domain = str(row.get("domain") or "").strip().lower()
    current_email = _normalize_email(str(row.get("email") or ""))

    level_results: list[dict[str, Any]] = []
    any_positive = False
    positive_matches: list[str] = []
    for level in levels:
        candidates = level["candidates"]
        matched = [candidate for candidate in candidates if candidate in known_emails]
        if matched:
            any_positive = True
            positive_matches.extend(matched)
        level_results.append(
            {
                "level": level["level"],
                "label": level["label"],
                "tested": len(candidates),
                "matched": matched,
                "status": "positive" if matched else "negative",
            }
        )

    domain_known = domain in known_domains if domain else False
    current_seen = current_email in known_emails if current_email else False

    is_valid = any_positive or current_seen or domain_known
    return {
        "test_type": "five_level_name_domain_pattern",
        "levels": level_results,
        "domain_known": domain_known,
        "current_email_seen": current_seen,
        "positive_matches": sorted(set(positive_matches)),
        "all_negative": not is_valid,
        "is_valid": is_valid,
    }


def _normalize_tier(value: str | None) -> str | None:
    if value is None:
        return None
    tier = str(value).strip().upper()
    return tier if tier in {"A", "B", "C"} else None


def _unsubscribe_base_url() -> str:
    return str(
        os.getenv("CAREERTROJAN_UNSUBSCRIBE_BASE_URL")
        or os.getenv("UNSUBSCRIBE_BASE_URL")
        or "https://careertrojan.ai/unsubscribe"
    ).strip()


def build_unsubscribe_url(email: str) -> str:
    base = _unsubscribe_base_url().rstrip("/")
    encoded_email = quote_plus(_normalize_email(email))
    return f"{base}?email={encoded_email}"


def _count_json_files(path: Path, limit: int = 20000) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    count = 0
    for _ in path.rglob("*.json"):
        count += 1
        if count >= limit:
            break
    return count


def load_email_database(
    ai_data_path: Path,
    run_five_level_test: bool = False,
) -> list[dict[str, Any]]:
    db_path = ai_data_path / "emails" / "emails_database.json"
    raw = _read_json(db_path, [])
    if not isinstance(raw, list):
        return []

    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            continue
        email = _normalize_email(str(row.get("email", "")))
        if not email or "@" not in email or email in seen:
            continue
        seen.add(email)
        domain = email.split("@", 1)[1]
        cleaned.append(
            {
                "email": email,
                "domain": row.get("domain") or domain,
                "first_seen": row.get("first_seen"),
                "source": row.get("source", "emails_database"),
                "source_count": row.get("source_count", 1),
                "sources": row.get("sources", []),
                "email_type": str(row.get("email_type") or "verified").lower(),
                "is_inferred": bool(row.get("is_inferred", False)),
                "inference_confidence": row.get("inference_confidence", "high"),
                "inference_method": row.get("inference_method", "observed_in_source"),
                "name": row.get("name", {}),
                "company": row.get("company", ""),
                "phone": row.get("phone") or row.get("phone_number") or row.get("telephone") or row.get("mobile"),
                "notes": row.get("notes"),
                "journal": row.get("journal") or row.get("journal_entries"),
                "additional_transactions": row.get("additional_transactions") or row.get("transactions"),
            }
        )

    known_emails = {str(r.get("email") or "").lower() for r in cleaned if r.get("email")}
    known_domains = {str(r.get("domain") or "").lower() for r in cleaned if r.get("domain")}

    for row in cleaned:
        tier, reasons = _email_trust_tier(row)
        should_validate_patterns = run_five_level_test and (bool(row.get("is_inferred")) or tier in {"B", "C"})
        if should_validate_patterns:
            validation = _run_five_level_email_test(row, known_emails, known_domains)
        else:
            validation = {
                "test_type": "deferred_or_trusted_observed",
                "levels": [],
                "domain_known": True,
                "current_email_seen": True,
                "positive_matches": [str(row.get("email") or "")],
                "all_negative": False,
                "is_valid": True,
            }

        if validation.get("all_negative"):
            tier = "C"
            reasons = list(dict.fromkeys([*reasons, "five_level_test_all_negative", "annotated_false_email"]))

        row["trust_tier"] = tier
        row["trust_reasons"] = reasons
        row["email_validation"] = validation

    return cleaned


def load_legacy_email_records(ai_data_path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    legacy_path = ai_data_path / "email_extracted"
    if not legacy_path.exists():
        return []

    records: list[dict[str, Any]] = []
    for idx, json_file in enumerate(sorted(legacy_path.glob("*.json"))):
        if limit is not None and idx >= limit:
            break
        row = _read_json(json_file, None)
        if not isinstance(row, dict):
            continue
        row["_source_file"] = str(json_file)
        records.append(row)
    return records


def get_email_records(
    ai_data_path: Path,
    limit: int = 500,
    offset: int = 0,
    domain: str | None = None,
    query: str | None = None,
    email_type: str | None = None,
    trust_tier: str | None = None,
) -> dict[str, Any]:
    normalized_tier = _normalize_tier(trust_tier)
    should_run_deep_validation = normalized_tier in {"B", "C"} or str(email_type or "").strip().lower() == "inferred"
    all_rows = load_email_database(ai_data_path, run_five_level_test=should_run_deep_validation)

    if email_type:
        email_type_needle = email_type.strip().lower()
        if email_type_needle in {"verified", "inferred"}:
            all_rows = [r for r in all_rows if str(r.get("email_type", "verified")).lower() == email_type_needle]

    if domain:
        domain_needle = domain.strip().lower()
        all_rows = [r for r in all_rows if str(r.get("domain", "")).lower() == domain_needle]

    if query:
        q = query.strip().lower()
        all_rows = [
            r
            for r in all_rows
            if q in str(r.get("email", "")).lower() or q in str(r.get("domain", "")).lower()
        ]

    if normalized_tier:
        all_rows = [r for r in all_rows if str(r.get("trust_tier") or "") == normalized_tier]

    total = len(all_rows)
    start = max(0, offset)
    end = max(start, start + max(0, min(limit, 5000)))
    page = all_rows[start:end]

    return {
        "total": total,
        "offset": start,
        "limit": limit,
        "records": page,
    }


def get_email_summary(ai_data_path: Path) -> dict[str, Any]:
    records = load_email_database(ai_data_path, run_five_level_test=False)
    legacy_count = len(list((ai_data_path / "email_extracted").glob("*.json"))) if (ai_data_path / "email_extracted").exists() else 0

    domain_counts = Counter(str(r.get("domain", "")).lower() for r in records if r.get("domain"))
    type_counts = Counter(str(r.get("email_type", "verified")).lower() for r in records)
    tier_counts = Counter(str(r.get("trust_tier") or "B") for r in records)
    invalid_count = sum(1 for r in records if bool((r.get("email_validation") or {}).get("all_negative")))
    top_domains = [{"domain": d, "count": c} for d, c in domain_counts.most_common(30)]

    return {
        "email_records": len(records),
        "verified_records": type_counts.get("verified", 0),
        "inferred_records": type_counts.get("inferred", 0),
        "trust_tier_counts": {
            "A": tier_counts.get("A", 0),
            "B": tier_counts.get("B", 0),
            "C": tier_counts.get("C", 0),
        },
        "invalidated_by_five_level_test": invalid_count,
        "five_level_validation_mode": "deferred_targeted",
        "default_outreach_tier": "A",
        "unsubscribe": {
            "required": True,
            "base_url": _unsubscribe_base_url(),
            "available_in_provider_payload": True,
            "note": "SendGrid/Klaviyo payloads include unsubscribe_url for each contact; wire this in send templates.",
        },
        "unique_domains": len(domain_counts),
        "top_domains": top_domains,
        "folders": {
            "emails": str(ai_data_path / "emails"),
            "verified": str(ai_data_path / "emails" / "emails_verified.json"),
            "inferred": str(ai_data_path / "emails" / "emails_inferred.json"),
            "email_extracted": str(ai_data_path / "email_extracted"),
            "legacy_file_count": legacy_count,
        },
        "runtime_ai_data_path": str(ai_data_path),
        "zero_data_alert": len(records) == 0,
        "merge_recommended": legacy_count > 0,
        "diagnostics": get_email_diagnostics(ai_data_path),
    }


def get_email_diagnostics(ai_data_path: Path) -> dict[str, Any]:
    emails_dir = ai_data_path / "emails"
    db_path = emails_dir / "emails_database.json"
    report_path = emails_dir / "extraction_report.json"
    inferred_path = emails_dir / "emails_inferred.json"
    verified_path = emails_dir / "emails_verified.json"

    report = _read_json(report_path, {})
    db_rows = load_email_database(ai_data_path, run_five_level_test=False)

    alerts: list[str] = []

    if not db_path.exists():
        alerts.append("emails_database_missing")
    if len(db_rows) == 0:
        alerts.append("runtime_email_records_zero")

    if isinstance(report, dict) and report:
        report_ai_data = str(report.get("ai_data_final") or "")
        if report_ai_data:
            report_path = Path(report_ai_data)
            report_total = int(report.get("total_unique_emails") or 0)
            runtime_norm = str(ai_data_path).replace("\\", "/").lower().rstrip("/")
            report_norm = str(report_ai_data).replace("\\", "/").lower().rstrip("/")
            mounted_equivalent = (
                runtime_norm.endswith("/ai_data_final")
                and report_norm.endswith("/ai_data_final")
                and report_total == len(db_rows)
            )
            if report_path != ai_data_path and not mounted_equivalent:
                alerts.append("runtime_vs_extractor_path_mismatch")

        scanned = int(report.get("scanned_files") or 0)
        total = int(report.get("total_unique_emails") or 0)
        if scanned >= 1000 and total == 0:
            alerts.append("extractor_zero_after_large_scan")

        for flag in report.get("alert_flags", []):
            if isinstance(flag, str):
                alerts.append(f"extractor:{flag}")
    else:
        alerts.append("extraction_report_missing_or_invalid")

    diagnostics = {
        "runtime_ai_data_path": str(ai_data_path),
        "emails_dir": str(emails_dir),
        "files": {
            "emails_database_exists": db_path.exists(),
            "emails_verified_exists": verified_path.exists(),
            "emails_inferred_exists": inferred_path.exists(),
            "extraction_report_exists": report_path.exists(),
        },
        "counts": {
            "runtime_loaded_records": len(db_rows),
            "emails_folder_json_files": _count_json_files(emails_dir),
            "email_extracted_json_files": _count_json_files(ai_data_path / "email_extracted"),
        },
        "extractor_report": report if isinstance(report, dict) else {},
        "alerts": sorted(set(alerts)),
        "ok": len(alerts) == 0,
    }
    return diagnostics


def build_provider_payload(
    ai_data_path: Path,
    provider: str,
    limit: int = 500,
    domain: str | None = None,
    email_type: str | None = "verified",
    trust_tier: str | None = "A",
) -> dict[str, Any]:
    dataset = get_email_records(
        ai_data_path,
        limit=limit,
        offset=0,
        domain=domain,
        email_type=email_type,
        trust_tier=trust_tier,
    )
    contacts = [r for r in dataset["records"] if r.get("email")]

    provider_key = provider.strip().lower()
    if provider_key == "sendgrid":
        payload = {
            "provider": "sendgrid",
            "email_type": email_type or "all",
            "trust_tier": _normalize_tier(trust_tier) or "ALL",
            "compliance": {
                "unsubscribe_required": True,
                "provider_mode": "sendgrid_subscription_tracking_or_asm",
                "unsubscribe_base_url": _unsubscribe_base_url(),
                "recommended_send_args": {
                    "asm_group_id_env": "SENDGRID_UNSUBSCRIBE_GROUP_ID",
                    "dynamic_template_var": "unsubscribe_url",
                    "custom_args_key": "unsubscribe_url",
                },
            },
            "contacts": [
                {
                    "email": str(r["email"]).lower(),
                    "first_name": str((r.get("name") or {}).get("first_name") or ""),
                    "last_name": str((r.get("name") or {}).get("last_name") or ""),
                    "full_name": str((r.get("name") or {}).get("full_name") or ""),
                    "company": str(r.get("company") or ""),
                    "email_type": str(r.get("email_type") or "verified"),
                    "trust_tier": str(r.get("trust_tier") or "B"),
                    "inference_confidence": str(r.get("inference_confidence") or "high"),
                    "unsubscribe_url": build_unsubscribe_url(str(r["email"])),
                }
                for r in contacts
            ],
            "count": len(contacts),
        }
    elif provider_key == "klaviyo":
        payload = {
            "provider": "klaviyo",
            "email_type": email_type or "all",
            "trust_tier": _normalize_tier(trust_tier) or "ALL",
            "compliance": {
                "unsubscribe_required": True,
                "provider_mode": "klaviyo_profile_properties_and_subscription_management",
                "unsubscribe_base_url": _unsubscribe_base_url(),
                "recommended_send_args": {
                    "template_var": "unsubscribe_url",
                    "manage_preferences_link": True,
                },
            },
            "data": [
                {
                    "type": "profile",
                    "attributes": {
                        "email": str(r["email"]).lower(),
                        "first_name": str((r.get("name") or {}).get("first_name") or ""),
                        "last_name": str((r.get("name") or {}).get("last_name") or ""),
                        "properties": {
                            "full_name": str((r.get("name") or {}).get("full_name") or ""),
                            "company": str(r.get("company") or ""),
                            "email_type": str(r.get("email_type") or "verified"),
                            "trust_tier": str(r.get("trust_tier") or "B"),
                            "inference_confidence": str(r.get("inference_confidence") or "high"),
                            "unsubscribe_url": build_unsubscribe_url(str(r["email"])),
                        },
                    },
                }
                for r in contacts
            ],
            "count": len(contacts),
        }
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return payload


def build_guarded_provider_payload(
    ai_data_path: Path,
    provider: str,
    limit: int = 500,
    domain: str | None = None,
    email_type: str | None = "verified",
    trust_tier: str | None = "A",
    allow_non_tier_a: bool = False,
    override_reason: str | None = None,
) -> dict[str, Any]:
    payload = build_provider_payload(
        ai_data_path=ai_data_path,
        provider=provider,
        limit=limit,
        domain=domain,
        email_type=email_type,
        trust_tier=trust_tier,
    )

    normalized_tier = _normalize_tier(trust_tier) or "A"
    reason = str(override_reason or "").strip()
    violations: list[str] = []

    if normalized_tier != "A" and not allow_non_tier_a:
        violations.append("non_tier_a_blocked_by_policy")
    if normalized_tier != "A" and allow_non_tier_a and len(reason) < 8:
        violations.append("override_reason_required_for_non_tier_a")

    compliance = payload.get("compliance") or {}
    if not bool(compliance.get("unsubscribe_required", False)):
        violations.append("unsubscribe_not_required_in_payload")

    contacts: list[dict[str, Any]] = []
    if payload.get("provider") == "sendgrid":
        contacts = [c for c in (payload.get("contacts") or []) if isinstance(c, dict)]
    elif payload.get("provider") == "klaviyo":
        for item in payload.get("data") or []:
            if not isinstance(item, dict):
                continue
            attrs = item.get("attributes") or {}
            props = attrs.get("properties") or {}
            contacts.append(
                {
                    "email": attrs.get("email"),
                    "unsubscribe_url": props.get("unsubscribe_url"),
                }
            )

    missing_unsubscribe = [
        str(c.get("email") or "")
        for c in contacts
        if not str(c.get("unsubscribe_url") or "").strip()
    ]
    if missing_unsubscribe:
        violations.append("missing_unsubscribe_url_for_contacts")

    guarded = {
        "policy": {
            "pass": len(violations) == 0,
            "enforced_default_tier": "A",
            "requested_tier": normalized_tier,
            "allow_non_tier_a": bool(allow_non_tier_a),
            "override_reason": reason,
            "violations": violations,
            "unsubscribe_required": True,
            "contacts_checked": len(contacts),
            "missing_unsubscribe_count": len(missing_unsubscribe),
        },
        "payload": payload,
    }

    if missing_unsubscribe:
        guarded["policy"]["missing_unsubscribe_examples"] = missing_unsubscribe[:20]

    return guarded


def _tracking_path(ai_data_path: Path) -> Path:
    return ai_data_path / "emails" / "email_tracking_log.json"


def _extract_reroute_targets(rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    reroute_count = 0
    holiday_count = 0

    for row in rows:
        to_email = _normalize_email(str(row.get("to_email") or ""))
        text_blob = " ".join(
            [
                str(row.get("bounce_reason") or ""),
                str(row.get("response_excerpt") or ""),
                str(row.get("notes") or ""),
            ]
        )
        if not text_blob.strip():
            continue
        lowered = text_blob.lower()
        marker_type = None
        if any(marker in lowered for marker in FORWARDING_MARKERS):
            marker_type = "reroute"
            reroute_count += 1
        elif any(marker in lowered for marker in HOLIDAY_MARKERS):
            marker_type = "holiday"
            holiday_count += 1
        else:
            continue

        for match in EMAIL_REGEX.findall(text_blob):
            candidate = _normalize_email(match)
            if not candidate or candidate == to_email or "@" not in candidate:
                continue
            key = (candidate, marker_type)
            if key in seen:
                continue
            seen.add(key)
            targets.append(
                {
                    "discovered_email": candidate,
                    "from_email": to_email,
                    "discovery_type": marker_type,
                    "source_event_id": str(row.get("id") or ""),
                    "sent_at": str(row.get("sent_at") or ""),
                }
            )

    return {
        "reroute_events": reroute_count,
        "holiday_events": holiday_count,
        "discovered_targets_count": len(targets),
        "discovered_targets": targets[:200],
    }


def _normalize_outcome(value: str | None) -> str:
    allowed = {
        "sent",
        "bounce",
        "response",
        "freemium_user",
        "converted_paid",
        "unknown",
    }
    normalized = str(value or "unknown").strip().lower()
    return normalized if normalized in allowed else "unknown"


def suggest_bounce_retry(bounce_reason: str | None) -> str:
    reason = str(bounce_reason or "").strip().lower()
    if not reason:
        return "Verify domain MX records and retry with a verified address format after 48h."
    if any(flag in reason for flag in ["mailbox full", "over quota", "quota"]):
        return "Retry in 48-72h and move this contact to a low-frequency send segment."
    if any(flag in reason for flag in ["user unknown", "no such user", "invalid recipient"]):
        return "Do not retry the same address; verify spelling or source a new contact at the same company."
    if any(flag in reason for flag in ["blocked", "spam", "policy", "rejected"]):
        return "Retry from a warmed sending domain with a plain-text first touch and reduced link density."
    if any(flag in reason for flag in ["dns", "mx", "domain"]):
        return "Re-check domain health and retry only after DNS/MX resolves consistently for 24h."
    return "Retry once with a shorter subject/body variation and monitor bounce classification before further sends."


def load_email_tracking_records(ai_data_path: Path) -> list[dict[str, Any]]:
    tracking_path = _tracking_path(ai_data_path)
    raw = _read_json(tracking_path, [])
    if not isinstance(raw, list):
        return []

    rows: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        email = _normalize_email(str(row.get("to_email", "")))
        if not email or "@" not in email:
            continue
        outcome = _normalize_outcome(str(row.get("result")))
        bounce_reason = str(row.get("bounce_reason") or "").strip()
        attempt_suggestion = str(row.get("bounce_attempt_suggestion") or "").strip()
        if outcome == "bounce" and not attempt_suggestion:
            attempt_suggestion = suggest_bounce_retry(bounce_reason)
        rows.append(
            {
                "id": str(row.get("id") or ""),
                "to_email": email,
                "to_name": str(row.get("to_name") or ""),
                "sent_at": str(row.get("sent_at") or ""),
                "campaign": str(row.get("campaign") or ""),
                "result": outcome,
                "bounce_reason": bounce_reason,
                "bounce_attempt_suggestion": attempt_suggestion,
                "response_excerpt": str(row.get("response_excerpt") or ""),
                "notes": str(row.get("notes") or ""),
                "created_at": str(row.get("created_at") or ""),
            }
        )
    rows.sort(key=lambda r: str(r.get("sent_at") or r.get("created_at") or ""), reverse=True)
    return rows


def save_email_tracking_record(
    ai_data_path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    from datetime import datetime, timezone
    from uuid import uuid4

    emails_dir = ai_data_path / "emails"
    emails_dir.mkdir(parents=True, exist_ok=True)
    tracking_path = _tracking_path(ai_data_path)

    existing = load_email_tracking_records(ai_data_path)
    to_email = _normalize_email(str(payload.get("to_email") or ""))
    if not to_email or "@" not in to_email:
        raise ValueError("Valid to_email is required")

    result = _normalize_outcome(str(payload.get("result") or "unknown"))
    bounce_reason = str(payload.get("bounce_reason") or "").strip()
    record = {
        "id": str(payload.get("id") or uuid4()),
        "to_email": to_email,
        "to_name": str(payload.get("to_name") or "").strip(),
        "sent_at": str(payload.get("sent_at") or datetime.now(timezone.utc).isoformat()),
        "campaign": str(payload.get("campaign") or "").strip(),
        "result": result,
        "bounce_reason": bounce_reason,
        "bounce_attempt_suggestion": str(payload.get("bounce_attempt_suggestion") or "").strip(),
        "response_excerpt": str(payload.get("response_excerpt") or "").strip(),
        "notes": str(payload.get("notes") or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if result == "bounce" and not record["bounce_attempt_suggestion"]:
        record["bounce_attempt_suggestion"] = suggest_bounce_retry(bounce_reason)

    existing.insert(0, record)
    tracking_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def get_email_tracking_records(
    ai_data_path: Path,
    limit: int = 200,
    offset: int = 0,
    result: str | None = None,
) -> dict[str, Any]:
    rows = load_email_tracking_records(ai_data_path)

    if result:
        result_needle = _normalize_outcome(result)
        rows = [r for r in rows if str(r.get("result") or "") == result_needle]

    total = len(rows)
    start = max(0, offset)
    end = max(start, start + max(0, min(limit, 2000)))
    return {
        "total": total,
        "offset": start,
        "limit": limit,
        "records": rows[start:end],
    }


def get_email_tracking_summary(ai_data_path: Path) -> dict[str, Any]:
    rows = load_email_tracking_records(ai_data_path)
    result_counts = Counter(str(r.get("result") or "unknown") for r in rows)
    bounce_rows = [r for r in rows if str(r.get("result") or "") == "bounce"]
    reroute = _extract_reroute_targets(rows)

    return {
        "total_events": len(rows),
        "result_counts": {
            "sent": result_counts.get("sent", 0),
            "bounce": result_counts.get("bounce", 0),
            "response": result_counts.get("response", 0),
            "freemium_user": result_counts.get("freemium_user", 0),
            "converted_paid": result_counts.get("converted_paid", 0),
            "unknown": result_counts.get("unknown", 0),
        },
        "bounce_retry_ready": sum(1 for r in bounce_rows if r.get("bounce_attempt_suggestion")),
        "reroute_intelligence": reroute,
        "latest_sent_at": rows[0].get("sent_at") if rows else None,
        "tracking_file": str(_tracking_path(ai_data_path)),
    }


def get_email_reroute_targets(ai_data_path: Path) -> dict[str, Any]:
    rows = load_email_tracking_records(ai_data_path)
    return _extract_reroute_targets(rows)
