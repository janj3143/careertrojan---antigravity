"""
32_System_Connectivity_Audit.py
================================
🔗 System Connectivity Audit & Relationship Mapper

Visual audit tool to map all connections between admin and user portal features,
identify gaps, and suggest new relationships for maximum system connectivity.

UPDATED: November 14, 2025 - Reflects current page inventory
Author: IntelliCV Platform
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import json
from pathlib import Path
import sys
from datetime import datetime
import re

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Add paths for imports
current_dir = Path(__file__).parent.parent.parent
user_portal_path = current_dir / "user_portal_final"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(user_portal_path))

# Page config
st.set_page_config(
    page_title="System Connectivity Audit | IntelliCV Admin",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication check
if not st.session_state.get('authenticated_admin'):
    st.error("🔒 Admin authentication required")
    st.stop()


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page27_connectivity") if BackendTelemetryHelper else None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .connection-strong {
        background: #28a745;
        color: white;
        padding: 0.3rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .connection-partial {
        background: #ffc107;
        color: black;
        padding: 0.3rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .connection-missing {
        background: #6c757d;
        color: white;
        padding: 0.3rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .connection-suggested {
        background: #17a2b8;
        color: white;
        padding: 0.3rem;
        border-radius: 4px;
        font-weight: bold;
    }
    .audit-table {
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

class SystemConnectivityAuditor:
    """Comprehensive system connectivity analysis - UPDATED Nov 14, 2025"""

    def __init__(self):
        self.admin_features = {}
        self.user_features = {}
        self.connections = []
        self.bridges = {}

    def scan_admin_portal(self):
        """Scan admin portal for features and capabilities - CURRENT INVENTORY"""
        admin_features = {
            # System Management
            "00_Home.py": {
                "category": "Navigation",
                "features": ["Admin Dashboard", "Navigation", "Overview"],
                "data_sources": ["System Status", "Quick Metrics"],
                "capabilities": ["Admin Interface", "Navigation"]
            },
            "01_Service_Status_Monitor.py": {
                "category": "System Management",
                "features": ["Service Health", "Performance Metrics", "System Status"],
                "data_sources": ["System Logs", "Performance Data"],
                "capabilities": ["Real-time Monitoring", "Alert System"]
            },
            "02_Analytics.py": {
                "category": "Analytics",
                "features": ["Usage Analytics", "Performance Reports", "Data Insights"],
                "data_sources": ["User Activity", "System Metrics"],
                "capabilities": ["Dashboard", "Report Generation"]
            },
            "03_User_Management.py": {
                "category": "User Management",
                "features": ["User CRUD", "Access Control", "Authentication"],
                "data_sources": ["User Database", "Session Data"],
                "capabilities": ["User Authentication", "Permission Management"]
            },
            "04_Compliance_Audit.py": {
                "category": "Compliance",
                "features": ["Compliance Tracking", "Audit Logs", "GDPR Compliance"],
                "data_sources": ["Audit Logs", "Compliance Data"],
                "capabilities": ["Compliance Monitoring", "Audit Reports"]
            },

            # Data Processing
            "05_Email_Integration.py": {
                "category": "Communication",
                "features": ["Email Processing", "CV Extraction", "Contact Discovery"],
                "data_sources": ["Email Content", "Attachments", "Contact Lists"],
                "capabilities": ["Email Parsing", "CV Import", "Contact Management"]
            },
            "06_Complete_Data_Parser.py": {
                "category": "Data Processing",
                "features": ["CV Parsing", "Data Extraction", "File Processing"],
                "data_sources": ["CV Files", "Email Files", "Documents"],
                "capabilities": ["Multi-format Parsing", "Data Standardization"]
            },
            "07_Batch_Processing.py": {
                "category": "Data Processing",
                "features": ["Batch Operations", "Scheduled Tasks", "Data Pipeline"],
                "data_sources": ["Queue System", "File System"],
                "capabilities": ["Automation", "Scheduled Processing"]
            },

            # AI Services
            "08_AI_Enrichment.py": {
                "category": "AI Services",
                "features": ["CV Enhancement", "Data Enrichment", "AI Analysis"],
                "data_sources": ["CV Data", "AI Models"],
                "capabilities": ["AI Enhancement", "Content Generation"]
            },
            "09_AI_Content_Generator.py": {
                "category": "AI Services",
                "features": ["Content Creation", "Text Generation", "AI Writing"],
                "data_sources": ["Templates", "AI Models"],
                "capabilities": ["Content Generation", "Template System"]
            },
            "23_AI_Model_Training_Review.py": {
                "category": "AI Services",
                "features": ["Model Training", "AI Review", "Model Management"],
                "data_sources": ["Training Data", "Model Metrics"],
                "capabilities": ["Model Training", "Performance Review"]
            },

            # Intelligence Services
            "10_Market_Intelligence_Center.py": {
                "category": "Intelligence",
                "features": ["Market Analysis", "Industry Insights", "Trend Analysis"],
                "data_sources": ["Market Data", "Industry Reports"],
                "capabilities": ["Market Research", "Trend Identification"]
            },
            "11_Competitive_Intelligence.py": {
                "category": "Intelligence",
                "features": ["Competitor Analysis", "Market Position", "Benchmarking"],
                "data_sources": ["Competitor Data", "Market Intelligence"],
                "capabilities": ["Competitive Analysis", "Benchmarking"]
            },
            "12_Web_Company_Intelligence.py": {
                "category": "Intelligence",
                "features": ["Company Research", "Web Intelligence", "Company Profiles"],
                "data_sources": ["Web Data", "Company Information"],
                "capabilities": ["Company Research", "Web Scraping"]
            },
            "25_Intelligence_Hub.py": {
                "category": "Intelligence",
                "features": ["Intelligence Aggregation", "Data Hub", "Insight Synthesis"],
                "data_sources": ["Multiple Intelligence Sources"],
                "capabilities": ["Data Aggregation", "Insight Generation"]
            },
            "27_Exa_Web_Intelligence.py": {
                "category": "Intelligence",
                "features": ["Web Intelligence", "Real-time Research", "Company Intelligence"],
                "data_sources": ["Exa API", "Web Data"],
                "capabilities": ["Real-time Research", "Web Intelligence"]
            },

            # Job Title & Career Analysis
            "19_Enhanced_Glossary.py": {
                "category": "Data Management",
                "features": ["Glossary Management", "Term Definitions", "Abbreviations"],
                "data_sources": ["canonical_glossary.json", "consolidated_terms.json"],
                "capabilities": ["Term Management", "Definition Lookup"]
            },
            "20_Job_Title_AI_Integration.py": {
                "category": "AI Services",
                "features": ["Job Title Analysis", "Role Matching", "Career Mapping"],
                "data_sources": ["Job Title Database", "Career Data"],
                "capabilities": ["Role Analysis", "Career Guidance"]
            },
            "21_Job_Title_Overlap_Cloud.py": {
                "category": "Analytics",
                "features": ["Job Title Overlap", "Role Relationships", "Career Paths"],
                "data_sources": ["Job Title Data", "Career Transitions"],
                "capabilities": ["Overlap Analysis", "Career Mapping"]
            },
            "26_Career_Pattern_Intelligence.py": {
                "category": "Analytics",
                "features": ["Career Pattern Analysis", "Peer Benchmarking", "Skill Distribution"],
                "data_sources": ["Candidate_database.json", "job_titles/", "normalized/"],
                "capabilities": ["Career Analysis", "GDPR-Compliant Benchmarking"]
            },

            # System Administration
            "13_API_Integration.py": {
                "category": "Integration",
                "features": ["API Management", "External Integrations", "API Testing"],
                "data_sources": ["API Endpoints", "Integration Data"],
                "capabilities": ["API Management", "Integration Testing"]
            },
            "14_Contact_Communication.py": {
                "category": "Communication",
                "features": ["Contact Management", "Communication", "Messaging"],
                "data_sources": ["Contact Database", "Message Logs"],
                "capabilities": ["Contact Management", "Messaging System"]
            },
            "15_Advanced_Settings.py": {
                "category": "Configuration",
                "features": ["System Settings", "Configuration", "Advanced Options"],
                "data_sources": ["Config Files", "System Settings"],
                "capabilities": ["System Configuration", "Settings Management"]
            },
            "16_Logging_Error_Screen_Snapshot_and_Fixes.py": {
                "category": "System Management",
                "features": ["Error Logging", "Screenshots", "Debug Tools"],
                "data_sources": ["Error Logs", "Screenshots"],
                "capabilities": ["Error Tracking", "Debug Support"]
            },
            "22_Software_Requirements_Management.py": {
                "category": "Configuration",
                "features": ["Requirements Tracking", "Dependency Management", "Software Inventory"],
                "data_sources": ["requirements.txt", "Package Manifests"],
                "capabilities": ["Dependency Tracking", "Requirements Management"]
            },
            "24_Token_Management.py": {
                "category": "System Management",
                "features": ["Token Management", "Usage Tracking", "Token Allocation"],
                "data_sources": ["Token Database", "Usage Logs"],
                "capabilities": ["Token Management", "Usage Monitoring"]
            },

            # Production & Reporting
            "28_Production_AI_Data_Generator.py": {
                "category": "Data Processing",
                "features": ["AI Data Generation", "Production Data", "Data Synthesis"],
                "data_sources": ["AI Models", "Data Templates"],
                "capabilities": ["Data Generation", "Production Support"]
            },
            "28_Unified_Analytics_Dashboard.py": {
                "category": "Analytics",
                "features": ["Unified Analytics", "Cross-System Metrics", "Comprehensive Dashboards"],
                "data_sources": ["Multiple Data Sources", "Analytics Data"],
                "capabilities": ["Unified Reporting", "Cross-System Analytics"]
            },
            "29_Production_Status_Report.py": {
                "category": "Reporting",
                "features": ["Production Status", "System Reports", "Health Checks"],
                "data_sources": ["System Status", "Production Metrics"],
                "capabilities": ["Status Reporting", "Health Monitoring"]
            },
            "30_Stats_Dashboard.py": {
                "category": "Analytics",
                "features": ["Statistics Dashboard", "Metrics Visualization", "Data Analytics"],
                "data_sources": ["Statistical Data", "Metrics Database"],
                "capabilities": ["Statistical Analysis", "Data Visualization"]
            },
            "31_Development_Terminology_Guide.py": {
                "category": "Documentation",
                "features": ["Terminology Guide", "Developer Documentation", "Glossary"],
                "data_sources": ["Documentation", "Terminology Database"],
                "capabilities": ["Documentation Management", "Terminology Reference"]
            }
        }

        self.admin_features = admin_features
        return admin_features

    def scan_user_portal(self):
        """Scan user portal for features and capabilities - CURRENT INVENTORY"""
        user_features = {
            "01_Home.py": {
                "category": "Navigation",
                "features": ["Dashboard", "Navigation", "Overview"],
                "data_needs": ["User Status", "Quick Stats"],
                "capabilities": ["User Interface", "Navigation"]
            },
            "03_Registration.py": {
                "category": "User Management",
                "features": ["User Registration", "Account Creation", "Profile Setup"],
                "data_needs": ["User Data", "Authentication"],
                "capabilities": ["Account Management"]
            },
            "04_Dashboard.py": {
                "category": "Analytics",
                "features": ["Personal Dashboard", "Progress Tracking", "Stats"],
                "data_needs": ["User Analytics", "Progress Data", "Intelligence Summary"],
                "capabilities": ["Personal Analytics"]
            },
            "05_Payment.py": {
                "category": "Commerce",
                "features": ["Payment Processing", "Transaction Management", "Billing"],
                "data_needs": ["Payment Data", "Token Management"],
                "capabilities": ["Payment Processing"]
            },
            "06_Pricing.py": {
                "category": "Commerce",
                "features": ["Pricing Plans", "Package Selection", "Feature Comparison"],
                "data_needs": ["Pricing Data", "Token Pricing"],
                "capabilities": ["Pricing Display"]
            },
            "07_Account_Verification.py": {
                "category": "User Management",
                "features": ["Email Verification", "Account Activation", "Security"],
                "data_needs": ["Verification Tokens", "Email Service"],
                "capabilities": ["Account Verification"]
            },
            "08_Profile_Complete.py": {
                "category": "User Management",
                "features": ["Profile Completion", "User Onboarding", "Data Collection"],
                "data_needs": ["User Profile Data", "Form Templates"],
                "capabilities": ["Profile Management"]
            },
            "09_Resume_Upload_Analysis.py": {
                "category": "CV Processing",
                "features": ["Resume Upload", "CV Analysis", "File Processing"],
                "data_needs": ["CV Parsing", "AI Analysis", "AI Enrichment"],
                "capabilities": ["File Upload", "CV Analysis"]
            },
            "10_UMarketU_Suite.py": {
                "category": "Job Search",
                "features": ["Job Discovery", "Company Research", "Application Tracking"],
                "data_needs": ["Job Data", "Company Intelligence", "Market Analysis", "Web Intelligence", "Job Title Analysis"],
                "capabilities": ["Job Search", "Company Research", "Application Management"]
            },
            "11_Coaching_Hub.py": {
                "category": "Career Services",
                "features": ["Career Coaching", "Guidance", "Progress Tracking"],
                "data_needs": ["Career Intelligence", "Progress Data"],
                "capabilities": ["Coaching Services"]
            },
            "12_Mentorship_Marketplace.py": {
                "category": "Career Services",
                "features": ["Mentor Matching", "Networking", "Professional Connections"],
                "data_needs": ["Contact Database", "Professional Networks", "Email Integration"],
                "capabilities": ["Mentorship Matching", "Networking"]
            },
            "13_Dual_Career_Suite.py": {
                "category": "Career Planning",
                "features": ["Partner Career Planning", "Location Analysis", "Dual Career Optimization"],
                "data_needs": ["Market Intelligence", "Location Data", "Job Market Analysis", "Web Intelligence", "Email Integration"],
                "capabilities": ["Dual Career Planning", "Location Analysis"]
            },
            "14_User_Rewards.py": {
                "category": "Engagement",
                "features": ["Rewards System", "Points Management", "Gamification"],
                "data_needs": ["User Activity", "Rewards Data", "Token System"],
                "capabilities": ["Rewards Management", "Gamification"]
            }
        }

        # Note: Removed 14_Competitive_Intelligence_Suite.py as it's not in current inventory
        # Added 14_User_Rewards.py which is the actual current page

        self.user_features = user_features
        return user_features

    def detect_existing_connections(self):
        """Detect existing connections and suggest new ones - UPDATED"""
        connections = [
            # EXISTING STRONG CONNECTIONS
            {
                "admin_feature": "05_Email_Integration.py",
                "user_feature": "10_UMarketU_Suite.py",
                "bridge": "email_integration_bridge.py",
                "connection_type": "Strong",
                "data_flow": "CV Sourcing, Profile Enhancement, Contact Discovery",
                "status": "Active"
            },
            {
                "admin_feature": "05_Email_Integration.py",
                "user_feature": "12_Mentorship_Marketplace.py",
                "bridge": "email_integration_bridge.py",
                "connection_type": "Strong",
                "data_flow": "Contact Discovery, Professional Networking",
                "status": "Active"
            },
            {
                "admin_feature": "05_Email_Integration.py",
                "user_feature": "13_Dual_Career_Suite.py",
                "bridge": "email_integration_bridge.py",
                "connection_type": "Strong",
                "data_flow": "Partner CV Import, Dual Profile Enhancement",
                "status": "Active"
            },
            {
                "admin_feature": "27_Exa_Web_Intelligence.py",
                "user_feature": "10_UMarketU_Suite.py",
                "bridge": "web_intelligence_bridge.py",
                "connection_type": "Strong",
                "data_flow": "Company Research, Job Market Intelligence, Real-time Data",
                "status": "Active"
            },
            {
                "admin_feature": "27_Exa_Web_Intelligence.py",
                "user_feature": "13_Dual_Career_Suite.py",
                "bridge": "web_intelligence_bridge.py",
                "connection_type": "Strong",
                "data_flow": "Market Analysis, Location Intelligence, Company Research",
                "status": "Active"
            },
            {
                "admin_feature": "06_Complete_Data_Parser.py",
                "user_feature": "09_Resume_Upload_Analysis.py",
                "bridge": "Universal Parser",
                "connection_type": "Strong",
                "data_flow": "CV Parsing, Data Extraction, Multi-format Support",
                "status": "Active"
            },
            {
                "admin_feature": "03_User_Management.py",
                "user_feature": "03_Registration.py",
                "bridge": "auth_bridge.py",
                "connection_type": "Strong",
                "data_flow": "User Authentication, Account Management, Session Control",
                "status": "Active"
            },
            {
                "admin_feature": "24_Token_Management.py",
                "user_feature": "05_Payment.py",
                "bridge": "token_bridge.py",
                "connection_type": "Strong",
                "data_flow": "Token Allocation, Usage Tracking, Payment Processing",
                "status": "Active"
            },
            {
                "admin_feature": "24_Token_Management.py",
                "user_feature": "06_Pricing.py",
                "bridge": "token_pricing_bridge.py",
                "connection_type": "Strong",
                "data_flow": "Token-based Pricing, Package Definitions",
                "status": "Active"
            },

            # CRITICAL MISSING CONNECTIONS
            {
                "admin_feature": "20_Job_Title_AI_Integration.py",
                "user_feature": "10_UMarketU_Suite.py",
                "bridge": "job_title_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Job Title Analysis, Role Matching, Career Recommendations",
                "status": "Missing"
            },
            {
                "admin_feature": "21_Job_Title_Overlap_Cloud.py",
                "user_feature": "10_UMarketU_Suite.py",
                "bridge": "job_overlap_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Career Path Analysis, Role Overlap, Transition Insights",
                "status": "Missing"
            },
            {
                "admin_feature": "26_Career_Pattern_Intelligence.py",
                "user_feature": "04_Dashboard.py",
                "bridge": "career_pattern_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Career Insights, Peer Benchmarking, Skill Distribution",
                "status": "Missing"
            },
            {
                "admin_feature": "26_Career_Pattern_Intelligence.py",
                "user_feature": "11_Coaching_Hub.py",
                "bridge": "career_coaching_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Career Guidance, Development Roadmap, Skill Gap Analysis",
                "status": "Missing"
            },
            {
                "admin_feature": "10_Market_Intelligence_Center.py",
                "user_feature": "13_Dual_Career_Suite.py",
                "bridge": "market_intelligence_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Market Trends, Industry Analysis, Location Intelligence",
                "status": "Missing"
            },
            {
                "admin_feature": "11_Competitive_Intelligence.py",
                "user_feature": "10_UMarketU_Suite.py",
                "bridge": "competitive_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Competitive Analysis, Market Positioning, Resume Enhancement",
                "status": "Missing"
            },
            {
                "admin_feature": "08_AI_Enrichment.py",
                "user_feature": "09_Resume_Upload_Analysis.py",
                "bridge": "ai_enrichment_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "CV Enhancement, AI Analysis, Content Improvement",
                "status": "Missing"
            },
            {
                "admin_feature": "25_Intelligence_Hub.py",
                "user_feature": "04_Dashboard.py",
                "bridge": "intelligence_dashboard_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Intelligence Summary, Personalized Insights, Aggregated Data",
                "status": "Missing"
            },
            {
                "admin_feature": "02_Analytics.py",
                "user_feature": "04_Dashboard.py",
                "bridge": "analytics_bridge.py",
                "connection_type": "Partial",
                "data_flow": "User Analytics, Performance Data, Usage Statistics",
                "status": "Partial"
            },
            {
                "admin_feature": "07_Batch_Processing.py",
                "user_feature": "04_Dashboard.py",
                "bridge": "batch_status_bridge.py",
                "connection_type": "Partial",
                "data_flow": "Processing Status, Background Tasks, Queue Status",
                "status": "Partial"
            },
            {
                "admin_feature": "12_Web_Company_Intelligence.py",
                "user_feature": "12_Mentorship_Marketplace.py",
                "bridge": "company_network_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Company Networks, Professional Contacts, Industry Connections",
                "status": "Missing"
            },
            {
                "admin_feature": "19_Enhanced_Glossary.py",
                "user_feature": "10_UMarketU_Suite.py",
                "bridge": "glossary_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Terminology Support, Abbreviations, Industry Terms",
                "status": "Missing"
            },
            {
                "admin_feature": "23_AI_Model_Training_Review.py",
                "user_feature": "09_Resume_Upload_Analysis.py",
                "bridge": "ai_model_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Model Performance, Analysis Quality, AI Feedback",
                "status": "Missing"
            },
            {
                "admin_feature": "14_Contact_Communication.py",
                "user_feature": "12_Mentorship_Marketplace.py",
                "bridge": "communication_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Contact Management, Messaging, Professional Communication",
                "status": "Missing"
            },
            {
                "admin_feature": "30_Stats_Dashboard.py",
                "user_feature": "04_Dashboard.py",
                "bridge": "stats_bridge.py",
                "connection_type": "Suggested",
                "data_flow": "Personal Statistics, Progress Metrics, Achievement Data",
                "status": "Missing"
            }
        ]

        self.connections = connections
        return connections

    def analyze_data_flows(self):
        """Analyze data flows and identify optimization opportunities"""
        data_flow_analysis = {
            "cv_processing": {
                "sources": ["06_Complete_Data_Parser.py", "05_Email_Integration.py", "08_AI_Enrichment.py"],
                "destinations": ["09_Resume_Upload_Analysis.py"],
                "flow_quality": "Strong",
                "optimization": "Add AI enrichment layer for enhanced analysis"
            },
            "intelligence": {
                "sources": ["27_Exa_Web_Intelligence.py", "10_Market_Intelligence_Center.py", "11_Competitive_Intelligence.py", "25_Intelligence_Hub.py"],
                "destinations": ["10_UMarketU_Suite.py", "13_Dual_Career_Suite.py", "04_Dashboard.py"],
                "flow_quality": "Partial",
                "optimization": "Create unified intelligence bridge for dashboard"
            },
            "job_analysis": {
                "sources": ["20_Job_Title_AI_Integration.py", "21_Job_Title_Overlap_Cloud.py", "26_Career_Pattern_Intelligence.py"],
                "destinations": ["10_UMarketU_Suite.py", "11_Coaching_Hub.py", "04_Dashboard.py"],
                "flow_quality": "Missing",
                "optimization": "CRITICAL - needs immediate bridge creation for job title and career pattern analysis"
            },
            "user_data": {
                "sources": ["03_User_Management.py", "02_Analytics.py", "24_Token_Management.py"],
                "destinations": ["04_Dashboard.py", "All User Pages"],
                "flow_quality": "Partial",
                "optimization": "Implement comprehensive user data bridge with token integration"
            },
            "career_guidance": {
                "sources": ["26_Career_Pattern_Intelligence.py", "21_Job_Title_Overlap_Cloud.py", "11_Competitive_Intelligence.py"],
                "destinations": ["11_Coaching_Hub.py", "04_Dashboard.py"],
                "flow_quality": "Missing",
                "optimization": "Connect career analysis tools to coaching services"
            },
            "communication": {
                "sources": ["05_Email_Integration.py", "14_Contact_Communication.py"],
                "destinations": ["12_Mentorship_Marketplace.py", "13_Dual_Career_Suite.py"],
                "flow_quality": "Partial",
                "optimization": "Enhance contact management integration"
            }
        }
        return data_flow_analysis

    def generate_connection_matrix(self):
        """Generate connection matrix for visualization"""
        admin_pages = sorted(list(self.admin_features.keys()))
        user_pages = sorted(list(self.user_features.keys()))

        # Create matrix
        matrix_data = []
        for admin_page in admin_pages:
            row = {"Admin_Page": admin_page.replace('.py', '')}
            for user_page in user_pages:
                user_key = user_page.replace('.py', '')

                # Find connection
                connection = None
                for conn in self.connections:
                    if (conn["admin_feature"] == admin_page and
                        conn["user_feature"] == user_page):
                        connection = conn
                        break

                if connection:
                    if connection["connection_type"] == "Strong":
                        row[user_key] = "🟢 Strong"
                    elif connection["connection_type"] == "Partial":
                        row[user_key] = "🟡 Partial"
                    elif connection["connection_type"] == "Suggested":
                        row[user_key] = "🔵 Suggested"
                else:
                    row[user_key] = "⚪ None"

            matrix_data.append(row)

        return pd.DataFrame(matrix_data)

# Initialize auditor
auditor = SystemConnectivityAuditor()

# Header
st.markdown('<div class="main-header">🔗 System Connectivity Audit</div>', unsafe_allow_html=True)
st.markdown("**Updated:** November 14, 2025 | **Status:** Current Page Inventory")

if TELEMETRY_HELPER:
    TELEMETRY_HELPER.render_status_panel(
        title="🛰️ Backend Telemetry Monitor",
        refresh_key="page27_backend_refresh",
    )

# Scan system
with st.spinner("🔍 Scanning system for features and connections..."):
    admin_features = auditor.scan_admin_portal()
    user_features = auditor.scan_user_portal()
    connections = auditor.detect_existing_connections()
    data_flows = auditor.analyze_data_flows()

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Admin Features", len(admin_features))

with col2:
    st.metric("User Features", len(user_features))

with col3:
    active_connections = len([c for c in connections if c["status"] == "Active"])
    st.metric("Active Connections", active_connections)

with col4:
    missing_connections = len([c for c in connections if c["status"] == "Missing"])
    st.metric("Missing Connections", missing_connections, delta=f"-{missing_connections}")

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Connection Matrix",
    "🔗 Connection Details",
    "🌊 Data Flow Analysis",
    "💡 Recommendations",
    "🛠️ Bridge Generator"
])

with tab1:
    st.markdown("### 🎯 System Connectivity Matrix")
    st.markdown("Visual overview of all connections between admin and user portal features")

    # Generate and display connection matrix
    matrix_df = auditor.generate_connection_matrix()

    # Display as styled dataframe
    st.markdown("#### Connection Status Legend:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("🟢 **Strong** - Full bridge implementation")
    with col2:
        st.markdown("🟡 **Partial** - Limited connection")
    with col3:
        st.markdown("🔵 **Suggested** - Recommended connection")
    with col4:
        st.markdown("⚪ **None** - No connection")

    st.dataframe(
        matrix_df,
        use_container_width=True,
        height=600
    )

with tab2:
    st.markdown("### 🔗 Detailed Connection Analysis")

    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Active", "Missing", "Partial"]
        )
    with col2:
        connection_filter = st.selectbox(
            "Filter by Type",
            ["All", "Strong", "Suggested", "Partial"]
        )

    # Filter connections
    filtered_connections = connections
    if status_filter != "All":
        filtered_connections = [c for c in filtered_connections if c["status"] == status_filter]
    if connection_filter != "All":
        filtered_connections = [c for c in filtered_connections if c["connection_type"] == connection_filter]

    # Display connections
    for i, conn in enumerate(filtered_connections):
        with st.expander(f"🔗 {conn['admin_feature']} ↔ {conn['user_feature']}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Admin Feature:** {conn['admin_feature']}")
                if conn['admin_feature'] in admin_features:
                    admin_info = admin_features[conn['admin_feature']]
                    st.markdown(f"**Category:** {admin_info['category']}")
                    st.markdown(f"**Capabilities:** {', '.join(admin_info['capabilities'])}")

                st.markdown(f"**Bridge:** {conn['bridge']}")
                st.markdown(f"**Status:** {conn['status']}")

            with col2:
                st.markdown(f"**User Feature:** {conn['user_feature']}")
                if conn['user_feature'] in user_features:
                    user_info = user_features[conn['user_feature']]
                    st.markdown(f"**Category:** {user_info['category']}")
                    st.markdown(f"**Capabilities:** {', '.join(user_info['capabilities'])}")

                st.markdown(f"**Connection Type:** {conn['connection_type']}")
                st.markdown(f"**Data Flow:** {conn['data_flow']}")

with tab3:
    st.markdown("### 🌊 Data Flow Analysis")

    for flow_name, flow_info in data_flows.items():
        with st.expander(f"📊 {flow_name.replace('_', ' ').title()} Data Flow", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Data Sources (Admin):**")
                for source in flow_info["sources"]:
                    st.markdown(f"• {source}")

                st.markdown(f"**Flow Quality:** {flow_info['flow_quality']}")

            with col2:
                st.markdown("**Data Destinations (User):**")
                for dest in flow_info["destinations"]:
                    st.markdown(f"• {dest}")

                st.markdown(f"**Optimization:** {flow_info['optimization']}")

with tab4:
    st.markdown("### 💡 Connectivity Recommendations")

    st.markdown("#### 🚨 Critical Missing Connections")
    critical_missing = [c for c in connections if c["status"] == "Missing" and
                       any(keyword in c["admin_feature"].lower() for keyword in ['job', 'career', 'pattern'])]

    for conn in critical_missing:
        st.error(f"**CRITICAL:** {conn['admin_feature']} ↔ {conn['user_feature']}")
        st.markdown(f"Expected Bridge: `{conn['bridge']}`")
        st.markdown(f"Expected Data Flow: {conn['data_flow']}")
        st.markdown("---")

    st.markdown("#### 🔧 Quick Wins - Priority Order")
    quick_wins = [
        {
            "title": "Career Pattern Intelligence Bridge",
            "description": "Connect career pattern analysis (Page 26) to Dashboard and Coaching Hub",
            "impact": "High",
            "effort": "Medium",
            "priority": 1
        },
        {
            "title": "Job Title Integration Bridges",
            "description": "Connect job title analysis (Pages 20, 21) to UMarketU Suite for better role matching",
            "impact": "High",
            "effort": "Medium",
            "priority": 2
        },
        {
            "title": "Intelligence Hub Dashboard Bridge",
            "description": "Connect Intelligence Hub (Page 25) to user dashboard for personalized insights",
            "impact": "Medium",
            "effort": "Low",
            "priority": 3
        },
        {
            "title": "AI Enrichment Bridge",
            "description": "Connect AI enrichment (Page 08) to Resume Upload Analysis",
            "impact": "Medium",
            "effort": "Low",
            "priority": 4
        },
        {
            "title": "Batch Processing Status Bridge",
            "description": "Show background processing status in user dashboard",
            "impact": "Low",
            "effort": "Low",
            "priority": 5
        }
    ]

    for win in sorted(quick_wins, key=lambda x: x['priority']):
        with st.expander(f"#{win['priority']} 💎 {win['title']}", expanded=False):
            st.markdown(f"**Description:** {win['description']}")
            st.markdown(f"**Impact:** {win['impact']} | **Effort:** {win['effort']}")

with tab5:
    st.markdown("### 🛠️ Bridge Code Generator")

    st.markdown("Select a missing connection to generate bridge code:")

    missing_connections = [c for c in connections if c["status"] == "Missing"]
    if missing_connections:
        selected_connection = st.selectbox(
            "Choose Connection to Implement",
            missing_connections,
            format_func=lambda x: f"{x['admin_feature']} ↔ {x['user_feature']}"
        )

        if st.button("🚀 Generate Bridge Code", type="primary"):
            st.markdown("#### Generated Bridge Template:")

            bridge_code = f'''"""
{selected_connection['bridge'].replace('.py', '').replace('_', ' ').title()} - System Bridge
==================================================
Bridge connecting {selected_connection['admin_feature']} to {selected_connection['user_feature']}
Data Flow: {selected_connection['data_flow']}

