import streamlit as st
from services.backend_client import BackendClient
import pandas as pd

st.set_page_config(page_title="Notifications", page_icon="🔔", layout="wide")

st.title("21 • System Notifications")
st.caption("Real-time alerts and system notifications")

client = BackendClient()

# Refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Stay informed about system events, warnings, and updates")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    data = client.get("/ops/notifications")

    if data and "notifications" in data:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Notifications", len(data["notifications"]))
        with col2:
            st.metric("Unread", data.get("unread_count", 0))
        with col3:
            st.metric("Last Updated", data.get("last_updated", "N/A")[:19])

        st.markdown("---")

        # Display notifications by type
        notifications = data["notifications"]

        # Filter by type
        filter_type = st.selectbox("Filter by Type", ["All", "info", "warning", "error", "success"])

        filtered_notifications = notifications if filter_type == "All" else [
            n for n in notifications if n.get("type") == filter_type
        ]

        # Display each notification
        for notif in filtered_notifications:
            notif_type = notif.get("type", "info")

            # Color coding based on type
            if notif_type == "error":
                st.error(f"**{notif.get('title')}**\n\n{notif.get('message')}\n\n*{notif.get('timestamp', 'N/A')[:19]}*")
            elif notif_type == "warning":
                st.warning(f"**{notif.get('title')}**\n\n{notif.get('message')}\n\n*{notif.get('timestamp', 'N/A')[:19]}*")
            elif notif_type == "success":
                st.success(f"**{notif.get('title')}**\n\n{notif.get('message')}\n\n*{notif.get('timestamp', 'N/A')[:19]}*")
            else:
                st.info(f"**{notif.get('title')}**\n\n{notif.get('message')}\n\n*{notif.get('timestamp', 'N/A')[:19]}*")

        if not filtered_notifications:
            st.info("No notifications match your filter")

    else:
        st.info("No notifications available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
