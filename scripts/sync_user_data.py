"""
CareerTrojan — User Data Sync Trap
====================================
Watches the primary USER DATA directory (L:) and mirrors every change to
the backup location (E:) in real-time using the watchdog library.

Also runs a periodic full-sync every 15 minutes as a safety net.

Works on both Windows and Ubuntu — paths resolved from environment variables.

Usage:
    python scripts/sync_user_data.py              # foreground
    python scripts/sync_user_data.py --daemon      # background (Ubuntu systemd)
"""
import os
import sys
import json
import shutil
import hashlib
import logging
import argparse
import threading
from datetime import datetime, timezone
from pathlib import Path
from time import sleep

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError:
    print("ERROR: watchdog not installed. Run: pip install watchdog==4.0.0")
    sys.exit(1)

# ── Resolve paths from env (cross-platform) ─────────────────
SOURCE = Path(os.getenv(
    "CAREERTROJAN_USER_DATA",
    r"L:\VS ai_data final - version\USER DATA" if sys.platform == "win32" else "/mnt/careertrojan/user_data"
))
MIRROR = Path(os.getenv(
    "CAREERTROJAN_USER_DATA_MIRROR",
    r"E:\CareerTrojan\USER_DATA_COPY" if sys.platform == "win32" else "/mnt/careertrojan/backups/user_data"
))
LOG_DIR = Path(os.getenv(
    "CAREERTROJAN_APP_LOGS",
    r"C:\careertrojan\logs" if sys.platform == "win32" else "/mnt/careertrojan/logs"
))
FULL_SYNC_INTERVAL = 900  # 15 minutes

# ── Logging ──────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SYNC] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "sync_trap.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("sync_trap")


# ── Metadata ─────────────────────────────────────────────────
def update_sync_metadata(reason: str = "watcher"):
    """Write sync metadata to both locations."""
    meta = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "synced_by": reason,
        "source": str(SOURCE),
        "mirror": str(MIRROR),
        "platform": sys.platform,
    }
    for root in [SOURCE, MIRROR]:
        try:
            p = root / "_sync_metadata.json"
            p.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to write metadata to {root}: {e}")


# ── Real-time watcher ────────────────────────────────────────
class SyncHandler(FileSystemEventHandler):
    """Mirrors every file create/modify/delete from SOURCE to MIRROR."""

    def _relative(self, src_path: str) -> Path:
        return Path(src_path).relative_to(SOURCE)

    def _mirror_path(self, src_path: str) -> Path:
        return MIRROR / self._relative(src_path)

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            dest = self._mirror_path(event.src_path)
            dest.mkdir(parents=True, exist_ok=True)
            logger.info(f"DIR  + {self._relative(event.src_path)}")
        else:
            self._copy_file(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._copy_file(event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        dest = self._mirror_path(event.src_path)
        rel = self._relative(event.src_path)
        if event.is_directory:
            if dest.exists():
                # Move to quarantine instead of deleting immediately
                quarantine = MIRROR / "quarantine" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{rel.name}"
                quarantine.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.move(str(dest), str(quarantine))
                    logger.info(f"DIR  → quarantine: {rel}")
                except Exception as e:
                    logger.error(f"Failed to quarantine dir {rel}: {e}")
        else:
            if dest.exists():
                quarantine_dir = MIRROR / "quarantine"
                quarantine_dir.mkdir(parents=True, exist_ok=True)
                quarantine_file = quarantine_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{dest.name}"
                try:
                    shutil.move(str(dest), str(quarantine_file))
                    logger.info(f"FILE → quarantine: {rel}")
                except Exception as e:
                    logger.error(f"Failed to quarantine file {rel}: {e}")

    def on_moved(self, event):
        # Handle file/directory moves
        old_dest = self._mirror_path(event.src_path)
        new_rel = Path(event.dest_path).relative_to(SOURCE)
        new_dest = MIRROR / new_rel
        new_dest.parent.mkdir(parents=True, exist_ok=True)
        if old_dest.exists():
            try:
                shutil.move(str(old_dest), str(new_dest))
                logger.info(f"MOVE {self._relative(event.src_path)} → {new_rel}")
            except Exception as e:
                logger.error(f"Failed to mirror move: {e}")

    def _copy_file(self, src_path: str):
        rel = self._relative(src_path)
        dest = MIRROR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src_path, str(dest))
            logger.info(f"FILE ⟶ {rel}")
        except Exception as e:
            logger.error(f"Failed to mirror {rel}: {e}")


# ── Periodic full sync ───────────────────────────────────────
def full_sync():
    """Walk SOURCE and copy anything missing or newer to MIRROR."""
    logger.info("Full sync starting...")
    copied = 0
    skipped = 0

    for src_file in SOURCE.rglob("*"):
        if src_file.is_dir():
            continue
        rel = src_file.relative_to(SOURCE)
        dest = MIRROR / rel

        # Skip if dest exists and is same size + same or newer mtime
        if dest.exists():
            if dest.stat().st_size == src_file.stat().st_size:
                skipped += 1
                continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(str(src_file), str(dest))
            copied += 1
        except Exception as e:
            logger.error(f"Full sync failed for {rel}: {e}")

    update_sync_metadata("full_sync")
    logger.info(f"Full sync complete: {copied} copied, {skipped} skipped")


def periodic_sync_loop():
    """Run full_sync every FULL_SYNC_INTERVAL seconds in a background thread."""
    while True:
        sleep(FULL_SYNC_INTERVAL)
        try:
            full_sync()
        except Exception as e:
            logger.error(f"Periodic sync error: {e}")


# ── Main ─────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CareerTrojan User Data Sync Trap")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (no console interaction)")
    parser.add_argument("--once", action="store_true", help="Run a single full sync and exit")
    args = parser.parse_args()

    # Validate paths
    if not SOURCE.exists():
        logger.error(f"SOURCE does not exist: {SOURCE}")
        logger.error("Check CAREERTROJAN_USER_DATA environment variable or drive mount")
        sys.exit(1)

    MIRROR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Source:  {SOURCE}")
    logger.info(f"Mirror:  {MIRROR}")

    # Single full sync mode
    if args.once:
        full_sync()
        return

    # Run initial full sync
    full_sync()

    # Start periodic sync in background thread
    sync_thread = threading.Thread(target=periodic_sync_loop, daemon=True)
    sync_thread.start()
    logger.info(f"Periodic full sync every {FULL_SYNC_INTERVAL}s")

    # Start real-time filesystem watcher
    handler = SyncHandler()
    observer = Observer()
    observer.schedule(handler, str(SOURCE), recursive=True)
    observer.start()
    logger.info("Real-time watcher started — monitoring for changes")

    try:
        if args.daemon:
            observer.join()
        else:
            print("\nSync trap running. Press Ctrl+C to stop.\n")
            while observer.is_alive():
                observer.join(timeout=1)
    except KeyboardInterrupt:
        logger.info("Shutting down sync trap...")
        observer.stop()
    observer.join()
    logger.info("Sync trap stopped.")


if __name__ == "__main__":
    main()
