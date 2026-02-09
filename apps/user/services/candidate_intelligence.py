"""
Candidate Intelligence Service - Uses SharedIOLayer
==================================================
Provides AI-powered candidate analysis and insights.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

root = Path(__file__).parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from shared.io_layer import get_io_layer


class CandidateIntelligence:
    """
    AI-powered candidate analysis using SharedIOLayer.
    """

    def __init__(self):
        """Initialize with SharedIOLayer."""
        self.io = get_io_layer()

    def analyze_candidate(self, user_id: str) -> Optional[Dict]:
        """
        Analyze candidate profile and return insights.

        Args:
            user_id: Candidate ID

        Returns:
            Analysis results with insights, recommendations
        """
        # Get candidate data
        candidate = self.io.get_candidate_data(user_id)
        if not candidate:
            return None

        # Get latest analysis from admin backend
        latest_analysis = self.io.get_latest_analysis('candidate')

        # Combine candidate data with analysis
        return {
            'candidate': candidate,
            'analysis': latest_analysis,
            'insights': self._generate_insights(candidate, latest_analysis)
        }

    def _generate_insights(self, candidate: Dict, analysis: Optional[Dict]) -> List[str]:
        """Generate insights from candidate data and analysis."""
        insights = []

        # Basic insights from profile
        profile = candidate.get('profile', {})
        experience = profile.get('experience_years', 0)
        skills = profile.get('skills', [])

        if experience > 10:
            insights.append("Highly experienced professional")
        elif experience > 5:
            insights.append("Mid-level professional")
        else:
            insights.append("Early-career professional")

        if len(skills) > 10:
            insights.append("Diverse skill set")

        # Add insights from analysis if available
        if analysis and 'results' in analysis:
            results = analysis.get('results', {})
            if 'insights' in results:
                insights.extend(results['insights'])

        return insights

    def compare_candidates(self, user_id: str, peer_ids: List[str] = None) -> Dict:
        """
        Compare candidate against peers.

        Args:
            user_id: Target candidate ID
            peer_ids: List of peer IDs (optional, will get automatically)

        Returns:
            Comparison results
        """
        # Get target candidate
        candidate = self.io.get_candidate_data(user_id)
        if not candidate:
            return {}

        # Get peers
        if not peer_ids:
            all_candidates = self.io.get_all_candidates()
            peers = [c for c in all_candidates if c.get('user_id') != user_id][:5]
        else:
            peers = [self.io.get_candidate_data(pid) for pid in peer_ids]
            peers = [p for p in peers if p is not None]

        # Simple comparison
        candidate_profile = candidate.get('profile', {})
        candidate_exp = candidate_profile.get('experience_years', 0)
        candidate_skills = len(candidate_profile.get('skills', []))

        peer_exp_avg = sum(p.get('profile', {}).get('experience_years', 0) for p in peers) / len(peers) if peers else 0
        peer_skills_avg = sum(len(p.get('profile', {}).get('skills', [])) for p in peers) / len(peers) if peers else 0

        return {
            'candidate': candidate,
            'peers': peers,
            'comparison': {
                'experience_vs_peers': 'above' if candidate_exp > peer_exp_avg else 'below',
                'skills_vs_peers': 'above' if candidate_skills > peer_skills_avg else 'below',
                'peer_count': len(peers)
            }
        }
