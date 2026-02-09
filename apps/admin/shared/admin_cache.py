"""shared.admin_cache

Lightweight Streamlit cache helper with explicit TTL and force refresh.

- Cache is stored in st.session_state to avoid cross-user leakage in multi-user deployments.
- Use short TTL for admin dashboards (default 30s) to keep data fresh.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

import streamlit as st


@dataclass
class _CacheEntry:
    value: Any
    stored_at: float


def get_cached(
    cache_key: str,
    ttl_s: int,
    fetch: Callable[[], Any],
    force: bool = False,
) -> Any:
    now = time.time()
    entry = st.session_state.get(cache_key)

    if force or entry is None or not isinstance(entry, _CacheEntry):
        value = fetch()
        st.session_state[cache_key] = _CacheEntry(value=value, stored_at=now)
        return value

    age = now - entry.stored_at
    if age > ttl_s:
        value = fetch()
        st.session_state[cache_key] = _CacheEntry(value=value, stored_at=now)
        return value

    return entry.value