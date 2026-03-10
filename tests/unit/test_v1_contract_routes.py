from fastapi.testclient import TestClient

from services.backend_api.main import app


client = TestClient(app, raise_server_exceptions=False)


def _assert_envelope(payload: dict):
    assert "status" in payload
    assert "message" in payload
    assert "data" in payload
    assert "source_summary" in payload
    assert "generated_at" in payload
    assert "request_id" in payload["source_summary"]


def test_v1_career_compass_map_missing_resume_contract():
    response = client.get("/api/v1/career-compass/map", params={"user_id": 999999})
    assert response.status_code == 409
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "missing_resume"


def test_v1_career_compass_routes_missing_resume_contract():
    response = client.get("/api/v1/career-compass/routes", params={"user_id": 999999})
    assert response.status_code == 409
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "missing_resume"


def test_v1_career_compass_culdesac_requires_target():
    response = client.post("/api/v1/career-compass/culdesac-check", json={})
    assert response.status_code == 409
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "missing_cluster"


def test_v1_career_compass_save_scenario_ok():
    response = client.post(
        "/api/v1/career-compass/save-scenario",
        json={
            "user_id": 12,
            "resume_id": 34,
            "scenario_key": "next_move",
            "selected_cluster_id": "cluster-2",
            "selected_target_role": "Engineering Manager",
            "notes": "Tracking possible next move",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "ok"
    assert payload["data"]["scenario_id"].startswith("scenario-")


def test_v1_profile_coach_start_respond_finish_flow():
    start = client.post(
        "/api/v1/profile-coach/start",
        json={"user_id": 4, "resume_id": 7, "user_name": "Jan"},
    )
    assert start.status_code == 200
    start_payload = start.json()
    _assert_envelope(start_payload)
    session_id = start_payload["data"]["session_id"]

    respond = client.post(
        "/api/v1/profile-coach/respond",
        json={"user_id": 4, "session_id": session_id, "answer": "I improved release delivery speed."},
    )
    assert respond.status_code == 200
    respond_payload = respond.json()
    _assert_envelope(respond_payload)
    assert respond_payload["status"] == "ok"

    finish = client.post(
        "/api/v1/profile-coach/finish",
        json={"user_id": 4, "session_id": session_id},
    )
    assert finish.status_code == 200
    finish_payload = finish.json()
    _assert_envelope(finish_payload)
    assert finish_payload["status"] == "ok"
    assert len(finish_payload["data"]["differentiators"]) >= 4


def test_v1_profile_build_and_signals_contract():
    build_missing = client.post(
        "/api/v1/profile/build",
        json={"user_id": 9, "resume_id": 13, "differentiators": []},
    )
    assert build_missing.status_code == 409
    missing_payload = build_missing.json()
    _assert_envelope(missing_payload)
    assert missing_payload["status"] == "missing_profile_enrichment"

    build_ok = client.post(
        "/api/v1/profile/build",
        json={
            "user_id": 9,
            "resume_id": 13,
            "differentiators": [
                "Led delivery improvements across two teams",
                "Mentored peers during production issues",
            ],
        },
    )
    assert build_ok.status_code == 200
    build_ok_payload = build_ok.json()
    _assert_envelope(build_ok_payload)
    assert build_ok_payload["status"] == "ok"

    signals_ok = client.post(
        "/api/v1/profile/signals",
        json={
            "user_id": 9,
            "resume_id": 13,
            "differentiators": ["Led architecture planning and stakeholder communication"],
        },
    )
    assert signals_ok.status_code == 200
    signals_payload = signals_ok.json()
    _assert_envelope(signals_payload)
    assert signals_payload["status"] == "ok"
    assert "signals" in signals_payload["data"]


def test_v1_user_vector_current_missing_resume_contract():
    response = client.get("/api/v1/user-vector/current", params={"user_id": 909090})
    assert response.status_code == 409
    payload = response.json()
    _assert_envelope(payload)
    assert payload["status"] == "missing_resume"
