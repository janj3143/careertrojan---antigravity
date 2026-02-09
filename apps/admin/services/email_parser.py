def extract_emails_from_file(file_path: Path) -> list:
def extract_emails_from_dir(email_dir: Path) -> list:

import os, re, json, csv, logging
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Set

# DATASET POINTER: All output JSON/CSV files will be saved to the ai_data directory for dashboard and downstream use.
AI_DATA_DIR = Path(__file__).resolve().parents[1] / "ai_data"
AI_DATA_DIR.mkdir(parents=True, exist_ok=True)


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}\b")
NAME_REGEX = re.compile(r"Name[:\s]+([A-Z][a-z]+(?: [A-Z][a-z]+)*)")
LOCATION_REGEX = re.compile(r"Location[:\s]+([A-Za-z ,]+)")
JOB_TITLE_REGEX = re.compile(r"Job Title[:\s]+([A-Za-z ,]+)")
EXCLUDE_DOMAIN = "@johnston-vere.co.uk"


def extract_contact_info_from_text(text: str) -> List[Dict[str, str]]:
    if not text:
        return []
    emails = EMAIL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)
    names = NAME_REGEX.findall(text)
    locations = LOCATION_REGEX.findall(text)
    job_titles = JOB_TITLE_REGEX.findall(text)
    contacts = []
    for i, email in enumerate(emails):
        contact = {
            "Name": names[i] if i < len(names) else "",
            "Location": locations[i] if i < len(locations) else "",
            "Job Title": job_titles[i] if i < len(job_titles) else "",
            "Email": email,
            "Telephone Number": phones[i] if i < len(phones) else ""
        }
        if EXCLUDE_DOMAIN not in email.lower():
            contacts.append(contact)
    return contacts

def extract_text_from_docx(filepath: Path) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except ImportError:
        return ""

def extract_text_from_pdf(filepath: Path) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(filepath))
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except ImportError:
        return ""
    except Exception:
        return ""

def extract_from_file(filepath: Path) -> str:
    suffix = filepath.suffix.lower()
    try:
        if suffix == ".txt":
            return filepath.read_text(encoding='utf-8', errors='ignore')
        elif suffix == ".docx":
            return extract_text_from_docx(filepath)
        elif suffix == ".pdf":
            return extract_text_from_pdf(filepath)
        elif suffix == ".csv":
            import pandas as pd
            df = pd.read_csv(filepath, encoding='utf-8', errors='ignore')
            return df.to_string()
        elif suffix == ".xlsx":
            import pandas as pd
            xl = pd.read_excel(filepath, sheet_name=None)
            return "\n".join(sheet.to_string() for sheet in xl.values())
        elif suffix == ".json":
            data = json.loads(filepath.read_text(encoding='utf-8', errors='ignore'))
            return json.dumps(data)
    except Exception:
        return ""
    return ""

    all_emails: Set[str] = set()
    results: Dict[str, List[Dict[str, str]]] = {}
    domain_counter = Counter()
    for data_dir in data_dirs:
        for file_path in data_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt','.docx','.pdf','.csv','.xlsx','.json']:
                text = extract_from_file(file_path)
                contacts = extract_contact_info_from_text(text)
                unique_contacts = [c for c in contacts if c["Email"] not in all_emails]
                if unique_contacts:
                    results[str(file_path)] = unique_contacts
                    all_emails.update(c["Email"] for c in unique_contacts)
                    domain_counter.update([c["Email"].split('@')[-1].lower() for c in unique_contacts])
    return results, domain_counter

def save_to_csv(results: Dict[str, List[Dict[str, str]]], csv_path: Path) -> bool:
    try:
        with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Filename", "Name", "Location", "Job Title", "Email", "Telephone Number"])
            for file, contacts in results.items():
                for contact in contacts:
                    writer.writerow([
                        file,
                        contact.get("Name", ""),
                        contact.get("Location", ""),
                        contact.get("Job Title", ""),
                        contact.get("Email", ""),
                        contact.get("Telephone Number", "")
                    ])
        return True
    except Exception as e:
        logging.warning(f"[CSV] Failed to save: {e}")
        return False

def save_to_json(results: Dict[str, List[str]], json_path: Path) -> bool:
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        return True
    except Exception as e:
        logging.warning(f"[JSON] Failed to save: {e}")
        return False

def save_domain_stats(domain_counter: Counter, stats_path: Path) -> bool:
    try:
        with open(stats_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Domain", "Count"])
            for domain, count in domain_counter.most_common():
                writer.writerow([domain, count])
        return True
    except Exception as e:
        logging.warning(f"[STATS] Failed to save: {e}")
        return False

def run_email_parsing_and_export():
    # Directories to scan (add more as needed)
    data_dirs = [
        AI_DATA_DIR,
        Path("../data"),
        Path("../logs"),  # Updated from working_copy
        Path("../admin_portal/data"),
    ]
    results, domain_counter = parse_all_emails(data_dirs)
    csv_path = AI_DATA_DIR / "emails_output.csv"
    json_path = AI_DATA_DIR / "emails_output.json"
    stats_path = AI_DATA_DIR / "email_domain_stats.csv"
    save_to_csv(results, csv_path)
    save_to_json(results, json_path)
    save_domain_stats(domain_counter, stats_path)
    return {
        "csv": str(csv_path),
        "json": str(json_path),
        "stats": str(stats_path),
        "total_emails": sum(len(v) for v in results.values()),
        "unique_domains": len(domain_counter),
        "top_domains": domain_counter.most_common(10)
    }
