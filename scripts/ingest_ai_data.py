"""Unified data ingestion runner for IntelliCV."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

from shared.config import AI_DATA_DIR, RAW_DATA_DIR
from phase1_extract_automated_parser import AutomatedParserExtractor
from parse_all_cvs import CVBatchParser


@dataclass
class StepResult:
    name: str
    success: bool
    details: str


def run_phase_one(parser_dir: Path | None, output_dir: Path | None) -> StepResult:
    extractor = AutomatedParserExtractor(parser_dir=parser_dir, output_dir=output_dir)
    success = extractor.run_extraction()
    details = (
        f"msg={extractor.stats['msg_files_processed']} "
        f"csv={extractor.stats['csv_files_processed']} "
        f"candidates={len(extractor.extracted_data['candidates'])}"
    )
    return StepResult("phase1", bool(success), details)


def run_cv_parser(source_dir: Path | None, output_dir: Path | None, force: bool) -> StepResult:
    parser = CVBatchParser(source_dir=source_dir, output_dir=output_dir, skip_existing=not force)
    parsed, failed = parser.parse_all_cvs()
    success = parsed > 0 and failed == 0
    details = f"parsed={parsed} failed={failed} output={parser.output_dir}"
    return StepResult("cv_parser", success, details)


def main() -> int:
    cli = argparse.ArgumentParser(description="Run IntelliCV ingestion pipeline")
    cli.add_argument(
        "--steps",
        default="phase1,cv",
        help="Comma separated steps to run: phase1, cv",
    )
    cli.add_argument(
        "--parser-dir",
        type=Path,
        default=None,
        help=f"Override automated_parser directory (defaults to {RAW_DATA_DIR})",
    )
    cli.add_argument(
        "--phase1-output",
        type=Path,
        default=None,
        help=f"Override phase1 output (defaults to {AI_DATA_DIR / 'parsed_from_automated'})",
    )
    cli.add_argument(
        "--cv-source",
        type=Path,
        default=None,
        help=f"Override CV parser source (defaults to {RAW_DATA_DIR})",
    )
    cli.add_argument(
        "--cv-output",
        type=Path,
        default=None,
        help=f"Override CV parser output (defaults to {AI_DATA_DIR / 'parsed_resumes'})",
    )
    cli.add_argument(
        "--force-cv",
        action="store_true",
        help="Reprocess CV JSON files even if they exist",
    )
    args = cli.parse_args()

    requested_steps: List[str] = [step.strip().lower() for step in args.steps.split(",") if step.strip()]
    results: List[StepResult] = []

    if "phase1" in requested_steps:
        results.append(run_phase_one(args.parser_dir, args.phase1_output))

    if any(step in ("cv", "cv_parser", "parse_cvs") for step in requested_steps):
        results.append(run_cv_parser(args.cv_source, args.cv_output, args.force_cv))

    if not results:
        cli.error("No valid steps requested")

    print("\n========== INGESTION SUMMARY ==========")
    exit_code = 0
    for result in results:
        status = "✅" if result.success else "⚠️"
        print(f"{status} {result.name}: {result.details}")
        if not result.success:
            exit_code = 1

    print("======================================\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
