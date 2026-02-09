"""Shared FastAPI telemetry helpers for admin portal pages.

Provides cached access to the AdminFastAPIClient plus reusable
Streamlit UI blocks so every admin page can surface live backend
telemetry without duplicating logic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Optional

import pandas as pd
import streamlit as st

try:  # Prefer relative import when executed as a package module
    from .api_client import AdminFastAPIClient  # type: ignore
except ImportError:  # pragma: no cover - fallback when imported top-level
    try:
        from services.api_client import AdminFastAPIClient  # type: ignore
    except ImportError:  # pragma: no cover - optional offline usage
        AdminFastAPIClient = None  # type: ignore

DEFAULT_CACHE_TTL = 90
HEALTH_CACHE_TTL = 45


def get_admin_api_client() -> Optional["AdminFastAPIClient"]:
    """Return (and cache) a singleton AdminFastAPIClient instance."""
    if AdminFastAPIClient is None:
        return None

    client = st.session_state.get("_admin_api_client")
    if client is None:
        try:
            client = AdminFastAPIClient()
            st.session_state["_admin_api_client"] = client
        except Exception:  # pragma: no cover - backend optional in dev
            return None
    return client


def _get_cached_admin_payload(
    cache_key: str,
    ts_key: str,
    fetcher: Callable[["AdminFastAPIClient"], Dict[str, Any]],
    *,
    ttl_seconds: int,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Generic helper that caches FastAPI payloads inside session_state."""
    if force_refresh:
        st.session_state.pop(cache_key, None)
        st.session_state.pop(ts_key, None)

    cached = st.session_state.get(cache_key)
    ts = st.session_state.get(ts_key)
    if cached is not None and ts:
        age_seconds = (datetime.now() - ts).total_seconds()
        if age_seconds < ttl_seconds:
            return cached

    client = get_admin_api_client()
    if client is None:
        return cached or {}

    try:
        payload = fetcher(client) or {}
        st.session_state[cache_key] = payload
        st.session_state[ts_key] = datetime.now()
        return payload
    except Exception:  # pragma: no cover - keep last known payload
        return cached or {}


def format_relative_time(timestamp: Any) -> str:
    """Return human-readable relative delta for ISO timestamps."""
    if not timestamp:
        return "N/A"
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        delta = datetime.now() - parsed
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"
    except Exception:
        return str(timestamp)


class BackendTelemetryHelper:
    """Encapsulate cached FastAPI telemetry for a specific admin page."""

    def __init__(self, namespace: str, cache_ttl: int = DEFAULT_CACHE_TTL) -> None:
        self.namespace = namespace
        self.cache_ttl = cache_ttl

    # ------------------------------------------------------------------
    # Cache key helpers
    # ------------------------------------------------------------------
    def _cache_key(self, suffix: str) -> str:
        return f"_{self.namespace}_{suffix}"

    def _ts_key(self, suffix: str) -> str:
        return f"_{self.namespace}_{suffix}_ts"

    # ------------------------------------------------------------------
    # Snapshot fetchers
    # ------------------------------------------------------------------
    def get_dashboard_snapshot(self, *, force_refresh: bool = False) -> Dict[str, Any]:
        return _get_cached_admin_payload(
            self._cache_key("dashboard"),
            self._ts_key("dashboard"),
            lambda client: client.get_dashboard_snapshot(),
            ttl_seconds=self.cache_ttl,
            force_refresh=force_refresh,
        )

    def get_system_health_snapshot(self, *, force_refresh: bool = False) -> Dict[str, Any]:
        return _get_cached_admin_payload(
            self._cache_key("system_health"),
            self._ts_key("system_health"),
            lambda client: client.get_system_health(),
            ttl_seconds=HEALTH_CACHE_TTL,
            force_refresh=force_refresh,
        )

    def get_system_activity_snapshot(self, *, force_refresh: bool = False) -> Dict[str, Any]:
        return _get_cached_admin_payload(
            self._cache_key("system_activity"),
            self._ts_key("system_activity"),
            lambda client: client.get_system_activity(),
            ttl_seconds=HEALTH_CACHE_TTL,
            force_refresh=force_refresh,
        )

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def render_status_panel(
        self,
        *,
        title: str = "🛰️ Platform Telemetry",
        refresh_key: str,
        refresh_label: str = "🔄 Refresh Telemetry",
    ) -> None:
        """Render a standardized telemetry block with metrics and events."""
        if get_admin_api_client() is None:
            st.info("Connect the FastAPI backend to enable live telemetry on this page.")
            return

        st.subheader(title)

        refresh_col, meta_col = st.columns([1, 3])
        with refresh_col:
            if st.button(refresh_label, key=refresh_key):
                self.get_dashboard_snapshot(force_refresh=True)
                self.get_system_health_snapshot(force_refresh=True)
                self.get_system_activity_snapshot(force_refresh=True)
                st.rerun()

        dashboard = self.get_dashboard_snapshot() or {}
        system_health = self.get_system_health_snapshot() or {}
        system_activity = self.get_system_activity_snapshot() or {}

        system_block = dashboard.get("system", {})
        tokens_block = dashboard.get("tokens", {})
        services = system_block.get("services") or system_health.get("services") or {}

        with meta_col:
            st.caption(
                f"Telemetry updated {format_relative_time(system_health.get('updated_at') or system_block.get('updated_at'))}"
            )
            st.caption(
                f"Token ledger refreshed {format_relative_time(tokens_block.get('updated_at'))}"
            )

        cpu_pct = system_health.get("cpu_pct", system_block.get("cpu_percent", 0.0)) or 0.0
        mem_pct = system_health.get("memory_pct", system_block.get("memory_percent", 0.0)) or 0.0
        jobs_in_queue = system_block.get("jobs_in_queue", 0)
        parsers_online = system_block.get("parsers_online", 0)
        token_30d = tokens_block.get("total_used_30d", 0)
        token_24h = tokens_block.get("total_used_24h", 0)

        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("CPU Load", f"{cpu_pct:.1f}%", f"{system_health.get('cpu_count', 0)} cores")
        with metric_cols[1]:
            st.metric(
                "Memory Usage",
                f"{mem_pct:.1f}%",
                f"{system_health.get('memory_available_gb', 0):.1f} GB free",
            )
        with metric_cols[2]:
            st.metric("Jobs In Queue", f"{jobs_in_queue:,}", f"{parsers_online} workers")
        with metric_cols[3]:
            st.metric("Tokens (30d)", f"{token_30d:,}", f"{token_24h:,} / 24h")

        if services:
            running = sum(1 for status in services.values() if status == "running")
            st.caption(f"Services online: {running}/{len(services)}")
            with st.expander("🔧 Service Status", expanded=False):
                service_rows = [
                    {"Service": name, "Status": state}
                    for name, state in sorted(services.items())
                ]
                st.dataframe(pd.DataFrame(service_rows), use_container_width=True)

        budget_alerts = tokens_block.get("budget_alerts") or []
        for alert in budget_alerts[:2]:
            st.warning(
                f"⚠️ {alert.get('org', 'Org')} ({alert.get('plan', 'plan')}) at {alert.get('usage_pct', 0):.1f}% token usage"
            )

        events = system_activity.get("events") or []
        if events:
            with st.expander("📝 Recent Backend Activity", expanded=False):
                try:
                    st.dataframe(pd.DataFrame(events).head(15), use_container_width=True)
                except Exception:
                    st.json(events[:10])
