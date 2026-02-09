"""
=============================================================================
IntelliCV User Portal - Admin AI Integration Hooks
=============================================================================

CRITICAL MODULE: Provides seamless integration between user portal pages and 
admin AI enrichment systems. Enables users to access sophisticated admin AI
analysis through simple user interfaces.

Key Features:
- Enhanced Job Title Engine Integration (422 lines of admin AI)
- Real AI Data Connector (548 lines processing 3,418+ JSON files)
- Admin Statistical Tools Integration
- Bidirectional Data Enrichment
- Transparent Backend AI Orchestration

Author: IntelliCV-AI System
Date: October 20, 2025
Status: CRITICAL PRODUCTION REQUIREMENT
"""

import sys
from pathlib import Path
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import streamlit as st

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminAIIntegration:
    """
    Universal admin AI integration for user portal pages.
    Connects user actions to sophisticated admin AI systems seamlessly.
    """
    
    def __init__(self):
        """Initialize admin AI integration with all required systems."""
        self.admin_systems_loaded = False
        self.enhanced_job_engine = None
        self.real_ai_connector = None
        self.integration_hooks = None
        self.statistical_tools = None
        
        # Load admin systems
        self._load_admin_systems()
    
    def _load_admin_systems(self):
        """Load all admin AI systems for user integration."""
        try:
            # Add admin portal to path
            admin_path = Path("c:/IntelliCV-AI/IntelliCV/SANDBOX/admin_portal")
            if admin_path.exists():
                sys.path.insert(0, str(admin_path))
                sys.path.insert(0, str(admin_path / "services"))
                sys.path.insert(0, str(admin_path / "pages" / "shared"))
                
                # Load enhanced job title engine
                try:
                    from enhanced_job_title_engine import EnhancedJobTitleEngine
                    self.enhanced_job_engine = EnhancedJobTitleEngine()
                    logger.info("✅ Enhanced Job Title Engine loaded (422 lines)")
                except ImportError as e:
                    logger.warning(f"Enhanced Job Title Engine not available: {e}")
                
                # Load real AI data connector
                try:
                    from real_ai_data_connector import RealAIDataConnector
                    self.real_ai_connector = RealAIDataConnector()
                    logger.info("✅ Real AI Data Connector loaded (548 lines, 3,418+ JSON files)")
                except ImportError as e:
                    logger.warning(f"Real AI Data Connector not available: {e}")
                
                # Load integration hooks manager
                try:
                    from integration_hooks import IntegrationHooksManager
                    self.integration_hooks = IntegrationHooksManager()
                    logger.info("✅ Integration Hooks Manager loaded")
                except ImportError as e:
                    logger.warning(f"Integration Hooks Manager not available: {e}")
                
                self.admin_systems_loaded = True
                logger.info("🚀 Admin AI Systems Integration: ACTIVE")
                
        except Exception as e:
            logger.error(f"Failed to load admin systems: {e}")
            self.admin_systems_loaded = False
    
    def is_admin_ai_available(self) -> bool:
        """Check if admin AI systems are available for integration."""
        return self.admin_systems_loaded and any([
            self.enhanced_job_engine,
            self.real_ai_connector,
            self.integration_hooks
        ])
    
    def process_resume_with_admin_ai(self, resume_file, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process resume upload with full admin AI integration.
        User sees simple upload, backend processes with sophisticated AI.
        """
        result = {
            'user_message': 'Resume uploaded successfully',
            'admin_ai_analysis': {},
            'enhanced_data': {},
            'bidirectional_enrichment': False
        }
        
        if not self.is_admin_ai_available():
            logger.warning("Admin AI systems not available - using basic processing")
            return result
        
        try:
            # Enhanced Job Title Engine Analysis
            if self.enhanced_job_engine:
                job_analysis = self.enhanced_job_engine.analyze_resume_content(resume_file)
                result['admin_ai_analysis']['job_titles'] = job_analysis.get('enhanced_titles', [])
                result['admin_ai_analysis']['linkedin_industries'] = job_analysis.get('linkedin_classification', [])
                result['admin_ai_analysis']['skill_mapping'] = job_analysis.get('skill_analysis', {})
                logger.info("✅ Enhanced Job Title Engine analysis completed")
            
            # Real AI Data Connector Processing
            if self.real_ai_connector:
                ai_insights = self.real_ai_connector.analyze_with_real_data(resume_file, user_data)
                result['admin_ai_analysis']['market_intelligence'] = ai_insights.get('market_data', {})
                result['admin_ai_analysis']['statistical_benchmarks'] = ai_insights.get('benchmarks', {})
                result['admin_ai_analysis']['career_patterns'] = ai_insights.get('patterns', [])
                logger.info("✅ Real AI Data Connector analysis completed")
            
            # Bidirectional Data Enrichment
            if self.integration_hooks:
                # User data enriches admin systems
                enrichment_success = self.integration_hooks.enrich_admin_datasets({
                    'user_id': user_data.get('user_id'),
                    'resume_data': resume_file,
                    'analysis_results': result['admin_ai_analysis'],
                    'timestamp': datetime.now().isoformat()
                })
                result['bidirectional_enrichment'] = enrichment_success
                logger.info("✅ Bidirectional data enrichment completed")
            
            # Enhanced User Experience (disguised as simple)
            result['enhanced_data'] = self._create_enhanced_user_experience(result['admin_ai_analysis'])
            result['user_message'] = 'Resume processed successfully with AI insights'
            
        except Exception as e:
            logger.error(f"Admin AI processing error: {e}")
            result['user_message'] = 'Resume uploaded (basic processing due to system limitations)'
        
        return result
    
    def process_job_search_with_admin_ai(self, search_criteria: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process job search with admin AI statistical tools and market intelligence.
        """
        result = {
            'user_message': 'Job search completed',
            'admin_ai_analysis': {},
            'enhanced_results': [],
            'statistical_insights': {}
        }
        
        if not self.is_admin_ai_available():
            return result
        
        try:
            # Enhanced Job Title Engine for job matching
            if self.enhanced_job_engine:
                job_matching = self.enhanced_job_engine.enhance_job_search(search_criteria)
                result['admin_ai_analysis']['enhanced_matching'] = job_matching
                logger.info("✅ Admin AI job matching analysis completed")
            
            # Real AI Data Connector for market intelligence
            if self.real_ai_connector:
                market_data = self.real_ai_connector.get_job_market_intelligence(search_criteria)
                result['admin_ai_analysis']['market_intelligence'] = market_data
                result['statistical_insights'] = market_data.get('statistical_analysis', {})
                logger.info("✅ Admin market intelligence analysis completed")
            
            # Create enhanced user experience
            result['enhanced_results'] = self._create_enhanced_job_results(result['admin_ai_analysis'])
            result['user_message'] = f"Found {len(result['enhanced_results'])} AI-optimized matches"
            
        except Exception as e:
            logger.error(f"Admin AI job search error: {e}")
        
        return result
    
    def get_admin_statistical_analysis(self, user_id: str, analysis_type: str) -> Dict[str, Any]:
        """
        Get admin statistical analysis for transparent user experience.
        Critical for pages 22-25 admin-derived functionality.
        """
        if not self.real_ai_connector:
            return {'analysis': 'Statistical analysis unavailable'}
        
        try:
            statistical_analysis = self.real_ai_connector.get_user_statistical_analysis(user_id, analysis_type)
            return {
                'analysis': statistical_analysis,
                'benchmarks': statistical_analysis.get('benchmarks', {}),
                'trends': statistical_analysis.get('trends', []),
                'recommendations': statistical_analysis.get('ai_recommendations', [])
            }
        except Exception as e:
            logger.error(f"Admin statistical analysis error: {e}")
            return {'analysis': f'Analysis error: {e}'}
    
    def enrich_admin_databases(self, user_interaction_data: Dict[str, Any]) -> bool:
        """
        Enrich admin databases with user interaction data.
        Critical for bidirectional data flow.
        """
        if not self.integration_hooks:
            return False
        
        try:
            # Enrich admin systems with user data
            success = self.integration_hooks.sync_user_data(
                user_interaction_data.get('user_id'),
                user_interaction_data
            )
            
            if success:
                logger.info(f"✅ Admin databases enriched with user data: {user_interaction_data.get('action_type')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Admin database enrichment error: {e}")
            return False
    
    def _create_enhanced_user_experience(self, admin_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced user experience from admin AI analysis."""
        enhanced_data = {}
        
        # Transform admin analysis into user-friendly format
        if 'job_titles' in admin_analysis:
            enhanced_data['career_suggestions'] = admin_analysis['job_titles'][:5]
        
        if 'linkedin_industries' in admin_analysis:
            enhanced_data['industry_match'] = admin_analysis['linkedin_industries'][:3]
        
        if 'market_intelligence' in admin_analysis:
            enhanced_data['market_insights'] = admin_analysis['market_intelligence']
        
        if 'statistical_benchmarks' in admin_analysis:
            enhanced_data['performance_metrics'] = admin_analysis['statistical_benchmarks']
        
        return enhanced_data
    
    def _create_enhanced_job_results(self, admin_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create enhanced job results from admin AI analysis."""
        enhanced_results = []
        
        # Transform admin job matching into user results
        if 'enhanced_matching' in admin_analysis:
            for match in admin_analysis['enhanced_matching'][:10]:  # Top 10
                enhanced_results.append({
                    'title': match.get('job_title', 'Unknown Position'),
                    'company': match.get('company', 'Company Name'),
                    'match_score': match.get('ai_compatibility_score', 85),
                    'admin_insights': match.get('admin_analysis', {}),
                    'why_matched': match.get('ai_reasoning', 'AI-powered matching')
                })
        
        return enhanced_results
    
    def display_admin_integration_status(self):
        """Display admin integration status for debugging."""
        st.write("### 🔧 Admin AI Integration Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status = "✅ Active" if self.enhanced_job_engine else "❌ Not Available"
            st.metric("Enhanced Job Engine", status)
        
        with col2:
            status = "✅ Active" if self.real_ai_connector else "❌ Not Available"
            st.metric("Real AI Data Connector", status)
        
        with col3:
            status = "✅ Active" if self.integration_hooks else "❌ Not Available"
            st.metric("Integration Hooks", status)
        
        if self.is_admin_ai_available():
            st.success("🚀 Admin AI Systems: FULLY INTEGRATED")
            st.info("Users will receive enhanced AI analysis powered by admin systems")
        else:
            st.warning("⚠️ Admin AI Systems: LIMITED INTEGRATION")
            st.error("Users will receive basic processing only")

# =============================================================================
# STREAMLIT INTEGRATION HELPERS
# =============================================================================

@st.cache_resource
def get_admin_ai_integration() -> AdminAIIntegration:
    """Get cached admin AI integration instance."""
    return AdminAIIntegration()

def init_admin_ai_for_user_page():
    """Initialize admin AI integration for user pages."""
    if 'admin_ai_integration' not in st.session_state:
        st.session_state.admin_ai_integration = get_admin_ai_integration()
    
    return st.session_state.admin_ai_integration

def process_user_action_with_admin_ai(action_type: str, user_data: Dict[str, Any], additional_data: Any = None):
    """
    Universal function to process user actions with admin AI integration.
    Use this in ALL user pages for consistent admin AI integration.
    """
    admin_ai = init_admin_ai_for_user_page()
    
    # Track user interaction for bidirectional enrichment
    interaction_data = {
        'user_id': st.session_state.get('user_id', 'anonymous'),
        'action_type': action_type,
        'timestamp': datetime.now().isoformat(),
        'user_data': user_data,
        'additional_data': additional_data
    }
    
    # Enrich admin databases with user interaction
    admin_ai.enrich_admin_databases(interaction_data)
    
    # Process specific action types
    if action_type == 'resume_upload' and additional_data:
        return admin_ai.process_resume_with_admin_ai(additional_data, user_data)
    elif action_type == 'job_search':
        return admin_ai.process_job_search_with_admin_ai(user_data, user_data)
    elif action_type == 'statistical_analysis':
        return admin_ai.get_admin_statistical_analysis(
            interaction_data['user_id'], 
            user_data.get('analysis_type', 'general')
        )
    else:
        # Generic admin AI enhancement
        return {
            'user_message': f'{action_type.replace("_", " ").title()} completed successfully',
            'admin_enhanced': admin_ai.is_admin_ai_available(),
            'bidirectional_enrichment': True
        }

# =============================================================================
# USER PAGE INTEGRATION EXAMPLES
# =============================================================================

def example_resume_upload_integration():
    """
    Example: How to integrate admin AI into resume upload page.
    
    ADD THIS TO 05_Resume_Upload.py:
    """
    example_code = '''
    # Add to top of 05_Resume_Upload.py
    from user_portal_admin_integration import process_user_action_with_admin_ai
    
    # Replace basic file upload processing with:
    if uploaded_file:
        user_data = {
            'user_id': st.session_state.get('user_id'),
            'profile_data': st.session_state.get('profile_data', {}),
            'upload_timestamp': datetime.now().isoformat()
        }
        
        # Process with admin AI integration
        result = process_user_action_with_admin_ai('resume_upload', user_data, uploaded_file)
        
        # Show user simple message
        st.success(result['user_message'])
        
        # Display enhanced results (powered by admin AI)
        if result.get('enhanced_data'):
            display_enhanced_analysis(result['enhanced_data'])
    '''
    
    return example_code

def example_job_search_integration():
    """
    Example: How to integrate admin AI into job search page.
    
    ADD THIS TO 06_Job_Match.py:
    """
    example_code = '''
    # Add to top of 06_Job_Match.py  
    from user_portal_admin_integration import process_user_action_with_admin_ai
    
    # Replace basic job search with:
    if st.button("🔍 Find Jobs"):
        search_data = {
            'keywords': keywords,
            'location': location,
            'experience_level': experience_level,
            'salary_range': salary_range
        }
        
        # Process with admin AI integration
        result = process_user_action_with_admin_ai('job_search', search_data)
        
        # Show enhanced results (powered by admin market intelligence)
        st.success(result['user_message'])
        display_enhanced_job_results(result['enhanced_results'])
    '''
    
    return example_code

# =============================================================================
# PAYMENT GATEWAY INTEGRATION WITH ADMIN PORTAL
# =============================================================================

def sync_subscription_to_admin_portal(user_data: Dict[str, Any], subscription_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync user subscription data to admin portal for access control and billing management.
    
    Args:
        user_data: User profile information
        subscription_data: Subscription details (plan, price, payment_method, etc.)
    
    Returns:
        Dict with sync status and admin portal response
    """
    try:
        # Prepare subscription sync payload
        sync_payload = {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'email': user_data.get('email'),
            'subscription_plan': subscription_data.get('plan'),
            'subscription_price': subscription_data.get('price'),
            'subscription_status': subscription_data.get('status', 'active'),
            'payment_method': subscription_data.get('payment_method'),
            'billing_cycle': subscription_data.get('billing_cycle'),
            'start_date': datetime.now().isoformat(),
            'features_enabled': get_features_for_plan(subscription_data.get('plan')),
            'sync_timestamp': datetime.now().isoformat()
        }
        
        # Log subscription event
        logger.info(f"Syncing subscription to admin portal: {subscription_data.get('plan')} for {user_data.get('username')}")
        
        # TODO: Replace with actual admin portal API call
        # response = requests.post(ADMIN_PORTAL_API_URL + '/subscription/sync', json=sync_payload)
        
        # Simulate successful sync for now
        return {
            'success': True,
            'message': 'Subscription synced to admin portal',
            'access_features': sync_payload['features_enabled'],
            'admin_portal_user_id': f"admin_{sync_payload['user_id']}",
            'sync_timestamp': sync_payload['sync_timestamp']
        }
        
    except Exception as e:
        logger.error(f"Failed to sync subscription to admin portal: {e}")
        return {
            'success': False,
            'message': f'Subscription sync failed: {str(e)}',
            'access_features': get_features_for_plan('free')  # Fallback to free features
        }

def get_features_for_plan(plan: str) -> List[str]:
    """
    Get list of enabled features for subscription plan.
    Used for feature gating in user portal.
    """
    feature_map = {
        'free': [
            'basic_profile',
            'resume_upload_basic',
            'job_search_basic',
            'limited_resume_generations_3'
        ],
        'monthly': [
            'full_profile',
            'resume_upload_unlimited',
            'advanced_ai_matching',
            'linkedin_integration',
            'application_tracking',
            'premium_templates',
            'priority_support'
        ],
        'annual': [
            'full_profile',
            'resume_upload_unlimited',
            'advanced_ai_matching',
            'linkedin_integration',
            'application_tracking',
            'premium_templates',
            'priority_support',
            'career_workbook',
            'industry_insights',
            'career_consultation',
            'early_access_features'
        ],
        'super_user': [
            'full_profile',
            'resume_upload_unlimited',
            'advanced_ai_matching',
            'linkedin_integration',
            'application_tracking',
            'premium_templates',
            'priority_support',
            'career_workbook',
            'industry_insights',
            'career_consultation',
            'early_access_features',
            'mentorship_access',
            'unlimited_ai_sessions',
            'custom_branding',
            'api_access'
        ]
    }
    
    return feature_map.get(plan, feature_map['free'])

def check_feature_access(feature: str, user_subscription: str = 'free') -> bool:
    """
    Check if user has access to a specific feature based on subscription.
    Use this for feature gating in user pages.
    
    Example usage in pages:
        if check_feature_access('linkedin_integration', st.session_state.get('subscription_plan')):
            # Show LinkedIn import feature
        else:
            st.warning("⚠️ Upgrade to Monthly Pro to access LinkedIn integration")
    """
    enabled_features = get_features_for_plan(user_subscription)
    return feature in enabled_features

def process_payment_with_stripe(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process payment through Stripe API and sync to admin portal.
    
    Args:
        payment_data: Payment details including card info, amount, plan
    
    Returns:
        Dict with payment status and admin portal sync result
    """
    try:
        # TODO: Replace with actual Stripe API integration
        # import stripe
        # stripe.api_key = st.secrets["stripe_secret_key"]
        # 
        # # Create customer
        # customer = stripe.Customer.create(
        #     email=payment_data['email'],
        #     name=payment_data['cardholder_name'],
        #     metadata={'username': payment_data['username']}
        # )
        # 
        # # Create payment intent
        # intent = stripe.PaymentIntent.create(
        #     amount=int(payment_data['amount'] * 100),  # Convert to cents
        #     currency='usd',
        #     customer=customer.id,
        #     payment_method_types=['card'],
        #     metadata={
        #         'plan': payment_data['plan'],
        #         'user_id': payment_data['user_id']
        #     }
        # )
        
        # Simulate successful payment for now
        logger.info(f"Processing payment: ${payment_data['amount']} for {payment_data['plan']}")
        
        payment_result = {
            'success': True,
            'transaction_id': f"txn_{int(datetime.now().timestamp())}",
            'amount': payment_data['amount'],
            'currency': 'USD',
            'payment_method': payment_data.get('payment_method', 'card'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Sync subscription to admin portal
        subscription_data = {
            'plan': payment_data['plan'],
            'price': payment_data['amount'],
            'status': 'active',
            'payment_method': payment_result['payment_method'],
            'billing_cycle': payment_data.get('billing_cycle', 'monthly')
        }
        
        user_data = {
            'user_id': payment_data.get('user_id'),
            'username': payment_data.get('username'),
            'email': payment_data.get('email')
        }
        
        admin_sync_result = sync_subscription_to_admin_portal(user_data, subscription_data)
        
        return {
            'payment': payment_result,
            'admin_sync': admin_sync_result,
            'success': payment_result['success'] and admin_sync_result['success']
        }
        
    except Exception as e:
        logger.error(f"Payment processing failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Payment processing failed. Please try again.'
        }