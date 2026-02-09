"""
Unit tests for GDPR models and Tier 2 additions.
"""
import pytest
from datetime import datetime


@pytest.mark.unit
class TestGDPRModels:
    """Verify the new GDPR / audit DB models exist with correct columns."""

    def test_consent_record_fields(self):
        from services.backend_api.db.models import ConsentRecord
        cols = {c.name for c in ConsentRecord.__table__.columns}
        assert "user_id" in cols
        assert "consent_type" in cols
        assert "granted" in cols
        assert "ip_address" in cols
        assert "version" in cols
        assert "revoked_at" in cols

    def test_audit_log_fields(self):
        from services.backend_api.db.models import AuditLog
        cols = {c.name for c in AuditLog.__table__.columns}
        assert "user_id" in cols
        assert "actor_id" in cols
        assert "action" in cols
        assert "resource_type" in cols
        assert "ip_address" in cols
        assert "created_at" in cols

    def test_data_export_request_fields(self):
        from services.backend_api.db.models import DataExportRequest
        cols = {c.name for c in DataExportRequest.__table__.columns}
        assert "user_id" in cols
        assert "status" in cols
        assert "file_path" in cols
        assert "requested_at" in cols
        assert "completed_at" in cols
        assert "expires_at" in cols

    def test_interaction_model_fields(self):
        from services.backend_api.db.models import Interaction
        cols = {c.name for c in Interaction.__table__.columns}
        assert "user_id" in cols
        assert "action_type" in cols
        assert "method" in cols
        assert "path" in cols
        assert "status_code" in cols
        assert "response_time_ms" in cols
        assert "ip_address" in cols

    def test_all_new_tables_in_metadata(self):
        from services.backend_api.db.models import Base
        table_names = set(Base.metadata.tables.keys())
        assert "consent_records" in table_names
        assert "audit_log" in table_names
        assert "data_export_requests" in table_names
        assert "interactions" in table_names


@pytest.mark.unit
class TestGDPRRouter:
    """Verify GDPR router has the required endpoints."""

    def test_gdpr_router_exists(self):
        from services.backend_api.routers.gdpr import router
        assert router.prefix == "/api/gdpr/v1"
        assert "gdpr" in router.tags

    def test_gdpr_routes_registered(self):
        from services.backend_api.main import app
        paths = [r.path for r in app.routes if hasattr(r, "methods")]
        assert "/api/gdpr/v1/consent" in paths
        assert "/api/gdpr/v1/export" in paths
        assert "/api/gdpr/v1/delete-account" in paths
        assert "/api/gdpr/v1/audit-log" in paths

    def test_route_count_increased(self):
        from services.backend_api.main import app
        routes = [r for r in app.routes if hasattr(r, "methods")]
        # Was 176 pre-Tier 2, should be ≥179 now
        assert len(routes) >= 179


@pytest.mark.unit
class TestAdminAILoopEndpoints:
    """Verify admin AI-loop stubs have been replaced with real implementations."""

    def test_admin_ai_enrichment_not_501(self):
        """The enrichment endpoints should no longer raise 501."""
        from services.backend_api.routers.admin import enrichment_status
        # If it were a stub, calling it without auth would raise 501
        # We just verify the function exists and is NOT the _not_impl pattern
        import inspect
        src = inspect.getsource(enrichment_status)
        assert "_not_impl" not in src

    def test_admin_dashboard_not_501(self):
        from services.backend_api.routers.admin import dashboard_snapshot
        import inspect
        src = inspect.getsource(dashboard_snapshot)
        assert "_not_impl" not in src

    def test_admin_activity_not_501(self):
        from services.backend_api.routers.admin import system_activity
        import inspect
        src = inspect.getsource(system_activity)
        assert "_not_impl" not in src

    def test_admin_compliance_not_501(self):
        from services.backend_api.routers.admin import compliance_summary
        import inspect
        src = inspect.getsource(compliance_summary)
        assert "_not_impl" not in src

    def test_admin_audit_events_not_501(self):
        from services.backend_api.routers.admin import audit_events
        import inspect
        src = inspect.getsource(audit_events)
        assert "_not_impl" not in src
