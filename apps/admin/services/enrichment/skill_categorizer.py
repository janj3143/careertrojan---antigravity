from typing import List, Dict

class SkillCategorizer:
    """
    Categorizes skills into predefined categories based on config keywords.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Configuration dict with 'skill_categories' mapping.
        """
        self.categories: Dict[str, List[str]] = config.get('skill_categories', {})

    def categorize(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize a list of skills into categories defined in config.
        Args:
            skills: List of skill strings.
        Returns:
            Dict mapping category names to lists of skills.
        """
        categorized: Dict[str, List[str]] = {cat: [] for cat in self.categories}
        uncategorized: List[str] = []
        for skill in skills:
            found = False
            for cat, keywords in self.categories.items():
                try:
                    if any((kw.lower() in skill.lower()) for kw in keywords):
                        categorized[cat].append(skill)
                        found = True
                        break
                except Exception as e:
                    logging.warning(f"[SkillCategorizer] Error categorizing skill '{skill}' in category '{cat}': {e}")
            if not found:
                uncategorized.append(skill)
        categorized['Other'] = uncategorized
        return categorized
