import pytest

from services.backend_api.services.company_intel_service import CompanyIntelService


@pytest.fixture
def isolated_paths(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    ai_data = data_root / "ai_data_final"
    ai_data.mkdir(parents=True)

    app_root = tmp_path / "app"
    logs_root = tmp_path / "logs"

    monkeypatch.setenv("CAREERTROJAN_DATA_ROOT", str(data_root))
    monkeypatch.setenv("CAREERTROJAN_AI_DATA", str(ai_data))
    monkeypatch.setenv("CAREERTROJAN_APP_ROOT", str(app_root))
    monkeypatch.setenv("CAREERTROJAN_APP_LOGS", str(logs_root))

    return {
        "data_root": data_root,
        "ai_data": ai_data,
        "app_root": app_root,
        "logs_root": logs_root,
    }


def test_company_intel_ingest_and_registry_summary(isolated_paths):
    service = CompanyIntelService()

    text = (
        "Worked at Acme Solutions Ltd and Beta Global Services. "
        "Later collaborated with Acme Solutions Ltd on a migration project."
    )

    result = service.ingest_resume_text(text=text, user_id="u1", source="resume_upload")

    assert result["companies_found"] >= 2
    assert result["companies_added"] >= 2

    summary = service.get_registry_summary()
    assert summary["total_companies"] >= 2
    assert summary["total_seen_events"] >= 2

    rows = service.list_registry(limit=10)
    assert len(rows) >= 2
    assert all("company" in row for row in rows)


def test_company_intel_recent_events_and_analytics(isolated_paths):
    service = CompanyIntelService()

    service.ingest_resume_text(
        text="Experience at Delta Technologies and Omega Group",
        user_id="user-a",
        source="resume_upload",
    )
    service.ingest_resume_text(
        text="Role with Delta Technologies and Nova Solutions",
        user_id="user-b",
        source="manual_extract",
    )

    all_events = service.list_recent_events(limit=20)
    assert len(all_events) == 2

    resume_events = service.list_recent_events(limit=20, source="resume_upload")
    assert len(resume_events) == 1
    assert resume_events[0]["source"] == "resume_upload"

    user_b_events = service.list_recent_events(limit=20, user_id="user-b")
    assert len(user_b_events) == 1
    assert user_b_events[0]["user_id"] == "user-b"

    analytics = service.get_registry_analytics(limit=5, event_limit=20)
    assert "summary" in analytics
    assert "top_companies" in analytics
    assert "source_counts" in analytics
    assert "user_activity" in analytics
    assert "recent_events" in analytics

    assert analytics["summary"]["total_companies"] >= 2
    assert len(analytics["recent_events"]) == 2
