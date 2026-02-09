import streamlit as st
from services.backend_client import BackendClient
import json

st.set_page_config(page_title="API Explorer", page_icon="🔍", layout="wide")

st.title("28 • API Explorer")
st.caption("Interactive API testing and exploration")

client = BackendClient()

st.markdown("Test API endpoints with custom parameters")

# API endpoint input
col1, col2 = st.columns([3, 1])
with col1:
    endpoint = st.text_input("API Endpoint", value="/about", placeholder="/ops/config")
with col2:
    method = st.selectbox("Method", ["GET", "POST", "PUT", "DELETE"])

# Parameters
st.subheader("📝 Query Parameters")
col1, col2 = st.columns(2)
with col1:
    param_name = st.text_input("Parameter Name", placeholder="e.g., limit")
with col2:
    param_value = st.text_input("Parameter Value", placeholder="e.g., 100")

# Body for POST/PUT
body_text = ""
if method in ["POST", "PUT"]:
    st.subheader("📦 Request Body (JSON)")
    body_text = st.text_area("Body", value='{\n  "example": "value"\n}', height=150)

# Execute button
if st.button("🚀 Execute Request", type="primary"):
    st.markdown("---")
    st.subheader("📊 Response")

    try:
        params = {}
        if param_name and param_value:
            params[param_name] = param_value

        if method == "GET":
            result = client.get(endpoint, **params)
            st.success("✅ Request successful")

            # Display response
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status", "200 OK")
            with col2:
                st.metric("Response Size", f"{len(json.dumps(result))} bytes")

            # JSON response
            st.json(result)

            # Pretty print option
            with st.expander("📋 Copy Response"):
                st.code(json.dumps(result, indent=2), language="json")
        else:
            st.info(f"{method} requests not yet implemented in BackendClient")

    except Exception as e:
        st.error("❌ Request failed")
        st.exception(e)

# Quick links to common endpoints
st.markdown("---")
st.subheader("⚡ Quick Access")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔍 Diagnostics"):
        st.rerun()
        endpoint = "/ops/diagnostics"
with col2:
    if st.button("⚙️ Config"):
        st.rerun()
        endpoint = "/ops/config"
with col3:
    if st.button("📊 About"):
        st.rerun()
        endpoint = "/about"

# OpenAPI documentation
st.markdown("---")
with st.expander("📖 View OpenAPI Documentation"):
    try:
        openapi_data = client.get("/openapi")
        st.json(openapi_data)
    except Exception as e:
        st.info("OpenAPI documentation endpoint not available")
