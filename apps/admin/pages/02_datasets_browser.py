import streamlit as st
from services.fs_view import list_dir

st.title("02 • Datasets Browser")
st.caption("UI-only directory browser rooted at AI_DATA_ROOT")

rel = st.text_input("Relative path under AI_DATA_ROOT", value="")
data = list_dir(rel)

if not data["exists"]:
    st.error(f"Path not found: {data['path']}")
else:
    st.write(f"Path: {data['path']}")
    for item in data["items"]:
        icon = "📁" if item["is_dir"] else "📄"
        size = "" if item["is_dir"] else f" ({item['size']} bytes)"
        st.write(f"{icon} {item['name']}{size}")
