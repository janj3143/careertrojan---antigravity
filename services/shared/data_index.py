"""
CareerTrojan — Unified Data Index System
==========================================
Scans automated_parser/ and ai_data_final/ directories, classifies every file,
and writes structured JSON indexes that the rest of the platform can query.

Usage:
    from services.shared.data_index import index_registry

    # Rebuild indexes (typically from admin endpoint or startup)
    index_registry.rebuild_all()

    # Query
    stats = index_registry.get_summary()
    unparsed = index_registry.parser_index.get_unparsed_files()
    stale = index_registry.ai_index.get_stale_sources(hours=48)

Author: CaReerTroJan System
Date: February 26, 2026
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("careertrojan.data_index")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FileEntry:
    """Single file record in an index."""
    rel_path: str                   # relative to the index root
    name: str
    extension: str
    size_bytes: int
    modified_iso: str               # ISO-8601
    category: str = "unknown"       # semantic category (cv, jd, profile, etc.)
    subcategory: str = ""           # e.g. client folder name, data type
    record_count: Optional[int] = None   # for JSON arrays
    md5_prefix: Optional[str] = None     # first 8 chars of MD5 for integrity
    parse_status: str = ""          # parsed | unparsed | failed | n/a


@dataclass
class IndexMeta:
    """Top-level metadata for an index."""
    index_type: str                 # "parser_source" | "ai_data"
    base_path: str
    generated_at: str
    generation_seconds: float
    total_files: int
    total_size_bytes: int
    categories: Dict[str, int] = field(default_factory=dict)
    extensions: Dict[str, int] = field(default_factory=dict)


@dataclass
class DataIndex:
    """A complete index: metadata + file entries."""
    meta: IndexMeta
    entries: List[FileEntry] = field(default_factory=list)

    # ── Query helpers ────────────────────────────────────────

    def by_category(self, cat: str) -> List[FileEntry]:
        return [e for e in self.entries if e.category == cat]

    def by_extension(self, ext: str) -> List[FileEntry]:
        ext = ext if ext.startswith(".") else f".{ext}"
        return [e for e in self.entries if e.extension == ext]

    def get_unparsed_files(self) -> List[FileEntry]:
        return [e for e in self.entries if e.parse_status == "unparsed"]

    def get_failed_files(self) -> List[FileEntry]:
        return [e for e in self.entries if e.parse_status == "failed"]

    def get_stale_sources(self, hours: int = 48) -> List[FileEntry]:
        """Files not modified in the last N hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        stale = []
        for e in self.entries:
            try:
                ts = datetime.fromisoformat(e.modified_iso).timestamp()
                if ts < cutoff:
                    stale.append(e)
            except (ValueError, TypeError):
                stale.append(e)
        return stale

    def summary_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self.meta),
            "sample_entries": [asdict(e) for e in self.entries[:10]],
        }


# ============================================================================
# FILE CLASSIFIERS
# ============================================================================

# Extensions commonly associated with CVs / resumes
_CV_EXTENSIONS = {".pdf", ".doc", ".docx", ".rtf", ".odt", ".txt"}
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".bmp"}
_SPREADSHEET_EXTENSIONS = {".xlsx", ".xls", ".csv"}
_EMAIL_EXTENSIONS = {".msg", ".eml"}
_ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".gz", ".tar"}

# Known ai_data_final subdirectory → category mapping
_AI_DIR_CATEGORIES = {
    "contacts": "contacts",
    "core_databases": "core_database",
    "cv_files": "cv_raw",
    "data_cloud_solutions": "cloud_data",
    "email_extracted": "email",
    "emails": "email",
    "enrichment_results": "enrichment",
    "exported_cvs": "cv_export",
    "exports": "export",
    "gazetteers": "gazetteer",
    "heatmaps": "visualization",
    "industries": "taxonomy",
    "job descriptions": "job_description",
    "job_descriptions": "job_description",
    "job_matches": "match_result",
    "job_matching": "match_result",
    "job_titles": "taxonomy",
    "journal_entries": "journal",
    "learning_library": "learning",
    "locations": "taxonomy",
    "logs": "log",
    "metadata": "metadata",
    "normalized": "normalized",
    "notes": "note",
    "parsed_cv_files": "cv_parsed",
    "parsed_from_automated": "cv_parsed",
    "parsed_job_descriptions": "jd_parsed",
    "parsed_resumes": "cv_parsed",
    "processed_cvs": "cv_processed",
    "profiles": "profile",
    "duplicates": "duplicate",
}


