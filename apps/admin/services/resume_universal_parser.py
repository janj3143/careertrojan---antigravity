# IntelliCV Universal Resume & Document Parser (Enterprise Edition)
# (See previous message for full script content)
# ...full combined parser code here...
#!/usr/bin/env python3
"""
IntelliCV Universal Resume & Document Parser (Enterprise Edition)
Combines and optimizes all resume/document parsing logic from master_resume_parser, resume_parser, and resume_parser_cli.
Extracts: candidate info, skills, education, experience, certifications, contact info, file metadata, and advanced intelligence features.
"""

import sys
import os
import re
import json
import uuid
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# --- Smart Resume Enrichment ---
from enrichment.ats_scorer import ATSScorer

# --- Configuration ---

# Robust config import with fallback
try:
    from admin_portal.config.config import load_config
    cfg = load_config()
    DATA_DIR = cfg.data_dir
    OUTPUT_DIR = cfg.normalized_json_dir
    LOGS_DIR = cfg.logs_dir
except Exception:
    PROJECT_ROOT = Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 1 else Path('.')
    DATA_DIR = PROJECT_ROOT / "data"
    OUTPUT_DIR = PROJECT_ROOT / "ai_data" / "normalized"
    LOGS_DIR = PROJECT_ROOT / "working_copy" / "logs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

import logging
log_file = LOGS_DIR / f"universal_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Resume NLP Import ---

# Robust import for resume_nlp
try:
    from frontend.utils.resume_nlp import extract_profile_data_from_file
    RESUME_PARSER_AVAILABLE = True
    logger.info("[SUCCESS] Resume parser available")
except Exception as e:
    RESUME_PARSER_AVAILABLE = False
    logger.warning(f"[WARNING] Resume parser not available: {e}")
    def extract_profile_data_from_file(*args, **kwargs):
        return {}

