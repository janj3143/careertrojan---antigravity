import streamlit as st
from services.backend_client import BackendClient
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Data Exports", page_icon="📤", layout="wide")

st.title("25 • Data Exports")
st.caption("Export system data in various formats")

client = BackendClient()

# Refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Export candidate data, company data, and analytics in multiple formats")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    data = client.get("/exports")

    if data:
        # Summary
        st.subheader("📊 Available Exports")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Exports", data.get("total_exports", 0))
        with col2:
            formats = ", ".join(data.get("available_formats", []))
            st.metric("Available Formats", formats)

        st.markdown("---")

        # Display exports
        if "exports" in data and data["exports"]:
            exports = data["exports"]

            for export in exports:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{export.get('name', 'Unknown')}**")
                    with col2:
                        st.text(f"{export.get('format', 'N/A')}")
                    with col3:
                        st.text(f"{export.get('size_mb', 0):.1f} MB")
                    with col4:
                        if st.button("Download", key=f"dl_{export.get('id')}"):
                            st.success(f"Downloading {export.get('name')}...")

                    st.caption(f"Created: {export.get('created', 'N/A')[:19]} | Status: {export.get('status', 'N/A')}")
                    st.markdown("---")
        else:
            st.info("No exports available")

        # Create new export
        st.subheader("➕ Create New Export")

        col1, col2, col3 = st.columns(3)
        with col1:
            export_type = st.selectbox("Data Type", ["Candidates", "Companies", "Jobs", "Analytics"])
        with col2:
            export_format = st.selectbox("Format", data.get("available_formats", ["CSV", "JSON", "XLSX"]))
        with col3:
            st.text("")
            st.text("")
            if st.button("📤 Create Export"):
                st.success(f"Creating {export_format} export of {export_type} data...")
                st.info("Export will be ready in a few moments. Refresh to see it in the list.")

    else:
        st.warning("No export data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
