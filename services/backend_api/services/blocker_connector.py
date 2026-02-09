"""
Application Blockers - Cross-Portal Bridge Service

Purpose: Share blocker detection and management across all three portals
- User Portal: Detect blockers during resume upload
- Admin Portal: Monitor blocker trends and effectiveness
- Mentor Portal: Guide mentorship focused on gap closure

Author: IntelliCV AI System
Date: November 15, 2025
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from services.backend_api.services.blocker.detector import BlockerDetector
from services.backend_api.services.blocker.service import BlockerService
from services.backend_api.db.connection import get_db

BLOCKER_SERVICES_AVAILABLE = True

class BlockerConnector:
    """
    Cross-portal bridge for Application Blockers system
    """

    def __init__(self):
        """Initialize blocker connector"""
        self.detector = BlockerDetector()
        # Service requires a DB session, which is typically passed in methods or context
        # For connector compatibility, we might need to handle this per-request
        self.service = None 

    def get_service(self, db_session):
        return BlockerService(db_session)


    # ========================================
    # USER PORTAL METHODS
    # ========================================

    def detect_blockers_for_user(
        self,
        jd_text: str,
        resume_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quick blocker detection for resume upload pages

        Args:
            jd_text: Job description text
            resume_data: Parsed resume {skills, experience_years, certifications, education_level}

        Returns:
            {
                'total_blockers': int,
                'critical_count': int,
                'blockers': [...],
                'overall_impact': float,
                'addressable_count': int
            }
        """
        if not self.detector:
            return {
                'total_blockers': 0,
                'critical_count': 0,
                'major_count': 0,
                'moderate_count': 0,
                'minor_count': 0,
                'blockers': [],
                'overall_impact': 0.0,
                'addressable_count': 0,
                'error': 'Blocker detection service unavailable'
            }

        try:
            return self.detector.detect_blockers(jd_text, resume_data)
        except Exception as e:
            return {
                'total_blockers': 0,
                'critical_count': 0,
                'blockers': [],
                'overall_impact': 0.0,
                'addressable_count': 0,
                'error': str(e)
            }

    def get_improvement_suggestions(
        self,
        blocker: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get improvement strategies for a blocker

        Args:
            blocker: Single blocker dictionary

        Returns:
            List of improvement strategies
        """
        if not self.detector:
            return []

        try:
            return self.detector.suggest_improvements(blocker)
        except Exception as e:
            print(f"Error getting improvement suggestions: {e}")
            return []

    def generate_interview_script(
        self,
        blocker: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate objection handling script for interview

        Args:
            blocker: Single blocker dictionary

        Returns:
            {
                'opening': str,
                'acknowledgment': str,
                'mitigation': str,
                'commitment': str,
                'value_proposition': str
            }
        """
        if not self.detector:
            return {}

        try:
            return self.detector.generate_objection_script(blocker)
        except Exception as e:
            print(f"Error generating objection script: {e}")
            return {}

    # ========================================
    # ADMIN PORTAL METHODS
    # ========================================

    def get_blocker_analytics(
        self,
        user_id: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get blocker analytics for admin dashboard

        Args:
            user_id: Optional filter by user
            date_range: Optional (start_date, end_date) tuple

        Returns:
            Analytics summary
        """
        # This would connect to blocker_service for database queries
        return {
            'total_blockers_detected': 0,
            'most_common_blockers': [],
            'average_resolution_time': 0,
            'resolution_success_rate': 0.0,
            'interview_rate_improvement': 0.0
        }

    # ========================================
    # MENTOR PORTAL METHODS
    # ========================================

    def get_mentee_blockers(
        self,
        mentee_id: str,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """
        Get mentee's current blockers for mentor guidance

        Args:
            mentee_id: Mentee user ID
            status: Filter by status (active, in_progress, resolved)

        Returns:
            List of blocker dictionaries
        """
        if not self.service:
            return []

        try:
            return self.service.get_user_blockers(mentee_id, status=status)
        except Exception as e:
            print(f"Error getting mentee blockers: {e}")
            return []

    def get_blocker_mentorship_guidance(
        self,
        blocker: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate mentor guidance for addressing a blocker

        Args:
            blocker: Single blocker dictionary

        Returns:
            {
                'focus_areas': [...],
                'suggested_activities': [...],
                'milestones': [...],
                'resources': [...]
            }
        """
        # This would be implemented in blocker_mentorship_integration.py
        return {
            'focus_areas': [],
            'suggested_activities': [],
            'milestones': [],
            'resources': []
        }

    # ========================================
    # HELPER METHODS
    # ========================================

    def is_available(self) -> bool:
        """Check if blocker services are available"""
        return BLOCKER_SERVICES_AVAILABLE and self.detector is not None

    def get_status(self) -> Dict[str, Any]:
        """Get connector status for debugging"""
        return {
            'services_available': BLOCKER_SERVICES_AVAILABLE,
            'detector_loaded': self.detector is not None,
            'service_loaded': self.service is not None,
            'ready': self.is_available()
        }


# ========================================
# SINGLETON INSTANCE
# ========================================

_blocker_connector_instance = None

def get_blocker_connector() -> BlockerConnector:
    """Get singleton blocker connector instance"""
    global _blocker_connector_instance
    if _blocker_connector_instance is None:
        _blocker_connector_instance = BlockerConnector()
    return _blocker_connector_instance


# ========================================
# CONVENIENCE FUNCTIONS FOR PAGES
# ========================================

def detect_blockers_quick(jd_text: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick blocker detection for page imports"""
    connector = get_blocker_connector()
    return connector.detect_blockers_for_user(jd_text, resume_data)


def get_blocker_improvements(blocker: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get improvement suggestions for page imports"""
    connector = get_blocker_connector()
    return connector.get_improvement_suggestions(blocker)


def generate_objection_script(blocker: Dict[str, Any]) -> Dict[str, str]:
    """Generate objection script for page imports"""
    connector = get_blocker_connector()
    return connector.generate_interview_script(blocker)


# ========================================
# EXAMPLE USAGE
# ========================================

if __name__ == "__main__":
    # Test the connector
    connector = get_blocker_connector()

    print(f"Blocker Connector Status: {connector.get_status()}")

    if connector.is_available():
        # Test detection
        jd_text = "Senior ML Engineer with 5+ years Python, AWS experience required"
        resume_data = {
            'skills': ['Python', 'TensorFlow'],
            'experience_years': 3,
            'certifications': [],
            'education_level': 'bachelor',
            'has_leadership': False
        }

        result = connector.detect_blockers_for_user(jd_text, resume_data)
        print(f"\nDetected {result['total_blockers']} blockers")
        print(f"Critical: {result['critical_count']}")
        print(f"Overall Impact: {result['overall_impact']:.1f}/10")
