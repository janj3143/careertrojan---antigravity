from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.backend_api.services.career.interview_coach_service import (
    generate_interview_questions,
    generate_star_stories,
    get_learning_profile,
    infer_role_family,
    record_interview_feedback,
)


ROLE_FUNCTIONS: Dict[str, str] = {
    "technical": "TECH",
    "development": "TECH",
    "engineering": "OPS",
    "sales": "SALES",
    "marketing": "MKT",
    "finance": "FIN",
    "management": "EXEC",
}


DEFAULT_90_DAY_PLAN = {
    "junior": {
        "days_1_30": ["Understand team goals", "Map current workflows", "Shadow key stakeholders"],
        "days_31_60": ["Own a scoped deliverable", "Improve one process bottleneck"],
        "days_61_90": ["Deliver measurable impact", "Present learnings and next roadmap"],
    },
    "mid": {
        "days_1_30": ["Audit baseline metrics", "Build stakeholder map", "Validate role KPIs"],
        "days_31_60": ["Execute high-priority initiatives", "Stabilize delivery cadence"],
        "days_61_90": ["Scale successful patterns", "Commit quarter roadmap"],
    },
    "senior": {
        "days_1_30": ["Set strategic priorities", "Assess risks/dependencies", "Align leadership expectations"],
        "days_31_60": ["Drive cross-functional execution", "Unblock structural constraints"],
        "days_61_90": ["Deliver strategic milestone", "Publish operating model + next quarter plan"],
    },
}


@dataclass
class InterviewCoachingService:
    """Role detection + question serving + 90-day plan + learning feedback facade."""

    def detect_role_function(
        self,
        job_data: Optional[Dict[str, Any]] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        resume_experience: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        resume_payload = dict(resume_data or {})
        if resume_experience and "work_experience" not in resume_payload:
            resume_payload["work_experience"] = resume_experience

        family = infer_role_family(resume_payload, job_data or {})
        code = ROLE_FUNCTIONS.get(family, "EXEC")

        return {
            "role_family": family,
            "role_function": code,
            "detected_at": datetime.utcnow().isoformat() + "Z",
        }

    def get_interview_questions(
        self,
        role_function: str,
        limit: int = 10,
        resume: Optional[Dict[str, Any]] = None,
        job: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        question_type = "Role-specific"
        fit = {"role_function": role_function}
        payload = generate_interview_questions(
            question_type=question_type,
            count=max(1, min(limit, 25)),
            resume=resume,
            job=job,
            fit=fit,
        )
        questions = payload.get("questions") if isinstance(payload, dict) else payload
        if not isinstance(questions, list):
            return []
        return questions[:limit]

    def get_90day_plan(self, role_function: str, seniority: str = "mid") -> Dict[str, Any]:
        bucket = seniority.strip().lower()
        if bucket not in DEFAULT_90_DAY_PLAN:
            bucket = "mid"
        return {
            "role_function": role_function,
            "seniority": bucket,
            "plan": DEFAULT_90_DAY_PLAN[bucket],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    def record_session_feedback(
        self,
        role_family: str,
        question_type: str,
        question: str,
        helpful: Optional[bool] = None,
        answer_score: Optional[int] = None,
        session_outcome: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return record_interview_feedback(
            role_family=role_family,
            question_type=question_type,
            question=question,
            helpful=helpful,
            answer_score=answer_score,
            session_outcome=session_outcome,
            user_id=user_id,
        )

    def get_learning_profile(self, role_family: Optional[str] = None) -> Dict[str, Any]:
        return get_learning_profile(role_family=role_family)

    def generate_star_stories(
        self,
        focus_areas: List[str],
        resume: Optional[Dict[str, Any]] = None,
        job: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        payload = generate_star_stories(focus_areas=focus_areas, resume=resume, job=job)
        if isinstance(payload, dict) and isinstance(payload.get("stories"), list):
            return payload["stories"]
        if isinstance(payload, list):
            return payload
        return []


_service: Optional[InterviewCoachingService] = None


def get_interview_coaching_service() -> InterviewCoachingService:
    global _service
    if _service is None:
        _service = InterviewCoachingService()
    return _service


def detect_role_function(
    job_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    resume_experience: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return get_interview_coaching_service().detect_role_function(
        job_data=job_data,
        resume_data=resume_data,
        resume_experience=resume_experience,
    )


def get_interview_questions(
    role_function: str,
    limit: int = 10,
    resume: Optional[Dict[str, Any]] = None,
    job: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    return get_interview_coaching_service().get_interview_questions(
        role_function=role_function,
        limit=limit,
        resume=resume,
        job=job,
    )


def get_90day_plan(role_function: str, seniority: str = "mid") -> Dict[str, Any]:
    return get_interview_coaching_service().get_90day_plan(role_function=role_function, seniority=seniority)
