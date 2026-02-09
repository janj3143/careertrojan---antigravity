import streamlit as st
from services.backend_client import BackendClient
import pandas as pd

st.set_page_config(page_title="API Route Map", page_icon="🗺️", layout="wide")

st.title("27 • API Route Map")
st.caption("Explore all available API endpoints")

client = BackendClient()

# Refresh button
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("Complete map of all API routes and their status")
with col2:
    if st.button("🔄 Refresh"):
        st.rerun()

try:
    data = client.get("/ops/routes")

    if data and "routes" in data:
        # Summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Routes", data.get("total_routes", 0))
        with col2:
            st.metric("Last Updated", data.get("last_updated", 'N/A')[:19])

        st.markdown("---")

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            method_filter = st.multiselect("Filter by Method", ["GET", "POST", "PUT", "DELETE", "PATCH"])
        with col2:
            status_filter = st.multiselect("Filter by Status", ["active", "inactive", "deprecated"])

        # Display routes
        routes = data["routes"]

        # Apply filters
        if method_filter:
            routes = [r for r in routes if r.get("method") in method_filter]
        if status_filter:
            routes = [r for r in routes if r.get("status") in status_filter]

        # Group by prefix
        st.subheader("📋 API Endpoints")

        for route in routes:
            with st.expander(f"{route.get('method', 'GET')} {route.get('path', '/')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Description:** {route.get('description', 'N/A')}")
                    st.markdown(f"**Method:** `{route.get('method', 'GET')}`")
                with col2:
                    status = route.get('status', 'unknown')
                    if status == "active":
                        st.success(f"Status: ✅ {status}")
                    elif status == "deprecated":
                        st.warning(f"Status: ⚠️ {status}")
                    else:
                        st.info(f"Status: {status}")

                # Test endpoint button
                if st.button(f"🧪 Test Endpoint", key=f"test_{route.get('path')}"):
                    st.info(f"Testing {route.get('path')}...")
                    try:
                        test_result = client.get(route.get('path', '/'))
                        st.json(test_result)
                    except Exception as e:
                        st.error(f"Test failed: {str(e)}")

        if not routes:
            st.info("No routes match your filters")

    else:
        st.warning("No route data available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
