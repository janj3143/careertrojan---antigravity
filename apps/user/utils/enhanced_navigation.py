"""
Enhanced Navigation System for IntelliCV User Portal Final
=========================================================

Provides advanced navigation with grouped sections for:
- Core User Journey
- Career Development Suite
- Intelligence & Analytics
- Community & Networking

Includes visual enhancements, progress tracking, and feature discovery.
"""

import streamlit as st
from typing import Dict, List, Any
from pathlib import Path

class EnhancedNavigation:
    """Advanced navigation system with grouped features"""
    
    def __init__(self):
        self.navigation_config = self._load_navigation_config()
        self.user_progress = self._load_user_progress()
    
    def _load_navigation_config(self) -> Dict[str, Any]:
        """Load navigation configuration with grouped sections"""
        return {
            "core_journey": {
                "title": "🎯 Core User Journey",
                "description": "Essential tools for CV optimization and job matching",
                "icon": "🎯",
                "expanded": True,
                "pages": [
                    {"name": "Resume Upload", "page": "Resume_Upload", "icon": "📄", "description": "Upload and analyze your CV"},
                    {"name": "Profile Manager", "page": "Profile", "icon": "👤", "description": "Manage your professional profile"},
                    {"name": "Job Description", "page": "Job_Description", "icon": "💼", "description": "Analyze target job requirements"},
                    {"name": "Resume Feedback", "page": "Resume_Feedback", "icon": "📊", "description": "Get AI-powered CV feedback"},
                    {"name": "Job Match Insights", "page": "Job_Match_Insights", "icon": "🎯", "description": "See how well you match jobs"},
                    {"name": "Resume History", "page": "Resume_History", "icon": "📚", "description": "Track your CV improvements"},
                    {"name": "Resume Tuner", "page": "Resume_Tuner", "icon": "⚙️", "description": "Fine-tune your CV for roles"},
                    {"name": "Job Tracker", "page": "Job_Tracker", "icon": "📋", "description": "Track your applications"}
                ]
            },
            "career_development": {
                "title": "🚀 Career Development Suite", 
                "description": "Advanced tools for career growth and skill development",
                "icon": "🚀",
                "expanded": False,
                "pages": [
                    {"name": "AI Interview Coach", "page": "AI_Interview_Coach", "icon": "🎯", "description": "Practice interviews with AI feedback", "featured": True},
                    {"name": "Career Intelligence", "page": "Career_Intelligence", "icon": "📊", "description": "Career quadrant positioning & analytics", "featured": True},
                    {"name": "Advanced Career Tools", "page": "Advanced_Career_Tools", "icon": "🛠️", "description": "Salary analysis & market intelligence"}
                ]
            },
            "community_networking": {
                "title": "🤝 Community & Networking",
                "description": "Connect, learn, and grow with professionals",
                "icon": "🤝", 
                "expanded": False,
                "pages": [
                    {"name": "Mentorship Hub", "page": "Mentorship_Hub", "icon": "🤝", "description": "Find mentors and networking opportunities", "featured": True}
                ]
            }
        }
    
    def _load_user_progress(self) -> Dict[str, Any]:
        """Load user progress and engagement data"""
        # In production, this would load from user database
        return {
            "completion_rates": {
                "Resume_Upload": 100,
                "Profile": 85, 
                "Job_Description": 75,
                "Resume_Feedback": 60,
                "Job_Match_Insights": 45,
                "AI_Interview_Coach": 25,
                "Career_Intelligence": 10,
                "Mentorship_Hub": 5
            },
            "engagement_score": 350,
            "level": "Active User",
            "streak_days": 7
        }
    
    def render_enhanced_sidebar(self):
        """Render the enhanced sidebar with grouped navigation"""
        
        # Sidebar header with user info
        st.sidebar.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">🚀 IntelliCV</h2>
            <p style="color: white; margin: 5px 0 0 0; opacity: 0.9;">Your Career Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # User engagement status
        self._render_user_status()
        
        # Navigation sections
        for section_key, section_data in self.navigation_config.items():
            self._render_navigation_section(section_key, section_data)
        
        # Quick actions
        self._render_quick_actions()
        
        # Footer
        self._render_sidebar_footer()
    
    def _render_user_status(self):
        """Render user engagement and progress status"""
        st.sidebar.markdown("### 👤 Your Progress")
        
        # Progress metrics
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            st.metric("Level", self.user_progress["level"])
        with col2:
            st.metric("Streak", f"{self.user_progress['streak_days']} days")
        
        # Overall completion
        completed_pages = sum(1 for rate in self.user_progress["completion_rates"].values() if rate > 80)
        total_pages = len(self.user_progress["completion_rates"])
        completion_rate = (completed_pages / total_pages) * 100
        
        st.sidebar.progress(completion_rate / 100, text=f"Platform Mastery: {completion_rate:.0f}%")
        
        st.sidebar.markdown("---")
    
    def _render_navigation_section(self, section_key: str, section_data: Dict[str, Any]):
        """Render a navigation section with pages"""
        
        # Section header
        with st.sidebar.expander(
            f"{section_data['icon']} {section_data['title']}", 
            expanded=section_data.get('expanded', False)
        ):
            st.markdown(f"*{section_data['description']}*")
            st.markdown("")
            
            # Render pages in section
            for page_data in section_data["pages"]:
                self._render_navigation_item(page_data)
    
    def _render_navigation_item(self, page_data: Dict[str, Any]):
        """Render individual navigation item with progress and features"""
        
        page_name = page_data["page"]
        display_name = page_data["name"]
        icon = page_data["icon"]
        description = page_data["description"]
        
        # Get completion rate
        completion = self.user_progress["completion_rates"].get(page_name, 0)
        
        # Create navigation button with styling
        is_current = st.session_state.get("current_page") == page_name
        
        # Button styling based on completion and current page
        if is_current:
            button_style = "🔹"
        elif completion >= 80:
            button_style = "✅"
        elif completion >= 40:
            button_style = "🟡"
        else:
            button_style = "⚪"
        
        # Featured indicator
        featured = page_data.get("featured", False)
        featured_indicator = " 🌟" if featured else ""
        
        # Navigation button
        if st.button(
            f"{button_style} {icon} {display_name}{featured_indicator}",
            key=f"nav_{page_name}",
            help=f"{description} (Progress: {completion}%)",
            use_container_width=True
        ):
            st.session_state.current_page = page_name
            st.rerun()
        
        # Progress bar for incomplete items
        if completion < 100 and completion > 0:
            st.progress(completion / 100, text=f"{completion}% complete")
        
        st.markdown("")
    
    def _render_quick_actions(self):
        """Render quick action buttons"""
        st.sidebar.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🎯 AI Coach", help="Start interview practice", use_container_width=True):
                st.session_state.current_page = "AI_Interview_Coach"
                st.rerun()
        
        with col2:
            if st.button("📊 Intelligence", help="View career analytics", use_container_width=True):
                st.session_state.current_page = "Career_Intelligence"
                st.rerun()
        
        st.sidebar.markdown("---")
    
    def _render_sidebar_footer(self):
        """Render sidebar footer with system info"""
        st.sidebar.markdown("### ⚙️ Account")
        
        # User actions
        if st.sidebar.button("🔒 Logout", use_container_width=True):
            # This would call the logout function
            st.session_state.authenticated_user = False
            st.session_state.current_page = "Landing"
            st.rerun()
        
        # System info
        st.sidebar.markdown("---")
        st.sidebar.caption("🚀 IntelliCV-AI | Enhanced Portal v2.0")
        
        # Debug toggle
        if st.sidebar.checkbox("🔧 Debug Mode", value=st.session_state.get("debug_mode", False)):
            st.session_state.debug_mode = True
        else:
            st.session_state.debug_mode = False

def render_enhanced_navigation():
    """Main function to render enhanced navigation"""
    nav_system = EnhancedNavigation()
    nav_system.render_enhanced_sidebar()

def inject_navigation_css():
    """Inject CSS for enhanced navigation styling"""
    st.markdown("""
    <style>
    /* Enhanced sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Navigation button enhancements */
    .stButton > button {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #dee2e6;
        border-radius: 8px;
        transition: all 0.3s ease;
        text-align: left;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-color: #2196f3;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2);
    }
    
    /* Featured item styling */
    .stButton > button:contains("🌟") {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-color: #ff9800;
    }
    
    /* Progress indicators */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4caf50 0%, #8bc34a 100%);
    }
    
    /* Expander enhancements */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f5f5f5 0%, #eeeeee 100%);
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# Export main functions
__all__ = ["render_enhanced_navigation", "inject_navigation_css", "EnhancedNavigation"]