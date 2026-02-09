"""
🔗 User Portal Token Integration
=============================== 
Connects user portals to backend admin token management system
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json

# Import token management from backend admin
try:
    backend_path = Path(__file__).parent.parent / "BACKEND-ADMIN-REORIENTATION"
    sys.path.insert(0, str(backend_path))
    from token_management_config import (
        TokenManager,
        TOKEN_COSTS,
        MONTHLY_TOKEN_ALLOCATIONS,
        POWER_USER_BOOSTS,
        get_user_token_status,
        check_action_availability,
        process_token_action,
        analyze_usage_and_recommend,
        TokenPricingTier,
        UserType
    )
    TOKEN_SYSTEM_AVAILABLE = True
except ImportError as e:
    TOKEN_SYSTEM_AVAILABLE = False
    print(f"⚠️ Token system not available: {e}")

class UserPortalTokenManager:
    """Token management interface for user portals"""
    
    def __init__(self):
        self.session_key = "token_manager_data"
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize token management in session state"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                "current_tokens": 0,
                "daily_usage": 0,
                "monthly_usage": 0,
                "last_refresh": datetime.now().isoformat(),
                "usage_history": [],
                "boost_packages": []
            }
    
    def get_user_plan(self) -> str:
        """Get current user's subscription plan"""
        plan_mapping = {
            "free": "free",
            "monthly": "monthly_pro", 
            "annual": "annual_pro",
            "enterprise": "enterprise_pro"
        }
        user_plan = st.session_state.get("subscription_plan", "free")
        return plan_mapping.get(user_plan, "free")
    
    def get_user_id(self) -> str:
        """Get current user ID"""
        return st.session_state.get("authenticated_user", "guest_user")
    
    def refresh_token_data(self):
        """Refresh token data from backend system"""
        if not TOKEN_SYSTEM_AVAILABLE:
            return False
        
        try:
            user_id = self.get_user_id()
            user_plan = self.get_user_plan()
            
            # Get current status from backend
            status = get_user_token_status(user_id, user_plan)
            
            # Update session state
            token_data = st.session_state[self.session_key]
            token_data.update({
                "current_tokens": status["current_tokens"],
                "monthly_allocation": status["monthly_allocation"],
                "rollover_limit": status["rollover_limit"],
                "daily_cap": status["daily_cap"],
                "features_unlocked": status["features_unlocked"],
                "plan": status["plan"]
            })
            
            return True
        except Exception as e:
            print(f"Error refreshing token data: {e}")
            return False
    
    def can_use_feature(self, feature_action: str) -> tuple[bool, str, int]:
        """Check if user can use a specific feature"""
        if not TOKEN_SYSTEM_AVAILABLE:
            return True, "Token system not available - access granted", 0
        
        try:
            user_id = self.get_user_id()
            user_plan = self.get_user_plan()
            
            result = check_action_availability(user_id, user_plan, feature_action)
            return result["can_perform"], result["message"], result["token_cost"]
        except Exception as e:
            print(f"Error checking feature availability: {e}")
            return True, "Error checking - access granted", 0
    
    def consume_tokens_for_action(self, action: str) -> tuple[bool, int]:
        """Consume tokens for an action"""
        if not TOKEN_SYSTEM_AVAILABLE:
            return True, 0
        
        try:
            user_id = self.get_user_id()
            user_plan = self.get_user_plan()
            
            result = process_token_action(user_id, user_plan, action)
            
            if result["success"]:
                # Update session state
                token_data = st.session_state[self.session_key]
                token_data["current_tokens"] = result["remaining_tokens"]
                token_data["usage_history"].append({
                    "action": action,
                    "cost": result["cost"],
                    "timestamp": datetime.now().isoformat()
                })
            
            return result["success"], result["remaining_tokens"]
        except Exception as e:
            print(f"Error consuming tokens: {e}")
            return True, 0
    
    def show_token_status_widget(self):
        """Display token status widget in sidebar"""
        if not TOKEN_SYSTEM_AVAILABLE:
            st.sidebar.info("🪙 Token system: Development mode")
            return
        
        try:
            # Refresh data
            self.refresh_token_data()
            token_data = st.session_state[self.session_key]
            
            # Token status display
            st.sidebar.markdown("### 🪙 Token Status")
            
            current = token_data.get("current_tokens", 0)
            monthly = token_data.get("monthly_allocation", 100)
            
            # Progress bar
            progress = min(current / monthly, 1.0) if monthly > 0 else 0
            st.sidebar.progress(progress)
            
            # Status info
            st.sidebar.markdown(f"""
            **Current Tokens:** {current}
            **Monthly Allocation:** {monthly}
            **Plan:** {token_data.get('plan', 'free').replace('_', ' ').title()}
            """)
            
            # Usage warnings
            if current < 50:
                st.sidebar.warning("⚠️ Low tokens remaining!")
                if st.sidebar.button("🚀 Get Boost Package"):
                    self.show_boost_packages()
            elif current < 20:
                st.sidebar.error("❌ Very low tokens!")
                st.sidebar.markdown("Consider upgrading your plan")
            
        except Exception as e:
            st.sidebar.error(f"Token status error: {e}")
    
    def show_boost_packages(self):
        """Show available boost packages"""
        if not TOKEN_SYSTEM_AVAILABLE:
            st.info("Boost packages not available in development mode")
            return
        
        st.markdown("### 🚀 Power User Boost Packages")
        st.markdown("Perfect for job search urgency or career transitions!")
        
        for boost_id, boost_info in POWER_USER_BOOSTS.items():
            with st.expander(f"💎 {boost_info['name']} - ${boost_info['price']}"):
                st.markdown(f"**{boost_info['description']}**")
                st.markdown(f"🪙 **Tokens:** {boost_info['tokens']}")
                st.markdown(f"⏰ **Valid for:** {boost_info['valid_days']} days")
                
                st.markdown("**Features included:**")
                for feature in boost_info['features']:
                    st.markdown(f"• {feature}")
                
                if st.button(f"Purchase {boost_info['name']}", key=f"boost_{boost_id}"):
                    st.success(f"✅ {boost_info['name']} purchased! (Simulation)")
                    # In real implementation, integrate with payment system
    
    def check_feature_access_with_ui(self, feature_action: str, feature_name: str) -> bool:
        """Check feature access and show UI feedback"""
        can_use, message, cost = self.can_use_feature(feature_action)
        
        if not can_use:
            st.error(f"❌ {message}")
            
            # Show upgrade options
            user_plan = self.get_user_plan()
            if user_plan == "free":
                st.info("💡 Upgrade to Monthly Pro ($15.99) to access this feature!")
                if st.button("Upgrade Plan"):
                    st.switch_page("pages/06_Pricing.py")
            else:
                st.info("💎 This feature requires a boost package for intensive usage")
                if st.button("View Boost Packages"):
                    self.show_boost_packages()
            
            return False
        
        # Show cost info
        if cost > 0:
            st.info(f"💰 This action will cost {cost} tokens")
        
        return True
    
    def log_feature_usage(self, feature_action: str, feature_name: str, success: bool = True):
        """Log feature usage for analytics"""
        try:
            token_data = st.session_state[self.session_key]
            usage_entry = {
                "feature": feature_name,
                "action": feature_action,
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "user_plan": self.get_user_plan()
            }
            token_data["usage_history"].append(usage_entry)
            
            # Keep only last 100 entries
            if len(token_data["usage_history"]) > 100:
                token_data["usage_history"] = token_data["usage_history"][-100:]
                
        except Exception as e:
            print(f"Error logging usage: {e}")
    
    def get_usage_analytics(self) -> Dict:
        """Get usage analytics for user"""
        if not TOKEN_SYSTEM_AVAILABLE:
            return {"error": "Analytics not available"}
        
        try:
            token_data = st.session_state[self.session_key]
            usage_history = token_data.get("usage_history", [])
            
            # Analyze usage patterns
            feature_counts = {}
            daily_usage = {}
            
            for entry in usage_history:
                feature = entry["feature"]
                date = entry["timestamp"][:10]  # YYYY-MM-DD
                
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
                daily_usage[date] = daily_usage.get(date, 0) + 1
            
            return {
                "total_actions": len(usage_history),
                "feature_usage": feature_counts,
                "daily_usage": daily_usage,
                "most_used_feature": max(feature_counts.items(), key=lambda x: x[1])[0] if feature_counts else None
            }
        except Exception as e:
            return {"error": str(e)}
    
    def show_usage_dashboard(self):
        """Show usage analytics dashboard"""
        st.markdown("### 📊 Your Usage Analytics")
        
        analytics = self.get_usage_analytics()
        
        if "error" in analytics:
            st.error(f"Analytics error: {analytics['error']}")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Actions", analytics["total_actions"])
        
        with col2:
            most_used = analytics.get("most_used_feature", "None")
            st.metric("Most Used Feature", most_used)
        
        with col3:
            current_tokens = st.session_state[self.session_key].get("current_tokens", 0)
            st.metric("Current Tokens", current_tokens)
        
        # Feature usage chart
        if analytics["feature_usage"]:
            st.markdown("#### Feature Usage Breakdown")
            st.bar_chart(analytics["feature_usage"])

