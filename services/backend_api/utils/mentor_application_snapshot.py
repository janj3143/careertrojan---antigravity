"""Utility helpers for building mentor application review snapshots."""

from datetime import datetime
from typing import Dict, Any, List, Optional


def format_packages_for_review(packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize package definitions for Guardian review."""
    formatted: List[Dict[str, Any]] = []
    for package in packages or []:
        price = float(package.get('price') or 0)
        sessions = int(package.get('sessions') or 1)
        duration = package.get('duration') or 60
        total_price = price * sessions
        formatted.append({
            'name': package.get('name') or 'Mentorship Package',
            'description': package.get('description') or '',
            'session_count': sessions,
            'session_duration': f"{duration} minutes",
            'price_per_session': price,
            'total_price': total_price,
            'mentor_earnings': round(total_price * 0.8, 2),
            'includes': package.get('includes')
        })
    return formatted


def _normalize_submitted_date(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def build_application_snapshot(
    application_id: Any,
    status: str,
    submitted_date: Optional[Any],
    step1: Dict[str, Any],
    step2: Dict[str, Any],
    step3: Dict[str, Any],
    ai_chat_history: Optional[List[Dict[str, Any]]] = None,
    source: str = 'user_portal'
) -> Dict[str, Any]:
    """Create a normalized snapshot shared between portals."""

    industries = step1.get('industry')
    if isinstance(industries, list):
        industries_list = industries
    elif isinstance(industries, str):
        industries_list = [industries] if industries else []
    else:
        industries_list = []

    years_value = step1.get('years_experience')
    if isinstance(years_value, (int, float)):
        years_display = f"{years_value} years"
    elif isinstance(years_value, str) and years_value.strip():
        years_display = years_value
    else:
        years_display = "Not provided"

    expertise_areas = step2.get('expertise_areas', []) or []
    packages = format_packages_for_review(step3.get('packages', []))
    chat_history = ai_chat_history or []

    snapshot = {
        'application_id': str(application_id) if application_id is not None else None,
        'status': status or 'submitted',
        'submitted_date': _normalize_submitted_date(submitted_date) or datetime.utcnow().isoformat(),
        'professional': {
            'full_name': step1.get('full_name'),
            'email': step1.get('email'),
            'phone': step1.get('phone'),
            'linkedin': step1.get('linkedin_url'),
            'current_role': step1.get('current_role'),
            'company': step1.get('current_company'),
            'years_experience': years_display,
            'industry': industries_list,
            'professional_summary': step1.get('specialization') or '',
            'achievements': step2.get('expertise_other')
        },
        'expertise': {
            'technical_expertise': [],
            'leadership_expertise': [],
            'career_expertise': expertise_areas,
            'business_expertise': [],
            'target_audience': step2.get('target_audience', []),
            'session_formats': step2.get('session_formats', []),
            'availability': (
                f"{step2.get('hours_per_week')} hours/week"
                if step2.get('hours_per_week')
                else 'Not provided'
            ),
            'ai_recommendations': step2.get('ai_recommendations', []) or []
        },
        'packages': packages,
        'ai_chat_history': chat_history,
        'guardian_notes': [],
        'source': source
    }

    return snapshot
