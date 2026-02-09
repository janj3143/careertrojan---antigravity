"""
🏠 IntelliCV-AI Admin Portal Home (Truth UI, centralised, backend-driven)

RULES:
- NO demo / placeholder values
- NO local psutil fallbacks
- NO local filesystem reads
- Backend is source of truth; missing keys -> hard stop (st.error + st.stop)

Requires modules (admin portal):
- shared.session.require_admin
- shared.session.get_access_token
- shared.admin_cache.get_cached
- services.admin_api_client.get_admin_api_client
- services.admin_contracts.PLAN_KEYS

Backend endpoints:
- GET /admin/dashboard/snapshot
- GET /admin/tokens/config
- GET /admin/tokens/usage
- GET /admin/user_subscriptions
"""

from __future__ import annotations

import datetime
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


from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client
from services.admin_contracts import PLAN_KEYS


# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(page_title="IntelliCV Admin Portal", page_icon="🛡️", layout="wide")


# -----------------------------------------------------------------------------
# Auth (hard guard)
# -----------------------------------------------------------------------------
admin = require_admin()
client = get_admin_api_client(access_token=get_access_token())


# -----------------------------------------------------------------------------
# Strict backend loaders (hard contract)
# -----------------------------------------------------------------------------
def _fetch_snapshot() -> dict:
    payload = client.get_dashboard_snapshot()
    if not isinstance(payload, dict):
        raise RuntimeError("Dashboard snapshot payload must be a dict")
    return payload


def _fetch_token_plans() -> dict:
    payload = client.get_token_plans()
    if not isinstance(payload, dict):
        raise RuntimeError("Token config payload must be a dict")
    plans = payload.get("plans")
    if not isinstance(plans, dict):
        raise RuntimeError("Token config payload must contain dict key: 'plans'")
    return payload


def _fetch_token_usage() -> dict:
    payload = client.get_token_usage()
    if not isinstance(payload, dict):
        raise RuntimeError("Token usage payload must be a dict")
    orgs = payload.get("orgs")
    if not isinstance(orgs, list):
        raise RuntimeError("Token usage payload must contain list key: 'orgs'")
    return payload


def _fetch_subscriptions() -> dict:
    payload = client.get_user_subscriptions()
    if not isinstance(payload, dict):
        raise RuntimeError("Subscriptions payload must be a dict")
    subs = payload.get("subscriptions")
    if not isinstance(subs, list):
        raise RuntimeError("Subscriptions payload must contain list key: 'subscriptions'")
    return payload


# -----------------------------------------------------------------------------
# Cache real payloads only (session_state TTL cache; NOT fabricated)
# -----------------------------------------------------------------------------
refresh = st.sidebar.button("🔄 Refresh dashboard (backend)", use_container_width=True)

ttl_s = 30
snapshot = get_cached("_home_snapshot", ttl_s=ttl_s, fetch=_fetch_snapshot, force=refresh)
token_plans_payload = get_cached("_home_token_plans", ttl_s=ttl_s, fetch=_fetch_token_plans, force=refresh)
token_usage_payload = get_cached("_home_token_usage", ttl_s=ttl_s, fetch=_fetch_token_usage, force=refresh)
subs_payload = get_cached("_home_subscriptions", ttl_s=ttl_s, fetch=_fetch_subscriptions, force=refresh)

# Persist for other admin pages to reuse (REAL data only)
st.session_state["admin_snapshot"] = snapshot
st.session_state["token_plans_payload"] = token_plans_payload
st.session_state["token_usage_payload"] = token_usage_payload
st.session_state["subscriptions_payload"] = subs_payload


# -----------------------------------------------------------------------------
# Contract checks (hard)
# -----------------------------------------------------------------------------
# Snapshot must contain these blocks
required_snapshot_keys = ("system", "tokens", "activity", "data_overview")
for key in required_snapshot_keys:
    if key not in snapshot:
        st.error(f"Dashboard snapshot missing required key: '{key}'")
        st.stop()

sys_block = snapshot["system"]
tok_block = snapshot["tokens"]
activity = snapshot["activity"]
overview = snapshot["data_overview"]

if not isinstance(sys_block, dict):
    st.error("snapshot.system must be a dict")
    st.stop()
if not isinstance(tok_block, dict):
    st.error("snapshot.tokens must be a dict")
    st.stop()
if not isinstance(activity, list):
    st.error("snapshot.activity must be a list")
    st.stop()
if not isinstance(overview, dict):
    st.error("snapshot.data_overview must be a dict")
    st.stop()

# Require token plan keys in snapshot.tokens.by_plan
by_plan = tok_block.get("by_plan")
if not isinstance(by_plan, dict):
    st.error("snapshot.tokens.by_plan must be a dict")
    st.stop()

missing_plan_keys = [k for k in PLAN_KEYS if k not in by_plan]
extra_plan_keys = [k for k in by_plan.keys() if k not in PLAN_KEYS]
if missing_plan_keys or extra_plan_keys:
    st.error(f"Plan key mismatch. Missing: {missing_plan_keys} | Extra: {extra_plan_keys}")
    st.stop()


