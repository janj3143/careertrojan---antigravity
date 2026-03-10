from fastapi.testclient import TestClient

from services.backend_api.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_profile_coach_system_prompt_route():
    response = client.get("/api/coaching/v1/profile/system-prompt")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["id"] == "profile_coach_v1"
    assert "Profile Coach" in payload["data"]["name"]
    assert "Ask one reflective question at a time" in payload["data"]["system_prompt"]
    assert "generated_at" in payload
    assert "source_summary" in payload


def test_profile_coach_config_route_renders_name():
    response = client.get("/api/coaching/v1/profile/config", params={"user_name": "Jan"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    intro = payload["data"]["config"]["context"]["ui_copy"]["intro"]
    assert "Jan" in intro


def test_profile_coach_reflect_returns_initial_question_on_empty_message():
    response = client.post("/api/coaching/v1/profile/reflect", json={"user_message": ""})
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["mode"] == "question"
    assert isinstance(payload["data"]["question"], str)
    assert len(payload["data"]["question"]) > 0


def test_profile_coach_reflect_continue_mode():
    response = client.post(
        "/api/coaching/v1/profile/reflect",
        json={
            "user_name": "Jan",
            "turn_index": 1,
            "user_message": "I improved our bug workflow and mentored a junior engineer.",
            "transcript": ["Earlier I solved release blockers."]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["mode"] == "continue"
    assert len(payload["data"]["mirror_bullets"]) >= 1
    assert isinstance(payload["data"]["follow_up_question"], str)


def test_profile_coach_reflect_finished_mode():
    response = client.post(
        "/api/coaching/v1/profile/reflect",
        json={
            "user_message": "that's all",
            "transcript": [
                "I built automation that reduced delays.",
                "I am the go-to person for production incidents.",
                "I mentor junior colleagues.",
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["mode"] == "finished"
    assert 4 <= len(payload["data"]["summary_bullets"]) <= 6


def test_profile_cv_upload_step_contract_route():
    response = client.get("/api/coaching/v1/profile/cv-upload-step", params={"user_name": "Jan"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["module"] == "cv_upload"
    assert payload["data"]["step"] == "profile"
    assert payload["data"]["contract_version"] == "1.0"
    assert "Jan" in payload["data"]["ui"]["intro"]
    assert payload["data"]["endpoints"]["lockstep"] == "/api/coaching/v1/profile/bridge-lockstep"


def test_profile_bridge_lockstep_reports_missing_fields_when_not_ready():
    response = client.post(
        "/api/coaching/v1/profile/bridge-lockstep",
        json={
            "user_id": "user-1",
            "source_portal": "user",
            "profile_state": {
                "profile_headline": "",
                "differentiators": [],
                "impact_examples": [],
            },
            "transcript": ["I led a workflow cleanup"],
            "last_user_message": "still thinking",
            "turn_index": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["lockstep"]["is_ready"] is False
    assert "profile_headline" in payload["data"]["lockstep"]["missing_fields"]
    assert "keep_reflecting" in payload["data"]["lockstep"]["next_actions"]


def test_profile_bridge_lockstep_ready_payload():
    response = client.post(
        "/api/coaching/v1/profile/bridge-lockstep",
        json={
            "user_id": "user-2",
            "user_name": "Jan",
            "session_id": "session-abc",
            "cv_upload_id": "cv-123",
            "source_portal": "user",
            "profile_state": {
                "profile_headline": "Operations leader focused on resilient delivery.",
                "differentiators": ["Turned around failing release process"],
                "impact_examples": ["Reduced incident recovery time by 30%"],
                "strengths": ["Systems thinking"],
            },
            "transcript": [
                "I reduced release blockers with better runbooks.",
                "I mentor newer engineers during incidents.",
            ],
            "last_user_message": "I think that is enough for now",
            "turn_index": 5,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["data"]["lockstep"]["is_ready"] is True
    assert payload["data"]["lockstep"]["missing_fields"] == []
    assert payload["data"]["bridge_event"]["event_type"] == "profile_coach.step_sync"
    assert payload["data"]["bridge_event"]["module"] == "cv_upload"
    assert payload["data"]["bridge_event"]["step"] == "profile"
