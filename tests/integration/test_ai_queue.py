"""
Integration tests for the AI agent job queue:
  GET    /api/support/v1/ai/queue
  DELETE /api/support/v1/ai/queue/{job_id}
  + queue writes from ticket creation / admin reply
"""

import json
import os
import shutil
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

from services.backend_api.db import models
from services.backend_api.utils.security import create_access_token, get_password_hash


# ── helpers ──────────────────────────────────────────────────────────────

def _admin_headers():
    token = create_access_token(data={"sub": "admin@careertrojan.com", "role": "admin", "user_id": 1})
    return {"Authorization": f"Bearer {token}"}


def _user_headers():
    token = create_access_token(data={"sub": "regular@careertrojan.com", "role": "user", "user_id": 100})
    return {"Authorization": f"Bearer {token}"}


def _ensure_user(db, email: str, role: str = "user"):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return user
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        full_name=f"Test {role.title()}",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(autouse=True)
def _temp_queue_dir(tmp_path, monkeypatch):
    """Point the AI queue to a temp directory for each test and enable the agent."""
    queue_dir = str(tmp_path / "ai_queue")
    monkeypatch.setenv("ZENDESK_AI_QUEUE_DIR", queue_dir)
    monkeypatch.setenv("ZENDESK_AI_AGENT_ENABLED", "true")
    # Patch the module-level constants too (already evaluated at import time)
    import services.backend_api.services.support_service as svc
    monkeypatch.setattr(svc, "AI_QUEUE_DIR", queue_dir)
    monkeypatch.setattr(svc, "ZENDESK_AI_AGENT_ENABLED", True)
    yield queue_dir
    # cleanup handled by tmp_path fixture


# ── enqueue_ai_job unit ─────────────────────────────────────────────────

class TestEnqueueAiJob:

    def test_creates_job_file(self, _temp_queue_dir):
        from services.backend_api.services.support_service import enqueue_ai_job
        job_id = enqueue_ai_job(
            action="new_ticket",
            ticket_id=42,
            payload={"subject": "Help me", "category": "bugs"},
        )
        assert job_id.startswith("zendesk_")
        job_path = Path(_temp_queue_dir) / f"{job_id}.json"
        assert job_path.exists()

        data = json.loads(job_path.read_text())
        assert data["action"] == "new_ticket"
        assert data["ticket_id"] == 42
        assert data["status"] == "pending"
        assert data["payload"]["subject"] == "Help me"

    def test_creates_queue_dir_if_missing(self, _temp_queue_dir):
        """Queue dir should be auto-created."""
        shutil.rmtree(_temp_queue_dir, ignore_errors=True)
        from services.backend_api.services.support_service import enqueue_ai_job
        enqueue_ai_job(action="test", ticket_id=1, payload={})
        assert Path(_temp_queue_dir).is_dir()


# ── GET /ai/queue ────────────────────────────────────────────────────────

class TestAdminAiQueueStatus:

    def test_empty_queue(self, test_client, _temp_queue_dir):
        resp = test_client.get("/api/support/v1/ai/queue", headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["jobs"] == []

    def test_lists_queued_jobs(self, test_client, _temp_queue_dir):
        from services.backend_api.services.support_service import enqueue_ai_job
        job1 = enqueue_ai_job(action="new_ticket", ticket_id=1, payload={"s": "a"})
        job2 = enqueue_ai_job(action="admin_reply", ticket_id=2, payload={"s": "b"})

        resp = test_client.get("/api/support/v1/ai/queue", headers=_admin_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        ids = [j["job_id"] for j in data["jobs"]]
        assert job1 in ids
        assert job2 in ids

    def test_403_for_non_admin(self, test_client):
        resp = test_client.get("/api/support/v1/ai/queue", headers=_user_headers())
        assert resp.status_code == 403


# ── DELETE /ai/queue/{job_id} ────────────────────────────────────────────

class TestAdminDeleteAiJob:

    def test_delete_existing_job(self, test_client, _temp_queue_dir):
        from services.backend_api.services.support_service import enqueue_ai_job
        job_id = enqueue_ai_job(action="new_ticket", ticket_id=5, payload={})

        resp = test_client.delete(
            f"/api/support/v1/ai/queue/{job_id}",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        # Verify file is gone
        assert not (Path(_temp_queue_dir) / f"{job_id}.json").exists()

    def test_delete_nonexistent_returns_404(self, test_client):
        resp = test_client.delete(
            "/api/support/v1/ai/queue/nonexistent_job",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404

    def test_403_for_non_admin(self, test_client):
        resp = test_client.delete(
            "/api/support/v1/ai/queue/some_job",
            headers=_user_headers(),
        )
        assert resp.status_code == 403


# ── Queue integration with admin reply ───────────────────────────────────

class TestReplyQueuesAiJob:

    def test_admin_reply_creates_queue_job(self, test_client, _temp_queue_dir):
        """Replying to a ticket should write an AI job to the queue."""
        from services.backend_api.db.connection import SessionLocal
        db = SessionLocal()
        try:
            user = _ensure_user(db, "queuetest@careertrojan.com")
            ticket = models.SupportTicket(
                user_id=user.id,
                subject="Queue integration test",
                description="Testing AI queue on reply",
                status="open",
                priority="normal",
                category="bugs",
                portal="user_portal",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(ticket)
            db.commit()
            db.refresh(ticket)
            ticket_id = ticket.id
        finally:
            db.close()

        with patch(
            "services.backend_api.services.support_service.zendesk_client.add_comment",
            new_callable=AsyncMock,
            return_value={"ticket": {"id": 99999}},
        ):
            resp = test_client.post(
                f"/api/support/v1/tickets/{ticket_id}/reply",
                json={"comment": "AI queue test reply", "public": True},
                headers=_admin_headers(),
            )

        assert resp.status_code == 200

        # Check a job file was written
        queue_dir = Path(_temp_queue_dir)
        job_files = list(queue_dir.glob("zendesk_*.json"))
        assert len(job_files) >= 1

        # Verify the job contents
        job_data = json.loads(job_files[0].read_text())
        assert job_data["action"] == "admin_reply"
        assert job_data["ticket_id"] == ticket_id
        assert job_data["payload"]["comment"] == "AI queue test reply"
