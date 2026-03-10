"""Quick diagnostic: what error do the webhook handlers throw under test?"""
import json, traceback, os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from services.backend_api.db.models import Base
from services.backend_api.main import app
from services.backend_api.db.connection import get_db
from starlette.testclient import TestClient

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

# Verify tables exist
insp = inspect(engine)
print("Tables in test DB:", [t for t in insp.get_table_names() if t in ("webhook_events", "subscriptions", "users")])

TestSession = sessionmaker(bind=engine)

def override_get_db():
    print(">>> OVERRIDE get_db CALLED <<<")
    s = TestSession()
    try:
        yield s
    finally:
        s.close()

app.dependency_overrides[get_db] = override_get_db
# Also check if get_db used in route is same object
from services.backend_api.routers.webhooks import get_db as wh_get_db
print(f"get_db from connection: {id(get_db)}")
print(f"get_db used in webhooks route... checking route deps")
for route in app.routes:
    p = getattr(route, "path", "")
    if p == "/api/webhooks/v1/braintree":
        deps = getattr(route, "dependant", None)
        if deps:
            for d in getattr(deps, "dependencies", []):
                print(f"  Dependency: {d.call} id={id(d.call)}")
print(f"Active overrides: {len(app.dependency_overrides)}")

# ── Test: Braintree valid event ──
print("=" * 60)
print("TEST: Braintree subscription_charged_successfully")
print("=" * 60)
with patch("services.backend_api.routers.webhooks.braintree_service") as mock_bt, \
     patch("services.backend_api.routers.webhooks.BRAINTREE_AVAILABLE", True):
    mock_notification = MagicMock()
    mock_notification.kind = "subscription_charged_successfully"
    mock_notification.timestamp = datetime.now(timezone.utc)
    mock_notification.subscription = MagicMock()
    mock_notification.subscription.id = "sub_test_123"
    mock_notification.subscription.status = "Active"
    mock_notification.subscription.price = "15.99"
    mock_notification.subscription.plan_id = "monthly"
    mock_notification.subscription.transactions = []
    mock_gw = MagicMock()
    mock_gw.webhook_notification.parse.return_value = mock_notification
    mock_bt.gateway.return_value = mock_gw
    mock_bt.is_configured.return_value = True

    client = TestClient(app, raise_server_exceptions=False)
    res = client.post("/api/webhooks/v1/braintree", data={"bt_signature": "v", "bt_payload": "v"})
    print(f"Status: {res.status_code}")
    if res.status_code != 200:
        print(f"Body: {res.text[:500]}")

app.dependency_overrides.pop(get_db, None)
