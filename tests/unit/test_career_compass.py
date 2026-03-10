"""
Career Compass + Profile Coach Tests — CareerTrojan
=====================================================

Tests cover:
  1. Career Compass Schemas — all Pydantic models validate correctly
  2. Profile Coach Service — start/respond/finish flow, stop detection
  3. Signal Extraction Service — axis signal extraction from differentiators
  4. User Vector Service — vector generation and storage
  5. Profile Builder Service — differentiator-to-profile text
  6. Career Compass Engine — map, cluster, spider, routes, culdesac, runway, mentors, market
  7. Help Router — page help registry

Author: CareerTrojan System
Date: March 2026
"""
import pytest
from unittest.mock import patch

# ── Schemas ──────────────────────────────────────────────────────
from services.backend_api.models.career_compass_schemas import (
    StandardResponse,
    SourceSummary,
    ProfileCoachStartRequest,
    ProfileCoachResponseRequest,
    ProfileCoachFinishRequest,
    ProfileCoachTurnResponse,
    ProfileCoachFinishResponse,
    BuildProfileRequest,
    BuildProfileResponse,
    UserVectorResponse,
    CareerMapNode,
    CareerMapResponse,
    ClusterProfileResponse,
    SpiderOverlayRequest,
    SpiderOverlayResponse,
    CareerRoutesResponse,
    CulDeSacCheckRequest,
    CulDeSacCheckResponse,
    SaveScenarioRequest,
    SaveScenarioResponse,
    CareerRunwayRequest,
    CareerRunwayStep,
    CareerRunwayResponse,
    CareerMentorMatchRequest,
    CareerMentorMatchResponse,
    CareerMentor,
    MarketSignalRequest,
    MarketSignalResponse,
    MentorSearchRequest,
    MentorSearchResponse,
    SignalExtractionRequest,
    SignalExtractionResponse,
)

# ── Services ─────────────────────────────────────────────────────
from services.backend_api.services.career.profile_coach_service import ProfileCoachService
from services.backend_api.services.career.signal_extraction_service import SignalExtractionService
from services.backend_api.services.career.user_vector_service import UserVectorService
from services.backend_api.services.career.profile_builder_service import ProfileBuilderService
from services.backend_api.services.career.career_compass_engine import CareerCompassEngine


# =====================================================================
# SECTION 1 — Schema Validation Tests
# =====================================================================

