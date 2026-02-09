"""
Universal Data Ingestor Service
===============================

This service handles the ingestion of ALL data types from the `automated_parser` directory
into the `ai_data_final` structure.

Supported formats:
- CSV (Candidates, Companies, Contacts)
- MSG (Emails, CVs attached to emails)
- PDF/DOC/DOCX (CVs, Job Descriptions)
- TXT (Notes)

"""

import os
import csv
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import extract_msg  # You might need to install this: pip install extract-msg
# import textract # For PDF/DOC processing
import sys
import pypdf
import docx
import zipfile

# Set UTF-8 encoding for Python
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import DataIngestionTracker for deduplication
try:
    ai_data_final_path = Path(__file__).resolve().parents[2] / "ai_data_final"
    if str(ai_data_final_path) not in sys.path:
        sys.path.append(str(ai_data_final_path))
    from data_ingestion_tracker import DataIngestionTracker
    TRACKER_AVAILABLE = True
    logger.info("✅ Data Ingestion Tracker integrated successfully")
except ImportError as e:
    logger.warning(f"⚠️ Data Ingestion Tracker not available: {e}")
    TRACKER_AVAILABLE = False

# Add shared_backend to path for taxonomy integration
try:
    # Assuming structure: .../admin_portal/services/universal_data_ingestor.py
    # shared_backend is at .../shared_backend
    shared_backend_path = Path(__file__).resolve().parents[2] / "shared_backend"
    if str(shared_backend_path) not in sys.path:
        sys.path.append(str(shared_backend_path))

    from services.industry_taxonomy import get_job_title_metadata, infer_industries_from_titles
    TAXONOMY_AVAILABLE = True
    logger.info("✅ Industry Taxonomy Service integrated successfully")
except ImportError as e:
    logger.warning(f"⚠️ Industry Taxonomy Service not available: {e}")
    TAXONOMY_AVAILABLE = False

