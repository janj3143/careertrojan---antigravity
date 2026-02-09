"""
📈 IntelliCV Admin Portal — Analytics (TRUTH VERSION)

RULES:
- NO demo / placeholder / mock / sample data
- NO local psutil fallbacks
- NO random data generation
- Backend is the single source of truth: missing keys -> st.error + st.stop
- All payloads cached ONLY as real backend responses (TTL cache)

Requires modules (admin portal):
- shared.session.require_admin
- shared.session.get_access_token
- shared.admin_cache.get_cached
- services.admin_api_client.get_admin_api_client

Backend endpoints required:
- GET /admin/analytics/overview
- GET /admin/analytics/timeseries?metric=<key>&window_days=<int>
- GET /admin/analytics/cohorts
- GET /admin/analytics/events?limit=<int>
"""

from __future__ import annotations

from typing import Any, Dict, List

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

import plotly.express as px

from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client


# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="📈 Analytics", page_icon="📈", layout="wide")



with st.sidebar.expander("🛰️ Backend ping", expanded=False):
    payload, err = _backend_try_get("/telemetry/status")
    if payload is not None:
        st.success("✅ Backend reachable")
        st.json(payload)
    else:
        st.info(f"Backend not reachable ({err})")

# -----------------------------------------------------------------------------
# Auth + client (hard guard)
# -----------------------------------------------------------------------------
admin = require_admin()
client = get_admin_api_client(access_token=get_access_token())


# -----------------------------------------------------------------------------
# Strict loaders (hard contract)
# -----------------------------------------------------------------------------
def _fetch_overview() -> Dict[str, Any]:
    payload = client.get_analytics_overview()
    if not isinstance(payload, dict):
        raise RuntimeError("Analytics overview payload must be a dict")
    return payload


def _fetch_timeseries(metric: str, window_days: int) -> Dict[str, Any]:
    payload = client.get_analytics_timeseries(metric=metric, window_days=window_days)
    if not isinstance(payload, dict):
        raise RuntimeError("Analytics timeseries payload must be a dict")
    return payload


def _fetch_cohorts() -> Dict[str, Any]:
    payload = client.get_analytics_cohorts()
    if not isinstance(payload, dict):
        raise RuntimeError("Analytics cohorts payload must be a dict")
    return payload


def _fetch_events(limit: int) -> Dict[str, Any]:
    payload = client.get_analytics_events(limit=limit)
    if not isinstance(payload, dict):
        raise RuntimeError("Analytics events payload must be a dict")
    return payload


# -----------------------------------------------------------------------------
# Controls
# -----------------------------------------------------------------------------
st.sidebar.subheader("Analytics Controls")
window_days = st.sidebar.selectbox("Time window (days)", [7, 14, 30, 60, 90], index=2)
event_limit = st.sidebar.selectbox("Recent events limit", [25, 50, 100, 200], index=1)
refresh_now = st.sidebar.button("🔄 Refresh analytics (backend)", use_container_width=True)

# Metrics you want to trend (must be supported by backend)
trend_metric = st.sidebar.selectbox(
    "Trend metric",
    ["tokens_used", "api_requests", "active_users", "uploads", "parses", "exports", "payments"],
    index=0,
)


# -----------------------------------------------------------------------------
# Cache real payloads only (TTL)
# -----------------------------------------------------------------------------
ttl_s = 30
overview = get_cached("_analytics_overview", ttl_s=ttl_s, fetch=_fetch_overview, force=refresh_now)
cohorts = get_cached("_analytics_cohorts", ttl_s=ttl_s, fetch=_fetch_cohorts, force=refresh_now)
events_payload = get_cached("_analytics_events", ttl_s=ttl_s, fetch=lambda: _fetch_events(event_limit), force=refresh_now)
timeseries = get_cached(
    f"_analytics_ts_{trend_metric}_{window_days}",
    ttl_s=ttl_s,
    fetch=lambda: _fetch_timeseries(trend_metric, window_days),
    force=refresh_now,
)

# Persist for other pages (real data only)
st.session_state["analytics_overview"] = overview
st.session_state["analytics_cohorts"] = cohorts
st.session_state["analytics_events"] = events_payload
st.session_state["analytics_timeseries"] = timeseries


# -----------------------------------------------------------------------------
# Contract checks (hard)
# -----------------------------------------------------------------------------
# Overview contract:
# {
#   "generated_at": "...",
#   "kpis": { ... },
#   "breakdowns": { ... }   (optional but recommended)
# }
for k in ("generated_at", "kpis"):
    if k not in overview:
        st.error(f"/admin/analytics/overview missing required key: '{k}'")
        st.stop()

