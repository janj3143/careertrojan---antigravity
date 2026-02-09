#!/usr/bin/env python3
"""
nightly_retrain.py — Scheduled model retrain script
=====================================================

Purpose:
  Runs a full model retrain cycle via the TrainingOrchestrator.
  Designed to be invoked nightly by Windows Task Scheduler, cron,
  or a CI/CD pipeline.

Workflow:
  1. Acquire a file-lock so only one instance runs at a time
  2. Load runtime config (data root, model dirs)
  3. Invoke TrainingOrchestrator.run_full_training()
  4. Back up previous models before overwriting
  5. Write a JSON run-log to logs/nightly_retrain/
  6. Exit 0 on success, 1 on failure

Usage:
  python scripts/nightly_retrain.py [--dry-run] [--data-dir PATH] [--models-dir PATH]

Schedule (Windows Task Scheduler):
  Action: C:\\Python\\python.exe
  Arguments: C:\\careertrojan\\scripts\\nightly_retrain.py
  Trigger: Daily 02:00
"""

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from services.ai_engine.config import models_path, AI_DATA_DIR, log_root


def acquire_lock(lock_path: Path) -> bool:
    """Simple file-lock: create lock file; fail if already exists."""
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.touch(exist_ok=False)
        return True
    except FileExistsError:
        return False


def release_lock(lock_path: Path):
    lock_path.unlink(missing_ok=True)


def backup_models(src: Path, backup_root: Path):
    """Copy current models to a timestamped backup folder."""
    if not src.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = backup_root / f"models_backup_{stamp}"
    shutil.copytree(src, dest, dirs_exist_ok=True)
    return dest


def write_run_log(log_dir: Path, result: dict):
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = log_dir / f"retrain_{stamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    return path


def main():
    parser = argparse.ArgumentParser(description="Nightly model retrain")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, don't train")
    parser.add_argument("--data-dir", type=str, default=str(AI_DATA_DIR), help="Training data directory")
    parser.add_argument("--models-dir", type=str, default=str(models_path), help="Output models directory")
    args = parser.parse_args()

    lock_path = log_root / "nightly_retrain" / ".retrain.lock"
    log_dir = log_root / "nightly_retrain"
    backup_root = models_path.parent / "model_backups"

    run_log = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_dir": args.data_dir,
        "models_dir": args.models_dir,
        "dry_run": args.dry_run,
        "status": "unknown",
        "duration_s": 0,
        "backup_path": None,
        "error": None,
    }

    # ── Lock ─────────────────────────────────────────────────────
    if not acquire_lock(lock_path):
        msg = "Another nightly_retrain instance is already running (lock exists)."
        print(f"⚠️  {msg}")
        run_log["status"] = "skipped"
        run_log["error"] = msg
        write_run_log(log_dir, run_log)
        return 0  # Not a failure — just a skip

    t0 = time.time()
    try:
        if args.dry_run:
            print("🔍 Dry-run mode — skipping actual training")
            print(f"   Data dir  : {args.data_dir}")
            print(f"   Models dir: {args.models_dir}")
            run_log["status"] = "dry-run"
            write_run_log(log_dir, run_log)
            return 0

        # ── Backup existing models ───────────────────────────────
        backup_dest = backup_models(Path(args.models_dir), backup_root)
        run_log["backup_path"] = str(backup_dest) if backup_dest else None
        if backup_dest:
            print(f"📦 Backed up models → {backup_dest}")

        # ── Run training ─────────────────────────────────────────
        from services.ai_engine.training_orchestrator import TrainingOrchestrator

        orchestrator = TrainingOrchestrator(
            data_dir=args.data_dir,
            models_dir=args.models_dir,
            registry_dir=args.models_dir,
        )
        success = orchestrator.run_full_training()

        duration = round(time.time() - t0, 2)
        run_log["duration_s"] = duration
        run_log["status"] = "success" if success else "failed"
        run_log["finished_at"] = datetime.now(timezone.utc).isoformat()

        log_path = write_run_log(log_dir, run_log)
        print(f"{'✅' if success else '❌'} Training {'succeeded' if success else 'failed'} in {duration}s")
        print(f"📄 Run log → {log_path}")
        return 0 if success else 1

    except Exception as exc:
        run_log["status"] = "error"
        run_log["error"] = str(exc)
        run_log["duration_s"] = round(time.time() - t0, 2)
        write_run_log(log_dir, run_log)
        print(f"❌ Nightly retrain crashed: {exc}")
        return 1

    finally:
        release_lock(lock_path)


if __name__ == "__main__":
    sys.exit(main())