class UniversalDataIngestor:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.source_dir = self.base_path / "automated_parser"
        self.dest_dir = self.base_path / "ai_data_final"

        # Destination subdirectories
        self.dirs = {
            "cv_files": self.dest_dir / "cv_files",
            "companies": self.dest_dir / "companies",
            "users": self.dest_dir / "users",
            "profiles": self.dest_dir / "profiles",
            "email_extracted": self.dest_dir / "email_extracted",
            "job_descriptions": self.dest_dir / "job_descriptions",
            "taxonomies": self.dest_dir / "taxonomies",
            "notes": self.dest_dir / "notes",
            "journal": self.dest_dir / "journal"
        }

        for d in self.dirs.values():
            d.mkdir(parents=True, exist_ok=True)

        # Initialize tracking system
        if TRACKER_AVAILABLE:
            self.tracker = DataIngestionTracker()
            self.tracker.register_source('automated_parser', self.source_dir)
            logger.info("📊 Ingestion tracking enabled - will skip already-processed files")
        else:
            self.tracker = None
            logger.warning("⚠️ Ingestion tracking disabled - may reprocess files")

        # Statistics
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }

    def ingest_all(self, progress_callback=None, force_reprocess=False):
        """
        Main entry point to ingest all data.

        Args:
            progress_callback: Optional function that accepts (current_step, total_steps, status_message)
            force_reprocess: If True, reprocess all files even if already ingested
        """
        logger.info("="*80)
        logger.info("Starting Universal Data Ingestion...")
        logger.info(f"Force reprocess: {force_reprocess}")
        logger.info("="*80)

        if not self.source_dir.exists():
            logger.error(f"Source directory not found: {self.source_dir}")
            if progress_callback:
                progress_callback(0, 1, f"Error: Source directory not found: {self.source_dir}")
            return

        # Reset statistics
        self.stats = {'processed': 0, 'skipped': 0, 'errors': 0}
        self.force_reprocess = force_reprocess

        steps = ["ZIP Archives", "CSV Files", "Excel Files", "MSG Files", "Document Files"]
        total_steps = len(steps)

        if progress_callback:
            progress_callback(0, total_steps, "Starting ingestion...")

        # Step 0: ZIP Archives (taxonomies)
        if progress_callback:
            progress_callback(0, total_steps, "Extracting ZIP archives...")
        self.process_zip_files()

        # Step 1: CSV
        if progress_callback:
            progress_callback(1, total_steps, "Processing CSV files...")
        self.process_csv_files()

        # Step 2: Excel
        if progress_callback:
            progress_callback(2, total_steps, "Processing Excel files...")
        self.process_excel_files()

        # Step 3: MSG
        if progress_callback:
            progress_callback(3, total_steps, "Processing MSG files...")
        self.process_msg_files()

        # Step 4: Documents
        if progress_callback:
            progress_callback(4, total_steps, "Processing Document files...")
        self.process_document_files() # PDF/DOC/DOCX

        if progress_callback:
            progress_callback(total_steps, total_steps, "Ingestion complete.")

        # Print statistics
        logger.info("="*80)
        logger.info("📊 INGESTION STATISTICS")
        logger.info(f"   ✅ Processed: {self.stats['processed']} files")
        logger.info(f"   ⏭️  Skipped: {self.stats['skipped']} files (already ingested)")
        logger.info(f"   ❌ Errors: {self.stats['errors']} files")
        logger.info(f"   📁 Total: {sum(self.stats.values())} files examined")
        logger.info("="*80)
        logger.info("Ingestion complete.")

        return self.stats

    def process_csv_files(self):
        """Process CSV files like Candidate.csv, Companies.csv"""
        logger.info("Processing CSV files...")

        csv_files = list(self.source_dir.glob("*.csv"))
        for csv_file in csv_files:
            # Check if already processed
            if self.tracker and not self.force_reprocess:
                if not self.tracker.needs_ingestion('automated_parser', csv_file):
                    logger.info(f"⏭️  Skipping {csv_file.name} (already ingested)")
                    self.stats['skipped'] += 1
                    continue

            try:
                logger.info(f"Processing {csv_file.name}...")

                # Try different encodings
                df = None
                for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(csv_file, on_bad_lines='skip', encoding=encoding, low_memory=False)
                        logger.info(f"Successfully read {csv_file.name} with encoding {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue

                if df is None:
                    logger.error(f"Failed to read {csv_file.name} with any supported encoding")
                    self.stats['errors'] += 1
                    continue

                # Dispatch based on filename
                rows_processed = 0
                if "Candidate" in csv_file.name:
                    rows_processed = self._ingest_candidates(df)
                elif "Compan" in csv_file.name:
                    rows_processed = self._ingest_companies(df)
                elif "Contact" in csv_file.name:
                    rows_processed = self._ingest_contacts(df)
                elif "job_match" in csv_file.name.lower():
                    rows_processed = self._ingest_job_matches(df)
                elif "Journal" in csv_file.name:
                    rows_processed = self._ingest_journal(df)
                elif "Notes" in csv_file.name:
                    rows_processed = self._ingest_notes(df)
                else:
                    # Generic CSV - save to appropriate location
                    rows_processed = self._ingest_generic_csv(df, csv_file.name)

                # Mark as ingested
                if self.tracker:
                    self.tracker.mark_ingested('automated_parser', csv_file,
                        metadata={
                            'file_type': 'csv',
                            'rows_processed': rows_processed,
                            'status': 'success'
                        })
                self.stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing {csv_file.name}: {e}")
                self.stats['errors'] += 1

    def process_excel_files(self):
        """Process Excel files (.xlsx, .xls)"""
        logger.info("Processing Excel files...")

        excel_files = list(self.source_dir.glob("*.xlsx")) + list(self.source_dir.glob("*.xls"))
        for excel_file in excel_files:
            # Check if already processed
            if self.tracker and not self.force_reprocess:
                if not self.tracker.needs_ingestion('automated_parser', excel_file):
                    logger.info(f"⏭️  Skipping {excel_file.name} (already ingested)")
                    self.stats['skipped'] += 1
                    continue

            try:
                logger.info(f"Processing {excel_file.name}...")

                # Read Excel file
                try:
                    df = pd.read_excel(excel_file)
                    logger.info(f"Successfully read {excel_file.name}")
                except Exception as e:
                    logger.error(f"Failed to read Excel {excel_file.name}: {e}")
                    self.stats['errors'] += 1
                    continue

                # Dispatch based on filename or content structure
                rows_processed = 0
                filename_lower = excel_file.name.lower()

                # Job descriptions files
                if "job" in filename_lower and ("profile" in filename_lower or "description" in filename_lower):
                    rows_processed = self._ingest_job_descriptions_excel(df, excel_file.name)
                # Taxonomy/classification files
                elif any(keyword in filename_lower for keyword in ["naics", "soc", "esco", "occupation"]):
                    rows_processed = self._ingest_taxonomy_excel(df, excel_file.name)
                # Candidate data
                elif "candidate" in filename_lower or "name" in df.columns:
                    rows_processed = self._ingest_candidates(df)
                # Company data
                elif "compan" in filename_lower:
                    rows_processed = self._ingest_companies(df)
                # Goldilocks master document
                elif "goldilocks" in filename_lower:
                    rows_processed = self._ingest_goldilocks_data(df, excel_file.name)
                else:
                    # Generic ingestion for unknown Excel types
                    logger.info(f"Ingesting generic Excel: {excel_file.name}")
                    data = df.to_dict(orient='records')
                    safe_name = "".join([c for c in excel_file.stem if c.isalnum() or c in (' ', '-', '_')]).strip()
                    output_file = self.dirs["profiles"] / f"excel_data_{safe_name}.json"
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, default=str)
                    rows_processed = len(data)

                # Mark as ingested
                if self.tracker:
                    self.tracker.mark_ingested('automated_parser', excel_file,
                        metadata={
                            'file_type': 'excel',
                            'rows_processed': rows_processed,
                            'status': 'success'
                        })
                self.stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing {excel_file.name}: {e}")
                self.stats['errors'] += 1

    def _ingest_candidates(self, df: pd.DataFrame) -> int:
        """Ingest candidate data into profiles/users with Taxonomy Integration"""
        rows_processed = 0
        for _, row in df.iterrows():
            rows_processed += 1
            # Create a profile JSON
            raw_profile = row.to_dict()
            # Clean keys and remove NaNs
            profile = {k: v for k, v in raw_profile.items() if pd.notna(v)}

            # --- NORMALIZE KEYS FOR REAL AI CONNECTOR ---
            # Map "Job Title" -> "job_title"
            if "Job Title" in profile:
                profile["job_title"] = profile["Job Title"]

            # Map "Company" -> "company"
            if "Company" in profile:
                profile["company"] = profile["Company"]

            # --- TAXONOMY INTEGRATION ---
            if TAXONOMY_AVAILABLE and "job_title" in profile:
                try:
                    jt = profile["job_title"]
                    # 1. Get metadata (industry, etc.)
                    meta = get_job_title_metadata(jt)
                    if meta:
                        profile["taxonomy_metadata"] = meta
                        if "industry" in meta:
                            profile["industry"] = meta["industry"]

                    # 2. Infer industry if not found
                    if "industry" not in profile:
                        inferred = infer_industries_from_titles([jt])
                        if inferred:
                            profile["industry"] = inferred[0]

                except Exception as e:
                    logger.warning(f"Taxonomy lookup failed for {profile.get('job_title')}: {e}")

            # Generate ID if missing
            candidate_id = str(profile.get("CandidateID", profile.get("ID", "unknown")))
            if candidate_id == "unknown":
                continue # Skip if no ID

            # Save to profiles
            output_file = self.dirs["profiles"] / f"candidate_{candidate_id}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(profile, f, indent=2)

        return rows_processed

    def _ingest_companies(self, df: pd.DataFrame) -> int:
        """Ingest company data"""
        rows_processed = 0
        for _, row in df.iterrows():
            company = row.to_dict()
            company = {k: v for k, v in company.items() if pd.notna(v)}

            company_name = str(company.get("CompanyName", company.get("Name", "unknown")))
            if company_name == "unknown":
                continue

            safe_name = "".join([c for c in company_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            output_file = self.dirs["companies"] / f"company_{safe_name}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(company, f, indent=2)
            rows_processed += 1

        return rows_processed

    def _ingest_contacts(self, df: pd.DataFrame) -> int:
        """Ingest contacts"""
        # Similar logic to candidates
        # TODO: Implement contact ingestion logic
        return 0

    def process_msg_files(self):
        """Process .msg files"""
        logger.info("Processing MSG files...")
        msg_files = list(self.source_dir.glob("*.msg"))

        for msg_file in msg_files:
            # Check if already processed
            if self.tracker and not self.force_reprocess:
                if not self.tracker.needs_ingestion('automated_parser', msg_file):
                    logger.info(f"⏭️  Skipping {msg_file.name} (already ingested)")
                    self.stats['skipped'] += 1
                    continue

            try:
                logger.info(f"Processing MSG file: {msg_file.name}")

                msg = extract_msg.Message(msg_file)

                # Extract email metadata
                email_data = {
                    "sender": msg.sender,
                    "to": msg.to,
                    "cc": msg.cc,
                    "date": str(msg.date),
                    "subject": msg.subject,
                    "body": msg.body,
                    "filename": msg_file.name
                }

                # Save email data
                safe_subject = "".join([c for c in (msg.subject or "no_subject") if c.isalnum() or c in (' ', '-', '_')]).strip()[:50]
                email_output_file = self.dirs["email_extracted"] / f"email_{safe_subject}_{msg_file.stem}.json"

                with open(email_output_file, "w", encoding="utf-8") as f:
                    json.dump(email_data, f, indent=2, default=str)

                # Handle attachments (CVs)
                attachments_saved = 0
                for attachment in msg.attachments:
                    if hasattr(attachment, 'save'):
                        # Check if it looks like a CV
                        filename = attachment.longFilename or attachment.shortFilename
                        if not filename:
                            continue

                        ext = Path(filename).suffix.lower()
                        if ext in ['.pdf', '.doc', '.docx', '.rtf', '.txt']:
                            # Save to cv_files
                            save_path = self.dirs["cv_files"] / f"{msg_file.stem}_{filename}"
                            attachment.save(customPath=str(self.dirs["cv_files"]), customFilename=f"{msg_file.stem}_{filename}")
                            logger.info(f"Saved attachment: {filename}")
                            attachments_saved += 1

                msg.close()

                # Mark as ingested
                if self.tracker:
                    self.tracker.mark_ingested('automated_parser', msg_file,
                        metadata={
                            'file_type': 'msg',
                            'attachments_saved': attachments_saved,
                            'status': 'success'
                        })
                self.stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing {msg_file.name}: {e}")
                self.stats['errors'] += 1

    def process_document_files(self):
        """Process PDF/DOCX files from cv_files and source_dir"""
        logger.info("Processing Document files...")

        # Gather all files
        files_to_process = []
        if self.dirs["cv_files"].exists():
            files_to_process.extend(self.dirs["cv_files"].glob("*.*"))
        files_to_process.extend(self.source_dir.glob("*.pdf"))
        files_to_process.extend(self.source_dir.glob("*.docx"))
        files_to_process.extend(self.source_dir.glob("*.txt"))

        # Deduplicate by path
        files_to_process = list(set(files_to_process))

        for file_path in files_to_process:
            if file_path.suffix.lower() not in ['.pdf', '.docx', '.txt']:
                continue

            # Check if already processed
            if self.tracker and not self.force_reprocess:
                if not self.tracker.needs_ingestion('automated_parser', file_path):
                    logger.info(f"⏭️  Skipping {file_path.name} (already ingested)")
                    self.stats['skipped'] += 1
                    continue

            try:
                logger.info(f"Processing document: {file_path.name}")
                text = ""

                # Extract text
                if file_path.suffix.lower() == '.pdf':
                    try:
                        reader = pypdf.PdfReader(file_path)
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to read PDF {file_path.name}: {e}")
                        self.stats['errors'] += 1
                        continue

                elif file_path.suffix.lower() == '.docx':
                    try:
                        doc = docx.Document(file_path)
                        for para in doc.paragraphs:
                            text += para.text + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to read DOCX {file_path.name}: {e}")
                        self.stats['errors'] += 1
                        continue

                elif file_path.suffix.lower() == '.txt':
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                    except Exception as e:
                        logger.warning(f"Failed to read TXT {file_path.name}: {e}")
                        self.stats['errors'] += 1
                        continue

                if not text.strip():
                    logger.warning(f"No text extracted from {file_path.name}")
                    self.stats['errors'] += 1
                    continue

                # Create a basic profile
                profile = {
                    "source_file": file_path.name,
                    "raw_text": text,
                    "ingestion_date": str(pd.Timestamp.now()),
                    "type": "parsed_cv"
                }

                # Try to find email (simple regex)
                import re
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                if emails:
                    profile["email"] = emails[0]

                # Save to profiles
                safe_name = "".join([c for c in file_path.stem if c.isalnum() or c in (' ', '-', '_')]).strip()
                output_file = self.dirs["profiles"] / f"doc_profile_{safe_name}.json"

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(profile, f, indent=2)

                # Mark as ingested
                if self.tracker:
                    self.tracker.mark_ingested('automated_parser', file_path,
                        metadata={
                            'file_type': file_path.suffix.lower(),
                            'text_length': len(text),
                            'status': 'success'
                        })
                self.stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error processing document {file_path.name}: {e}")
                self.stats['errors'] += 1

    def process_zip_files(self):
        """Extract and process ZIP archives containing taxonomies"""
        logger.info("Processing ZIP archives...")

        zip_files = list(self.source_dir.glob("*.zip"))
        for zip_file in zip_files:
            # Check if already processed
            if self.tracker and not self.force_reprocess:
                if not self.tracker.needs_ingestion('automated_parser', zip_file):
                    logger.info(f"⏭️  Skipping {zip_file.name} (already extracted)")
                    self.stats['skipped'] += 1
                    continue

            try:
                logger.info(f"Extracting {zip_file.name}...")

                # Extract to taxonomies directory with subfolder
                extract_dir = self.dirs["taxonomies"] / zip_file.stem
                extract_dir.mkdir(parents=True, exist_ok=True)

                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                logger.info(f"✅ Extracted {zip_file.name} to {extract_dir}")

                # Mark as ingested
                if self.tracker:
                    self.tracker.mark_ingested('automated_parser', zip_file,
                        metadata={
                            'file_type': 'zip',
                            'extract_location': str(extract_dir),
                            'status': 'success'
                        })
                self.stats['processed'] += 1

            except Exception as e:
                logger.error(f"Error extracting {zip_file.name}: {e}")
                self.stats['errors'] += 1

    def _ingest_job_matches(self, df):
        """Ingest job match results"""
        logger.info(f"  Ingesting job match data: {len(df)} rows")

        # Save as JSON for easy querying
        output_file = self.dirs["job_descriptions"] / "job_matches.json"
        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} job matches")
        return len(records)

    def _ingest_journal(self, df):
        """Ingest journal/activity log"""
        logger.info(f"  Ingesting journal data: {len(df)} rows")

        # Save to journal directory
        output_file = self.dirs["journal"] / "activity_journal.json"
        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} journal entries")
        return len(records)

    def _ingest_notes(self, df):
        """Ingest notes database"""
        logger.info(f"  Ingesting notes data: {len(df)} rows")

        # Save to notes directory
        output_file = self.dirs["notes"] / "notes_database.json"
        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} notes")
        return len(records)

    def _ingest_generic_csv(self, df, filename):
        """Ingest generic CSV file"""
        logger.info(f"  Ingesting generic CSV: {filename} with {len(df)} rows")

        # Save to appropriate directory based on filename
        safe_name = "".join([c for c in filename if c.isalnum() or c in ('.', '-', '_')]).strip()
        output_file = self.dest_dir / safe_name.replace('.csv', '.json')

        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} records to {output_file.name}")
        return len(records)

    def _ingest_job_descriptions_excel(self, df, filename):
        """Ingest job descriptions from Excel files"""
        logger.info(f"  Ingesting job descriptions from {filename}: {len(df)} rows")

        # Save to job_descriptions directory
        safe_name = "".join([c for c in filename if c.isalnum() or c in ('.', '-', '_')]).strip()
        output_file = self.dirs["job_descriptions"] / safe_name.replace('.xlsx', '.json').replace('.xls', '.json')

        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} job descriptions")
        return len(records)

    def _ingest_taxonomy_excel(self, df, filename):
        """Ingest taxonomy/classification data from Excel"""
        logger.info(f"  Ingesting taxonomy data from {filename}: {len(df)} rows")

        # Save to taxonomies directory
        safe_name = "".join([c for c in filename if c.isalnum() or c in ('.', '-', '_')]).strip()
        output_file = self.dirs["taxonomies"] / safe_name.replace('.xlsx', '.json').replace('.xls', '.json')

        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} taxonomy entries")
        return len(records)

    def _ingest_goldilocks_data(self, df, filename):
        """Ingest Goldilocks master document data"""
        logger.info(f"  Ingesting Goldilocks data from {filename}: {len(df)} rows")

        # This is a master tracking document - save to root
        safe_name = "".join([c for c in filename if c.isalnum() or c in ('.', '-', '_')]).strip()
        output_file = self.dest_dir / f"goldilocks_{safe_name.replace('.xlsx', '.json').replace('.xls', '.json')}"

        records = df.to_dict(orient='records')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Saved {len(records)} Goldilocks entries")
        return len(records)

if __name__ == "__main__":
    # Run from command line
    base_path = r"C:\IntelliCV\SANDBOX\Full system"
    ingestor = UniversalDataIngestor(base_path)
    ingestor.ingest_all()
