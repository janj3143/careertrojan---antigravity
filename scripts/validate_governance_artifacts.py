from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    ROOT / "reports" / "ROLE_OUTPUT_ACCEPTANCE_CRITERIA.md",
    ROOT / "reports" / "ROLE_FACTORIAL_TEST_MATRIX.md",
    ROOT / "reports" / "ENDPOINT_TOPOLOGY_MAP.md",
    ROOT / "reports" / "ENDPOINT_BRIDGE_TOUCHPOINT_MAP.md",
    ROOT / "data" / "governance" / "README.md",
    ROOT / "data" / "governance" / "outcome_labels.jsonl",
]


REQUIRED_JSONL_FIELDS = {
    "label_id",
    "role",
    "journey",
    "outcome",
    "ground_truth",
    "source",
    "evidence_refs",
    "created_at",
}


def validate_required_files() -> list[str]:
    errors: list[str] = []
    for file_path in REQUIRED_FILES:
        if not file_path.exists():
            errors.append(f"missing file: {file_path}")
    return errors


def validate_jsonl() -> list[str]:
    errors: list[str] = []
    jsonl_path = ROOT / "data" / "governance" / "outcome_labels.jsonl"
    if not jsonl_path.exists():
        return [f"missing file: {jsonl_path}"]

    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return ["outcome_labels.jsonl is empty"]

    for index, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {index}: invalid json ({exc})")
            continue

        missing = REQUIRED_JSONL_FIELDS.difference(record.keys())
        if missing:
            errors.append(f"line {index}: missing fields: {sorted(missing)}")

        if not isinstance(record.get("evidence_refs"), list):
            errors.append(f"line {index}: evidence_refs must be a list")

    return errors


def main() -> int:
    errors = []
    errors.extend(validate_required_files())
    errors.extend(validate_jsonl())

    if errors:
        print("GOVERNANCE_ARTIFACTS_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("GOVERNANCE_ARTIFACTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