# -----------------------------------------------------------------------------
# Styling
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 1.25rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '⬢⬡⬢⬡⬢\\A⬡⬢⬡⬢⬡\\A⬢⬡⬢⬡⬢';
    white-space: pre;
    position: absolute;
    top: 50%;
    right: 20px;
    transform: translateY(-50%);
    opacity: 0.15;
    z-index: 1;
    font-size: 60px;
    line-height: 0.8;
    color: white;
}
.main-header > * { position: relative; z-index: 2; }
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Render
# -----------------------------------------------------------------------------
now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

st.markdown(
    f"""
<div class="main-header">
  <h1 style="color:white;margin:0;font-size:2.5rem;">🛡️ IntelliCV-AI Admin Portal</h1>
  <p style="color:white;margin:0.5rem 0 0 0;opacity:0.9;font-size:1.15rem;">
    Truth dashboard • Centralised wiring • Backend-driven
  </p>
  <p style="color:white;margin:0.4rem 0 0 0;opacity:0.8;font-size:1rem;">
    Welcome back, {admin.display_name} • {now_str}
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# System metrics (must be provided by backend)
st.subheader("📊 System Status (backend truth)")

required_sys_keys = ("cpu_percent", "memory_percent", "jobs_in_queue", "parsers_online", "ai_status")
for k in required_sys_keys:
    if k not in sys_block:
        st.error(f"snapshot.system missing '{k}'")
        st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("CPU", f"{float(sys_block['cpu_percent']):.1f}%")
c2.metric("Memory", f"{float(sys_block['memory_percent']):.1f}%")
c3.metric("Jobs in queue", int(sys_block["jobs_in_queue"]))
c4.metric("Parsers online", int(sys_block["parsers_online"]))
c5.metric("AI status", str(sys_block["ai_status"]).capitalize())

# Tokens overview
st.subheader("🧮 Tokens & Plans (backend truth)")

required_tok_keys = ("total_used_24h", "total_used_30d", "by_plan", "budget_alerts")
for k in required_tok_keys:
    if k not in tok_block:
        st.error(f"snapshot.tokens missing '{k}'")
        st.stop()

t1, t2, t3, t4, t5, t6 = st.columns(6)
t1.metric("Tokens (24h)", f"{int(tok_block['total_used_24h']):,}")
t2.metric("Tokens (30d)", f"{int(tok_block['total_used_30d']):,}")
t3.metric("Free", f"{int(by_plan['free']):,}")
t4.metric("Monthly", f"{int(by_plan['monthly']):,}")
t5.metric("Annual", f"{int(by_plan['annual']):,}")
t6.metric("Elite Pro", f"{int(by_plan['elitepro']):,}")

# Subscription distribution (proof of linkage to Registration/Payment truth)
subscriptions = subs_payload.get("subscriptions")
if not isinstance(subscriptions, list):
    st.error("Subscriptions payload missing list 'subscriptions'")
    st.stop()

counts = {k: 0 for k in PLAN_KEYS}
for s in subscriptions:
    plan = (s or {}).get("plan")
    if plan not in counts:
        st.error(f"Unknown subscription plan key from backend: {plan}")
        st.stop()
    counts[plan] += 1

st.markdown("**👥 Users by Plan (from subscriptions store)**")
u1, u2, u3, u4 = st.columns(4)
u1.metric("Free users", counts["free"])
u2.metric("Monthly users", counts["monthly"])
u3.metric("Annual users", counts["annual"])
u4.metric("Elite Pro users", counts["elitepro"])

# Budget alerts
alerts = tok_block.get("budget_alerts")
if not isinstance(alerts, list):
    st.error("snapshot.tokens.budget_alerts must be a list")
    st.stop()

if alerts:
    st.markdown("**⚠️ Budget Alerts**")
    for a in alerts:
        org = a.get("org")
        plan = a.get("plan")
        pct = a.get("usage_pct")
        if org is None or plan is None or pct is None:
            st.error(f"Budget alert missing required fields: {a}")
            st.stop()
        st.write(f"- `{org}` on `{plan}` at **{pct}%**")
else:
    st.info("No budget alerts in the current reporting window (real 0 state).")

# Quick actions
st.subheader("🚀 Quick Actions")

qa1, qa2, qa3, qa4 = st.columns(4)
with qa1:
    if st.button("🔧 Service Monitor", use_container_width=True):
        st.switch_page("pages/01_Service_Status_Monitor.py")
with qa2:
    if st.button("👥 User Management", use_container_width=True):
        st.switch_page("pages/03_User_Management.py")
with qa3:
    if st.button("🧩 Data Parser", use_container_width=True):
        st.switch_page("pages/06_Complete_Data_Parser.py")
with qa4:
    if st.button("🧮 Token Management", use_container_width=True):
        st.switch_page("pages/10_Token_Management.py")

# Activity + Data overview
left, right = st.columns([2, 1])

with left:
    st.subheader("📈 Recent Activity (backend truth)")
    if activity:
        st.dataframe(activity[:50], use_container_width=True)
    else:
        st.info("No activity in the current window (real 0 state).")

with right:
    st.subheader("📂 Data Overview (backend truth)")
    if overview:
        for k in sorted(overview.keys()):
            st.metric(k, f"{int(overview[k]):,}")
    else:
        st.info("No data overview keys returned (real 0 state).")

st.markdown("---")
st.caption("IntelliCV Admin Portal • Truth UI • Centralised wiring • Backend-driven")
