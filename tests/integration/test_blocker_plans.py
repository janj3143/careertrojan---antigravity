import pytest
from services.backend_api.db.connection import get_db
from services.backend_api.db.models import ApplicationBlocker
from services.backend_api.utils import security
from services.backend_api.main import app
from fastapi.testclient import TestClient

def test_generate_plans():
    client = TestClient(app)
    
    # get a session from the app directly
    db = next(get_db())
    blocker = ApplicationBlocker(
        blocker_id="test-blocker-123",
        user_id=1,
        blocker_type="SKILL_GAP",
        gap_description="Missing Python skills",
        criticality_score=8,
        status="active"
    )
    db.add(blocker)
    db.commit()
    
    user_token = security.create_access_token(data={"sub": "user@example.com", "role": "user"})
    headers = {"Authorization": f"Bearer {user_token}"}
    
    payload = {"blocker_id": "test-blocker-123", "user_id": 1}
    res = client.post("/api/blockers/v1/improvement-plans/generate", json=payload, headers=headers)
    
    # cleanup
    db.delete(blocker)
    db.commit()
    
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