# Convenience functions for easy integration in pages
def init_token_manager() -> UserPortalTokenManager:
    """Initialize token manager for page"""
    return UserPortalTokenManager()

def check_tokens_before_action(feature_action: str, feature_name: str) -> bool:
    """Check tokens before performing an action"""
    manager = UserPortalTokenManager()
    return manager.check_feature_access_with_ui(feature_action, feature_name)

def consume_tokens_after_action(feature_action: str, feature_name: str):
    """Consume tokens after successful action"""
    manager = UserPortalTokenManager()
    success, remaining = manager.consume_tokens_for_action(feature_action)
    manager.log_feature_usage(feature_action, feature_name, success)
    return success, remaining

def show_token_sidebar():
    """Show token status in sidebar"""
    manager = UserPortalTokenManager()
    manager.show_token_status_widget()

# Action mapping for different features
FEATURE_ACTION_MAPPING = {
    # Resume generation features
    "resume_upload": "resume_generation_basic",
    "resume_enhancement": "resume_generation_advanced", 
    "custom_resume": "resume_generation_custom",
    
    # Job matching features
    "job_search": "job_matching_basic",
    "advanced_job_match": "job_matching_advanced",
    "precision_job_match": "job_matching_precision",
    
    # AI insights features
    "basic_insights": "ai_insights_basic",
    "detailed_insights": "ai_insights_detailed",
    "comprehensive_analysis": "ai_insights_comprehensive",
    
    # Career coaching features
    "career_chat": "career_coaching_chat",
    "career_assessment": "career_coaching_assessment",
    "action_plan": "career_coaching_action_plan",
    
    # Application tracking
    "track_application": "application_tracking_add",
    "analyze_applications": "application_tracking_analysis",
    "application_insights": "application_tracking_insights",
    
    # Interview preparation
    "interview_questions": "interview_prep_questions",
    "mock_interview": "interview_prep_mock",
    "interview_feedback": "interview_prep_feedback",
    
    # Profile optimization
    "linkedin_optimization": "profile_optimization_linkedin",
    "resume_optimization": "profile_optimization_resume",
    "portfolio_optimization": "profile_optimization_portfolio",
    
    # Industry analysis
    "industry_trends": "industry_analysis_trends",
    "salary_analysis": "industry_analysis_salary",
    "company_analysis": "industry_analysis_companies",
}

def get_action_for_feature(feature_name: str) -> str:
    """Get token action for feature name"""
    return FEATURE_ACTION_MAPPING.get(feature_name, "basic_action")

if __name__ == "__main__":
    print("🔗 User Portal Token Integration System")
    print("======================================")
    print(f"Token system available: {TOKEN_SYSTEM_AVAILABLE}")
    print(f"Available features: {len(FEATURE_ACTION_MAPPING)}")