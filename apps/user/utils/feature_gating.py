"""
Feature Gating Utility for IntelliCV-AI User Portal
===================================================
Controls access to features based on subscription tier.
"""

import streamlit as st
from typing import List, Dict, Any

# Feature definitions by subscription tier
SUBSCRIPTION_FEATURES = {
    'free': {
        'name': 'Free Trial',
        'price': 0,
        'features': [
            'basic_profile',
            'resume_upload_basic',
            'job_search_basic',
            'limited_resume_generations',
            'standard_templates'
        ],
        'limits': {
            'resume_generations': 3,
            'job_applications': 10,
            'ai_sessions': 5
        }
    },
    'monthly': {
        'name': 'Monthly Pro',
        'price': 9.99,
        'features': [
            'full_profile',
            'resume_upload_unlimited',
            'advanced_ai_matching',
            'linkedin_integration',
            'application_tracking',
            'premium_templates',
            'priority_support',
            'job_alerts',
            'career_insights'
        ],
        'limits': {
            'resume_generations': -1,  # Unlimited
            'job_applications': -1,
            'ai_sessions': 50
        }
    },
    'annual': {
        'name': 'Annual Pro',
        'price': 149.99,
        'features': [
            'full_profile',
            'resume_upload_unlimited',
            'advanced_ai_matching',
            'linkedin_integration',
            'application_tracking',
            'premium_templates',
            'priority_support',
            'job_alerts',
            'career_insights',
            'career_workbook',
            'industry_insights',
            'career_consultation',
            'early_access_features',
            'advanced_analytics'
        ],
        'limits': {
            'resume_generations': -1,
            'job_applications': -1,
            'ai_sessions': -1
        }
    },
    'super_user': {
        'name': 'Super-User',
        'price': 299,
        'features': [
            'full_profile',
            'resume_upload_unlimited',
            'advanced_ai_matching',
            'linkedin_integration',
            'application_tracking',
            'premium_templates',
            'priority_support',
            'job_alerts',
            'career_insights',
            'career_workbook',
            'industry_insights',
            'career_consultation',
            'early_access_features',
            'advanced_analytics',
            'mentorship_access',
            'unlimited_ai_sessions',
            'custom_branding',
            'api_access',
            'white_label_options'
        ],
        'limits': {
            'resume_generations': -1,
            'job_applications': -1,
            'ai_sessions': -1
        }
    }
}

def get_user_subscription() -> str:
    """Get user's current subscription tier from session state."""
    return st.session_state.get('subscription_plan', 'free')

def get_subscription_features(plan: str) -> List[str]:
    """Get list of features enabled for a subscription plan."""
    return SUBSCRIPTION_FEATURES.get(plan, SUBSCRIPTION_FEATURES['free'])['features']

def check_feature_access(feature: str, user_plan: str = None) -> bool:
    """
    Check if user has access to a specific feature.
    
    Args:
        feature: Feature name to check
        user_plan: Optional subscription plan (uses session state if not provided)
    
    Returns:
        True if user has access, False otherwise
    """
    if user_plan is None:
        user_plan = get_user_subscription()
    
    enabled_features = get_subscription_features(user_plan)
    return feature in enabled_features

def get_feature_limit(limit_type: str, user_plan: str = None) -> int:
    """
    Get usage limit for a specific feature type.
    
    Args:
        limit_type: Type of limit (e.g., 'resume_generations', 'ai_sessions')
        user_plan: Optional subscription plan (uses session state if not provided)
    
    Returns:
        Limit value (-1 for unlimited, positive number for specific limit)
    """
    if user_plan is None:
        user_plan = get_user_subscription()
    
    limits = SUBSCRIPTION_FEATURES.get(user_plan, SUBSCRIPTION_FEATURES['free'])['limits']
    return limits.get(limit_type, 0)

