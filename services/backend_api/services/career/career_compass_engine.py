"""
Career Compass Engine — Core intelligence service (spec §9/§15/§16/§17).

Provides: career map, cluster profiles, spider overlay, route classification,
cul-de-sac detection, runway planning, mentor matching, scenario save.

LIVE DATA ONLY — returns structured missing-data states when dependencies
are absent (spec §5 / §24).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Stub cluster registry (replace with live ai_data_final loader) ──
# This will be loaded from live clustered records at startup
_cluster_registry: Dict[str, dict] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CareerCompassEngine:
    """Orchestrates Career Compass intelligence operations."""

    # ── Career Map (spec §9.1) ─────────────────────────────────
    async def get_map(self, user_id: str = None, resume_id: str = None) -> dict:
        if not _cluster_registry:
            return {
                "status": "missing_cluster",
                "message": "No live peer cluster is currently available. Try refreshing the clustered dataset.",
                "nodes": [],
                "source_summary": {"resume_id": resume_id, "cluster_record_count": 0},
                "generated_at": _now_iso(),
            }
        nodes = []
        for cid, cdata in _cluster_registry.items():
            nodes.append({
                "cluster_id": cid,
                "label": cdata.get("label", cid),
                "route_type": cdata.get("route_type"),
                "x": cdata.get("x", 0.0),
                "y": cdata.get("y", 0.0),
            })
        return {
            "status": "ok",
            "nodes": nodes,
            "source_summary": {"resume_id": resume_id, "cluster_record_count": len(nodes)},
            "generated_at": _now_iso(),
        }

    # ── Cluster Profile (spec §9.2) ───────────────────────────
    async def get_cluster_profile(self, cluster_id: str) -> dict:
        cluster = _cluster_registry.get(cluster_id)
        if not cluster:
            return {
                "status": "missing_cluster",
                "cluster_id": cluster_id,
                "message": f"No live cluster data found for '{cluster_id}'.",
                "source_summary": {"cluster_record_count": 0},
            }
        return {
            "status": "ok",
            "cluster_id": cluster_id,
            "title": cluster.get("label", cluster_id),
            "summary": cluster.get("summary", {}),
            "vector": cluster.get("vector", {}),
            "source_summary": {"cluster_record_count": 1},
        }

    # ── Spider Overlay (spec §9.3) ─────────────────────────────
    async def get_spider_overlay(self, payload) -> dict:
        # Requires both user vector and target cluster vector
        from services.backend_api.services.career.user_vector_service import UserVectorService
        uv_svc = UserVectorService()
        uv_resp = await uv_svc.get_current_vector(payload.user_id, payload.resume_id)

        if uv_resp["status"] != "ok" or not uv_resp.get("vector"):
            return {
                "status": "missing_resume",
                "message": "No live user vector found. Please upload a processed resume.",
                "source_summary": {"resume_id": payload.resume_id},
            }

        cluster = _cluster_registry.get(payload.cluster_id)
        if not cluster or not cluster.get("vector"):
            return {
                "status": "missing_cluster",
                "message": f"No live cluster vector for '{payload.cluster_id}'.",
                "source_summary": {"resume_id": payload.resume_id, "cluster_record_count": 0},
            }

        user_vec = uv_resp["vector"]
        target_vec = cluster["vector"]
        gap_vec = {k: round(target_vec.get(k, 0) - user_vec.get(k, 0), 3) for k in set(user_vec) | set(target_vec)}
        strengths = [k for k, v in gap_vec.items() if v <= 0]
        gaps = [k for k, v in gap_vec.items() if v > 0]

        return {
            "status": "ok",
            "user_vector": user_vec,
            "target_vector": target_vec,
            "gap_vector": gap_vec,
            "strengths": strengths,
            "gaps": gaps,
            "source_summary": {"resume_id": payload.resume_id, "cluster_record_count": 1},
        }

    # ── Routes (spec §15.1) ────────────────────────────────────
    async def get_routes(self, user_id: str = None, resume_id: str = None) -> dict:
        if not _cluster_registry:
            return {
                "status": "missing_cluster",
                "message": "No live cluster data available to classify routes.",
                "natural_next_steps": [],
                "strategic_stretch": [],
                "too_far_for_now": [],
                "source_summary": {"cluster_record_count": 0},
            }
        natural = [c["label"] for c in _cluster_registry.values() if c.get("route_type") == "natural_next_step"]
        stretch = [c["label"] for c in _cluster_registry.values() if c.get("route_type") == "strategic_stretch"]
        far = [c["label"] for c in _cluster_registry.values() if c.get("route_type") == "too_far_for_now"]
        return {
            "status": "ok",
            "natural_next_steps": natural,
            "strategic_stretch": stretch,
            "too_far_for_now": far,
            "source_summary": {"cluster_record_count": len(_cluster_registry)},
        }

    # ── Cul-de-sac Detection (spec §15.2) ──────────────────────
    async def check_culdesac(self, payload) -> dict:
        cluster = _cluster_registry.get(payload.cluster_id)
        if not cluster:
            return {
                "status": "missing_cluster",
                "risk_level": None,
                "reasons": [f"No live cluster data for '{payload.cluster_id}'."],
                "source_summary": {"cluster_record_count": 0},
            }
        mobility = cluster.get("mobility", "moderate_mobility")
        reasons = cluster.get("culdesac_reasons", [])
        return {
            "status": "ok",
            "risk_level": mobility,
            "reasons": reasons,
            "source_summary": {"cluster_record_count": 1},
        }

    # ── Runway (spec §18) ──────────────────────────────────────
    async def get_runway(self, payload) -> dict:
        spider = await self.get_spider_overlay(payload)
        if spider["status"] != "ok":
            return {
                "status": spider["status"],
                "message": spider.get("message", "Cannot build runway without spider overlay."),
                "steps": [],
                "source_summary": spider.get("source_summary"),
            }
        gaps = spider.get("gaps", [])
        steps = []
        for i, gap_axis in enumerate(gaps[:5], 1):
            steps.append({
                "step_number": i,
                "title": f"Close the {gap_axis.replace('_', ' ').title()} gap",
                "detail": f"Focus on building evidence and experience in {gap_axis.replace('_', ' ')}.",
            })
        if not steps:
            steps.append({
                "step_number": 1,
                "title": "Maintain current strengths",
                "detail": "Your profile already aligns well with this route. Focus on deepening expertise.",
            })
        return {
            "status": "ok",
            "steps": steps,
            "source_summary": spider.get("source_summary"),
        }

    # ── Mentor Match (spec §17) ────────────────────────────────
    async def get_mentor_matches(self, payload) -> dict:
        spider = await self.get_spider_overlay(payload)
        if spider["status"] != "ok":
            return {
                "status": spider["status"],
                "message": spider.get("message"),
                "mentors": [],
                "source_summary": spider.get("source_summary"),
            }
        gaps = spider.get("gaps", [])
        if not gaps:
            return {
                "status": "ok",
                "mentors": [],
                "source_summary": {"resume_id": payload.resume_id, "mentor_records_scanned": 0},
            }
        # Phase A: Ideal mentor profile types (spec §17 Phase A)
        mentors = []
        for gap in gaps[:3]:
            mentors.append({
                "mentor_id": f"ideal_{gap}",
                "name": f"Ideal {gap.replace('_', ' ').title()} Mentor",
                "match_reason": f"Can help close the {gap.replace('_', ' ')} gap.",
            })
        return {
            "status": "ok",
            "mentors": mentors,
            "source_summary": {"resume_id": payload.resume_id, "mentor_records_scanned": 0},
        }

    # ── Market Signal (spec §16) ───────────────────────────────
    async def get_market_signal(self, payload) -> dict:
        cluster = _cluster_registry.get(payload.cluster_id)
        if not cluster:
            return {
                "status": "missing_market_data",
                "message": "Live market validation is not available yet for this route.",
                "metrics": None,
                "recurring_skills": [],
                "source_summary": {"job_records_analyzed": 0},
            }
        market = cluster.get("market", {})
        if not market:
            return {
                "status": "missing_market_data",
                "message": "Live market validation is not available yet for this route. Peer-based route analysis is available, but live job traction has not been loaded.",
                "metrics": None,
                "recurring_skills": [],
                "source_summary": {"job_records_analyzed": 0},
            }
        return {
            "status": "ok",
            "metrics": market.get("metrics", {}),
            "recurring_skills": market.get("recurring_skills", []),
            "source_summary": {"job_records_analyzed": market.get("job_count", 0)},
        }

    # ── Save Scenario (spec §15.8) ─────────────────────────────
    async def save_scenario(self, payload) -> dict:
        scenario_id = f"{payload.user_id}:{payload.resume_id}:{payload.cluster_id}"
        if payload.scenario_key:
            scenario_id = f"{scenario_id}:{payload.scenario_key}"
        return {
            "status": "ok",
            "scenario_id": scenario_id,
            "source_summary": {"resume_id": payload.resume_id},
        }


def register_cluster(cluster_id: str, data: dict):
    """Register a live cluster into the career compass registry."""
    _cluster_registry[cluster_id] = data
    logger.info("Registered cluster: %s", cluster_id)


def get_cluster_count() -> int:
    return len(_cluster_registry)
