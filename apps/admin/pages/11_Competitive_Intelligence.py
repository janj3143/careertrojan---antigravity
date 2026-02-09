""" 
11 – Competitive Intelligence (ADMIN TRUTH PAGE)
=============================================================================

Backend-truth control surface for competitive intelligence.

RULES (ENFORCED):
- NO demo data
- NO fallback values
- Backend is the ONLY source of truth
- If required backend keys/endpoints are missing -> HARD ERROR (raise)

Requires these Admin API client methods (services.admin_api_client):
- get_ci_overview()
- get_ci_competitors()
- upsert_ci_competitor(payload)
- delete_ci_competitor(competitor_id)
- get_ci_signals(days:int)
- get_ci_benchmarks()
- get_ci_tasks()
- create_ci_task(payload)
- run_ci_task(task_id)
- delete_ci_task(task_id)
- get_ci_reports(days:int)
- get_ci_report(report_id)
- get_ci_config()
- update_ci_config(payload)
- get_health()

"""

from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Any, Dict, List

from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client


# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Competitive Intelligence",
    page_icon="🧠",
    layout="wide",
)

require_admin()
client = get_admin_api_client(access_token=get_access_token())

st.title("🧠 Competitive Intelligence")
st.caption(
    "Backend-truth competitive intelligence: competitors, signals, benchmarks, tasks & reports. "
    "No synthesized values. Missing contracts raise hard errors."
)

# Convenience link to API Integration page (Page 13)
if hasattr(st, "page_link"):
    try:
        st.page_link("pages/13_API_Integration.py", label="🔗 Open API Integration (Page 13)")
    except Exception:
        # Do not fail the page for a non-critical UI link.
        pass

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

overview_payload = get_cached(
    "_ci_overview",
    ttl_s=30,
    fetch=client.get_ci_overview,
    force=refresh,
)

competitors_payload = get_cached(
    "_ci_competitors",
    ttl_s=30,
    fetch=client.get_ci_competitors,
    force=refresh,
)

signals_payload = get_cached(
    "_ci_signals_30d",
    ttl_s=30,
    fetch=lambda: client.get_ci_signals(days=30),
    force=refresh,
)

benchmarks_payload = get_cached(
    "_ci_benchmarks",
    ttl_s=30,
    fetch=client.get_ci_benchmarks,
    force=refresh,
)

tasks_payload = get_cached(
    "_ci_tasks",
    ttl_s=15,
    fetch=client.get_ci_tasks,
    force=refresh,
)

reports_payload = get_cached(
    "_ci_reports_30d",
    ttl_s=30,
    fetch=lambda: client.get_ci_reports(days=30),
    force=refresh,
)

config_payload = get_cached(
    "_ci_config",
    ttl_s=60,
    fetch=client.get_ci_config,
    force=refresh,
)


# -------------------------------------------------------------------
# OVERVIEW
# -------------------------------------------------------------------

kpis = _require_dict(overview_payload, "kpis")

with st.expander("📌 KPIs (backend-sourced)", expanded=True):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monitored competitors", kpis.get("competitor_count"))
    c2.metric("Signals (30d)", kpis.get("signals_30d"))
    c3.metric("Reports (30d)", kpis.get("reports_30d"))
    c4.metric("Last CI run", kpis.get("last_run_at"))


# -------------------------------------------------------------------
# TABS
# -------------------------------------------------------------------

t_overview, t_competitors, t_signals, t_benchmarks, t_tasks, t_reports, t_config, t_health = st.tabs(
    [
        "🧭 Overview",
        "🏢 Competitors",
        "📈 Signals",
        "🧪 Benchmarks",
        "🧰 Tasks",
        "🗂️ Reports",
        "⚙️ Config",
        "🛰️ Health",
    ]
)


# -------------------------------------------------------------------
# TAB: OVERVIEW
# -------------------------------------------------------------------

with t_overview:
    st.subheader("🧭 Overview")

    summary = _require_dict(overview_payload, "summary")

    left, right = st.columns([2, 1])
    with left:
        st.markdown("### Summary")
        st.json(summary)

    with right:
        st.markdown("### Quick actions")
        if st.button("▶️ Run CI now", use_container_width=True):
            run = client.run_ci_task(task_id="__ad_hoc__")
            job = _require_dict(run, "job")
            st.success("CI job triggered.")
            st.json(job)


