#!/usr/bin/env python3
"""
IntelliCV Complete Data Parser - Master Historical Data Processing Engine
===========================================================================

This comprehensive parser processes ALL historical data from multiple sources:
- CV/Resume files (PDF, DOC, DOCX, TXT)
- Email attachments and archives (going back to 2011)
- CSV data files (Candidates, Companies, Contacts, etc.)
- Excel spreadsheets and databases
- Web-scraped company intelligence data
- Enriched AI outputs from previous runs

Designed specifically for the IntelliCV Admin Portal to prepare all historical
data for AI enrichment and provide a complete dataset for analysis.
"""

import sys
import os
import re
import json
import csv
import uuid
import hashlib
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import logging
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger, LoggingMixin
from utils.exception_handler import ExceptionHandler, SafeOperationsMixin

# Initialize logging
setup_logging()
logger = get_logger(__name__)

class ResumeParser(LoggingMixin, SafeOperationsMixin):
    """
    Master data parser that processes all historical data from multiple sources
    and prepares it for AI enrichment in the IntelliCV system.
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize the complete data parser with all necessary configurations"""
        super().__init__()

        # Set up base paths
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.data_directories = self._discover_data_directories()

        # Output directories
        self.output_dir = self.base_path / "ai_data" / "complete_parsing_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Regex patterns for data extraction
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'(?:\+\d{1,3}[-.\s]?)?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')
        self.date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b')

        # File extensions to process
        self.supported_extensions = {
            'documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
            'data': {'.csv', '.xlsx', '.xls', '.json'},
            'images': {'.jpg', '.jpeg', '.png', '.tiff'},  # For OCR processing
            'archives': {'.zip', '.rar', '.7z'}  # For extracting historical data
        }

        # Statistics tracking
        self.stats = {
            "total_files_found": 0,
            "total_files_processed": 0,
            "documents_processed": 0,
            "emails_extracted": 0,
            "companies_found": 0,
            "candidates_processed": 0,
            "contacts_extracted": 0,
            "skills_identified": 0,
            "errors_encountered": 0,
            "processing_start_time": datetime.now(),
            "data_directories_scanned": 0,
            "historical_emails_found": 0,
            "cv_attachments_processed": 0
        }

        # Data storage
        self.extracted_data = {
            "candidates": [],
            "companies": [],
            "contacts": [],
            "emails": [],
            "skills": set(),
            "job_titles": set(),
            "locations": set(),
            "education": [],
            "certifications": [],
            "projects": [],
            "metadata": {}
        }

        logger.info(f"Complete Data Parser initialized")
        logger.info(f"Base path: {self.base_path}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Data directories discovered: {len(self.data_directories)}")

    def _discover_data_directories(self) -> List[Path]:
        """Discover all potential data directories in the IntelliCV system"""
        include_absolute_fallback = os.getenv("INTELLICV_INCLUDE_ABSOLUTE_DATA_FALLBACK", "false").lower() == "true"

        potential_directories = [
            # Main data directories
            self.base_path / "data",
            # Primary ingestion drop (provided by customer)
            self.base_path / "automated_parser",
            self.base_path / "Data_forAi_Enrichment_linked_Admin_portal_final" / "data",
            self.base_path / "ai_data",
            self.base_path / "ai_enriched_output",
            self.base_path / "csv_repaired_files",
            self.base_path / "csv_parsed_output",

            # Historical data locations
            self.base_path.parent / "data",
            self.base_path.parent / "SANDBOX" / "admin_portal" / "data",
            self.base_path.parent / "admin_portal" / "data",

            # Email and attachment directories
            self.base_path / "email_attachments",
            self.base_path / "historical_cvs",
            self.base_path / "outlook_exports",

            # Working directories
            self.base_path / "working_copy",
            self.base_path / "enriched_output",

            # Legacy directories
            self.base_path.parent / "IntelliCV" / "data",
        ]

        # Absolute fallback is opt-in only (it can be extremely large).
        if include_absolute_fallback:
            potential_directories.append(Path("C:/IntelliCV/data"))

        # Filter to existing directories
        existing_dirs = []
        for directory in potential_directories:
            if directory.exists() and directory.is_dir():
                existing_dirs.append(directory)
                logger.info(f"Found data directory: {directory}")

        return existing_dirs

    def scan_all_data_sources(self) -> Dict[str, Any]:
        """
        Comprehensive scan of all data sources to catalog available files
        Returns detailed inventory of all discoverable data
        """
        logger.info("Starting comprehensive data source scan...")

        inventory = {
            "directories_scanned": [],
            "file_types_found": defaultdict(int),
            "file_inventory": [],
            "potential_cvs": [],
            "potential_company_data": [],
            "potential_contact_data": [],
            "email_files": [],
            "historical_data": [],
            "scan_summary": {}
        }

        total_files = 0

        for data_dir in self.data_directories:
            logger.info(f"Scanning directory: {data_dir}")
            inventory["directories_scanned"].append(str(data_dir))

            try:
                # Recursively scan all files
                for file_path in data_dir.rglob("*"):
                    if file_path.is_file():
                        total_files += 1
                        file_ext = file_path.suffix.lower()
                        inventory["file_types_found"][file_ext] += 1

                        file_info = {
                            "path": str(file_path),
                            "name": file_path.name,
                            "extension": file_ext,
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime,
                            "category": self._categorize_file(file_path)
                        }
                        inventory["file_inventory"].append(file_info)

                        # Categorize files by potential content
                        if self._looks_like_cv(file_path):
                            inventory["potential_cvs"].append(file_info)
                        elif self._looks_like_company_data(file_path):
                            inventory["potential_company_data"].append(file_info)
                        elif self._looks_like_contact_data(file_path):
                            inventory["potential_contact_data"].append(file_info)
                        elif self._looks_like_email_data(file_path):
                            inventory["email_files"].append(file_info)
                        elif self._is_historical_data(file_path):
                            inventory["historical_data"].append(file_info)

            except Exception as e:
                logger.error(f"Error scanning directory {data_dir}: {e}")
                inventory["scan_summary"][str(data_dir)] = f"Error: {e}"
                continue

            inventory["scan_summary"][str(data_dir)] = f"Scanned successfully"

        self.stats["total_files_found"] = total_files
        self.stats["data_directories_scanned"] = len(self.data_directories)

        # Save inventory
        inventory_file = self.output_dir / f"data_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(inventory_file, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Data source scan completed. Found {total_files} files across {len(self.data_directories)} directories")
        logger.info(f"Inventory saved to: {inventory_file}")

        return inventory

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on name patterns and extensions"""
        name_lower = file_path.name.lower()
        ext_lower = file_path.suffix.lower()

        # Document categories
        if ext_lower in self.supported_extensions['documents']:
            if any(keyword in name_lower for keyword in ['cv', 'resume', 'curriculum']):
                return 'cv_document'
            elif any(keyword in name_lower for keyword in ['cover', 'letter']):
                return 'cover_letter'
            else:
                return 'document'

        # Data file categories
        elif ext_lower in self.supported_extensions['data']:
            if any(keyword in name_lower for keyword in ['candidate', 'resume', 'cv']):
                return 'candidate_data'
            elif any(keyword in name_lower for keyword in ['company', 'companies', 'client']):
                return 'company_data'
            elif any(keyword in name_lower for keyword in ['contact', 'email', 'phone']):
                return 'contact_data'
            else:
                return 'data_file'

        # Other categories
        elif ext_lower in self.supported_extensions['images']:
            return 'image_file'
        elif ext_lower in self.supported_extensions['archives']:
            return 'archive_file'
        else:
            return 'other'

    def _looks_like_cv(self, file_path: Path) -> bool:
        """Determine if file likely contains CV/resume data"""
        name_lower = file_path.name.lower()
        cv_keywords = ['cv', 'resume', 'curriculum', 'vitae', 'profile']
        return any(keyword in name_lower for keyword in cv_keywords)

    def _looks_like_company_data(self, file_path: Path) -> bool:
        """Determine if file likely contains company data"""
        name_lower = file_path.name.lower()
        company_keywords = ['company', 'companies', 'client', 'employer', 'organization']
        return any(keyword in name_lower for keyword in company_keywords)

    def _looks_like_contact_data(self, file_path: Path) -> bool:
        """Determine if file likely contains contact information"""
        name_lower = file_path.name.lower()
        contact_keywords = ['contact', 'email', 'phone', 'address', 'directory']
        return any(keyword in name_lower for keyword in contact_keywords)

    def _looks_like_email_data(self, file_path: Path) -> bool:
        """Determine if file likely contains email data"""
        name_lower = file_path.name.lower()
        email_keywords = ['email', 'mail', 'outlook', 'gmail', 'yahoo', 'message']
        return any(keyword in name_lower for keyword in email_keywords)

    def _is_historical_data(self, file_path: Path) -> bool:
        """Determine if file is historical data (2011-2020)"""
        name_lower = file_path.name.lower()
        # Check for year patterns in filename
        years = re.findall(r'20[01][0-9]', name_lower)
        return len(years) > 0 and any(int(year) <= 2020 for year in years)

    def process_all_data(self, include_historical: bool = True) -> Dict[str, Any]:
        """
        Main processing function that handles all discovered data
        """
        logger.info("Starting complete data processing...")

        # First, scan all data sources
        inventory = self.scan_all_data_sources()

        processing_results = {
            "inventory": inventory,
            "processing_stats": {},
            "extracted_data_summary": {},
            "errors": [],
            "recommendations": []
        }

        # Process different file categories
        try:
            # Process CV/Resume documents
            cv_results = self._process_cv_documents(inventory["potential_cvs"])
            processing_results["cv_processing"] = cv_results

            # Process company data files
            company_results = self._process_company_data(inventory["potential_company_data"])
            processing_results["company_processing"] = company_results

            # Process contact data
            contact_results = self._process_contact_data(inventory["potential_contact_data"])
            processing_results["contact_processing"] = contact_results

            # Process email files and extract attachments
            email_results = self._process_email_data(inventory["email_files"])
            processing_results["email_processing"] = email_results

            # Process historical data if requested
            if include_historical:
                historical_results = self._process_historical_data(inventory["historical_data"])
                processing_results["historical_processing"] = historical_results

            # Generate comprehensive summary
            summary = self._generate_processing_summary(processing_results)
            processing_results["final_summary"] = summary

        except Exception as e:
            error_info = self.handle_exception(e, "Critical error during data processing")
            processing_results["errors"].append({
                "type": "critical_error",
                "message": error_info.get("message", str(e)),
                "traceback": error_info.get("traceback", "")
            })

        # Save complete results
        results_file = self.output_dir / f"complete_processing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(processing_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Complete data processing finished. Results saved to: {results_file}")

        return processing_results

    def _process_cv_documents(self, cv_files: List[Dict]) -> Dict[str, Any]:
        """Process all CV/Resume documents"""
        logger.info(f"Processing {len(cv_files)} CV documents...")

        results = {
            "files_processed": 0,
            "candidates_extracted": [],
            "skills_found": set(),
            "errors": []
        }

        for file_info in cv_files:
            try:
                file_path = Path(file_info["path"])
                candidate_data = self._extract_candidate_from_document(file_path)

                if candidate_data:
                    results["candidates_extracted"].append(candidate_data)
                    results["files_processed"] += 1

                    # Collect skills
                    if "skills" in candidate_data:
                        results["skills_found"].update(candidate_data["skills"])

                    self.stats["candidates_processed"] += 1

            except Exception as e:
                logger.error(f"Error processing CV file {file_info['path']}: {e}")
                results["errors"].append({
                    "file": file_info["path"],
                    "error": str(e)
                })
                self.stats["errors_encountered"] += 1

        # Convert set to list for JSON serialization
        results["skills_found"] = list(results["skills_found"])
        self.extracted_data["candidates"].extend(results["candidates_extracted"])
        self.extracted_data["skills"].update(results["skills_found"])

        logger.info(f"CV processing completed. {results['files_processed']} files processed successfully")

        return results

    def _extract_candidate_from_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Extract candidate information from a document"""
        try:
            # Try to extract text based on file type
            text_content = self._extract_text_from_file(file_path)

            if not text_content:
                return None

            # Extract structured data
            candidate = {
                "source_file": str(file_path),
                "file_name": file_path.name,
                "processed_date": datetime.now().isoformat(),
                "extraction_method": "resume_parser"
            }

            # Extract basic contact information
            emails = self.email_pattern.findall(text_content)
            phones = self.phone_pattern.findall(text_content)
            names = self.name_pattern.findall(text_content)

            if emails:
                candidate["emails"] = list(set(emails))
            if phones:
                candidate["phones"] = list(set(phones))
            if names:
                candidate["potential_names"] = list(set(names))

            # Extract skills (basic keyword matching)
            skills = self._extract_skills_from_text(text_content)
            if skills:
                candidate["skills"] = skills

            # Extract education information
            education = self._extract_education_from_text(text_content)
            if education:
                candidate["education"] = education

            # Extract work experience
            experience = self._extract_experience_from_text(text_content)
            if experience:
                candidate["experience"] = experience

            # Store raw text for further processing
            candidate["raw_text"] = text_content[:2000]  # First 2000 chars
            candidate["text_length"] = len(text_content)

            return candidate

        except Exception as e:
            self.handle_exception(e, f"Error extracting candidate data from {file_path}")
            return None

    def _extract_text_from_file(self, file_path: Path) -> Optional[str]:
        """Extract text content from various file types"""
        try:
            extension = file_path.suffix.lower()

            if extension == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            elif extension in ['.doc', '.docx']:
                try:
                    from docx import Document
                    doc = Document(file_path)
                    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    logger.warning("python-docx not available, skipping DOCX files")
                    return None
                except Exception as e:
                    logger.error(f"Error reading DOCX file {file_path}: {e}")
                    return None

            elif extension == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        return text
                except ImportError:
                    logger.warning("PyPDF2 not available, skipping PDF files")
                    return None
                except Exception as e:
                    logger.error(f"Error reading PDF file {file_path}: {e}")
                    return None

            else:
                logger.warning(f"Unsupported file type for text extraction: {extension}")
                return None

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from text using keyword matching"""
        # Common technical skills - this could be expanded significantly
        skill_keywords = [
            # Programming languages
            'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'typescript', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css',

            # Frameworks and libraries
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'nodejs', 'express',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn',

            # Tools and platforms
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'jira',
            'tableau', 'powerbi', 'excel', 'salesforce', 'sap',

            # Methodologies
            'agile', 'scrum', 'devops', 'ci/cd', 'machine learning', 'data science',
            'project management', 'business analysis'
        ]

        found_skills = []
        text_lower = text.lower()

        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        return found_skills

    def _extract_education_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract education information from text"""
        education = []

        # Look for degree patterns
        degree_patterns = [
            r'(bachelor|ba|bs|b\.a\.|b\.s\.)\s+(?:of|in)?\s+([a-zA-Z\s]+)',
            r'(master|ma|ms|m\.a\.|m\.s\.)\s+(?:of|in)?\s+([a-zA-Z\s]+)',
            r'(phd|ph\.d\.|doctorate|doctoral)\s+(?:of|in)?\s+([a-zA-Z\s]+)',
        ]

        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    "degree_level": match.group(1),
                    "field": match.group(2).strip(),
                    "raw_text": match.group(0)
                })

        return education

    def _extract_experience_from_text(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience from text"""
        experience = []

        # Look for job title patterns
        job_patterns = [
            r'(software engineer|developer|programmer|analyst|manager|director|consultant)',
            r'(senior|junior|lead|principal)\s+(engineer|developer|analyst|manager)',
        ]

        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                experience.append({
                    "job_title": match.group(0),
                    "raw_text": match.group(0)
                })

        return experience

    def _process_company_data(self, company_files: List[Dict]) -> Dict[str, Any]:
        """Process company data files"""
        logger.info(f"Processing {len(company_files)} company data files...")

        results = {
            "files_processed": 0,
            "companies_extracted": [],
            "errors": []
        }

        for file_info in company_files:
            try:
                file_path = Path(file_info["path"])
                company_data = self._extract_company_data_from_file(file_path)

                if company_data:
                    results["companies_extracted"].extend(company_data)
                    results["files_processed"] += 1
                    self.stats["companies_found"] += len(company_data)

            except Exception as e:
                logger.error(f"Error processing company file {file_info['path']}: {e}")
                results["errors"].append({
                    "file": file_info["path"],
                    "error": str(e)
                })
                self.stats["errors_encountered"] += 1

        self.extracted_data["companies"].extend(results["companies_extracted"])

        logger.info(f"Company data processing completed. {results['files_processed']} files processed")

        return results

    def _extract_company_data_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract company data from CSV/Excel files"""
        companies = []

        try:
            extension = file_path.suffix.lower()

            if extension == '.csv':
                import pandas as pd
                df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
                companies = self._process_company_dataframe(df, file_path)

            elif extension in ['.xlsx', '.xls']:
                import pandas as pd
                df = pd.read_excel(file_path)
                companies = self._process_company_dataframe(df, file_path)

        except Exception as e:
            logger.error(f"Error extracting company data from {file_path}: {e}")

        return companies

    def _process_company_dataframe(self, df, source_file: Path) -> List[Dict[str, Any]]:
        """Process company data from pandas DataFrame"""
        companies = []

        # Map common column name variations
        column_mapping = {
            'name': ['name', 'company_name', 'company', 'organization'],
            'email': ['email', 'email_address', 'contact_email'],
            'phone': ['phone', 'telephone', 'contact_phone', 'phone_number'],
            'address': ['address', 'location', 'city', 'country'],
            'website': ['website', 'url', 'web', 'domain']
        }

        # Find actual column names
        actual_columns = {}
        for standard_name, variations in column_mapping.items():
            for col in df.columns:
                if col.lower() in [v.lower() for v in variations]:
                    actual_columns[standard_name] = col
                    break

        # Process each row
        for index, row in df.iterrows():
            company = {
                "source_file": str(source_file),
                "row_index": index,
                "processed_date": datetime.now().isoformat()
            }

            # Extract available data
            for standard_name, actual_col in actual_columns.items():
                if pd.notna(row[actual_col]):
                    company[standard_name] = str(row[actual_col])

            # Extract emails from any text fields
            for col in df.columns:
                if pd.notna(row[col]):
                    emails = self.email_pattern.findall(str(row[col]))
                    if emails:
                        company.setdefault('extracted_emails', []).extend(emails)

            if len(company) > 3:  # More than just metadata
                companies.append(company)

        return companies

    def _process_contact_data(self, contact_files: List[Dict]) -> Dict[str, Any]:
        """Process contact data files"""
        logger.info(f"Processing {len(contact_files)} contact data files...")

        results = {
            "files_processed": 0,
            "contacts_extracted": [],
            "emails_found": 0,
            "errors": []
        }

        for file_info in contact_files:
            try:
                file_path = Path(file_info["path"])
                contact_data = self._extract_contact_data_from_file(file_path)

                if contact_data:
                    results["contacts_extracted"].extend(contact_data)
                    results["files_processed"] += 1

                    # Count emails
                    for contact in contact_data:
                        if 'emails' in contact:
                            results["emails_found"] += len(contact['emails'])

                self.stats["contacts_extracted"] += len(contact_data) if contact_data else 0

            except Exception as e:
                logger.error(f"Error processing contact file {file_info['path']}: {e}")
                results["errors"].append({
                    "file": file_info["path"],
                    "error": str(e)
                })
                self.stats["errors_encountered"] += 1

        self.extracted_data["contacts"].extend(results["contacts_extracted"])
        self.stats["emails_extracted"] += results["emails_found"]

        logger.info(f"Contact data processing completed. {results['files_processed']} files processed")

        return results

    def _extract_contact_data_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract contact data from files"""
        contacts = []

        try:
            extension = file_path.suffix.lower()

            if extension == '.csv':
                import pandas as pd
                df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
                contacts = self._process_contact_dataframe(df, file_path)

            elif extension in ['.xlsx', '.xls']:
                import pandas as pd
                df = pd.read_excel(file_path)
                contacts = self._process_contact_dataframe(df, file_path)

            elif extension == '.txt':
                # Extract emails and phones from text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

                emails = list(set(self.email_pattern.findall(text)))
                phones = list(set(self.phone_pattern.findall(text)))

                if emails or phones:
                    contacts.append({
                        "source_file": str(file_path),
                        "emails": emails,
                        "phones": phones,
                        "processed_date": datetime.now().isoformat()
                    })

        except Exception as e:
            logger.error(f"Error extracting contact data from {file_path}: {e}")

        return contacts

    def _process_contact_dataframe(self, df, source_file: Path) -> List[Dict[str, Any]]:
        """Process contact data from pandas DataFrame"""
        contacts = []

        for index, row in df.iterrows():
            contact = {
                "source_file": str(source_file),
                "row_index": index,
                "processed_date": datetime.now().isoformat()
            }

            # Extract all available data
            for col in df.columns:
                if pd.notna(row[col]):
                    value = str(row[col])
                    contact[col.lower().replace(' ', '_')] = value

                    # Check for emails and phones in any field
                    emails = self.email_pattern.findall(value)
                    phones = self.phone_pattern.findall(value)

                    if emails:
                        contact.setdefault('emails', []).extend(emails)
                    if phones:
                        contact.setdefault('phones', []).extend(phones)

            if len(contact) > 3:  # More than just metadata
                contacts.append(contact)

        return contacts

    def _process_email_data(self, email_files: List[Dict]) -> Dict[str, Any]:
        """Process email files and search for CV attachments"""
        logger.info(f"Processing {len(email_files)} email-related files...")

        results = {
            "files_processed": 0,
            "emails_extracted": [],
            "attachments_found": [],
            "historical_emails": 0,
            "errors": []
        }

        for file_info in email_files:
            try:
                file_path = Path(file_info["path"])
                email_data = self._extract_email_data_from_file(file_path)

                if email_data:
                    results["emails_extracted"].extend(email_data)
                    results["files_processed"] += 1

                    # Check for historical emails (2011-2020)
                    for email in email_data:
                        if self._is_historical_email(email):
                            results["historical_emails"] += 1

            except Exception as e:
                logger.error(f"Error processing email file {file_info['path']}: {e}")
                results["errors"].append({
                    "file": file_info["path"],
                    "error": str(e)
                })
                self.stats["errors_encountered"] += 1

        self.extracted_data["emails"].extend(results["emails_extracted"])
        self.stats["historical_emails_found"] = results["historical_emails"]

        logger.info(f"Email data processing completed. {results['files_processed']} files processed")

        return results

    def _extract_email_data_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract email data from various file formats"""
        emails = []

        try:
            extension = file_path.suffix.lower()

            if extension in ['.txt', '.eml']:
                # Plain text email files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                email_addresses = list(set(self.email_pattern.findall(content)))
                dates = list(set(self.date_pattern.findall(content)))

                if email_addresses:
                    emails.append({
                        "source_file": str(file_path),
                        "email_addresses": email_addresses,
                        "dates_found": dates,
                        "content_preview": content[:500],
                        "processed_date": datetime.now().isoformat()
                    })

            elif extension == '.csv':
                # CSV files that might contain email data
                import pandas as pd
                df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')

                for index, row in df.iterrows():
                    email_data = {"source_file": str(file_path), "row_index": index}
                    found_emails = []

                    for col in df.columns:
                        if pd.notna(row[col]):
                            value = str(row[col])
                            emails_in_field = self.email_pattern.findall(value)
                            found_emails.extend(emails_in_field)

                            # Store the field data
                            email_data[col.lower().replace(' ', '_')] = value

                    if found_emails:
                        email_data["email_addresses"] = list(set(found_emails))
                        emails.append(email_data)

        except Exception as e:
            logger.error(f"Error extracting email data from {file_path}: {e}")

        return emails

    def _is_historical_email(self, email_data: Dict) -> bool:
        """Check if email data appears to be from 2011-2020"""
        if "dates_found" in email_data:
            for date_str in email_data["dates_found"]:
                years = re.findall(r'20[01][0-9]', date_str)
                if years and any(2011 <= int(year) <= 2020 for year in years):
                    return True
        return False

    def _process_historical_data(self, historical_files: List[Dict]) -> Dict[str, Any]:
        """Process historical data files (2011-2020)"""
        logger.info(f"Processing {len(historical_files)} historical data files...")

        results = {
            "files_processed": 0,
            "historical_records": [],
            "years_covered": set(),
            "errors": []
        }

        for file_info in historical_files:
            try:
                file_path = Path(file_info["path"])
                historical_data = self._extract_historical_data_from_file(file_path)

                if historical_data:
                    results["historical_records"].extend(historical_data)
                    results["files_processed"] += 1

                    # Track years
                    for record in historical_data:
                        if "year" in record:
                            results["years_covered"].add(record["year"])

            except Exception as e:
                logger.error(f"Error processing historical file {file_info['path']}: {e}")
                results["errors"].append({
                    "file": file_info["path"],
                    "error": str(e)
                })
                self.stats["errors_encountered"] += 1

        # Convert set to list for JSON serialization
        results["years_covered"] = sorted(list(results["years_covered"]))

        logger.info(f"Historical data processing completed. {results['files_processed']} files processed")
        logger.info(f"Years covered: {results['years_covered']}")

        return results

    def _extract_historical_data_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract historical data from files"""
        historical_data = []

        try:
            # Extract year from filename
            year_match = re.search(r'20[01][0-9]', file_path.name)
            year = int(year_match.group()) if year_match else None

            # Process based on file type
            extension = file_path.suffix.lower()

            if extension in ['.csv', '.xlsx', '.xls']:
                # Structured data files
                import pandas as pd

                if extension == '.csv':
                    df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
                else:
                    df = pd.read_excel(file_path)

                for index, row in df.iterrows():
                    record = {
                        "source_file": str(file_path),
                        "year": year,
                        "row_index": index,
                        "processed_date": datetime.now().isoformat()
                    }

                    # Add all available data
                    for col in df.columns:
                        if pd.notna(row[col]):
                            record[col.lower().replace(' ', '_')] = str(row[col])

                    historical_data.append(record)

            elif extension in ['.txt', '.doc', '.docx', '.pdf']:
                # Document files
                text_content = self._extract_text_from_file(file_path)

                if text_content:
                    record = {
                        "source_file": str(file_path),
                        "year": year,
                        "content_preview": text_content[:1000],
                        "emails_found": self.email_pattern.findall(text_content),
                        "phones_found": self.phone_pattern.findall(text_content),
                        "processed_date": datetime.now().isoformat()
                    }
                    historical_data.append(record)

        except Exception as e:
            logger.error(f"Error extracting historical data from {file_path}: {e}")

        return historical_data

    def _generate_processing_summary(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of all processing results"""

        summary = {
            "processing_completion_time": datetime.now().isoformat(),
            "total_processing_time": str(datetime.now() - self.stats["processing_start_time"]),
            "overall_stats": self.stats.copy(),
            "data_quality_assessment": {},
            "recommendations": [],
            "next_steps": [],
            "ai_readiness_score": 0
        }

        # Calculate data quality metrics
        total_files = self.stats["total_files_found"]
        processed_files = self.stats["total_files_processed"]

        if total_files > 0:
            processing_rate = (processed_files / total_files) * 100
            summary["data_quality_assessment"]["processing_success_rate"] = processing_rate

            if processing_rate > 80:
                summary["data_quality_assessment"]["quality_level"] = "High"
                summary["ai_readiness_score"] += 30
            elif processing_rate > 60:
                summary["data_quality_assessment"]["quality_level"] = "Medium"
                summary["ai_readiness_score"] += 20
            else:
                summary["data_quality_assessment"]["quality_level"] = "Low"
                summary["ai_readiness_score"] += 10

        # Assess data completeness
        candidates = len(self.extracted_data["candidates"])
        companies = len(self.extracted_data["companies"])
        contacts = len(self.extracted_data["contacts"])

        summary["data_quality_assessment"]["data_completeness"] = {
            "candidates_found": candidates,
            "companies_found": companies,
            "contacts_found": contacts,
            "emails_extracted": self.stats["emails_extracted"]
        }

        # Calculate AI readiness score
        if candidates > 100:
            summary["ai_readiness_score"] += 25
        elif candidates > 50:
            summary["ai_readiness_score"] += 15
        elif candidates > 10:
            summary["ai_readiness_score"] += 10

        if companies > 50:
            summary["ai_readiness_score"] += 20
        elif companies > 20:
            summary["ai_readiness_score"] += 15
        elif companies > 5:
            summary["ai_readiness_score"] += 10

        if self.stats["emails_extracted"] > 1000:
            summary["ai_readiness_score"] += 15
        elif self.stats["emails_extracted"] > 500:
            summary["ai_readiness_score"] += 10
        elif self.stats["emails_extracted"] > 100:
            summary["ai_readiness_score"] += 5

        # Historical data bonus
        if self.stats["historical_emails_found"] > 0:
            summary["ai_readiness_score"] += 10

        # Generate recommendations
        if summary["ai_readiness_score"] > 70:
            summary["recommendations"].append("🎉 Excellent data quality! Ready for advanced AI enrichment.")
            summary["next_steps"].append("Proceed with full AI enrichment pipeline")
            summary["next_steps"].append("Implement real-time data processing")
        elif summary["ai_readiness_score"] > 50:
            summary["recommendations"].append("✅ Good data foundation. Some optimization recommended.")
            summary["next_steps"].append("Address data gaps identified in processing")
            summary["next_steps"].append("Run targeted data enrichment")
        else:
            summary["recommendations"].append("⚠️ Data quality needs improvement before AI processing.")
            summary["next_steps"].append("Focus on data cleaning and standardization")
            summary["next_steps"].append("Collect additional data sources")

        # Specific recommendations based on findings
        if candidates < 50:
            summary["recommendations"].append("📄 Consider adding more CV/resume sources")

        if companies < 20:
            summary["recommendations"].append("🏢 Expand company database for better matching")

        if self.stats["emails_extracted"] < 500:
            summary["recommendations"].append("📧 Search for additional email data sources")

        if self.stats["historical_emails_found"] == 0:
            summary["recommendations"].append("🕐 Look for historical email archives (2011-2020)")

        return summary

    def save_extracted_data(self) -> Dict[str, str]:
        """Save all extracted data to structured files"""
        logger.info("Saving extracted data to files...")

        saved_files = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save candidates data
        if self.extracted_data["candidates"]:
            candidates_file = self.output_dir / f"extracted_candidates_{timestamp}.json"
            with open(candidates_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data["candidates"], f, indent=2, ensure_ascii=False, default=str)
            saved_files["candidates"] = str(candidates_file)

            # Also save as CSV for easy viewing
            try:
                import pandas as pd
                candidates_df = pd.json_normalize(self.extracted_data["candidates"])
                candidates_csv = self.output_dir / f"extracted_candidates_{timestamp}.csv"
                candidates_df.to_csv(candidates_csv, index=False, encoding='utf-8')
                saved_files["candidates_csv"] = str(candidates_csv)
            except Exception as e:
                logger.warning(f"Could not save candidates CSV: {e}")

        # Save companies data
        if self.extracted_data["companies"]:
            companies_file = self.output_dir / f"extracted_companies_{timestamp}.json"
            with open(companies_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data["companies"], f, indent=2, ensure_ascii=False, default=str)
            saved_files["companies"] = str(companies_file)

        # Save contacts data
        if self.extracted_data["contacts"]:
            contacts_file = self.output_dir / f"extracted_contacts_{timestamp}.json"
            with open(contacts_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data["contacts"], f, indent=2, ensure_ascii=False, default=str)
            saved_files["contacts"] = str(contacts_file)

        # Save emails data
        if self.extracted_data["emails"]:
            emails_file = self.output_dir / f"extracted_emails_{timestamp}.json"
            with open(emails_file, 'w', encoding='utf-8') as f:
                json.dump(self.extracted_data["emails"], f, indent=2, ensure_ascii=False, default=str)
            saved_files["emails"] = str(emails_file)

        # Save consolidated skills and job titles
        consolidated_data = {
            "skills": list(self.extracted_data["skills"]),
            "job_titles": list(self.extracted_data["job_titles"]),
            "locations": list(self.extracted_data["locations"]),
            "extraction_timestamp": datetime.now().isoformat(),
            "total_unique_skills": len(self.extracted_data["skills"]),
            "total_unique_job_titles": len(self.extracted_data["job_titles"]),
            "total_unique_locations": len(self.extracted_data["locations"])
        }

        consolidated_file = self.output_dir / f"consolidated_metadata_{timestamp}.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False, default=str)
        saved_files["consolidated_metadata"] = str(consolidated_file)

        logger.info(f"Extracted data saved to {len(saved_files)} files")

        return saved_files


def main():
    """Main function to run the complete data parser"""
    import argparse

    parser = argparse.ArgumentParser(description="IntelliCV Complete Data Parser")
    parser.add_argument("--base-path", help="Base path for data discovery")
    parser.add_argument("--include-historical", action="store_true",
                       help="Include historical data processing (2011-2020)")
    parser.add_argument("--scan-only", action="store_true",
                       help="Only scan and catalog data, don't process")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("IntelliCV Complete Data Parser Starting...")
    logger.info("=" * 60)

    # Initialize parser
    complete_parser = ResumeParser(base_path=args.base_path)

    if args.scan_only:
        logger.info("Scanning data sources only...")
        inventory = complete_parser.scan_all_data_sources()
        logger.info(f"Scan completed. Found {inventory.get('scan_summary', {})}")
    else:
        logger.info("Processing all discovered data...")
        results = complete_parser.process_all_data(include_historical=args.include_historical)

        # Save extracted data
        saved_files = complete_parser.save_extracted_data()

        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)

        final_summary = results.get("final_summary", {})
        stats = final_summary.get("overall_stats", {})

        logger.info(f"Total files found: {stats.get('total_files_found', 0)}")
        logger.info(f"Files processed: {stats.get('total_files_processed', 0)}")
        logger.info(f"Candidates extracted: {stats.get('candidates_processed', 0)}")
        logger.info(f"Companies found: {stats.get('companies_found', 0)}")
        logger.info(f"Emails extracted: {stats.get('emails_extracted', 0)}")
        logger.info(f"Historical emails: {stats.get('historical_emails_found', 0)}")
        logger.info(f"Errors encountered: {stats.get('errors_encountered', 0)}")

        ai_readiness = final_summary.get("ai_readiness_score", 0)
        logger.info(f"\nAI Readiness Score: {ai_readiness}/100")

        if ai_readiness > 70:
            logger.info("Excellent! Your data is ready for advanced AI processing.")
        elif ai_readiness > 50:
            logger.info("Good data foundation. Some optimization recommended.")
        else:
            logger.warning("Data quality needs improvement before AI processing.")

        logger.info(f"\nOutput files saved:")
        for file_type, file_path in saved_files.items():
            logger.info(f"   {file_type}: {file_path}")

        logger.info(f"\nTotal processing time: {final_summary.get('total_processing_time', 'Unknown')}")

        recommendations = final_summary.get("recommendations", [])
        if recommendations:
            logger.info(f"\nRECOMMENDATIONS:")
            for rec in recommendations:
                logger.info(f"   {rec}")

        next_steps = final_summary.get("next_steps", [])
        if next_steps:
            logger.info(f"\nNEXT STEPS:")
            for step in next_steps:
                logger.info(f"   - {step}")

    logger.info("\nComplete Data Parser finished!")


if __name__ == "__main__":
    main()