def _classify_parser_file(rel_path: str, ext: str) -> tuple[str, str]:
    """Return (category, subcategory) for a file in automated_parser/."""
    parts = Path(rel_path).parts
    subcategory = parts[0] if parts else ""

    ext_lower = ext.lower()
    if ext_lower in _CV_EXTENSIONS:
        category = "cv_document"
    elif ext_lower in _IMAGE_EXTENSIONS:
        category = "image"
    elif ext_lower == ".json":
        category = "json_data"
    elif ext_lower in _SPREADSHEET_EXTENSIONS:
        category = "spreadsheet"
    elif ext_lower in _EMAIL_EXTENSIONS:
        category = "email"
    elif ext_lower in _ARCHIVE_EXTENSIONS:
        category = "archive"
    elif ext_lower == ".dat":
        category = "thumbs_cache"
    elif ext_lower == ".db":
        category = "thumbs_cache"
    else:
        category = "other"

    return category, subcategory


def _classify_ai_file(rel_path: str, ext: str) -> tuple[str, str]:
    """Return (category, subcategory) for a file in ai_data_final/."""
    parts = Path(rel_path).parts
    top_dir = parts[0].lower() if parts and len(parts) > 1 else ""

    # Match against known directory categories
    category = _AI_DIR_CATEGORIES.get(top_dir, "")
    if not category:
        # Top-level files
        if ext.lower() == ".json":
            category = "root_json"
        elif ext.lower() in _CV_EXTENSIONS:
            category = "cv_raw"
        else:
            category = "other"

    subcategory = top_dir or "(root)"
    return category, subcategory


def _quick_md5(filepath: Path, chunk_size: int = 8192) -> str:
    """Read first 8KB and return first 8 hex chars of MD5 — fast integrity check."""
    h = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            h.update(f.read(chunk_size))
    except (OSError, PermissionError):
        return "????????"
    return h.hexdigest()[:8]


def _count_json_records(filepath: Path) -> Optional[int]:
    """If file is a JSON array, return len. For objects return 1. Otherwise None."""
    if filepath.suffix.lower() != ".json":
        return None
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            first_char = f.read(1).strip()
            if not first_char:
                return 0
            f.seek(0)
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                return 1
    except (json.JSONDecodeError, OSError, PermissionError, MemoryError):
        pass
    return None


# ============================================================================
# INDEX BUILDER
# ============================================================================

class IndexBuilder:
    """Scans a directory tree and produces a DataIndex."""

    def __init__(
        self,
        root: Path,
        index_type: str,
        classifier=None,
        compute_hashes: bool = False,
        count_records: bool = False,
        parsed_set: Optional[Set[str]] = None,
        failed_set: Optional[Set[str]] = None,
        progress_cb=None,
    ):
        self.root = root
        self.index_type = index_type
        self.classifier = classifier or (lambda rp, ext: ("unknown", ""))
        self.compute_hashes = compute_hashes
        self.count_records = count_records
        self.parsed_set = parsed_set or set()
        self.failed_set = failed_set or set()
        self.progress_cb = progress_cb

    def build(self) -> DataIndex:
        if not self.root.exists():
            logger.warning("Index root does not exist: %s", self.root)
            return DataIndex(
                meta=IndexMeta(
                    index_type=self.index_type,
                    base_path=str(self.root),
                    generated_at=datetime.now(timezone.utc).isoformat(),
                    generation_seconds=0,
                    total_files=0,
                    total_size_bytes=0,
                ),
            )

        start = time.monotonic()
        entries: List[FileEntry] = []
        cat_counts: Dict[str, int] = defaultdict(int)
        ext_counts: Dict[str, int] = defaultdict(int)
        total_size = 0
        scanned = 0

        for dirpath, _dirnames, filenames in os.walk(self.root):
            for fname in filenames:
                full = Path(dirpath) / fname
                try:
                    stat = full.stat()
                except (OSError, PermissionError):
                    continue

                rel = str(full.relative_to(self.root))
                ext = full.suffix.lower()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

                category, subcategory = self.classifier(rel, ext)

                # Parse status (for parser index)
                stem_lower = full.stem.lower()
                if self.parsed_set and stem_lower in self.parsed_set:
                    parse_status = "parsed"
                elif self.failed_set and stem_lower in self.failed_set:
                    parse_status = "failed"
                elif self.parsed_set:
                    parse_status = "unparsed"
                else:
                    parse_status = "n/a"

                # Optional: hash
                md5_prefix = _quick_md5(full) if self.compute_hashes else None

                # Optional: record count for JSON
                rec_count = None
                if self.count_records and ext == ".json" and size < 50_000_000:
                    rec_count = _count_json_records(full)

                entry = FileEntry(
                    rel_path=rel,
                    name=fname,
                    extension=ext,
                    size_bytes=size,
                    modified_iso=mtime,
                    category=category,
                    subcategory=subcategory,
                    record_count=rec_count,
                    md5_prefix=md5_prefix,
                    parse_status=parse_status,
                )
                entries.append(entry)
                cat_counts[category] += 1
                ext_counts[ext] += 1
                total_size += size
                scanned += 1

                if self.progress_cb and scanned % 10000 == 0:
                    self.progress_cb(scanned)

        elapsed = time.monotonic() - start

        meta = IndexMeta(
            index_type=self.index_type,
            base_path=str(self.root),
            generated_at=datetime.now(timezone.utc).isoformat(),
            generation_seconds=round(elapsed, 2),
            total_files=len(entries),
            total_size_bytes=total_size,
            categories=dict(cat_counts),
            extensions=dict(ext_counts),
        )

        logger.info(
            "Built %s index: %d files, %.1f MB in %.1fs",
            self.index_type, len(entries),
            total_size / (1024 * 1024), elapsed,
        )

        return DataIndex(meta=meta, entries=entries)


