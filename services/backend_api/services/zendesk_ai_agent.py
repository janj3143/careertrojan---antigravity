"""
CareerTrojan — Zendesk AI Agent Worker
=======================================
Polls the AI job queue for pending Zendesk jobs and runs LLM-powered
triage / draft-reply / summarisation.

Usage (standalone)::

    python -m services.backend_api.services.zendesk_ai_agent

Or import and call ``process_one()`` / ``run_loop()`` from a supervisor.

Supported job kinds
-------------------
- ``ticket_triage``     — classify priority + category
- ``draft_reply``       — generate an admin-approved reply draft
- ``summarise_thread``  — produce a concise conversation summary
- ``escalation_check``  — flag whether a ticket needs human escalation
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from services.backend_api.services.ai_queue_service import (
    claim_next,
    complete_job,
    ensure_queue_dirs,
    fail_job,
)

try:
    from services.backend_api.services.zendesk_bridge_service import (
        get_comments as zendesk_get_comments,
        get_ticket as zendesk_get_ticket,
        get_user as zendesk_get_user,
    )
except Exception:
    zendesk_get_ticket = None  # type: ignore
    zendesk_get_comments = None  # type: ignore
    zendesk_get_user = None  # type: ignore

logger = logging.getLogger("zendesk_ai_agent")

# ── LLM Backend Selection ────────────────────────────────────────────────

_LLM_PROVIDER: Optional[str] = None   # lazily resolved


def _get_llm_provider() -> str:
    """Return 'openai' or 'anthropic' based on env config."""
    global _LLM_PROVIDER
    if _LLM_PROVIDER:
        return _LLM_PROVIDER

    model = os.getenv("LLM_DEFAULT_MODEL", "gpt-4o")
    if "claude" in model.lower() or "anthropic" in model.lower():
        _LLM_PROVIDER = "anthropic"
    else:
        _LLM_PROVIDER = "openai"
    return _LLM_PROVIDER


# ── OpenAI helpers ────────────────────────────────────────────────────────

def _openai_chat(messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 1024) -> str:
    """Call the OpenAI chat completions API."""
    try:
        import openai  # type: ignore
    except ImportError:
        raise RuntimeError("openai package is not installed — run: pip install openai")

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = model or os.getenv("LLM_DEFAULT_MODEL", "gpt-4o")
    resp = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


# ── Anthropic helpers ─────────────────────────────────────────────────────

def _anthropic_chat(messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 1024) -> str:
    """Call the Anthropic messages API."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        raise RuntimeError("anthropic package is not installed — run: pip install anthropic")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = model or "claude-sonnet-4-20250514"

    # Anthropic expects system as a separate param.
    system_msg = ""
    user_msgs = []
    for m in messages:
        if m["role"] == "system":
            system_msg = m["content"]
        else:
            user_msgs.append(m)

    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_msg,
        messages=user_msgs,  # type: ignore[arg-type]
        temperature=0.3,
    )
    return resp.content[0].text


def _llm_chat(messages: List[Dict[str, str]], **kwargs: Any) -> str:
    """Route to the configured LLM provider."""
    provider = _get_llm_provider()
    if provider == "anthropic":
        return _anthropic_chat(messages, **kwargs)
    return _openai_chat(messages, **kwargs)


# ── System prompts ────────────────────────────────────────────────────────

SYSTEM_TRIAGE = """\
You are the CareerTrojan support AI agent.  Given a Zendesk support ticket,
classify it and return **only** valid JSON (no markdown fences):

{
  "priority": "low" | "normal" | "high" | "urgent",
  "category": "billing" | "account" | "technical" | "feature_request" | "career_advice" | "other",
  "summary": "<one-sentence summary>",
  "suggested_tags": ["tag1", "tag2"],
  "escalate": true | false,
  "escalation_reason": "<reason if escalate is true, else null>"
}

Be conservative with "urgent" — only use it for account lockouts, payment
failures, or data-loss scenarios.
"""

SYSTEM_DRAFT_REPLY = """\
You are the CareerTrojan support AI agent.  Draft a helpful, empathetic reply
to the user's support ticket.  Follow these rules:

1. Address the user by first name if available, otherwise "there".
2. Be concise — aim for 3-6 sentences.
3. If the issue requires investigation, say so honestly.
4. Sign off as "CareerTrojan Support".
5. Do NOT promise features or timelines that aren't confirmed.
6. Return **only** valid JSON (no markdown fences):

{
  "draft_reply": "<your suggested reply text>",
  "confidence": 0.0-1.0,
  "needs_human_review": true | false,
  "internal_note": "<optional note for the admin>"
}
"""

