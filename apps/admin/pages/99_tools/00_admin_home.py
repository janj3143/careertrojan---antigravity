import streamlit as st
from shared.env import settings

st.title("00 • Admin Home")
st.write("Admin = UI only. Execution happens in the backend service.")
st.code(f"AI_DATA_ROOT = {settings.AI_DATA_ROOT}\nBACKEND_BASE_URL = {settings.BACKEND_BASE_URL}")
