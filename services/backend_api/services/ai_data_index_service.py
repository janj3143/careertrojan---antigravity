"""
AI Data Index Service
======================

Provides full indexing capabilities for ai_data_final and automated_parser directories.
Tracks content distribution, parsing status, skills/industries aggregation, and run history.
"""

from __future__ import annotations

import json
import hashlib
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from services.shared.paths import CareerTrojanPaths

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Field extraction utilities
# ---------------------------------------------------------------------------

SKILL_FIELDS = [
    "skills",
    "technical_skills",
    "soft_skills",
    "competencies",
    "technologies",
    "tools",
    "programming_languages",
    "certifications",
]

INDUSTRY_FIELDS = ["industry", "industries", "sector", "domain", "field", "vertical"]
LOCATION_FIELDS = ["location", "locations", "city", "state", "country", "region", "address"]


def _as_list(v: Any) -> List[str]:
    """Normalize any value to a list of strings."""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        parts = [p.strip() for p in v.replace("|", ",").replace(";", ",").split(",")]
        return [p for p in parts if p]
    return []


def _extract_by_fields(obj: Dict[str, Any], fields: List[str], min_len: int = 2) -> List[str]:
    """Extract values from a dict by field names."""
    out: List[str] = []
    for f in fields:
        if f in obj:
            out.extend(_as_list(obj.get(f)))
    return [x for x in out if len(x) >= min_len]


def _extract_skills(obj: Dict[str, Any]) -> List[str]:
    skills: List[str] = []
    for f in SKILL_FIELDS:
        if f in obj:
            skills.extend(_as_list(obj.get(f)))
    # nested experience blocks
    exp = obj.get("experience") or obj.get("work_experience") or obj.get("roles")
    if isinstance(exp, list):
        for e in exp:
            if isinstance(e, dict):
                for k, v in e.items():
                    if "skill" in str(k).lower():
                        skills.extend(_as_list(v))
    return [s.strip() for s in skills if len(s.strip()) > 1]


def _extract_industries(obj: Dict[str, Any]) -> List[str]:
    return _extract_by_fields(obj, INDUSTRY_FIELDS, min_len=3)


def _extract_locations(obj: Dict[str, Any]) -> List[str]:
    return _extract_by_fields(obj, LOCATION_FIELDS, min_len=2)


def _safe_read_json(path: Path) -> Any:
    """Read JSON file safely, returning empty dict on error."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {}


def _file_hash(path: Path) -> str:
    """Compute MD5 hash of a file for change detection."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Data classes for index results
# ---------------------------------------------------------------------------

@dataclass
class FileIngestionRecord:
    """Individual file ingestion tracking with timestamp."""
    file_path: str
    file_name: str
    category: str
    size_bytes: int
    file_hash: str
    ingested_at: str
    modified_at: str
    source_type: str  # ai_data_final | automated_parser


@dataclass
class CategoryStats:
    """Stats for a single content category."""
    category: str
    folder: str
    file_count: int
    total_size_bytes: int
    oldest_file: Optional[str] = None
    newest_file: Optional[str] = None
    new_since_last_index: int = 0


@dataclass
class AIDataIndexSummary:
    """Summary of indexed ai_data_final content."""
    indexed_at: str
    data_root: str
    total_files: int
    total_size_bytes: int
    categories: List[CategoryStats]
    unique_skills: int
    unique_industries: int
    unique_locations: int
    top_skills: Dict[str, int]
    top_industries: Dict[str, int]
    top_locations: Dict[str, int]


@dataclass
class ParserIndexEntry:
    """Single entry in the parser source index."""
    source_path: str
    file_name: str
    file_type: str
    size_bytes: int
    status: str  # ingested | pending_not_attempted | pending_parse_error | blocked_missing_dependency
    indexed: bool
    failure_reason: str = ""
    last_attempt: str = ""
    file_hash: str = ""


@dataclass
class ParserIndexSummary:
    """Summary of automated parser state."""
    indexed_at: str
    parser_root: str
    output_root: str
    processed_count: int
    pending_count: int
    error_count: int
    blocked_count: int
    total_sources: int
    status_counts: Dict[str, int]
    file_type_distribution: Dict[str, int]
    trap_flags: List[str]


@dataclass
class ParserRunRecord:
    """Record of a parser execution run."""
    run_id: str
    started_at: str
    completed_at: Optional[str]
    total_files: int
    processed: int
    skipped: int
    errors: int
    duration_seconds: Optional[float]
    file_types: Dict[str, int]


