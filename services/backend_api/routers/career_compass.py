from __future__ import annotations

from datetime import datetime
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from services.backend_api.db.connection import get_db
from services.backend_api.db.models import Job, Mentor, Resume
from services.backend_api.routers.runtime_contract import respond
from services.shared.paths import CareerTrojanPaths


router = APIRouter(prefix="/career-compass", tags=["career-compass"])

_VECTOR_AXES = [
    "leadership",
    "commercial",
    "technical",
    "communication",
    "delivery",
    "strategic_thinking",
    "domain_expertise",
]


def _ts() -> str:
    return datetime.utcnow().isoformat()


def _ok(data: Dict[str, Any], source_summary: Dict[str, Any], message: Optional[str] = None):
    return respond(status="ok", data=data, source_summary=source_summary, message=message)


def _missing(status: str, message: str, source_summary: Dict[str, Any]):
    return respond(status=status, message=message, data={}, source_summary=source_summary)


def _resume_text_for_user(db: Session, user_id: int) -> Optional[str]:
    row = (
        db.query(Resume)
        .filter(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    if not row:
        return None
    return (row.parsed_content or "").strip() or None


def _norm_score(matches: int, max_matches: int = 8) -> float:
    if matches <= 0:
        return 0.0
    return round(min(1.0, matches / max_matches) * 100.0, 2)


def _vector_from_text(text: str) -> Dict[str, float]:
    text_l = text.lower()
    lexicon = {
        "leadership": ["lead", "mentored", "managed", "owner"],
        "commercial": ["revenue", "growth", "customer", "sales"],
        "technical": ["python", "sql", "api", "architecture", "cloud"],
        "communication": ["presented", "stakeholder", "collaborat", "communicat"],
        "delivery": ["delivered", "shipped", "launched", "implemented"],
        "strategic_thinking": ["strategy", "roadmap", "planning", "vision"],
        "domain_expertise": ["industry", "domain", "specialist", "expert"],
    }
    vec: Dict[str, float] = {}
    for axis in _VECTOR_AXES:
        hits = sum(1 for token in lexicon[axis] if token in text_l)
        vec[axis] = _norm_score(hits)
    return vec


def _discover_role_files(paths: CareerTrojanPaths, limit: int = 600) -> List[Path]:
    roots = [
        paths.ai_data_final / "parsed_job_descriptions",
        paths.ai_data_final / "job_descriptions",
        paths.ai_data_final / "job_titles",
    ]
    files: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        files.extend(root.rglob("*.json"))
        if len(files) >= limit:
            break
    return files[:limit]


def _load_live_role_titles(paths: CareerTrojanPaths, limit: int = 600) -> List[str]:
    import json

    titles: List[str] = []
    for fp in _discover_role_files(paths, limit=limit):
        try:
            payload = json.loads(fp.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        records: List[Dict[str, Any]] = []
        if isinstance(payload, dict):
            records = [payload]
        elif isinstance(payload, list):
            records = [item for item in payload if isinstance(item, dict)]

        for rec in records:
            title = str(rec.get("title") or rec.get("job_title") or "").strip()
            if title:
                titles.append(title)
    return titles


class SpiderOverlayRequest(BaseModel):
    user_id: int
    role_text: str


class RunwayRequest(BaseModel):
    user_id: int
    target_role: str


class MentorMatchRequest(BaseModel):
    user_id: int
    target_role: str


class CuldesacCheckRequest(BaseModel):
    cluster_id: Optional[str] = None
    target_role: Optional[str] = None


class SaveScenarioRequest(BaseModel):
    user_id: int
    resume_id: Optional[int] = None
    scenario_key: str
    selected_cluster_id: Optional[str] = None
    selected_target_role: Optional[str] = None
    notes: Optional[str] = None


@router.get("/map")
def career_compass_map(
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    paths = CareerTrojanPaths()
    resume_text = _resume_text_for_user(db, user_id)
    live_titles = _load_live_role_titles(paths)

    source_summary = {
        "user_id": user_id,
        "resume_found": bool(resume_text),
        "role_records": len(live_titles),
        "ai_data_root": str(paths.ai_data_final),
    }

    if not resume_text:
        return _missing(
            status="missing_resume",
            message="No live parsed resume available. Upload a resume to generate your career profile.",
            source_summary=source_summary,
        )

    if not live_titles:
        return _missing(
            status="missing_cluster",
            message="No peer cluster found for this role. Try broadening the search criteria.",
            source_summary=source_summary,
        )

    grouped: Dict[str, int] = {}
    for title in live_titles:
        bucket = title.split("-")[0].split("/")[0].strip()
        if not bucket:
            continue
        grouped[bucket] = grouped.get(bucket, 0) + 1

    clusters = [
        {
            "cluster_id": f"cluster-{idx+1}",
            "label": label,
            "cluster_size": size,
        }
        for idx, (label, size) in enumerate(sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:12])
    ]

    return _ok(data={"clusters": clusters}, source_summary=source_summary)


@router.get("/cluster/{cluster_id}")
def career_compass_cluster(cluster_id: str, db: Session = Depends(get_db)):
    paths = CareerTrojanPaths()
    live_titles = _load_live_role_titles(paths)
    source_summary = {
        "cluster_id": cluster_id,
        "role_records": len(live_titles),
        "ai_data_root": str(paths.ai_data_final),
    }

    if not live_titles:
        return _missing(
            status="missing_cluster",
            message="No peer cluster found for this role. Try broadening the search criteria.",
            source_summary=source_summary,
        )

    top_titles = sorted(set(live_titles))[:20]
    industries = ["live_market_mapped"]
    return _ok(
        data={
            "cluster_id": cluster_id,
            "cluster_size": len(live_titles),
            "typical_titles": top_titles,
            "common_industries": industries,
        },
        source_summary=source_summary,
    )


@router.post("/spider-overlay")
def career_compass_spider_overlay(payload: SpiderOverlayRequest, db: Session = Depends(get_db)):
    resume_text = _resume_text_for_user(db, payload.user_id)
    source_summary = {
        "user_id": payload.user_id,
        "resume_found": bool(resume_text),
        "target_role_text_len": len(payload.role_text.strip()),
    }

    if not resume_text:
        return _missing(
            status="missing_resume",
            message="No live parsed resume available. Upload a resume to generate your career profile.",
            source_summary=source_summary,
        )

    role_text = payload.role_text.strip()
    if not role_text:
        return _missing(
            status="missing_cluster",
            message="No peer cluster found for this role. Try broadening the search criteria.",
            source_summary=source_summary,
        )

    user_vector = _vector_from_text(resume_text)
    cluster_vector = _vector_from_text(role_text)
    gap_vector = {axis: round(cluster_vector[axis] - user_vector[axis], 2) for axis in _VECTOR_AXES}

    return _ok(
        data={
            "axes": _VECTOR_AXES,
            "user_vector": user_vector,
            "cluster_vector": cluster_vector,
            "gap_vector": gap_vector,
        },
        source_summary=source_summary,
    )


@router.get("/market-signal")
def career_compass_market_signal(
    role: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    active_roles = (
        db.query(func.count(Job.id))
        .filter(Job.is_active.is_(True))
        .filter(Job.title.ilike(f"%{role}%"))
        .scalar()
        or 0
    )

    hiring_companies = (
        db.query(func.count(func.distinct(Job.company)))
        .filter(Job.is_active.is_(True))
        .filter(Job.title.ilike(f"%{role}%"))
        .scalar()
        or 0
    )

    source_summary = {
        "role": role,
        "jobs_analyzed": int(active_roles),
        "companies_analyzed": int(hiring_companies),
    }

    if active_roles == 0:
        return _missing(
            status="missing_market_data",
            message="Live job market signals unavailable. Cluster analysis remains available.",
            source_summary=source_summary,
        )

    traction_score = round(min(100.0, (active_roles * 0.6) + (hiring_companies * 1.8)), 2)

    return _ok(
        data={
            "role": role,
            "active_roles": int(active_roles),
            "hiring_companies": int(hiring_companies),
            "career_traction_score": traction_score,
        },
        source_summary=source_summary,
    )


@router.post("/runway")
def career_compass_runway(payload: RunwayRequest, db: Session = Depends(get_db)):
    resume_text = _resume_text_for_user(db, payload.user_id)
    source_summary = {
        "user_id": payload.user_id,
        "resume_found": bool(resume_text),
        "target_role": payload.target_role,
    }

    if not resume_text:
        return _missing(
            status="missing_resume",
            message="No live parsed resume available. Upload a resume to generate your career profile.",
            source_summary=source_summary,
        )

    current_role = "Current Profile"
    target = payload.target_role.strip()
    if not target:
        return _missing(
            status="missing_cluster",
            message="No peer cluster found for this role. Try broadening the search criteria.",
            source_summary=source_summary,
        )

    stages = [
        {"stage": "current", "role": current_role},
        {"stage": "adjacent", "role": f"Adjacent to {target}"},
        {"stage": "target", "role": target},
        {"stage": "stretch", "role": f"Senior {target}"},
    ]

    return _ok(data={"runway": stages}, source_summary=source_summary)


@router.post("/mentor-match")
def career_compass_mentor_match(payload: MentorMatchRequest, db: Session = Depends(get_db)):
    resume_text = _resume_text_for_user(db, payload.user_id)
    mentors = db.query(Mentor).limit(500).all()

    source_summary = {
        "user_id": payload.user_id,
        "resume_found": bool(resume_text),
        "mentors_considered": len(mentors),
    }

    if not resume_text:
        return _missing(
            status="missing_resume",
            message="No live parsed resume available. Upload a resume to generate your career profile.",
            source_summary=source_summary,
        )

    if not mentors:
        return _missing(
            status="missing_mentor_data",
            message="No live mentors available for the current gap profile.",
            source_summary=source_summary,
        )

    target_l = payload.target_role.lower().strip()
    ranked: List[Dict[str, Any]] = []
    for mentor in mentors:
        spec = (mentor.specialty or "").lower()
        score = 100 if target_l and target_l in spec else (60 if spec else 10)
        ranked.append(
            {
                "mentor_id": mentor.id,
                "specialty": mentor.specialty,
                "availability": mentor.availability,
                "match_score": score,
            }
        )

    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return _ok(data={"matches": ranked[:10]}, source_summary=source_summary)


@router.get("/routes")
def career_compass_routes(
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    resume_text = _resume_text_for_user(db, user_id)
    source_summary = {
        "user_id": user_id,
        "resume_found": bool(resume_text),
    }

    if not resume_text:
        return _missing(
            status="missing_resume",
            message="No live parsed resume available. Upload a resume to generate your route analysis.",
            source_summary=source_summary,
        )

    user_vector = _vector_from_text(resume_text)
    leadership = user_vector.get("leadership", 0.0)
    technical = user_vector.get("technical", 0.0)
    strategic = user_vector.get("strategic_thinking", 0.0)

    natural_next_steps = []
    strategic_stretch = []
    too_far_for_now = []

    if technical >= 40:
        natural_next_steps.append("Senior Engineer")
    else:
        natural_next_steps.append("Engineer II")

    if leadership >= 40 and strategic >= 35:
        strategic_stretch.append("Engineering Manager")
    else:
        too_far_for_now.append("Director of Engineering")

    return _ok(
        data={
            "natural_next_steps": natural_next_steps,
            "strategic_stretch": strategic_stretch,
            "too_far_for_now": too_far_for_now,
        },
        source_summary=source_summary,
    )


@router.post("/culdesac-check")
def career_compass_culdesac_check(
    payload: CuldesacCheckRequest,
    db: Session = Depends(get_db),
):
    target_role = (payload.target_role or payload.cluster_id or "").strip()
    source_summary = {
        "cluster_id": payload.cluster_id,
        "target_role": payload.target_role,
    }

    if not target_role:
        return _missing(
            status="missing_cluster",
            message="A target role or cluster_id is required for cul-de-sac assessment.",
            source_summary=source_summary,
        )

    active_roles = (
        db.query(func.count(Job.id))
        .filter(Job.is_active.is_(True))
        .filter(Job.title.ilike(f"%{target_role}%"))
        .scalar()
        or 0
    )

    source_summary["job_records_analyzed"] = int(active_roles)

    if active_roles == 0:
        return _ok(
            data={
                "risk_level": "Cul-de-Sac Risk",
                "reasons": [
                    "No active live role demand found for the selected route.",
                    "Transferability should be reviewed before committing.",
                ],
            },
            source_summary=source_summary,
        )

    if active_roles < 20:
        risk_level = "Moderate Mobility"
        reasons = ["Live demand exists but is limited in volume."]
    else:
        risk_level = "High Mobility"
        reasons = ["Live demand is healthy for this route."]

    return _ok(data={"risk_level": risk_level, "reasons": reasons}, source_summary=source_summary)


@router.post("/save-scenario")
def career_compass_save_scenario(payload: SaveScenarioRequest):
    paths = CareerTrojanPaths()
    store_dir = paths.user_data / "career_compass_scenarios"
    store_dir.mkdir(parents=True, exist_ok=True)

    scenario_id = f"scenario-{uuid.uuid4()}"
    scenario_record = {
        "scenario_id": scenario_id,
        "user_id": payload.user_id,
        "resume_id": payload.resume_id,
        "scenario_key": payload.scenario_key,
        "selected_cluster_id": payload.selected_cluster_id,
        "selected_target_role": payload.selected_target_role,
        "notes": payload.notes,
        "saved_at": _ts(),
    }

    target_file = store_dir / f"{payload.user_id}_{payload.scenario_key}.json"
    target_file.write_text(json.dumps(scenario_record, ensure_ascii=False, indent=2), encoding="utf-8")

    source_summary = {
        "user_id": payload.user_id,
        "resume_id": payload.resume_id,
        "scenario_key": payload.scenario_key,
        "storage_path": str(target_file),
    }

    return _ok(data={"scenario_id": scenario_id}, source_summary=source_summary)
