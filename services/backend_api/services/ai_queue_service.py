"""
CareerTrojan — AI Agent Job Queue Service
==========================================
File-based job queue for asynchronous AI processing.

Zendesk webhooks drop JSON job files into a queue directory.
The AI agent worker polls the directory, picks up jobs, runs
LLM triage / draft-reply, writes results back, and moves the
job to processed/ or failed/.

Queue layout::

    <QUEUE_ROOT>/
        pending/        ← new jobs land here
        processing/     ← worker moves a job here while it runs
        processed/      ← finished jobs (kept for audit trail)
        failed/         ← jobs that errored out

Each job is a single JSON file named ``<job_id>.json``.

Works cross-platform (Windows dev / Linux prod).
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger("ai_queue")

# ── Queue root resolution ────────────────────────────────────────────────

_DEFAULT_QUEUE_ROOT_LINUX = Path("/opt/careertrojan/api/queue")
_DEFAULT_QUEUE_ROOT_WIN = Path(os.environ.get("CAREERTROJAN_APP_ROOT", r"J:\Codec - runtime version\Antigravity\careertrojan")) / "queue"


def _resolve_queue_root() -> Path:
    """Return the queue root directory, honouring env override."""
    env = os.getenv("CAREERTROJAN_AI_QUEUE_ROOT") or os.getenv("ZENDESK_AI_QUEUE_DIR")
    if env:
        return Path(env)
    if os.name == "nt":
        return _DEFAULT_QUEUE_ROOT_WIN
    return _DEFAULT_QUEUE_ROOT_LINUX


QUEUE_ROOT: Path = _resolve_queue_root()

SUBDIRS: List[str] = ["pending", "processing", "processed", "failed"]


def ensure_queue_dirs(root: Optional[Path] = None) -> Path:
    """Create the queue directory tree if it does not exist.  Returns root."""
    root = root or QUEUE_ROOT
    for sub in SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


# ── Job ID generation ────────────────────────────────────────────────────

def make_job_id(source: str = "zendesk") -> str:
    """Deterministic-prefix job ID with timestamp + random hex."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{source}_{ts}_{uuid.uuid4().hex[:12]}"


# ── Enqueue ──────────────────────────────────────────────────────────────

JobKind = Literal[
    "ticket_triage",       # classify priority / category
    "draft_reply",         # generate an AI-suggested reply
    "summarise_thread",    # produce a concise summary for admin
    "escalation_check",    # decide whether to escalate
]


def enqueue(
    payload: Dict[str, Any],
    *,
    kind: JobKind = "draft_reply",
    source: str = "zendesk",
    root: Optional[Path] = None,
    job_id: Optional[str] = None,
) -> str:
    """
    Write a job JSON file to ``pending/``.

    Parameters
    ----------
    payload : dict
        The raw webhook / ticket data to process.
    kind : str
        What the AI worker should do with this job.
    source : str
        Origin system (``zendesk``, ``support_form``, etc.).
    root : Path, optional
        Override queue root (mainly for tests).
    job_id : str, optional
        Explicit job ID (auto-generated if omitted).

    Returns
    -------
    str
        The job ID.
    """
    root = root or QUEUE_ROOT
    ensure_queue_dirs(root)

    job_id = job_id or make_job_id(source)
    job_path = root / "pending" / f"{job_id}.json"

    envelope: Dict[str, Any] = {
        "job_id": job_id,
        "kind": kind,
        "source": source,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "result": None,
        "error": None,
    }

    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(envelope, f, ensure_ascii=False, indent=2)

    logger.info("Enqueued AI job %s  kind=%s  source=%s", job_id, kind, source)
    return job_id


# ── Dequeue (for the worker) ────────────────────────────────────────────

def claim_next(root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Atomically move the oldest pending job into ``processing/`` and
    return the parsed envelope.  Returns *None* when the queue is empty.
    """
    root = root or QUEUE_ROOT
    pending_dir = root / "pending"
    if not pending_dir.exists():
        return None

    # Sort by filename (timestamp-prefixed) so oldest job wins.
    jobs = sorted(pending_dir.glob("*.json"))
    if not jobs:
        return None

    src = jobs[0]
    dst = root / "processing" / src.name
    try:
        shutil.move(str(src), str(dst))
    except OSError:
        # Another worker got it first — not an error.
        logger.debug("Lost race for %s", src.name)
        return None

    with open(dst, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    envelope["status"] = "processing"
    envelope["claimed_at"] = datetime.now(timezone.utc).isoformat()
    _overwrite(dst, envelope)

    logger.info("Claimed AI job %s", envelope["job_id"])
    return envelope


# ── Complete / fail ───────────────────────────────────────────────────────

def complete_job(
    job_id: str,
    result: Dict[str, Any],
    root: Optional[Path] = None,
) -> Path:
    """Move a processing job to ``processed/`` and write its result."""
    root = root or QUEUE_ROOT
    src = root / "processing" / f"{job_id}.json"
    dst = root / "processed" / f"{job_id}.json"

    envelope = _read(src)
    envelope["status"] = "processed"
    envelope["completed_at"] = datetime.now(timezone.utc).isoformat()
    envelope["result"] = result

    _overwrite(src, envelope)
    shutil.move(str(src), str(dst))
    logger.info("Completed AI job %s", job_id)
    return dst


def fail_job(
    job_id: str,
    error: str,
    root: Optional[Path] = None,
) -> Path:
    """Move a processing job to ``failed/`` with an error message."""
    root = root or QUEUE_ROOT
    src = root / "processing" / f"{job_id}.json"
    dst = root / "failed" / f"{job_id}.json"

    envelope = _read(src)
    envelope["status"] = "failed"
    envelope["failed_at"] = datetime.now(timezone.utc).isoformat()
    envelope["error"] = error

    _overwrite(src, envelope)
    shutil.move(str(src), str(dst))
    logger.warning("Failed AI job %s: %s", job_id, error)
    return dst


# ── Introspection (admin dashboard) ──────────────────────────────────────

def queue_stats(root: Optional[Path] = None) -> Dict[str, int]:
    """Return counts per sub-directory."""
    root = root or QUEUE_ROOT
    ensure_queue_dirs(root)
    return {
        sub: len(list((root / sub).glob("*.json")))
        for sub in SUBDIRS
    }


def list_jobs(
    bucket: str = "pending",
    limit: int = 50,
    root: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Return job summaries (no full payload) from a given bucket."""
    root = root or QUEUE_ROOT
    d = root / bucket
    if not d.exists():
        return []

    results: List[Dict[str, Any]] = []
    for p in sorted(d.glob("*.json"))[:limit]:
        try:
            env = json.loads(p.read_text(encoding="utf-8"))
            results.append({
                "job_id": env.get("job_id"),
                "kind": env.get("kind"),
                "source": env.get("source"),
                "status": env.get("status"),
                "created_at": env.get("created_at"),
                "claimed_at": env.get("claimed_at"),
                "completed_at": env.get("completed_at"),
                "error": env.get("error"),
            })
        except Exception:
            results.append({"job_id": p.stem, "status": "unreadable"})
    return results


def read_job(job_id: str, root: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Find a job by ID across all buckets and return full envelope."""
    root = root or QUEUE_ROOT
    for sub in SUBDIRS:
        p = root / sub / f"{job_id}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return None


# ── Helpers ──────────────────────────────────────────────────────────────

def _read(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _overwrite(path: Path, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
