"""
=============================================================================
IntelliCV Admin Portal - AI Content Generator Suite (Page 09)
=============================================================================

This is the **full-hit** Page 09 implementation:

- Uses centralized paths from shared/config.py
- Real-time indexing of ai_data_final (skills/industries/locations)
- Calls FastAPI backend for AI generation (OpenAI/Perplexity)
- Keeps UI fully functional in Streamlit
- NO fake counters, NO dummy corpus data

Backend expected (included in this package):
- `backend/app/main.py` running on http://localhost:8000

"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

# =============================================================================
# BACKEND-FIRST SWITCH (lockstep) — falls back to local execution when backend is unavailable
# =============================================================================
try:
    from portal_bridge.python.intellicv_api_client import IntelliCVApiClient  # preferred
except Exception:  # pragma: no cover
    IntelliCVApiClient = None  # type: ignore

def _get_api_client():
    return IntelliCVApiClient() if IntelliCVApiClient else None

def _backend_try_get(path: str, params: dict | None = None):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.get(path, params=params), None
    except Exception as e:
        return None, str(e)

def _backend_try_post(path: str, payload: dict):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.post(path, payload), None
    except Exception as e:
        return None, str(e)


# Shared configuration (single source of truth for paths)
from shared.config import AI_DATA_DIR

BACKEND_URL = os.getenv("INTELLICV_BACKEND_URL", "http://localhost:8000")
# Prefer the unified portal bridge base URL if set (lockstep), else fall back to INTELLICV_BACKEND_URL
BACKEND_URL = os.getenv("INTELLICV_API_BASE_URL", BACKEND_URL)



# -----------------------------------------------------------------------------
# Authentication guard (admin portal standard)
# -----------------------------------------------------------------------------
def check_authentication() -> None:
    if not st.session_state.get("admin_authenticated", False):
        st.error("🔒 ADMIN AUTHENTICATION REQUIRED")
        st.warning("Login through the main admin portal to access this module.")
        if st.button("🏠 Return to Main Portal", type="primary"):
            st.switch_page("main.py")
        st.stop()


check_authentication()


# -----------------------------------------------------------------------------
# Backend client
# -----------------------------------------------------------------------------
class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self) -> dict:
        return requests.get(f"{self.base_url}/health", timeout=10).json()

    def index(self, max_files_per_category: int | None = None) -> dict:
        params = {}
        if max_files_per_category is not None:
            params["max_files_per_category"] = max_files_per_category
        r = requests.get(f"{self.base_url}/ai-data/index", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def generate_summary(self, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/ai-content/summary", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def generate_star_bullets(self, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/ai-content/star-bullets", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def optimize_ats(self, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/ai-content/ats-optimize", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()

    def cover_letter(self, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}/ai-content/cover-letter", json=payload, timeout=90)
        r.raise_for_status()
        return r.json()


@st.cache_resource
def get_backend() -> BackendClient:
    return BackendClient(BACKEND_URL)


# -----------------------------------------------------------------------------
# Real-time ai_data_final reader (for UI visibility)
# -----------------------------------------------------------------------------
@dataclass
class LocalIndex:
    total_files: int
    categories: dict
    unique_skills: int
    unique_industries: int
    unique_locations: int
    top_skills: dict
    top_industries: dict
    top_locations: dict
    last_indexed: str


def _safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def render_section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


def render() -> None:
    st.set_page_config(page_title="Admin | AI Content Generator", layout="wide")

    render_section_header(
        "🤖 AI Content Generator Suite",
        "GPT-4 / Perplexity generation + live ai_data_final indexing. No dummy data.",
    )

    backend = get_backend()

    # Top status row
    colA, colB, colC, colD = st.columns(4)
    with colA:
        st.metric("📁 AI_DATA_DIR", str(AI_DATA_DIR))
    with colB:
        st.metric("🌐 Backend", BACKEND_URL)
    with colC:
        ok = "unknown"
        try:
            ok = backend.health().get("status", "unknown")
        except Exception as e:
            ok = f"error: {str(e)[:60]}"
        st.metric("🧪 Health", ok)
    with colD:
        st.metric("⏰ Now", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "⚡ Real-Time AI Data",
            "📝 Professional Summary",
            "⭐ STAR Bullets",
            "🎯 ATS Optimization",
            "📄 Cover Letter",
            "🔧 Bulk Processing",
            "➕ Add New User",
        ]
    )

    with tab1:
        st.markdown("### ⚡ Real-Time AI Data (from backend indexer)")
        st.info("Indexes your real ai_data_final folder to build skill/industry/location counters.")

        c1, c2, c3 = st.columns(3)
        with c1:
            max_files = st.number_input(
                "Max files per category (speed cap)", min_value=10, max_value=5000, value=200, step=10
            )
        with c2:
            if st.button("🔄 Refresh Index", type="primary"):
                st.session_state["_force_reindex"] = time.time()
        with c3:
            st.caption("Tip: set INTELLICV_BACKEND_URL if backend is remote.")

        # fetch
        try:
            _ = st.session_state.get("_force_reindex")
            data = backend.index(max_files_per_category=int(max_files))
            idx = LocalIndex(**data)
        except Exception as e:
            st.error(f"Failed to index ai_data_final via backend: {e}")
            st.stop()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📄 Total JSON files", f"{idx.total_files:,}")
        m2.metric("🛠️ Unique skills", f"{idx.unique_skills:,}")
        m3.metric("🏭 Unique industries", f"{idx.unique_industries:,}")
        m4.metric("📍 Unique locations", f"{idx.unique_locations:,}")

        st.caption(
            "**Meaning of unique counts**: distinct strings observed in the corpus (e.g., distinct skill labels), not people/profiles."
        )
        st.caption(f"Last indexed: {idx.last_indexed}")

        dtab1, dtab2, dtab3 = st.tabs(["🔧 Skills", "🏭 Industries", "📍 Locations"])

        with dtab1:
            df = pd.DataFrame(list(idx.top_skills.items()), columns=["Skill", "Frequency"])
            st.dataframe(df, use_container_width=True, height=420)

        with dtab2:
            df = pd.DataFrame(list(idx.top_industries.items()), columns=["Industry", "Count"])
            st.dataframe(df, use_container_width=True, height=420)

        with dtab3:
            df = pd.DataFrame(list(idx.top_locations.items()), columns=["Location", "Count"])
            st.dataframe(df, use_container_width=True, height=420)

    with tab2:
        st.subheader("📝 AI Professional Summary")

        col1, col2 = st.columns(2)
        with col1:
            target_role = st.text_input("Target Role", value="Software Engineer")
            target_industry = st.selectbox(
                "Industry", ["technology", "sales", "marketing", "finance", "management", "healthcare"]
            )
            experience = st.text_input("Experience", value="Mid-Level (3-7 years)")
        with col2:
            name = st.text_input("Candidate Name", value="")
            skills = st.text_area("Skills (comma-separated)", value="")
            achievements = st.text_area("Achievements", value="")

        if st.button("🚀 Generate Summary", type="primary"):
            payload = {
                "target_role": target_role,
                "target_industry": target_industry,
                "experience": experience,
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "achievements": achievements,
            }
            with st.spinner("Generating..."):
                out = backend.generate_summary(payload)
            st.success(f"✅ Generated via {out.get('provider')} ({out.get('model')})")
            st.text_area("Summary", value=out.get("text", ""), height=180)

    with tab3:
        st.subheader("⭐ STAR Method Bullets")

        col1, col2 = st.columns(2)
        with col1:
            industry = st.selectbox(
                "Industry", ["technology", "sales", "marketing", "finance", "management", "healthcare"], key="star_ind"
            )
            role_level = st.selectbox("Level", ["entry", "mid", "senior", "executive"], key="star_lvl")
        with col2:
            basic_desc = st.text_area("Basic job description", height=140)

        if st.button("⭐ Generate STAR Bullets", type="primary"):
            if not basic_desc.strip():
                st.error("Please enter a description.")
            else:
                payload = {"basic_description": basic_desc, "target_industry": industry, "role_level": role_level}
                with st.spinner("Generating..."):
                    out = backend.generate_star_bullets(payload)
                st.success(f"✅ Generated via {out.get('provider')} ({out.get('model')})")
                st.text_area("Bullets", value=out.get("text", ""), height=220)

    with tab4:
        st.subheader("🎯 ATS Optimization")

        col1, col2 = st.columns(2)
        with col1:
            target_role = st.text_input("Target role", key="ats_role")
            content = st.text_area("Content to optimize", height=240, key="ats_content")
            kws = st.text_input("Explicit keywords (comma-separated)", value="", key="ats_kw")
        with col2:
            st.info("Uses real corpus trending skills as optional context and blends explicit keywords naturally.")

        if st.button("🎯 Optimize", type="primary"):
            payload = {
                "target_role": target_role or "(unspecified)",
                "content": content,
                "keywords": [k.strip() for k in kws.split(",") if k.strip()] or None,
            }
            with st.spinner("Optimizing..."):
                out = backend.optimize_ats(payload)
            st.success(f"✅ Optimized via {out.get('provider')} ({out.get('model')})")
            st.text_area("ATS-Optimized", value=out.get("text", ""), height=260)

    with tab5:
        st.subheader("📄 Cover Letter")

        col1, col2 = st.columns(2)
        with col1:
            candidate_name = st.text_input("Candidate name", key="cl_name")
            company_name = st.text_input("Company name", key="cl_company")
            position_title = st.text_input("Position title", key="cl_position")
            skills = st.text_area("Skills (comma-separated)", key="cl_skills")
        with col2:
            experience = st.text_input("Experience", value="5 years", key="cl_exp")
            tone = st.selectbox("Tone", ["Professional", "Confident", "Warm", "Direct"], key="cl_tone")
            job_desc = st.text_area("Job description", height=160, key="cl_jd")

        if st.button("📄 Generate Cover Letter", type="primary"):
            payload = {
                "candidate_name": candidate_name or "Candidate",
                "company_name": company_name,
                "position_title": position_title,
                "experience": experience,
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "job_description": job_desc,
                "tone": tone,
            }
            with st.spinner("Generating..."):
                out = backend.cover_letter(payload)
            st.success(f"✅ Generated via {out.get('provider')} ({out.get('model')})")
            st.text_area("Cover letter", value=out.get("text", ""), height=320)

    with tab6:
        st.subheader("🔧 Bulk Processing")

        st.info("Uploads JSON payloads and runs one of the generators for each file. (No simulations.)")

        processing_type = st.selectbox(
            "Processing Type",
            ["Professional Summaries", "STAR Bullets", "ATS Optimization", "Cover Letters"],
        )

        uploaded = st.file_uploader("Upload JSON files", type=["json"], accept_multiple_files=True)
        if uploaded and st.button("🚀 Run Bulk", type="primary"):
            results = []
            for f in uploaded:
                try:
                    payload = json.loads(f.getvalue().decode("utf-8"))
                    if processing_type == "Professional Summaries":
                        out = backend.generate_summary(payload)
                    elif processing_type == "STAR Bullets":
                        out = backend.generate_star_bullets(payload)
                    elif processing_type == "ATS Optimization":
                        out = backend.optimize_ats(payload)
                    else:
                        out = backend.cover_letter(payload)
                    results.append({"file": f.name, "status": "✅", "provider": out.get("provider"), "chars": len(out.get("text", ""))})
                except Exception as e:
                    results.append({"file": f.name, "status": "❌", "error": str(e)[:120]})
            st.dataframe(pd.DataFrame(results), use_container_width=True)

    with tab7:
        st.subheader("➕ Add New User")
        st.warning("This writes REAL data into AI_DATA_DIR. Ensure you comply with data handling policies.")

        with st.form("add_user"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full name*")
                email = st.text_input("Email*")
                location = st.text_input("Location*")
                job_title = st.text_input("Current job title*")
            with col2:
                industry = st.text_input("Industry (comma-separated)*")
                skills = st.text_area("Skills (comma-separated)*", height=90)
                experience = st.text_area("Experience*", height=90)

            submit = st.form_submit_button("💾 Save")
            if submit:
                if not all([full_name.strip(), email.strip(), location.strip(), job_title.strip(), skills.strip(), experience.strip(), industry.strip()]):
                    st.error("All * fields required.")
                else:
                    normalized_dir = AI_DATA_DIR / "normalized"
                    normalized_dir.mkdir(parents=True, exist_ok=True)
                    payload = {
                        "full_name": full_name.strip(),
                        "email": email.strip(),
                        "location": location.strip(),
                        "job_title": job_title.strip(),
                        "industries": [i.strip() for i in industry.split(",") if i.strip()],
                        "skills": [s.strip() for s in skills.split(",") if s.strip()],
                        "experience": experience.strip(),
                        "added_via": "admin_portal_page09",
                        "added_date": datetime.utcnow().isoformat() + "Z",
                    }
                    filename = f"manual_entry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{full_name.replace(' ', '_').lower()}.json"
                    (normalized_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
                    st.success(f"Saved: {filename}")
                    st.info("Now click 'Refresh Index' in the Real-Time AI Data tab to see it reflected.")


if __name__ == "__main__":
    render()
