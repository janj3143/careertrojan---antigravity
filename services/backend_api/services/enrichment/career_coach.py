"""Career Coach enrichment hook.
This stays thin and delegates to `CareerCoachService` so that the
same logic is used for:
- admin dashboards
- API endpoints
- user portal Coaching Hub (via portal bridge)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from admin_portal.services.career.career_coach import (
    get_career_coach_recommendations,
)


def enrich_career_coach(
    user_profile: Dict[str, Any],
    resume_data: Dict[str, Any],
    job_data: Optional[Dict[str, Any]] = None,
    applications: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Analyze user career trajectory, suggest next steps, and provide coaching insights.

    This is the function that the hybrid enrichment harness can call.
    """
    return get_career_coach_recommendations(
        user_profile=user_profile,
        resume_data=resume_data,
        job_data=job_data,
        applications=applications,
    )
