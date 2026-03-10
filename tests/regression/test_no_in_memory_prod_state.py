from pathlib import Path
import pytest


@pytest.mark.regression
def test_queue_pending_not_written_by_read_only_health_flow(test_client):
    pending_dir = Path("queue/pending")
    before = {p.name for p in pending_dir.glob("*.json")} if pending_dir.exists() else set()

    response = test_client.get("/api/shared/v1/health")
    assert response.status_code == 200

    after = {p.name for p in pending_dir.glob("*.json")} if pending_dir.exists() else set()
    assert after == before


@pytest.mark.regression
@pytest.mark.xfail(reason="Known debt: runtime still contains in-memory fallback code paths pending hard-removal phase")
def test_no_in_memory_fallback_markers_in_runtime_codebase():
    root = Path("services/backend_api")
    markers = ("in_memory", "fallback", "mock")
    hits = []

    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(marker in text for marker in markers):
            hits.append(str(path))

    assert not hits
