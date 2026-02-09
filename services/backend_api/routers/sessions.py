"""
Session & User Data Router — CareerTrojan Backend
==================================================
Provides endpoints for:
  - Session history and summaries
  - User interaction logging
  - Consolidated user data view
  - Data sync status

All writes to USER DATA are trapped and mirrored to E:\\CareerTrojan\\USER_DATA_COPY
"""
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("backend.sessions")

router = APIRouter(
    prefix="/api/sessions/v1",
    tags=["sessions"],
)

# ── Data Paths ────────────────────────────────────────────────
USER_DATA_ROOT = Path(os.getenv(
    "CAREERTROJAN_USER_DATA",
    r"L:\VS ai_data final - version\USER DATA"
))
USER_DATA_MIRROR = Path(os.getenv(
    "CAREERTROJAN_USER_DATA_MIRROR",
    r"E:\CareerTrojan\USER_DATA_COPY"
))


# ── Models ────────────────────────────────────────────────────
class SessionEvent(BaseModel):
    user_id: str
    action: str       # login, logout, page_view, upload, search, coaching, enrichment
    page: Optional[str] = None
    metadata: Optional[dict] = None


class SessionSummary(BaseModel):
    totalSessions: int
    totalPageViews: int
    lastSessionDate: str
    averageDuration: str


# ── Helpers ───────────────────────────────────────────────────
def _ensure_dirs():
    """Ensure session and interaction directories exist in both locations."""
    for root in [USER_DATA_ROOT, USER_DATA_MIRROR]:
        for sub in ["sessions", "interactions", "profiles", "cv_uploads", "ai_matches", "session_logs"]:
            (root / sub).mkdir(parents=True, exist_ok=True)


def _write_with_mirror(relative_path: str, data: dict):
    """Write JSON to USER DATA on L: and mirror to E:."""
    for root in [USER_DATA_ROOT, USER_DATA_MIRROR]:
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    logger.info(f"Wrote + mirrored: {relative_path}")


def _update_sync_metadata():
    """Update sync metadata in both locations."""
    meta = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "synced_by": "session_router",
        "l_drive_path": str(USER_DATA_ROOT),
        "e_drive_path": str(USER_DATA_MIRROR),
    }
    for root in [USER_DATA_ROOT, USER_DATA_MIRROR]:
        p = root / "_sync_metadata.json"
        p.write_text(json.dumps(meta, indent=2), encoding="utf-8")


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/log")
async def log_session_event(event: SessionEvent):
    """
    Log a user session event (login, page view, action, etc.).
    Written to both L: and E: USER DATA.
    """
    _ensure_dirs()
    ts = datetime.now(timezone.utc)
    filename = f"{ts.strftime('%Y%m%d')}_{event.user_id}_{event.action}.json"

    entry = {
        "user_id": event.user_id,
        "action": event.action,
        "page": event.page,
        "timestamp": ts.isoformat(),
        "metadata": event.metadata or {},
    }

    _write_with_mirror(f"interactions/{filename}", entry)

    # Also append to session log (immutable audit trail)
    log_path = f"session_logs/{ts.strftime('%Y%m%d')}_log.jsonl"
    log_line = json.dumps(entry, default=str) + "\n"
    for root in [USER_DATA_ROOT, USER_DATA_MIRROR]:
        p = root / log_path
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(log_line)

    _update_sync_metadata()
    return {"status": "logged", "file": filename}


@router.get("/summary/{user_id}", response_model=SessionSummary)
async def get_session_summary(user_id: str):
    """
    Get a summary of a user's session history.
    """
    sessions_dir = USER_DATA_ROOT / "sessions"
    interactions_dir = USER_DATA_ROOT / "interactions"

    total_sessions = 0
    total_page_views = 0
    last_date = "Never"

    # Count interactions for this user
    if interactions_dir.exists():
        for f in interactions_dir.glob(f"*_{user_id}_*.json"):
            total_sessions += 1
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if data.get("action") == "page_view":
                    total_page_views += 1
                last_date = data.get("timestamp", last_date)
            except Exception:
                pass

    # Check active sessions
    active = sessions_dir / "active_sessions.json"
    if active.exists():
        try:
            all_sessions = json.loads(active.read_text(encoding="utf-8"))
            user_sessions = [s for s in all_sessions if s.get("user_id") == user_id]
            total_sessions = max(total_sessions, len(user_sessions))
        except Exception:
            pass

    return SessionSummary(
        totalSessions=total_sessions,
        totalPageViews=total_page_views,
        lastSessionDate=last_date,
        averageDuration="—",
    )


@router.get("/sync-status")
async def get_sync_status():
    """
    Check the sync status between L: and E: USER DATA mirrors.
    """
    l_meta_path = USER_DATA_ROOT / "_sync_metadata.json"
    e_meta_path = USER_DATA_MIRROR / "_sync_metadata.json"

    l_connected = USER_DATA_ROOT.exists()
    e_connected = USER_DATA_MIRROR.exists()

    l_meta = None
    e_meta = None
    if l_meta_path.exists():
        l_meta = json.loads(l_meta_path.read_text(encoding="utf-8"))
    if e_meta_path.exists():
        e_meta = json.loads(e_meta_path.read_text(encoding="utf-8"))

    # Count files in each location
    l_count = sum(1 for _ in USER_DATA_ROOT.rglob("*") if _.is_file()) if l_connected else 0
    e_count = sum(1 for _ in USER_DATA_MIRROR.rglob("*") if _.is_file()) if e_connected else 0

    return {
        "l_drive_connected": l_connected,
        "e_drive_connected": e_connected,
        "l_drive_file_count": l_count,
        "e_drive_file_count": e_count,
        "in_sync": l_count == e_count,
        "l_last_sync": l_meta.get("last_sync") if l_meta else None,
        "e_last_sync": e_meta.get("last_sync") if e_meta else None,
        "status": "synced" if (l_count == e_count and l_connected and e_connected) else "behind" if (l_connected and e_connected) else "error",
    }


@router.get("/consolidated/{user_id}")
async def get_consolidated_user_data(user_id: str):
    """
    Returns a consolidated view of all user data — profile, sessions,
    resume, matches, coaching, mentorship — for the Consolidation Page.
    """
    result = {
        "user_id": user_id,
        "profile": None,
        "sessions": None,
        "resume": None,
        "matches": None,
        "interactions_count": 0,
    }

    # Profile
    profile_path = USER_DATA_ROOT / "profiles" / f"{user_id}.json"
    if profile_path.exists():
        result["profile"] = json.loads(profile_path.read_text(encoding="utf-8"))

    # Sessions
    interactions_dir = USER_DATA_ROOT / "interactions"
    if interactions_dir.exists():
        user_files = list(interactions_dir.glob(f"*_{user_id}_*.json"))
        result["interactions_count"] = len(user_files)

    # Resume
    cv_dir = USER_DATA_ROOT / "cv_uploads" / user_id
    if cv_dir.exists():
        files = sorted(cv_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
        if files:
            result["resume"] = {"filename": files[0].name, "path": str(files[0])}

    # AI Matches
    matches_path = USER_DATA_ROOT / "ai_matches" / f"{user_id}_matches.json"
    if matches_path.exists():
        result["matches"] = json.loads(matches_path.read_text(encoding="utf-8"))

    return result