class TestSchemas:
    """Verify all Pydantic schemas accept valid data and reject invalid."""

    def test_standard_response_ok(self):
        r = StandardResponse(status="ok", message="Success")
        assert r.status == "ok"

    def test_standard_response_missing_data(self):
        r = StandardResponse(status="missing_resume")
        assert r.status == "missing_resume"
        assert r.data is None

    def test_source_summary(self):
        s = SourceSummary(resume_id="r1", cluster_record_count=10)
        assert s.resume_id == "r1"
        assert s.cluster_record_count == 10

    def test_profile_coach_start_request(self):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1", user_name="Alice")
        assert req.user_name == "Alice"

    def test_profile_coach_start_request_no_name(self):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1")
        assert req.user_name is None

    def test_profile_coach_turn_response(self):
        resp = ProfileCoachTurnResponse(
            status="ok", session_id="s1", question="What?", mirrored_points=["point1"],
        )
        assert resp.stop_detected is False

    def test_profile_coach_finish_response(self):
        resp = ProfileCoachFinishResponse(status="ok", session_id="s1", differentiators=["a", "b"])
        assert len(resp.differentiators) == 2

    def test_career_map_node(self):
        n = CareerMapNode(cluster_id="c1", label="Ops", x=0.5, y=0.3)
        assert n.cluster_id == "c1"

    def test_career_map_response(self):
        r = CareerMapResponse(status="ok", nodes=[])
        assert r.nodes == []

    def test_spider_overlay_request(self):
        req = SpiderOverlayRequest(user_id="u1", resume_id="r1", cluster_id="c1")
        assert req.cluster_id == "c1"

    def test_spider_overlay_response(self):
        r = SpiderOverlayResponse(status="ok", strengths=["Leadership"], gaps=["Innovation"])
        assert len(r.strengths) == 1

    def test_career_routes_response(self):
        r = CareerRoutesResponse(
            status="ok",
            natural_next_steps=["c1"],
            strategic_stretch=["c2"],
            too_far_for_now=["c3"],
        )
        assert len(r.natural_next_steps) == 1

    def test_culdesac_check(self):
        req = CulDeSacCheckRequest(cluster_id="c1")
        resp = CulDeSacCheckResponse(status="ok", risk_level="high_mobility", reasons=["diverse outflows"])
        assert req.cluster_id == "c1"
        assert resp.risk_level == "high_mobility"

    def test_runway_step(self):
        step = CareerRunwayStep(step_number=1, title="Upskill", detail="Take course X")
        assert step.step_number == 1

    def test_runway_response(self):
        r = CareerRunwayResponse(status="ok", steps=[
            CareerRunwayStep(step_number=1, title="Go", detail="Do it"),
        ])
        assert len(r.steps) == 1

    def test_mentor_match(self):
        m = CareerMentor(mentor_id="m1", name="Bob", match_reason="Strong leadership")
        assert m.mentor_id == "m1"

    def test_market_signal_request(self):
        req = MarketSignalRequest(user_id="u1", cluster_id="c1")
        assert req.region is None

    def test_market_signal_response(self):
        r = MarketSignalResponse(status="ok", metrics={"demand": 0.8}, recurring_skills=["Python"])
        assert r.metrics["demand"] == 0.8

    def test_build_profile_request(self):
        req = BuildProfileRequest(user_id="u1", resume_id="r1", differentiators=["a", "b"])
        assert len(req.differentiators) == 2

    def test_signal_extraction_request(self):
        req = SignalExtractionRequest(user_id="u1", resume_id="r1", differentiators=["led teams"])
        assert len(req.differentiators) == 1


# =====================================================================
# SECTION 2 — Profile Coach Service Tests
# =====================================================================

class TestProfileCoachService:
    """Start/respond/finish flow, stop detection, mirror-then-deepen."""

    @pytest.fixture
    def svc(self):
        return ProfileCoachService()

    @pytest.mark.asyncio
    async def test_start_returns_session_and_question(self, svc):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1", user_name="Alice")
        result = await svc.start(req)
        assert result["status"] == "ok"
        assert "session_id" in result
        assert result["question"] is not None
        assert result["stop_detected"] is False

    @pytest.mark.asyncio
    async def test_respond_returns_follow_up(self, svc):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1")
        start = await svc.start(req)
        sid = start["session_id"]

        resp_req = ProfileCoachResponseRequest(user_id="u1", session_id=sid, answer="I managed a team of 5 and improved delivery speed by 30%.")
        result = await svc.respond(resp_req)
        assert result["status"] == "ok"
        assert result["question"] is not None
        assert result["stop_detected"] is False

    @pytest.mark.asyncio
    async def test_stop_phrase_detected(self, svc):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1")
        start = await svc.start(req)
        sid = start["session_id"]

        resp_req = ProfileCoachResponseRequest(user_id="u1", session_id=sid, answer="that's all for now, enough for now")
        result = await svc.respond(resp_req)
        assert result["stop_detected"] is True

    @pytest.mark.asyncio
    async def test_finish_returns_differentiators(self, svc):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1")
        start = await svc.start(req)
        sid = start["session_id"]

        # Provide some answers first
        for answer in [
            "Led digital transformation saving £2M annually in operational costs.",
            "Built mentoring programme that improved retention by 40% across the department.",
            "Known for simplifying complex regulatory requirements into actionable plans.",
        ]:
            await svc.respond(ProfileCoachResponseRequest(user_id="u1", session_id=sid, answer=answer))

        fin = await svc.finish(ProfileCoachFinishRequest(user_id="u1", session_id=sid))
        assert fin["status"] == "ok"
        assert len(fin["differentiators"]) >= 1

    @pytest.mark.asyncio
    async def test_finish_idempotent(self, svc):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1")
        start = await svc.start(req)
        sid = start["session_id"]

        await svc.respond(ProfileCoachResponseRequest(user_id="u1", session_id=sid, answer="I did amazing things."))

        fin1 = await svc.finish(ProfileCoachFinishRequest(user_id="u1", session_id=sid))
        fin2 = await svc.finish(ProfileCoachFinishRequest(user_id="u1", session_id=sid))
        assert fin1["differentiators"] == fin2["differentiators"]

    @pytest.mark.asyncio
    async def test_respond_invalid_session(self, svc):
        result = await svc.respond(ProfileCoachResponseRequest(user_id="u1", session_id="invalid", answer="hello"))
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_finish_invalid_session(self, svc):
        result = await svc.finish(ProfileCoachFinishRequest(user_id="u1", session_id="invalid"))
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_personalised_question(self, svc):
        req = ProfileCoachStartRequest(user_id="u1", resume_id="r1", user_name="Bob")
        result = await svc.start(req)
        assert "Bob" in result["question"]


