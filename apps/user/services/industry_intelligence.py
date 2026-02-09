"""
Industry Intelligence Service - Uses SharedIOLayer
=================================================
Provides industry analysis and market insights.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

root = Path(__file__).parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from shared.io_layer import get_io_layer


class IndustryIntelligence:
    """
    Industry analysis using SharedIOLayer.
    """

    def __init__(self):
        """Initialize with SharedIOLayer."""
        self.io = get_io_layer()

    def get_industry_overview(self, industry: str = None) -> Dict:
        """
        Get industry overview and statistics.

        Args:
            industry: Industry name (optional)

        Returns:
            Industry overview data
        """
        # Get all companies
        companies = self.io.get_companies()

        # Filter by industry if specified
        if industry:
            companies = [c for c in companies if c.get('industry') == industry]

        # Get all jobs
        jobs = self.io.get_jobs()

        # Calculate industry stats
        industries = {}
        for company in companies:
            ind = company.get('industry', 'Unknown')
            if ind not in industries:
                industries[ind] = {'companies': 0, 'jobs': 0}
            industries[ind]['companies'] += 1

        for job in jobs:
            company_name = job.get('company', '')
            # Find company industry
            company = next((c for c in companies if c.get('name') == company_name), None)
            if company:
                ind = company.get('industry', 'Unknown')
                if ind in industries:
                    industries[ind]['jobs'] += 1

        return {
            'industries': industries,
            'total_companies': len(companies),
            'total_jobs': len(jobs),
            'analysis_available': self.io.get_latest_analysis('industry') is not None
        }

    def get_trending_skills(self, industry: str = None) -> List[Dict]:
        """
        Get trending skills in industry.

        Args:
            industry: Industry name (optional)

        Returns:
            List of trending skills with counts
        """
        # Get all jobs
        jobs = self.io.get_jobs()

        # Get companies for industry filtering
        if industry:
            companies = self.io.get_companies({'industry': industry})
            company_names = [c.get('name') for c in companies]
            jobs = [j for j in jobs if j.get('company') in company_names]

        # Count skills
        skill_counts = {}
        for job in jobs:
            skills = job.get('required_skills', [])
            for skill in skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Convert to list and sort
        trending = [
            {'skill': skill, 'count': count}
            for skill, count in skill_counts.items()
        ]
        trending.sort(key=lambda x: x['count'], reverse=True)

        return trending[:20]  # Top 20
