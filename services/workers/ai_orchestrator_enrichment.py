"""
CareerTrojan — AI Orchestrator Enrichment Worker
==================================================
Monitors USER DATA/interactions/ for new user events and feeds them back
into ai_data_final to continuously improve the AI knowledge base.

Triggers:
  - Resume uploaded → parse + update parsed_resumes/
  - Match accepted/rejected → update job_matching/ training data
  - Profile updated → re-extract skills → update profiles/
  - Coaching session → extract interests → update learning_library/

Works on both Windows and Ubuntu — all paths from environment variables.
"""
import os
import sys
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog==4.0.0")
    sys.exit(1)

# ── Paths (cross-platform) ──────────────────────────────────
INTERACTIONS_DIR = Path(os.getenv(
    "CAREERTROJAN_USER_DATA",
    r"L:\VS ai_data final - version\USER DATA" if sys.platform == "win32" else "/mnt/careertrojan/user_data"
)) / "interactions"

AI_DATA_ROOT = Path(os.getenv(
    "CAREERTROJAN_AI_DATA",
    r"L:\VS ai_data final - version\ai_data_final" if sys.platform == "win32" else "/mnt/careertrojan/ai_data_final"
))

LOG_DIR = Path(os.getenv(
    "CAREERTROJAN_APP_LOGS",
    r"C:\careertrojan\logs" if sys.platform == "win32" else "/mnt/careertrojan/logs"
))

# ── Logging ──────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AI-ORCH] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "ai_orchestrator.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("ai_orchestrator")

# ── Enrichment Targets in ai_data_final ──────────────────────
ENRICHMENT_TARGETS = {
    "upload":      AI_DATA_ROOT / "parsed_resumes",
    "search":      AI_DATA_ROOT / "job_matching",
    "coaching":    AI_DATA_ROOT / "learning_library",
    "enrichment":  AI_DATA_ROOT / "profiles",
    "login":       AI_DATA_ROOT / "metadata",
    "mentor":      AI_DATA_ROOT / "mentorship_matches.json",
}


def ensure_enrichment_dirs():
    """Create enrichment target directories if missing."""
    for target in ENRICHMENT_TARGETS.values():
        if target.suffix:  # It's a file path, ensure parent
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)


def process_interaction(filepath: Path):
    """
    Read an interaction JSON and route it to the appropriate
    enrichment pipeline in ai_data_final.
    """
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Cannot read interaction {filepath.name}: {e}")
        return

    action = data.get("action", "unknown")
    user_id = data.get("user_id", "unknown")
    timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())

    logger.info(f"Processing: {action} from user {user_id}")

    if action == "upload":
        _handle_resume_upload(data, user_id, timestamp)
    elif action == "search":
        _handle_search_event(data, user_id, timestamp)
    elif action == "coaching":
        _handle_coaching_event(data, user_id, timestamp)
    elif action == "enrichment":
        _handle_enrichment_event(data, user_id, timestamp)
    elif action == "login":
        _handle_login_event(data, user_id, timestamp)
    elif action == "mentor":
        _handle_mentor_event(data, user_id, timestamp)
    elif action == "match_decision":
        _handle_match_decision(data, user_id, timestamp)
    else:
        logger.debug(f"No enrichment handler for action: {action}")


def _handle_resume_upload(data: dict, user_id: str, ts: str):
    """Resume uploaded → extract metadata for AI training."""
    target_dir = ENRICHMENT_TARGETS["upload"]
    entry = {
        "user_id": user_id,
        "timestamp": ts,
        "source": "user_upload",
        "metadata": data.get("metadata", {}),
        "enriched_at": datetime.now(timezone.utc).isoformat(),
    }
    outfile = target_dir / f"{user_id}_latest_upload.json"
    outfile.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    logger.info(f"  → Enriched parsed_resumes for {user_id}")


def _handle_search_event(data: dict, user_id: str, ts: str):
    """Search query → update job matching model training data."""
    target_dir = ENRICHMENT_TARGETS["search"]
    # Append to user's search history for model training
    history_file = target_dir / f"{user_id}_search_history.jsonl"
    entry = json.dumps({
        "user_id": user_id,
        "timestamp": ts,
        "query": data.get("metadata", {}).get("query", ""),
        "results_count": data.get("metadata", {}).get("results_count", 0),
    }) + "\n"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"  → Appended search event to job_matching for {user_id}")


