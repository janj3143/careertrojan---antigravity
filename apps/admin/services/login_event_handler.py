"""
Login Event Handler - SANDBOX Version
====================================

Handles user login events and triggers automatic data screening.
Integrates with Streamlit authentication system to provide seamless
AI-powered user data analysis upon login.

Features:
- Automatic screening trigger on user login
- Background processing with status updates
- Integration with existing authentication system
- Real-time user feedback and recommendations

Author: IntelliCV AI Team
Purpose: Seamless login-triggered AI data screening
Environment: SANDBOX Admin Portal
"""

import streamlit as st
import asyncio
import threading
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

# Import our screening system
try:
    from services.auto_screen_system import get_auto_screen_system, auto_screen_user
    AUTO_SCREEN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Auto-screen system not available: {e}")
    AUTO_SCREEN_AVAILABLE = False

class LoginEventHandler:
    """
    Handles login events and triggers automatic screening
    """
    
    def __init__(self):
        """Initialize the login event handler"""
        self.auto_screen_system = None
        if AUTO_SCREEN_AVAILABLE:
            self.auto_screen_system = get_auto_screen_system()
        
        # Initialize session state for login tracking
        if 'login_screening_status' not in st.session_state:
            st.session_state.login_screening_status = {}
        
        if 'login_event_handler_initialized' not in st.session_state:
            st.session_state.login_event_handler_initialized = True
    
    def handle_user_login(self, user_id: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle user login event and trigger automatic screening
        
        Args:
            user_id: Unique user identifier
            user_data: Optional user data dictionary
            
        Returns:
            Dictionary with login handling results
        """
        print(f"🔐 Handling login for user: {user_id}")
        
        login_result = {
            'user_id': user_id,
            'login_timestamp': datetime.now().isoformat(),
            'screening_triggered': False,
            'screening_status': 'not_started',
            'screening_results': None,
            'auto_screen_available': AUTO_SCREEN_AVAILABLE
        }
        
        # Check if user has been screened recently
        recent_screening = self._check_recent_screening(user_id)
        if recent_screening:
            login_result['screening_status'] = 'recent_screening_found'
            login_result['screening_results'] = recent_screening
            print(f"✅ Recent screening found for user {user_id}")
            return login_result
        
        # Trigger automatic screening if available
        if AUTO_SCREEN_AVAILABLE and self.auto_screen_system:
            try:
                login_result['screening_triggered'] = True
                login_result['screening_status'] = 'in_progress'
                
                # Run screening in background
                screening_results = self.auto_screen_system.screen_user_on_login(user_id, user_data)
                
                login_result['screening_results'] = screening_results
                login_result['screening_status'] = screening_results.get('processing_status', 'completed')
                
                # Store in session state for UI updates
                st.session_state.login_screening_status[user_id] = {
                    'timestamp': datetime.now().isoformat(),
                    'results': screening_results,
                    'status': login_result['screening_status']
                }
                
                print(f"✅ Auto-screening completed for user {user_id}")
                
            except Exception as e:
                print(f"❌ Error in auto-screening for user {user_id}: {e}")
                login_result['screening_status'] = 'error'
                login_result['error'] = str(e)
        else:
            print(f"⚠️ Auto-screening not available for user {user_id}")
        
        return login_result
    
    def _check_recent_screening(self, user_id: str, hours_threshold: int = 24) -> Optional[Dict[str, Any]]:
        """Check if user has been screened recently"""
        if AUTO_SCREEN_AVAILABLE and self.auto_screen_system:
            try:
                screening_status = self.auto_screen_system.get_user_screening_status(user_id)
                if screening_status:
                    screening_time = datetime.fromisoformat(screening_status['screening_timestamp'])
                    time_diff = datetime.now() - screening_time
                    
                    if time_diff.total_seconds() < (hours_threshold * 3600):
                        return screening_status
            except Exception as e:
                print(f"⚠️ Error checking recent screening: {e}")
        
        return None
    
    def display_screening_status(self, user_id: str):
        """Display screening status in Streamlit UI"""
        if user_id in st.session_state.login_screening_status:
            screening_info = st.session_state.login_screening_status[user_id]
            status = screening_info['status']
            results = screening_info['results']
            
            # Create status display
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if status == 'in_progress':
                    st.info("🔍 **Analyzing your data with AI...** Please wait.")
                    st.progress(0.5)
                
                elif status == 'completed':
                    files_processed = results.get('files_processed', 0)
                    data_quality_score = results.get('data_quality_score', 0.0)
                    
                    st.success(f"✅ **AI Analysis Complete!** Processed {files_processed} files")
                    
                    # Show data quality score
                    if data_quality_score > 0:
                        quality_percentage = int(data_quality_score * 100)
                        st.metric("Data Quality Score", f"{quality_percentage}%")
                        
                        # Quality indicator
                        if quality_percentage >= 80:
                            st.success("🎯 Excellent data quality!")
                        elif quality_percentage >= 60:
                            st.info("👍 Good data quality")
                        else:
                            st.warning("⚠️ Data quality could be improved")
                    
                    # Show recommendations
                    recommendations = results.get('recommendations', [])
                    if recommendations:
                        st.markdown("### 💡 **Recommendations:**")
                        for rec in recommendations:
                            st.markdown(f"• {rec}")
                
                elif status == 'no_data':
                    st.warning("📄 **No data files found** - Upload your CV/Resume to get started!")
                    if st.button("Upload Files", key=f"upload_{user_id}"):
                        st.switch_page("pages/06_Document_Parser.py")
                
                elif status == 'error':
                    st.error("❌ **Error during analysis** - Please try again later")
                    if st.button("Retry Analysis", key=f"retry_{user_id}"):
                        self.handle_user_login(user_id)
                        st.rerun()
                
                elif status == 'recent_screening_found':
                    files_processed = results.get('files_processed', 0)
                    data_quality_score = results.get('data_quality_score', 0.0)
                    
                    st.info(f"📊 **Recent analysis found** - {files_processed} files processed")
                    if data_quality_score > 0:
                        quality_percentage = int(data_quality_score * 100)
                        st.metric("Data Quality Score", f"{quality_percentage}%")
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get user dashboard data including screening results"""
        dashboard_data = {
            'user_id': user_id,
            'screening_available': AUTO_SCREEN_AVAILABLE,
            'last_screening': None,
            'files_count': 0,
            'data_quality_score': 0.0,
            'recommendations': [],
            'ai_analysis_summary': {}
        }
        
        if AUTO_SCREEN_AVAILABLE and self.auto_screen_system:
            try:
                screening_status = self.auto_screen_system.get_user_screening_status(user_id)
                if screening_status:
                    dashboard_data.update({
                        'last_screening': screening_status['screening_timestamp'],
                        'files_count': screening_status.get('files_processed', 0),
                        'data_quality_score': screening_status.get('data_quality_score', 0.0),
                        'recommendations': screening_status.get('recommendations', []),
                        'ai_analysis_summary': {
                            'total_analyses': len(screening_status.get('ai_analysis_results', [])),
                            'average_scores': self._calculate_average_scores(screening_status.get('ai_analysis_results', []))
                        }
                    })
            except Exception as e:
                print(f"⚠️ Error getting dashboard data: {e}")
        
        return dashboard_data
    
    def _calculate_average_scores(self, analysis_results: list) -> Dict[str, float]:
        """Calculate average AI scores from analysis results"""
        if not analysis_results:
            return {}
        
        score_keys = ['bayesian_confidence', 'nlp_sentiment', 'fuzzy_logic_score', 'llm_coherence', 'combined_score']
        averages = {}
        
        for key in score_keys:
            scores = [result.get(key, 0) for result in analysis_results if key in result]
            if scores:
                averages[key] = sum(scores) / len(scores)
        
        return averages
    
    def trigger_background_screening(self, user_id: str):
        """Trigger screening in background thread"""
        if AUTO_SCREEN_AVAILABLE:
            def background_screen():
                try:
                    result = auto_screen_user(user_id)
                    st.session_state.login_screening_status[user_id] = {
                        'timestamp': datetime.now().isoformat(),
                        'results': result,
                        'status': result.get('processing_status', 'completed')
                    }
                except Exception as e:
                    print(f"❌ Background screening error: {e}")
            
            # Run in background thread
            thread = threading.Thread(target=background_screen)
            thread.daemon = True
            thread.start()

# Authentication integration functions
def check_authentication_with_screening():
    """
    Enhanced authentication check that triggers automatic screening
    """
    # Check basic authentication first
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("🔒 **Access Denied** - Please log in to continue")
        if st.button("Go to Login"):
            st.switch_page("app.py")
        st.stop()
    
    # Get current user
    current_user = st.session_state.get('username', 'anonymous')
    
    # Initialize login handler
    if 'login_handler' not in st.session_state:
        st.session_state.login_handler = LoginEventHandler()
    
    # Check if this is a new login (screening not yet done)
    if f'screened_{current_user}' not in st.session_state:
        with st.spinner("🔍 Analyzing your data with AI..."):
            login_result = st.session_state.login_handler.handle_user_login(current_user)
            st.session_state[f'screened_{current_user}'] = True
            
            # Show immediate results if available
            if login_result.get('screening_results'):
                st.session_state['last_login_screening'] = login_result
    
    return True

def display_user_screening_dashboard(user_id: str = None):
    """
    Display user screening dashboard
    """
    if not user_id:
        user_id = st.session_state.get('username', 'anonymous')
    
    if 'login_handler' not in st.session_state:
        st.session_state.login_handler = LoginEventHandler()
    
    handler = st.session_state.login_handler
    
    # Get dashboard data
    dashboard_data = handler.get_user_dashboard_data(user_id)
    
    st.markdown("### 📊 **Your AI Analysis Dashboard**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Files Analyzed", dashboard_data['files_count'])
    
    with col2:
        quality_score = dashboard_data['data_quality_score']
        quality_percentage = int(quality_score * 100) if quality_score > 0 else 0
        st.metric("Data Quality", f"{quality_percentage}%")
    
    with col3:
        recommendations_count = len(dashboard_data['recommendations'])
        st.metric("Recommendations", recommendations_count)
    
    # Show recent analysis status
    handler.display_screening_status(user_id)
    
    # Manual re-analysis button
    if st.button("🔄 Re-analyze My Data", key=f"reanalyze_{user_id}"):
        with st.spinner("Re-analyzing your data..."):
            handler.handle_user_login(user_id)
            st.rerun()

# Global handler instance
_login_handler = None

def get_login_handler() -> LoginEventHandler:
    """Get global login handler instance"""
    global _login_handler
    if _login_handler is None:
        _login_handler = LoginEventHandler()
    return _login_handler

if __name__ == "__main__":
    # Test the login handler
    handler = LoginEventHandler()
    print("🔐 IntelliCV Login Event Handler Test")
    print("=" * 40)
    
    # Test login handling
    test_result = handler.handle_user_login("test_user_001")
    print(f"Login Result: {json.dumps(test_result, indent=2, default=str)}")