"""
=============================================================================
IntelliCV Admin Portal - Compliance Audit Module
=============================================================================

Comprehensive compliance and audit suite with enterprise-grade security,
data governance, and regulatory compliance monitoring.

Features:
- Dataset integrity auditing
- Admin activity monitoring
- Enterprise compliance tracking
- Regulatory compliance reporting
- Integration hooks for audit trails
"""

import streamlit as st

# =============================================================================
# BACKEND-FIRST SWITCH (lockstep) — falls back to local execution when backend is unavailable
# =============================================================================
try:
    from portal_bridge.python.intellicv_api_client import IntelliCVApiClient  # preferred
except Exception:  # pragma: no cover
    IntelliCVApiClient = None  # type: ignore

def _get_api_client():
    return IntelliCVApiClient() if IntelliCVApiClient else None

def _backend_try_get(path: str, params: dict | None = None):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.get(path, params=params), None
    except Exception as e:
        return None, str(e)

def _backend_try_post(path: str, payload: dict):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.post(path, payload), None
    except Exception as e:
        return None, str(e)


import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SERVICES_PATH = ROOT_DIR / "services"
if str(SERVICES_PATH) not in sys.path:
    sys.path.insert(0, str(SERVICES_PATH))

# =============================================================================
# MANDATORY AUTHENTICATION CHECK
# =============================================================================

def check_authentication():
    """Check if admin is authenticated"""
    if not st.session_state.get('admin_authenticated', False):
        st.error("🔒 **ADMIN AUTHENTICATION REQUIRED**")
        st.warning("You must login through the main admin portal to access this module.")

        if st.button("🏠 Return to Main Portal", type="primary"):
            st.switch_page("main.py")
        st.stop()
    return True


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

USER_METRICS_CACHE_KEY = "_compliance_user_metrics_snapshot"
USER_METRICS_TS_KEY = "_compliance_user_metrics_ts"
USER_SECURITY_CACHE_KEY = "_compliance_user_security_snapshot"
USER_SECURITY_TS_KEY = "_compliance_user_security_ts"
DASHBOARD_CACHE_KEY = "_compliance_dashboard_snapshot"
DASHBOARD_TS_KEY = "_compliance_dashboard_ts"
SYSTEM_HEALTH_CACHE_KEY = "_compliance_system_health_snapshot"
SYSTEM_HEALTH_TS_KEY = "_compliance_system_health_ts"
SYSTEM_ACTIVITY_CACHE_KEY = "_compliance_system_activity_snapshot"
SYSTEM_ACTIVITY_TS_KEY = "_compliance_system_activity_ts"
API_CACHE_TTL = 90

def render_section_header(title, icon="", show_line=True):
    """Render section header"""
    st.markdown(f"## {icon} {title}")
    if show_line:
        st.markdown("---")


    """Ensure user is authenticated before accessing this page"""
    if not st.session_state.get('admin_authenticated', False):
        st.error("🚫 **AUTHENTICATION REQUIRED**")
        st.info("Please return to the main page and login to access this module.")
        st.markdown("---")
        st.markdown("### 🔐 Access Denied")
        st.markdown("This page is only accessible to authenticated admin users.")
        if st.button("🔙 Return to Main Page"):
            st.switch_page("main.py")
        st.stop()

# Check authentication immediately
check_authentication()

