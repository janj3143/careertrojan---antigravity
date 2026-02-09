import streamlit as st
from typing import Dict, List, Optional
import json
import time

# =============================================================================
# INTERACTIVE NAVIGATION SYSTEM - IntelliCV-AI Admin Portal
# Features: Hover help, query system, guided navigation
# =============================================================================

class InteractiveNavigation:
    """Interactive navigation with help system and query processing"""
    
    def __init__(self):
        self.navigation_data = self._load_navigation_config()
        self.help_system = HelpSystem()
    
    def _load_navigation_config(self) -> Dict:
        """Load navigation configuration with help data"""
        return {
            "main_sections": {
                "🏠 Admin Home": {
                    "description": "Main dashboard with system overview and quick actions",
                    "features": [
                        "System status monitoring",
                        "Quick service controls",
                        "Recent activity logs",
                        "Performance metrics"
                    ],
                    "help_text": "The Admin Home provides a comprehensive overview of your IntelliCV-AI system. Monitor all services, check system health, and perform quick administrative tasks.",
                    "quick_actions": [
                        "Start/Stop Backend Services",
                        "View System Logs",
                        "Check Database Status",
                        "Monitor Performance"
                    ]
                },
                "👥 User Management": {
                    "description": "Manage admin and user accounts with advanced security controls",
                    "features": [
                        "Create/edit admin accounts",
                        "Manage user permissions",
                        "Monitor user activity",
                        "Security audit logs"
                    ],
                    "help_text": "Comprehensive user management system with role-based access control, session monitoring, and security auditing capabilities.",
                    "quick_actions": [
                        "Add New Admin",
                        "Reset User Password",
                        "View Login History",
                        "Export User Data"
                    ]
                },
                "🔧 Service Management": {
                    "description": "Control and monitor all backend services, databases, and containers",
                    "features": [
                        "Backend API management",
                        "PostgreSQL database control",
                        "Redis cache management",
                        "Docker container orchestration"
                    ],
                    "help_text": "Centralized service management for all IntelliCV-AI components. Start, stop, monitor, and troubleshoot services from one interface.",
                    "quick_actions": [
                        "Start Backend API",
                        "Backup Databases",
                        "Clear Redis Cache",
                        "Restart Containers"
                    ]
                },
                "📊 Analytics Dashboard": {
                    "description": "Comprehensive analytics and reporting system",
                    "features": [
                        "User engagement metrics",
                        "System performance analytics",
                        "Usage statistics",
                        "Custom reports"
                    ],
                    "help_text": "Advanced analytics dashboard providing insights into system usage, performance trends, and user behavior patterns.",
                    "quick_actions": [
                        "Generate Usage Report",
                        "Export Analytics Data",
                        "View Performance Trends",
                        "Create Custom Dashboard"
                    ]
                },
                "🛠️ System Tools": {
                    "description": "Advanced system administration and maintenance tools",
                    "features": [
                        "Database maintenance",
                        "Log file management",
                        "System cleanup utilities",
                        "Backup and restore"
                    ],
                    "help_text": "Professional system administration tools for maintaining optimal performance and data integrity.",
                    "quick_actions": [
                        "Run System Cleanup",
                        "Schedule Backups",
                        "Analyze Log Files",
                        "Optimize Database"
                    ]
                },
                "📈 Performance Monitor": {
                    "description": "Real-time system performance monitoring and alerting",
                    "features": [
                        "CPU and memory monitoring",
                        "Database performance metrics",
                        "API response time tracking",
                        "Alert configuration"
                    ],
                    "help_text": "Comprehensive performance monitoring with real-time metrics, historical trends, and intelligent alerting.",
                    "quick_actions": [
                        "View Real-time Metrics",
                        "Configure Alerts",
                        "Export Performance Data",
                        "Run Performance Test"
                    ]
                }
            },
            "common_queries": {
                "How do I start the backend?": {
                    "section": "Service Management",
                    "steps": [
                        "Navigate to Service Management page",
                        "Click on 'Backend Services' tab",
                        "Click 'Start Backend' button",
                        "Monitor status in real-time dashboard"
                    ]
                },
                "How do I add a new admin user?": {
                    "section": "User Management", 
                    "steps": [
                        "Go to User Management page",
                        "Click 'Add New Admin' button",
                        "Fill in user details and permissions",
                        "Send invitation email to new admin"
                    ]
                },
                "How do I backup the database?": {
                    "section": "Service Management",
                    "steps": [
                        "Navigate to Service Management",
                        "Select PostgreSQL tab",
                        "Choose database to backup",
                        "Click 'Backup DB' and wait for completion"
                    ]
                },
                "How do I view system logs?": {
                    "section": "System Tools",
                    "steps": [
                        "Go to System Tools page",
                        "Select 'Log Management' section",
                        "Choose log type (Backend, Database, etc.)",
                        "Filter by date range and severity"
                    ]
                }
            }
        }
    
    def get_section_help(self, section_name: str) -> Optional[Dict]:
        """Get help information for a specific section"""
        return self.navigation_data["main_sections"].get(section_name)
    
    def search_help(self, query: str) -> List[Dict]:
        """Search help content based on user query"""
        results = []
        query_lower = query.lower()
        
        # Search in common queries
        for question, info in self.navigation_data["common_queries"].items():
            if query_lower in question.lower():
                results.append({
                    "type": "common_query",
                    "question": question,
                    "section": info["section"],
                    "steps": info["steps"]
                })
        
        # Search in section descriptions
        for section, data in self.navigation_data["main_sections"].items():
            if (query_lower in data["description"].lower() or 
                query_lower in data["help_text"].lower() or
                any(query_lower in feature.lower() for feature in data["features"])):
                results.append({
                    "type": "section_match",
                    "section": section,
                    "description": data["description"],
                    "help_text": data["help_text"],
                    "features": data["features"]
                })
        
        return results

