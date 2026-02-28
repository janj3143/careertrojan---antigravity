import argparse
import csv
import json
import re
import shutil
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.paths import CareerTrojanPaths

try:
    import extract_msg  # type: ignore
except Exception:
    extract_msg = None


COMMON_TLDS = {
    "com", "net", "org", "co", "us", "ai", "io", "xyz", "shop", "pro",
    "store", "online", "inc", "llc", "info", "tech", "uk", "de", "fr", "it",
    "es", "pt", "nl", "se", "no", "fi", "ie", "ch", "at", "be", "dk", "pl",
    "cz", "ro", "gr", "tr", "ae", "sa", "qa", "in", "cn", "jp", "kr", "au",
    "nz", "za", "br", "mx", "ca", "edu", "gov", "mil", "int",
}

STOPWORDS_COMPANY = {
    "ltd", "limited", "plc", "inc", "llc", "gmbh", "sa", "bv", "pte", "corp", "co", "company", "group"
}

EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._%+\-])"
    r"([A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9\-][A-Za-z0-9.\-]{0,252}\.[A-Za-z0-9\-]{2,63})"
    r"(?![A-Za-z0-9._%+\-])"
)


def load_tld_hints(domain_file: Path | None) -> set[str]:
    tlds = set(COMMON_TLDS)
    if not domain_file or not domain_file.exists():
        return tlds

    raw = domain_file.read_text(encoding="utf-8", errors="ignore")
    for token in re.findall(r"\.[a-z0-9\-]{2,63}", raw.lower()):
        tlds.add(token[1:])
    for token in re.findall(r"xn--[a-z0-9\-]{2,59}", raw.lower()):
        tlds.add(token)
    return tlds


def is_valid_email(value: str, tlds: set[str]) -> bool:
    if "@" not in value:
        return False
    local, domain = value.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    tld = domain.rsplit(".", 1)[1].lower()
    if len(tld) == 2:
        return True
    return tld in tlds


def clean_email(value: str) -> str:
    return value.strip().strip("<>()[]{}\"'`.,;:\\/").lower()


