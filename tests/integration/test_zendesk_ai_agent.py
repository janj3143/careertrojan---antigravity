"""
test_zendesk_ai_agent.py — Unit tests for the Zendesk AI agent service.

Tests:
  - _parse_ai_metadata extracts CONFIDENCE / TAGS / PRIORITY
  - _build_prompt includes all context sections (including requester profile)
  - process_ticket generates a draft with mocked LLM + Zendesk client
  - Auto-reply posts internal note when enabled
  - Graceful degradation when LLM / KB / comments fail
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

# All async tests use anyio backend
pytestmark = pytest.mark.anyio


# ═══════════════════════════════════════════════════════════════════════════
# Mock LLM Response
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MockLLMResponse:
    content: str = (
        "Here is my draft reply.\n\nCONFIDENCE: 0.85\nTAGS: billing, refund\nPRIORITY: high"
    )
    model: str = "gpt-4o"
    provider: str = "openai"
    input_tokens: int = 500
    output_tokens: int = 200
    cost_usd: float = 0.01
    latency_ms: float = 450.0


# ═══════════════════════════════════════════════════════════════════════════
# 1 — _parse_ai_metadata
# ═══════════════════════════════════════════════════════════════════════════

class TestParseAIMetadata:
    """Test extraction of CONFIDENCE/TAGS/PRIORITY from LLM output."""

    def setup_method(self):
        from services.backend_api.services.zendesk_ai.agent_service import ZendeskAIAgent
        self.parse = ZendeskAIAgent._parse_ai_metadata

    def test_parses_confidence(self):
        draft = "Some reply text.\n\nCONFIDENCE: 0.92\nTAGS: test\nPRIORITY: normal"
        tags, priority, confidence = self.parse(draft, [], "normal")
        assert confidence == pytest.approx(0.92, abs=0.01)

    def test_parses_tags(self):
        draft = "Reply.\nCONFIDENCE: 0.5\nTAGS: billing, refund, urgent\nPRIORITY: high"
        tags, priority, confidence = self.parse(draft, ["existing"], "normal")
        assert "billing" in tags
        assert "refund" in tags
        assert "urgent" in tags
        assert "existing" in tags  # existing tags preserved

    def test_parses_priority(self):
        draft = "Reply.\nCONFIDENCE: 0.5\nTAGS: test\nPRIORITY: urgent"
        _, priority, _ = self.parse(draft, [], "normal")
        assert priority == "urgent"

    def test_invalid_priority_kept_as_existing(self):
        draft = "Reply.\nPRIORITY: super_urgent"
        _, priority, _ = self.parse(draft, [], "normal")
        assert priority == "normal"  # unchanged — invalid value

    def test_missing_metadata_uses_defaults(self):
        draft = "Just a plain reply with no metadata lines."
        tags, priority, confidence = self.parse(draft, ["existing"], "normal")
        assert confidence == 0.5  # default
        assert tags == ["existing"]
        assert priority == "normal"

    def test_confidence_clamped_to_0_1(self):
        draft = "Reply.\nCONFIDENCE: 5.0"
        _, _, confidence = self.parse(draft, [], "normal")
        assert confidence == 1.0  # clamped

        draft2 = "Reply.\nCONFIDENCE: -0.5"
        _, _, confidence2 = self.parse(draft2, [], "normal")
        assert confidence2 == 0.0  # clamped

    def test_malformed_confidence_uses_default(self):
        draft = "Reply.\nCONFIDENCE: not_a_number"
        _, _, confidence = self.parse(draft, [], "normal")
        assert confidence == 0.5  # default


# ═══════════════════════════════════════════════════════════════════════════
# 2 — _build_prompt
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildPrompt:
    """Verify the prompt includes all expected context sections."""

    def setup_method(self):
        from services.backend_api.services.zendesk_ai.agent_service import ZendeskAIAgent
        self.agent = ZendeskAIAgent()

    def _default_kwargs(self, **overrides):
        """Base kwargs for _build_prompt — override any key."""
        kw = dict(
            subject="Test",
            description="Desc",
            tags=[],
            status="new",
            priority="normal",
            comments_context="",
            kb_context="",
            requester_context="",
            requester_email=None,
            event_type="ticket.created",
        )
        kw.update(overrides)
        return kw

    def test_includes_subject_and_description(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(
                subject="Login issues",
                description="I can't log into my account.",
            )
        )
        assert "Login issues" in prompt
        assert "I can't log into my account" in prompt

    def test_includes_tags_when_present(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(tags=["billing", "urgent"])
        )
        assert "billing" in prompt
        assert "urgent" in prompt

    def test_includes_requester_email(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(requester_email="john@example.com")
        )
        assert "john@example.com" in prompt

    def test_includes_requester_context(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(
                requester_context="Name: John Smith\nLocale: en-GB\nCustomer since: 2025-06-01",
            )
        )
        assert "John Smith" in prompt
        assert "Customer profile" in prompt
        assert "en-GB" in prompt

    def test_omits_requester_context_when_empty(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(requester_context="")
        )
        assert "Customer profile" not in prompt

    def test_includes_comments_context(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(
                comments_context="Agent said: We're looking into this."
            )
        )
        assert "We're looking into this" in prompt

    def test_includes_kb_context(self):
        prompt = self.agent._build_prompt(
            **self._default_kwargs(
                kb_context="KB Article: How to reset your password\nClick Settings..."
            )
        )
        assert "How to reset your password" in prompt
        assert "knowledge-base articles" in prompt.lower()

    def test_includes_output_instructions(self):
        prompt = self.agent._build_prompt(**self._default_kwargs())
        assert "CONFIDENCE:" in prompt
        assert "TAGS:" in prompt
        assert "PRIORITY:" in prompt
        assert "300 words" in prompt


# ═══════════════════════════════════════════════════════════════════════════
# 3 — process_ticket (mocked end-to-end)
# ═══════════════════════════════════════════════════════════════════════════

class TestProcessTicket:
    """Integration test with mocked LLM and Zendesk client."""

    @pytest.fixture(autouse=True)
    def _setup_agent(self, monkeypatch):
        monkeypatch.setenv("ZENDESK_AI_AGENT_ENABLED", "true")
        monkeypatch.setenv("ZENDESK_AI_AGENT_AUTO_REPLY", "false")
        from services.backend_api.services.zendesk_ai.agent_service import ZendeskAIAgent
        self.agent = ZendeskAIAgent()

    def _mock_zendesk(self):
        mock = AsyncMock()
        mock.is_configured = True
        mock.get_ticket = AsyncMock(return_value={
            "ticket": {
                "id": 42,
                "subject": "Resume help",
                "description": "I need help with my resume.",
                "status": "new",
                "priority": "normal",
                "tags": ["resume"],
                "requester_id": 100,
            }
        })
        mock.get_user = AsyncMock(return_value={
            "id": 100,
            "name": "Jane Doe",
            "email": "jane@example.com",
            "role": "end-user",
            "locale": "en-GB",
            "organization_id": None,
            "tags": ["premium"],
            "created_at": "2025-06-15T10:00:00Z",
        })
        mock.get_ticket_comments = AsyncMock(return_value=[
            {
                "id": 1,
                "body": "Please help me with my resume.",
                "author_id": 100,
                "public": True,
            },
        ])
        mock.search_articles = AsyncMock(return_value=[
            {
                "title": "Resume Writing Guide",
                "snippet": "Top tips for resumes...",
                "html_url": "https://support.careertrojan.com/articles/resume",
            },
        ])
        mock.add_comment = AsyncMock(return_value={"ticket": {"id": 42}})
        return mock

    def _mock_llm(self):
        mock = AsyncMock()
        mock.chat = AsyncMock(return_value=MockLLMResponse())
        return mock

    @pytest.mark.asyncio
    async def test_process_returns_complete_result(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()

        result = await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={
                "id": 42,
                "subject": "Resume help",
                "description": "I need help.",
                "status": "new",
            },
            event_type="ticket.created",
            requester_email="user@example.com",
        )

        assert "draft_reply" in result
        assert result["draft_reply"]  # non-empty
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert "suggested_tags" in result
        assert isinstance(result["suggested_tags"], list)
        assert "suggested_priority" in result
        assert "model_used" in result
        assert result["model_used"] == "gpt-4o"
        assert "latency_ms" in result
        assert result["latency_ms"] > 0
        assert result["auto_posted"] is False
        assert "processed_at" in result
        assert "kb_articles_used" in result

    @pytest.mark.asyncio
    async def test_fetches_full_ticket_when_description_missing(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()

        await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={"id": 42, "subject": "Resume", "status": "new"},
        )

        # Should have fetched full ticket
        self.agent._zendesk.get_ticket.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_skips_full_fetch_when_description_present(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()

        await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={
                "id": 42,
                "subject": "Test",
                "description": "Already here",
                "status": "new",
            },
        )

        # Should NOT have fetched full ticket
        self.agent._zendesk.get_ticket.assert_not_called()

    @pytest.mark.asyncio
    async def test_enriches_requester_profile(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()

        await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={
                "id": 42,
                "subject": "Test",
                "description": "Help",
                "status": "new",
                "requester_id": 100,
            },
        )

        self.agent._zendesk.get_user.assert_called_once_with(100)

    @pytest.mark.asyncio
    async def test_auto_reply_posts_internal_note(self, monkeypatch):
        import services.backend_api.services.zendesk_ai.agent_service as mod
        monkeypatch.setattr(mod, "ZENDESK_AI_AGENT_AUTO_REPLY", True)

        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()

        result = await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={"id": 42, "description": "Help", "status": "new"},
        )

        assert result["auto_posted"] is True
        self.agent._zendesk.add_comment.assert_called_once()
        call_kwargs = self.agent._zendesk.add_comment.call_args
        assert call_kwargs.kwargs.get("public") is False

    @pytest.mark.asyncio
    async def test_graceful_when_comments_fetch_fails(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()
        self.agent._zendesk.get_ticket_comments = AsyncMock(
            side_effect=Exception("Zendesk timeout")
        )

        result = await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={"id": 42, "description": "Test", "status": "new"},
        )
        assert result["draft_reply"]

    @pytest.mark.asyncio
    async def test_graceful_when_kb_search_fails(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()
        self.agent._zendesk.search_articles = AsyncMock(
            side_effect=Exception("KB unavailable")
        )

        result = await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={"id": 42, "description": "Test", "status": "new"},
        )
        assert result["draft_reply"]
        assert result["kb_articles_used"] == []

    @pytest.mark.asyncio
    async def test_graceful_when_requester_fetch_fails(self):
        self.agent._llm = self._mock_llm()
        self.agent._zendesk = self._mock_zendesk()
        self.agent._zendesk.get_user = AsyncMock(
            side_effect=Exception("User not found")
        )

        result = await self.agent.process_ticket(
            ticket_id=42,
            ticket_data={
                "id": 42,
                "description": "Test",
                "status": "new",
                "requester_id": 999,
            },
        )
        # Should still produce a draft
        assert result["draft_reply"]

    @pytest.mark.asyncio
    async def test_llm_failure_raises(self):
        self.agent._llm = self._mock_llm()
        self.agent._llm.chat = AsyncMock(side_effect=RuntimeError("LLM overloaded"))
        self.agent._zendesk = self._mock_zendesk()

        with pytest.raises(RuntimeError, match="LLM overloaded"):
            await self.agent.process_ticket(
                ticket_id=42,
                ticket_data={"id": 42, "description": "Test", "status": "new"},
            )
