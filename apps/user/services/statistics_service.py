"""
Statistics Service - Real-time User and System Statistics
==========================================================
Provides dynamic statistics for the home page and dashboard.
Uses SharedIOLayer for data access - NO HARDCODED PATHS.
"""

import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta

# Add shared to path
root = Path(__file__).parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from shared.io_layer import get_io_layer


class StatisticsService:
    """
    Real-time statistics for user portal displays.

    Usage:
        from services.statistics_service import get_statistics

        stats = get_statistics()
        st.metric("Total Users", stats['total_users'])
    """

    def __init__(self):
        """Initialize service with SharedIOLayer."""
        self.io = get_io_layer()

    def get_total_users(self) -> int:
        """Get total number of registered users."""
        try:
            # Count all candidates in the system
            all_candidates = self.io.get_all_candidates()
            return len(all_candidates) if all_candidates else 0
        except Exception as e:
            print(f"Error counting users: {e}")
            return 0

    def get_total_resumes(self) -> int:
        """Get total number of resumes processed."""
        try:
            # Count all candidate profiles (each has uploaded resume)
            all_candidates = self.io.get_all_candidates()
            # Count only those with resume data
            with_resume = [c for c in all_candidates if c.get('resume_text') or c.get('parsed_resume')]
            return len(with_resume)
        except Exception as e:
            print(f"Error counting resumes: {e}")
            return 0

    def get_total_analyses(self) -> int:
        """Get total number of analyses performed."""
        try:
            # Count all candidates with analysis data
            all_candidates = self.io.get_all_candidates()
            with_analysis = [c for c in all_candidates if c.get('analysis') or c.get('match_scores')]
            return len(with_analysis)
        except Exception as e:
            print(f"Error counting analyses: {e}")
            return 0

    def get_total_jobs(self) -> int:
        """Get total number of jobs in database."""
        try:
            jobs = self.io.get_jobs(limit=10000)  # Get all
            return len(jobs) if jobs else 0
        except Exception as e:
            print(f"Error counting jobs: {e}")
            return 0

    def get_total_companies(self) -> int:
        """Get total number of companies in database."""
        try:
            companies = self.io.get_companies(limit=10000)  # Get all
            return len(companies) if companies else 0
        except Exception as e:
            print(f"Error counting companies: {e}")
            return 0

    def get_active_users_today(self) -> int:
        """Get number of users active today."""
        try:
            # This would require session tracking - return estimate for now
            # TODO: Implement proper session tracking
            total = self.get_total_users()
            # Estimate 10% daily active users
            return max(1, int(total * 0.1))
        except Exception as e:
            print(f"Error counting active users: {e}")
            return 0

    def get_premium_users(self) -> int:
        """Get number of premium tier users."""
        try:
            all_candidates = self.io.get_all_candidates()
            premium = [c for c in all_candidates if c.get('tier') in ['monthly_pro', 'annual_pro', 'enterprise_pro']]
            return len(premium)
        except Exception as e:
            print(f"Error counting premium users: {e}")
            return 0

    def get_all_statistics(self) -> Dict:
        """
        Get all statistics at once for dashboard display.

        Returns:
            Dict with all statistics
        """
        return {
            'total_users': self.get_total_users(),
            'total_resumes': self.get_total_resumes(),
            'total_analyses': self.get_total_analyses(),
            'total_jobs': self.get_total_jobs(),
            'total_companies': self.get_total_companies(),
            'active_today': self.get_active_users_today(),
            'premium_users': self.get_premium_users(),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# Singleton instance
_stats_service = None

def get_statistics() -> Dict:
    """
    Get all statistics (singleton pattern for caching).

    Returns:
        Dict with current system statistics
    """
    global _stats_service
    if _stats_service is None:
        _stats_service = StatisticsService()

    return _stats_service.get_all_statistics()


def format_stat_number(num: int) -> str:
    """
    Format statistics number for display.

    Args:
        num: Raw number

    Returns:
        Formatted string (e.g., "1,234" or "5,000+")
    """
    if num >= 1000:
        # Round to nearest hundred for large numbers
        rounded = (num // 100) * 100
        return f"{rounded:,}+"
    else:
        return f"{num:,}"
