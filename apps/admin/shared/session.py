from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import streamlit as st

@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    username: str
    display_name: str
    role: str  # 'admin' | 'user' | ...

def _coerce_user(raw: Any) -> Optional[CurrentUser]:
    if raw is None:
        return None
    if isinstance(raw, CurrentUser):
        return raw
    if isinstance(raw, dict):
        uid = str(raw.get("user_id") or raw.get("id") or raw.get("uid") or "").strip()
        uname = str(raw.get("username") or raw.get("email") or raw.get("name") or "").strip()
        dname = str(raw.get("display_name") or raw.get("displayName") or uname).strip()
        role = str(raw.get("role") or raw.get("user_role") or "user").strip().lower()
        if not uname:
            return None
        return CurrentUser(user_id=uid or uname, username=uname, display_name=dname or uname, role=role)
    return None

def get_current_user() -> Optional[CurrentUser]:
    # Canonical key
    user = _coerce_user(st.session_state.get("current_user"))
    if user:
        return user

    # Backwards-compatible fallbacks
    legacy_user = st.session_state.get("authenticated_user") or st.session_state.get("user")
    user = _coerce_user(legacy_user)
    if user:
        return user

    # Admin-only flag in older builds
    if st.session_state.get("admin_authenticated", False):
        uname = str(st.session_state.get("admin_username") or "admin").strip()
        return CurrentUser(user_id=uname, username=uname, display_name=uname, role="admin")

    return None

def get_access_token() -> str:
    # Canonical
    tok = st.session_state.get("access_token")
    if isinstance(tok, str) and tok.strip():
        return tok.strip()

    # Backwards compatible keys
    for k in ("admin_access_token", "token", "jwt", "bearer_token"):
        v = st.session_state.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()

    raise RuntimeError(
        "Access token missing. Ensure login flow stores an access token in st.session_state['access_token']."
    )

def require_admin() -> CurrentUser:
    user = get_current_user()
    if user and user.role.lower() == "admin":
        st.session_state["is_admin"] = True
        return user

    # legacy admin_authenticated boolean
    if st.session_state.get("admin_authenticated", False):
        st.session_state["is_admin"] = True
        uname = str(st.session_state.get("admin_username") or "admin").strip()
        return CurrentUser(user_id=uname, username=uname, display_name=uname, role="admin")

    st.session_state["is_admin"] = False
    st.error("🔒 Admin authentication required.")
    st.caption("Please sign in via the Admin Login page to access this module.")
    # Avoid hard-coded switch_page targets if your app routes differ
    if st.button("Go to Admin Login"):
        try:
            st.switch_page("pages/99_admin/00_admin_login.py")
        except Exception:
            pass
    st.stop()
    raise RuntimeError("Unreachable")