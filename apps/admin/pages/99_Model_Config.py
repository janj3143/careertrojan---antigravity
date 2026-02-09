
import streamlit as st
import sys
from pathlib import Path

# Add services path
sys.path.append(str(Path(__file__).resolve().parents[3]))
from services.ai_engine.llm_service import LLMFactory, LLMBackendType

st.set_page_config(page_title="Model Configuration", page_icon="⚙️", layout="wide")

st.title("⚙️ AI Model Configuration")

st.markdown("### 🧠 LLM Backend Strategy")

# Current Status
current_backend = "openai" # In real app, fetch from global config/db
st.info(f"Current Active Backend: **{current_backend.upper()}**")

# Switcher
with st.container(border=True):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_backend = st.radio(
            "Select Inference Engine",
            [e.value for e in LLMBackendType],
            index=0,
            key="backend_selector"
        )
    
    with col2:
        if selected_backend == "vllm":
            st.warning("⚠️ High VRAM Requirement")
            vllm_endpoint = st.text_input("vLLM Endpoint URL", "http://localhost:8000/v1")
        elif selected_backend == "openai":
            st.success("✅ Cloud Hosted (Low Latency)")
            api_key = st.text_input("OpenAI API Key (masked)", type="password")
        elif selected_backend == "anthropic":
            st.success("✅ Cloud Hosted (Claude 3 Opus)")
            api_key = st.text_input("Anthropic API Key (masked)", type="password")

    if st.button("Apply Configuration"):
        # This would call an API or update a config file in production
        LLMFactory.switch_backend(selected_backend)
        st.success(f"Successfully switched runtime to {selected_backend.upper()}")

st.markdown("---")

st.markdown("### 📊 Bayesian & Statistical Models")

with st.expander("Bayesian Priors", expanded=True):
    enable_priors = st.toggle("Enable Adaptive Priors", value=True)
    smoothing = st.slider("Smoothing Factor (Alpha)", 0.1, 5.0, 1.0)
    
    if enable_priors:
        st.caption("Adaptive priors are active. New user data will influence future classifications.")
    else:
        st.caption("Using static distribution.")

with st.expander("Neural Network Architecture"):
    model_type = st.selectbox("Classifier Backbone", ["DNN-128", "Transformer-Tiny", "RandomForest-Large"])
    st.metric("Estimated Memory", "256 MB", delta="-12 MB")

