#!/usr/bin/env python3
"""
CareerTrojan Backup Script — Track E, Step E5
==============================================

Backs up:
  1. PostgreSQL database  → pg_dump / SQLite .backup
  2. AI training data     → ai_data_final/ directory
  3. User uploads         → data/user_uploads/
  4. Trained models       → trained_models/
  5. Interaction logs     → ai_data_final/USER DATA/interactions/

Designed to run either:
  - Manually:   python scripts/backup_all.py
  - Cron/Task:  Daily at 02:00 UTC (see schedule examples at bottom)
  - Docker:     docker exec careertrojan-backend python scripts/backup_all.py

Outputs:
  - Timestamped .tar.gz archives in  BACKUP_DIR  (default: ./backups/)
  - Backup manifest JSON
  - Cleans up archives older than RETENTION_DAYS

Environment variables (all optional — sane defaults provided):
  BACKUP_DIR           where to write archives     (default: ./backups)
  BACKUP_RETENTION_DAYS  how many days to keep      (default: 30)
  CAREERTROJAN_DB_URL  postgres://...               (default: SQLite dev DB)
  PGPASSWORD           if not embedded in DB_URL
"""

import datetime
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.parse import urlparse

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", str(PROJECT_ROOT / "backups")))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
TIMESTAMP = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
DB_URL = os.getenv("CAREERTROJAN_DB_URL", "")

# Directories to back up
DATA_DIRS = {
    "ai_data":      PROJECT_ROOT / "ai_data_final",
    "user_uploads":  PROJECT_ROOT / "data" / "user_uploads",
    "trained_models": PROJECT_ROOT / "trained_models",
    "interaction_logs": PROJECT_ROOT / "ai_data_final" / "USER DATA" / "interactions",
}


# ============================================================================
# UTILITIES
# ============================================================================