kpis = overview["kpis"]
if not isinstance(kpis, dict):
    st.error("overview.kpis must be a dict")
    st.stop()

# Timeseries contract:
# { "metric": "...", "window_days": N, "points": [ {"date":"YYYY-MM-DD","value":123}, ... ] }
for k in ("metric", "window_days", "points"):
    if k not in timeseries:
        st.error(f"/admin/analytics/timeseries missing required key: '{k}'")
        st.stop()

points = timeseries["points"]
if not isinstance(points, list):
    st.error("timeseries.points must be a list")
    st.stop()

# Cohorts contract:
# { "generated_at": "...", "cohorts": [ { "name": "...", "count": 1, ... }, ... ] }
for k in ("generated_at", "cohorts"):
    if k not in cohorts:
        st.error(f"/admin/analytics/cohorts missing required key: '{k}'")
        st.stop()

cohort_rows = cohorts["cohorts"]
if not isinstance(cohort_rows, list):
    st.error("cohorts.cohorts must be a list")
    st.stop()

# Events contract:
# { "generated_at": "...", "events": [ ... ] }
for k in ("generated_at", "events"):
    if k not in events_payload:
        st.error(f"/admin/analytics/events missing required key: '{k}'")
        st.stop()

events = events_payload["events"]
if not isinstance(events, list):
    st.error("events_payload.events must be a list")
    st.stop()


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown(
    f"""
<div style="background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
            color:white; padding:1.6rem; border-radius:12px; margin-bottom:1.3rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15); text-align:center;">
  <h1 style="margin:0; font-size:2.25rem;">📈 Analytics</h1>
  <p style="margin:0.35rem 0 0 0; opacity:0.9; font-size:1.05rem;">
    Backend-truth analytics • Admin: {admin.display_name}
  </p>
  <p style="margin:0.25rem 0 0 0; opacity:0.75; font-size:0.95rem;">
    Overview snapshot: {overview['generated_at']}
  </p>
</div>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# KPI row (strictly real values)
# -----------------------------------------------------------------------------
st.subheader("Key KPIs (backend truth)")

# Required KPI keys (adjust to your backend contract)
required_kpi_keys = (
    "active_users_24h",
    "active_users_30d",
    "tokens_used_24h",
    "tokens_used_30d",
    "uploads_24h",
    "parses_24h",
    "exports_24h",
    "revenue_30d",
)

missing = [k for k in required_kpi_keys if k not in kpis]
if missing:
    st.error(f"overview.kpis missing required KPI keys: {missing}")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active users (24h)", int(kpis["active_users_24h"]))
c2.metric("Active users (30d)", int(kpis["active_users_30d"]))
c3.metric("Tokens used (24h)", f"{int(kpis['tokens_used_24h']):,}")
c4.metric("Tokens used (30d)", f"{int(kpis['tokens_used_30d']):,}")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Uploads (24h)", int(kpis["uploads_24h"]))
c6.metric("Parses (24h)", int(kpis["parses_24h"]))
c7.metric("Exports (24h)", int(kpis["exports_24h"]))
c8.metric("Revenue (30d)", f"£{float(kpis['revenue_30d']):,.2f}")


# -----------------------------------------------------------------------------
# Trend chart
# -----------------------------------------------------------------------------
st.subheader(f"Trend: {timeseries['metric']} (last {timeseries['window_days']} days)")

if points:
    # Validate shape
    for p in points:
        if not isinstance(p, dict) or "date" not in p or "value" not in p:
            st.error(f"Invalid timeseries point. Each point must be {{date, value}}. Got: {p}")
            st.stop()

    fig = px.line(points, x="date", y="value", markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No timeseries points returned in this window (real 0-state).")


# -----------------------------------------------------------------------------
# Cohorts (plan + funnel cohorts should be computed backend-side)
# -----------------------------------------------------------------------------
st.subheader("Cohorts (backend truth)")

if cohort_rows:
    st.dataframe(cohort_rows, use_container_width=True)
else:
    st.info("No cohorts returned by backend (real 0-state).")


# -----------------------------------------------------------------------------
# Events (audit/event log stream)
# -----------------------------------------------------------------------------
st.subheader("Recent Events (backend truth)")

if events:
    st.dataframe(events, use_container_width=True)
else:
    st.info("No events returned in this window (real 0-state).")


st.markdown("---")
st.caption("Analytics • Truth UI • Backend-driven • No demo/fallback data")
