"""
=============================================================================
IntelliCV Admin Portal - Unified Analytics Dashboard (Page 28)
=============================================================================

Consolidated analytics dashboard merging functionality from pages 28, 29, 30.
Provides comprehensive statistics, production status, and data insights.

Features:
- Real-time system metrics
- Data integrity monitoring
- Processing statistics
- Performance analytics
- Production status tracking
- Candidate/Company insights

NO HARDCODED PATHS - Uses shared layer exclusively.
NO DEMO DATA - Real AI data only.
"""

import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime, timedelta
import time

# Shared services for backend telemetry
services_path = Path(__file__).parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

try:
    from services.backend_telemetry import BackendTelemetryHelper
except ImportError:  # pragma: no cover - backend optional offline
    BackendTelemetryHelper = None

# Add shared modules to path
shared_path = Path(__file__).parent.parent.parent / "shared"
backend_path = Path(__file__).parent.parent.parent / "shared_backend"
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(backend_path))

# Import shared layer - NO HARDCODED PATHS
from shared.config import AI_DATA_DIR, RAW_DATA_DIR, WORKING_COPY_DIR, get_system_status
from shared.io import (
    load_data_index,
    validate_data_integrity,
    load_analysis_report,
    get_latest_processing_report,
    get_company_stats,
    list_candidate_analyses,
    save_stats_payload,
    list_stats_files,
    browse_ai_data_structure
)

# Services imports
try:
    from services.intelligence_hub_connector import get_real_service_metrics
    INTELLIGENCE_HUB_AVAILABLE = True
except ImportError:
    INTELLIGENCE_HUB_AVAILABLE = False


TELEMETRY_HELPER = BackendTelemetryHelper(namespace="page26_unified_analytics") if BackendTelemetryHelper else None

# =============================================================================
# AUTHENTICATION CHECK
# =============================================================================

def check_authentication():
    """Real authentication check - NO FALLBACKS"""
    try:
        if 'authenticated' in st.session_state and st.session_state.authenticated:
            return True
        return False
    except:
        return False

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Unified Analytics | IntelliCV Admin",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# MAIN PAGE
# =============================================================================

def main():
    """Main analytics dashboard"""

    # Authentication
    if not check_authentication():
        st.error("🔒 Authentication required")
        st.stop()

    # Header
    st.title("📊 Unified Analytics Dashboard")
    st.markdown("**Comprehensive system metrics and data insights**")

    if TELEMETRY_HELPER:
        TELEMETRY_HELPER.render_status_panel(
            title="🛰️ Backend Telemetry Monitor",
            refresh_key="page26_backend_refresh",
        )

    # Data integrity check first - CRITICAL
    with st.spinner("🔍 Validating data integrity..."):
        integrity_check = validate_data_integrity()

    if integrity_check["status"] != "VALID":
        st.error("⚠️ CRITICAL: Data integrity issues detected!")
        with st.expander("🔍 View Integrity Details"):
            st.json(integrity_check)

        if not st.checkbox("⚠️ Continue with potentially corrupted data (not recommended)"):
            st.stop()
    else:
        st.success(f"✅ Data integrity validated: {integrity_check['actual_files']} files")

    st.markdown("---")

    # Tabs for consolidated functionality
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 System Overview",
        "📈 Processing Analytics",
        "🏢 Data Insights",
        "⚡ Performance Metrics",
        "🔍 Data Browser"
    ])

    with tab1:
        render_system_overview()

    with tab2:
        render_processing_analytics()

    with tab3:
        render_data_insights()

    with tab4:
        render_performance_metrics()

    with tab5:
        render_data_browser()

# =============================================================================
# TAB 1: SYSTEM OVERVIEW
# =============================================================================