def clean_name(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def sanitize_local_part(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def normalize_company(value: str) -> str:
    raw = re.sub(r"[^a-z0-9\s&\-]", " ", (value or "").lower())
    parts = [p for p in re.split(r"\s+", raw) if p and p not in STOPWORDS_COMPANY]
    return " ".join(parts)


def company_slug(value: str) -> str:
    norm = normalize_company(value)
    if not norm:
        return ""
    parts = re.findall(r"[a-z0-9]+", norm)
    return "".join(parts)


def extract_domain_from_value(value: str, tlds: set[str]) -> str:
    raw = (value or "").strip().strip("\"'` ,;")
    if not raw:
        return ""

    if "@" in raw and raw.count("@") == 1:
        candidate = clean_email(raw)
        if is_valid_email(candidate, tlds):
            return candidate.split("@", 1)[1]

    probe = raw
    if "[" in probe or "]" in probe:
        return ""
    try:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    except Exception:
        return ""
    host = (parsed.netloc or parsed.path or "").lower().strip()
    if host.startswith("www."):
        host = host[4:]
    host = host.split("/")[0].strip(".")
    if not host or "." not in host:
        return ""

    if re.match(r"^[0-9.]+$", host):
        return ""

    tld = host.rsplit(".", 1)[1]
    if len(tld) == 2 or tld in tlds:
        return host
    return ""


def build_company_domain_hints_from_company_store(
    parser_root: Path,
    ai_data_final: Path,
    tlds: set[str],
) -> dict[str, str]:
    hints: dict[str, Counter] = {}

    companies_csv = parser_root / "Companies.csv"
    for row in parse_csv_rows(companies_csv):
        name = find_field(row, {"name", "companyname", "company"})
        if not name:
            continue
        norm_name = normalize_company(name)
        if not norm_name:
            continue

        domain_candidates: list[str] = []
        for value in row.values():
            domain = extract_domain_from_value(value, tlds)
            if domain:
                domain_candidates.append(domain)
        for domain in domain_candidates:
            hints.setdefault(norm_name, Counter())[domain] += 1

    potential_company_dirs = [
        ai_data_final / "companies",
        ai_data_final / "core_databases",
        ai_data_final / "metadata",
    ]
    files_seen = 0
    max_company_json_files = 2000
    for directory in potential_company_dirs:
        if not directory.exists():
            continue
        for json_file in directory.rglob("*.json"):
            if files_seen >= max_company_json_files:
                break
            files_seen += 1
            try:
                payload = json.loads(json_file.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue

            rows = payload if isinstance(payload, list) else [payload]
            for item in rows:
                if not isinstance(item, dict):
                    continue
                company_name = clean_name(
                    str(item.get("company") or item.get("name") or item.get("company_name") or "")
                )
                if not company_name:
                    continue
                norm_name = normalize_company(company_name)
                if not norm_name:
                    continue

                values_to_check = [
                    str(item.get("website") or ""),
                    str(item.get("domain") or ""),
                    str(item.get("url") or ""),
                    str(item.get("email") or ""),
                ]
                for value in values_to_check:
                    domain = extract_domain_from_value(value, tlds)
                    if domain:
                        hints.setdefault(norm_name, Counter())[domain] += 1

    resolved: dict[str, str] = {}
    for company, counter in hints.items():
        if counter:
            resolved[company] = counter.most_common(1)[0][0]
    return resolved


def split_first_last(firstname: str, surname: str) -> tuple[str, str, str]:
    fn = clean_name(firstname)
    sn = clean_name(surname)
    if not sn and fn and " " in fn:
        tokens = fn.split()
        if len(tokens) >= 2:
            fn = " ".join(tokens[:-1])
            sn = tokens[-1]
    full = clean_name(f"{fn} {sn}")
    return fn, sn, full


def parse_csv_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not path.exists():
        return rows
    try:
        with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if not isinstance(row, dict):
                    continue
                rows.append({str(k or "").strip(): str(v or "").strip() for k, v in row.items()})
    except Exception:
        return []
    return rows


def find_field(row: dict[str, str], aliases: set[str]) -> str:
    for key, value in row.items():
        normalized = re.sub(r"[^a-z0-9]", "", key.lower())
        if normalized in aliases:
            return value.strip()
    return ""


def collect_contact_rows(parser_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for file_name in ("Contacts.csv", "Candidate.csv"):
        source = parser_root / file_name
        for row in parse_csv_rows(source):
            first = find_field(row, {"firstname", "first", "givenname"})
            surname = find_field(row, {"surname", "lastname", "last", "familyname"})
            company = find_field(row, {"company", "organisation", "organization", "employer"})
            work_email = find_field(row, {"workemail", "businessemail", "companyemail"})
            personal_email = find_field(row, {"personalemail", "email", "emailaddress"})
            if not any([first, surname, company, work_email, personal_email]):
                continue
            rows.append(
                {
                    "source_file": str(source),
                    "first_name": first,
                    "last_name": surname,
                    "company": company,
                    "work_email": clean_email(work_email),
                    "personal_email": clean_email(personal_email),
                }
            )
    return rows


def build_company_domain_hints(contact_rows: list[dict[str, str]], tlds: set[str]) -> dict[str, str]:
    company_domains: dict[str, Counter] = {}
    for row in contact_rows:
        company = normalize_company(row.get("company", ""))
        work_email = clean_email(row.get("work_email", ""))
        if not company or not work_email or not is_valid_email(work_email, tlds):
            continue
        domain = work_email.split("@", 1)[1]
        company_domains.setdefault(company, Counter())[domain] += 1

    resolved: dict[str, str] = {}
    for company, counter in company_domains.items():
        if not counter:
            continue
        resolved[company] = counter.most_common(1)[0][0]
    return resolved


def infer_email_candidates(
    contact_rows: list[dict[str, str]],
    existing_verified: set[str],
    company_domains: dict[str, str],
    tlds: set[str],
) -> list[dict]:
    inferred: dict[str, dict] = {}

    for row in contact_rows:
        first_name, last_name, full_name = split_first_last(row.get("first_name", ""), row.get("last_name", ""))
        company = row.get("company", "")
        work_email = clean_email(row.get("work_email", ""))
        if work_email and is_valid_email(work_email, tlds):
            continue
        if not first_name or not last_name:
            continue

        local_part = sanitize_local_part(first_name + last_name)
        if len(local_part) < 3:
            continue

        norm_company = normalize_company(company)
        domain = company_domains.get(norm_company, "")
        inference_method = "company_observed_domain"
        confidence = "medium"
        if not domain:
            slug = company_slug(company)
            if not slug:
                continue
            domain = f"{slug}.com"
            inference_method = "company_slug_dot_com"
            confidence = "low"
        elif domain and norm_company in company_domains:
            if domain == company_domains.get(norm_company):
                confidence = "high"

        email = f"{local_part}@{domain}".lower()
        if email in existing_verified or not is_valid_email(email, tlds):
            continue

        if email not in inferred:
            inferred[email] = {
                "email": email,
                "domain": domain,
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "source_count": 1,
                "sources": [row.get("source_file", "contacts")],
                "email_type": "inferred",
                "is_inferred": True,
                "inference_confidence": confidence,
                "inference_method": inference_method,
                "name": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": full_name,
                },
                "company": clean_name(company),
            }
        else:
            inferred[email]["source_count"] += 1
            source_file = row.get("source_file", "contacts")
            if source_file not in inferred[email]["sources"]:
                inferred[email]["sources"].append(source_file)

    return sorted(inferred.values(), key=lambda r: r["email"])


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def read_msg_file(path: Path) -> str:
    if extract_msg is not None:
        try:
            msg = extract_msg.Message(str(path))
            pieces = [msg.sender or "", msg.to or "", msg.cc or "", msg.subject or "", msg.body or ""]
            return "\n".join(pieces)
        except Exception:
            pass
    try:
        return path.read_bytes().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def iter_zip_texts(path: Path) -> Iterable[tuple[str, str]]:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                inner_name = info.filename
                lower = inner_name.lower()
                if not lower.endswith((".txt", ".csv", ".json", ".md", ".html", ".htm", ".xml", ".eml", ".msg")):
                    continue
                try:
                    raw = archive.read(info)
                    text = raw.decode("utf-8", errors="ignore")
                    if text:
                        yield inner_name, text
                except Exception:
                    continue
    except Exception:
        return


def extract_from_text(text: str, tlds: set[str]) -> set[str]:
    emails: set[str] = set()
    for match in EMAIL_PATTERN.findall(text):
        e = clean_email(match)
        if is_valid_email(e, tlds):
            emails.add(e)
    return emails


def merge_legacy_records(ai_data_final: Path, output_dir: Path) -> tuple[int, int]:
    legacy = ai_data_final / "email_extracted"
    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    if not legacy.exists():
        return (0, 0)

    copied = 0
    existing = 0
    for item in legacy.glob("*.json"):
        target = records_dir / item.name
        if target.exists():
            existing += 1
            continue
        shutil.copy2(item, target)
        copied += 1
    return (copied, existing)


def scan_sources(paths: CareerTrojanPaths, tlds: set[str], max_files: int | None = None) -> dict:
    parser_root = paths.parser_root
    ai_data_final = paths.ai_data_final
    output_dir = ai_data_final / "emails"
    output_dir.mkdir(parents=True, exist_ok=True)

    extensions = {".txt", ".csv", ".json", ".md", ".html", ".htm", ".xml", ".eml", ".msg", ".zip"}
    excluded_names = {
        "emails_database.json",
        "emails_verified.json",
        "emails_inferred.json",
        "domain_counts.json",
        "extraction_report.json",
    }

    email_sources: dict[str, set[str]] = {}
    scanned = 0
    scanned_by_ext = Counter()

    source_roots = [parser_root, ai_data_final / "email_extracted", ai_data_final / "emails"]
    for root in source_roots:
        if not root.exists():
            continue
        for file_path in root.rglob("*"):
            if max_files is not None and scanned >= max_files:
                break
            if not file_path.is_file():
                continue
            if file_path.name in excluded_names:
                continue
            if file_path.suffix.lower() not in extensions:
                continue

            scanned += 1
            scanned_by_ext[file_path.suffix.lower()] += 1

            if file_path.suffix.lower() == ".zip":
                for inner_name, inner_text in iter_zip_texts(file_path):
                    found = extract_from_text(inner_text, tlds)
                    if not found:
                        continue
                    source = f"{file_path}::{inner_name}"
                    for email in found:
                        email_sources.setdefault(email, set()).add(source)
                continue

            if file_path.suffix.lower() == ".msg":
                text = read_msg_file(file_path)
            else:
                text = read_text_file(file_path)
            if not text:
                continue

            found = extract_from_text(text, tlds)
            if not found:
                continue

            source = str(file_path)
            for email in found:
                email_sources.setdefault(email, set()).add(source)

    now = datetime.now(timezone.utc).isoformat()
    verified_records = [
        {
            "email": email,
            "domain": email.split("@", 1)[1],
            "first_seen": now,
            "source_count": len(srcs),
            "sources": sorted(srcs)[:20],
            "email_type": "verified",
            "is_inferred": False,
            "inference_confidence": "high",
            "inference_method": "observed_in_source",
            "name": {
                "first_name": "",
                "last_name": "",
                "full_name": "",
            },
            "company": "",
        }
        for email, srcs in sorted(email_sources.items())
    ]

    contact_rows = collect_contact_rows(parser_root)
    company_domains = build_company_domain_hints(contact_rows, tlds)
    company_store_hints = build_company_domain_hints_from_company_store(parser_root, ai_data_final, tlds)
    for company, domain in company_store_hints.items():
        company_domains.setdefault(company, domain)
    verified_set = {row["email"] for row in verified_records}
    inferred_records = infer_email_candidates(contact_rows, verified_set, company_domains, tlds)

    records = sorted([*verified_records, *inferred_records], key=lambda x: x["email"])
    domain_counts = Counter(r["domain"] for r in records)
    type_counts = Counter(r.get("email_type", "verified") for r in records)
    inferred_methods = Counter(r.get("inference_method", "") for r in inferred_records)

    (output_dir / "emails_database.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    (output_dir / "emails_verified.json").write_text(json.dumps(verified_records, indent=2), encoding="utf-8")
    (output_dir / "emails_inferred.json").write_text(json.dumps(inferred_records, indent=2), encoding="utf-8")
    (output_dir / "domain_counts.json").write_text(
        json.dumps([{"domain": d, "count": c} for d, c in domain_counts.most_common()], indent=2),
        encoding="utf-8",
    )

    copied, existing = merge_legacy_records(ai_data_final, output_dir)

    alert_flags: list[str] = []
    source_root_status = {str(root): root.exists() for root in source_roots}
    if scanned == 0:
        alert_flags.append("no_files_scanned")
    if scanned >= 1000 and len(records) == 0:
        alert_flags.append("zero_emails_after_large_scan")
    if not source_root_status.get(str(parser_root), False):
        alert_flags.append("parser_root_missing")
    if not source_root_status.get(str(ai_data_final / "email_extracted"), False):
        alert_flags.append("legacy_email_extracted_missing")

    report = {
        "ok": len(alert_flags) == 0,
        "timestamp": now,
        "parser_root": str(parser_root),
        "ai_data_final": str(ai_data_final),
        "source_roots": source_root_status,
        "alert_flags": alert_flags,
        "scanned_files": scanned,
        "scanned_by_extension": dict(scanned_by_ext),
        "total_unique_emails": len(records),
        "verified_emails": type_counts.get("verified", 0),
        "inferred_emails": type_counts.get("inferred", 0),
        "inferred_methods": dict(inferred_methods),
        "total_unique_domains": len(domain_counts),
        "top_domains": [{"domain": d, "count": c} for d, c in domain_counts.most_common(30)],
        "contact_rows_scanned": len(contact_rows),
        "company_domain_hints": len(company_domains),
        "company_domain_hints_from_store": len(company_store_hints),
        "legacy_merge": {
            "source": str(ai_data_final / "email_extracted"),
            "target": str(output_dir / "records"),
            "copied": copied,
            "already_present": existing,
        },
    }
    (output_dir / "extraction_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep email extraction from automated_parser and ai_data_final")
    parser.add_argument("--max-files", type=int, default=None, help="Optional cap for scanned files")
    parser.add_argument(
        "--domain-file",
        type=str,
        default=None,
        help="Optional path to domain/TLD hints text (e.g. L:/Codec - Antigravity Data set/email domains.txt)",
    )
    parser.add_argument(
        "--allow-zero",
        action="store_true",
        help="Allow zero-email result without non-zero process exit",
    )
    args = parser.parse_args()

    paths = CareerTrojanPaths()
    if args.domain_file:
        domain_file = Path(args.domain_file)
    else:
        domain_file = paths.ai_data_final.parent / "email domains.txt"

    tlds = load_tld_hints(domain_file)
    report = scan_sources(paths, tlds, max_files=args.max_files)

    print("EMAIL_DEEP_SCAN_OK=1")
    print(f"SCANNED_FILES={report['scanned_files']}")
    print(f"UNIQUE_EMAILS={report['total_unique_emails']}")
    print(f"VERIFIED_EMAILS={report['verified_emails']}")
    print(f"INFERRED_EMAILS={report['inferred_emails']}")
    print(f"UNIQUE_DOMAINS={report['total_unique_domains']}")
    print(f"ALERT_FLAGS={','.join(report.get('alert_flags', [])) if report.get('alert_flags') else 'none'}")
    print(f"EMAIL_DB={paths.ai_data_final / 'emails' / 'emails_database.json'}")
    print(f"REPORT={paths.ai_data_final / 'emails' / 'extraction_report.json'}")
    if report.get("alert_flags") and not args.allow_zero:
        print("EMAIL_DEEP_SCAN_ALERT=1")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
