"""Shared admin API client for Streamlit admin pages."""

from __future__ import annotations

from typing import Optional

import os
import requests


class AdminApiClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        # Allow override via env var, fallback to localhost
        if base_url is None:
            base_url = os.getenv("INTELLICV_ADMIN_API_URL", "http://localhost:8000")
        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()

        # Optional auth header hook – can be upgraded to JWT later
        if api_key is None:
            api_key = os.getenv("INTELLICV_ADMIN_API_KEY")
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def get(self, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        return self.session.get(url, timeout=10, **kwargs)

    def post(self, path: str, json=None, **kwargs):
        url = f"{self.base_url}{path}"
        return self.session.post(url, json=json, timeout=10, **kwargs)

    def put(self, path: str, json=None, **kwargs):
        url = f"{self.base_url}{path}"
        return self.session.put(url, json=json, timeout=10, **kwargs)


def get_admin_api_client() -> AdminApiClient:
    """
    Return a shared AdminApiClient instance.

    For now we simply construct a new one; if you want you can cache it
    in st.session_state later.
    """
    return AdminApiClient()
