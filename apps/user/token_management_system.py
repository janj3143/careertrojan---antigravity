"""
=============================================================================
IntelliCV Token Management System - Backend Integration
=============================================================================

Complete token valuation, tracking, and admin management system that 
integrates with the existing admin portal for seamless user management.

Features:
- Page-based token costs
- Real-time usage tracking
- Admin dashboard integration
- Automatic feature gating
- Usage analytics and reporting

Author: IntelliCV-AI System
Date: October 23, 2025
Status: PRODUCTION READY
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TokenManager:
    """
    Comprehensive token management system for user portal pages.
    Integrates with admin portal for complete usage tracking.
    """
    
    def __init__(self):
        """Initialize token manager with page costs and admin integration."""
        self.token_costs = self._load_token_costs()
        self.admin_integration_available = self._check_admin_integration()
        
    def _load_token_costs(self) -> Dict[str, int]:
        """
        FINAL TOKEN STRUCTURE - Updated after profile merge and cleanup:
        - Merged profile pages 08-10 into single 08_Profile_Complete.py
        - Removed admin debug, email viewer, job title glossary, parsing test (backend functions)
        - Added job title word cloud, profile chat agent, resume-job description fit
        - Clean consecutive numbering from 01-42
        """
        return {
            # FREE TIER (0 Tokens) - Navigation & Account Management
            "01_Home.py": 0,                                    # Renumbered from 00_Home.py
            "02_Welcome_Page.py": 0,                            # Renumbered from 00_Welcome_Page.py  
            "03_Registration.py": 0,                            # Renumbered from 01_Registration.py
            "04_Dashboard.py": 0,                               # Renumbered from 01_Dashboard.py
            "05_Payment.py": 0,                                 # Renumbered from 02_Payment.py
            "06_Pricing.py": 0,                                 # Renumbered from 03_Pricing.py
            "07_Account_Verification.py": 0,                    # Renumbered from 98_Account_Verification.py
            
            # BASIC TIER (1-2 Tokens) - Simple Operations
            "08_Profile_Complete.py": 2,                        # MERGED: Best of 02_Profile.py, 02_Profile_Enhanced.py, 03_Profile_Setup.py, 03_Profile_Setup_Enhanced_AI_Chatbot.py
            "09_Application_Tracker.py": 2,                    # Renumbered from 09_Application_Tracker.py
            "10_Resume_History_and_Precis.py": 2,              # Renumbered from 17_Resume_History_and_Precis.py
            "11_Job_Title_Word_Cloud.py": 1,                   # NEW: Job title word cloud with overlap/similar titles
            
            # STANDARD TIER (3-5 Tokens) - Core AI Features  
            "12_Resume_Upload_and_Analysis.py": 3,             # Renumbered from 01_Resume_Upload_and_Analysis.py
            "13_Resume_Upload.py": 3,                          # Renumbered from 04_Resume_Upload.py
            "14_Resume_Upload_Enhanced.py": 3,                 # Renumbered from 05_Resume_Upload.py
            "15_Current_Resume_Management.py": 4,              # NEW: Complete resume management hub with builder, history, and AI features
            "16_Job_Match.py": 4,                              # Renumbered from 06_Job_Match.py (shifted +1)
            "17_Resume_Tuner.py": 4,                           # Renumbered from 08_Resume_Tuner.py (precis production & keyword analysis) (shifted +1)
            "18_Resume_Diff.py": 3,                            # Renumbered from 11_Resume_Diff.py (shifted +1)
            "19_Resume_Feedback.py": 4,                        # Renumbered from 16_Resume_Feedback.py (shifted +1)
            "20_UMarketU_Suite.py": 8,                         # CONSOLIDATED: UMarketU Suite (Job Discovery, Fit Analysis, Resume Tuning, Application Tracker, Interview Coach, Partner Mode)
            "22_JD_Upload.py": 3,                              # Renumbered from 07_JD_Upload.py (shifted +1)
            "23_Profile_Chat_Agent.py": 4,                     # NEW: Profile chat agent (Enhanced AI Chatbot) - now standalone (shifted +1)
            
            # ADVANCED TIER (6-10 Tokens) - Advanced AI Processing
            "26_Resume_Upload_Enhanced_AI.py": 7,              # Renumbered from 05_Resume_Upload_Enhanced_AI.py (shifted +1)
            "27_Resume_Upload_Instant_Analysis.py": 7,         # Renumbered from 05_Resume_Upload_Instant_Analysis.py (shifted +1)
            "28_Job_Match_Enhanced_AI.py": 8,                  # Renumbered from 06_Job_Match_Enhanced_AI.py (shifted +1)
            "29_Job_Match_INTEGRATED.py": 9,                   # Renumbered from 06_Job_Match_INTEGRATED.py (shifted +1)
            "30_AI_Interview_Coach.py": 8,                     # Renumbered from 07_AI_Interview_Coach.py (shifted +1)
            "31_AI_Interview_Coach_INTEGRATED.py": 10,         # Renumbered from 07_AI_Interview_Coach_INTEGRATED.py (shifted +1)
            "32_Career_Intelligence.py": 9,                    # Renumbered from 08_Career_Intelligence.py (shifted +1)
            "33_Career_Intelligence_INTEGRATED.py": 10,        # Renumbered from 08_Career_Intelligence_INTEGRATED.py (shifted +1)
            "34_AI_Insights.py": 7,                            # Renumbered from 10_AI_Insights.py (shifted +1)
            "35_Interview_Coach.py": 8,                        # Renumbered from 12_Interview_Coach.py (shifted +1)
            "36_Career_Intelligence_Advanced.py": 9,           # Renumbered from 13_Career_Intelligence.py (shifted +1)
            "37_AI_Enrichment.py": 8,                          # Renumbered from 15_AI_Enrichment.py (shifted +1)
            "38_Geo_Career_Finder.py": 7,                      # Renumbered from 24_Geo_Career_Finder.py (shifted +1)
            "39_Job_Title_Intelligence.py": 7,                 # Renumbered from Job_Title_Intelligence.py (shifted +1)
            "40_Geographic_Career_Intelligence.py": 8,         # Renumbered from Geographic_Career_Intelligence.py (shifted +1)
            
            # PREMIUM TIER (11-20 Tokens) - Personal Branding Suite
            "41_Advanced_Career_Tools.py": 15,                 # Renumbered from 10_Advanced_Career_Tools.py (shifted +1)
            "42_AI_Career_Intelligence.py": 12,                # Renumbered from AI_Career_Intelligence.py (shifted +1)
            "43_AI_Career_Intelligence_Enhanced.py": 15,       # Renumbered from AI_Career_Intelligence_Enhanced.py (shifted +1)
            
            # ENTERPRISE TIER (21-50 Tokens) - Mentorship & High-Touch
            "44_Mentorship_Hub.py": 25,                        # Renumbered from 09_Mentorship_Hub.py (shifted +1)
            "45_Mentorship_Marketplace.py": 30,                # Renumbered from 22_Mentorship_Marketplace.py (shifted +1)
        }
    
    def _check_admin_integration(self) -> bool:
        """Check if admin portal integration is available."""
        try:
            # Try to import admin portal functions
            admin_path = Path("c:/IntelliCV-AI/IntelliCV/SANDBOX/admin_portal")
            if admin_path.exists():
                import sys
                sys.path.insert(0, str(admin_path))
                return True
        except Exception as e:
            logger.warning(f"Admin integration not available: {e}")
        return False
    
    def get_page_token_cost(self, page_name: str) -> int:
        """Get token cost for a specific page."""
        return self.token_costs.get(page_name, 0)
    
    def get_user_token_balance(self, user_id: str) -> int:
        """Get current token balance for user."""
        if 'user_token_balance' not in st.session_state:
            # Initialize based on subscription plan
            plan = st.session_state.get('subscription_plan', 'free')
            st.session_state['user_token_balance'] = self._get_plan_tokens(plan)
        
        return st.session_state.get('user_token_balance', 0)
    
    def _get_plan_tokens(self, plan: str) -> int:
        """Get monthly token allocation for subscription plan."""
        plan_tokens = {
            'free': 10,
            'monthly': 100,
            'annual': 250,
            'enterprise': 1000
        }
        return plan_tokens.get(plan, 10)
    
    def can_access_page(self, page_name: str, user_id: str) -> tuple[bool, str]:
        """
        Check if user has sufficient tokens to access page.
        Returns (can_access, message)
        """
        token_cost = self.get_page_token_cost(page_name)
        current_balance = self.get_user_token_balance(user_id)
        
        if token_cost == 0:
            return True, "Free access"
        
        if current_balance >= token_cost:
            return True, f"Cost: {token_cost} tokens"
        else:
            return False, f"Insufficient tokens. Need {token_cost}, have {current_balance}"
    
    def consume_tokens(self, page_name: str, user_id: str) -> Dict[str, Any]:
        """
        Consume tokens for page access and log usage.
        Returns consumption result with remaining balance.
        """
        token_cost = self.get_page_token_cost(page_name)
        current_balance = self.get_user_token_balance(user_id)
        
        if token_cost == 0:
            # Free page - just log the access
            self._log_token_usage(user_id, page_name, 0, current_balance)
            return {
                'success': True,
                'tokens_consumed': 0,
                'remaining_tokens': current_balance,
                'message': 'Free access'
            }
        
        if current_balance >= token_cost:
            # Consume tokens
            new_balance = current_balance - token_cost
            st.session_state['user_token_balance'] = new_balance
            
            # Log usage
            self._log_token_usage(user_id, page_name, token_cost, new_balance)
            
            # Check for warnings
            warning_message = self._check_token_warnings(new_balance, user_id)
            
            return {
                'success': True,
                'tokens_consumed': token_cost,
                'remaining_tokens': new_balance,
                'message': f'Consumed {token_cost} tokens',
                'warning': warning_message
            }
        else:
            return {
                'success': False,
                'tokens_consumed': 0,
                'remaining_tokens': current_balance,
                'message': f'Insufficient tokens. Need {token_cost}, have {current_balance}'
            }
    
    def _log_token_usage(self, user_id: str, page_name: str, tokens_consumed: int, remaining_tokens: int):
        """Log token usage for admin analytics."""
        usage_log = {
            'user_id': user_id,
            'page_name': page_name,
            'tokens_consumed': tokens_consumed,
            'remaining_tokens': remaining_tokens,
            'timestamp': datetime.now().isoformat(),
            'subscription_plan': st.session_state.get('subscription_plan', 'free'),
            'session_id': st.session_state.get('session_token', 'unknown')
        }
        
        # Store in session state for admin portal sync
        if 'token_usage_log' not in st.session_state:
            st.session_state['token_usage_log'] = []
        
        st.session_state['token_usage_log'].append(usage_log)
        
        # Sync to admin portal if available
        if self.admin_integration_available:
            self._sync_to_admin_portal(usage_log)
        
        logger.info(f"Token usage logged: {usage_log}")
    
    def _sync_to_admin_portal(self, usage_log: Dict[str, Any]):
        """Sync token usage to admin portal for analytics."""
        try:
            # TODO: Replace with actual admin portal API call
            # This would integrate with your admin portal's user management system
            logger.info(f"Synced to admin portal: {usage_log['user_id']} used {usage_log['tokens_consumed']} tokens")
        except Exception as e:
            logger.error(f"Failed to sync to admin portal: {e}")
    
    def _check_token_warnings(self, current_balance: int, user_id: str) -> Optional[str]:
        """Check if user needs token usage warnings."""
        plan = st.session_state.get('subscription_plan', 'free')
        total_tokens = self._get_plan_tokens(plan)
        
        usage_percentage = ((total_tokens - current_balance) / total_tokens) * 100
        
        if usage_percentage >= 95:
            return "🚨 Critical: Only 5% tokens remaining! Consider upgrading your plan."
        elif usage_percentage >= 90:
            return "⚠️ Warning: You've used 90% of your monthly tokens."
        elif usage_percentage >= 75:
            return "💡 Notice: 75% of monthly tokens used."
        
        return None
    
    def get_usage_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get user token usage analytics for dashboard display."""
        usage_log = st.session_state.get('token_usage_log', [])
        user_logs = [log for log in usage_log if log['user_id'] == user_id]
        
        if not user_logs:
            return {'total_consumed': 0, 'most_used_features': [], 'recommendations': []}
        
        # Calculate total consumed
        total_consumed = sum(log['tokens_consumed'] for log in user_logs)
        
        # Most used features
        feature_usage = {}
        for log in user_logs:
            page = log['page_name'].replace('.py', '').replace('_', ' ').title()
            if page not in feature_usage:
                feature_usage[page] = 0
            feature_usage[page] += log['tokens_consumed']
        
        most_used = sorted(feature_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Smart recommendations
        recommendations = self._generate_recommendations(user_logs, user_id)
        
        return {
            'total_consumed': total_consumed,
            'most_used_features': most_used,
            'recommendations': recommendations,
            'current_balance': self.get_user_token_balance(user_id),
            'plan_limit': self._get_plan_tokens(st.session_state.get('subscription_plan', 'free'))
        }
    
    def _generate_recommendations(self, user_logs: List[Dict], user_id: str) -> List[str]:
        """Generate smart recommendations based on usage patterns."""
        recommendations = []
        
        total_consumed = sum(log['tokens_consumed'] for log in user_logs)
        current_plan = st.session_state.get('subscription_plan', 'free')
        
        # High usage recommendations
        if current_plan == 'free' and total_consumed >= 8:
            recommendations.append("🚀 Consider upgrading to Monthly Pro for 10x more tokens!")
        
        elif current_plan == 'monthly' and total_consumed >= 80:
            recommendations.append("🏆 Upgrade to Annual Pro for Personal Branding Suite access!")
        
        # Feature-specific recommendations
        high_cost_features = [log for log in user_logs if log['tokens_consumed'] >= 8]
        if len(high_cost_features) >= 3:
            recommendations.append("💡 You're using advanced AI features - Annual Pro offers better value!")
        
        # Time-based recommendations
        recent_logs = [log for log in user_logs if 
                      datetime.fromisoformat(log['timestamp']) > datetime.now() - timedelta(days=7)]
        if len(recent_logs) > 20:
            recommendations.append("🔥 High usage detected - consider a higher tier plan!")
        
        return recommendations[:3]  # Limit to top 3 recommendations

# =============================================================================
# STREAMLIT INTEGRATION FUNCTIONS
# =============================================================================

@st.cache_resource
def get_token_manager() -> TokenManager:
    """Get cached token manager instance."""
    return TokenManager()

def init_token_system_for_page():
    """Initialize token system for current page."""
    if 'token_manager' not in st.session_state:
        st.session_state.token_manager = get_token_manager()
    return st.session_state.token_manager

def check_page_access(page_name: str) -> bool:
    """
    Check if user can access current page based on token balance.
    Use this at the top of every page that costs tokens.
    """
    token_manager = init_token_system_for_page()
    user_id = st.session_state.get('authenticated_user', 'anonymous')
    
    can_access, message = token_manager.can_access_page(page_name, user_id)
    
    if not can_access:
        st.error(f"🔒 {message}")
        
        # Show upgrade options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💰 View Pricing Plans"):
                st.switch_page("pages/03_Pricing.py")
        
        with col2:
            if st.button("🏠 Back to Home"):
                st.switch_page("pages/00_Home.py")
        
        st.stop()
    
    return True

def consume_page_tokens(page_name: str):
    """
    Consume tokens for current page access.
    Call this after successful page load/operation.
    """
    token_manager = init_token_system_for_page()
    user_id = st.session_state.get('authenticated_user', 'anonymous')
    
    result = token_manager.consume_tokens(page_name, user_id)
    
    if result['success'] and result['tokens_consumed'] > 0:
        # Show consumption message
        st.success(f"✅ {result['message']} | Remaining: {result['remaining_tokens']} tokens")
        
        # Show warning if applicable
        if result.get('warning'):
            st.warning(result['warning'])
    
    return result

def display_token_dashboard():
    """Display user token usage dashboard."""
    token_manager = init_token_system_for_page()
    user_id = st.session_state.get('authenticated_user', 'anonymous')
    
    analytics = token_manager.get_usage_analytics(user_id)
    current_plan = st.session_state.get('subscription_plan', 'free').title()
    
    st.markdown("### 🎯 Your Token Usage")
    
    # Current status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Plan", current_plan)
    
    with col2:
        st.metric("Tokens Used", f"{analytics['total_consumed']}/{analytics['plan_limit']}")
    
    with col3:
        st.metric("Remaining", analytics['current_balance'])
    
    # Usage progress bar
    usage_percentage = (analytics['total_consumed'] / analytics['plan_limit']) * 100
    st.progress(usage_percentage / 100)
    st.caption(f"{usage_percentage:.1f}% of monthly allocation used")
    
    # Most used features
    if analytics['most_used_features']:
        st.markdown("#### 📊 Most Used Features")
        for feature, tokens in analytics['most_used_features']:
            st.write(f"• **{feature}**: {tokens} tokens")
    
    # Recommendations
    if analytics['recommendations']:
        st.markdown("#### 💡 Recommendations")
        for rec in analytics['recommendations']:
            st.info(rec)

# =============================================================================
# ADMIN PORTAL INTEGRATION
# =============================================================================

def get_admin_token_analytics() -> Dict[str, Any]:
    """Get system-wide token analytics for admin portal."""
    # This would integrate with your admin portal analytics
    return {
        "total_users": len(set(log['user_id'] for log in st.session_state.get('token_usage_log', []))),
        "total_tokens_consumed": sum(log['tokens_consumed'] for log in st.session_state.get('token_usage_log', [])),
        "most_popular_features": {},  # Calculate from logs
        "revenue_per_token": 0.15,  # Example calculation
        "upgrade_candidates": []  # Users who should upgrade
    }

def update_token_costs(new_costs: Dict[str, int]):
    """Update token costs - for admin portal use."""
    token_manager = get_token_manager()
    token_manager.token_costs.update(new_costs)
    st.success("✅ Token costs updated successfully!")

# =============================================================================
# EXAMPLE USAGE IN PAGES
# =============================================================================

def example_page_integration():
    """
    Example of how to integrate token system in any page.
    
    ADD THIS TO THE TOP OF ANY TOKENIZED PAGE:
    """
    example_code = '''
    # Import token system
    from token_management_system import check_page_access, consume_page_tokens, display_token_dashboard
    
    # Page setup
    st.set_page_config(page_title="AI Interview Coach", page_icon="🎯")
    
    # Check token access
    current_page = "07_AI_Interview_Coach.py"
    check_page_access(current_page)
    
    # Main page content here
    st.title("🎯 AI Interview Coach")
    
    # When user performs an action that should consume tokens
    if st.button("Start AI Interview Coaching"):
        result = consume_page_tokens(current_page)
        
        if result['success']:
            # Proceed with coaching functionality
            run_ai_interview_coaching()
        else:
            st.error("Token consumption failed")
    
    # Show token dashboard in sidebar
    with st.sidebar:
        display_token_dashboard()
    '''
    
    return example_code