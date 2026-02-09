import streamlit as st
from services.backend_client import BackendClient
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Admin Audit", page_icon="📋", layout="wide")

st.title("20 • Admin Audit Trail")
st.caption("Track all administrative actions and system changes")

client = BackendClient()

# Auto-refresh toggle
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Monitor all administrative actions, configuration changes, and system access")
with col2:
    auto_refresh = st.checkbox("Auto-refresh", value=False)

try:
    data = client.get("/audit/admin")

    if data and "audit_entries" in data:
        st.metric("Total Audit Entries", data.get("total_entries", 0))
        st.caption(f"Last Activity: {data.get('last_activity', 'N/A')}")

        # Display audit entries
        if data["audit_entries"]:
            df = pd.DataFrame(data["audit_entries"])

            # Format columns for better display
            display_cols = ["timestamp", "admin_user", "action", "resource", "status", "details"]
            df_display = df[[col for col in display_cols if col in df.columns]]

            # Add filtering
            col1, col2, col3 = st.columns(3)
            with col1:
                action_filter = st.multiselect("Filter by Action", df["action"].unique() if "action" in df else [])
            with col2:
                status_filter = st.multiselect("Filter by Status", df["status"].unique() if "status" in df else [])
            with col3:
                user_filter = st.multiselect("Filter by User", df["admin_user"].unique() if "admin_user" in df else [])

            # Apply filters
            filtered_df = df_display.copy()
            if action_filter:
                filtered_df = filtered_df[filtered_df["action"].isin(action_filter)]
            if status_filter:
                filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]
            if user_filter:
                filtered_df = filtered_df[filtered_df["admin_user"].isin(user_filter)]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # Export option
            if st.button("📥 Export Audit Log"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No audit entries found")
    else:
        st.warning("No audit data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)

if auto_refresh:
    st.rerun()
