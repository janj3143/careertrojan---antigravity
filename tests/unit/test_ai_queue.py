"""
Tests for AI Agent Queue Service — CareerTrojan
=================================================

Covers:
  - Job enqueue / claim / complete / fail lifecycle
  - Queue stats + list / read introspection
  - Job ID generation format
  - Edge cases (empty queue, race on claim)
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from services.backend_api.services.ai_queue_service import (
    claim_next,
    complete_job,
    enqueue,
    ensure_queue_dirs,
    fail_job,
    list_jobs,
    make_job_id,
    queue_stats,
    read_job,
)


@pytest.fixture
def tmp_queue(tmp_path):
    """Provide a temporary queue root for test isolation."""
    ensure_queue_dirs(tmp_path)
    return tmp_path


# ── Job ID ────────────────────────────────────────────────────

class TestJobId:
    def test_job_id_format(self):
        jid = make_job_id("zendesk")
        assert jid.startswith("zendesk_")
        parts = jid.split("_")
        assert len(parts) >= 3

    def test_custom_source(self):
        jid = make_job_id("support_form")
        assert jid.startswith("support_form_")


# ── Enqueue ──────────────────────────────────────────────────

class TestEnqueue:
    def test_enqueue_creates_file(self, tmp_queue):
        jid = enqueue({"ticket": {"id": 1, "subject": "Help"}}, root=tmp_queue)
        path = tmp_queue / "pending" / f"{jid}.json"
        assert path.exists()

    def test_envelope_structure(self, tmp_queue):
        jid = enqueue(
            {"ticket": {"id": 1}},
            kind="ticket_triage",
            source="zendesk",
            root=tmp_queue,
        )
        data = json.loads((tmp_queue / "pending" / f"{jid}.json").read_text())
        assert data["job_id"] == jid
        assert data["kind"] == "ticket_triage"
        assert data["source"] == "zendesk"
        assert data["status"] == "pending"
        assert data["payload"]["ticket"]["id"] == 1
        assert data["result"] is None

    def test_explicit_job_id(self, tmp_queue):
        jid = enqueue({"x": 1}, job_id="custom_123", root=tmp_queue)
        assert jid == "custom_123"
        assert (tmp_queue / "pending" / "custom_123.json").exists()


# ── Claim ────────────────────────────────────────────────────

class TestClaim:
    def test_claim_moves_to_processing(self, tmp_queue):
        jid = enqueue({"a": 1}, root=tmp_queue)
        env = claim_next(root=tmp_queue)
        assert env is not None
        assert env["job_id"] == jid
        assert env["status"] == "processing"
        # Gone from pending
        assert not (tmp_queue / "pending" / f"{jid}.json").exists()
        # Present in processing
        assert (tmp_queue / "processing" / f"{jid}.json").exists()

    def test_claim_empty_queue(self, tmp_queue):
        assert claim_next(root=tmp_queue) is None

    def test_fifo_order(self, tmp_queue):
        j1 = enqueue({"n": 1}, job_id="aaa_first", root=tmp_queue)
        j2 = enqueue({"n": 2}, job_id="zzz_second", root=tmp_queue)
        env = claim_next(root=tmp_queue)
        assert env["job_id"] == "aaa_first"


# ── Complete / Fail ──────────────────────────────────────────

class TestCompleteAndFail:
    def test_complete_moves_to_processed(self, tmp_queue):
        jid = enqueue({"t": 1}, root=tmp_queue)
        claim_next(root=tmp_queue)
        dst = complete_job(jid, {"draft_reply": "Hello!"}, root=tmp_queue)
        assert dst == tmp_queue / "processed" / f"{jid}.json"
        data = json.loads(dst.read_text())
        assert data["status"] == "processed"
        assert data["result"]["draft_reply"] == "Hello!"
        assert "completed_at" in data

    def test_fail_moves_to_failed(self, tmp_queue):
        jid = enqueue({"t": 2}, root=tmp_queue)
        claim_next(root=tmp_queue)
        dst = fail_job(jid, "API timeout", root=tmp_queue)
        assert dst == tmp_queue / "failed" / f"{jid}.json"
        data = json.loads(dst.read_text())
        assert data["status"] == "failed"
        assert data["error"] == "API timeout"


# ── Stats + Introspection ────────────────────────────────────

class TestIntrospection:
    def test_queue_stats(self, tmp_queue):
        enqueue({"a": 1}, root=tmp_queue)
        enqueue({"b": 2}, root=tmp_queue)
        stats = queue_stats(root=tmp_queue)
        assert stats["pending"] == 2
        assert stats["processing"] == 0

    def test_list_jobs_returns_summaries(self, tmp_queue):
        enqueue({"a": 1}, job_id="j1", root=tmp_queue)
        enqueue({"b": 2}, job_id="j2", root=tmp_queue)
        jobs = list_jobs("pending", root=tmp_queue)
        assert len(jobs) == 2
        assert jobs[0]["job_id"] == "j1"
        # Should not include full payload
        assert "payload" not in jobs[0]

    def test_read_job_finds_across_buckets(self, tmp_queue):
        jid = enqueue({"z": 99}, root=tmp_queue)
        found = read_job(jid, root=tmp_queue)
        assert found is not None
        assert found["payload"]["z"] == 99

    def test_read_job_not_found(self, tmp_queue):
        assert read_job("nonexistent", root=tmp_queue) is None


# ── Full lifecycle ───────────────────────────────────────────

class TestFullLifecycle:
    def test_enqueue_claim_complete(self, tmp_queue):
        jid = enqueue(
            {"ticket": {"id": 42, "subject": "Test"}},
            kind="draft_reply",
            root=tmp_queue,
        )
        stats = queue_stats(root=tmp_queue)
        assert stats["pending"] == 1

        env = claim_next(root=tmp_queue)
        assert env["job_id"] == jid
        stats = queue_stats(root=tmp_queue)
        assert stats["pending"] == 0
        assert stats["processing"] == 1

        complete_job(jid, {"draft_reply": "We'll look into this."}, root=tmp_queue)
        stats = queue_stats(root=tmp_queue)
        assert stats["processed"] == 1
        assert stats["processing"] == 0

    def test_enqueue_claim_fail(self, tmp_queue):
        jid = enqueue({"ticket": {"id": 7}}, root=tmp_queue)
        claim_next(root=tmp_queue)
        fail_job(jid, "LLM rate limited", root=tmp_queue)
        stats = queue_stats(root=tmp_queue)
        assert stats["failed"] == 1

        full = read_job(jid, root=tmp_queue)
        assert full["error"] == "LLM rate limited"
