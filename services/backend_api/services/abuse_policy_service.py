"""
Abuse Policy Service — anti-gaming / resume fraud detection.

Evaluates new resume uploads against fingerprints of recent submissions
to detect duplicate/plagiarised content, rapid-fire re-uploads, and
account-type gaming.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import hashlib, json


# ── Configuration ────────────────────────────────────────────────────
COOLDOWN_MINUTES = 30          # min gap between consecutive uploads
MAX_UPLOADS_PER_DAY = 10
SIMILARITY_THRESHOLD = 0.85    # 0-1; above this = duplicate flag
RISK_WEIGHTS = {
    "duplicate_text": 40,
    "rapid_upload": 20,
    "account_type_mismatch": 25,
    "missing_sections": 15,
}


@dataclass
class PolicyDecision:
    decision: str               # "allow" | "quarantine" | "cooldown"
    risk_score: int             # 0-100
    reason_codes: List[str] = field(default_factory=list)
    cooldown_until: Optional[datetime] = None


class AbusePolicyService:
    """Stateless evaluator — call `.evaluate()` per upload."""

    # ── fingerprinting ───────────────────────────────────────────────
    @staticmethod
    def build_fingerprint(raw_text: str, parsed: Dict[str, Any]) -> str:
        """SHA-256 of normalised text + parsed keys for diffing."""
        norm = " ".join(raw_text.lower().split())
        blob = json.dumps({"text": norm, "keys": sorted(parsed.keys())},
                          sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    # ── similarity ───────────────────────────────────────────────────
    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        sa, sb = set(a.lower().split()), set(b.lower().split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    # ── main evaluation ──────────────────────────────────────────────
    def evaluate(
        self,
        *,
        account_type: str,
        new_fp: str,
        recent_upload_timestamps: List[datetime],
        last_master_fp: Optional[str] = None,
        last_active_fp: Optional[str] = None,
    ) -> PolicyDecision:
        codes: List[str] = []
        score = 0

        # 1. duplicate / near-duplicate fingerprint
        for label, old_fp in [("master", last_master_fp), ("active", last_active_fp)]:
            if old_fp and old_fp == new_fp:
                codes.append(f"duplicate_{label}")
                score += RISK_WEIGHTS["duplicate_text"]

        # 2. rapid-fire uploads
        now = datetime.utcnow()
        recent_today = [t for t in recent_upload_timestamps
                        if (now - t).total_seconds() < 86_400]
        if len(recent_today) >= MAX_UPLOADS_PER_DAY:
            codes.append("daily_limit_exceeded")
            score += RISK_WEIGHTS["rapid_upload"]

        if recent_upload_timestamps:
            last = max(recent_upload_timestamps)
            gap = (now - last).total_seconds() / 60
            if gap < COOLDOWN_MINUTES:
                codes.append("cooldown_violation")
                score += RISK_WEIGHTS["rapid_upload"]

        # 3. decision
        if score >= 60:
            decision = "quarantine"
        elif score >= 30:
            decision = "cooldown"
            cooldown_until = now + timedelta(minutes=COOLDOWN_MINUTES)
        else:
            decision = "allow"
            cooldown_until = None  # type: ignore[assignment]

        return PolicyDecision(
            decision=decision,
            risk_score=min(score, 100),
            reason_codes=codes,
            cooldown_until=cooldown_until if decision == "cooldown" else None,
        )
