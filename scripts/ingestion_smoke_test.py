import os
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

from services.shared.paths import CareerTrojanPaths


def print_pass(msg: str) -> None:
    print(f"[PASS] {msg}")


def print_fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def print_warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def scan_json_files(root: Path, max_samples: int = 3) -> dict:
    result = {"count": 0, "latest": None, "samples": []}
    if not root.exists():
        return result

    latest_time = 0.0
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if not filename.lower().endswith(".json"):
                continue
            result["count"] += 1
            if len(result["samples"]) < max_samples:
                result["samples"].append(str(Path(dirpath) / filename))
            try:
                mtime = os.path.getmtime(os.path.join(dirpath, filename))
                if mtime > latest_time:
                    latest_time = mtime
            except OSError:
                continue

    if latest_time:
        result["latest"] = datetime.fromtimestamp(latest_time).isoformat()
    return result


def check_paths(paths: CareerTrojanPaths) -> None:
    print("\n--- 1. Path Resolution ---")
    print(f"data_root:      {paths.data_root}")
    print(f"ai_data_final:  {paths.ai_data_final}")
    print(f"parser_root:    {paths.parser_root}")
    print(f"user_data:      {paths.user_data}")
    print(f"interactions:  {paths.interactions}")

    if paths.data_root.exists():
        print_pass("Data root exists")
    else:
        print_fail("Data root missing")

    if paths.ai_data_final.exists():
        print_pass("AI data root exists")
    else:
        print_fail("AI data root missing")

    if paths.interactions.exists():
        print_pass("Interactions root exists")
    else:
        print_warn("Interactions root missing")


def check_ai_structure(paths: CareerTrojanPaths) -> None:
    print("\n--- 2. AI Data Structure ---")
    required_any = [
        "parsed_resumes",
        "parsed_job_descriptions",
        "job_titles",
        "metadata",
    ]
    recommended = [
        "profiles",
        "learning_library",
        "job_matching",
        "trained_models",
    ]

    existing_required = [name for name in required_any if (paths.ai_data_final / name).is_dir()]
    if existing_required:
        print_pass(f"Required AI subdirs present: {', '.join(existing_required)}")
    else:
        print_fail("No required AI subdirs found in ai_data_final")

    missing_recommended = [name for name in recommended if not (paths.ai_data_final / name).is_dir()]
    if missing_recommended:
        print_warn(f"Recommended AI subdirs missing: {', '.join(missing_recommended)}")
    else:
        print_pass("Recommended AI subdirs present")


def check_ingestion_outputs(paths: CareerTrojanPaths) -> None:
    print("\n--- 3. Ingestion Outputs ---")
    ai_json = scan_json_files(paths.ai_data_final)
    if ai_json["count"] > 0:
        print_pass(f"AI data JSON files found: {ai_json['count']}")
    else:
        print_warn("No JSON files found in ai_data_final")

    if ai_json["latest"]:
        print(f"Latest AI data JSON: {ai_json['latest']}")

    interactions_json = scan_json_files(paths.interactions)
    if interactions_json["count"] > 0:
        print_pass(f"Interaction JSON files found: {interactions_json['count']}")
    else:
        print_warn("No interaction JSON files found")

    if interactions_json["latest"]:
        print(f"Latest interaction JSON: {interactions_json['latest']}")


def main() -> None:
    print("CareerTrojan Ingestion Smoke Test")
    print("=================================")

    paths = CareerTrojanPaths()
    check_paths(paths)
    check_ai_structure(paths)
    check_ingestion_outputs(paths)

    print("\nIngestion smoke test complete.")


if __name__ == "__main__":
    main()