# =====================================================================
# SECTION 3 — Signal Extraction Service Tests
# =====================================================================

class TestSignalExtractionService:
    """Keyword → 10-axis signal mapping."""

    @pytest.fixture
    def svc(self):
        return SignalExtractionService()

    @pytest.mark.asyncio
    async def test_extract_leadership_signal(self, svc):
        req = SignalExtractionRequest(user_id="u1", resume_id="r1", differentiators=["Led cross-functional team"])
        result = await svc.extract(req)
        assert result["status"] == "ok"
        assert "leadership" in result["signals"]
        assert result["signals"]["leadership"] > 0

    @pytest.mark.asyncio
    async def test_extract_empty_differentiators(self, svc):
        req = SignalExtractionRequest(user_id="u1", resume_id="r1", differentiators=[])
        result = await svc.extract(req)
        assert result["status"] == "missing_profile_enrichment"
        assert result["signals"] == {}

    @pytest.mark.asyncio
    async def test_extract_multiple_axes(self, svc):
        req = SignalExtractionRequest(
            user_id="u1", resume_id="r1",
            differentiators=["Led teams and innovated new products", "Strategic planning and stakeholder management"],
        )
        result = await svc.extract(req)
        signals = result["signals"]
        # Should have multiple axes hit
        assert len(signals) >= 2


# =====================================================================
# SECTION 4 — User Vector Service Tests
# =====================================================================

class TestUserVectorService:
    """Vector generation and retrieval."""

    @pytest.fixture
    def svc(self):
        return UserVectorService()

    @pytest.mark.asyncio
    async def test_get_vector_missing(self, svc):
        result = await svc.get_current_vector(user_id="nonexistent", resume_id="r1")
        assert result["status"] == "missing_resume"
        assert result["vector"] is None

    @pytest.mark.asyncio
    async def test_update_and_get_vector(self, svc):
        signals = {"leadership": 0.8, "innovation": 0.6}
        await svc.update_vector(user_id="u1", resume_id="r1", signals=signals)
        result = await svc.get_current_vector(user_id="u1", resume_id="r1")
        assert result["status"] == "ok"
        assert result["vector"]["leadership"] == 0.8
        assert result["vector_version"] is not None


# =====================================================================
# SECTION 5 — Profile Builder Service Tests
# =====================================================================

class TestProfileBuilderService:
    """Differentiator → profile text transformation."""

    @pytest.fixture
    def svc(self):
        return ProfileBuilderService()

    @pytest.mark.asyncio
    async def test_build_profile(self, svc):
        req = BuildProfileRequest(
            user_id="u1", resume_id="r1",
            differentiators=["Led teams through change", "Known for simplifying complexity"],
        )
        result = await svc.build_profile(req)
        assert result["status"] == "ok"
        assert result["profile_text"] is not None
        assert len(result["profile_text"]) > 0

    @pytest.mark.asyncio
    async def test_build_profile_empty(self, svc):
        req = BuildProfileRequest(user_id="u1", resume_id="r1", differentiators=[])
        result = await svc.build_profile(req)
        assert result["status"] == "missing_profile_enrichment"