# -------------------------------------------------------------------
# TAB: COMPETITORS (CRUD)
# -------------------------------------------------------------------

with t_competitors:
    st.subheader("🏢 Monitored Competitors")

    competitors = _require_list(competitors_payload, "competitors")

    if competitors:
        df = pd.DataFrame(competitors)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info(
            "Backend returned 0 competitors. This is a real zero if not configured yet. "
            "Add competitors below to begin monitoring."
        )

    st.markdown("---")
    st.markdown("### ➕ Add / Update competitor")

    with st.form("ci_competitor_upsert"):
        col1, col2, col3 = st.columns(3)

        with col1:
            competitor_id = st.text_input(
                "Competitor ID (leave blank to create)",
                help="If provided, backend will update the competitor with this ID.",
            ).strip()

            name = st.text_input("Name", placeholder="e.g., Competitor Ltd").strip()

        with col2:
            website = st.text_input("Website", placeholder="https://...").strip()
            category = st.text_input("Category", placeholder="e.g., Resume AI").strip()

        with col3:
            region = st.text_input("Region", placeholder="e.g., UK / EU").strip()
            notes = st.text_area("Notes", height=92).strip()

        submit = st.form_submit_button("💾 Save competitor")

    if submit:
        payload = {
            "id": competitor_id or None,
            "name": name,
            "website": website,
            "category": category,
            "region": region,
            "notes": notes or None,
        }
        saved = client.upsert_ci_competitor(payload)
        _ = _require_dict(saved, "competitor")
        st.success("✅ Competitor saved.")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🗑️ Delete competitor")

    ids = [c.get("id") for c in competitors if isinstance(c, dict) and c.get("id")]
    if not ids:
        st.info("No competitors available for deletion.")
    else:
        del_id = st.selectbox("Competitor ID", options=sorted(ids))
        if st.button("Delete", type="secondary", use_container_width=True):
            res = client.delete_ci_competitor(del_id)
            ok = _require_str(res, "status")
            if ok.lower() != "ok":
                raise RuntimeError(f"Backend returned non-ok delete status: {ok}")
            st.success("✅ Competitor deleted.")
            st.rerun()


# -------------------------------------------------------------------
# TAB: SIGNALS (TIMESERIES)
# -------------------------------------------------------------------

with t_signals:
    st.subheader("📈 Market Signals")

    signals = _require_list(signals_payload, "timeseries")

    if not signals:
        st.info("Backend returned empty timeseries. This is a real zero if no signals; otherwise fix CI collectors.")
    else:
        s_df = pd.DataFrame(signals)
        if "date" not in s_df.columns:
            raise RuntimeError("Signals timeseries requires key: date")

        # Render all numeric series (except date)
        numeric_cols = [c for c in s_df.columns if c != "date" and pd.api.types.is_numeric_dtype(s_df[c])]
        if not numeric_cols:
            raise RuntimeError("Signals timeseries has no numeric columns to chart")

        st.dataframe(s_df, use_container_width=True, hide_index=True)
        for col in numeric_cols:
            st.markdown(f"#### {col}")
            st.line_chart(s_df.set_index("date")[[col]])


# -------------------------------------------------------------------
# TAB: BENCHMARKS
# -------------------------------------------------------------------

