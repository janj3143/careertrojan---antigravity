
"""
Email & Contact Parser Module (Expanded)
- Extracts, normalizes, deduplicates, and validates contact data from files
- Links contacts to job titles and companies, supports enrichment hooks
"""
from pathlib import Path
import re, json
from typing import List, Dict, Any, Set

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}\b")
NAME_REGEX = re.compile(r"Name[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)*)")
LOCATION_REGEX = re.compile(r"Location[:\s]+([A-Za-z ,]+)")
JOB_TITLE_REGEX = re.compile(r"Job Title[:\s]+([A-Za-z ,]+)")
COMPANY_REGEX = re.compile(r"Company[:\s]+([A-Za-z0-9 &.,-]+)")
LINKEDIN_REGEX = re.compile(r"https?://(www\.)?linkedin.com/in/[A-Za-z0-9-_%]+")

def extract_contacts_from_text(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    emails = EMAIL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)
    names = NAME_REGEX.findall(text)
    locations = LOCATION_REGEX.findall(text)
    job_titles = JOB_TITLE_REGEX.findall(text)
    companies = COMPANY_REGEX.findall(text)
    linkedins = LINKEDIN_REGEX.findall(text)
    contacts = []
    for i, email in enumerate(emails):
        contact = {
            "Name": names[i] if i < len(names) else "",
            "Location": locations[i] if i < len(locations) else "",
            "Job Title": job_titles[i] if i < len(job_titles) else "",
            "Company": companies[i] if i < len(companies) else "",
            "Email": email,
            "Telephone Number": phones[i] if i < len(phones) else "",
            "LinkedIn": linkedins[i] if i < len(linkedins) else ""
        }
        if validate_email(email):
            contacts.append(contact)
    return contacts

def validate_email(email: str) -> bool:
    # Simple validation, can be extended
    return bool(EMAIL_REGEX.fullmatch(email)) and len(email) <= 100

def deduplicate_contacts(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = set()
    deduped = []
    for c in contacts:
        key = (c.get("Email", "") + c.get("Telephone Number", "")).lower()
        if key and key not in seen:
            deduped.append(c)
            seen.add(key)
    return deduped

def extract_contacts(file_path: Path) -> Dict[str, Any]:
    # Extract text from file (expand as needed)
    text = ""
    suffix = file_path.suffix.lower()
    try:
        if suffix == ".txt":
            text = file_path.read_text(encoding='utf-8', errors='ignore')
        elif suffix == ".json":
            data = json.loads(file_path.read_text(encoding='utf-8', errors='ignore'))
            text = json.dumps(data)
        # Add PDF, DOCX, CSV, XLSX support as needed
    except Exception:
        pass
    contacts = extract_contacts_from_text(text)
    contacts = deduplicate_contacts(contacts)
    return {"filename": file_path.name, "contacts": contacts}

def parse_all_contacts(resume_dir: Path) -> List[Dict[str, Any]]:
    return [extract_contacts(f) for f in resume_dir.glob("*.pdf")]

# Enrichment hook: add logic for seniority, value scoring, clustering, etc.
def enrich_contacts(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Placeholder: implement enrichment logic (e.g., flag high-value, infer seniority)
    return contacts