@dataclass
class DataIndexState:
    """Combined state of all indexes."""
    ai_data_summary: Optional[AIDataIndexSummary] = None
    parser_summary: Optional[ParserIndexSummary] = None
    parser_run_history: List[ParserRunRecord] = field(default_factory=list)
    last_full_index: Optional[str] = None
    file_manifest: Dict[str, FileIngestionRecord] = field(default_factory=dict)  # path -> record


# ---------------------------------------------------------------------------
# Main Index Service
# ---------------------------------------------------------------------------

class AIDataIndexService:
    """
    Full indexing service for ai_data_final and automated_parser.

    Features:
    - Index all content categories in ai_data_final
    - Aggregate skills, industries, locations across profiles
    - Track parser source file status
    - Record parser run history
    - Persist index state for fast reload
    """

    # Mapping of logical category names to folder names
    CATEGORY_MAP = {
        "parsed_resumes": "parsed_resumes",
        "normalized_profiles": "normalized",
        "profiles": "profiles",
        "companies": "companies",
        "job_titles": "job_titles",
        "locations": "locations",
        "email_extractions": "email_extracted",
        "metadata": "metadata",
        "training": "training",
        "models": "models",
        # Alternate names in older corpus structures
        "normalized": "normalized",
        "email_extracted": "email_extracted",
    }

    def __init__(self, paths: Optional[CareerTrojanPaths] = None):
        self.paths = paths or CareerTrojanPaths()
        self.ai_data_final = self.paths.ai_data_final
        self.parser_root = self.paths.parser_root
        self._index_file = self.ai_data_final / "_data_index_state.json"
        self._parser_runs_file = self.ai_data_final / "_parser_run_history.jsonl"
        self._file_manifest_file = self.ai_data_final / "_file_manifest.json"

        # In-memory counters
        self._skills = Counter()
        self._industries = Counter()
        self._locations = Counter()
        self._state: DataIndexState = DataIndexState()

        # Try to load persisted state
        self._load_persisted_state()
        self._load_file_manifest()

    def _load_persisted_state(self) -> None:
        """Load index state from disk if available."""
        if self._index_file.exists():
            try:
                raw = json.loads(self._index_file.read_text(encoding="utf-8"))
                if raw.get("ai_data_summary"):
                    cats = [CategoryStats(**c) for c in raw["ai_data_summary"].get("categories", [])]
                    raw["ai_data_summary"]["categories"] = cats
                    self._state.ai_data_summary = AIDataIndexSummary(**raw["ai_data_summary"])
                if raw.get("parser_summary"):
                    self._state.parser_summary = ParserIndexSummary(**raw["parser_summary"])
                self._state.last_full_index = raw.get("last_full_index")
            except Exception as e:
                logger.warning(f"Could not load persisted index state: {e}")

        # Load run history
        if self._parser_runs_file.exists():
            try:
                for line in self._parser_runs_file.read_text(encoding="utf-8").strip().split("\n"):
                    if line.strip():
                        rec = json.loads(line)
                        self._state.parser_run_history.append(ParserRunRecord(**rec))
            except Exception as e:
                logger.warning(f"Could not load parser run history: {e}")

    def _persist_state(self) -> None:
        """Save current index state to disk."""
        try:
            self.ai_data_final.mkdir(parents=True, exist_ok=True)
            payload = {
                "last_full_index": self._state.last_full_index,
            }
            if self._state.ai_data_summary:
                summary = asdict(self._state.ai_data_summary)
                payload["ai_data_summary"] = summary
            if self._state.parser_summary:
                payload["parser_summary"] = asdict(self._state.parser_summary)

            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not persist index state: {e}")

    def _load_file_manifest(self) -> None:
        """Load the file ingestion manifest for incremental tracking."""
        if self._file_manifest_file.exists():
            try:
                raw = json.loads(self._file_manifest_file.read_text(encoding="utf-8"))
                for path, rec in raw.items():
                    self._state.file_manifest[path] = FileIngestionRecord(**rec)
            except Exception as e:
                logger.warning(f"Could not load file manifest: {e}")

    def _persist_file_manifest(self) -> None:
        """Save the file ingestion manifest."""
        try:
            self.ai_data_final.mkdir(parents=True, exist_ok=True)
            payload = {path: asdict(rec) for path, rec in self._state.file_manifest.items()}
            with open(self._file_manifest_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not persist file manifest: {e}")

    def _append_run_record(self, record: ParserRunRecord) -> None:
        """Append a parser run record to history."""
        try:
            self.ai_data_final.mkdir(parents=True, exist_ok=True)
            with open(self._parser_runs_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
            self._state.parser_run_history.append(record)
        except Exception as e:
            logger.warning(f"Could not append run record: {e}")

    # -----------------------------------------------------------------------
    # ai_data_final indexing
    # -----------------------------------------------------------------------

    def index_ai_data(self, max_files_per_category: Optional[int] = None) -> AIDataIndexSummary:
        """
        Index all content in ai_data_final.

        Args:
            max_files_per_category: Optional limit per category for faster indexing
        """
        self._skills.clear()
        self._industries.clear()
        self._locations.clear()

        categories: List[CategoryStats] = []
        total_files = 0
        total_size = 0
        now_iso = datetime.utcnow().isoformat() + "Z"

        for logical_cat, folder in self.CATEGORY_MAP.items():
            cat_path = self.ai_data_final / folder
            if not cat_path.exists():
                continue

            # Skip duplicate logical names mapping to same folder
            if any(c.folder == folder for c in categories):
                continue

            files = list(cat_path.rglob("*.json"))
            if max_files_per_category:
                files = files[:max_files_per_category]

            cat_size = 0
            oldest_mtime = None
            newest_mtime = None
            new_since_last = 0

            for fp in files:
                try:
                    stat = fp.stat()
                    cat_size += stat.st_size
                    mtime = stat.st_mtime
                    rel_path = str(fp.relative_to(self.ai_data_final))
                    file_hash = _file_hash(fp) if stat.st_size < 10_000_000 else ""

                    # Track in manifest with timestamp
                    is_new = rel_path not in self._state.file_manifest
                    is_changed = (
                        not is_new
                        and file_hash
                        and self._state.file_manifest[rel_path].file_hash != file_hash
                    )

                    if is_new or is_changed:
                        new_since_last += 1
                        self._state.file_manifest[rel_path] = FileIngestionRecord(
                            file_path=rel_path,
                            file_name=fp.name,
                            category=logical_cat,
                            size_bytes=stat.st_size,
                            file_hash=file_hash,
                            ingested_at=now_iso,
                            modified_at=datetime.fromtimestamp(mtime).isoformat() + "Z",
                            source_type="ai_data_final",
                        )

                    if oldest_mtime is None or mtime < oldest_mtime:
                        oldest_mtime = mtime
                    if newest_mtime is None or mtime > newest_mtime:
                        newest_mtime = mtime

                    data = _safe_read_json(fp)
                    if isinstance(data, dict):
                        self._skills.update(_extract_skills(data))
                        self._industries.update(_extract_industries(data))
                        self._locations.update(_extract_locations(data))
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                self._skills.update(_extract_skills(item))
                                self._industries.update(_extract_industries(item))
                                self._locations.update(_extract_locations(item))
                except Exception:
                    continue

            categories.append(
                CategoryStats(
                    category=logical_cat,
                    folder=folder,
                    file_count=len(files),
                    total_size_bytes=cat_size,
                    oldest_file=datetime.fromtimestamp(oldest_mtime).isoformat() if oldest_mtime else None,
                    newest_file=datetime.fromtimestamp(newest_mtime).isoformat() if newest_mtime else None,
                    new_since_last_index=new_since_last,
                )
            )
            total_files += len(files)
            total_size += cat_size

        summary = AIDataIndexSummary(
            indexed_at=datetime.utcnow().isoformat() + "Z",
            data_root=str(self.ai_data_final),
            total_files=total_files,
            total_size_bytes=total_size,
            categories=categories,
            unique_skills=len(self._skills),
            unique_industries=len(self._industries),
            unique_locations=len(self._locations),
            top_skills=dict(self._skills.most_common(100)),
            top_industries=dict(self._industries.most_common(50)),
            top_locations=dict(self._locations.most_common(50)),
        )

        self._state.ai_data_summary = summary
        self._state.last_full_index = summary.indexed_at
        self._persist_state()
        self._persist_file_manifest()

        return summary

    # -----------------------------------------------------------------------
    # Parser source indexing
    # -----------------------------------------------------------------------

    def index_parser_sources(self) -> ParserIndexSummary:
        """
        Index all parseable source files in the parser root directory.
        Returns summary of pending, processed, errored files.
        """
        extensions = {
            ".pdf", ".docx", ".doc", ".csv", ".xlsx", ".xls", ".zip",
            ".msg", ".eml", ".mbox", ".txt", ".json", ".rtf", ".odt",
            ".ods", ".xml", ".yaml", ".yml", ".html", ".htm", ".md"
        }
        ignored_folders = {
            "incoming", "completed", "__pycache__", ".git", ".venv", "node_modules"
        }
        skip_files = {
            "data_ingestion_tracker.py", "README.md", ".gitignore",
            "desktop.ini", "Thumbs.db"
        }

        # Load processed/failed indexes from parser output
        processed_index_file = self.ai_data_final / "_processed_sources.txt"
        failed_index_file = self.ai_data_final / "_failed_sources.json"

        processed_sources: set = set()
        failed_sources: Dict[str, Dict[str, Any]] = {}

        if processed_index_file.exists():
            try:
                for line in processed_index_file.read_text(encoding="utf-8").strip().split("\n"):
                    if line.strip():
                        processed_sources.add(line.strip())
            except Exception:
                pass

        if failed_index_file.exists():
            try:
                failed_sources = json.loads(failed_index_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Detect optional dependencies
        optional_deps = self._detect_optional_dependencies()

        # Scan parser root
        entries: List[ParserIndexEntry] = []
        status_counts = {
            "ingested": 0,
            "pending_not_attempted": 0,
            "pending_parse_error": 0,
            "blocked_missing_dependency": 0,
        }
        file_types: Dict[str, int] = {}

        if self.parser_root.exists():
            for file_path in self.parser_root.rglob("*"):
                if not file_path.is_file():
                    continue
                if any(ignored in file_path.parts for ignored in ignored_folders):
                    continue
                if file_path.name in skip_files:
                    continue
                if file_path.name.startswith("~$") or file_path.name.startswith(".~lock."):
                    continue
                if "~$" in file_path.name:
                    continue

                ext = file_path.suffix.lower()
                if ext not in extensions:
                    continue

                rel = str(file_path.relative_to(self.parser_root))
                file_types[ext] = file_types.get(ext, 0) + 1

                # Determine status
                if rel in processed_sources:
                    status = "ingested"
                elif rel in failed_sources:
                    status = "pending_parse_error"
                elif ext == ".xls" and not optional_deps.get("xlrd"):
                    status = "blocked_missing_dependency"
                elif ext == ".msg" and not optional_deps.get("extract_msg"):
                    status = "blocked_missing_dependency"
                elif ext == ".xlsx" and not optional_deps.get("openpyxl"):
                    status = "blocked_missing_dependency"
                elif ext == ".docx" and not optional_deps.get("python_docx"):
                    status = "blocked_missing_dependency"
                else:
                    status = "pending_not_attempted"

                status_counts[status] = status_counts.get(status, 0) + 1

                try:
                    stat = file_path.stat()
                    size = stat.st_size
                except Exception:
                    size = 0

                failure_info = failed_sources.get(rel, {})
                entries.append(
                    ParserIndexEntry(
                        source_path=rel,
                        file_name=file_path.name,
                        file_type=ext,
                        size_bytes=size,
                        status=status,
                        indexed=rel in processed_sources,
                        failure_reason=failure_info.get("reason", ""),
                        last_attempt=failure_info.get("last_attempt", ""),
                        file_hash=_file_hash(file_path) if size < 10_000_000 else "",
                    )
                )

        # Trap flags
        trap_flags = []
        if status_counts.get("pending_not_attempted", 0) > 0:
            trap_flags.append("pending_parser_data_detected")
        if status_counts.get("pending_parse_error", 0) > 0:
            trap_flags.append("parser_parse_error_backlog_detected")
        if status_counts.get("blocked_missing_dependency", 0) > 0:
            trap_flags.append("parser_blocked_by_missing_dependency")

        summary = ParserIndexSummary(
            indexed_at=datetime.utcnow().isoformat() + "Z",
            parser_root=str(self.parser_root),
            output_root=str(self.ai_data_final),
            processed_count=status_counts.get("ingested", 0),
            pending_count=status_counts.get("pending_not_attempted", 0),
            error_count=status_counts.get("pending_parse_error", 0),
            blocked_count=status_counts.get("blocked_missing_dependency", 0),
            total_sources=len(entries),
            status_counts=status_counts,
            file_type_distribution=file_types,
            trap_flags=trap_flags,
        )

        self._state.parser_summary = summary
        self._persist_state()

        # Also write detailed manifest
        self._write_parser_manifest(entries, summary)

        return summary

    def _detect_optional_dependencies(self) -> Dict[str, bool]:
        """Check which optional parsing libraries are available."""
        status = {
            "xlrd": False,
            "extract_msg": False,
            "openpyxl": False,
            "python_docx": False,
            "pdfplumber": False,
            "pypdf2": False,
        }
        try:
            import xlrd  # type: ignore
            status["xlrd"] = True
        except Exception:
            pass
        try:
            import extract_msg  # type: ignore
            status["extract_msg"] = True
        except Exception:
            pass
        try:
            import openpyxl  # type: ignore
            status["openpyxl"] = True
        except Exception:
            pass
        try:
            import docx  # type: ignore
            status["python_docx"] = True
        except Exception:
            pass
        try:
            import pdfplumber  # type: ignore
            status["pdfplumber"] = True
        except Exception:
            pass
        try:
            from PyPDF2 import PdfReader  # type: ignore
            status["pypdf2"] = True
        except Exception:
            pass
        return status

    def _write_parser_manifest(
        self, entries: List[ParserIndexEntry], summary: ParserIndexSummary
    ) -> None:
        """Write detailed parser manifest files."""
        try:
            self.ai_data_final.mkdir(parents=True, exist_ok=True)

            # Full manifest
            manifest_file = self.ai_data_final / "parser_ingestion_status.json"
            payload = {
                "created_at": summary.indexed_at,
                "parser_root": summary.parser_root,
                "output_root": summary.output_root,
                "status_counts": summary.status_counts,
                "file_type_distribution": summary.file_type_distribution,
                "trap_flags": summary.trap_flags,
                "optional_dependencies": self._detect_optional_dependencies(),
                "records": [asdict(e) for e in entries],
            }
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            # Summary manifest (without records)
            summary_file = self.ai_data_final / "parser_ingestion_status_summary.json"
            summary_payload = {
                "created_at": summary.indexed_at,
                "parser_root": summary.parser_root,
                "output_root": summary.output_root,
                "processed_count": summary.processed_count,
                "pending_count": summary.pending_count,
                "error_count": summary.error_count,
                "blocked_count": summary.blocked_count,
                "total_sources": summary.total_sources,
                "status_counts": summary.status_counts,
                "file_type_distribution": summary.file_type_distribution,
                "trap_flags": summary.trap_flags,
            }
            with open(summary_file, "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"Could not write parser manifest: {e}")

    # -----------------------------------------------------------------------
    # Parser run tracking
    # -----------------------------------------------------------------------

    def record_parser_run(
        self,
        run_id: str,
        started_at: str,
        completed_at: Optional[str],
        total_files: int,
        processed: int,
        skipped: int,
        errors: int,
        duration_seconds: Optional[float],
        file_types: Dict[str, int],
    ) -> ParserRunRecord:
        """Record a parser execution run."""
        record = ParserRunRecord(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            total_files=total_files,
            processed=processed,
            skipped=skipped,
            errors=errors,
            duration_seconds=duration_seconds,
            file_types=file_types,
        )
        self._append_run_record(record)
        return record

    def get_parser_run_history(self, limit: int = 50) -> List[ParserRunRecord]:
        """Get recent parser run history."""
        return self._state.parser_run_history[-limit:]

    # -----------------------------------------------------------------------
    # Combined operations
    # -----------------------------------------------------------------------

    def full_index(self, max_files_per_category: Optional[int] = None) -> DataIndexState:
        """Run full index of all data sources."""
        self.index_ai_data(max_files_per_category=max_files_per_category)
        self.index_parser_sources()
        return self._state

    def get_state(self) -> DataIndexState:
        """Return current index state."""
        return self._state

    def get_ai_data_summary(self) -> Optional[AIDataIndexSummary]:
        """Return cached AI data summary."""
        return self._state.ai_data_summary

    def get_parser_summary(self) -> Optional[ParserIndexSummary]:
        """Return cached parser summary."""
        return self._state.parser_summary

    # -----------------------------------------------------------------------
    # Query helpers
    # -----------------------------------------------------------------------

    def search_skills(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search indexed skills by prefix/substring match."""
        query_lower = query.lower()
        results = []
        for skill, count in self._skills.most_common():
            if query_lower in skill.lower():
                results.append({"skill": skill, "count": count})
                if len(results) >= limit:
                    break
        return results

    def search_industries(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search indexed industries by prefix/substring match."""
        query_lower = query.lower()
        results = []
        for industry, count in self._industries.most_common():
            if query_lower in industry.lower():
                results.append({"industry": industry, "count": count})
                if len(results) >= limit:
                    break
        return results

    def search_locations(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search indexed locations by prefix/substring match."""
        query_lower = query.lower()
        results = []
        for location, count in self._locations.most_common():
            if query_lower in location.lower():
                results.append({"location": location, "count": count})
                if len(results) >= limit:
                    break
        return results

    def get_files_since(
        self,
        since: str,
        source_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get files ingested since a given ISO timestamp.

        Args:
            since: ISO timestamp (e.g., "2026-02-27T00:00:00Z")
            source_type: Filter by "ai_data_final" or "automated_parser"
            category: Filter by category name
            limit: Max results to return
        """
        results = []
        for path, rec in self._state.file_manifest.items():
            if rec.ingested_at >= since:
                if source_type and rec.source_type != source_type:
                    continue
                if category and rec.category != category:
                    continue
                results.append(asdict(rec))
                if len(results) >= limit:
                    break
        # Sort by ingested_at descending (newest first)
        results.sort(key=lambda x: x["ingested_at"], reverse=True)
        return results

    def get_new_data_summary(self) -> Dict[str, Any]:
        """
        Quick summary of new data since last full index.
        Useful for monitoring dashboards and alerts.
        """
        last_index = self._state.last_full_index
        if not last_index:
            return {
                "status": "never_indexed",
                "new_files_count": 0,
                "categories_with_new_data": [],
            }

        new_files = self.get_files_since(last_index, limit=10000)
        categories_with_new = set(f["category"] for f in new_files)

        return {
            "status": "ok",
            "last_full_index": last_index,
            "new_files_count": len(new_files),
            "categories_with_new_data": sorted(list(categories_with_new)),
            "newest_files": new_files[:10],  # Only return top 10 newest
        }

    def get_file_manifest_stats(self) -> Dict[str, Any]:
        """Get statistics about the file manifest."""
        total = len(self._state.file_manifest)
        by_category: Dict[str, int] = {}
        by_source: Dict[str, int] = {}

        for rec in self._state.file_manifest.values():
            by_category[rec.category] = by_category.get(rec.category, 0) + 1
            by_source[rec.source_type] = by_source.get(rec.source_type, 0) + 1

        return {
            "total_tracked_files": total,
            "by_category": by_category,
            "by_source": by_source,
            "manifest_file": str(self._file_manifest_file),
        }

    def incremental_index(self) -> Dict[str, Any]:
        """
        Perform incremental indexing - only process new/changed files.
        Returns summary of what was added.
        """
        now_iso = datetime.utcnow().isoformat() + "Z"
        new_files: List[FileIngestionRecord] = []
        changed_files: List[FileIngestionRecord] = []

        # Scan ai_data_final for new/changed files
        for logical_cat, folder in self.CATEGORY_MAP.items():
            cat_path = self.ai_data_final / folder
            if not cat_path.exists():
                continue

            for fp in cat_path.rglob("*.json"):
                try:
                    stat = fp.stat()
                    rel_path = str(fp.relative_to(self.ai_data_final))
                    file_hash = _file_hash(fp) if stat.st_size < 10_000_000 else ""

                    existing = self._state.file_manifest.get(rel_path)
                    if existing is None:
                        # New file
                        rec = FileIngestionRecord(
                            file_path=rel_path,
                            file_name=fp.name,
                            category=logical_cat,
                            size_bytes=stat.st_size,
                            file_hash=file_hash,
                            ingested_at=now_iso,
                            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z",
                            source_type="ai_data_final",
                        )
                        self._state.file_manifest[rel_path] = rec
                        new_files.append(rec)
                    elif file_hash and existing.file_hash != file_hash:
                        # Changed file
                        rec = FileIngestionRecord(
                            file_path=rel_path,
                            file_name=fp.name,
                            category=logical_cat,
                            size_bytes=stat.st_size,
                            file_hash=file_hash,
                            ingested_at=now_iso,
                            modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z",
                            source_type="ai_data_final",
                        )
                        self._state.file_manifest[rel_path] = rec
                        changed_files.append(rec)
                except Exception:
                    continue

        # Persist manifest if anything changed
        if new_files or changed_files:
            self._persist_file_manifest()

        return {
            "indexed_at": now_iso,
            "new_files_count": len(new_files),
            "changed_files_count": len(changed_files),
            "new_files": [asdict(r) for r in new_files[:50]],
            "changed_files": [asdict(r) for r in changed_files[:50]],
        }


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------

_service_instance: Optional[AIDataIndexService] = None


def get_ai_data_index_service() -> AIDataIndexService:
    """Get or create the AI data index service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AIDataIndexService()
    return _service_instance