with t_benchmarks:
    st.subheader("🧪 Benchmarks")

    matrix = _require_list(benchmarks_payload, "matrix")

    if not matrix:
        st.info("Backend returned 0 benchmark rows.")
    else:
        m_df = pd.DataFrame(matrix)
        st.dataframe(m_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------
# TAB: TASKS
# -------------------------------------------------------------------

with t_tasks:
    st.subheader("🧰 CI Tasks")

    tasks = _require_list(tasks_payload, "tasks")

    if tasks:
        t_df = pd.DataFrame(tasks)
        st.dataframe(t_df, use_container_width=True, hide_index=True)
    else:
        st.info("Backend returned 0 tasks. Create tasks to automate monitoring.")

    st.markdown("---")
    st.markdown("### ➕ Create task")

    with st.form("ci_task_create"):
        col1, col2 = st.columns(2)
        with col1:
            task_name = st.text_input("Task name", placeholder="e.g., Daily competitor scrape").strip()
            task_kind = st.text_input("Task kind", placeholder="e.g., scrape, benchmark, report").strip()
        with col2:
            schedule = st.text_input(
                "Schedule (cron / rrule / backend format)",
                placeholder="e.g., 0 6 * * *",
                help="Backend defines schedule format; this page will not transform it.",
            ).strip()
            enabled = st.checkbox("Enabled", value=True)

        task_payload = st.text_area(
            "Task payload (JSON)",
            placeholder='{"competitor_ids": ["..."], "sources": ["careers", "pricing"]}',
            height=120,
        ).strip()

        create = st.form_submit_button("Create")

    if create:
        if not task_payload:
            raise RuntimeError("Task payload JSON is required (backend will validate).")
        created = client.create_ci_task(
            {
                "name": task_name,
                "kind": task_kind,
                "schedule": schedule,
                "enabled": bool(enabled),
                "payload_json": task_payload,
            }
        )
        _ = _require_dict(created, "task")
        st.success("✅ Task created.")
        st.rerun()

    st.markdown("---")
    st.markdown("### ▶️ Run / 🗑️ Delete")

    ids = [t.get("id") for t in tasks if isinstance(t, dict) and t.get("id")]
    if ids:
        selected = st.selectbox("Task", options=sorted(ids))
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Run task", use_container_width=True):
                run = client.run_ci_task(selected)
                _ = _require_dict(run, "job")
                st.success("Task triggered.")
                st.rerun()
        with c2:
            if st.button("Delete task", use_container_width=True, type="secondary"):
                res = client.delete_ci_task(selected)
                ok = _require_str(res, "status")
                if ok.lower() != "ok":
                    raise RuntimeError(f"Backend returned non-ok delete status: {ok}")
                st.success("Task deleted.")
                st.rerun()
    else:
        st.info("No tasks available.")


# -------------------------------------------------------------------
# TAB: REPORTS
# -------------------------------------------------------------------

with t_reports:
    st.subheader("🗂️ Reports")

    reports = _require_list(reports_payload, "reports")

    if reports:
        r_df = pd.DataFrame(reports)
        st.dataframe(r_df, use_container_width=True, hide_index=True)

        report_ids = [r.get("id") for r in reports if isinstance(r, dict) and r.get("id")]
        if report_ids:
            selected = st.selectbox("Open report", options=sorted(report_ids))
            if st.button("Load report", use_container_width=True):
                report = client.get_ci_report(selected)
                doc = _require_dict(report, "report")
                st.markdown("### Report")
                st.json(doc)
    else:
        st.info("Backend returned 0 reports for this period.")


# -------------------------------------------------------------------
# TAB: CONFIG
# -------------------------------------------------------------------

with t_config:
    st.subheader("⚙️ Competitive Intelligence Config")

    cfg = _require_dict(config_payload, "config")

    st.markdown("### Current config (backend)")
    st.json(cfg)

    st.markdown("---")
    st.markdown("### Update config")

    with st.form("ci_config_update"):
        cfg_json = st.text_area(
            "Config JSON",
            value=str(cfg),
            height=200,
            help="Paste JSON object. Backend validates and persists.",
        ).strip()
        save_cfg = st.form_submit_button("💾 Save config")

    if save_cfg:
        if not cfg_json:
            raise RuntimeError("Config JSON is required")
        res = client.update_ci_config({"config_json": cfg_json})
        _ = _require_dict(res, "config")
        st.success("✅ Config saved.")
        st.rerun()


# -------------------------------------------------------------------
# TAB: HEALTH
# -------------------------------------------------------------------

with t_health:
    st.subheader("🛰️ Backend Health & Contracts")

    health = client.get_health()
    status = _require_str(health, "status")
    st.write(f"**Backend status:** {status}")

    contracts = _require_list(health, "contracts")
    st.dataframe(pd.DataFrame(contracts), use_container_width=True, hide_index=True)
