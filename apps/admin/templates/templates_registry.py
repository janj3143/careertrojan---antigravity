from pathlib import Path
from enum import Enum
from typing import List, Dict

TEMPLATES_ROOT = Path(__file__).resolve().parent

class TemplateCategory(str, Enum):
    CV = "cv"
    INTERVIEW_ACCEPT = "interview_acceptance"
    FOLLOW_UP = "follow_up"
    SPECULATIVE = "speculative"


def list_templates(category: TemplateCategory) -> List[Path]:
    """Return all template files for a category."""
    base = TEMPLATES_ROOT / category.value
    if not base.exists():
        return []
    return sorted(p for p in base.iterdir() if p.is_file() and p.suffix in {'.md', '.txt', '.docx'})


def get_template_by_slug(category: TemplateCategory, slug: str) -> Path | None:
    """Find a template whose stem starts with the given slug (e.g. '01_classic')."""
    for p in list_templates(category):
        if p.stem.startswith(slug):
            return p
    return None


def load_template_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def describe_templates() -> Dict[str, list]:
    """Return a JSON-serialisable description for admin UI / APIs."""
    summary: Dict[str, list] = {}
    for cat in TemplateCategory:
        summary[cat.value] = [p.name for p in list_templates(cat)]
    return summary
