import pytest
from services.backend_api.db import models
from services.backend_api.utils import security

def test_admin_impersonate(test_client):
    admin_token = security.create_access_token(data={"sub": "admin@example.com", "role": "admin"})
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Grab whatever users exist
    res_users = test_client.get("/api/admin/v1/users", headers=headers)
    assert res_users.status_code == 200
    users = res_users.json()
    if not users:
        pytest.skip("No test users in test database to impersonate.")

    target_user = users[0]
    
    res = test_client.post(f"/api/admin/v1/users/{target_user['id']}/impersonate", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["impersonated_user"] == target_user["email"]
    
