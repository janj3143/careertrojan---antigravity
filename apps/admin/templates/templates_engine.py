from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from .templates_registry import (
    TemplateCategory,
    get_template_by_slug,
    load_template_text,
)


@dataclass
class ExaContext:
    """Represents enriched company intel from the Exa-powered admin service."""
    company_name: str
    recent_news_headline_1: str | None = None
    recent_article_title: str | None = None
    initiative_or_programme: str | None = None
    theme_from_news: str | None = None
    operational_initiative: str | None = None


def render_template_with_placeholders(template_text: str, placeholders: Dict[str, Any]) -> str:
    """Simple placeholder replacement using {{key}} style markers.

    NOTE: this is intentionally minimal – upstream AI / templating engines
    in the admin portal can replace this with Jinja2, etc.
    """
    result = template_text
    for key, value in placeholders.items():
        token = "{{" + key + "}}"
        result = result.replace(token, str(value))
    return result


def generate_speculative_letter(
    slug: str,
    user_profile: Dict[str, Any],
    exa_context: ExaContext,
    extra: Dict[str, Any] | None = None,
) -> str:
    """Render a speculative application letter using a named template + Exa context.

    slug: e.g. '01_speculative_application_strategy_focus'
    user_profile: dict from admin/user portal (skills, experience, contact)
    exa_context: enriched company intel from Exa admin page
    extra: any additional overrides for placeholders
    """
    tpl_path = get_template_by_slug(TemplateCategory.SPECULATIVE, slug)
    if not tpl_path:
        raise ValueError(f"No speculative template found for slug: {slug}")

    raw = load_template_text(tpl_path)

    placeholders: Dict[str, Any] = {
        "candidate_name": user_profile.get("full_name", "Candidate"),
        "candidate_email": user_profile.get("email", ""),
        "candidate_phone": user_profile.get("phone", ""),
        "linkedin_url": user_profile.get("linkedin", ""),
        "years_experience": user_profile.get("years_experience", ""),
        "experience_area": user_profile.get("experience_area", ""),
        "transferable_skills": user_profile.get("transferable_skills", ""),
        "key_achievement": user_profile.get("key_achievement", ""),
        "current_role_summary": user_profile.get("current_role_summary", ""),
        "candidate_sector_or_role": user_profile.get("sector_or_role", ""),
        "impact_bullet_1": user_profile.get("impact_bullet_1", ""),
        "impact_bullet_2": user_profile.get("impact_bullet_2", ""),
        "impact_bullet_3": user_profile.get("impact_bullet_3", ""),
        "company_name": exa_context.company_name,
        "exa_recent_news_headline_1": exa_context.recent_news_headline_1 or "",
        "exa_recent_article_title": exa_context.recent_article_title or "",
        "exa_initiative_or_programme": exa_context.initiative_or_programme or "",
        "exa_theme_from_news": exa_context.theme_from_news or "",
        "exa_operational_initiative": exa_context.operational_initiative or "",
    }

    if extra:
        placeholders.update(extra)

    return render_template_with_placeholders(raw, placeholders)
