"""
CareerTrojan — Enrichment Watchdog
====================================

Background service that closes the learning feedback loop:

    User interaction (CV upload, search, job browse)
      → interaction_logger.py writes JSON to L:/…/USER DATA/interactions/
      → THIS watchdog detects new files
      → Feeds text through collocation_engine.enrichment_ingest()
      → Collocation engine discovers new phrases
      → persist_learned_phrases() writes them back to L: drive
      → Next user gets richer phrase matching

Can run as:
  1. A periodic background task inside FastAPI (via BackgroundTasks or on_startup)
  2. A standalone cron-like script (python -m services.ai_engine.enrichment_watchdog)

Usage inside FastAPI:
    from services.ai_engine.enrichment_watchdog import start_enrichment_loop
    @app.on_event("startup")
    async def startup():
        start_enrichment_loop(interval_seconds=300)  # every 5 minutes
"""

import os
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Data Paths ────────────────────────────────────────────────────────────
_DATA_ROOT = Path(os.getenv("CAREERTROJAN_DATA_ROOT", r"L:\antigravity_version_ai_data_final"))
INTERACTION_DIR = _DATA_ROOT / "USER DATA" / "interactions"
WATCHDOG_STATE_PATH = _DATA_ROOT / "ai_data_final" / "enrichment_watchdog_state.json"


class EnrichmentWatchdog:
    """
    Monitors the interaction log directory and feeds new text through
    the collocation engine's learning pipeline.
    """

    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_processed_time: float = self._load_state()

    # ── State persistence ────────────────────────────────────────────────

    def _load_state(self) -> float:
        """Load the last-processed timestamp so we don't re-ingest old files."""
        if WATCHDOG_STATE_PATH.exists():
            try:
                with open(WATCHDOG_STATE_PATH, "r") as f:
                    data = json.load(f)
                ts = data.get("last_processed_time", 0.0)
                logger.info("Watchdog state restored: last_processed=%s",
                            datetime.fromtimestamp(ts).isoformat() if ts > 0 else "never")
                return ts
            except Exception as e:
                logger.warning("Failed to load watchdog state: %s", e)
        return 0.0

    def _save_state(self) -> None:
        """Persist the last-processed timestamp."""
        try:
            WATCHDOG_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(WATCHDOG_STATE_PATH, "w") as f:
                json.dump({
                    "last_processed_time": self._last_processed_time,
                    "saved_at": datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.warning("Failed to save watchdog state: %s", e)

    # ── Core scan logic ──────────────────────────────────────────────────

    def scan_and_ingest(self) -> Dict[str, Any]:
        """
        Scan for new interaction files since last run, extract text,
        feed through collocation_engine.enrichment_ingest().
        """
        from services.ai_engine.collocation_engine import collocation_engine

        if not INTERACTION_DIR.exists():
            return {"status": "skip", "reason": f"Interaction dir missing: {INTERACTION_DIR}"}

        texts = []
        files_scanned = 0
        cutoff = self._last_processed_time
        newest_mtime = cutoff

        for date_dir in INTERACTION_DIR.iterdir():
            if not date_dir.is_dir():
                continue
            for json_file in date_dir.glob("*.json"):
                try:
                    mtime = json_file.stat().st_mtime
                    if mtime <= cutoff:
                        continue
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Extract text from any known field
                    for key in ("body", "text", "query", "content", "resume_text",
                                "search_query", "description", "cover_letter"):
                        val = data.get(key)
                        if isinstance(val, str) and len(val) > 30:
                            texts.append(val)
                    files_scanned += 1
                    newest_mtime = max(newest_mtime, mtime)
                except Exception as e:
                    logger.debug("Skip %s: %s", json_file, e)

        if not texts:
            return {
                "status": "no_new_data",
                "files_scanned": files_scanned,
                "cutoff": datetime.fromtimestamp(cutoff).isoformat() if cutoff > 0 else "epoch",
            }

        # Feed through the learning engine
        result = collocation_engine.enrichment_ingest(texts, source="watchdog")

        # Update watermark
        self._last_processed_time = newest_mtime
        self._save_state()

        result["files_scanned"] = files_scanned
        result["status"] = "ingested"
        logger.info("Watchdog ingested %d texts from %d files → %d new phrases",
                     len(texts), files_scanned, result.get("new_discoveries", 0))
        return result

    # ── Background loop ──────────────────────────────────────────────────

    def _loop(self) -> None:
        """Background thread loop — runs scan_and_ingest periodically."""
        logger.info("Enrichment watchdog started (interval=%ds)", self.interval)
        while self._running:
            try:
                self.scan_and_ingest()
            except Exception as e:
                logger.error("Watchdog scan error: %s", e)
            time.sleep(self.interval)

    def start(self) -> None:
        """Start the watchdog in a background daemon thread."""
        if self._running:
            logger.warning("Watchdog already running")
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="enrichment-watchdog")
        self._thread.start()

    def stop(self) -> None:
        """Signal the watchdog loop to stop."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Enrichment watchdog stopped")


# ── Module-level singleton ───────────────────────────────────────────────
_watchdog: Optional[EnrichmentWatchdog] = None


def start_enrichment_loop(interval_seconds: int = 300) -> EnrichmentWatchdog:
    """
    Start the enrichment watchdog as a background daemon.
    Safe to call multiple times — only one instance runs.

    Usage in FastAPI:
        @app.on_event("startup")
        async def startup():
            start_enrichment_loop(interval_seconds=300)
    """
    global _watchdog
    if _watchdog is None or not _watchdog._running:
        _watchdog = EnrichmentWatchdog(interval_seconds)
        _watchdog.start()
    return _watchdog


def stop_enrichment_loop() -> None:
    """Stop the running watchdog."""
    global _watchdog
    if _watchdog:
        _watchdog.stop()
        _watchdog = None


# ── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    watchdog = EnrichmentWatchdog(interval_seconds=60)
    result = watchdog.scan_and_ingest()
    print(json.dumps(result, indent=2, default=str))