def _handle_coaching_event(data: dict, user_id: str, ts: str):
    """Coaching session → extract topics for learning library."""
    target_dir = ENRICHMENT_TARGETS["coaching"]
    topics = data.get("metadata", {}).get("topics", [])
    if topics:
        topics_file = target_dir / f"{user_id}_coaching_topics.json"
        existing = []
        if topics_file.exists():
            try:
                existing = json.loads(topics_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing.extend([{"topic": t, "timestamp": ts} for t in topics])
        topics_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        logger.info(f"  → Updated learning_library with {len(topics)} topics for {user_id}")


def _handle_enrichment_event(data: dict, user_id: str, ts: str):
    """Enrichment completed → update user's AI profile."""
    target_dir = ENRICHMENT_TARGETS["enrichment"]
    profile_file = target_dir / f"{user_id}.json"
    profile = {}
    if profile_file.exists():
        try:
            profile = json.loads(profile_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    profile["last_enrichment"] = ts
    profile["skills"] = data.get("metadata", {}).get("skills", profile.get("skills", []))
    profile_file.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    logger.info(f"  → Updated profile enrichment for {user_id}")


def _handle_login_event(data: dict, user_id: str, ts: str):
    """Login → track usage patterns in metadata."""
    target_dir = ENRICHMENT_TARGETS["login"]
    logins_file = target_dir / "login_patterns.jsonl"
    entry = json.dumps({"user_id": user_id, "timestamp": ts}) + "\n"
    with open(logins_file, "a", encoding="utf-8") as f:
        f.write(entry)


def _handle_mentor_event(data: dict, user_id: str, ts: str):
    """Mentor interaction → update mentorship matching model."""
    target = ENRICHMENT_TARGETS["mentor"]
    existing = []
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.append({
        "user_id": user_id,
        "timestamp": ts,
        "feedback": data.get("metadata", {}).get("feedback", ""),
    })
    target.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    logger.info(f"  → Updated mentorship matches for {user_id}")


def _handle_match_decision(data: dict, user_id: str, ts: str):
    """User accepted/rejected a match → training signal for AI."""
    target_dir = ENRICHMENT_TARGETS["search"]
    decisions_file = target_dir / f"{user_id}_match_decisions.jsonl"
    entry = json.dumps({
        "user_id": user_id,
        "timestamp": ts,
        "job_id": data.get("metadata", {}).get("job_id", ""),
        "decision": data.get("metadata", {}).get("decision", ""),  # "accepted" or "rejected"
        "score": data.get("metadata", {}).get("score", 0),
    }) + "\n"
    with open(decisions_file, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.info(f"  → Recorded match decision for {user_id}")


# ── Filesystem Watcher ───────────────────────────────────────
class InteractionHandler(FileSystemEventHandler):
    """Watches interactions/ for new files and routes them to enrichment."""

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            try:
                process_interaction(Path(event.src_path))
            except Exception as e:
                logger.error(f"Error processing {event.src_path}: {e}")


def main():
    logger.info("AI Orchestrator Enrichment Worker starting...")
    logger.info(f"  Watching:   {INTERACTIONS_DIR}")
    logger.info(f"  Enriching:  {AI_DATA_ROOT}")

    if not INTERACTIONS_DIR.exists():
        INTERACTIONS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"  Created interactions dir: {INTERACTIONS_DIR}")

    ensure_enrichment_dirs()

    # Process any existing unprocessed interactions on startup
    existing = list(INTERACTIONS_DIR.glob("*.json"))
    if existing:
        logger.info(f"  Processing {len(existing)} existing interactions...")
        for f in existing:
            try:
                process_interaction(f)
            except Exception as e:
                logger.error(f"Startup processing error for {f.name}: {e}")

    # Start watching for new interactions
    handler = InteractionHandler()
    observer = Observer()
    observer.schedule(handler, str(INTERACTIONS_DIR), recursive=False)
    observer.start()
    logger.info("Watching for new interactions...")

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("Shutting down AI orchestrator...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