# ============================================================================
# INDEX PERSISTENCE — write/read JSON
# ============================================================================

_INDEX_DIR_NAME = "metadata"


def _index_path(base: Path, index_type: str) -> Path:
    """Where to write the index JSON file."""
    return base / _INDEX_DIR_NAME / f"{index_type}_index.json"


def save_index(index: DataIndex, base_path: Path) -> Path:
    """Serialize a DataIndex to JSON on disk."""
    out = _index_path(base_path, index.meta.index_type)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "meta": asdict(index.meta),
        "entries": [asdict(e) for e in index.entries],
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)

    logger.info("Saved %s index → %s (%.1f MB)", index.meta.index_type, out,
                out.stat().st_size / (1024 * 1024))
    return out


def load_index(base_path: Path, index_type: str) -> Optional[DataIndex]:
    """Load a previously-saved index from disk."""
    path = _index_path(base_path, index_type)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = IndexMeta(**data["meta"])
        entries = [FileEntry(**e) for e in data["entries"]]
        return DataIndex(meta=meta, entries=entries)
    except Exception as exc:
        logger.error("Failed to load index %s: %s", path, exc)
        return None


# ============================================================================
# CROSS-REFERENCE: discover what's been parsed
# ============================================================================

def _build_parsed_set(ai_data_root: Path) -> Set[str]:
    """Collect stems of all parsed outputs so we can mark parser source files."""
    parsed = set()
    for subdir in ("parsed_cv_files", "parsed_from_automated", "parsed_resumes", "parsed_job_descriptions"):
        d = ai_data_root / subdir
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    parsed.add(f.stem.lower())
    return parsed


# ============================================================================
# INDEX REGISTRY — singleton that holds both indexes
# ============================================================================