SYSTEM_SUMMARISE = """\
You are a support thread summariser.  Given the full conversation thread
of a Zendesk ticket, produce a concise summary.  Return **only** valid JSON:

{
  "summary": "<2-4 sentence summary>",
  "key_issue": "<the core problem in one phrase>",
  "resolution_status": "resolved" | "pending" | "escalated" | "unknown",
  "action_items": ["item1", "item2"]
}
"""

SYSTEM_ESCALATION = """\
You are a support escalation classifier.  Given a ticket's details,
decide whether it should be escalated to a senior agent.  Return **only** JSON:

{
  "escalate": true | false,
  "urgency": "low" | "medium" | "high" | "critical",
  "reason": "<brief justification>",
  "suggested_group": "billing" | "technical" | "management" | null
}
"""


# ── Job processors ────────────────────────────────────────────────────────

def _build_ticket_context(payload: Dict[str, Any]) -> str:
    """Flatten a webhook/ticket payload into a human-readable context block."""
    ticket = payload.get("ticket") or payload
    parts = []
    if ticket.get("subject"):
        parts.append(f"Subject: {ticket['subject']}")
    if ticket.get("description"):
        parts.append(f"Description:\n{ticket['description']}")
    if ticket.get("status"):
        parts.append(f"Status: {ticket['status']}")
    if ticket.get("priority"):
        parts.append(f"Priority: {ticket['priority']}")

    requester = payload.get("requester") or ticket.get("requester") or {}
    if requester:
        parts.append("\n--- Requester profile ---")
        if requester.get("name"):
            parts.append(f"Name: {requester['name']}")
        if requester.get("email"):
            parts.append(f"Email: {requester['email']}")
        if requester.get("locale"):
            parts.append(f"Locale: {requester['locale']}")
        if requester.get("time_zone"):
            parts.append(f"Time zone: {requester['time_zone']}")

    # Include recent comments if present
    comments = payload.get("comments") or ticket.get("comments") or []
    if comments:
        parts.append("\n--- Conversation thread ---")
        for c in comments[-10:]:   # last 10 comments
            author = c.get("author_name") or c.get("author_email") or "Unknown"
            body = c.get("body") or c.get("html_body") or ""
            parts.append(f"[{author}]: {body}")

    return "\n".join(parts) or json.dumps(ticket, indent=2)


