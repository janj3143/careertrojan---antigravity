import json
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.shared.paths import CareerTrojanPaths

PARSER_MODULE_DIR = PROJECT_ROOT / "services" / "workers" / "ai" / "ai-workers" / "parser"
if str(PARSER_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(PARSER_MODULE_DIR))

from automated_parser_engine import AutomatedParserEngine


def append_progress(log_path: Path, payload: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    batch_size = 20000
    sleep_seconds = 3

    paths = CareerTrojanPaths()
    parser_root = paths.parser_root
    output_root = paths.ai_data_final / "parsed_from_automated"

    progress_log = PROJECT_ROOT / "logs" / "parser_until_complete_progress.jsonl"
    session_started = datetime.utcnow().isoformat() + "Z"

    run_no = 0
    while True:
        run_no += 1
        started_at = time.time()

        engine = AutomatedParserEngine(
            parser_root=str(parser_root),
            output_root=str(output_root),
        )
        results = engine.run(max_files=batch_size)

        duration = round(time.time() - started_at, 2)
        discovered = int(results.get("total_files", 0))
        processed = int(results.get("processed", 0))
        skipped = int(results.get("skipped", 0))
        skipped_existing = int(results.get("skipped_existing", 0))
        errors = len(results.get("errors", []))

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_started": session_started,
            "run_no": run_no,
            "duration_seconds": duration,
            "batch_size": batch_size,
            "discovered_unprocessed": discovered,
            "processed": processed,
            "skipped": skipped,
            "skipped_existing": skipped_existing,
            "errors": errors,
            "done": discovered <= batch_size,
        }
        append_progress(progress_log, payload)

        print(
            f"RUN={run_no} DISCOVERED={discovered} PROCESSED={processed} "
            f"SKIP={skipped} SKIP_EXISTING={skipped_existing} ERRORS={errors} "
            f"DONE={payload['done']} DURATION={duration}s"
        )

        if discovered == 0 or discovered <= batch_size:
            print("PARSER_UNTIL_COMPLETE_DONE=1")
            break

        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