# =====================================================================
# SECTION 6 — Career Compass Engine Tests
# =====================================================================

class TestCareerCompassEngine:
    """Core intelligence operations — map, cluster, spider, routes, etc."""

    @pytest.fixture
    def engine(self):
        return CareerCompassEngine()

    @pytest.mark.asyncio
    async def test_get_map_empty_registry(self, engine):
        result = await engine.get_map(user_id="u1")
        assert result["status"] == "missing_cluster"
        assert result["nodes"] == []

    @pytest.mark.asyncio
    async def test_get_map_with_clusters(self, engine):
        from services.backend_api.services.career.career_compass_engine import register_cluster
        register_cluster("c1", {"label": "Operations", "x": 0.5, "y": 0.3, "route_type": "natural_next_step"})
        register_cluster("c2", {"label": "Strategy", "x": 0.8, "y": 0.7, "route_type": "strategic_stretch"})

        result = await engine.get_map()
        assert result["status"] == "ok"
        assert len(result["nodes"]) >= 2

    @pytest.mark.asyncio
    async def test_get_cluster_profile_missing(self, engine):
        result = await engine.get_cluster_profile("nonexistent")
        assert result["status"] == "missing_cluster"

    @pytest.mark.asyncio
    async def test_get_cluster_profile_exists(self, engine):
        from services.backend_api.services.career.career_compass_engine import register_cluster
        register_cluster("c_test", {"label": "Test Cluster", "vector": {"Leadership": 0.7}})
        result = await engine.get_cluster_profile("c_test")
        assert result["status"] == "ok"
        assert result["title"] == "Test Cluster"

    @pytest.mark.asyncio
    async def test_spider_overlay_missing_cluster(self, engine):
        req = SpiderOverlayRequest(user_id="u1", resume_id="r1", cluster_id="nope")
        result = await engine.get_spider_overlay(req)
        # Will return missing_resume or missing_cluster depending on vector store state
        assert result["status"] in ("missing_resume", "missing_cluster")

    @pytest.mark.asyncio
    async def test_routes_empty(self, engine):
        result = await engine.get_routes()
        assert result["status"] in ("ok", "missing_cluster")

    @pytest.mark.asyncio
    async def test_culdesac_check_missing(self, engine):
        req = CulDeSacCheckRequest(cluster_id="nope")
        result = await engine.check_culdesac(req)
        assert result["status"] == "missing_cluster"

    @pytest.mark.asyncio
    async def test_runway_missing_cluster(self, engine):
        req = SpiderOverlayRequest(user_id="u1", resume_id="r1", cluster_id="nope")
        result = await engine.get_runway(req)
        # Will return missing_resume or missing_cluster
        assert result["status"] in ("missing_resume", "missing_cluster")

    @pytest.mark.asyncio
    async def test_mentor_matches_missing(self, engine):
        req = CareerMentorMatchRequest(user_id="u1", resume_id="r1", cluster_id="nope")
        result = await engine.get_mentor_matches(req)
        # Will return missing_resume or missing_cluster
        assert result["status"] in ("missing_resume", "missing_cluster")

    @pytest.mark.asyncio
    async def test_market_signal_missing(self, engine):
        req = MarketSignalRequest(user_id="u1", cluster_id="nope")
        result = await engine.get_market_signal(req)
        assert result["status"] == "missing_market_data"

    @pytest.mark.asyncio
    async def test_save_scenario(self, engine):
        from services.backend_api.models.career_compass_schemas import SaveScenarioRequest
        req = SaveScenarioRequest(user_id="u1", resume_id="r1", cluster_id="c1")
        result = await engine.save_scenario(req)
        assert result["status"] == "ok"
        assert result["scenario_id"] is not None


# =====================================================================
# SECTION 7 — Help Router Tests
# =====================================================================

