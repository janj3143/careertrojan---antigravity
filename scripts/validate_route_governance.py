from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"


@dataclass
class GateResult:
    passed: bool
    reasons: List[str]


def latest_report_path() -> Optional[Path]:
    candidates = sorted(REPORTS_DIR.glob("ROUTE_GOVERNANCE_REPORT_*.json"))
    if not candidates:
        return None
    return candidates[-1]


def evaluate(report: Dict[str, Any], args: argparse.Namespace) -> GateResult:
    reasons: List[str] = []

    added_count = int(report.get("added_count", 0))
    removed_count = int(report.get("removed_count", 0))
    duplicates = report.get("duplicate_semantic_routes", []) or []
    prefix_churn = report.get("prefix_churn", []) or []

    high_churn_count = sum(1 for row in prefix_churn if bool(row.get("high_churn")))
    duplicate_count = len(duplicates)

    if added_count > args.max_added_routes:
        reasons.append(
            f"added routes {added_count} exceeds max_added_routes {args.max_added_routes}"
        )
    if removed_count > args.max_removed_routes:
        reasons.append(
            f"removed routes {removed_count} exceeds max_removed_routes {args.max_removed_routes}"
        )
    if high_churn_count > args.max_high_churn_buckets:
        reasons.append(
            "high-churn prefix buckets "
            f"{high_churn_count} exceeds max_high_churn_buckets {args.max_high_churn_buckets}"
        )
    if duplicate_count > args.max_duplicate_semantic_routes:
        reasons.append(
            "duplicate semantic routes "
            f"{duplicate_count} exceeds max_duplicate_semantic_routes {args.max_duplicate_semantic_routes}"
        )

    return GateResult(passed=len(reasons) == 0, reasons=reasons)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate route governance report against gate thresholds")
    parser.add_argument(
        "--report",
        type=str,
        default="",
        help="Optional path to ROUTE_GOVERNANCE_REPORT_*.json; latest report is used when omitted.",
    )
    parser.add_argument("--max-added-routes", type=int, default=50)
    parser.add_argument("--max-removed-routes", type=int, default=5)
    parser.add_argument("--max-high-churn-buckets", type=int, default=10)
    parser.add_argument("--max-duplicate-semantic-routes", type=int, default=10)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    report_path = Path(args.report) if args.report else latest_report_path()
    if report_path is None or not report_path.exists():
        print("ROUTE_GOVERNANCE_GATE_FAIL")
        print("- no governance report found")
        return 1

    report = json.loads(report_path.read_text(encoding="utf-8"))
    result = evaluate(report, args)

    if not result.passed:
        print("ROUTE_GOVERNANCE_GATE_FAIL")
        print(f"- report: {report_path}")
        for reason in result.reasons:
            print(f"- {reason}")
        return 1

    print("ROUTE_GOVERNANCE_GATE_OK")
    print(f"- report: {report_path}")
    print(f"- added: {report.get('added_count', 0)}")
    print(f"- removed: {report.get('removed_count', 0)}")
    print(
        "- high_churn_buckets: "
        f"{sum(1 for row in (report.get('prefix_churn', []) or []) if bool(row.get('high_churn')))}"
    )
    print(f"- duplicate_semantic_routes: {len(report.get('duplicate_semantic_routes', []) or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