def _enrich_from_zendesk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Hydrate payload with live Zendesk ticket/comments/requester context when possible."""
    enabled = os.getenv("ZENDESK_AI_ENRICH_REQUESTER", "true").lower() in ("1", "true", "yes")
    if not enabled:
        return payload

    if not zendesk_get_ticket or not zendesk_get_comments:
        return payload

    ticket = payload.get("ticket") or {}
    raw_ticket_id = ticket.get("id") or payload.get("ticket_id")
    if not raw_ticket_id:
        return payload

    try:
        ticket_id = int(raw_ticket_id)
    except (TypeError, ValueError):
        return payload

    try:
        provider_ticket = zendesk_get_ticket(ticket_id)
        comments = zendesk_get_comments(ticket_id)

        merged_payload = dict(payload)
        merged_ticket = dict(ticket)
        merged_ticket["id"] = raw_ticket_id

        for field in ("subject", "status", "priority"):
            if not merged_ticket.get(field) and provider_ticket.get(field):
                merged_ticket[field] = provider_ticket[field]

        provider_raw = provider_ticket.get("raw") or {}
        description = provider_raw.get("description")
        if not merged_ticket.get("description") and description:
            merged_ticket["description"] = description

        merged_payload["ticket"] = merged_ticket
        if comments:
            merged_payload["comments"] = comments

        requester_id = provider_ticket.get("requester_id") or provider_raw.get("requester_id")
        if requester_id and zendesk_get_user:
            try:
                requester = zendesk_get_user(int(requester_id))
                merged_payload["requester"] = requester
            except Exception as requester_exc:
                logger.warning("Failed to fetch Zendesk requester for ticket %s: %s", ticket_id, requester_exc)

        return merged_payload
    except Exception as exc:
        logger.warning("Zendesk enrichment failed for ticket %s: %s", raw_ticket_id, exc)
        return payload


def _process_triage(payload: Dict[str, Any]) -> Dict[str, Any]:
    context = _build_ticket_context(payload)
    raw = _llm_chat([
        {"role": "system", "content": SYSTEM_TRIAGE},
        {"role": "user", "content": context},
    ])
    return _safe_json(raw, fallback={"priority": "normal", "category": "other", "summary": raw[:200]})


def _process_draft_reply(payload: Dict[str, Any]) -> Dict[str, Any]:
    enriched_payload = _enrich_from_zendesk(payload)
    context = _build_ticket_context(enriched_payload)
    raw = _llm_chat([
        {"role": "system", "content": SYSTEM_DRAFT_REPLY},
        {"role": "user", "content": context},
    ])
    return _safe_json(raw, fallback={"draft_reply": raw, "confidence": 0.5, "needs_human_review": True})


def _process_summarise(payload: Dict[str, Any]) -> Dict[str, Any]:
    context = _build_ticket_context(payload)
    raw = _llm_chat([
        {"role": "system", "content": SYSTEM_SUMMARISE},
        {"role": "user", "content": context},
    ])
    return _safe_json(raw, fallback={"summary": raw[:500]})


def _process_escalation(payload: Dict[str, Any]) -> Dict[str, Any]:
    context = _build_ticket_context(payload)
    raw = _llm_chat([
        {"role": "system", "content": SYSTEM_ESCALATION},
        {"role": "user", "content": context},
    ])
    return _safe_json(raw, fallback={"escalate": False, "reason": raw[:200]})


_PROCESSORS = {
    "ticket_triage": _process_triage,
    "draft_reply": _process_draft_reply,
    "summarise_thread": _process_summarise,
    "escalation_check": _process_escalation,
}


# ── Main loop ─────────────────────────────────────────────────────────────

def process_one(root=None) -> bool:
    """
    Claim and process a single job.  Returns True if a job was processed.
    """
    envelope = claim_next(root=root)
    if not envelope:
        return False

    job_id = envelope["job_id"]
    kind = envelope.get("kind", "draft_reply")
    payload = envelope.get("payload", {})

    processor = _PROCESSORS.get(kind)
    if not processor:
        fail_job(job_id, f"Unknown job kind: {kind}", root=root)
        return True

    try:
        logger.info("Processing AI job %s  kind=%s", job_id, kind)
        result = processor(payload)
        result["processed_at"] = datetime.now(timezone.utc).isoformat()
        result["llm_provider"] = _get_llm_provider()
        result["llm_model"] = os.getenv("LLM_DEFAULT_MODEL", "gpt-4o")
        complete_job(job_id, result, root=root)
        logger.info("AI job %s completed successfully", job_id)
    except Exception as e:
        logger.exception("AI job %s failed: %s", job_id, e)
        fail_job(job_id, str(e), root=root)

    return True


def run_loop(
    poll_interval: float = 5.0,
    max_iterations: int = 0,
    root=None,
) -> None:
    """
    Blocking poll loop.  Runs forever unless *max_iterations* is set.

    Parameters
    ----------
    poll_interval : float
        Seconds to sleep when the queue is empty.
    max_iterations : int
        Stop after N jobs (0 = unlimited).
    root : Path, optional
        Override queue root.
    """
    ensure_queue_dirs(root)
    logger.info("Zendesk AI agent worker started  poll=%.1fs  provider=%s", poll_interval, _get_llm_provider())

    processed = 0
    while True:
        had_work = process_one(root=root)
        if had_work:
            processed += 1
            if max_iterations and processed >= max_iterations:
                logger.info("Reached max_iterations=%d — stopping", max_iterations)
                break
        else:
            time.sleep(poll_interval)


# ── Helpers ──────────────────────────────────────────────────────────────

def _safe_json(raw: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Try to parse JSON from LLM output, stripping markdown fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Strip ```json ... ```
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON — using fallback. Raw: %s", raw[:300])
        return fallback or {"raw_response": raw}


# ── CLI entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from pathlib import Path as _Path

    # Load .env if present
    try:
        from dotenv import load_dotenv
        env_path = _Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ZD-AI] %(levelname)s %(message)s",
    )

    poll = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
    run_loop(poll_interval=poll)
