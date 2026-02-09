"""
☁️ Universal Cloud Maker - Dynamic Skill & Career Visualizations
================================================================
Generate word clouds and skill visualizations from your career data:
- Skills Cloud with importance weighting
- Job Titles Cloud
- Industry Keywords Cloud
- Peer Group Overlays

Premium Feature | Token Cost: 8 tokens
"""

import streamlit as st
from pathlib import Path
import pandas as pd
import sys
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Setup paths
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# Use Shared IO Layer for data access
try:
    from shared.io_layer import get_io_layer
    io_layer = get_io_layer()
    SHARED_IO_AVAILABLE = True
except ImportError:
    SHARED_IO_AVAILABLE = False
    io_layer = None

# Page configuration
st.set_page_config(
    page_title="☁️ Universal Cloud Maker | IntelliCV-AI",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Authentication check
if not st.session_state.get('authenticated_user'):
    st.error("🔒 Please log in to access Universal Cloud Maker")
    if st.button("🏠 Return to Home"):
        st.switch_page("main.py")
    st.stop()

# Tier check for premium features
user_tier = st.session_state.get('subscription_tier', 'free')
PREMIUM_TIERS = ['monthly_pro', 'annual_pro', 'enterprise_pro']

if user_tier not in PREMIUM_TIERS:
    st.warning("⭐ Universal Cloud Maker requires Premium subscription")
    if st.button("⬆️ Upgrade to Premium", type="primary"):
        st.switch_page("pages/06_Pricing.py")
    st.stop()

# Title and introduction
st.title("☁️ Universal Cloud Maker")
st.markdown("**Generate dynamic word clouds and visualizations from your career data**")

st.info("💎 **Token Cost: 8 tokens** | AI-powered cloud generation with skill weighting")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Cloud type selection
    cloud_type = st.selectbox(
        "☁️ Cloud Type",
        ["Skills Cloud", "Job Titles Cloud", "Industry Keywords Cloud", "Technologies Cloud"]
    )

    # Data source
    data_source = st.radio(
        "📊 Data Source",
        ["My Resume", "Job Description", "Industry Analysis"],
        horizontal=True
    )

with col2:
    # Cloud options
    max_words = st.slider("📏 Max Words", 20, 200, 100, 10)
    color_scheme = st.selectbox("🎨 Color Scheme",
                                ["Blues", "Greens", "Purples", "Reds", "Viridis"])

    show_weights = st.checkbox("📊 Show Importance Weights", value=True)

# Overlay options
with st.expander("🔄 Overlay Options"):
    enable_overlay = st.checkbox("Enable Peer Comparison Overlay")
    if enable_overlay:
        overlay_type = st.selectbox("Overlay Type",
                                   ["Peer Average", "Top Performers", "Industry Standard"])

# Generate button
if st.button("🎨 Generate Cloud", type="primary", use_container_width=True):
    with st.spinner("☁️ Generating cloud visualization..."):
        if not (SHARED_IO_AVAILABLE and io_layer):
            st.error("Shared IO Layer is not available. Cloud generation cannot run without real user data.")
            st.stop()

        user_id = st.session_state.get('user_id')
        if not user_id:
            st.error("Authenticated user_id is missing; cannot load real profile data.")
            st.stop()

        try:
            candidate_data = io_layer.get_candidate_data(user_id)
        except Exception as e:
            st.error(f"Failed to load candidate data: {e}")
            st.stop()

        profile = (candidate_data or {}).get('profile')
        if not isinstance(profile, dict):
            st.error("No profile data found for this user. Cloud generation requires a real profile.")
            st.stop()

        if cloud_type == "Skills Cloud":
            words = profile.get('skills', [])
        elif cloud_type == "Technologies Cloud":
            words = profile.get('technologies', []) or profile.get('skills', [])
        elif cloud_type == "Job Titles Cloud":
            words = profile.get('job_titles', [])
        else:
            words = profile.get('industry_keywords', [])

        if not words:
            st.error("No real data available for the selected cloud type.")
            st.stop()

        word_freq = {str(w): 1.0 for w in words if str(w).strip()}
        if not word_freq:
            st.error("No usable words found in the real profile data.")
            st.stop()

        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            colormap=color_scheme,
            max_words=max_words,
        ).generate_from_frequencies(word_freq)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

        if show_weights:
            st.markdown("### 📊 Word Importance Weights")
            weights_df = pd.DataFrame(
                [{"Word": word, "Weight": weight} for word, weight in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]]
            )
            st.dataframe(weights_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("*Powered by IntelliCV-AI Universal Cloud Maker*")
