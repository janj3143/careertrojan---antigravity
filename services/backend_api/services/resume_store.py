"""
Resume Store — JSON-file-backed store for resume snapshots.

Each user gets a directory under ``{project_root}/user_data/{user_id}/resumes/``.
Files are named ``{resume_id}.json`` and carry the parsed content,
fingerprint, abuse metadata, and status flag.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ResumeRecord:
    resume_id: str
    user_id: str
    status: str                        # "active" | "master" | "pending"
    fingerprint: str
    abuse: Dict[str, Any] = field(default_factory=dict)
    parsed: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    created_at: str = ""


class ResumeStore:
    """Flat-file resume persistence (one JSON per upload)."""

    def __init__(self, project_root: Path):
        self.base = project_root / "user_data"
        self.base.mkdir(parents=True, exist_ok=True)

    # ── helpers ──────────────────────────────────────────────────────
    def _user_dir(self, user_id: str) -> Path:
        d = self.base / user_id / "resumes"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _load(self, path: Path) -> ResumeRecord:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ResumeRecord(**{k: data[k] for k in ResumeRecord.__dataclass_fields__ if k in data})

    # ── public API ───────────────────────────────────────────────────
    def save(
        self,
        *,
        user_id: str,
        status: str,
        fingerprint: str,
        abuse: Dict[str, Any],
        parsed: Dict[str, Any],
        raw_text: str,
    ) -> ResumeRecord:
        rid = uuid.uuid4().hex[:12]
        rec = ResumeRecord(
            resume_id=rid,
            user_id=user_id,
            status=status,
            fingerprint=fingerprint,
            abuse=abuse,
            parsed=parsed,
            raw_text=raw_text,
            created_at=datetime.utcnow().isoformat(),
        )
        path = self._user_dir(user_id) / f"{rid}.json"
        path.write_text(json.dumps(rec.__dict__, indent=2, default=str),
                        encoding="utf-8")
        return rec

    def get_latest_by_status(self, user_id: str, status: str) -> Optional[ResumeRecord]:
        d = self._user_dir(user_id)
        candidates = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in candidates:
            rec = self._load(p)
            if rec.status == status:
                return rec
        return None

    def list_upload_timestamps(self, user_id: str) -> List[datetime]:
        d = self._user_dir(user_id)
        out: List[datetime] = []
        for p in d.glob("*.json"):
            rec = self._load(p)
            if rec.created_at:
                out.append(datetime.fromisoformat(rec.created_at))
        return out
