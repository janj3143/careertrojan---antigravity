#!/usr/bin/env python3
"""Unified automated_parser ingestion runner.

This script performs three orchestrated steps:

1. Consolidate all ai_data_final directories into a single canonical root.
2. Execute the admin_portal Complete Data Parser against automated_parser assets.
3. Bulk-ingest the parser outputs into ai_data_final using the automatic ingestion service.

Usage examples:

    python automated_parser/run_full_ingest.py --include-historical
    python automated_parser/run_full_ingest.py --skip-parse --limit 50
"""
from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADMIN_PORTAL_ROOT = PROJECT_ROOT / "admin_portal"
SHARED_BACKEND_ROOT = PROJECT_ROOT / "shared_backend"
SHARED_ROOT = PROJECT_ROOT / "shared"

# Keep admin_portal (and repo root) ahead of shared paths to avoid namespace collisions
sys.path[:0] = [
    str(ADMIN_PORTAL_ROOT),
    str(PROJECT_ROOT),
]

# Preload admin_portal utils before shared paths register their own package names
importlib.import_module("utils.logging_config")

for supplemental_path in (SHARED_BACKEND_ROOT, SHARED_ROOT):
    supplemental_str = str(supplemental_path)
    if supplemental_str not in sys.path:
        sys.path.append(supplemental_str)

from admin_portal.services.resume_parser import ResumeParser  # type: ignore
from admin_portal.services.automatic_data_ingestion_service import (  # type: ignore
    AutomaticDataIngestionService,
)

from shared_backend.services.data_path_resolver import (  # type: ignore
    get_ai_data_root,
    iter_existing_candidates,
)


class AutomatedParserOrchestrator:
    """Coordinates consolidation, parsing, and ingestion."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ai_root = get_ai_data_root(ensure_exists=False)
        self.legacy_ai_dirs = [
            project_root / "admin_portal" / "ai_data_final",
            project_root / "SANDBOX" / "Full system" / "admin_portal" / "ai_data_final",
        ]

    def consolidate_ai_data(self, clean_legacy: bool = True) -> Dict[str, int]:
        """Merge every discovered ai_data_final folder into the canonical root."""
        target = self.ai_root
        target.mkdir(parents=True, exist_ok=True)
        summary = {"merged_files": 0, "sources": 0}

        candidates = list(iter_existing_candidates())
        candidates.extend([d for d in self.legacy_ai_dirs if d.exists()])

        for source in candidates:
            if source.resolve() == target.resolve():
                continue
            summary["sources"] += 1
            for file_path in source.rglob("*"):
                if file_path.is_file():
                    relative = file_path.relative_to(source)
                    destination = target / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        if destination.exists() and destination.stat().st_mtime >= file_path.stat().st_mtime:
                            continue
                        shutil.copy2(file_path, destination)
                        summary["merged_files"] += 1
                    except Exception as exc:
                        print(f"⚠️ Unable to copy {file_path} → {destination}: {exc}")
        if clean_legacy:
            for legacy in self.legacy_ai_dirs:
                self._flatten_legacy_dir(legacy)
        return summary

    def _flatten_legacy_dir(self, legacy_path: Path) -> None:
        if not legacy_path.exists() or legacy_path.resolve() == self.ai_root.resolve():
            return
        try:
            shutil.rmtree(legacy_path)
        except Exception:
            pass
        legacy_path.mkdir(parents=True, exist_ok=True)
        placeholder = legacy_path / "README.md"
        placeholder.write_text(
            "This directory has been consolidated. Use ai_data_final at the repo root for all data access.\n",
            encoding="utf-8",
        )

    def run_parser(self, include_historical: bool, scan_only: bool = False) -> Dict[str, str]:
        parser = ResumeParser(base_path=self.project_root)
        if scan_only:
            parser.scan_all_data_sources()
            return {"status": "scan-only"}
        results = parser.process_all_data(include_historical=include_historical)
        parser.save_extracted_data()
        return {"status": "processed", "summary_file": results.get("final_summary", {}).get("processing_completion_time", "")}

    def ingest_outputs(self, limit: Optional[int] = None) -> Dict[str, int]:
        ingestion_service = AutomaticDataIngestionService(base_path=str(self.project_root))
        return ingestion_service.ingest_parsed_directory(limit=limit)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automated parser ingestion workflow")
    parser.add_argument("--skip-consolidate", action="store_true", help="Skip ai_data_final consolidation step")
    parser.add_argument("--skip-parse", action="store_true", help="Skip running the complete data parser")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip ingesting parser outputs")
    parser.add_argument("--include-historical", action="store_true", help="Process historical (2011-2020) data")
    parser.add_argument("--scan-only", action="store_true", help="Inventory data sources without parsing")
    parser.add_argument("--keep-legacy", action="store_true", help="Do not delete legacy ai_data_final copies after merge")
    parser.add_argument("--limit", type=int, help="Limit the number of CV records ingested")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    orchestrator = AutomatedParserOrchestrator(PROJECT_ROOT)

    if not args.skip_consolidate:
        summary = orchestrator.consolidate_ai_data(clean_legacy=not args.keep_legacy)
        print(f"✅ Consolidated ai_data_final | Sources: {summary['sources']} | Files merged: {summary['merged_files']}")

    if not args.skip_parse:
        parse_summary = orchestrator.run_parser(include_historical=args.include_historical, scan_only=args.scan_only)
        print(f"🧾 Parser step complete: {parse_summary}")

    if not args.skip_ingest:
        ingest_summary = orchestrator.ingest_outputs(limit=args.limit)
        print(f"📦 Ingestion summary: {ingest_summary}")


if __name__ == "__main__":
    main()
