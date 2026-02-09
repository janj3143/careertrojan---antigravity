from typing import List
import re

class AchievementAnalyzer:
    """
    Analyzer for extracting achievements with measurable impact.
    """
    @staticmethod
    def extract_impact(achievements: List[str]) -> List[str]:
        """
        Extract achievements that mention measurable impact (e.g., %, $).
        Args:
            achievements: List of achievement strings.
        Returns:
            List of achievements with measurable impact.
        """
        impact_phrases: List[str] = []
        for ach in achievements:
            try:
                match = re.search(r'(\d+%|\$\d+[kKmM]?|increased|decreased|reduced|improved)', ach)
                if match:
                    impact_phrases.append(ach)
            except Exception as e:
                logging.warning(f"[AchievementAnalyzer] Error analyzing achievement '{ach}': {e}")
        return impact_phrases
