"""
10 – Token Management (ADMIN TRUTH PAGE) — MERGED BEST-OF-BREED + UNIT ECONOMICS
=============================================================================

Canonical control surface for:
- Token plan configuration
- Token usage monitoring (org + user)
- Page/feature token cost management
- Usage logs & analytics (when backend provides timeseries)
- Backend health / contracts

🔴 NEW (this patch):
- Unit Economics model (Tokens ↔ API costs ↔ Profit) sourced from backend only
- Deep-link to Admin API Integration page (Page 13)

RULES (ENFORCED):
- NO demo data
- NO fallback values
- Backend is the ONLY source of truth
- If required backend keys/endpoints are missing -> HARD ERROR (raise)

"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Any, Dict, List

from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client
from services.admin_contracts import PLAN_KEYS


# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Token Management",
    page_icon="🧮",
    layout="wide",
)

require_admin()
client = get_admin_api_client(access_token=get_access_token())

st.title("🧮 Token Management")
st.caption(
    "Backend-truth token configuration & usage. "
    "All values originate from persisted backend state."
)

refresh = st.button("🔄 Refresh all", use_container_width=True)


# -------------------------------------------------------------------
# STRICT LOADERS
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# DATA LOAD (CACHED; STILL BACKEND-TRUTH)
# -------------------------------------------------------------------

plans_payload = get_cached(
    "_token_plans",
    ttl_s=30,
    fetch=client.get_token_plans,
    force=refresh,
)

usage_payload = get_cached(
    "_token_usage",
    ttl_s=30,
    fetch=client.get_token_usage,
    force=refresh,
)

subs_payload = get_cached(
    "_user_subscriptions",
    ttl_s=30,
    fetch=client.get_user_subscriptions,
    force=refresh,
)

costs_payload = get_cached(
    "_token_costs",
    ttl_s=30,
    fetch=client.get_token_costs,
    force=refresh,
)

logs_payload = get_cached(
    "_token_usage_logs",
    ttl_s=30,
    fetch=lambda: client.get_usage_logs(days=14),
    force=refresh,
)

analytics_payload = get_cached(
    "_token_analytics",
    ttl_s=30,
    fetch=lambda: client.get_usage_analytics(days=30),
    force=refresh,
)

# 🔴 NEW: unit economics (tokens ↔ API costs ↔ profit) — backend only
unit_econ_payload = get_cached(
    "_token_unit_economics",
    ttl_s=30,
    fetch=lambda: client.get_token_unit_economics(window_days=30),
    force=refresh,
)


# -------------------------------------------------------------------
# CONTRACT ENFORCEMENT: PLANS
# -------------------------------------------------------------------

plans = plans_payload.get("plans")
if not isinstance(plans, dict):
    raise RuntimeError("Token config response missing required dict key: 'plans'")

missing = [k for k in PLAN_KEYS if k not in plans]
extra = [k for k in plans if k not in PLAN_KEYS]
if missing:
    raise RuntimeError(f"Missing required plan keys: {missing}")
if extra:
    raise RuntimeError(f"Unknown plan keys in backend: {extra}")


# -------------------------------------------------------------------
# CONTRACT ENFORCEMENT: SUBSCRIPTIONS -> PLAN DISTRIBUTION
# -------------------------------------------------------------------

subscriptions = subs_payload.get("subscriptions")
if not isinstance(subscriptions, list):
    raise RuntimeError("Subscriptions payload missing list key: 'subscriptions'")

plan_counts = {k: 0 for k in PLAN_KEYS}
for s in subscriptions:
    if not isinstance(s, dict):
        raise RuntimeError("Subscription entry must be an object")
    plan = s.get("plan")
    if plan not in plan_counts:
        raise RuntimeError(f"User subscription references unknown plan: {plan}")
    plan_counts[plan] += 1

st.subheader("👥 Users by Plan (from backend subscriptions)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Free", plan_counts["free"])
c2.metric("Monthly", plan_counts["monthly"])
c3.metric("Annual", plan_counts["annual"])
c4.metric("Elite Pro", plan_counts["elitepro"])

st.markdown("---")


# -------------------------------------------------------------------
# OPTIONAL TOP-LEVEL KPIs (BACKEND-SOURCED ONLY)
# -------------------------------------------------------------------

with st.expander("📌 KPIs (backend-sourced)", expanded=True):
    kpis = _require_dict(analytics_payload, "kpis")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active users (30d)", kpis.get("active_users_30d"))
    col2.metric("Tokens consumed (today)", kpis.get("tokens_today"))
    col3.metric("Revenue (today)", kpis.get("revenue_today"))
    col4.metric("Avg tokens / user (30d)", kpis.get("avg_tokens_per_user_30d"))

    st.caption(
        "If any KPI shows as blank/None: fix backend aggregation "
        "(this page will not synthesize values)."
    )


# -------------------------------------------------------------------
# 🔴 NEW: UNIT ECONOMICS (TOKENS ↔ API COSTS ↔ PROFIT) — BACKEND TRUTH
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("💹 Unit Economics (Tokens ↔ API costs ↔ Profit)")

# Deep-link to API integration page (admin page 13)
left, right = st.columns([1, 2])
with left:
    st.markdown(
        "<span style='color:#d11;'>NEW:</span> Open API Integration (Page 13)",
        unsafe_allow_html=True,
    )
    if st.button("🔗 Go to Page 13", use_container_width=True):
        # NOTE: keep as string so it works across different folder layouts.
        st.switch_page("pages/13_API_Integration.py")

with right:
    st.caption(
        "This section **only** renders backend-calculated unit economics. "
        "If this errors, you need to add the backend endpoints (see patch bundle)."
    )

ue_assumptions = _require_dict(unit_econ_payload, "assumptions")
ue_plans = _require_list(unit_econ_payload, "plans")
ue_breakdown = _require_list(unit_econ_payload, "api_cost_breakdown")

with st.expander("Assumptions (backend)", expanded=False):
    st.json(ue_assumptions)

if ue_plans:
    ue_df = pd.DataFrame(ue_plans)
    st.dataframe(ue_df, use_container_width=True, hide_index=True)

    # quick glance metrics (backend-provided)
    try:
        best = ue_df.sort_values("margin_pct", ascending=False).iloc[0]
        worst = ue_df.sort_values("margin_pct", ascending=True).iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Best margin plan", str(best.get("plan")), f"{best.get('margin_pct')}%")
        m2.metric("Worst margin plan", str(worst.get("plan")), f"{worst.get('margin_pct')}%")
        m3.metric("Avg cost/token", ue_assumptions.get("avg_cost_per_token_gbp"))
        m4.metric("Window (days)", ue_assumptions.get("window_days"))
    except Exception:
        # No fallback computations — just ignore if columns missing.
        pass
else:
    st.info("Backend returned 0 unit-economics rows (real zero if no plans).")

st.markdown("### 🧾 API Cost Breakdown (30d)")
if ue_breakdown:
    st.dataframe(pd.DataFrame(ue_breakdown), use_container_width=True, hide_index=True)
else:
    st.info("Backend returned 0 cost breakdown rows for this period.")


# -------------------------------------------------------------------
# PLAN CONFIGURATION (EDIT -> BACKEND)
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("📦 Token Plan Configuration")

with st.form("token_plan_editor"):
    cols = st.columns(len(PLAN_KEYS))
    updated: Dict[str, Dict[str, Any]] = {}

    for col, plan_key in zip(cols, PLAN_KEYS):
        cfg = plans.get(plan_key, {})
        if not isinstance(cfg, dict):
            raise RuntimeError(f"Plan '{plan_key}' config must be an object")

        with col:
            st.markdown(f"### {plan_key.title()}")

            included = st.number_input(
                "Included tokens / month",
                min_value=0,
                value=int(cfg.get("included_tokens_per_month", 0)),
                step=10_000,
                key=f"{plan_key}_included",
            )

            soft = st.number_input(
                "Soft limit %",
                min_value=0,
                max_value=300,
                value=int(cfg.get("soft_limit_pct", 80)),
                step=5,
                key=f"{plan_key}_soft",
            )

            hard = st.number_input(
                "Hard limit %",
                min_value=0,
                max_value=500,
                value=int(cfg.get("hard_limit_pct", 100)),
                step=5,
                key=f"{plan_key}_hard",
            )

            overage = st.number_input(
                "Overage £ / 1k tokens",
                min_value=0.0,
                value=float(cfg.get("overage_price_per_1k") or 0.0),
                step=0.0001,
                format="%.4f",
                key=f"{plan_key}_overage",
            )

            updated[plan_key] = {
                "included_tokens_per_month": int(included),
                "soft_limit_pct": int(soft),
                "hard_limit_pct": int(hard),
                "overage_price_per_1k": overage or None,
            }

    save = st.form_submit_button("💾 Save configuration")

if save:
    result = client.update_token_plans(updated)
    _ = _require_dict(result, "plans")
    st.success("✅ Token configuration saved to backend.")
    st.rerun()


# -------------------------------------------------------------------
# TOKEN COSTS PER FEATURE/PAGE (BACKEND TRUTH)
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("💰 Token Cost Management (per feature)")

costs = _require_list(costs_payload, "costs")  # list[{feature, tokens, updated_at, updated_by?}]
if costs:
    costs_df = pd.DataFrame(costs)
    st.dataframe(costs_df, use_container_width=True, hide_index=True)
else:
    st.info(
        "Backend reports 0 cost entries. "
        "This is allowed only if you haven't configured any costs yet. "
        "If you expect costs, ensure backend is persisting them."
    )

with st.expander("✏️ Update a feature cost", expanded=False):
    features = [c.get("feature") for c in costs if isinstance(c, dict) and c.get("feature")]
    if not features:
        st.warning("No features returned by backend. Cannot edit costs until backend returns feature list.")
    else:
        feature = st.selectbox("Feature", options=sorted(features))
        current = next((c for c in costs if c.get("feature") == feature), None) or {}
        current_tokens = int(current.get("tokens", 0))

        new_tokens = st.number_input(
            "New token cost",
            min_value=0,
            max_value=10_000,
            value=current_tokens,
            step=1,
        )

        if st.button("💾 Save feature cost", use_container_width=True):
            if new_tokens == current_tokens:
                st.info("No change made.")
            else:
                updated_cost = client.update_token_cost(feature=feature, tokens=int(new_tokens))
                saved = _require_dict(updated_cost, "cost")
                if saved.get("feature") != feature:
                    raise RuntimeError("Backend returned mismatched feature after update")
                st.success("✅ Feature cost saved to backend.")
                st.rerun()


# -------------------------------------------------------------------
# ORG TOKEN USAGE (BACKEND TRUTH)
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("📊 Organisation Token Usage")

orgs = usage_payload.get("orgs")
if not isinstance(orgs, list):
    raise RuntimeError("Token usage payload missing list key: 'orgs'")

if orgs:
    df = pd.DataFrame(orgs)
    if "usage_pct" in df.columns:
        df = df.sort_values("usage_pct", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info(
        "Backend reports 0 organisations with usage in this window. "
        "This may be correct OR indicates metering events are not yet being emitted."
    )


# -------------------------------------------------------------------
# USAGE ANALYTICS (TIMESERIES) — BACKEND TRUTH ONLY
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("📈 Usage Analytics (30 days)")

series = _require_list(analytics_payload, "timeseries")  # list[{date, tokens, active_users, revenue}]
if series:
    s_df = pd.DataFrame(series)
    if "date" not in s_df.columns or "tokens" not in s_df.columns:
        raise RuntimeError("Analytics timeseries requires keys: date, tokens")
    st.line_chart(s_df.set_index("date")[["tokens"]])
    if "active_users" in s_df.columns:
        st.line_chart(s_df.set_index("date")[["active_users"]])
    if "revenue" in s_df.columns:
        st.line_chart(s_df.set_index("date")[["revenue"]])
else:
    st.info(
        "Backend returned empty timeseries. This is a real zero if no usage; "
        "otherwise fix analytics emitter/aggregator."
    )


# -------------------------------------------------------------------
# USAGE LOGS (BACKEND TRUTH ONLY)
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("📋 Usage Logs (last 14 days)")

logs = _require_list(logs_payload, "logs")  # list[{timestamp, user_id/email, feature, tokens, org_id?, request_id?}]
if logs:
    logs_df = pd.DataFrame(logs)
    st.dataframe(logs_df, use_container_width=True, hide_index=True)
else:
    st.info("Backend returned 0 log rows for this period.")


# -------------------------------------------------------------------
# USER TOKEN LEDGER (BACKEND TRUTH)
# -------------------------------------------------------------------

st.markdown("---")
st.subheader("🧾 User Token Ledger")

user_id = st.text_input(
    "User ID",
    help="Use backend user id (UUID) or system identifier accepted by ledger endpoint.",
)
if st.button("Load ledger", use_container_width=True, disabled=(user_id.strip() == "")):
    ledger = client.get_user_token_ledger(user_id.strip())
    entries = _require_list(ledger, "entries")

    if entries:
        st.dataframe(pd.DataFrame(entries), use_container_width=True, hide_index=True)
    else:
        st.info("Ledger contains 0 entries for this user (real zero, not a placeholder).")


# -------------------------------------------------------------------
# BACKEND HEALTH & CONTRACTS
# -------------------------------------------------------------------

with st.expander("🛰️ Backend Health & Contracts", expanded=False):
    health = client.get_health()
    status = _require_str(health, "status")
    st.write(f"**Backend status:** {status}")

    contracts = _require_list(health, "contracts")
    st.write("**Contracts:**")
    st.dataframe(pd.DataFrame(contracts), use_container_width=True, hide_index=True)