def render_system_overview():
    """System status and health overview"""

    st.markdown("### 🎯 System Overview")

    # Get system status from shared config
    system_status = get_system_status()

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        candidates_count = len(list_candidate_analyses())
        st.metric("Total Candidates", f"{candidates_count:,}")

    with col2:
        company_stats = get_company_stats()
        companies_count = company_stats.get("total_companies", 0)
        st.metric("Total Companies", f"{companies_count:,}")

    with col3:
        ai_files = system_status.get("total_ai_files", 0)
        st.metric("AI Data Files", f"{ai_files:,}")

    with col4:
        data_health = "🟢 Healthy" if system_status.get("all_directories_valid", False) else "🔴 Issues"
        st.metric("Data Health", data_health)

    # Directory validation details
    st.markdown("### 📁 Directory Status")

    dir_validation = system_status.get("directory_validation", {})

    cols = st.columns(3)
    for i, (dir_name, valid) in enumerate(dir_validation.items()):
        with cols[i % 3]:
            status_icon = "✅" if valid else "❌"
            st.write(f"{status_icon} **{dir_name}**")

    # Intelligence services status (if available)
    if INTELLIGENCE_HUB_AVAILABLE:
        st.markdown("### 🧠 AI Services Status")

        try:
            service_metrics = get_real_service_metrics()

            col1, col2, col3 = st.columns(3)
            with col1:
                unified_status = service_metrics.get("unified_ai_engine", {}).get("status", "Unknown")
                st.metric("UnifiedAI Engine", unified_status)

            with col2:
                fusion_status = service_metrics.get("fusion_engine", {}).get("status", "Unknown")
                st.metric("Fusion Engine", fusion_status)

            with col3:
                portal_bridge_status = service_metrics.get("portal_bridge", {}).get("status", "Unknown")
                st.metric("Portal Bridge", portal_bridge_status)

        except Exception as e:
            st.warning(f"Could not load AI service metrics: {e}")

    # Save overview access stats
    overview_stats = {
        "page": "unified_analytics_overview",
        "system_status": system_status,
        "candidates_count": candidates_count,
        "companies_count": companies_count,
        "access_timestamp": datetime.now().isoformat()
    }

    try:
        save_stats_payload(overview_stats, "overview_access")
    except Exception as e:
        st.warning(f"Could not save overview stats: {e}")

# =============================================================================
# TAB 2: PROCESSING ANALYTICS
# =============================================================================

