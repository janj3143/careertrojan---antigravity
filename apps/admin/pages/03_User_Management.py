
"""
=============================================================================
IntelliCV Admin Portal — 03 User Management (Truth-only)
=============================================================================

This page is intentionally "thin UI":
- All live data comes from the backend (FastAPI) OR local registration directory if configured.
- No fake metrics, no hard-coded demo users.

What you get:
- User list (search/filter/paginate)
- User detail panel
- Admin actions (role change, deactivate/reactivate, invalidate sessions, reset password, MFA reset)
- Sync tools (trigger user sync, trigger parser run)
- Visibility panels (backend health + data source readiness + file-based registrations)

Environment variables:
- ADMIN_API_BASE_URL  (e.g. http://localhost:8000)
- ADMIN_API_TOKEN     (optional bearer token)
- USER_REG_DIR        (optional local folder path for JSON registrations)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
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


try:
    from services.admin_api_client import AdminFastAPIClient
except Exception:
    AdminFastAPIClient = None  # type: ignore


# -------------------------
# Session helpers
# -------------------------
API_CACHE_TTL = 60
CACHE_KEYS = {
    "dashboard": ("_um_dashboard", "_um_dashboard_ts", 60),
    "health": ("_um_health", "_um_health_ts", 45),
    "activity": ("_um_activity", "_um_activity_ts", 45),
    "sources": ("_um_sources", "_um_sources_ts", 90),
    "user_metrics": ("_um_user_metrics", "_um_user_metrics_ts", 90),
    "user_security": ("_um_user_security", "_um_user_security_ts", 90),
    "subs": ("_um_subs", "_um_subs_ts", 120),
}

def check_authentication() -> bool:
    return bool(st.session_state.get("admin_authenticated", False))

def get_client():
    if AdminFastAPIClient is None:
        return None
    client = st.session_state.get("_admin_api_client_v1")
    if client is None:
        st.session_state["_admin_api_client_v1"] = AdminFastAPIClient()
        client = st.session_state["_admin_api_client_v1"]
    return client

def _get_cached(cache_key: str, ts_key: str, ttl: int, fetcher, force_refresh: bool = False):
    if force_refresh:
        st.session_state.pop(cache_key, None)
        st.session_state.pop(ts_key, None)

    payload = st.session_state.get(cache_key)
    ts = st.session_state.get(ts_key)
    if payload is not None and ts is not None:
        if (datetime.now() - ts).total_seconds() < ttl:
            return payload

    client = get_client()
    if not client:
        return payload if payload is not None else {}

    ok, status, data, err = fetcher(client)
    # truth-only: if endpoint missing, return empty, but show a warning once
    if not ok:
        st.session_state.setdefault("_um_errors", [])
        st.session_state["_um_errors"].append({"at": datetime.now().isoformat(), "status": status, "err": err})
        return {}
    st.session_state[cache_key] = data or {}
    st.session_state[ts_key] = datetime.now()
    return data or {}

def format_relative(ts: Optional[str]) -> str:
    if not ts:
        return "N/A"
    try:
        now = datetime.now()
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        delta = now - dt
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours:
            return f"{hours}h ago"
        mins = delta.seconds // 60
        if mins:
            return f"{mins}m ago"
        return "Just now"
    except Exception:
        return str(ts)

# -------------------------
# Backend snapshot panels
# -------------------------
def backend_status_panel():
    st.subheader("🛰️ Backend & FastAPI Health")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("🔄 Refresh", use_container_width=True):
            for k, (ck, tk, _) in CACHE_KEYS.items():
                st.session_state.pop(ck, None)
                st.session_state.pop(tk, None)
            st.rerun()

    dashboard = _get_cached(*CACHE_KEYS["dashboard"], fetcher=lambda c: c.get_dashboard_snapshot())
    health = _get_cached(*CACHE_KEYS["health"], fetcher=lambda c: c.get_system_health())
    activity = _get_cached(*CACHE_KEYS["activity"], fetcher=lambda c: c.get_system_activity())
    sources = _get_cached(*CACHE_KEYS["sources"], fetcher=lambda c: c.get_user_data_sources())

    with c2:
        st.caption(f"Health updated {format_relative(health.get('updated_at') if isinstance(health, dict) else None)}")
        st.caption(f"Data sources scanned {format_relative(sources.get('last_scan') if isinstance(sources, dict) else None)}")

    system = (dashboard.get("system") or {}) if isinstance(dashboard, dict) else {}
    tokens = (dashboard.get("tokens") or {}) if isinstance(dashboard, dict) else {}
    services = system.get("services") or (health.get("services") if isinstance(health, dict) else {}) or {}

    cpu = (health.get("cpu_pct") if isinstance(health, dict) else None) or system.get("cpu_percent") or 0.0
    mem = (health.get("memory_pct") if isinstance(health, dict) else None) or system.get("memory_percent") or 0.0
    jobs = system.get("jobs_in_queue", 0)
    parsers = system.get("parsers_online", 0)
    used_30d = tokens.get("total_used_30d", 0)
    used_24h = tokens.get("total_used_24h", 0)

    cols = st.columns(4)
    cols[0].metric("CPU", f"{float(cpu):.1f}%")
    cols[1].metric("Memory", f"{float(mem):.1f}%")
    cols[2].metric("Jobs in Queue", f"{jobs:,}", f"{parsers} parsers")
    cols[3].metric("Tokens (30d)", f"{used_30d:,}", f"{used_24h:,}/24h")

    if services:
        running = sum(1 for s in services.values() if s == "running")
        st.caption(f"Services online: {running}/{len(services)}")

    # Source table
    src_list = (sources.get("sources") or []) if isinstance(sources, dict) else []
    if src_list:
        with st.expander("🔌 Data Sources", expanded=False):
            st.dataframe(pd.DataFrame(src_list), use_container_width=True)

    # Activity table
    events = (activity.get("events") or []) if isinstance(activity, dict) else []
    if events:
        with st.expander("📝 Recent Activity", expanded=False):
            st.dataframe(pd.DataFrame(events).head(20), use_container_width=True)

# -------------------------
# Local registration directory (optional, real files)
# -------------------------
def load_local_registrations(reg_dir: Path, limit: int = 200) -> pd.DataFrame:
    if not reg_dir.exists():
        return pd.DataFrame()
    rows: List[Dict[str, Any]] = []
    files = sorted(reg_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            rows.append({
                "user_id": data.get("id") or fp.stem,
                "email": data.get("email"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "role": data.get("role") or "user",
                "status": data.get("status") or "active",
                "created_at": data.get("created_at") or datetime.fromtimestamp(fp.stat().st_mtime).isoformat(),
                "source": "local_json",
                "file": fp.name,
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

# -------------------------
# Users UI
# -------------------------
def user_list_panel():
    st.subheader("👥 Users")

    client = get_client()
    if not client:
        st.warning("Admin API client not available (services/admin_api_client.py missing).")
        return None, None

    filters = st.columns([2, 1, 1, 1])
    q = filters[0].text_input("Search (name/email/id)", placeholder="e.g. jan@, Holly, user_123")
    role = filters[1].selectbox("Role", ["all", "user", "mentor", "admin"], index=0)
    status = filters[2].selectbox("Status", ["all", "active", "disabled", "pending"], index=0)
    limit = filters[3].selectbox("Page size", [25, 50, 100], index=1)

    pag = st.columns([1, 1, 2])
    if "um_offset" not in st.session_state:
        st.session_state.um_offset = 0
    if pag[0].button("⬅️ Prev"):
        st.session_state.um_offset = max(0, st.session_state.um_offset - limit)
        st.rerun()
    if pag[1].button("Next ➡️"):
        st.session_state.um_offset = st.session_state.um_offset + limit
        st.rerun()
    pag[2].caption(f"Offset: {st.session_state.um_offset}")

    ok, status_code, payload, err = client.list_users(q=q, role=role, status=status, limit=limit, offset=st.session_state.um_offset)
    if not ok:
        st.error(f"Users endpoint unavailable: {err or status_code}")
        st.info("Expected endpoint: GET /api/admin/users")
        return None, None

    items = payload.get("items") if isinstance(payload, dict) else payload
    total = payload.get("total") if isinstance(payload, dict) else None
    if not items:
        st.info("No users returned.")
        return None, None

    df = pd.DataFrame(items)
    # Normalize common fields
    for col in ["id", "user_id"]:
        if col in df.columns:
            df["user_id"] = df[col]
            break
    if "email" not in df.columns:
        df["email"] = None
    if "role" not in df.columns:
        df["role"] = "user"
    if "status" not in df.columns:
        df["status"] = "active"

    st.caption(f"Returned {len(df)} users" + (f" (total: {total})" if total is not None else ""))
    st.dataframe(df[ [c for c in ["user_id","email","role","status","created_at","last_login_at"] if c in df.columns] ], use_container_width=True, hide_index=True)

    selected = st.selectbox("Select user_id", df["user_id"].astype(str).tolist())
    return client, str(selected)

def user_detail_panel(client, user_id: str):
    st.subheader("🧾 User Detail")
    ok, status, payload, err = client.get_user(user_id)
    if not ok:
        st.error(f"User detail unavailable: {err or status}")
        st.info("Expected endpoint: GET /api/admin/users/{user_id}")
        return

    st.json(payload, expanded=False)

def user_actions_panel(client, user_id: str):
    st.subheader("⚙️ Admin Actions")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        new_role = st.selectbox("Set role", ["user", "mentor", "admin"], index=0, key="um_new_role")
        if st.button("✅ Update role", use_container_width=True):
            ok, status, payload, err = client.update_user(user_id, {"role": new_role})
            if ok:
                st.success("Role updated.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info("Expected endpoint: PATCH /api/admin/users/{user_id}")

    with a2:
        new_status = st.selectbox("Status", ["deactivate", "reactivate"], index=0, key="um_status_action")
        if st.button("🚫 Apply status", use_container_width=True):
            if new_status == "deactivate":
                ok, status, payload, err = client.deactivate_user(user_id)
                expected = "POST /api/admin/users/{user_id}/deactivate"
            else:
                ok, status, payload, err = client.reactivate_user(user_id)
                expected = "POST /api/admin/users/{user_id}/reactivate"
            if ok:
                st.success("Status updated.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info(f"Expected endpoint: {expected}")

    with a3:
        if st.button("🔒 Invalidate sessions", use_container_width=True):
            ok, status, payload, err = client.invalidate_sessions(user_id)
            if ok:
                st.success("Sessions invalidated.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info("Expected endpoint: POST /api/admin/users/{user_id}/invalidate-sessions")

    with a4:
        if st.button("🔑 Reset password", use_container_width=True):
            ok, status, payload, err = client.reset_password(user_id)
            if ok:
                st.success("Password reset initiated.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info("Expected endpoint: POST /api/admin/users/{user_id}/reset-password")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("📱 Force MFA reset", use_container_width=True):
            ok, status, payload, err = client.force_mfa_reset(user_id)
            if ok:
                st.success("MFA reset issued.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info("Expected endpoint: POST /api/admin/users/{user_id}/mfa/reset")

    with b2:
        with st.expander("➕ Create new user", expanded=False):
            with st.form("um_create_user"):
                email = st.text_input("Email")
                first = st.text_input("First name")
                last = st.text_input("Last name")
                role = st.selectbox("Role", ["user","mentor","admin"], index=0)
                submit = st.form_submit_button("Create")
            if submit:
                payload = {"email": email, "first_name": first, "last_name": last, "role": role}
                ok, status, data, err = client.create_user(payload)
                if ok:
                    st.success("User created.")
                    st.json(data, expanded=False)
                else:
                    st.error(f"Failed: {err or status}")
                    st.info("Expected endpoint: POST /api/admin/users")

def sync_tools_panel(client):
    st.subheader("🔄 Sync & Pipeline Tools")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔄 Trigger user sync", use_container_width=True):
            ok, status, payload, err = client.trigger_user_sync()
            if ok:
                st.success("User sync triggered.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info("Expected endpoint: POST /api/admin/sync/users")

    with c2:
        mode = st.selectbox("Parser mode", ["pending","all"], index=0)
        limit = st.number_input("Parser limit", min_value=10, max_value=2000, value=200, step=10)
        if st.button("🤖 Trigger parser run", use_container_width=True):
            ok, status, payload, err = client.trigger_parser_run(mode=mode, limit=int(limit))
            if ok:
                st.success("Parser run requested.")
                st.json(payload, expanded=False)
            else:
                st.error(f"Failed: {err or status}")
                st.info("Expected endpoint: POST /api/admin/parser/run")

    with c3:
        if st.button("📥 Export users (CSV)", use_container_width=True):
            ok, status, payload, err = client.list_users(limit=500, offset=0)
            if not ok:
                st.error(f"Export failed: {err or status}")
            else:
                items = payload.get("items") if isinstance(payload, dict) else payload
                df = pd.DataFrame(items or [])
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", data=csv, file_name=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")

def local_dir_panel():
    st.subheader("🗂️ Local Registrations (optional)")
    reg_dir = Path(st.secrets.get("USER_REG_DIR", "") or st.session_state.get("USER_REG_DIR", "") or (Path.cwd() / "data" / "user_registrations"))
    reg_dir = Path(st.text_input("USER_REG_DIR", value=str(reg_dir)))
    st.session_state["USER_REG_DIR"] = str(reg_dir)

    if not reg_dir.exists():
        st.warning("Directory does not exist.")
        return

    df = load_local_registrations(reg_dir)
    st.caption(f"Found {len(df)} registration files")
    if not df.empty:
        st.dataframe(df.head(50), use_container_width=True, hide_index=True)

def render():
    if not check_authentication():
        st.error("🚫 AUTHENTICATION REQUIRED")
        st.info("Set st.session_state['admin_authenticated']=True after login.")
        st.stop()

    st.title("👥 Admin — User Management")

# -----------------------------------------------------------------------------
# Authentication guard (admin portal standard)
# -----------------------------------------------------------------------------
def _require_admin_session():
    if st.session_state.get("user_role") == "admin":
        return True
    if st.session_state.get("admin_authenticated", False):
        return True
    st.error("🔒 Admin access required")
    st.stop()

_require_admin_session()

    st.caption("Truth-only: no mock users. All actions call FastAPI endpoints.")

    backend_status_panel()
    st.divider()

    client, user_id = user_list_panel()
    if not client or not user_id:
        st.divider()
        local_dir_panel()
        return

    tabs = st.tabs(["🧾 Detail", "⚙️ Actions", "🔄 Sync Tools", "🗂️ Local Reg Dir"])
    with tabs[0]:
        user_detail_panel(client, user_id)
    with tabs[1]:
        user_actions_panel(client, user_id)
    with tabs[2]:
        sync_tools_panel(client)
    with tabs[3]:
        local_dir_panel()


if __name__ == "__main__":
    render()
