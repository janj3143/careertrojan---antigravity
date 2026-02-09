import streamlit as st
from services.backend_client import BackendClient
import json

st.set_page_config(page_title="System Config", page_icon="⚙️", layout="wide")

st.title("22 • System Configuration")
st.caption("View and manage system settings")

client = BackendClient()

# Refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Comprehensive system configuration and settings")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    data = client.get("/ops/config")

    if data:
        # System Information
        if "system" in data:
            st.subheader("🖥️ System Information")
            sys_info = data["system"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Platform", sys_info.get("platform", "N/A"))
            with col2:
                st.metric("Python", sys_info.get("python_version", "N/A"))
            with col3:
                st.metric("Processor", sys_info.get("processor", "N/A")[:20])
            with col4:
                st.metric("Architecture", sys_info.get("architecture", "N/A"))

        st.markdown("---")

        # Paths Configuration
        if "paths" in data:
            st.subheader("📁 System Paths")
            paths = data["paths"]
            for path_name, path_value in paths.items():
                st.text(f"{path_name}: {path_value}")

        st.markdown("---")

        # Features
        if "features" in data:
            st.subheader("✨ Enabled Features")
            features = data["features"]
            cols = st.columns(3)
            for idx, (feature_name, enabled) in enumerate(features.items()):
                with cols[idx % 3]:
                    status = "✅ Enabled" if enabled else "❌ Disabled"
                    st.metric(feature_name.replace("_", " ").title(), status)

        st.markdown("---")

        # System Limits
        if "limits" in data:
            st.subheader("⚡ System Limits")
            limits = data["limits"]
            col1, col2, col3 = st.columns(3)
            for idx, (limit_name, limit_value) in enumerate(limits.items()):
                with [col1, col2, col3][idx % 3]:
                    st.metric(limit_name.replace("_", " ").title(), limit_value)

        st.markdown("---")

        # Raw JSON view
        with st.expander("🔍 View Raw Configuration JSON"):
            st.json(data)

    else:
        st.warning("No configuration data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
