"""
Zendesk AI Agent Service
=========================
Uses the LLM Gateway to generate intelligent draft replies for Zendesk
support tickets.  Called by the queue worker for each pending job.

Flow:
    1. Fetch ticket details + recent comments from Zendesk API
    2. Fetch requester profile for personalisation
    3. Search knowledge-base articles for relevant context
    4. Build a context-rich prompt
    5. Call LLM Gateway → generate draft reply
    6. Optionally post as an internal note (or public reply if auto_reply is on)
    7. Return the result payload (draft text, confidence, metadata)

Usage::

    from services.backend_api.services.zendesk_ai.agent_service import zendesk_ai_agent

    result = await zendesk_ai_agent.process_ticket(ticket_id=42, ticket_data={...})
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("careertrojan.zendesk_ai.agent")

# ── Config from env ───────────────────────────────────────────────────────
ZENDESK_AI_AGENT_SYSTEM_PROMPT = os.getenv(
    "ZENDESK_AI_AGENT_SYSTEM_PROMPT",
    (
        "You are CareerTrojan's AI support agent. You help users with "
        "career-related questions, resume analysis, account issues, and "
        "platform usage. Be professional, concise, and empathetic. If the "
        "issue requires a human agent, say so clearly."
    ),
)
ZENDESK_AI_AGENT_MODEL = os.getenv("ZENDESK_AI_AGENT_MODEL", "auto")
ZENDESK_AI_AGENT_AUTO_REPLY = os.getenv(
    "ZENDESK_AI_AGENT_AUTO_REPLY", "false"
).lower() in ("true", "1", "yes")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL", "")


class ZendeskAIAgent:
    """
    AI-powered Zendesk support agent.

    Generates draft replies using the LLM Gateway, enriched with
    knowledge-base context, ticket history, and requester profile.
    """

    def __init__(self) -> None:
        self._llm = None  # lazy-init
        self._zendesk = None  # lazy-init

    # ── Lazy inits ────────────────────────────────────────────────────

    def _get_llm(self):
        if self._llm is None:
            try:
                from services.backend_api.services.llm_service import LLMService
                self._llm = LLMService()
            except Exception as exc:
                logger.error("LLM Gateway not available: %s", exc)
                raise RuntimeError("LLM Gateway is required for AI agent") from exc
        return self._llm

    def _get_zendesk(self):
        if self._zendesk is None:
            from services.backend_api.services.support_service import zendesk_client
            self._zendesk = zendesk_client
        return self._zendesk

    # ── Main entry point ──────────────────────────────────────────────

    async def process_ticket(
        self,
        ticket_id: int,
        ticket_data: Dict[str, Any],
        *,
        event_type: str = "ticket.created",
        requester_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an AI-drafted reply for a support ticket.

        Args:
            ticket_id:        Zendesk ticket ID
            ticket_data:      Ticket payload from webhook or API fetch
            event_type:       The webhook event type
            requester_email:  End-user email (for personalisation)

        Returns:
            {
                "draft_reply": str,
                "confidence": float,       # 0.0 - 1.0
                "suggested_tags": [...],
                "suggested_priority": str,
                "kb_articles_used": [...],
                "model_used": str,
                "latency_ms": float,
                "auto_posted": bool,
            }
        """
        t0 = time.perf_counter()
        zd = self._get_zendesk()

        # 1. Enrich: fetch full ticket if we only have partial data
        subject = ticket_data.get("subject", "")
        description = ticket_data.get("description", "")
        tags = ticket_data.get("tags", [])
        status = ticket_data.get("status", "new")
        priority = ticket_data.get("priority", "normal")
        requester_id = ticket_data.get("requester_id") or (
            ticket_data.get("requester", {}).get("id")
        )

        if not description:
            full_ticket = await zd.get_ticket(ticket_id)
            if full_ticket and "ticket" in full_ticket:
                t = full_ticket["ticket"]
                subject = t.get("subject", subject)
                description = t.get("description", description)
                tags = t.get("tags", tags)
                status = t.get("status", status)
                priority = t.get("priority", priority)
                if not requester_id:
                    requester_id = t.get("requester_id")

        # 1b. Enrich: fetch requester profile for personalisation
        requester_context = ""
        if requester_id:
            try:
                user = await zd.get_user(int(requester_id))
                if user:
                    parts = []
                    if user.get("name"):
                        parts.append(f"Name: {user['name']}")
                    if user.get("email"):
                        requester_email = requester_email or user["email"]
                        parts.append(f"Email: {user['email']}")
                    if user.get("role"):
                        parts.append(f"Zendesk role: {user['role']}")
                    if user.get("locale"):
                        parts.append(f"Locale: {user['locale']}")
                    if user.get("organization_id"):
                        parts.append(f"Org ID: {user['organization_id']}")
                    if user.get("tags"):
                        parts.append(f"User tags: {', '.join(user['tags'])}")
                    created = user.get("created_at", "")
                    if created:
                        parts.append(f"Customer since: {created[:10]}")
                    requester_context = "\n".join(parts)
                    logger.info(
                        "Enriched requester %d for ticket %d: %s",
                        requester_id, ticket_id, user.get("name", "?"),
                    )
            except Exception as exc:
                logger.warning(
                    "Could not fetch requester %s for ticket %d: %s",
                    requester_id, ticket_id, exc,
                )

        # 2. Fetch recent comments for context (up to 10)
        comments_context = ""
        try:
            comments = await zd.get_ticket_comments(ticket_id, sort_order="asc")
            if comments:
                parts = []
                for c in comments[:10]:
                    author = c.get("author_id", "unknown")
                    body = c.get("plain_body") or c.get("body", "")
                    is_public = c.get("public", True)
                    parts.append(
                        f"[{'Public' if is_public else 'Internal'}] Author {author}:\n{body}"
                    )
                comments_context = "\n---\n".join(parts)
        except Exception as exc:
            logger.warning("Could not fetch comments for ticket %d: %s", ticket_id, exc)

        # 3. Search knowledge base for relevant articles
        kb_context = ""
        kb_articles: List[Dict[str, str]] = []
        if subject or description:
            search_query = f"{subject} {description}"[:200]
            try:
                articles = await zd.search_articles(search_query, per_page=3)
                if articles:
                    for art in articles:
                        title = art.get("title", "")
                        snippet = art.get("snippet", "")
                        url = art.get("html_url", "")
                        kb_articles.append({"title": title, "url": url})
                        kb_context += f"KB Article: {title}\n{snippet}\n\n"
            except Exception as exc:
                logger.warning("KB search failed for ticket %d: %s", ticket_id, exc)

        # 4. Build the prompt
        prompt = self._build_prompt(
            subject=subject,
            description=description,
            tags=tags,
            status=status,
            priority=priority,
            comments_context=comments_context,
            kb_context=kb_context,
            requester_context=requester_context,
            requester_email=requester_email,
            event_type=event_type,
        )

        # 5. Call LLM
        llm = self._get_llm()
        response = await llm.chat(
            prompt,
            model=ZENDESK_AI_AGENT_MODEL,
            system=ZENDESK_AI_AGENT_SYSTEM_PROMPT,
            temperature=0.4,  # lower temp for support = more consistent
            max_tokens=1024,
        )

        draft_reply = response.content.strip()
        model_used = response.model
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

        # 6. Extract suggested tags and priority from the draft
        suggested_tags, suggested_priority, confidence = self._parse_ai_metadata(
            draft_reply, tags, priority
        )

        # 7. Optionally auto-post as internal note
        auto_posted = False
        if ZENDESK_AI_AGENT_AUTO_REPLY and draft_reply:
            try:
                result = await zd.add_comment(
                    ticket_id,
                    comment=f"\U0001f916 **AI Agent Draft:**\n\n{draft_reply}",
                    public=False,  # internal note — agents review before sending
                )
                auto_posted = "error" not in result
                if auto_posted:
                    logger.info(
                        "AI draft auto-posted as internal note on ticket %d", ticket_id
                    )
            except Exception as exc:
                logger.warning("Auto-post failed for ticket %d: %s", ticket_id, exc)

        result = {
            "draft_reply": draft_reply,
            "confidence": confidence,
            "suggested_tags": suggested_tags,
            "suggested_priority": suggested_priority,
            "kb_articles_used": kb_articles,
            "model_used": model_used,
            "latency_ms": latency_ms,
            "auto_posted": auto_posted,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "AI agent processed ticket %d in %.0fms (model=%s, confidence=%.2f, auto_posted=%s)",
            ticket_id,
            latency_ms,
            model_used,
            confidence,
            auto_posted,
        )
        return result

    # ── Prompt builder ────────────────────────────────────────────────

    def _build_prompt(
        self,
        *,
        subject: str,
        description: str,
        tags: List[str],
        status: str,
        priority: str,
        comments_context: str,
        kb_context: str,
        requester_context: str,
        requester_email: Optional[str],
        event_type: str,
    ) -> str:
        """Assemble the full prompt for the LLM."""
        parts = [
            "You are reviewing a Zendesk support ticket. Generate a helpful, professional "
            "draft reply that an agent can review and send to the customer.\n",
            f"**Event:** {event_type}",
            f"**Subject:** {subject}",
            f"**Status:** {status}  |  **Priority:** {priority}",
        ]
        if tags:
            parts.append(f"**Tags:** {', '.join(tags)}")
        if requester_email:
            parts.append(f"**Requester:** {requester_email}")

        if requester_context:
            parts.append(f"\n**Customer profile:**\n{requester_context}")

        parts.append(f"\n**Description:**\n{description}\n")

        if comments_context:
            parts.append(f"**Recent conversation:**\n{comments_context}\n")

        if kb_context:
            parts.append(
                "**Relevant knowledge-base articles** (reference these if applicable):\n"
                f"{kb_context}"
            )

        parts.append(
            "\n**Instructions:**\n"
            "1. Draft a clear, empathetic reply addressing the user's issue.\n"
            "2. Reference relevant KB articles if they help.\n"
            "3. If the issue needs human expertise (billing disputes, security, "
            "account deletion), say: 'I'm escalating this to a specialist agent.'\n"
            "4. Keep the reply under 300 words.\n"
            "5. At the end, on a new line, output: CONFIDENCE: <0.0-1.0> based on "
            "how certain you are the reply fully addresses the issue.\n"
            "6. On another new line, output: TAGS: <comma-separated suggested tags>\n"
            "7. On another new line, output: PRIORITY: <low|normal|high|urgent>\n"
        )

        return "\n".join(parts)

    # ── Parse AI metadata from response ───────────────────────────────

    @staticmethod
    def _parse_ai_metadata(
        draft: str,
        existing_tags: List[str],
        existing_priority: str,
    ) -> tuple:
        """
        Extract structured metadata from the LLM output.

        Returns (suggested_tags, suggested_priority, confidence).
        """
        confidence = 0.5  # default
        suggested_tags = list(existing_tags)
        suggested_priority = existing_priority

        lines = draft.strip().split("\n")
        for line in reversed(lines):
            line_lower = line.strip().lower()
            if line_lower.startswith("confidence:"):
                try:
                    val = float(line_lower.split(":", 1)[1].strip())
                    confidence = max(0.0, min(1.0, val))
                except (ValueError, IndexError):
                    pass
            elif line_lower.startswith("tags:"):
                raw = line.strip().split(":", 1)[1].strip()
                new_tags = [t.strip() for t in raw.split(",") if t.strip()]
                if new_tags:
                    suggested_tags = list(set(existing_tags + new_tags))
            elif line_lower.startswith("priority:"):
                raw = line_lower.split(":", 1)[1].strip()
                if raw in ("low", "normal", "high", "urgent"):
                    suggested_priority = raw

        return (suggested_tags, suggested_priority, confidence)


# Module-level singleton
zendesk_ai_agent = ZendeskAIAgent()
