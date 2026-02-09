#!/usr/bin/env python3
"""
Automatic Data Ingestion Service - Real-Time AI Enrichment Pipeline
====================================================================

This service automatically enriches the IntelliCV AI system whenever:
- A user registers (adds profile data to AI database)
- A user uploads a resume (adds CV data to AI enrichment)
- A user updates their profile (updates AI intelligence)
- Any new data is parsed by resume_parser

AUTOMATIC FLOW:
1. User Action (register/upload/update) →
2. Portal Bridge parses data →
3. THIS SERVICE automatically copies to ai_data_final →
4. AI enrichment runs automatically →
5. All pages immediately have access to new enriched data

This ensures the AI system continuously learns from every user interaction.
"""

import sys
import os
import json
import shutil
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)


class AutomaticDataIngestionService:
    """
    Automatically ingests user data into the AI system for continuous enrichment.

    This service acts as the bridge between user actions and AI intelligence:
    - Watches for new resume uploads
    - Automatically categorizes and stores data
    - Triggers AI enrichment pipelines
    - Updates system-wide intelligence
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize the automatic data ingestion service"""
        # Default to the project root (not admin_portal/) so ai_data_final is
        # written to the canonical location used by downstream AI consumers.
        self.base_path = Path(base_path) if base_path else Path(__file__).resolve().parents[2]

        # Source directory (where resume_parser saves)
        self.source_dir = self.base_path / "ai_data" / "complete_parsing_output"

        # Destination directory (where real_ai_connector reads from)
        self.ai_data_final = self.base_path / "ai_data_final"

        # Ensure directories exist
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.ai_data_final.mkdir(parents=True, exist_ok=True)

        # Create category subdirectories
        self.categories = {
            "cv_files": self.ai_data_final / "cv_files",
            "companies": self.ai_data_final / "companies",
            "skills": self.ai_data_final / "skills",
            "job_titles": self.ai_data_final / "job_titles",
            "users": self.ai_data_final / "users",
            "profiles": self.ai_data_final / "profiles"
        }

        for category_dir in self.categories.values():
            category_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "total_ingested": 0,
            "cv_files_added": 0,
            "companies_added": 0,
            "skills_added": 0,
            "profiles_added": 0,
            "last_ingestion": None,
            "errors": 0
        }

        logger.info(f"Automatic Data Ingestion Service initialized")
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Destination: {self.ai_data_final}")

    def ingest_user_registration(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically ingest user registration data into AI system.

        Called automatically when a user registers.

        Args:
            user_data: User registration data (name, email, profile info)

        Returns:
            Ingestion result with file path and status
        """
        try:
            logger.info(f"Ingesting user registration: {user_data.get('email', 'unknown')}")

            # Create unique user profile
            user_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            profile_data = {
                "user_id": user_id,
                "created_at": timestamp,
                "email": user_data.get("email", ""),
                "name": user_data.get("name", ""),
                "profile": user_data.get("profile", {}),
                "source": "user_registration",
                "enrichment_status": "pending",
                "data_type": "user_profile"
            }

            # Save to profiles directory
            profile_file = self.categories["profiles"] / f"user_{user_id}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            self.stats["profiles_added"] += 1
            self.stats["total_ingested"] += 1
            self.stats["last_ingestion"] = timestamp

            logger.info(f"✅ User profile ingested: {profile_file}")

            return {
                "status": "success",
                "user_id": user_id,
                "file_path": str(profile_file),
                "message": "User profile automatically added to AI system"
            }

        except Exception as e:
            logger.error(f"Error ingesting user registration: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "message": str(e)
            }

    def ingest_resume_upload(self, resume_data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Automatically ingest uploaded resume into AI system.

        Called automatically when a user uploads a resume.

        Args:
            resume_data: Parsed resume data from resume_parser
            user_id: Optional user identifier

        Returns:
            Ingestion result with file path and status
        """
        try:
            logger.info(f"Ingesting resume upload for user: {user_id or 'anonymous'}")

            # Create unique CV entry
            cv_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            # Enrich resume data with metadata
            enriched_resume = {
                "cv_id": cv_id,
                "user_id": user_id,
                "ingested_at": timestamp,
                "source": "user_upload",
                "data_type": "cv_file",
                "enrichment_status": "auto_ingested",
                **resume_data  # Include all parsed resume data
            }

            # Save to cv_files directory
            cv_file = self.categories["cv_files"] / f"cv_{cv_id}.json"
            with open(cv_file, 'w', encoding='utf-8') as f:
                json.dump(enriched_resume, f, indent=2, ensure_ascii=False)

            # Also extract and save skills separately
            if "skills" in resume_data and resume_data["skills"]:
                self._extract_and_save_skills(resume_data["skills"], cv_id)

            # Extract and save job titles
            if "job_titles" in resume_data and resume_data["job_titles"]:
                self._extract_and_save_job_titles(resume_data["job_titles"], cv_id)

            # Extract and save companies
            if "companies" in resume_data and resume_data["companies"]:
                self._extract_and_save_companies(resume_data["companies"], cv_id)

            self.stats["cv_files_added"] += 1
            self.stats["total_ingested"] += 1
            self.stats["last_ingestion"] = timestamp

            logger.info(f"✅ Resume ingested: {cv_file}")

            return {
                "status": "success",
                "cv_id": cv_id,
                "file_path": str(cv_file),
                "message": "Resume automatically added to AI system for enrichment",
                "skills_extracted": len(resume_data.get("skills", [])),
                "companies_extracted": len(resume_data.get("companies", []))
            }

        except Exception as e:
            logger.error(f"Error ingesting resume upload: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "message": str(e)
            }

    def ingest_profile_update(self, profile_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Automatically ingest profile update into AI system.

        Called automatically when a user updates their profile.

        Args:
            profile_data: Updated profile data
            user_id: User identifier

        Returns:
            Ingestion result with file path and status
        """
        try:
            logger.info(f"Ingesting profile update for user: {user_id}")

            timestamp = datetime.now().isoformat()

            # Find existing user profile or create new
            existing_files = list(self.categories["profiles"].glob(f"user_{user_id}.json"))

            if existing_files:
                # Update existing profile
                profile_file = existing_files[0]
                with open(profile_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

                # Merge updates
                existing_data.update({
                    "updated_at": timestamp,
                    "profile": profile_data,
                    "enrichment_status": "updated_pending_enrichment"
                })

                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)

                logger.info(f"✅ Profile updated: {profile_file}")
            else:
                # Create new profile
                profile_data_full = {
                    "user_id": user_id,
                    "created_at": timestamp,
                    "profile": profile_data,
                    "source": "profile_update",
                    "enrichment_status": "pending",
                    "data_type": "user_profile"
                }

                profile_file = self.categories["profiles"] / f"user_{user_id}.json"
                with open(profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile_data_full, f, indent=2, ensure_ascii=False)

                self.stats["profiles_added"] += 1
                logger.info(f"✅ New profile created: {profile_file}")

            self.stats["total_ingested"] += 1
            self.stats["last_ingestion"] = timestamp

            return {
                "status": "success",
                "user_id": user_id,
                "file_path": str(profile_file),
                "message": "Profile automatically updated in AI system"
            }

        except Exception as e:
            logger.error(f"Error ingesting profile update: {e}")
            self.stats["errors"] += 1
            return {
                "status": "error",
                "message": str(e)
            }

    def ingest_parsed_directory(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Bulk-ingest the latest Complete Data Parser outputs.

        This is the ingestion entrypoint used by automated_parser/run_full_ingest.py.

        It reads the newest extracted_* artifacts under ai_data/complete_parsing_output
        and materializes them into ai_data_final category folders so downstream AI
        consumers can pick them up.
        """
        summary: Dict[str, int] = {
            "candidates_ingested": 0,
            "companies_ingested": 0,
            "skills_ingested": 0,
            "job_titles_ingested": 0,
            "contacts_snapshots_written": 0,
            "emails_snapshots_written": 0,
            "errors": 0,
        }

        try:
            self.source_dir.mkdir(parents=True, exist_ok=True)
            self.ai_data_final.mkdir(parents=True, exist_ok=True)

            candidates_path = self._latest_output_file("extracted_candidates_", suffix=".json")
            companies_path = self._latest_output_file("extracted_companies_", suffix=".json")
            contacts_path = self._latest_output_file("extracted_contacts_", suffix=".json")
            emails_path = self._latest_output_file("extracted_emails_", suffix=".json")
            consolidated_path = self._latest_output_file("consolidated_metadata_", suffix=".json")

            if not any([candidates_path, companies_path, contacts_path, emails_path, consolidated_path]):
                logger.warning(f"No parser outputs found in: {self.source_dir}")
                return summary

            # Candidates → cv_files
            if candidates_path and candidates_path.exists():
                try:
                    with open(candidates_path, "r", encoding="utf-8") as f:
                        candidates = json.load(f)
                    if isinstance(candidates, list):
                        for idx, candidate in enumerate(candidates):
                            if limit is not None and idx >= limit:
                                break
                            if not isinstance(candidate, dict):
                                continue
                            cv_id = str(uuid.uuid4())
                            payload = {
                                "cv_id": cv_id,
                                "ingested_at": datetime.now().isoformat(),
                                "source": "complete_parser",
                                "data_type": "cv_file",
                                "enrichment_status": "bulk_ingested",
                                **candidate,
                            }
                            cv_file = self.categories["cv_files"] / f"cv_{cv_id}.json"
                            with open(cv_file, "w", encoding="utf-8") as out:
                                json.dump(payload, out, indent=2, ensure_ascii=False, default=str)
                            summary["candidates_ingested"] += 1
                            self.stats["cv_files_added"] += 1
                            self.stats["total_ingested"] += 1
                except Exception as exc:
                    logger.error(f"Error ingesting candidates from {candidates_path}: {exc}")
                    summary["errors"] += 1
                    self.stats["errors"] += 1

            # Companies → companies
            if companies_path and companies_path.exists():
                try:
                    with open(companies_path, "r", encoding="utf-8") as f:
                        companies = json.load(f)

                    company_names: List[str] = []
                    if isinstance(companies, list):
                        for item in companies:
                            if isinstance(item, str):
                                company_names.append(item)
                            elif isinstance(item, dict):
                                for key in ("company", "company_name", "name"):
                                    value = item.get(key)
                                    if isinstance(value, str) and value.strip():
                                        company_names.append(value)
                                        break

                    if company_names:
                        self._extract_and_save_companies(company_names, source_id="complete_parser")
                        summary["companies_ingested"] = len({n.strip().lower() for n in company_names if n.strip()})
                except Exception as exc:
                    logger.error(f"Error ingesting companies from {companies_path}: {exc}")
                    summary["errors"] += 1
                    self.stats["errors"] += 1

            # Consolidated metadata → skills + job_titles
            if consolidated_path and consolidated_path.exists():
                try:
                    with open(consolidated_path, "r", encoding="utf-8") as f:
                        consolidated = json.load(f)

                    skills = consolidated.get("skills") if isinstance(consolidated, dict) else None
                    titles = consolidated.get("job_titles") if isinstance(consolidated, dict) else None

                    if isinstance(skills, list) and skills:
                        self._extract_and_save_skills([s for s in skills if isinstance(s, str)], source_id="complete_parser")
                        summary["skills_ingested"] = len({s.strip().lower() for s in skills if isinstance(s, str) and s.strip()})

                    if isinstance(titles, list) and titles:
                        self._extract_and_save_job_titles([t for t in titles if isinstance(t, str)], source_id="complete_parser")
                        summary["job_titles_ingested"] = len({t.strip().lower() for t in titles if isinstance(t, str) and t.strip()})
                except Exception as exc:
                    logger.error(f"Error ingesting consolidated metadata from {consolidated_path}: {exc}")
                    summary["errors"] += 1
                    self.stats["errors"] += 1

            # Contacts/emails → store snapshots (keeps data available without inventing new schema)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if contacts_path and contacts_path.exists():
                try:
                    snapshot = self.categories["users"] / f"contacts_snapshot_{timestamp}.json"
                    shutil.copy2(contacts_path, snapshot)
                    summary["contacts_snapshots_written"] += 1
                except Exception as exc:
                    logger.error(f"Error snapshotting contacts from {contacts_path}: {exc}")
                    summary["errors"] += 1
                    self.stats["errors"] += 1

            if emails_path and emails_path.exists():
                try:
                    snapshot = self.categories["users"] / f"emails_snapshot_{timestamp}.json"
                    shutil.copy2(emails_path, snapshot)
                    summary["emails_snapshots_written"] += 1
                except Exception as exc:
                    logger.error(f"Error snapshotting emails from {emails_path}: {exc}")
                    summary["errors"] += 1
                    self.stats["errors"] += 1

            self.stats["last_ingestion"] = datetime.now().isoformat()
            logger.info(f"✅ Bulk ingestion complete: {summary}")
            return summary

        except Exception as exc:
            logger.error(f"Bulk ingestion failed: {exc}")
            summary["errors"] += 1
            self.stats["errors"] += 1
            return summary

    def _latest_output_file(self, prefix: str, suffix: str = ".json") -> Optional[Path]:
        candidates = sorted(
            self.source_dir.glob(f"{prefix}*{suffix}"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
        return candidates[0] if candidates else None

    def _extract_and_save_skills(self, skills: List[str], source_id: str) -> None:
        """Extract and save skills to skills directory"""
        try:
            for skill in skills:
                if not skill or not skill.strip():
                    continue

                # Create skill entry
                skill_id = hashlib.md5(skill.lower().encode()).hexdigest()[:12]
                skill_file = self.categories["skills"] / f"skill_{skill_id}.json"

                # Check if skill exists
                if skill_file.exists():
                    with open(skill_file, 'r', encoding='utf-8') as f:
                        existing_skill = json.load(f)

                    # Update frequency and sources
                    existing_skill["frequency"] = existing_skill.get("frequency", 1) + 1
                    existing_skill["sources"] = existing_skill.get("sources", [])
                    if source_id not in existing_skill["sources"]:
                        existing_skill["sources"].append(source_id)
                    existing_skill["last_seen"] = datetime.now().isoformat()

                    with open(skill_file, 'w', encoding='utf-8') as f:
                        json.dump(existing_skill, f, indent=2, ensure_ascii=False)
                else:
                    # Create new skill entry
                    skill_data = {
                        "skill_id": skill_id,
                        "skill_name": skill,
                        "frequency": 1,
                        "sources": [source_id],
                        "first_seen": datetime.now().isoformat(),
                        "last_seen": datetime.now().isoformat(),
                        "category": "auto_extracted",
                        "data_type": "skill"
                    }

                    with open(skill_file, 'w', encoding='utf-8') as f:
                        json.dump(skill_data, f, indent=2, ensure_ascii=False)

                    self.stats["skills_added"] += 1

        except Exception as e:
            logger.error(f"Error extracting skills: {e}")

    def _extract_and_save_job_titles(self, job_titles: List[str], source_id: str) -> None:
        """Extract and save job titles to job_titles directory"""
        try:
            for title in job_titles:
                if not title or not title.strip():
                    continue

                # Create job title entry
                title_id = hashlib.md5(title.lower().encode()).hexdigest()[:12]
                title_file = self.categories["job_titles"] / f"title_{title_id}.json"

                # Check if title exists
                if title_file.exists():
                    with open(title_file, 'r', encoding='utf-8') as f:
                        existing_title = json.load(f)

                    # Update frequency
                    existing_title["frequency"] = existing_title.get("frequency", 1) + 1
                    existing_title["sources"] = existing_title.get("sources", [])
                    if source_id not in existing_title["sources"]:
                        existing_title["sources"].append(source_id)
                    existing_title["last_seen"] = datetime.now().isoformat()

                    with open(title_file, 'w', encoding='utf-8') as f:
                        json.dump(existing_title, f, indent=2, ensure_ascii=False)
                else:
                    # Create new title entry
                    title_data = {
                        "title_id": title_id,
                        "job_title": title,
                        "frequency": 1,
                        "sources": [source_id],
                        "first_seen": datetime.now().isoformat(),
                        "last_seen": datetime.now().isoformat(),
                        "data_type": "job_title"
                    }

                    with open(title_file, 'w', encoding='utf-8') as f:
                        json.dump(title_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error extracting job titles: {e}")

    def _extract_and_save_companies(self, companies: List[str], source_id: str) -> None:
        """Extract and save companies to companies directory"""
        try:
            for company in companies:
                if not company or not company.strip():
                    continue

                # Create company entry
                company_id = hashlib.md5(company.lower().encode()).hexdigest()[:12]
                company_file = self.categories["companies"] / f"company_{company_id}.json"

                # Check if company exists
                if company_file.exists():
                    with open(company_file, 'r', encoding='utf-8') as f:
                        existing_company = json.load(f)

                    # Update frequency
                    existing_company["frequency"] = existing_company.get("frequency", 1) + 1
                    existing_company["sources"] = existing_company.get("sources", [])
                    if source_id not in existing_company["sources"]:
                        existing_company["sources"].append(source_id)
                    existing_company["last_seen"] = datetime.now().isoformat()

                    with open(company_file, 'w', encoding='utf-8') as f:
                        json.dump(existing_company, f, indent=2, ensure_ascii=False)
                else:
                    # Create new company entry
                    company_data = {
                        "company_id": company_id,
                        "company_name": company,
                        "frequency": 1,
                        "sources": [source_id],
                        "first_seen": datetime.now().isoformat(),
                        "last_seen": datetime.now().isoformat(),
                        "data_type": "company"
                    }

                    with open(company_file, 'w', encoding='utf-8') as f:
                        json.dump(company_data, f, indent=2, ensure_ascii=False)

                    self.stats["companies_added"] += 1

        except Exception as e:
            logger.error(f"Error extracting companies: {e}")

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get current ingestion statistics"""
        return {
            **self.stats,
            "total_cv_files": len(list(self.categories["cv_files"].glob("*.json"))),
            "total_companies": len(list(self.categories["companies"].glob("*.json"))),
            "total_skills": len(list(self.categories["skills"].glob("*.json"))),
            "total_profiles": len(list(self.categories["profiles"].glob("*.json"))),
            "total_job_titles": len(list(self.categories["job_titles"].glob("*.json")))
        }


# Singleton instance
_ingestion_service = None

def get_ingestion_service() -> AutomaticDataIngestionService:
    """Get singleton ingestion service instance"""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = AutomaticDataIngestionService()
    return _ingestion_service


def main():
    """Main function for testing"""
    logger.info("Automatic Data Ingestion Service - Test Mode")
    logger.info("=" * 60)

    service = get_ingestion_service()

    # Show current stats
    stats = service.get_ingestion_stats()
    logger.info("Current System Stats:")
    logger.info(f"  Total CV Files: {stats['total_cv_files']}")
    logger.info(f"  Total Companies: {stats['total_companies']}")
    logger.info(f"  Total Skills: {stats['total_skills']}")
    logger.info(f"  Total Profiles: {stats['total_profiles']}")
    logger.info(f"  Total Job Titles: {stats['total_job_titles']}")
    logger.info(f"  Total Ingested: {stats['total_ingested']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  Last Ingestion: {stats['last_ingestion']}")

    logger.info("\n✅ Automatic Data Ingestion Service is ready!")
    logger.info("All user uploads will automatically enrich the AI system.")


if __name__ == "__main__":
    main()
