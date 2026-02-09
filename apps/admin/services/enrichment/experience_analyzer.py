from typing import List, Dict, Any
from datetime import datetime
import logging

class ExperienceAnalyzer:
    """
    Analyzer for calculating total years of experience from a list of experience entries.
    """
    @staticmethod
    def calculate_total_duration(experiences: List[Dict[str, Any]]) -> float:
        """
        Calculate total years of experience from start/end dates.
        Args:
            experiences: List of experience dicts, each with 'start_date' and 'end_date'.
        Returns:
            Total years of experience as a float.
        """
        import dateutil.parser
        total_months = 0
        for exp in experiences:
            try:
                start = exp.get('start_date')
                end = exp.get('end_date') or datetime.now().isoformat()
                start_dt = dateutil.parser.parse(start) if start else None
                end_dt = dateutil.parser.parse(end) if end else datetime.now()
                if start_dt:
                    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
                    total_months += max(0, months)
            except Exception as e:
                logging.warning(f"[ExperienceAnalyzer] Failed to parse dates for experience entry: {exp}. Error: {e}")
        return round(total_months / 12, 2) if total_months else float(len(experiences))