class HelpSystem:
    """Interactive help system with guided tutorials"""
    
    def __init__(self):
        self.tutorials = self._load_tutorials()
    
    def _load_tutorials(self) -> Dict:
        """Load interactive tutorials"""
        return {
            "first_time_setup": {
                "title": "🚀 First Time Setup Guide",
                "description": "Complete setup guide for new IntelliCV-AI administrators",
                "steps": [
                    {
                        "title": "Change Default Password",
                        "description": "Secure your admin account with a strong password",
                        "action": "Navigate to login and change default password",
                        "estimated_time": "2 minutes"
                    },
                    {
                        "title": "Enable Two-Factor Authentication",
                        "description": "Add an extra layer of security to your account",
                        "action": "Set up 2FA in User Management settings",
                        "estimated_time": "3 minutes"
                    },
                    {
                        "title": "Start Backend Services",
                        "description": "Initialize all core system services",
                        "action": "Use Service Management to start database and API services",
                        "estimated_time": "5 minutes"
                    },
                    {
                        "title": "Configure System Monitoring",
                        "description": "Set up alerts and monitoring thresholds",
                        "action": "Configure alerts in Performance Monitor",
                        "estimated_time": "10 minutes"
                    }
                ]
            },
            "daily_operations": {
                "title": "📅 Daily Operations Checklist",
                "description": "Recommended daily maintenance tasks",
                "steps": [
                    {
                        "title": "Check System Status",
                        "description": "Verify all services are running properly",
                        "action": "Review Admin Home dashboard",
                        "estimated_time": "2 minutes"
                    },
                    {
                        "title": "Review Performance Metrics",
                        "description": "Monitor system performance and resource usage",
                        "action": "Check Performance Monitor for any alerts",
                        "estimated_time": "3 minutes"
                    },
                    {
                        "title": "Check Error Logs",
                        "description": "Review system logs for any issues",
                        "action": "Use System Tools to analyze recent logs",
                        "estimated_time": "5 minutes"
                    }
                ]
            }
        }
    
    def get_tutorial(self, tutorial_name: str) -> Optional[Dict]:
        """Get specific tutorial"""
        return self.tutorials.get(tutorial_name)
    
    def get_contextual_help(self, current_page: str) -> Dict:
        """Get contextual help based on current page"""
        help_content = {
            "general_tips": [
                "Use the search box in the top-right to quickly find information",
                "Hover over any navigation item for detailed descriptions",
                "Check the Performance Monitor regularly for system health",
                "Always backup your data before making major changes"
            ],
            "keyboard_shortcuts": {
                "Ctrl + R": "Refresh current page",
                "Ctrl + F": "Search within page content",
                "Esc": "Close open dialogs or modals"
            }
        }
        
        # Add page-specific help
        if "home" in current_page.lower():
            help_content["page_specific"] = [
                "The dashboard updates automatically every 30 seconds",
                "Red indicators require immediate attention",
                "Use Quick Actions for common administrative tasks"
            ]
        elif "service" in current_page.lower():
            help_content["page_specific"] = [
                "Always check dependencies before stopping services",
                "Use 'Test Connection' before making changes",
                "Monitor logs when starting/stopping services"
            ]
        
        return help_content

