"""
User Data Service - Refactored to use SharedIOLayer
===================================================
Central service that loads user-specific data via SharedIOLayer.

NO HARDCODED PATHS - All data access goes through shared.io_layer
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add shared to path
root = Path(__file__).parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from shared.io_layer import get_io_layer


class UserDataService:
    """
    Load user-specific data using SharedIOLayer.
    
    Usage:
        from services.user_data_service import UserDataService
        
        service = UserDataService()
        user_data = service.get_user_data(st.session_state.user_id)
    """
    
    def __init__(self):
        """Initialize service with SharedIOLayer."""
        self.io = get_io_layer()
    
    def get_user_data(self, user_id: str) -> Dict:
        """
        Get complete data for a specific user.
        
        Args:
            user_id: User identifier (e.g., 'candidate_001' or email)
            
        Returns:
            Dict with user profile, analysis, peers, jobs, companies
        """
        # Get user's candidate profile
        profile = self.io.get_candidate_data(user_id)
        
        # Get latest analysis for this user
        latest_analysis = self.io.get_latest_analysis('candidate')
        
        # Get peer candidates for comparison (first 10)
        peers = self.io.get_all_candidates(limit=10)
        
        # Get relevant jobs (all for now, could add filtering)
        jobs = self.io.get_jobs(limit=50)
        
        # Get companies
        companies = self.io.get_companies(limit=50)
        
        return {
            'profile': profile,
            'latest_analysis': latest_analysis,
            'peers': peers,
            'jobs': jobs,
            'companies': companies,
            'has_data': profile is not None
        }
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get just the user profile."""
        return self.io.get_candidate_data(user_id)
    
    def get_user_analysis(self, user_id: str) -> Optional[Dict]:
        """Get latest analysis for user."""
        return self.io.get_latest_analysis('candidate')
    
    def get_peer_candidates(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get peer candidates for comparison.
        
        Args:
            user_id: Current user ID
            limit: Number of peers to return
            
        Returns:
            List of candidate profiles (excluding current user)
        """
        all_candidates = self.io.get_all_candidates()
        
        # Filter out current user
        peers = [c for c in all_candidates if c.get('user_id') != user_id]
        
        return peers[:limit]
    
    def get_matched_jobs(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Get jobs matched to user's profile.
        
        Args:
            user_id: User ID
            limit: Maximum jobs to return
            
        Returns:
            List of matched jobs
        """
        # Get user profile
        profile = self.io.get_candidate_data(user_id)
        if not profile:
            return self.io.get_jobs(limit=limit)
        
        # Get all jobs
        all_jobs = self.io.get_jobs()
        
        # Simple matching (can be enhanced with AI)
        user_skills = profile.get('profile', {}).get('skills', [])
        user_location = profile.get('preferences', {}).get('target_locations', [])
        
        matched = []
        for job in all_jobs:
            # Check location match
            if user_location and job.get('location') in user_location:
                matched.append(job)
            # Check skill match
            elif user_skills:
                job_skills = job.get('required_skills', [])
                if any(skill in job_skills for skill in user_skills):
                    matched.append(job)
        
        # If no matches, return all jobs
        if not matched:
            matched = all_jobs
        
        return matched[:limit]
    
    def save_user_data(self, user_id: str, user_data: Dict) -> bool:
        """
        Save/update user data.
        
        Args:
            user_id: User ID
            user_data: Complete user profile data
            
        Returns:
            Success status
        """
        # Ensure user_id is set
        if 'user_id' not in user_data:
            user_data['user_id'] = user_id
        
        return self.io.save_candidate_data(user_data)
