import streamlit as st
from services.backend_client import BackendClient
import pandas as pd

st.set_page_config(page_title="Logs Viewer", page_icon="📜", layout="wide")

st.title("23 • System Logs Viewer")
st.caption("View and search system logs")

client = BackendClient()

# Controls
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    log_level = st.selectbox("Filter by Level", ["All", "INFO", "WARNING", "ERROR", "DEBUG"])
with col2:
    limit = st.number_input("Limit", min_value=10, max_value=1000, value=100, step=10)
with col3:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    params = {"limit": limit}
    if log_level != "All":
        params["level"] = log_level

    data = client.get("/ops/logs", **params)

    if data and "logs" in data:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Logs", data.get("total_count", 0))
        with col2:
            st.metric("Filter", data.get("filter_applied", "None") or "All")
        with col3:
            st.metric("Limit", data.get("limit", limit))

        st.markdown("---")

        # Search box
        search_term = st.text_input("🔍 Search logs", placeholder="Enter search term...")

        # Display logs
        if data["logs"]:
            logs = data["logs"]

            # Apply search filter
            if search_term:
                logs = [log for log in logs if search_term.lower() in log.get("message", "").lower()]

            # Display as dataframe
            df = pd.DataFrame(logs)
            display_cols = ["timestamp", "level", "message", "source"]
            df_display = df[[col for col in display_cols if col in df.columns]]

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Download option
            if st.button("📥 Download Logs"):
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"logs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No logs found matching your criteria")

    else:
        st.info("No log data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
