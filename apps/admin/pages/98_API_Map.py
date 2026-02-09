
import streamlit as st
import streamlit.components.v1 as components
import json
from pathlib import Path

st.set_page_config(page_title="API & Endpoint Map", page_icon="🗺️", layout="wide")

st.title("🗺️ API Endpoint & Dependency Map")

# Paths to generated files
MAPPING_ROOT = Path("static/mapping")
VISUAL_HTML = MAPPING_ROOT / "endpoints_visual.html"
ENDPOINTS_JSON = MAPPING_ROOT / "endpoints.json"
CONNECTIONS_JSON = MAPPING_ROOT / "connections.json"

tab1, tab2 = st.tabs(["Visualization", "Raw Data"])

with tab1:
    if VISUAL_HTML.exists():
        with open(VISUAL_HTML, "r", encoding="utf-8") as f:
            html_content = f.read()
        # Clean up relative paths in the HTML for Streamlit embedding if necessary
        # The HTML fetches .json files relative to itself. 
        # In Streamlit, static files are served differently. 
        # For a quick fix, we can inject the JSON data directly into the HTML or use Streamlit's static serving.
        
        # Injecting JSON data directly to ensure it works without static server config issues
        if ENDPOINTS_JSON.exists() and CONNECTIONS_JSON.exists():
            ep_data = json.dumps(json.loads(ENDPOINTS_JSON.read_text(encoding="utf-8")))
            conn_data = json.dumps(json.loads(CONNECTIONS_JSON.read_text(encoding="utf-8")))
            
            # Monkey-patch the fetch calls in the HTML
            # This is a bit hacky but robust for a single-file portable visualizer
            html_content = html_content.replace(
                'fetch("./connections.json").then(r=>r.json())',
                f'Promise.resolve({conn_data})'
            ).replace(
                'fetch("./endpoints.json").then(r=>r.json())',
                f'Promise.resolve({ep_data})'
            )
            
        components.html(html_content, height=800, scrolling=True)
    else:
        st.error(f"Visualization Map not found at {VISUAL_HTML}")
        if st.button("Regenerate Map"):
            # Call the PowerShell script or Python script to regenerate
            st.info("Triggering regeneration... (Not implemented in this demo)")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Endpoints")
        if ENDPOINTS_JSON.exists():
            st.json(json.loads(ENDPOINTS_JSON.read_text(encoding="utf-8")))
    with col2:
        st.subheader("Graph Connections")
        if CONNECTIONS_JSON.exists():
            st.json(json.loads(CONNECTIONS_JSON.read_text(encoding="utf-8")))
