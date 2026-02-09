import streamlit as st
from services.backend_client import BackendClient

st.set_page_config(page_title="About", page_icon="ℹ️", layout="wide")

st.title("29 • About IntelliCV")
st.caption("System information and version details")

client = BackendClient()

try:
    data = client.get("/about")

    if data:
        # Header banner
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; padding: 2rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;'>
            <h1>{data.get('system_name', 'IntelliCV')}</h1>
            <h3>Version {data.get('version', '1.0.0')} • Built {data.get('build_date', 'N/A')}</h3>
            <p>Environment: <strong>{data.get('environment', 'production').upper()}</strong></p>
        </div>
        """, unsafe_allow_html=True)

        # Components
        st.subheader("🧩 System Components")
        if "components" in data:
            components = data["components"]
            cols = st.columns(len(components))
            for idx, (component, version) in enumerate(components.items()):
                with cols[idx]:
                    st.metric(component.replace("_", " ").title(), version)

        st.markdown("---")

        # Features
        st.subheader("✨ Key Features")
        if "features" in data:
            features = data["features"]
            for feature in features:
                st.markdown(f"- {feature}")

        st.markdown("---")

        # Contact information
        st.subheader("📞 Contact & Support")
        if "contact" in data:
            contact = data["contact"]
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Support Email:** {contact.get('support_email', 'N/A')}")
            with col2:
                st.markdown(f"**Documentation:** {contact.get('documentation', 'N/A')}")

        st.markdown("---")

        # Technology stack
        st.subheader("🛠️ Technology Stack")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Frontend**")
            st.markdown("- Streamlit")
            st.markdown("- Plotly")
            st.markdown("- Pandas")
        with col2:
            st.markdown("**Backend**")
            st.markdown("- FastAPI")
            st.markdown("- Python 3.10+")
            st.markdown("- PostgreSQL")
        with col3:
            st.markdown("**AI/ML**")
            st.markdown("- OpenAI GPT")
            st.markdown("- Spacy NLP")
            st.markdown("- Scikit-learn")

        st.markdown("---")

        # License and credits
        st.subheader("📜 License & Credits")
        st.markdown("""
        © 2025 IntelliCV. All rights reserved.

        This software is proprietary and confidential. Unauthorized copying, distribution,
        or use of this software is strictly prohibited.
        """)

        st.markdown("---")
        st.caption(f"Last Updated: {data.get('last_updated', 'N/A')[:19]}")

    else:
        st.warning("No system information available")

except Exception as e:
    st.error("❌ Backend call failed")
    with st.expander("Error Details"):
        st.exception(e)
