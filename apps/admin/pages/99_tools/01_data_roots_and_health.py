import streamlit as st
from shared.env import settings
from services.backend_client import BackendClient

st.title("01 • Data Roots and Health")

client = BackendClient()

col1, col2 = st.columns(2)
with col1:
    st.subheader("Configured roots")
    st.json({"AI_DATA_ROOT": settings.AI_DATA_ROOT, "BACKEND_BASE_URL": settings.BACKEND_BASE_URL})

with col2:
    st.subheader("Backend health")
    try:
        data = client.get("/health")
        st.success("Backend reachable")
        st.json(data)
    except Exception as e:
        st.error("Backend not reachable")
        st.exception(e)