def log(msg: str):
    print(f"[{datetime.datetime.utcnow().isoformat()}] {msg}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


# ============================================================================
# DATABASE BACKUP
# ============================================================================

def backup_postgres(db_url: str) -> Path | None:
    """Run pg_dump and produce a .sql.gz file."""
    parsed = urlparse(db_url)
    host = parsed.hostname or "localhost"
    port = str(parsed.port or 5432)
    user = parsed.username or "postgres"
    password = parsed.password or os.getenv("PGPASSWORD", "")
    dbname = parsed.path.lstrip("/")

    if not dbname:
        log("WARNING: No database name in CAREERTROJAN_DB_URL, skipping PG backup")
        return None

    dump_file = BACKUP_DIR / f"pg_{dbname}_{TIMESTAMP}.sql"
    gz_file = dump_file.with_suffix(".sql.gz")

    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password

    cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", user,
        "-F", "plain",        # plain SQL for max portability
        "--no-owner",
        "--no-privileges",
        "-f", str(dump_file),
        dbname,
    ]

    log(f"Running pg_dump for {dbname}@{host}:{port} ...")
    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        log("WARNING: pg_dump not found. Install PostgreSQL client tools.")
        return None
    except subprocess.CalledProcessError as e:
        log(f"WARNING: pg_dump failed: {e.stderr}")
        return None

    # Compress
    import gzip
    with open(dump_file, "rb") as f_in, gzip.open(gz_file, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    dump_file.unlink()

    log(f"PostgreSQL backup: {gz_file.name} ({gz_file.stat().st_size:,} bytes)")
    return gz_file


def backup_sqlite() -> Path | None:
    """Back up the dev SQLite database."""
    db_path = PROJECT_ROOT / "data" / "ai_data_final" / "ai_learning_table.db"
    if not db_path.exists():
        log("No SQLite database found, skipping")
        return None

    dest = BACKUP_DIR / f"sqlite_dev_{TIMESTAMP}.db"
    log(f"Backing up SQLite: {db_path.name} ...")

    # Use SQLite online backup API for consistency
    src_conn = sqlite3.connect(str(db_path))
    dst_conn = sqlite3.connect(str(dest))
    src_conn.backup(dst_conn)
    src_conn.close()
    dst_conn.close()

    log(f"SQLite backup: {dest.name} ({dest.stat().st_size:,} bytes)")
    return dest


def backup_database() -> Path | None:
    """Detect environment and back up the right database."""
    if DB_URL and DB_URL.startswith("postgres"):
        return backup_postgres(DB_URL)
    else:
        return backup_sqlite()


# ============================================================================
# DIRECTORY BACKUP
# ============================================================================

def backup_directory(name: str, source: Path) -> Path | None:
    """Tar + gzip a directory."""
    if not source.exists():
        log(f"Skipping {name}: {source} does not exist")
        return None

    # Count files
    file_count = sum(1 for _ in source.rglob("*") if _.is_file())
    if file_count == 0:
        log(f"Skipping {name}: directory is empty")
        return None

    archive = BACKUP_DIR / f"{name}_{TIMESTAMP}.tar.gz"
    log(f"Archiving {name}: {file_count} files from {source.relative_to(PROJECT_ROOT)} ...")

    with tarfile.open(archive, "w:gz") as tar:
        tar.add(str(source), arcname=name)

    log(f"  → {archive.name} ({archive.stat().st_size:,} bytes)")
    return archive


# ============================================================================
# RETENTION CLEANUP
# ============================================================================

def cleanup_old_backups():
    """Remove backup files older than RETENTION_DAYS."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=RETENTION_DAYS)
    removed = 0
    for f in BACKUP_DIR.iterdir():
        if f.is_file() and f.suffix in (".gz", ".db", ".json"):
            mtime = datetime.datetime.utcfromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                removed += 1
    if removed:
        log(f"Cleaned up {removed} backup(s) older than {RETENTION_DAYS} days")


# ============================================================================
# MANIFEST
# ============================================================================

def write_manifest(files: list):
    """Write a JSON manifest of all backup files with checksums."""
    manifest = {
        "timestamp": TIMESTAMP,
        "utc_time": datetime.datetime.utcnow().isoformat() + "Z",
        "retention_days": RETENTION_DAYS,
        "files": [],
    }
    for f in files:
        if f and f.exists():
            manifest["files"].append({
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "sha256": sha256_file(f),
            })

    manifest_path = BACKUP_DIR / f"manifest_{TIMESTAMP}.json"
    with open(manifest_path, "w") as fp:
        json.dump(manifest, fp, indent=2)
    log(f"Manifest written: {manifest_path.name}")
    return manifest


# ============================================================================
# MAIN
# ============================================================================

def main():
    log("=" * 60)
    log("CareerTrojan Backup — Starting")
    log(f"  Project root : {PROJECT_ROOT}")
    log(f"  Backup dir   : {BACKUP_DIR}")
    log(f"  Retention    : {RETENTION_DAYS} days")
    log(f"  DB URL set   : {'yes (PostgreSQL)' if DB_URL else 'no (SQLite dev)'}")
    log("=" * 60)

    ensure_dir(BACKUP_DIR)

    results = []

    # 1) Database
    results.append(backup_database())

    # 2) Data directories
    for name, path in DATA_DIRS.items():
        results.append(backup_directory(name, path))

    # 3) Manifest
    write_manifest(results)

    # 4) Retention cleanup
    cleanup_old_backups()

    # Summary
    completed = [r for r in results if r is not None]
    log("=" * 60)
    log(f"Backup complete: {len(completed)} archive(s) in {BACKUP_DIR}")
    total_bytes = sum(r.stat().st_size for r in completed)
    log(f"Total size: {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.1f} MB)")
    log("=" * 60)

    return 0 if completed else 1


if __name__ == "__main__":
    sys.exit(main())


# ============================================================================
# CRON / SCHEDULED TASK EXAMPLES
# ============================================================================
#
# --- Linux cron (daily 02:00 UTC) ---
# 0 2 * * * cd /opt/careertrojan && /usr/bin/python3 scripts/backup_all.py >> /var/log/careertrojan-backup.log 2>&1
#
# --- Windows Task Scheduler (PowerShell) ---
# $action  = New-ScheduledTaskAction -Execute "J:\Python311\python.exe" -Argument "scripts\backup_all.py" -WorkingDirectory "C:\careertrojan"
# $trigger = New-ScheduledTaskTrigger -Daily -At 2am
# Register-ScheduledTask -TaskName "CareerTrojan Backup" -Action $action -Trigger $trigger
#
# --- Docker (run from host) ---
# docker exec careertrojan-backend python scripts/backup_all.py
#
# --- Docker Compose service (add to compose.yaml) ---
# backup:
#   image: careertrojan-backend
#   command: python scripts/backup_all.py
#   volumes:
#     - ./backups:/app/backups
#   environment:
#     - CAREERTROJAN_DB_URL=postgresql://user:pass@postgres:5432/careertrojan
#   depends_on:
#     - postgres
