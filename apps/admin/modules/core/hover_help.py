"""
Hover Help System for IntelliCV Admin Portal
==========================================

This module provides comprehensive hover help tooltips and documentation
for all UI elements throughout the admin portal.
"""

class HoverHelp:
    """Centralized hover help and tooltip system"""
    
    # Navigation Help
    NAVIGATION_HELP = {
        "dashboard": "🏠 Main dashboard with system overview, metrics, and quick access to all major functions",
        "users": "👥 Manage user accounts, permissions, access controls, and user activity monitoring",
        "parsers": "📊 CV/Resume parsing engines, document processing, and batch operations",
        "monitor": "📈 Real-time system health monitoring, performance metrics, and resource utilization",
        "ai": "🤖 AI-powered data enrichment, enhanced analysis, and automated insights generation",
        "analytics": "📊 Advanced data analytics, trend analysis, custom reporting, and visualizations",
        "market": "🔍 Market intelligence, job trends, salary benchmarking, and competitive analysis",
        "compliance": "⚖️ Data privacy controls, GDPR compliance, audit trails, and regulatory management",
        "api": "🔧 External system integrations, API management, and third-party connections",
        "errors": "🐞 System error tracking, debugging tools, and issue resolution monitoring",
        "email_integration": "📧 Email account integration, document extraction, and contact management",
        "settings": "⚙️ System configuration, preferences, environment settings, and customization",
        "login": "🔒 Administrative authentication, security controls, and session management"
    }
    
    # Dashboard Help
    DASHBOARD_HELP = {
        "system_metrics": "Real-time system performance indicators including CPU, memory, and database status",
        "user_metrics": "Current user statistics: total users, active sessions, and recent registrations",
        "cv_metrics": "CV processing statistics: total processed, success rate, and processing queue status",
        "error_metrics": "System error tracking: recent errors, error rate trends, and critical issues",
        "data_generator": "Controls for the data generation system - creates sample data for testing and development",
        "quick_actions": "Fast access buttons to the most commonly used admin functions",
        "system_health": "Overall system health indicator with detailed status information",
        "recent_activity": "Latest system activities, user actions, and processing events"
    }
    
    # User Management Help
    USER_MANAGEMENT_HELP = {
        "add_user": "Create new user account with email, permissions, and access level settings",
        "user_list": "Complete list of all users with status, last login, and account details",
        "permissions": "Configure user access levels: admin, standard user, or view-only permissions",
        "bulk_actions": "Perform actions on multiple users: bulk email, permission changes, or account status updates",
        "user_activity": "Monitor user login history, session duration, and system usage patterns",
        "export_users": "Export user data to CSV or Excel format for external analysis or backup",
        "user_search": "Search and filter users by name, email, registration date, or activity status",
        "account_status": "Manage user account status: active, suspended, pending approval, or disabled"
    }
    
    # Data Parsers Help
    DATA_PARSERS_HELP = {
        "upload_cv": "Upload individual CV/resume files (PDF, DOCX, TXT) for parsing and analysis",
        "batch_upload": "Upload multiple CV files at once for bulk processing - supports ZIP archives",
        "parsing_status": "Monitor the status of CV parsing operations: queued, processing, completed, or failed",
        "parsing_results": "View detailed parsing results including extracted text, structured data, and confidence scores",
        "parser_settings": "Configure parsing engine settings: language detection, field extraction, and accuracy thresholds",
        "export_data": "Export parsed CV data in various formats: JSON, CSV, XML, or custom templates",
        "parsing_history": "Complete history of all parsing operations with timestamps and user information",
        "error_analysis": "Analyze parsing errors and failures to improve system accuracy and reliability"
    }
    
    # System Monitor Help
    SYSTEM_MONITOR_HELP = {
        "cpu_usage": "Real-time CPU utilization showing current load and historical trends",
        "memory_usage": "System memory consumption including RAM usage and available free memory",
        "disk_space": "Storage utilization across all system drives with capacity warnings",
        "database_status": "Database connection health, query performance, and transaction statistics",
        "network_traffic": "Inbound and outbound network activity with bandwidth utilization",
        "process_list": "Active system processes with resource consumption and status information",
        "log_viewer": "Real-time system logs with filtering, search, and export capabilities",
        "alerts_config": "Configure system monitoring alerts and notification thresholds"
    }
    
    # AI Enrichment Help
    AI_ENRICHMENT_HELP = {
        "enrichment_pipeline": "Automated data enhancement using AI models for improved accuracy and insights",
        "model_management": "Manage AI models: training, updates, performance monitoring, and version control",
        "enhancement_results": "View AI-enhanced data with confidence scores and improvement metrics",
        "training_data": "Manage training datasets for AI model improvement and customization",
        "ai_insights": "AI-generated insights and recommendations based on processed data patterns",
        "performance_metrics": "AI model performance statistics: accuracy, processing speed, and reliability",
        "custom_models": "Upload and deploy custom AI models for specialized data processing requirements",
        "api_connections": "Integrate with external AI services and APIs for enhanced processing capabilities"
    }
    
    # Email Integration Help
    EMAIL_INTEGRATION_HELP = {
        "add_email_account": "Connect email accounts (Gmail, Outlook, Yahoo) using secure app passwords",
        "email_scanning": "Scan email archives to extract documents, resumes, and attachments automatically",
        "document_extraction": "Extract and classify documents from email attachments with AI-powered analysis",
        "contact_harvesting": "Build contact databases by extracting email addresses from documents and communications",
        "historical_scan": "Scan email archives dating back to 2011 for comprehensive document discovery",
        "ai_export": "Export extracted data directly to the AI enrichment pipeline for further processing",
        "scan_progress": "Monitor email scanning progress with real-time status updates and statistics",
        "email_security": "Secure email integration using OAuth2 and app passwords - never stores main passwords"
    }
    
    # Settings Help
    SETTINGS_HELP = {
        "system_config": "Core system configuration including database, security, and performance settings",
        "user_preferences": "Default user interface preferences and behavior settings",
        "notification_settings": "Configure email notifications, alerts, and system messages",
        "security_settings": "Authentication requirements, password policies, and access controls",
        "backup_config": "Automated backup settings including frequency, retention, and storage location",
        "integration_settings": "Third-party service configurations and API connection settings",
        "performance_tuning": "System performance optimization settings and resource allocation",
        "maintenance_mode": "Enable maintenance mode for system updates and scheduled downtime"
    }
    
    # Analytics Help
    ANALYTICS_HELP = {
        "dashboard_analytics": "Comprehensive analytics dashboard with key performance indicators and trends",
        "user_analytics": "User behavior analysis including usage patterns, feature adoption, and engagement metrics",
        "cv_analytics": "CV processing analytics: success rates, common errors, and processing time trends",
        "custom_reports": "Create custom reports with flexible filtering, grouping, and visualization options",
        "export_analytics": "Export analytics data in various formats for external analysis and reporting",
        "trend_analysis": "Historical trend analysis with predictive insights and forecasting capabilities",
        "comparative_analysis": "Compare performance across different time periods, user groups, or system components",
        "real_time_metrics": "Live analytics with real-time updates and streaming data visualization"
    }
    
    # Market Intelligence Help
    MARKET_INTELLIGENCE_HELP = {
        "job_market_trends": "Current job market analysis including in-demand skills and salary trends",
        "industry_analysis": "Comprehensive industry reports with growth projections and market dynamics",
        "competitor_analysis": "Competitive intelligence including competitor profiles and market positioning",
        "salary_benchmarking": "Salary comparison tools with location-based adjustments and role-specific data",
        "skills_demand": "Analysis of skill demand trends and emerging technology requirements",
        "market_research": "Custom market research tools for specific industries or job categories",
        "economic_indicators": "Economic indicators affecting the job market including unemployment rates and GDP",
        "forecast_models": "Predictive models for job market trends and industry growth projections"
    }
    
    # Compliance Help
    COMPLIANCE_HELP = {
        "gdpr_compliance": "GDPR compliance tools including data mapping, consent management, and audit trails",
        "data_retention": "Configure data retention policies with automatic deletion and archival processes",
        "privacy_controls": "User privacy controls including data access, modification, and deletion rights",
        "audit_trails": "Comprehensive audit logging for all system activities and data access events",
        "consent_management": "Manage user consent for data processing with granular permission controls",
        "data_export": "Provide users with complete data exports in machine-readable formats",
        "breach_notification": "Automated breach notification system with regulatory reporting capabilities",
        "compliance_reports": "Generate compliance reports for regulatory submissions and internal audits"
    }
    
    # Error Tracking Help
    ERROR_TRACKING_HELP = {
        "error_dashboard": "Comprehensive error tracking dashboard with severity levels and trend analysis",
        "error_details": "Detailed error information including stack traces, user context, and reproduction steps",
        "error_resolution": "Track error resolution progress with assignment, status updates, and resolution notes",
        "error_patterns": "Identify recurring error patterns and common failure points for system improvement",
        "notification_config": "Configure error notifications with severity-based routing and escalation rules",
        "error_reporting": "Generate error reports for system reliability analysis and improvement planning",
        "performance_impact": "Analyze the performance impact of errors on system reliability and user experience",
        "automated_resolution": "Set up automated error resolution for common issues and system recovery"
    }
    
    # Form Field Help
    FORM_HELP = {
        "email_address": "Enter a valid email address - this will be used for account notifications and login",
        "password": "Password must be at least 8 characters with uppercase, lowercase, and special characters",
        "confirm_password": "Re-enter your password to confirm it matches the original password",
        "first_name": "Enter your first name as it should appear in the system",
        "last_name": "Enter your last name as it should appear in the system",
        "phone_number": "Enter phone number with country code (e.g., +1-555-123-4567)",
        "date_range": "Select start and end dates for the analysis period",
        "file_upload": "Select files to upload - supported formats: PDF, DOCX, TXT, ZIP",
        "search_query": "Enter search terms - supports partial matches and wildcard characters (*)",
        "batch_size": "Number of items to process at once - larger batches are faster but use more memory"
    }
    
    # Button Help
    BUTTON_HELP = {
        "save": "Save current changes to the database - changes are not permanent until saved",
        "cancel": "Cancel current operation and return to previous screen without saving changes",
        "delete": "Permanently delete selected item(s) - this action cannot be undone",
        "export": "Export current data to file - choose from CSV, Excel, JSON, or PDF formats",
        "refresh": "Reload current data from the database to show latest changes",
        "test_connection": "Test connection to external service - verifies credentials and connectivity",
        "run_analysis": "Start analysis process - this may take several minutes for large datasets",
        "download": "Download file to your computer - file will be saved to your default download folder"
    }
    
    # Status Indicators Help
    STATUS_HELP = {
        "online": "🟢 System is online and functioning normally",
        "offline": "🔴 System is offline or experiencing connectivity issues",
        "warning": "🟡 System is online but experiencing performance issues or warnings",
        "maintenance": "🔵 System is in maintenance mode - limited functionality available",
        "processing": "🟠 Operation in progress - please wait for completion",
        "completed": "✅ Operation completed successfully",
        "failed": "❌ Operation failed - check error details for more information",
        "pending": "⏳ Operation is queued and waiting to be processed"
    }

    @staticmethod
    def get_help_text(category: str, key: str) -> str:
        """Get help text for a specific UI element"""
        help_dict = getattr(HoverHelp, f"{category.upper()}_HELP", {})
        return help_dict.get(key, "No help available for this item")
    
    @staticmethod
    def get_navigation_help(section: str) -> str:
        """Get help text for navigation sections"""
        return HoverHelp.NAVIGATION_HELP.get(section, "Navigation help not available")
    
    @staticmethod
    def format_help_tooltip(text: str) -> str:
        """Format help text for display in tooltips"""
        return f"ℹ️ {text}"

# Quick access functions for common help patterns
def nav_help(section: str) -> str:
    """Get navigation help with tooltip formatting"""
    return HoverHelp.format_help_tooltip(HoverHelp.get_navigation_help(section))

def form_help(field: str) -> str:
    """Get form field help with tooltip formatting"""
    return HoverHelp.format_help_tooltip(HoverHelp.get_help_text("form", field))

def button_help(action: str) -> str:
    """Get button help with tooltip formatting"""
    return HoverHelp.format_help_tooltip(HoverHelp.get_help_text("button", action))

def status_help(status: str) -> str:
    """Get status indicator help with tooltip formatting"""
    return HoverHelp.format_help_tooltip(HoverHelp.get_help_text("status", status))