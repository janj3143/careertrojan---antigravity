
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False

"""
System Monitor Page for IntelliCV Admin Portal
Shows system health, logs, and performance metrics with help/hover features.
"""
import streamlit as st
from pathlib import Path
from utils.log_utils import get_latest_log_content
from utils.stats_utils import (
    get_resume_count, get_daily_processed_count, get_running_jobs_count,
    get_last_sync_time, check_system_health, get_recent_activity
)
from utils.help_sidebar import show_help_sidebar
from utils.ui_helpers import metric_with_help, button_with_help

LOGS_DIR = Path("data/logs")  # Adjust as needed for your deployment
DATA_DIR = Path("IntelliCV-data")

def main():
    st.set_page_config(page_title="System Monitor", layout="wide")

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    show_help_sidebar()
    st.title("🖥️ System Monitor")
    st.write("Monitor system health, logs, and performance metrics.")

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        metric_with_help("Total Resumes", get_resume_count(DATA_DIR), "Total number of resumes in the system.")
    with col2:
        metric_with_help("Processed Today", get_daily_processed_count(LOGS_DIR), "Number of resumes processed today.")
    with col3:
        metric_with_help("AI Jobs Running", get_running_jobs_count(), "Number of currently running AI jobs.")
    with col4:
        metric_with_help("Last Sync", get_last_sync_time(), "Last synchronization time.")
    with col5:
        metric_with_help("System Health", check_system_health(), "Overall system health status.")

    st.subheader("Recent Activity")
    activity = get_recent_activity(limit=10)
    st.table(activity)

    st.subheader("Latest Log File")
    log_info = get_latest_log_content(LOGS_DIR)
    if log_info.get("file"):
        st.write(f"**File:** {log_info['file']}  ")
        st.write(f"**Modified:** {log_info['modified']}  ")
        st.write(f"**Size:** {log_info['size']} bytes  ")
        st.text_area("Log Tail", log_info["content"], height=300)
    else:
        st.info("No log file found.")

if __name__ == "__main__":
    main()
