import streamlit as st
import json
from pathlib import Path
from shared.env import settings

st.title("03 • Resume JSON Viewer")
st.caption("UI-only JSON viewer. Point to a file under AI_DATA_ROOT.")

rel = st.text_input("Relative JSON path", value="")
if rel:
    p = Path(settings.AI_DATA_ROOT).joinpath(rel)
    if not p.exists():
        st.error(f"Not found: {p}")
    else:
        try:
            st.json(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:
            st.error("Failed to parse JSON")
            st.exception(e)
else:
    st.info("Example: `individual_json/sample.json`")
