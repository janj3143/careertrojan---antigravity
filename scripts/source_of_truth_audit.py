#!/usr/bin/env python3
"""
Deep Source-of-Truth Audit
==========================
Audits what is physically present under ai_data_final and automated_parser,
including .msg coverage and high-level parsed-output completeness.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.paths import CareerTrojanPaths


@dataclass
class FolderStats:
    name: str
    files: int
    json_files: int
    size_bytes: int
    top_extensions: List[Tuple[str, int]]

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "files": self.files,
            "json_files": self.json_files,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "top_extensions": [{"ext": ext, "count": count} for ext, count in self.top_extensions],
        }


def scan_folder(folder: Path, max_files: int = 0) -> FolderStats:
    total_files = 0
    json_files = 0
    size_bytes = 0
    ext_counter: Counter = Counter()

    for root, _dirs, files in os.walk(folder):
        for file_name in files:
            if max_files and total_files >= max_files:
                break

            total_files += 1
            suffix = Path(file_name).suffix.lower() or "<none>"
            ext_counter[suffix] += 1
            if suffix == ".json":
                json_files += 1

            file_path = Path(root) / file_name
            try:
                size_bytes += file_path.stat().st_size
            except Exception:
                pass

        if max_files and total_files >= max_files:
            break

    return FolderStats(
        name=folder.name,
        files=total_files,
        json_files=json_files,
        size_bytes=size_bytes,
        top_extensions=ext_counter.most_common(10),
    )


def scan_top_level(root: Path, max_files_per_folder: int = 0) -> List[FolderStats]:
    stats: List[FolderStats] = []
    if not root.exists():
        return stats

    for entry in root.iterdir():
        if entry.is_dir():
            stats.append(scan_folder(entry, max_files=max_files_per_folder))

    stats.sort(key=lambda row: row.files, reverse=True)
    return stats


def scan_root_files(root: Path) -> List[Dict]:
    rows: List[Dict] = []
    if not root.exists():
        return rows

    for entry in root.iterdir():
        if not entry.is_file():
            continue
        try:
            size = entry.stat().st_size
        except Exception:
            size = 0
        rows.append(
            {
                "name": entry.name,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 3),
                "ext": entry.suffix.lower() or "<none>",
            }
        )

    rows.sort(key=lambda row: row["size_bytes"], reverse=True)
    return rows


def find_msg_locations(root: Path, top_n: int = 100) -> List[Dict]:
    locations: Counter = Counter()
    if not root.exists():
        return []

    for walk_root, _dirs, files in os.walk(root):
        count = 0
        for file_name in files:
            if file_name.lower().endswith(".msg"):
                count += 1
        if count:
            locations[str(Path(walk_root))] += count

    rows = [{"path": path, "msg_count": count} for path, count in locations.most_common(top_n)]
    return rows


def check_key_processed_dirs(ai_root: Path) -> Dict[str, Dict]:
    key_dirs = [
        "parsed_from_automated",
        "parsed_cv_files",
        "parsed_resumes",
        "job_descriptions",
        "parsed_job_descriptions",
        "cv_files",
        "profiles",
        "learning_library",
    ]

    result: Dict[str, Dict] = {}
    for name in key_dirs:
        path = ai_root / name
        if not path.exists():
            result[name] = {"exists": False, "files": 0, "json_files": 0}
            continue

        files = 0
        json_files = 0
        for walk_root, _dirs, file_names in os.walk(path):
            files += len(file_names)
            json_files += sum(1 for file_name in file_names if file_name.lower().endswith(".json"))
        result[name] = {"exists": True, "files": files, "json_files": json_files}

    return result


def print_table(title: str, rows: List[FolderStats]) -> None:
    print("=" * 100)
    print(title)
    print("=" * 100)
    print(f"{'Folder':<42} {'Files':>10} {'JSON':>10} {'Size(MB)':>12}  Top extensions")
    print("-" * 100)
    for row in rows:
        ext_str = ", ".join(f"{ext}:{count}" for ext, count in row.top_extensions[:4])
        print(f"{row.name:<42} {row.files:>10,} {row.json_files:>10,} {row.size_bytes/1024/1024:>12.2f}  {ext_str}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit ai_data_final vs automated_parser coverage")
    parser.add_argument("--output", default=None, help="Optional JSON report output path")
    parser.add_argument(
        "--max-files-per-folder",
        type=int,
        default=0,
        help="Optional cap per top-level folder scan (0 = full scan)",
    )
    args = parser.parse_args()

    paths = CareerTrojanPaths()
    ai_root = paths.ai_data_final
    parser_root = paths.parser_root

    ai_stats = scan_top_level(ai_root, max_files_per_folder=max(0, args.max_files_per_folder))
    parser_stats = scan_top_level(parser_root, max_files_per_folder=max(0, args.max_files_per_folder))

    ai_root_files = scan_root_files(ai_root)
    parser_root_files = scan_root_files(parser_root)

    msg_locations = find_msg_locations(parser_root, top_n=200)
    key_processed = check_key_processed_dirs(ai_root)

    print_table("AI_DATA_FINAL — TOP LEVEL SUBFOLDER BREAKDOWN", ai_stats)
    print()
    print_table("AUTOMATED_PARSER — TOP LEVEL SUBFOLDER BREAKDOWN", parser_stats)

    print("\n" + "=" * 100)
    print("ROOT-LEVEL FILES")
    print("=" * 100)
    print(f"ai_data_final root files: {len(ai_root_files)}")
    print(f"automated_parser root files: {len(parser_root_files)}")

    print("\n" + "=" * 100)
    print(".MSG LOCATIONS")
    print("=" * 100)
    print(f"Total locations with .msg files: {len(msg_locations)}")
    for row in msg_locations[:20]:
        print(f"{row['msg_count']:>8,}  {row['path']}")

    print("\n" + "=" * 100)
    print("KEY PROCESSED DIRS (ai_data_final)")
    print("=" * 100)
    for name, data in key_processed.items():
        status = "OK" if data["exists"] else "MISSING"
        print(f"{name:<30} {status:<8} files={data['files']:>8,} json={data['json_files']:>8,}")

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "paths": {
            "data_root": str(paths.data_root),
            "ai_data_final": str(ai_root),
            "parser_root": str(parser_root),
        },
        "ai_data_final": {
            "top_level": [row.to_dict() for row in ai_stats],
            "root_files": ai_root_files,
        },
        "automated_parser": {
            "top_level": [row.to_dict() for row in parser_stats],
            "root_files": parser_root_files,
            "msg_locations": msg_locations,
        },
        "processed_coverage": key_processed,
    }

    if args.output:
        output = Path(args.output)
    else:
        output = paths.logs / f"source_of_truth_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written: {output}")


if __name__ == "__main__":
    main()