class ResumeParser:
    """Comprehensive universal document parser with advanced intelligence features"""

    def __init__(self):
        self.processed_files = {}
        self.supported_extensions = {'.doc', '.docx', '.pdf', '.txt', '.csv', '.xlsx', '.xls'}
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'(?:\+\d{1,3}[-.\s]?)?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}')
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b')
        self.stats = {
            "total_processed": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "high_quality_profiles": 0,
            "recommended_candidates": 0
        }
        self.smart_enrichment = ATSScorer([])

    def generate_file_id(self, file_path: Path) -> str:
        try:
            content_hash = hashlib.md5((str(file_path) + str(file_path.stat().st_size)).encode()).hexdigest()[:12]
            return f"file_{content_hash}"
        except Exception:
            return f"file_{uuid.uuid4().hex[:12]}"

    def extract_basic_info(self, text: str) -> Dict[str, Any]:
        if not text:
            return {}
        emails = list(set(self.email_pattern.findall(text)))
        phones = list(set(self.phone_pattern.findall(text)))
        names = list(set(self.name_pattern.findall(text)))
        return {
            'emails': emails[:5],
            'phones': phones[:3],
            'names': names[:3]
        }

    def _enhance_profile(self, profile: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        enhanced = profile.copy()
        enhanced["source_file"] = file_path.name
        enhanced["file_size"] = file_path.stat().st_size if file_path.exists() else 0
        raw_text = profile.get("raw_text", "")
        if raw_text:
            enhanced["word_count"] = len(raw_text.split())
            enhanced["char_count"] = len(raw_text)
            enhanced["industry"] = self._detect_industry(raw_text)
        enhanced["quality_score"] = self._calculate_quality_score(profile)
        enhanced["seniority"] = self._analyze_seniority(profile.get("experience", []))
        enhanced["contact_completeness"] = self._assess_contact_completeness(profile)
        return enhanced

    def _calculate_quality_score(self, profile: Dict[str, Any]) -> int:
        score = 0
        if profile.get("name") and profile["name"] != "Unknown Candidate":
            score += 1
        if profile.get("email"):
            score += 1
        if profile.get("phone"):
            score += 1
        skills_count = len(profile.get("skills", []))
        if skills_count >= 5:
            score += 2
        elif skills_count >= 3:
            score += 1
        experience_count = len(profile.get("experience", []))
        if experience_count >= 3:
            score += 2
        elif experience_count >= 1:
            score += 1
        word_count = profile.get("word_count", 0)
        if word_count >= 500:
            score += 2
        elif word_count >= 200:
            score += 1
        return min(score, 10)

    def _analyze_seniority(self, experience: List[str]) -> str:
        all_exp = " ".join(experience).lower() if experience else ""
        if any(word in all_exp for word in ['ceo', 'cto', 'president', 'founder', 'chief']):
            return "Executive"
        elif any(word in all_exp for word in ['director', 'head of', 'vp', 'vice president']):
            return "Director"
        elif any(word in all_exp for word in ['senior', 'lead', 'principal', 'manager']):
            return "Senior"
        elif any(word in all_exp for word in ['junior', 'associate', 'assistant', 'intern']):
            return "Junior"
        else:
            return "Unknown"

    def _detect_industry(self, text: str) -> str:
        text_lower = text.lower()
        tech_keywords = ['python', 'java', 'javascript', 'software', 'developer', 'programming']
        finance_keywords = ['financial', 'banking', 'investment', 'accounting', 'audit']
        healthcare_keywords = ['medical', 'healthcare', 'patient', 'clinical', 'pharmaceutical']
        marketing_keywords = ['marketing', 'social media', 'brand', 'campaign', 'advertising']
        tech_score = sum(1 for kw in tech_keywords if kw in text_lower)
        finance_score = sum(1 for kw in finance_keywords if kw in text_lower)
        healthcare_score = sum(1 for kw in healthcare_keywords if kw in text_lower)
        marketing_score = sum(1 for kw in marketing_keywords if kw in text_lower)
        scores = {
            "Technology": tech_score,
            "Finance": finance_score,
            "Healthcare": healthcare_score,
            "Marketing": marketing_score
        }
        # Fix: get industry with highest score, default to 'General' if all zero
        if scores and max(scores.values()) > 0:
            return max(scores, key=lambda k: scores[k])
        else:
            return "General"

    def _assess_contact_completeness(self, profile: Dict[str, Any]) -> str:
        completeness_score = 0
        if profile.get("email"): completeness_score += 1
        if profile.get("phone"): completeness_score += 1
        if profile.get("linkedin"): completeness_score += 1
        if completeness_score == 3:
            return "Full"
        elif completeness_score == 2:
            return "Partial"
        elif completeness_score == 1:
            return "Minimal"
        else:
            return "None"

    def process_file(self, file_path: Path, job_target: Optional[str] = None, user_profile: Optional[object] = None) -> Optional[Dict]:
        try:
            if not file_path.is_file() or file_path.suffix.lower() not in self.supported_extensions:
                return None
            logger.info(f"Processing: {file_path}")
            profile = {}
            if RESUME_PARSER_AVAILABLE:
                profile = extract_profile_data_from_file(str(file_path))
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                profile = self.extract_basic_info(text)
                profile['raw_text'] = text
            enhanced = self._enhance_profile(profile, file_path)
            # --- Smart Resume Enrichment ---
            enhanced = self.smart_enrichment.enrich(enhanced, job_target, user_profile=user_profile)
            self.stats["total_processed"] += 1
            if enhanced.get("quality_score", 0) >= 7:
                self.stats["high_quality_profiles"] += 1
            self.stats["successful_parses"] += 1
            return enhanced
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            self.stats["failed_parses"] += 1
            return None

    def run(self, input_dir: Optional[str] = None, output_dir: Optional[str] = None, job_target: Optional[str] = None):
        # Accept None for input_dir/output_dir and use defaults
        data_dir = Path(input_dir) if input_dir else DATA_DIR
        output_path = Path(output_dir) if output_dir else OUTPUT_DIR
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"[INFO] Starting universal parser...")
        logger.info(f"[INFO] Input directory: {data_dir}")
        logger.info(f"[INFO] Output directory: {output_path}")
        if not data_dir.exists():
            logger.error(f"Input directory does not exist: {data_dir}")
            return
        processed_count = 0
        skipped_count = 0
        error_count = 0
        for file_path in data_dir.rglob("*"):
            if not file_path.is_file() or file_path.suffix.lower() not in self.supported_extensions:
                skipped_count += 1
                continue
            result = self.process_file(file_path, job_target=job_target)
            if result:
                file_id = self.generate_file_id(file_path)
                self.processed_files[file_id] = result
                out_file = output_path / (file_path.stem + ".json")
                try:
                    with open(out_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to save output for {file_path}: {e}")
                    error_count += 1
            else:
                error_count += 1
        summary = {
            'run_id': str(uuid.uuid4()),
            'completed_at': datetime.now().isoformat(),
            'input_directory': str(data_dir),
            'output_directory': str(output_path),
            'files_processed': processed_count,
            'files_skipped': skipped_count,
            'files_error': error_count,
            'stats': self.stats,
            'processed_files': list(self.processed_files.keys())
        }
        summary_file = output_path / "processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"[SUCCESS] Universal parser completed!")
        logger.info(f"[STATS] Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")
        logger.info(f"[OUTPUT] Summary: {summary_file}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="IntelliCV Universal Document Parser")
    parser.add_argument("--in", dest="input_dir", help="Input directory path")
    parser.add_argument("--out", dest="output_dir", help="Output directory path")
    parser.add_argument("--job", dest="job_target", help="Target job description for enrichment (optional)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    resume_parser = ResumeParser()
    resume_parser.run(args.input_dir, args.output_dir, job_target=args.job_target)

if __name__ == "__main__":
    main()