class IndexRegistry:
    """
    Central access point for all data indexes.

    Lazily loads from disk; provides rebuild / query APIs.
    """

    def __init__(self):
        self._parser_index: Optional[DataIndex] = None
        self._ai_index: Optional[DataIndex] = None
        self._resolve_paths()

    def _resolve_paths(self):
        from services.shared.paths import paths
        self.data_root: Path = paths.data_root
        self.ai_data_root: Path = paths.ai_data_final
        self.parser_root: Path = paths.parser_root

    # ── Lazy accessors ───────────────────────────────────────

    @property
    def parser_index(self) -> Optional[DataIndex]:
        if self._parser_index is None:
            self._parser_index = load_index(self.data_root, "parser_source")
        return self._parser_index

    @property
    def ai_index(self) -> Optional[DataIndex]:
        if self._ai_index is None:
            self._ai_index = load_index(self.data_root, "ai_data")
        return self._ai_index

    # ── Rebuild ──────────────────────────────────────────────

    def rebuild_parser_index(self, compute_hashes: bool = False, progress_cb=None) -> DataIndex:
        """Full scan of automated_parser/."""
        parsed_set = _build_parsed_set(self.ai_data_root)

        builder = IndexBuilder(
            root=self.parser_root,
            index_type="parser_source",
            classifier=_classify_parser_file,
            compute_hashes=compute_hashes,
            parsed_set=parsed_set,
            progress_cb=progress_cb,
        )
        self._parser_index = builder.build()
        save_index(self._parser_index, self.data_root)
        return self._parser_index

    def rebuild_ai_index(self, compute_hashes: bool = False,
                         count_records: bool = True, progress_cb=None) -> DataIndex:
        """Full scan of ai_data_final/."""
        builder = IndexBuilder(
            root=self.ai_data_root,
            index_type="ai_data",
            classifier=_classify_ai_file,
            compute_hashes=compute_hashes,
            count_records=count_records,
            progress_cb=progress_cb,
        )
        self._ai_index = builder.build()
        save_index(self._ai_index, self.data_root)
        return self._ai_index

    def rebuild_all(self, compute_hashes: bool = False, progress_cb=None) -> Dict[str, DataIndex]:
        """Rebuild both indexes. Returns {type: index}."""
        logger.info("Rebuilding all data indexes...")
        return {
            "parser_source": self.rebuild_parser_index(compute_hashes, progress_cb),
            "ai_data": self.rebuild_ai_index(compute_hashes, progress_cb=progress_cb),
        }

    # ── Query helpers ────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Dashboard-ready summary of both indexes."""
        result: Dict[str, Any] = {"indexes": {}}

        for label, idx in [("parser_source", self.parser_index), ("ai_data", self.ai_index)]:
            if idx is None:
                result["indexes"][label] = {
                    "status": "not_built",
                    "message": "Run rebuild to generate index",
                }
            else:
                result["indexes"][label] = {
                    "status": "ok",
                    "generated_at": idx.meta.generated_at,
                    "generation_seconds": idx.meta.generation_seconds,
                    "total_files": idx.meta.total_files,
                    "total_size_mb": round(idx.meta.total_size_bytes / (1024 * 1024), 1),
                    "categories": idx.meta.categories,
                    "extensions_top10": dict(
                        sorted(idx.meta.extensions.items(), key=lambda x: -x[1])[:10]
                    ),
                }

        # Cross-ref: unparsed count
        if self.parser_index:
            unparsed = self.parser_index.get_unparsed_files()
            cv_unparsed = [f for f in unparsed if f.category == "cv_document"]
            result["parser_coverage"] = {
                "total_cv_documents": sum(
                    1 for e in self.parser_index.entries if e.category == "cv_document"
                ),
                "parsed": sum(
                    1 for e in self.parser_index.entries
                    if e.category == "cv_document" and e.parse_status == "parsed"
                ),
                "unparsed": len(cv_unparsed),
                "failed": sum(
                    1 for e in self.parser_index.entries
                    if e.category == "cv_document" and e.parse_status == "failed"
                ),
            }

        return result

    def is_fresh(self, max_age_hours: int = 24) -> Dict[str, bool]:
        """Check if indexes are fresh enough."""
        cutoff = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        result = {}
        for label, idx in [("parser_source", self.parser_index), ("ai_data", self.ai_index)]:
            if idx is None:
                result[label] = False
            else:
                try:
                    gen_ts = datetime.fromisoformat(idx.meta.generated_at).timestamp()
                    result[label] = gen_ts > cutoff
                except (ValueError, TypeError):
                    result[label] = False
        return result

    def search(self, query: str, index_type: str = "both", limit: int = 50) -> List[Dict[str, Any]]:
        """Simple filename/path search across indexes."""
        query_lower = query.lower()
        results = []

        indexes_to_search = []
        if index_type in ("both", "parser_source") and self.parser_index:
            indexes_to_search.append(("parser_source", self.parser_index))
        if index_type in ("both", "ai_data") and self.ai_index:
            indexes_to_search.append(("ai_data", self.ai_index))

        for idx_type, idx in indexes_to_search:
            for entry in idx.entries:
                if query_lower in entry.name.lower() or query_lower in entry.rel_path.lower():
                    results.append({
                        "index": idx_type,
                        **asdict(entry),
                    })
                    if len(results) >= limit:
                        return results

        return results


# ── Singleton ────────────────────────────────────────────────

_registry: Optional[IndexRegistry] = None


def get_index_registry() -> IndexRegistry:
    """Get the singleton IndexRegistry."""
    global _registry
    if _registry is None:
        _registry = IndexRegistry()
    return _registry
