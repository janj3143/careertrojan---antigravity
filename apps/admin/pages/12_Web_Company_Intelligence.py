"""12 – Web Company Intelligence (ADMIN TRUTH PAGE)

RULES (ENFORCED):
- NO demo data
- NO fallback values
- Backend is the ONLY source of truth
- If required backend keys/endpoints are missing -> HARD ERROR (raise)

This page is a UI shell. All intelligence gathering must happen in the backend:
- ai_data_final company index (primary)
- EXA / Google / News integrations (secondary)
- Any scraping should be performed server-side, not in Streamlit.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Any, Dict, List

from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client
from services.admin_contracts import (
    WEB_INTEL_COMPANY_INDEX_KEYS,
    WEB_INTEL_INDUSTRY_INDEX_KEYS,
)

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Web Company Intelligence",
    page_icon="🌐",
    layout="wide",
)

require_admin()
client = get_admin_api_client(access_token=get_access_token())

st.title("🌐 Web Company Intelligence Suite")
st.caption(
    "Multi-source company research and competitive intelligence. "
    "All data is backend-sourced (ai_data_final → EXA/Google/News), no UI fallbacks."
)

refresh = st.button("🔄 Refresh", use_container_width=True)

# ----------------------------
# Strict helpers
# ----------------------------
def _require_dict(payload: Dict[str, Any], key: str) -> Dict[str, Any]:
    v = payload.get(key)
    if not isinstance(v, dict):
        raise RuntimeError(f"Backend payload missing required dict key: '{key}'")
    return v

def _require_list(payload: Dict[str, Any], key: str) -> List[Any]:
    v = payload.get(key)
    if not isinstance(v, list):
        raise RuntimeError(f"Backend payload missing required list key: '{key}'")
    return v

def _require_str(payload: Dict[str, Any], key: str) -> str:
    v = payload.get(key)
    if not isinstance(v, str) or not v.strip():
        raise RuntimeError(f"Backend payload missing required string key: '{key}'")
    return v

# ----------------------------
# Load indexes (backend truth)
# ----------------------------
company_index = get_cached(
    "_webintel_company_index",
    ttl_s=60,
    fetch=lambda: client.webintel_company_index(q="", limit=500),
    force=refresh,
)
for k in WEB_INTEL_COMPANY_INDEX_KEYS:
    if k not in company_index:
        raise RuntimeError(f"Company index missing required key: {k}")

industry_index = get_cached(
    "_webintel_industry_index",
    ttl_s=120,
    fetch=lambda: client.webintel_industry_index(q="", limit=500),
    force=refresh,
)
for k in WEB_INTEL_INDUSTRY_INDEX_KEYS:
    if k not in industry_index:
        raise RuntimeError(f"Industry index missing required key: {k}")

companies = _require_list(company_index, "companies")
industries = _require_list(industry_index, "industries")

# ----------------------------
# Top metrics (real counts)
# ----------------------------
m1, m2, m3 = st.columns(3)
m1.metric("Companies indexed", len(companies))
m2.metric("Industries indexed", len(industries))
try:
    integ = get_cached(
        "_webintel_integrations",
        ttl_s=30,
        fetch=client.webintel_integrations_status,
        force=refresh,
    )
    status = _require_str(integ, "status")
    m3.metric("Integrations status", status)
except Exception as e:
    # This section is optional: if backend doesn't support it yet, HARD ERROR per your rule.
    raise

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["🔍 Company Research", "🏭 Industry Analysis", "🎯 Competitive Intel", "🔧 Bulk Research"]
)

with tab1:
    st.subheader("🔍 Company Research")
    q = st.text_input("Search companies", value="", placeholder="Type to filter indexed companies…")
    filtered = [c for c in companies if q.strip().lower() in str(c).lower()] if q.strip() else companies

    company = st.selectbox("Company", options=filtered[:500])
    depth = st.selectbox("Research depth", ["standard", "deep", "competitive"], index=0)
    include_news = st.checkbox("Include recent news", value=True)
    include_tech = st.checkbox("Include technology stack", value=True)

    if st.button("🚀 Research Company", type="primary", use_container_width=True):
        payload = client.webintel_research_company(
            company_name=str(company),
            depth=depth,
            include_news=include_news,
            include_tech_stack=include_tech,
        )
        report = _require_dict(payload, "report")
        st.success("✅ Research complete (backend sourced)")
        st.json(report)

        # Optionally save the report (backend decides persistence)
        if st.button("💾 Save report", use_container_width=True):
            saved = client.webintel_save_report(report=report)
            _ = _require_dict(saved, "saved")
            st.success("✅ Report saved")

with tab2:
    st.subheader("🏭 Industry Analysis")
    q2 = st.text_input("Search industries", value="", placeholder="Type to filter industries…")
    inds = [i for i in industries if q2.strip().lower() in str(i).lower()] if q2.strip() else industries
    industry = st.selectbox("Industry", options=inds[:500])

    include_trends = st.checkbox("Include emerging trends", value=True)
    include_funding = st.checkbox("Include funding data (if available)", value=False)
    include_talent = st.checkbox("Include talent insights", value=False)

    if st.button("📊 Analyze Industry", type="primary", use_container_width=True):
        payload = client.webintel_analyze_industry(
            industry=str(industry),
            include_trends=include_trends,
            include_funding=include_funding,
            include_talent=include_talent,
        )
        report = _require_dict(payload, "report")
        st.success("✅ Industry analysis complete")
        st.json(report)

with tab3:
    st.subheader("🎯 Competitive Intelligence")
    primary = st.selectbox("Primary company", options=companies[:500], key="ci_primary")
    competitors = st.multiselect("Compare against", options=[c for c in companies if c != primary][:500])
    criteria = st.multiselect(
        "Criteria",
        options=["revenue", "employees", "market_position", "tech_stack", "culture", "hiring_signals", "news_velocity"],
        default=["employees", "market_position"],
    )

    if st.button("🎯 Generate Competitive Analysis", type="primary", use_container_width=True):
        payload = client.webintel_competitive_compare(
            primary_company=str(primary),
            competitors=[str(c) for c in competitors],
            criteria=[str(c) for c in criteria],
        )
        report = _require_dict(payload, "report")
        st.success("✅ Competitive analysis complete")
        st.json(report)

with tab4:
    st.subheader("🔧 Bulk Research")
    st.caption("Paste companies (one per line) or select from the indexed list. Backend executes research.")

    mode = st.radio("Input mode", ["Paste list", "Select"], horizontal=True)
    company_list: List[str] = []

    if mode == "Paste list":
        raw = st.text_area("Companies", height=160, placeholder="Company A\nCompany B\nCompany C")
        company_list = [x.strip() for x in raw.splitlines() if x.strip()]
    else:
        company_list = st.multiselect("Companies", options=companies[:500])

    opt1 = st.checkbox("Basic info", value=True)
    opt2 = st.checkbox("Tech stack", value=True)
    opt3 = st.checkbox("Recent news", value=False)
    opt4 = st.checkbox("Competitive position", value=False)

    if st.button("🚀 Start bulk research", type="primary", use_container_width=True, disabled=(len(company_list) == 0)):
        payload = client.webintel_bulk_research(
            companies=[str(c) for c in company_list],
            options={
                "basic_info": opt1,
                "tech_stack": opt2,
                "recent_news": opt3,
                "competitive_analysis": opt4,
            },
        )
        report = _require_dict(payload, "report")
        results = _require_list(report, "results")
        st.success(f"✅ Bulk research complete: {len(results)} companies")
        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

st.markdown("---")
with st.expander("📚 Saved reports", expanded=False):
    reports_payload = get_cached(
        "_webintel_reports",
        ttl_s=30,
        fetch=lambda: client.webintel_list_reports(limit=50),
        force=refresh,
    )
    reports = _require_list(reports_payload, "reports")
    if reports:
        st.dataframe(pd.DataFrame(reports), use_container_width=True, hide_index=True)
    else:
        st.info("Backend reports 0 saved intelligence reports.")