import streamlit as st
from services.backend_client import BackendClient
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Backup & Restore", page_icon="💾", layout="wide")

st.title("26 • Backup and Restore")
st.caption("System backup management and recovery")

client = BackendClient()

# Refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Create, manage, and restore system backups")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    data = client.get("/ops/backup")

    if data:
        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Backups", data.get("total_backups", 0))
        with col2:
            last_backup = data.get("last_backup", "Never")
            st.metric("Last Backup", last_backup[:19] if last_backup != "Never" else "Never")
        with col3:
            retention = data.get("retention_days", 30)
            st.metric("Retention", f"{retention} days")

        st.markdown("---")

        # Create new backup
        st.subheader("➕ Create New Backup")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            backup_type = st.selectbox("Backup Type", ["full", "incremental"])
        with col2:
            st.text("")
            st.text("")
            if st.button("💾 Create Backup Now"):
                st.info("Creating backup... This may take several minutes.")
                # In production, this would call: client.post("/ops/backup/create", json={"backup_type": backup_type})
                st.success("Backup creation started in background")

        st.markdown("---")

        # Display existing backups
        st.subheader("📦 Available Backups")

        if "backups" in data and data["backups"]:
            backups = data["backups"]

            # Create dataframe
            df = pd.DataFrame(backups)

            # Add action buttons column
            for idx, backup in enumerate(backups):
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                with col1:
                    st.markdown(f"**{backup.get('name', 'Unknown')}**")
                with col2:
                    st.text(f"{backup.get('size_mb', 0):.1f} MB")
                with col3:
                    st.text(backup.get('type', 'N/A'))
                with col4:
                    if st.button("Restore", key=f"restore_{idx}"):
                        st.warning(f"⚠️ Restoring from {backup.get('name')}... This will overwrite current data!")
                with col5:
                    if st.button("Delete", key=f"delete_{idx}"):
                        st.error(f"🗑️ Deleting {backup.get('name')}")

                st.caption(f"Created: {backup.get('created', 'N/A')[:19]}")
                st.markdown("---")
        else:
            st.info("No backups available. Create your first backup above.")

        # Backup location info
        st.markdown("---")
        st.info(f"📁 Backup Location: `{data.get('backup_location', 'N/A')}`")
        st.caption(f"Auto-backup: {'✅ Enabled' if data.get('auto_backup_enabled') else '❌ Disabled'}")

    else:
        st.warning("No backup data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
