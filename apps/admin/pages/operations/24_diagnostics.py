import streamlit as st
from services.backend_client import BackendClient
import plotly.graph_objects as go

st.set_page_config(page_title="Diagnostics", page_icon="🔬", layout="wide")

st.title("24 • System Diagnostics")
st.caption("Comprehensive system health monitoring")

client = BackendClient()

# Auto-refresh
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Real-time system metrics and health checks")
with col2:
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)

try:
    data = client.get("/ops/diagnostics")

    if data:
        # Health Status Banner
        status = data.get("status", "unknown")
        if status == "healthy":
            st.success(f"✅ System Status: **{status.upper()}**")
        elif status == "warning":
            st.warning(f"⚠️ System Status: **{status.upper()}**")
        else:
            st.error(f"❌ System Status: **{status.upper()}**")

        st.caption(f"Last checked: {data.get('timestamp', 'N/A')[:19]}")

        st.markdown("---")

        # System Metrics
        if "system_metrics" in data:
            st.subheader("📊 System Metrics")
            metrics = data["system_metrics"]

            col1, col2, col3 = st.columns(3)
            with col1:
                cpu = metrics.get("cpu_usage_percent", 0)
                st.metric("CPU Usage", f"{cpu:.1f}%", delta=f"{cpu - 50:.1f}%" if cpu > 50 else None)
            with col2:
                mem = metrics.get("memory_usage_percent", 0)
                st.metric("Memory Usage", f"{mem:.1f}%", delta=f"{mem - 70:.1f}%" if mem > 70 else None)
            with col3:
                disk = metrics.get("disk_usage_percent", 0)
                st.metric("Disk Usage", f"{disk:.1f}%", delta=f"{disk - 80:.1f}%" if disk > 80 else None)

            # Memory details
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Available Memory", f"{metrics.get('memory_available_gb', 0):.2f} GB")
            with col2:
                st.metric("Total Memory", f"{metrics.get('memory_total_gb', 0):.2f} GB")

        st.markdown("---")

        # Health Checks
        if "health_checks" in data:
            st.subheader("🏥 Health Checks")
            checks = data["health_checks"]

            cols = st.columns(4)
            for idx, (check_name, check_status) in enumerate(checks.items()):
                with cols[idx % 4]:
                    if check_status == "ok":
                        st.success(f"✅ {check_name.upper()}")
                    else:
                        st.warning(f"⚠️ {check_name.upper()}")

        st.markdown("---")

        # Path Status
        if "paths_status" in data:
            st.subheader("📁 Critical Paths Status")
            paths = data["paths_status"]

            cols = st.columns(3)
            for idx, (path_name, exists) in enumerate(paths.items()):
                with cols[idx % 3]:
                    status = "✅ Found" if exists else "❌ Missing"
                    st.metric(path_name.replace("_", " ").title(), status)

        st.markdown("---")

        # Automated Parser Files
        if "automated_parser_files" in data:
            st.subheader("📂 Automated Parser Files")
            files = data["automated_parser_files"]

            if files:
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("MSG Files", files.get("msg_files", 0))
                with col2:
                    st.metric("CSV Files", files.get("csv_files", 0))
                with col3:
                    st.metric("PDF Files", files.get("pdf_files", 0))
                with col4:
                    st.metric("DOC Files", files.get("doc_files", 0))
                with col5:
                    st.metric("Total Files", files.get("total_files", 0))
            else:
                st.info("No files found in automated_parser")

        st.markdown("---")

        # Raw JSON view
        with st.expander("🔍 View Raw Diagnostics Data"):
            st.json(data)

    else:
        st.warning("No diagnostics data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)

if auto_refresh:
    import time
    time.sleep(5)
    st.rerun()