class TestHelpRouter:
    """Page help registry completeness and access."""

    def test_help_registry_has_all_user_pages(self):
        from services.backend_api.routers.help import PAGE_HELP
        user_slugs = [k for k, v in PAGE_HELP.items() if v["portal"] == "user"]
        assert len(user_slugs) >= 18, f"Expected ≥18 user pages, got {len(user_slugs)}"

    def test_help_registry_has_all_admin_pages(self):
        from services.backend_api.routers.help import PAGE_HELP
        admin_slugs = [k for k, v in PAGE_HELP.items() if v["portal"] == "admin"]
        assert len(admin_slugs) >= 30, f"Expected ≥30 admin pages, got {len(admin_slugs)}"

    def test_help_registry_has_admin_tools(self):
        from services.backend_api.routers.help import PAGE_HELP
        tools_slugs = [k for k, v in PAGE_HELP.items() if v["portal"] == "admin-tools"]
        assert len(tools_slugs) >= 29, f"Expected ≥29 tool pages, got {len(tools_slugs)}"

    def test_help_registry_has_admin_ops(self):
        from services.backend_api.routers.help import PAGE_HELP
        ops_slugs = [k for k, v in PAGE_HELP.items() if v["portal"] == "admin-ops"]
        assert len(ops_slugs) >= 10, f"Expected ≥10 ops pages, got {len(ops_slugs)}"

    def test_help_registry_has_all_mentor_pages(self):
        from services.backend_api.routers.help import PAGE_HELP
        mentor_slugs = [k for k, v in PAGE_HELP.items() if v["portal"] == "mentor"]
        assert len(mentor_slugs) >= 12, f"Expected ≥12 mentor pages, got {len(mentor_slugs)}"

    def test_every_entry_has_description(self):
        from services.backend_api.routers.help import PAGE_HELP
        for slug, entry in PAGE_HELP.items():
            assert "description" in entry, f"Missing description for {slug}"
            assert len(entry["description"]) > 10, f"Description too short for {slug}"

    def test_compass_help_text(self):
        from services.backend_api.routers.help import PAGE_HELP
        compass = PAGE_HELP.get("compass")
        assert compass is not None
        assert "spider" in compass["description"].lower() or "career" in compass["description"].lower()


# =====================================================================
# SECTION 8 — Profile Coach Router Config Tests
# =====================================================================

class TestProfileCoachConfig:
    """Verify config and prompt match spec §11/§12."""

    def test_config_structure(self):
        from services.backend_api.routers.profile_coach import PROFILE_COACH_CONFIG
        cfg = PROFILE_COACH_CONFIG
        assert cfg["id"] == "profile_coach_v1"
        assert cfg["context"]["module"] == "cv_upload"
        assert cfg["context"]["step"] == "profile"
        assert len(cfg["initial_questions"]) == 3
        assert cfg["interaction_rules"]["ask_one_question_at_a_time"] is True
        assert cfg["interaction_rules"]["max_turns_default"] == 8
        assert cfg["interaction_rules"]["follow_up_style"] == "mirror_then_deepen"
        assert cfg["output_format"]["bullet_point_count"]["min"] == 4
        assert cfg["output_format"]["bullet_point_count"]["max"] == 6

    def test_system_prompt_content(self):
        from services.backend_api.routers.profile_coach import PROFILE_COACH_SYSTEM_PROMPT
        prompt = PROFILE_COACH_SYSTEM_PROMPT
        assert "Profile Coach" in prompt
        assert "differentiator" in prompt.lower() or "differentiators" in prompt.lower()
        assert "mirror" in prompt.lower()
        assert "4–6" in prompt or "4-6" in prompt

    def test_stop_phrases(self):
        from services.backend_api.routers.profile_coach import PROFILE_COACH_CONFIG
        stops = PROFILE_COACH_CONFIG["interaction_rules"]["stop_phrases"]
        assert "that's all" in stops
        assert "i'm done" in stops
        assert "enough for now" in stops