# Hide sidebar navigation for unauthorized access
if not st.session_state.get('admin_authenticated', False):
    st.markdown("""
    <style>
        .css-1d391kg {display: none;}
        [data-testid="stSidebar"] {display: none;}
        .css-1rs6os {display: none;}
        .css-17ziqus {display: none;}
    </style>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Admin API helpers
# -----------------------------------------------------------------------------

def get_admin_api_client():
    if AdminFastAPIClient is None:
        return None
    client = st.session_state.get("_admin_api_client")
    if client is None:
        st.session_state["_admin_api_client"] = AdminFastAPIClient()
        client = st.session_state["_admin_api_client"]
    return client


def _get_cached_admin_payload(
    cache_key: str,
    ts_key: str,
    fetcher,
    force_refresh: bool = False,
    ttl_seconds: int = API_CACHE_TTL,
):
    if force_refresh:
        st.session_state.pop(cache_key, None)
        st.session_state.pop(ts_key, None)

    payload = st.session_state.get(cache_key)
    timestamp = st.session_state.get(ts_key)
    if payload and timestamp:
        if (datetime.now() - timestamp).total_seconds() < ttl_seconds:
            return payload

    client = get_admin_api_client()
    if not client:
        return payload or {}

    data = fetcher(client) or {}
    st.session_state[cache_key] = data
    st.session_state[ts_key] = datetime.now()
    return data


def get_user_metrics_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        USER_METRICS_CACHE_KEY,
        USER_METRICS_TS_KEY,
        lambda client: client.get_user_metrics(),
        force_refresh,
    )


def get_user_security_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        USER_SECURITY_CACHE_KEY,
        USER_SECURITY_TS_KEY,
        lambda client: client.get_user_security(),
        force_refresh,
    )


def get_dashboard_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        DASHBOARD_CACHE_KEY,
        DASHBOARD_TS_KEY,
        lambda client: client.get_dashboard_snapshot(),
        force_refresh,
        ttl_seconds=60,
    )


def get_system_health_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        SYSTEM_HEALTH_CACHE_KEY,
        SYSTEM_HEALTH_TS_KEY,
        lambda client: client.get_system_health(),
        force_refresh,
        ttl_seconds=45,
    )


def get_system_activity_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    return _get_cached_admin_payload(
        SYSTEM_ACTIVITY_CACHE_KEY,
        SYSTEM_ACTIVITY_TS_KEY,
        lambda client: client.get_system_activity(),
        force_refresh,
        ttl_seconds=45,
    )


def format_relative_time(timestamp: Optional[str]) -> str:
    if not timestamp:
        return "N/A"
    try:
        reference = datetime.now()
        parsed = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
        delta = reference - parsed
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except Exception:
        return str(timestamp)


def show_backend_api_status():
    """Link compliance module to FastAPI telemetry."""
    st.subheader("🛰️ Backend & FastAPI Health")

    refresh_col, meta_col = st.columns([1, 3])
    with refresh_col:
        if st.button("🔄 Refresh Backend Data", key="refresh_backend_for_compliance"):
            get_dashboard_snapshot(force_refresh=True)
            get_system_health_snapshot(force_refresh=True)
            get_system_activity_snapshot(force_refresh=True)
            get_user_metrics_snapshot(force_refresh=True)
            get_user_security_snapshot(force_refresh=True)
            st.rerun()

    dashboard = get_dashboard_snapshot() or {}
    system_health = get_system_health_snapshot() or {}
    system_activity = get_system_activity_snapshot() or {}

    with meta_col:
        updated_at = system_health.get('updated_at') or (dashboard.get('system') or {}).get('updated_at')
        st.caption(f"System telemetry updated {format_relative_time(updated_at)}")

    system_block = dashboard.get('system', {})
    tokens_block = dashboard.get('tokens', {})
    services = system_block.get('services') or system_health.get('services') or {}

    cpu_pct = system_health.get('cpu_pct', system_block.get('cpu_percent', 0.0)) or 0.0
    mem_pct = system_health.get('memory_pct', system_block.get('memory_percent', 0.0)) or 0.0
    jobs_in_queue = system_block.get('jobs_in_queue', 0)
    parsers_online = system_block.get('parsers_online', 0)
    token_30d = tokens_block.get('total_used_30d', 0)
    token_24h = tokens_block.get('total_used_24h', 0)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("CPU Load", f"{cpu_pct:.1f}%", f"{system_health.get('cpu_count', 0)} cores")
    with metric_cols[1]:
        st.metric("Memory Usage", f"{mem_pct:.1f}%", f"{system_health.get('memory_available_gb', 0):.1f} GB free")
    with metric_cols[2]:
        st.metric("Jobs in Queue", f"{jobs_in_queue:,}", f"{parsers_online} parsers")
    with metric_cols[3]:
        st.metric("Tokens (30d)", f"{token_30d:,}", f"{token_24h:,} / 24h")

    if services:
        running = sum(1 for status in services.values() if status == 'running')
        st.caption(f"Services online: {running}/{len(services)}")

    budget_alerts = tokens_block.get('budget_alerts') or []
    for alert in budget_alerts[:3]:
        st.warning(
            f"⚠️ {alert.get('org', 'Org')} ({alert.get('plan', 'plan')}) at {alert.get('usage_pct', 0):.1f}% token usage"
        )

    data_overview = dashboard.get('data_overview') or {}
    if data_overview:
        with st.expander("🔎 Data Overview", expanded=False):
            overview_df = pd.DataFrame(
                [{"Type": key.upper(), "Count": value} for key, value in data_overview.items()]
            )
            st.dataframe(overview_df, use_container_width=True)

    events = system_activity.get('events') or []
    if events:
        with st.expander("📝 Recent System Activity", expanded=False):
            st.dataframe(pd.DataFrame(events).head(12), use_container_width=True)


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

# Import real compliance data service
sys.path.append(str(Path(__file__).parent.parent / "services"))
try:
    from compliance_data_service import ComplianceDataService  # type: ignore[import]
    compliance_service = ComplianceDataService()
except ImportError:
    compliance_service = None
    st.error("Compliance data service not available")

try:
    from services.api_client import AdminFastAPIClient
except ImportError:  # pragma: no cover - optional dependency for local dev
    AdminFastAPIClient = None

# Import shared components
# from shared.components import render_section_header, render_metrics_row  # Using fallback implementations
# from shared.integration_hooks import get_integration_hooks  # Using fallback implementations

# =============================================================================
# COMPLIANCE AUDIT CLASS
# =============================================================================

class ComplianceAudit:
    """Consolidated Compliance & Audit Suite"""

    def __init__(self):
        """Initialize compliance audit."""
        pass

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance overview metrics from real system data."""
        if compliance_service:
            return compliance_service.get_real_compliance_metrics()

        # No service available - return zeros
        # TODO: Connect to real compliance monitoring system
        return {
            'compliance_score': 0.0,
            'compliance_delta': 0.0,
            'audits_completed': 0,
            'audits_delta': 0,
            'issues_found': 0,
            'issues_delta': 0,
            'risk_level': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }

    def get_dataset_audit_results(self) -> List[Dict[str, Any]]:
        """Get dataset audit results from real system data."""
        if compliance_service:
            return compliance_service.get_real_dataset_audit_results()

        # No service available - return empty list
        # TODO: Connect to real dataset audit system
        return []

    def get_admin_audit_results(self, audit_areas: List[str], date_range: List) -> List[Dict[str, Any]]:
        """Get admin activity audit results."""
        if compliance_service:
            return compliance_service.get_admin_audit_results(audit_areas, date_range)

        # No service available - return empty list
        # TODO: Connect to real admin audit log system (database)
        return []

    def get_compliance_areas(self) -> List[Dict[str, Any]]:
        """Get enterprise compliance areas status from real system."""
        if compliance_service:
            return compliance_service.get_real_compliance_areas()

        # No service available - return empty list
        # TODO: Connect to real compliance tracking system
        return []

    def get_recent_audits(self) -> List[Dict[str, Any]]:
        """Get recent audit history."""
        if compliance_service:
            return compliance_service.get_recent_audits()

        # No service available - return empty list
        # TODO: Connect to real audit history database
        return []

    def generate_compliance_report(self, compliance_areas: List[Dict[str, Any]]) -> str:
        """Generate compliance report content."""
        if not compliance_areas:
            return f"""
INTELLICV COMPLIANCE REPORT
===========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

STATUS: No compliance data available

Please connect to compliance monitoring system to generate reports.

Report generated by IntelliCV Admin Portal
Contact: admin@intellicv.com
"""

        report_content = f"""
INTELLICV COMPLIANCE REPORT
===========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
-----------------
Overall Compliance Score: {sum(area['Score'] for area in compliance_areas) / len(compliance_areas):.1f}%
Total Areas Assessed: {len(compliance_areas)}
Areas Fully Compliant: {sum(1 for area in compliance_areas if '✅' in area['Status'])}
Areas with Issues: {sum(1 for area in compliance_areas if '⚠️' in area['Status'])}

DETAILED ASSESSMENT
-------------------
"""

        for area in compliance_areas:
            report_content += f"""
{area['Area']}:
  Status: {area['Status']}
  Score: {area['Score']}%
  Last Audit: {area['Last_Audit']}
  Next Review: {area['Next_Review']}
  Open Issues: {area['Issues']}
"""

        report_content += f"""

RECOMMENDATIONS
---------------
1. Continue regular compliance monitoring
2. Address any identified issues promptly
3. Schedule upcoming reviews as planned
4. Maintain documentation updates
5. Regular staff compliance training

Report generated by IntelliCV Admin Portal
Contact: admin@intellicv.com
"""

        return report_content

# =============================================================================
# RENDER FUNCTION
# =============================================================================

def render():
    """Render the Compliance Audit page."""
    # Initialize compliance audit
    compliance_audit = ComplianceAudit()

    render_section_header("🛡️ Compliance & Audit Suite", "Enterprise-grade compliance monitoring and audit management")

    st.markdown("### Compliance Dashboard")

    show_backend_api_status()
    st.markdown("---")

    if not compliance_service:
        st.info("🔌 **Compliance Service Required** - Connect to compliance monitoring system")

    # Get compliance metrics from real service or return zeros
    metrics = compliance_audit.get_compliance_metrics()

    # Compliance overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Compliance Score",
            f"{metrics['compliance_score']:.1f}%",
            f"+{metrics['compliance_delta']:.1f}%"
        )

    with col2:
        st.metric(
            "Audits Completed",
            metrics['audits_completed'],
            f"+{metrics['audits_delta']}"
        )

    with col3:
        delta_sign = "+" if metrics['issues_delta'] > 0 else ""
        st.metric(
            "Issues Found",
            metrics['issues_found'],
            f"{delta_sign}{metrics['issues_delta']}"
        )

    with col4:
        risk_color = "🟢" if metrics['risk_level'] == 'Low' else "🟡" if metrics['risk_level'] == 'Medium' else "🔴"
        st.metric("Risk Level", f"{risk_color} {metrics['risk_level']}")

    st.markdown("---")

    # Compliance tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dataset Audit",
        "🔍 Admin Activity Audit",
        "🏢 Enterprise Compliance",
        "📋 Audit Reports",
        "🔒 Security Monitoring"
    ])

    with tab1:
        st.subheader("📊 Dataset Integrity Audit")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔍 Dataset Health Check")

            if st.button("🔍 Scan All Datasets", type="primary"):
                with st.spinner("Scanning datasets for integrity issues..."):
                    time.sleep(3)  # Simulate scan time

                    # Get audit results
                    audit_results = compliance_audit.get_dataset_audit_results()

                    st.success(f"✅ Dataset scan completed - {len(audit_results)} issues found")

                    # Store results in session state
                    st.session_state['dataset_audit_results'] = audit_results

            # Display audit results if available
            audit_results = st.session_state.get('dataset_audit_results', [])

            if audit_results:
                st.markdown("#### 🚨 Identified Issues")

                for issue in audit_results:
                    severity_colors = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                    status_colors = {"Open": "🔴", "In Progress": "🟡", "Resolved": "🟢"}

                    with st.expander(f"{severity_colors[issue['Severity']]} {issue['Dataset']} - {issue['Issue']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.text(f"Severity: {issue['Severity']}")
                            st.text(f"Status: {status_colors[issue['Status']]} {issue['Status']}")
                        with col_b:
                            st.text(f"Detected: {issue['Detected']}")
                            if st.button(f"Resolve Issue", key=f"resolve_{issue['Dataset']}"):
                                st.success("Issue marked for resolution")

        with col2:
            st.markdown("#### 📊 Dataset Statistics")

            # TODO: Connect to real dataset monitoring system
            issues_count = len(st.session_state.get('dataset_audit_results', []))
            data_overview = (get_dashboard_snapshot() or {}).get('data_overview', {})
            total_datasets = int(sum(data_overview.values()))
            healthy_datasets = max(total_datasets - issues_count, 0)

            st.metric("Total Datasets", f"{total_datasets:,}")
            st.metric("Healthy Datasets", f"{healthy_datasets:,}")
            st.metric("Datasets with Issues", issues_count)

            if data_overview:
                overview_df = pd.DataFrame(
                    [{"Format": key.upper(), "Count": value} for key, value in data_overview.items()]
                )
                st.dataframe(overview_df, use_container_width=True)
            else:
                st.info("📊 Dataset statistics require database connection")

    with tab2:
        st.subheader("🔍 Admin Activity Audit")

        # Audit configuration
        col1, col2 = st.columns(2)

        with col1:
            audit_areas = st.multiselect("Select Audit Areas", [
                "User Access Logs",
                "Admin Actions",
                "Data Modifications",
                "System Configuration Changes",
                "API Usage",
                "File Operations"
            ], default=["User Access Logs", "Admin Actions"])

        with col2:
            date_range = st.date_input(
                "Audit Period",
                [datetime.now() - timedelta(days=7), datetime.now()],
                max_value=datetime.now()
            )

        if st.button("🔍 Run Admin Activity Audit", type="primary"):
            if audit_areas and len(date_range) == 2:
                with st.spinner("Analyzing admin activity logs..."):
                    time.sleep(2)

                    # Get audit results
                    audit_results = compliance_audit.get_admin_audit_results(audit_areas, list(date_range))

                    st.success(f"✅ Admin audit completed - {len(audit_results)} activities analyzed")

                    # Display results
                    if audit_results:
                        # Summary metrics
                        col_a, col_b, col_c = st.columns(3)

                        with col_a:
                            success_count = sum(1 for r in audit_results if r['Result'] == 'Success')
                            st.metric("Successful Actions", success_count)

                        with col_b:
                            failed_count = sum(1 for r in audit_results if r['Result'] == 'Failed')
                            st.metric("Failed Actions", failed_count)

                        with col_c:
                            unique_admins = len(set(r['Admin'] for r in audit_results))
                            st.metric("Unique Administrators", unique_admins)

                        # Detailed results table
                        st.markdown("#### 📋 Detailed Activity Log")

                        # Convert to DataFrame for better display
                        audit_df = pd.DataFrame(audit_results)

                        # Add color coding for results
                        def highlight_result(row):
                            if row['Result'] == 'Failed':
                                return ['background-color: #ffebee'] * len(row)
                            return [''] * len(row)

                        styled_df = audit_df.style.apply(highlight_result, axis=1)
                        st.dataframe(styled_df, use_container_width=True)

                        # Export audit log
                        if st.button("📥 Export Audit Log"):
                            audit_text = audit_df.to_csv(index=False)
                            st.download_button(
                                label="📊 Download Audit Log",
                                data=audit_text,
                                file_name=f"admin_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
            else:
                st.error("Please select audit areas and a valid date range.")

    with tab3:
        st.subheader("🏢 Enterprise Compliance Dashboard")

        # Get compliance areas
        compliance_areas = compliance_audit.get_compliance_areas()

        # Compliance overview
        st.markdown("#### 📊 Compliance Status Overview")

        for area in compliance_areas:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"**{area['Area']}**")
            with col2:
                st.write(area['Status'])
            with col3:
                st.write(f"{area['Score']}%")
            with col4:
                if area['Issues'] > 0:
                    st.write(f"🚨 {area['Issues']} issues")
                else:
                    st.write("✅ No issues")

        st.markdown("---")

        # Compliance score visualization
        col1, col2 = st.columns(2)

        with col1:
            # Compliance scores chart
            compliance_df = pd.DataFrame(compliance_areas)

            fig_compliance = px.bar(
                compliance_df,
                x='Area',
                y='Score',
                title='Compliance Scores by Area',
                color='Score',
                color_continuous_scale='RdYlGn',
                range_color=[80, 100]
            )
            fig_compliance.update_layout(height=400, xaxis_tickangle=45)
            st.plotly_chart(fig_compliance, use_container_width=True)

        with col2:
            # Overall compliance gauge
            overall_score = sum(area['Score'] for area in compliance_areas) / len(compliance_areas)

            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = overall_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Overall Compliance Score"},
                delta = {'reference': 90},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 80], 'color': "lightgray"},
                        {'range': [80, 90], 'color': "yellow"},
                        {'range': [90, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            fig_gauge.update_layout(height=400)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # Generate compliance report
        if st.button("📋 Generate Compliance Report", type="primary"):
            with st.spinner("Generating comprehensive compliance report..."):
                time.sleep(2)

                report_content = compliance_audit.generate_compliance_report(compliance_areas)

                st.success("✅ Compliance report generated successfully!")

                # Show report preview
                with st.expander("📋 Report Preview"):
                    st.text(report_content[:500] + "...")

                # Download report
                st.download_button(
                    label="📥 Download Full Compliance Report",
                    data=report_content,
                    file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

    with tab4:
        st.subheader("📋 Audit Reports & History")

        # Recent audits
        recent_audits = compliance_audit.get_recent_audits()

        st.markdown("#### 📚 Recent Audit History")

        # Convert to DataFrame
        audits_df = pd.DataFrame(recent_audits)

        # Add status color coding
        def highlight_status(row):
            colors = []
            for col in row.index:
                if col == 'Status':
                    if row[col] == 'Completed':
                        colors.append('background-color: #e8f5e8')
                    elif row[col] == 'In Progress':
                        colors.append('background-color: #fff3cd')
                    elif row[col] == 'Failed':
                        colors.append('background-color: #f8d7da')
                    else:
                        colors.append('')
                else:
                    colors.append('')
            return colors

        styled_audits_df = audits_df.style.apply(highlight_status, axis=1)
        st.dataframe(styled_audits_df, use_container_width=True)

        # Audit summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            completed_count = sum(1 for audit in recent_audits if audit['Status'] == 'Completed')
            st.metric("Completed Audits", completed_count)

        with col2:
            in_progress_count = sum(1 for audit in recent_audits if audit['Status'] == 'In Progress')
            st.metric("In Progress", in_progress_count)

        with col3:
            total_issues = sum(audit['Issues'] for audit in recent_audits if isinstance(audit['Issues'], int))
            st.metric("Total Issues Found", total_issues)

        with col4:
            avg_duration = sum(int(audit['Duration'].split()[0]) for audit in recent_audits if audit['Duration'] != '-') / max(1, sum(1 for audit in recent_audits if audit['Duration'] != '-'))
            st.metric("Avg Duration", f"{avg_duration:.0f} min")

        # Generate audit summary
        if st.button("📊 Generate Audit Summary Report"):
            with st.spinner("Generating audit summary..."):
                time.sleep(1)

                summary_content = f"""
AUDIT SUMMARY REPORT
====================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS
------------------
Total Audits: {len(recent_audits)}
Completed: {completed_count}
In Progress: {in_progress_count}
Total Issues Found: {total_issues}
Average Duration: {avg_duration:.0f} minutes

RECENT AUDIT DETAILS
--------------------
"""
                for audit in recent_audits[:5]:  # Top 5 recent audits
                    summary_content += f"""
Date: {audit['Date']}
Type: {audit['Type']}
Status: {audit['Status']}
Issues: {audit['Issues']}
Duration: {audit['Duration']}
Auditor: {audit['Auditor']}
---
"""

                st.success("✅ Audit summary generated!")

                st.download_button(
                    label="📥 Download Audit Summary",
                    data=summary_content,
                    file_name=f"audit_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

    with tab5:
        st.subheader("🔒 Security Monitoring & Alerts")

        security_metrics = get_user_security_snapshot() or {}
        user_metrics = get_user_metrics_snapshot() or {}
        suspicious_users = security_metrics.get('suspicious_users', 0)
        failed_logins = security_metrics.get('failed_login_attempts', 0)
        active_sessions = security_metrics.get('active_sessions', 0)

        # Security metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🚨 Security Alerts")
            if suspicious_users > 0:
                st.warning(f"⚠️ {suspicious_users} suspicious accounts require review")
            else:
                st.success("✅ No suspicious activity detected")
            st.caption(f"Failed logins last 24h: {failed_logins}")

        with col2:
            st.markdown("#### 🔐 Access Control")
            st.metric("Active Sessions", f"{active_sessions:,}")
            st.metric("Failed Logins (24h)", f"{failed_logins:,}")
            st.metric("Admin Users", f"{user_metrics.get('admin_users', 0):,}")

        with col3:
            st.markdown("#### 🛡️ Security Score")
            base_score = max(50.0, min(99.0, 100.0 - failed_logins * 0.05 - suspicious_users * 2))
            st.metric("Security Rating", f"{base_score:.1f}%")
            st.caption("Derived from FastAPI security metrics")

if __name__ == "__main__":
    render()
