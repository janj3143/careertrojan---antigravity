"""
Real-time Analytics Service
Reads actual data from ai_data_final folder and dashboard_data.json.

USAGE:
1. Import in admin_portal/pages/02_Analytics.py
2. Replace mock data section with real data calls
3. No database needed - uses existing JSON data files

DATA SOURCES:
- ai_data_final/parsed_resumes/*.json
- admin_portal/dashboard_data.json
- ai_data_final/companies/*.json
- ai_data_final/skills/*.json
- services/email_verification_service (if available)
- services/two_factor_auth_service (if available)
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import glob
import streamlit as st
import logging

class AnalyticsService:
    """
    Provides real-time analytics data from ai_data_final folder and JSON files.
    NO DATABASE REQUIRED - uses existing file-based data.
    """

    def __init__(self):
        """Initialize paths to data sources."""
        self.logger = logging.getLogger(__name__)
        # Determine base path (works from admin_portal or admin_portal/services)
        current_file = Path(__file__).resolve()

        # Try to find ai_data_final folder
        possible_paths = [
            current_file.parent.parent.parent / "ai_data_final",  # From services/
            current_file.parent.parent / "ai_data_final",  # From admin_portal/
            Path.cwd() / "ai_data_final",  # From current directory
            Path.cwd().parent / "ai_data_final",  # One level up
        ]

        self.ai_data_path = None
        for path in possible_paths:
            if path.exists():
                self.ai_data_path = path
                break

        # No demo/mock analytics. If not configured, operate in a disabled/no-op
        # state and return empty/unavailable results.
        self.disabled = not bool(self.ai_data_path)
        if self.disabled:
            self.logger.warning("Analytics not configured - analytics disabled")

        # Path to dashboard data
        self.dashboard_data_path = current_file.parent.parent / "dashboard_data.json"

        # Cache for performance
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = 60  # Cache for 60 seconds

    def _get_cached_or_load(self, key: str, loader_func):
        """Get cached data or load fresh if expired."""
        now = datetime.now()

        if key in self._cache:
            cache_time = self._cache_timestamp.get(key, now)
            if (now - cache_time).seconds < self._cache_ttl:
                return self._cache[key]

        # Load fresh data
        data = loader_func()
        self._cache[key] = data
        self._cache_timestamp[key] = now

        return data

    def _load_dashboard_data(self) -> Dict[str, Any]:
        """Load dashboard_data.json file."""
        try:
            if self.dashboard_data_path.exists():
                with open(self.dashboard_data_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading dashboard data: {str(e)}")

        return {
            "metrics": {},
            "analytics": {},
            "intelligence": {},
            "email_analytics": {}
        }

    def _count_json_files(self, folder: str) -> int:
        """Count JSON files in a folder."""
        if not self.ai_data_path:
            return 0

        folder_path = self.ai_data_path / folder
        if not folder_path.exists():
            return 0

        return len(list(folder_path.glob("*.json")))

    def _get_recent_files(self, folder: str, days: int = 7) -> List[Path]:
        """Get files modified in the last N days."""
        if not self.ai_data_path:
            return []

        folder_path = self.ai_data_path / folder
        if not folder_path.exists():
            return []

        cutoff_time = datetime.now() - timedelta(days=days)
        recent_files = []

        for file_path in folder_path.glob("*.json"):
            if datetime.fromtimestamp(file_path.stat().st_mtime) > cutoff_time:
                recent_files.append(file_path)

        return recent_files

    def get_user_metrics(self) -> Dict[str, Any]:
        """
        Get real-time user metrics from actual data files.

        Returns:
            Dict with user statistics from ai_data_final
        """
        def _load():
            if self.disabled or not self.ai_data_path:
                return {
                    'status': 'unavailable',
                    'error': 'ai_data_final not configured',
                    'total_users': 0,
                    'enriched_profiles': 0,
                    'new_today': 0,
                    'new_this_week': 0,
                    'active_users': 0,
                    'verified_users': 0,
                    'growth_rate': 0.0,
                    'verification_rate': 0.0
                }

            dashboard_data = self._load_dashboard_data()

            # Count parsed resumes (proxy for users)
            total_resumes = self._count_json_files("parsed_resumes")

            # Get recent resumes (last 7 days)
            recent_resumes = len(self._get_recent_files("parsed_resumes", days=7))
            recent_resumes_today = len(self._get_recent_files("parsed_resumes", days=1))

            # Try to get email verification data if available
            verified_count = 0
            try:
                from email_verification_service import get_email_verification_service
                email_service = get_email_verification_service()
                stats = email_service.get_verification_stats()
                verified_count = stats.get('verified_count', 0)
            except:
                # If email service not available, estimate from dashboard
                verified_count = dashboard_data.get('email_analytics', {}).get('verified_emails', 0)

            # Get intelligence data
            intelligence = dashboard_data.get('intelligence', {})
            enriched_candidates = intelligence.get('enriched_candidates', {}).get('data_points', 0)

            active_users_30d = len(self._get_recent_files("parsed_resumes", days=30))

            return {
                'total_users': total_resumes,
                'enriched_profiles': enriched_candidates,
                'new_today': recent_resumes_today,
                'new_this_week': recent_resumes,
                'active_users': active_users_30d,
                'verified_users': verified_count,
                'growth_rate': (recent_resumes / total_resumes * 100) if total_resumes > 0 else 0,
                'verification_rate': (verified_count / total_resumes * 100) if total_resumes > 0 else 0
            }

        return self._get_cached_or_load('user_metrics', _load)

    def get_subscription_metrics(self) -> Dict[str, Any]:
        """
        Get subscription and revenue metrics.
        NOTE: Real subscription data would come from payment processor.
        This provides estimates based on tier distribution.

        Returns:
            Dict with subscription statistics
        """
        def _load():
            # No estimates / demo data. Real subscription metrics must come from a payment processor.
            return {
                'status': 'unavailable',
                'error': 'Payment processor integration not configured (no Stripe/PayPal webhook data found).',
                'subscriptions_by_tier': {},
                'revenue_by_tier': {},
                'total_active_subscriptions': 0,
                'monthly_revenue': 0.0
            }

        return self._get_cached_or_load('subscription_metrics', _load)

    def get_ai_usage_metrics(self) -> Dict[str, Any]:
        """
        Get AI feature usage statistics from REAL data files.

        Returns:
            Dict with AI usage statistics from ai_data_final
        """
        def _load():
            if self.disabled or not self.ai_data_path:
                return {
                    'status': 'unavailable',
                    'error': 'ai_data_final not configured',
                    'total_analyses': 0,
                    'analyses_this_month': 0,
                    'analyses_this_week': 0,
                    'total_companies': 0,
                    'total_skills': 0,
                    'total_job_titles': 0,
                    'total_emails_extracted': 0,
                    'analyses_by_type': {},
                    'ai_features_usage': {},
                    'tokens_used_this_month': None,
                }

            dashboard_data = self._load_dashboard_data()

            # Total resume analyses (parsed resumes)
            total_analyses = self._count_json_files("parsed_resumes")

            # Recent analyses
            analyses_this_month = len(self._get_recent_files("parsed_resumes", days=30))
            analyses_this_week = len(self._get_recent_files("parsed_resumes", days=7))

            # Companies data
            total_companies = dashboard_data.get('intelligence', {}).get('enriched_companies', {}).get('data_points', 0)

            # Skills data
            total_skills = dashboard_data.get('metrics', {}).get('total_skills', 0)

            # Job titles
            job_titles_count = self._count_json_files("job_titles")

            # Email analytics
            total_emails = dashboard_data.get('email_analytics', {}).get('total_emails', 0)

            return {
                'total_analyses': total_analyses,
                'analyses_this_month': analyses_this_month,
                'analyses_this_week': analyses_this_week,
                'total_companies': total_companies,
                'total_skills': total_skills,
                'total_job_titles': job_titles_count,
                'total_emails_extracted': total_emails,
                'analyses_by_type': {
                    'resume_parse': analyses_this_month,
                    'skills_extraction': total_skills,
                    'company_enrichment': total_companies
                },
                'ai_features_usage': {
                    'resume_parsing': analyses_this_month,
                    'company_intelligence': total_companies,
                    'skills_mapping': total_skills
                },
                'tokens_used_this_month': None
            }

        return self._get_cached_or_load('ai_metrics', _load)

    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """
        Get data quality metrics from dashboard_data.json.

        Returns:
            Dict with data quality statistics
        """
        dashboard_data = self._load_dashboard_data()

        metrics = dashboard_data.get('metrics', {})
        analytics = dashboard_data.get('analytics', {})
        intelligence = dashboard_data.get('intelligence', {})

        return {
            'total_candidates': metrics.get('total_candidates', 0),
            'total_companies': metrics.get('total_companies', 0),
            'total_emails': metrics.get('total_emails', 0),
            'total_skills': metrics.get('total_skills', 0),
            'data_quality_score': analytics.get('data_quality_score', 0),
            'intelligence_categories': metrics.get('intelligence_categories', 0),
            'enriched_data_points': sum(
                cat.get('data_points', 0)
                for cat in intelligence.values()
            )
        }

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health metrics.

        Returns:
            Dict with system health statistics
        """
        try:
            # Check if ai_data_final is accessible
            ai_data_healthy = self.ai_data_path is not None and self.ai_data_path.exists()

            # Check dashboard data
            dashboard_healthy = self.dashboard_data_path.exists()

            # Try to check email service
            email_service_healthy = False
            try:
                from email_verification_service import get_email_verification_service
                email_service = get_email_verification_service()
                email_service_healthy = True
            except:
                pass

            # Try to check 2FA service
            twofa_service_healthy = False
            try:
                from two_factor_auth_service import get_2fa_service
                twofa_service = get_2fa_service()
                twofa_service_healthy = True
            except:
                pass

            return {
                'ai_data_accessible': ai_data_healthy,
                'dashboard_data_accessible': dashboard_healthy,
                'email_service_active': email_service_healthy,
                '2fa_service_active': twofa_service_healthy,
                'overall_health': 'Healthy' if (ai_data_healthy and dashboard_healthy) else 'Degraded'
            }

        except Exception as e:
            return {
                'ai_data_accessible': False,
                'dashboard_data_accessible': False,
                'email_service_active': False,
                '2fa_service_active': False,
                'overall_health': 'Error',
                'error': str(e)
            }

    def get_error_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent error logs (placeholder for future implementation).

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of error log entries
        """
        # TODO: Implement error logging system
        return []


# Singleton instance
_analytics_service = None

def get_analytics_service() -> AnalyticsService:
    """
    Get singleton instance of analytics service.

    Returns:
        AnalyticsService instance
    """
    global _analytics_service

    if _analytics_service is None:
        _analytics_service = AnalyticsService()

    return _analytics_service