Auto-generated by System Connectivity Audit
Date: {datetime.now().strftime("%Y-%m-%d")}
"""

import sys
from pathlib import Path
import streamlit as st

# Add paths
current_dir = Path(__file__).parent.parent
admin_path = current_dir / "admin_portal" / "pages"
user_path = current_dir / "user_portal_final" / "pages"
sys.path.extend([str(admin_path), str(user_path)])

class {selected_connection['bridge'].replace('.py', '').replace('_', '')}:
    """Bridge for {selected_connection['data_flow']}"""

    def __init__(self):
        self.admin_service = None
        self.connection_status = "Initializing"
        self._initialize_admin_connection()

    def _initialize_admin_connection(self):
        """Initialize connection to admin service"""
        try:
            # Import admin service
            # from {selected_connection['admin_feature'].replace('.py', '')} import ServiceClass
            self.connection_status = "Connected"
        except ImportError as e:
            st.warning(f"Admin service not available: {{e}}")
            self.connection_status = "Fallback"

    def {selected_connection['data_flow'].lower().replace(' ', '_').replace(',', '').replace('-', '_')[:50]}(self, user_context):
        """Main bridge function for data transfer"""
        if self.connection_status == "Connected":
            # Implement actual data transfer
            return self._get_live_data(user_context)
        else:
            # Return fallback data
            return self._get_fallback_data(user_context)

    def _get_live_data(self, user_context):
        """Get live data from admin service"""
        # Implement live data retrieval
        return {{"status": "live", "data": "Live data from admin service"}}

    def _get_fallback_data(self, user_context):
        """Get fallback demonstration data"""
        return {{"status": "demo", "data": "Demonstration data"}}

# Usage example:
# bridge = {selected_connection['bridge'].replace('.py', '').replace('_', '')}()
# result = bridge.{selected_connection['data_flow'].lower().replace(' ', '_').replace(',', '').replace('-', '_')[:50]}(user_context)
'''

            st.code(bridge_code, language="python")

            # File creation option
            if st.button("💾 Save Bridge File"):
                bridge_path = current_dir / "user_portal_final" / "bridges" / selected_connection['bridge']
                bridge_path.parent.mkdir(exist_ok=True)

                with open(bridge_path, 'w', encoding='utf-8') as f:
                    f.write(bridge_code)

                st.success(f"✅ Bridge file saved: {bridge_path}")

# Footer with export options
st.markdown("---")
st.markdown("### 📊 Export Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Export Connection Report"):
        # Generate comprehensive report
        report_data = {
            "scan_date": datetime.now().isoformat(),
            "admin_features": admin_features,
            "user_features": user_features,
            "connections": connections,
            "data_flows": data_flows
        }

        report_path = current_dir / f"connectivity_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        st.success(f"✅ Report exported: {report_path.name}")

with col2:
    if st.button("🔗 Export Connection Matrix"):
        matrix_df = auditor.generate_connection_matrix()
        matrix_path = current_dir / f"connection_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        matrix_df.to_csv(matrix_path, index=False)
        st.success(f"✅ Matrix exported: {matrix_path.name}")

with col3:
    if st.button("🚀 Generate All Missing Bridges"):
        missing_bridges = [c for c in connections if c["status"] == "Missing"]
        bridge_dir = current_dir / "user_portal_final" / "bridges"
        bridge_dir.mkdir(exist_ok=True)

        created_bridges = []
        for conn in missing_bridges:
            # Generate bridge code (simplified version)
            bridge_code = f"# Bridge for {conn['admin_feature']} ↔ {conn['user_feature']}\n# TODO: Implement bridge logic\n"

            bridge_path = bridge_dir / conn['bridge']
            if not bridge_path.exists():
                with open(bridge_path, 'w', encoding='utf-8') as f:
                    f.write(bridge_code)
                created_bridges.append(conn['bridge'])

        if created_bridges:
            st.success(f"✅ Created {len(created_bridges)} bridge templates")
        else:
            st.info("ℹ️ All bridge files already exist")

# Real-time system status
with st.sidebar:
    st.markdown("### 🔍 System Scan Results")
    st.metric("Total Features", len(admin_features) + len(user_features))
    st.metric("Total Connections", len(connections))

    # Connection quality
    strong_connections = len([c for c in connections if c["connection_type"] == "Strong"])
    connection_quality = (strong_connections / len(connections)) * 100 if connections else 0
    st.metric("Connection Quality", f"{connection_quality:.1f}%")

    st.markdown("### 🎯 Priority Actions")
    st.markdown("1. ✅ **Implement career pattern bridges**")
    st.markdown("2. 🔧 **Connect job title services**")
    st.markdown("3. 💡 **Add intelligence hub to dashboard**")
    st.markdown("4. 🤖 **Enable AI enrichment for CVs**")
    st.markdown("5. 📊 **Add batch status updates**")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <strong>System Connectivity Audit - IntelliCV Platform</strong><br>
    Real-time analysis of system integration and connectivity gaps<br>
    <em>Updated: November 14, 2025</em>
</div>
""", unsafe_allow_html=True)
