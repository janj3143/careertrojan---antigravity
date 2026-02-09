"""
Unit tests — Insights, touchpoints, mapping endpoint logic.
"""

import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("CAREERTROJAN_DB_URL", "sqlite:///./test_careertrojan.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


@pytest.mark.unit
class TestInsightsVisuals:

    def test_visuals_catalogue_returns_list(self):
        from services.backend_api.routers.insights import get_visual_catalogue
        result = get_visual_catalogue()
        assert "visuals" in result
        assert isinstance(result["visuals"], list)
        assert len(result["visuals"]) >= 4

    def test_visuals_catalogue_has_required_fields(self):
        from services.backend_api.routers.insights import get_visual_catalogue
        for v in get_visual_catalogue()["visuals"]:
            assert "id" in v
            assert "title" in v
            assert "react_component" in v

    def test_skills_radar_returns_axes(self):
        from services.backend_api.routers.insights import get_skills_radar
        result = get_skills_radar(loader=None, profile_id=None)
        assert "axes" in result
        assert "series" in result
        assert len(result["axes"]) >= 5


@pytest.mark.unit
class TestTouchpoints:

    def test_evidence_empty_ids_returns_empty(self):
        import asyncio
        from services.backend_api.routers.touchpoints import get_evidence
        result = asyncio.get_event_loop().run_until_complete(get_evidence(touchpoint_id=[], loader=None))
        assert result == {"items": []}

    def test_touchnots_empty_ids_returns_empty(self):
        import asyncio
        from services.backend_api.routers.touchpoints import get_touchnots
        result = asyncio.get_event_loop().run_until_complete(get_touchnots(touchpoint_id=[], loader=None))
        assert result == {"items": []}

    def test_evidence_with_unknown_ids(self):
        import asyncio
        from services.backend_api.routers.touchpoints import get_evidence
        result = asyncio.get_event_loop().run_until_complete(
            get_evidence(touchpoint_id=["fake_1", "fake_2"], loader=None)
        )
        assert result["count"] == 2
        # Unknown IDs should still return stub items
        for item in result["items"]:
            assert item["confidence"] == 0.0


@pytest.mark.unit
class TestMapping:

    def test_visual_registry_loads(self):
        from services.backend_api.routers.mapping import load_registry
        visuals = load_registry()
        assert isinstance(visuals, list)
        assert len(visuals) >= 4
