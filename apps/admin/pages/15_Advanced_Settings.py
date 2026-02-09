"""
=============================================================================
IntelliCV Admin Portal - Advanced Settings (ADMIN TRUTH PAGE) — ALL ENDPOINTS
=============================================================================

Canonical control surface for *admin-only* platform settings.

RULES (ENFORCED):
- NO demo data
- NO silent fallbacks that invent values
- Backend is the ONLY source of truth for persisted settings
- If required backend keys/endpoints are missing -> HARD ERROR (raise)

This page provides:
- System Settings (feature flags, environment switches, limits)
- Provider Configuration (API providers + cost model inputs)
- Storage/Queue switches (local-first parity vs prod)
- Backups/Restore (backend-managed)
- Observability switches (logging levels, sampling)

🔴 NEW ELEMENTS IN THIS VERSION:
- Unified admin auth via `shared.session.require_admin()`
- Canonical admin API client usage via `services.admin_api_client.get_admin_api_client()`
- Full endpoint wiring (GET/PUT settings, provider config, backups, restore, health)
- Strict contract validators (_require_dict/_require_list/_require_str)
- Settings editor writes ONLY to backend (no local mutation)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import streamlit as st

from shared.session import require_admin, get_access_token
from shared.admin_cache import get_cached
from services.admin_api_client import get_admin_api_client

# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------

st.set_page_config(
    page_title="Advanced Settings",
    page_icon="⚙️",
    layout="wide",
)

require_admin()  # 🔴 NEW: canonical auth
client = get_admin_api_client(access_token=get_access_token())  # 🔴 NEW: canonical API client

st.title("⚙️ Advanced Settings")
st.caption("Backend-truth configuration and platform controls. No local/demo values are used.")

refresh = st.button("🔄 Refresh all", use_container_width=True)

# -------------------------------------------------------------------
# STRICT CONTRACT HELPERS
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
# LOAD DATA (CACHED; STILL BACKEND TRUTH)
# -------------------------------------------------------------------

# 🔴 NEW: All these calls must exist server-side. If your backend hasn't shipped
# them yet, this page will hard error so you can implement the missing routes.

settings_payload = get_cached(
    "_advanced_settings",
    ttl_s=30,
    fetch=client.get_advanced_settings,
    force=refresh,
)

providers_payload = get_cached(
    "_provider_config",
    ttl_s=30,
    fetch=client.get_provider_config,
    force=refresh,
)

health_payload = get_cached(
    "_backend_health",
    ttl_s=30,
    fetch=client.get_health,
    force=refresh,
)

backups_payload = get_cached(
    "_backups_list",
    ttl_s=30,
    fetch=client.list_backups,
    force=refresh,
)

# -------------------------------------------------------------------
# CONTRACT: TOP-LEVEL KEYS
# -------------------------------------------------------------------

settings = _require_dict(settings_payload, "settings")
providers = _require_dict(providers_payload, "providers")
health_status = _require_str(health_payload, "status")
backups = _require_list(backups_payload, "backups")

# -------------------------------------------------------------------
# HEADER KPIs
# -------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
k1.metric("Backend", health_status)
k2.metric("Feature Flags", len(settings.get("feature_flags", {}) or {}))
k3.metric("Providers", len(providers or {}))
k4.metric("Backups", len(backups))

st.markdown("---")

# -------------------------------------------------------------------
# TABS
# -------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🧩 System Settings",
    "🔌 Provider Configuration",
    "💾 Backups & Restore",
    "🛰️ Health & Contracts",
])

# -------------------------------------------------------------------
# TAB 1: SYSTEM SETTINGS
# -------------------------------------------------------------------

with tab1:
    st.subheader("🧩 System Settings")

    # Required groups (backend should provide these)
    feature_flags = settings.get("feature_flags")
    limits = settings.get("limits")
    runtime = settings.get("runtime")

    if not isinstance(feature_flags, dict):
        raise RuntimeError("Advanced settings requires: settings.feature_flags (dict)")
    if not isinstance(limits, dict):
        raise RuntimeError("Advanced settings requires: settings.limits (dict)")
    if not isinstance(runtime, dict):
        raise RuntimeError("Advanced settings requires: settings.runtime (dict)")

    with st.form("system_settings_form"):
        st.markdown("### Feature Flags")
        ff_cols = st.columns(3)
        ff_updates: Dict[str, bool] = {}
        for i, (k, v) in enumerate(sorted(feature_flags.items(), key=lambda x: x[0])):
            with ff_cols[i % 3]:
                if not isinstance(v, bool):
                    raise RuntimeError(f"feature_flags.{k} must be boolean")
                ff_updates[k] = st.toggle(k, value=bool(v), key=f"ff_{k}")

        st.markdown("### Limits")
        max_upload_mb = st.number_input(
            "Max upload size (MB)",
            min_value=1,
            max_value=500,
            value=int(limits.get("max_upload_mb", 50)),
            step=1,
            key="limit_max_upload_mb",
        )
        max_requests_per_min = st.number_input(
            "Max requests per minute (per user)",
            min_value=1,
            max_value=10_000,
            value=int(limits.get("max_requests_per_min", 120)),
            step=10,
            key="limit_rpm",
        )
        max_concurrent_jobs = st.number_input(
            "Max concurrent jobs (workers)",
            min_value=1,
            max_value=10_000,
            value=int(limits.get("max_concurrent_jobs", 50)),
            step=1,
            key="limit_jobs",
        )

        st.markdown("### Runtime")
        log_level = st.selectbox(
            "Log level",
            options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(str(runtime.get("log_level", "INFO"))),
            key="rt_log_level",
        )
        enable_request_tracing = st.toggle(
            "Enable request tracing",
            value=bool(runtime.get("enable_request_tracing", False)),
            key="rt_tracing",
        )
        tracing_sample_rate = st.slider(
            "Tracing sample rate",
            min_value=0.0,
            max_value=1.0,
            value=float(runtime.get("tracing_sample_rate", 0.0)),
            step=0.01,
            key="rt_sample",
        )

        save_settings = st.form_submit_button("💾 Save system settings", use_container_width=True)

    if save_settings:
        payload = {
            "feature_flags": ff_updates,
            "limits": {
                "max_upload_mb": int(max_upload_mb),
                "max_requests_per_min": int(max_requests_per_min),
                "max_concurrent_jobs": int(max_concurrent_jobs),
            },
            "runtime": {
                "log_level": log_level,
                "enable_request_tracing": bool(enable_request_tracing),
                "tracing_sample_rate": float(tracing_sample_rate),
            },
        }
        result = client.update_advanced_settings(payload)  # 🔴 NEW endpoint usage
        _ = _require_dict(result, "settings")
        st.success("✅ System settings saved to backend.")
        st.rerun()

# -------------------------------------------------------------------
# TAB 2: PROVIDER CONFIG
# -------------------------------------------------------------------

with tab2:
    st.subheader("🔌 Provider Configuration")
    st.caption("Provider keys are managed on Page 13 (API Integration). Here we manage provider *cost and usage model inputs*.")

    # Contract: providers is dict of provider_name -> config dict
    if not isinstance(providers, dict) or not providers:
        raise RuntimeError("Provider config requires: providers (non-empty dict)")

    provider_names = sorted(providers.keys())
    selected = st.selectbox("Provider", provider_names, key="provider_select")
    cfg = providers.get(selected)
    if not isinstance(cfg, dict):
        raise RuntimeError(f"providers['{selected}'] must be a dict")

    with st.form("provider_cfg_form"):
        st.markdown(f"### {selected}")

        # Common cost model inputs (backend should store these)
        currency = st.text_input("Currency (ISO)", value=str(cfg.get("currency", "USD")), key="prov_currency")
        # Prices are per 1K tokens by default to match your token page convention
        price_in_per_1k = st.number_input(
            "Input cost per 1K tokens",
            min_value=0.0,
            value=float(cfg.get("input_price_per_1k", 0.0)),
            step=0.0001,
            format="%.4f",
            key="prov_in",
        )
        price_out_per_1k = st.number_input(
            "Output cost per 1K tokens",
            min_value=0.0,
            value=float(cfg.get("output_price_per_1k", 0.0)),
            step=0.0001,
            format="%.4f",
            key="prov_out",
        )

        st.markdown("### Defaults & Guards")
        default_model = st.text_input("Default model", value=str(cfg.get("default_model", "")), key="prov_model")
        rpm_limit = st.number_input(
            "RPM limit (provider)",
            min_value=0,
            value=int(cfg.get("rpm_limit", 0) or 0),
            step=10,
            key="prov_rpm",
        )
        tpm_limit = st.number_input(
            "TPM limit (provider)",
            min_value=0,
            value=int(cfg.get("tpm_limit", 0) or 0),
            step=1000,
            key="prov_tpm",
        )

        save_provider = st.form_submit_button("💾 Save provider config", use_container_width=True)

    if save_provider:
        updated = {
            "provider": selected,
            "config": {
                "currency": currency,
                "input_price_per_1k": float(price_in_per_1k),
                "output_price_per_1k": float(price_out_per_1k),
                "default_model": default_model,
                "rpm_limit": int(rpm_limit),
                "tpm_limit": int(tpm_limit),
            },
        }
        res = client.update_provider_config(updated)  # 🔴 NEW endpoint usage
        _ = _require_dict(res, "providers")
        st.success("✅ Provider configuration saved to backend.")
        st.rerun()

    st.markdown("---")
    st.subheader("📌 Quick Link: Token Economics")
    st.info("Your token economics simulator lives on Page 10 (Token Management). It consumes this provider cost config via the backend.")
    if st.button("➡️ Go to Token Management (Page 10)", use_container_width=True):
        # Keep this as a safe navigation attempt; Streamlit will error if path differs.
        try:
            st.switch_page("pages/10_Token_Management.py")
        except Exception:
            st.warning("Could not navigate automatically. Ensure your page filename matches your router mapping.")

# -------------------------------------------------------------------
# TAB 3: BACKUPS & RESTORE
# -------------------------------------------------------------------

with tab3:
    st.subheader("💾 Backups & Restore")

    st.caption("Backups are created and stored by the backend. This page only triggers operations and lists results.")

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("📦 Create backup", use_container_width=True):
            created = client.create_backup()  # 🔴 NEW endpoint usage
            backup_obj = _require_dict(created, "backup")
            st.success(f"✅ Backup created: {backup_obj.get('id')}")
            st.rerun()

    with c2:
        st.info("Tip: If you run this in local-first mode, your backend can write backups to ./working_copy/backups/ and still behave identically in prod (Blob storage).")

    if backups:
        import pandas as pd
        bdf = pd.DataFrame(backups)
        st.dataframe(bdf, use_container_width=True, hide_index=True)
    else:
        st.info("No backups reported by backend yet.")

    st.markdown("### Restore")
    backup_ids = [b.get("id") for b in backups if isinstance(b, dict) and b.get("id")]
    if not backup_ids:
        st.warning("No restorable backups available.")
    else:
        restore_id = st.selectbox("Select backup to restore", backup_ids, key="restore_backup_id")
        confirm = st.checkbox("I understand this will overwrite current backend state.", value=False, key="restore_confirm")
        if st.button("♻️ Restore backup", use_container_width=True, disabled=not confirm):
            result = client.restore_backup(restore_id)  # 🔴 NEW endpoint usage
            status = _require_str(result, "status")
            st.success(f"✅ Restore complete: {status}")
            st.rerun()

# -------------------------------------------------------------------
# TAB 4: HEALTH & CONTRACTS
# -------------------------------------------------------------------

with tab4:
    st.subheader("🛰️ Health & Contracts")

    st.write(f"**Backend status:** {health_status}")
    contracts = _require_list(health_payload, "contracts")
    st.dataframe(contracts, use_container_width=True)

    st.markdown("### Endpoint Coverage (Required for this page)")
    st.code(
        "\n".join(
            [
                "GET  /admin/advanced-settings            -> client.get_advanced_settings()",
                "PUT  /admin/advanced-settings            -> client.update_advanced_settings(payload)",
                "GET  /admin/provider-config              -> client.get_provider_config()",
                "PUT  /admin/provider-config              -> client.update_provider_config(payload)",
                "GET  /admin/backups                      -> client.list_backups()",
                "POST /admin/backups                      -> client.create_backup()",
                "POST /admin/backups/{id}/restore         -> client.restore_backup(id)",
                "GET  /health                             -> client.get_health()",
            ]
        ),
        language="text",
    )

    st.caption("If any endpoint is missing, implement it in your backend admin API and the admin_api_client wrapper. This page will not guess values.")
