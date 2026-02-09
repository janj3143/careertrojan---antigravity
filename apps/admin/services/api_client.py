"""FastAPI client wrapper for IntelliCV admin portal."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx


class AdminFastAPIClient:
    """Lightweight synchronous client for the shared FastAPI backend."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 8.0,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url or os.getenv("INTELLICV_ADMIN_API", "http://localhost:8000/api/admin/v1")
        self.timeout = timeout
        self._headers = {"X-Admin-Portal": "intellicv-admin"}
        if default_headers:
            self._headers.update(default_headers)
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout, headers=self._headers)
        self.logger = logging.getLogger(self.__class__.__name__)

    # ---------------------------------------------------------------------
    # Low-level request helper
    # ---------------------------------------------------------------------
    def _request(self, method: str, path: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            if response.content:
                return response.json()
            return {}
        except httpx.HTTPError as exc:
            self.logger.warning("FastAPI request failed: %s %s (%s)", method, path, exc)
            return None

    # ---------------------------------------------------------------------
    # High-level helpers referenced by admin pages/services
    # ---------------------------------------------------------------------
    def get_system_health(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/system/health")

    def get_system_activity(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/system/activity")

    def get_user_metrics(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/users/metrics")

    def get_user_security(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/users/security")

    def get_user_subscriptions(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/users/subscriptions")

    def get_user_data_sources(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/users/data-sources")

    def post_bridge_payload(self, bridge: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send bridge payloads (e.g., UMarketU, Dual Career)."""
        return self._request("POST", f"/bridges/{bridge}", json=payload)

    def get_dashboard_snapshot(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/dashboard/snapshot")

    def get_token_summary(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/tokens/summary")

    def get_token_plans(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/tokens/config")

    def update_token_plans(self, plans: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._request("PUT", "/tokens/config", json={"plans": plans})

    def get_token_usage(self) -> Optional[Dict[str, Any]]:
        return self._request("GET", "/tokens/usage")

    def close(self) -> None:
        self._client.close()


__all__ = ["AdminFastAPIClient"]