def render_navigation_header():
    """Render interactive navigation header with help system"""
    
    # Initialize navigation system
    if 'nav_system' not in st.session_state:
        st.session_state.nav_system = InteractiveNavigation()
    
    nav = st.session_state.nav_system
    
    # Custom CSS for navigation
    st.markdown("""
    <style>
    .nav-header {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(30, 60, 114, 0.1));
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(0, 212, 255, 0.3);
        margin-bottom: 1rem;
    }
    
    .help-tooltip {
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.9rem;
        max-width: 300px;
    }
    
    .nav-search {
        position: relative;
    }
    
    .quick-help {
        background: rgba(0, 212, 255, 0.1);
        border-left: 4px solid #00d4ff;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation header
    st.markdown('<div class="nav-header">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        st.markdown("### 🧭 Navigation Guide")
        if st.checkbox("Show section details", key="show_nav_details"):
            render_section_details(nav)
    
    with col2:
        st.markdown("### 🔍 Quick Help")
        query = st.text_input("Ask a question or search help...", 
                             placeholder="e.g., How do I start the backend?",
                             key="help_query")
        
        if query:
            render_help_results(nav, query)
    
    with col3:
        st.markdown("### 📚 Tutorials")
        if st.button("🚀 First Setup", help="Complete setup guide"):
            st.session_state.show_tutorial = "first_time_setup"
        
        if st.button("📅 Daily Tasks", help="Daily operations checklist"):
            st.session_state.show_tutorial = "daily_operations"
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show tutorial if requested
    if st.session_state.get('show_tutorial'):
        render_tutorial(nav.help_system, st.session_state.show_tutorial)

def render_section_details(nav: InteractiveNavigation):
    """Render detailed section information"""
    
    with st.expander("📋 All Sections Overview", expanded=False):
        for section, data in nav.navigation_data["main_sections"].items():
            st.markdown(f"**{section}**")
            st.write(data["description"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("*Features:*")
                for feature in data["features"]:
                    st.write(f"• {feature}")
            
            with col2:
                st.markdown("*Quick Actions:*")
                for action in data["quick_actions"]:
                    if st.button(f"🚀 {action}", key=f"action_{action.replace(' ', '_')}"):
                        st.info(f"Navigating to {action}...")
            
            with st.expander(f"Help for {section}", expanded=False):
                st.info(data["help_text"])
            
            st.markdown("---")

def render_help_results(nav: InteractiveNavigation, query: str):
    """Render help search results"""
    
    results = nav.search_help(query)
    
    if results:
        for result in results:
            if result["type"] == "common_query":
                st.markdown('<div class="quick-help">', unsafe_allow_html=True)
                st.markdown(f"**❓ {result['question']}**")
                st.markdown(f"*Section: {result['section']}*")
                
                for i, step in enumerate(result["steps"], 1):
                    st.write(f"{i}. {step}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            elif result["type"] == "section_match":
                with st.expander(f"📍 {result['section']}", expanded=True):
                    st.write(result["description"])
                    st.info(result["help_text"])
                    
                    st.markdown("**Features:**")
                    for feature in result["features"]:
                        st.write(f"• {feature}")
    else:
        st.warning("No help results found. Try different keywords or check the tutorials.")

def render_tutorial(help_system: HelpSystem, tutorial_name: str):
    """Render interactive tutorial"""
    
    tutorial = help_system.get_tutorial(tutorial_name)
    
    if tutorial:
        with st.expander(f"{tutorial['title']}", expanded=True):
            st.write(tutorial["description"])
            
            total_time = sum(int(step.get("estimated_time", "5").split()[0]) 
                           for step in tutorial["steps"])
            st.info(f"⏱️ Estimated completion time: {total_time} minutes")
            
            for i, step in enumerate(tutorial["steps"], 1):
                with st.container():
                    col1, col2, col3 = st.columns([1, 4, 1])
                    
                    with col1:
                        st.markdown(f"**Step {i}**")
                    
                    with col2:
                        st.markdown(f"**{step['title']}**")
                        st.write(step["description"])
                        st.caption(f"🎯 Action: {step['action']}")
                        st.caption(f"⏱️ Time: {step['estimated_time']}")
                    
                    with col3:
                        if st.button("✅", key=f"complete_step_{i}", 
                                   help="Mark as completed"):
                            st.success("Step completed!")
                    
                    st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏃‍♂️ Start Tutorial", use_container_width=True):
                    st.info("Tutorial started! Follow the steps above.")
            
            with col2:
                if st.button("❌ Close Tutorial", use_container_width=True):
                    st.session_state.show_tutorial = None
                    st.rerun()

def render_contextual_help_sidebar():
    """Render contextual help in sidebar"""
    
    with st.sidebar:
        st.markdown("### 🆘 Quick Help")
        
        # Get current page context
        current_page = st.session_state.get('current_page', 'home')
        help_system = HelpSystem()
        help_content = help_system.get_contextual_help(current_page)
        
        # General tips
        with st.expander("💡 General Tips", expanded=False):
            for tip in help_content["general_tips"]:
                st.write(f"• {tip}")
        
        # Keyboard shortcuts
        with st.expander("⌨️ Shortcuts", expanded=False):
            for shortcut, description in help_content["keyboard_shortcuts"].items():
                st.code(f"{shortcut}: {description}")
        
        # Page-specific help
        if "page_specific" in help_content:
            with st.expander("📍 Page Help", expanded=True):
                for tip in help_content["page_specific"]:
                    st.write(f"• {tip}")
        
        # Emergency contacts (for production)
        st.markdown("---")
        st.markdown("### 🚨 Emergency Support")
        st.info("📞 Admin Hotline: +1-800-SUPPORT")
        st.info("📧 Support: admin@intellicv-ai.com")
        
        # System status indicator
        st.markdown("---")
        st.markdown("### 🎛️ System Status")
        
        # Mock system status
        status_color = "🟢" if time.time() % 10 < 8 else "🟡"
        st.markdown(f"{status_color} System Status: Operational")
        
        if st.button("📊 View Full Status", use_container_width=True):
            st.session_state.current_page = "system_status"
            st.rerun()

def render_floating_help_widget():
    """Render floating help widget"""
    
    # CSS for floating widget
    st.markdown("""
    <style>
    .floating-help {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: linear-gradient(135deg, #00d4ff, #1e3c72);
        color: white;
        border-radius: 50px;
        padding: 15px;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
        cursor: pointer;
        z-index: 1000;
        font-size: 1.2rem;
        transition: all 0.3s ease;
    }
    
    .floating-help:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 30px rgba(0, 212, 255, 0.5);
    }
    </style>
    
    <div class="floating-help" onclick="alert('Help system activated!')">
        🆘
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# MAIN NAVIGATION INTEGRATION
# =============================================================================

def initialize_navigation_system():
    """Initialize the complete navigation system"""
    
    # Set up navigation in session state
    if 'navigation_initialized' not in st.session_state:
        st.session_state.navigation_initialized = True
        st.session_state.nav_system = InteractiveNavigation()
        st.session_state.current_page = 'home'
    
    # Render components
    render_navigation_header()
    render_contextual_help_sidebar()
    render_floating_help_widget()

def get_navigation_system() -> InteractiveNavigation:
    """Get the navigation system instance"""
    if 'nav_system' not in st.session_state:
        st.session_state.nav_system = InteractiveNavigation()
    return st.session_state.nav_system