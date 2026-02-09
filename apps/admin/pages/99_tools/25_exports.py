import streamlit as st
from services.backend_client import BackendClient

st.title("25 • Exports")
st.caption("This page is UI-only and pulls data from the backend API.")

client = BackendClient()

if st.button("Refresh"):
    try:
        data = client.get("/exports")
        st.json(data)
    except Exception as e:
        st.error("Backend call failed")
        st.exception(e)
