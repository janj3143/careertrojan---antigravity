"""
Unit tests for Tier 3 — Observability & Ops.
"""
import pytest


@pytest.mark.unit
class TestStructuredLogging:
    """Verify structlog is properly configured."""

    def test_configure_logging_callable(self):
        from services.backend_api.config.logging_config import configure_logging
        # Should not raise
        configure_logging()

    def test_get_logger_returns_bound_logger(self):
        from services.backend_api.config.logging_config import get_logger
        import structlog
        logger = get_logger("test_module")
        # structlog BoundLogger wraps stdlib logger
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_logger_can_emit(self):
        """Logger should emit without error even with extra kwargs."""
        from services.backend_api.config.logging_config import configure_logging, get_logger
        configure_logging()
        logger = get_logger("test_emit")
        # Should not raise
        logger.info("test_event", user_id=1, action="test")

    def test_structlog_imported_in_main(self):
        """main.py should use configure_logging, not bare logging.basicConfig."""
        import inspect
        from services.backend_api import main
        src = inspect.getsource(main)
        assert "configure_logging" in src
        assert "get_logger" in src


@pytest.mark.unit
class TestRequestCorrelationMiddleware:
    """Verify request correlation middleware exists and is wired."""

    def test_middleware_importable(self):
        from services.backend_api.middleware.request_correlation import RequestCorrelationMiddleware
        assert RequestCorrelationMiddleware is not None

    def test_middleware_wired_in_app(self):
        from services.backend_api.main import app
        middleware_classes = [m.cls.__name__ for m in app.user_middleware if hasattr(m, 'cls')]
        assert "RequestCorrelationMiddleware" in middleware_classes


@pytest.mark.unit
class TestHealthCheckEndpoints:
    """Verify health check endpoints exist."""

    def test_light_health_exists(self):
        from services.backend_api.main import app
        paths = [r.path for r in app.routes if hasattr(r, "methods")]
        assert "/api/shared/v1/health" in paths

    def test_deep_health_exists(self):
        from services.backend_api.main import app
        paths = [r.path for r in app.routes if hasattr(r, "methods")]
        assert "/api/shared/v1/health/deep" in paths

    def test_route_count_still_healthy(self):
        """Route count should be ≥180 after Tier 3 additions."""
        from services.backend_api.main import app
        routes = [r for r in app.routes if hasattr(r, "methods")]
        assert len(routes) >= 180


@pytest.mark.unit
class TestLegacyCleanup:
    """Verify legacy stubs/duplicates were removed and Streamlit demos renamed."""

    def test_stub_harness_removed(self):
        import os
        assert not os.path.exists("services/backend_api/services/qa/test_harness.py")
        assert not os.path.exists("apps/admin/services/qa/test_harness.py")

    def test_duplicate_enrichment_test_removed(self):
        import os
        assert not os.path.exists("apps/admin/services/test_smart_enrichment.py")

    def test_streamlit_demos_renamed(self):
        import os
        # Old names should not exist
        assert not os.path.exists("apps/user/test_advanced_features.py")
        assert not os.path.exists("apps/user/test_resume_upload.py")
        # New names should exist
        assert os.path.exists("apps/user/demo_advanced_features.py")
        assert os.path.exists("apps/user/demo_resume_upload.py")