def render_processing_analytics():
    """Processing statistics and trends"""

    st.markdown("### 📈 Processing Analytics")

    # Load latest processing report
    try:
        processing_report = get_latest_processing_report()

        if not processing_report:
            st.warning("No processing reports available")
            return

        # Processing summary
        summary = processing_report.get("processing_summary", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_files = summary.get("total_files", 0)
            st.metric("Total Files Processed", f"{total_files:,}")

        with col2:
            processed_ok = summary.get("processed_ok", 0)
            st.metric("Successfully Processed", f"{processed_ok:,}")

        with col3:
            errors = summary.get("errors", 0)
            st.metric("Processing Errors", f"{errors:,}")

        with col4:
            if total_files > 0:
                success_rate = (processed_ok / total_files) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            else:
                st.metric("Success Rate", "N/A")

        # Processing details
        st.markdown("### 📋 Processing Details")

        # Top companies
        top_companies = processing_report.get("top_companies", [])
        if top_companies:
            st.markdown("**Top Companies by Volume:**")
            for i, company in enumerate(top_companies[:10], 1):
                st.write(f"{i}. {company.get('name', 'Unknown')} ({company.get('count', 0)} records)")

        # Top job titles
        top_job_titles = processing_report.get("top_job_titles", [])
        if top_job_titles:
            st.markdown("**Top Job Titles:**")
            for i, title in enumerate(top_job_titles[:10], 1):
                st.write(f"{i}. {title.get('title', 'Unknown')} ({title.get('count', 0)} occurrences)")

        # File counts breakdown
        file_counts = processing_report.get("file_counts", {})
        if file_counts:
            st.markdown("### 📊 File Distribution")

            df = pd.DataFrame(list(file_counts.items()), columns=['File Type', 'Count'])
            st.bar_chart(df.set_index('File Type'))

    except Exception as e:
        st.error(f"Failed to load processing analytics: {e}")

# =============================================================================
# TAB 3: DATA INSIGHTS
# =============================================================================

def render_data_insights():
    """Data distribution and insights"""

    st.markdown("### 🏢 Data Insights")

    # Company insights
    st.markdown("#### 🏭 Company Analysis")

    try:
        company_stats = get_company_stats()

        if company_stats.get("total_companies", 0) > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Top Industries:**")
                top_industries = company_stats.get("top_industries", [])
                for industry, count in top_industries[:8]:
                    st.write(f"• {industry}: {count}")

            with col2:
                st.markdown("**Top Locations:**")
                top_locations = company_stats.get("top_locations", [])
                for location, count in top_locations[:8]:
                    st.write(f"• {location}: {count}")

            # Industry distribution chart
            if top_industries:
                st.markdown("### 📊 Industry Distribution")
                industry_df = pd.DataFrame(top_industries[:10], columns=['Industry', 'Count'])
                st.bar_chart(industry_df.set_index('Industry'))

        else:
            st.info("No company data available for analysis")

    except Exception as e:
        st.error(f"Failed to load company insights: {e}")

    # Candidate insights
    st.markdown("#### 👥 Candidate Analysis")

    try:
        candidates_list = list_candidate_analyses()
        candidate_count = len(candidates_list)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Candidates", f"{candidate_count:,}")

        with col2:
            # Sample recent candidates for analysis
            recent_sample = candidates_list[:min(100, candidate_count)]
            st.metric("Analysis Sample", f"{len(recent_sample):,}")

        with col3:
            # Data coverage estimate
            coverage = min(100, (candidate_count / 1000) * 100) if candidate_count else 0
            st.metric("Data Coverage", f"{coverage:.1f}%")

        if candidate_count > 0:
            st.success(f"✅ Candidate analysis ready: {candidate_count} profiles available")
        else:
            st.warning("⚠️ No candidate analyses found")

    except Exception as e:
        st.error(f"Failed to load candidate insights: {e}")

# =============================================================================
# TAB 4: PERFORMANCE METRICS
# =============================================================================

def render_performance_metrics():
    """System performance and efficiency metrics"""

    st.markdown("### ⚡ Performance Metrics")

    # Data loading performance
    start_time = time.time()

    try:
        # Test data loading speed
        data_index = load_data_index()
        load_time = time.time() - start_time

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Data Index Load Time", f"{load_time:.3f}s")

        with col2:
            data_size = data_index.get("total_size_mb", 0)
            st.metric("Total Data Size", f"{data_size:.1f} MB")

        with col3:
            if load_time > 0:
                throughput = data_size / load_time
                st.metric("Load Throughput", f"{throughput:.1f} MB/s")

        # Recent stats files performance
        st.markdown("### 📊 Recent Activity")

        stats_files = list_stats_files()

        if stats_files:
            # Show recent stats files
            recent_files = stats_files[:10]

            st.markdown("**Recent Analytics Files:**")
            for file_info in recent_files:
                filename = file_info['filename']
                size_kb = file_info['size_bytes'] / 1024
                modified = file_info['modified'][:19].replace('T', ' ')
                st.write(f"• {filename} ({size_kb:.1f} KB) - {modified}")

            # Performance chart
            if len(stats_files) >= 3:
                file_sizes = [f['size_bytes'] / 1024 for f in recent_files]
                file_names = [f['filename'][:20] + '...' if len(f['filename']) > 20 else f['filename'] for f in recent_files]

                performance_df = pd.DataFrame({
                    'File': file_names,
                    'Size (KB)': file_sizes
                })

                st.bar_chart(performance_df.set_index('File'))

        else:
            st.info("No recent stats files to analyze")

    except Exception as e:
        st.error(f"Failed to load performance metrics: {e}")

# =============================================================================
# TAB 5: DATA BROWSER
# =============================================================================

def render_data_browser():
    """Interactive data structure browser"""

    st.markdown("### 🔍 Data Browser")
    st.info("Browse ai_data_final structure and content")

    try:
        # Load data structure
        structure_info = browse_ai_data_structure()

        if "error" in structure_info:
            st.error(f"Failed to browse structure: {structure_info['error']}")
            return

        data_index = structure_info.get("data_index", {})
        directory_structure = structure_info.get("directory_structure", {})

        # Data index overview
        st.markdown("#### 📋 Data Index")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write(f"**Generated:** {data_index.get('generated_at', 'Unknown')}")

        with col2:
            st.write(f"**Total Files:** {data_index.get('file_count', 0):,}")

        with col3:
            st.write(f"**Total Size:** {data_index.get('total_size_mb', 0):.1f} MB")

        # Directory browser
        st.markdown("#### 📁 Directory Structure")

        selected_dir = st.selectbox(
            "Select Directory:",
            list(directory_structure.keys()) if directory_structure else []
        )

        if selected_dir and selected_dir in directory_structure:
            dir_info = directory_structure[selected_dir]

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Files in Directory", dir_info['file_count'])

            with col2:
                has_more = dir_info.get('more_files', False)
                st.metric("Showing", f"{'First 10' if has_more else 'All'} files")

            # List files
            files = dir_info.get('files', [])
            if files:
                st.markdown("**Files:**")
                for file in files:
                    st.write(f"• {file}")

                if has_more:
                    st.info("...and more files in this directory")

                # File preview option
                if st.checkbox("Enable file preview (select a JSON file)"):
                    selected_file = st.selectbox("Select file to preview:", files)

                    if selected_file and selected_file.endswith('.json'):
                        try:
                            file_path = AI_DATA_DIR / selected_dir / selected_file
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = json.load(f)

                            st.markdown(f"**Preview of {selected_file}:**")
                            st.json(file_content)

                        except Exception as e:
                            st.error(f"Could not preview file: {e}")

            else:
                st.info("No files found in this directory")

    except Exception as e:
        st.error(f"Failed to load data browser: {e}")

# =============================================================================
# RUN MAIN
# =============================================================================

if __name__ == "__main__":
    main()