def display_locked_feature_message(feature_name: str, required_plan: str = 'monthly'):
    """
    Display a styled message for locked features with upgrade prompt.
    
    Args:
        feature_name: Name of the locked feature
        required_plan: Minimum plan required to access feature
    """
    plan_info = SUBSCRIPTION_FEATURES.get(required_plan, SUBSCRIPTION_FEATURES['monthly'])
    
    st.warning(f"""
    🔒 **{feature_name}** is available with {plan_info['name']} subscription
    
    **Upgrade to unlock:**
    - {feature_name} and more advanced features
    - Price: ${plan_info['price']}/month
    """)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("⬆️ Upgrade Now", key=f"upgrade_{feature_name}"):
            st.switch_page("pages/02_Payment.py")

def render_feature_with_gate(feature_name: str, feature_content, required_plan: str = 'monthly'):
    """
    Render feature content or locked message based on user subscription.
    
    Args:
        feature_name: Display name of the feature
        feature_content: Function that renders the feature content
        required_plan: Minimum plan required
    """
    user_plan = get_user_subscription()
    
    # Check if user has access
    feature_key = feature_name.lower().replace(' ', '_')
    if check_feature_access(feature_key, user_plan):
        # User has access, render content
        feature_content()
    else:
        # User doesn't have access, show locked message
        display_locked_feature_message(feature_name, required_plan)

def get_usage_status(limit_type: str, current_usage: int) -> Dict[str, Any]:
    """
    Get usage status for a feature with limits.
    
    Args:
        limit_type: Type of limit to check
        current_usage: Current usage count
    
    Returns:
        Dict with usage information and status
    """
    user_plan = get_user_subscription()
    limit = get_feature_limit(limit_type, user_plan)
    
    if limit == -1:
        # Unlimited
        return {
            'status': 'unlimited',
            'remaining': -1,
            'percentage': 0,
            'message': '✅ Unlimited usage'
        }
    elif current_usage >= limit:
        # Limit reached
        return {
            'status': 'limit_reached',
            'remaining': 0,
            'percentage': 100,
            'message': f'⚠️ Limit reached ({current_usage}/{limit})'
        }
    else:
        # Within limits
        percentage = (current_usage / limit) * 100
        return {
            'status': 'active',
            'remaining': limit - current_usage,
            'percentage': percentage,
            'message': f'✅ {current_usage}/{limit} used'
        }

def render_upgrade_prompt(current_plan: str = 'free'):
    """
    Render an upgrade prompt with available plans.
    
    Args:
        current_plan: User's current subscription plan
    """
    st.markdown("---")
    st.markdown("### 🚀 Upgrade Your Plan")
    
    # Get plans higher than current
    plan_order = ['free', 'monthly', 'annual', 'super_user']
    current_index = plan_order.index(current_plan) if current_plan in plan_order else 0
    
    available_upgrades = plan_order[current_index + 1:]
    
    if available_upgrades:
        cols = st.columns(len(available_upgrades))
        
        for idx, plan in enumerate(available_upgrades):
            plan_info = SUBSCRIPTION_FEATURES[plan]
            
            with cols[idx]:
                st.markdown(f"**{plan_info['name']}**")
                st.markdown(f"💰 ${plan_info['price']}/month")
                
                # Show top features
                st.markdown("**Top Features:**")
                for feature in plan_info['features'][:3]:
                    st.markdown(f"✅ {feature.replace('_', ' ').title()}")
                
                if st.button(f"Upgrade to {plan_info['name']}", key=f"upgrade_prompt_{plan}"):
                    st.switch_page("pages/02_Payment.py")
    else:
        st.success("✅ You have the highest tier subscription!")

def get_subscription_badge(plan: str = None) -> str:
    """
    Get a styled badge for subscription tier.
    
    Args:
        plan: Subscription plan (uses session state if not provided)
    
    Returns:
        HTML badge string
    """
    if plan is None:
        plan = get_user_subscription()
    
    badge_colors = {
        'free': '#95a5a6',
        'monthly': '#3498db',
        'annual': '#9b59b6',
        'super_user': '#f39c12'
    }
    
    plan_info = SUBSCRIPTION_FEATURES.get(plan, SUBSCRIPTION_FEATURES['free'])
    color = badge_colors.get(plan, '#95a5a6')
    
    badge_html = f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: bold;
        display: inline-block;
    ">
        {plan_info['name']}
    </span>
    """
    
    return badge_html
